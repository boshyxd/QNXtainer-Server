import json
from pathlib import Path
import re
import os
import socket

from image import Image
from data import Data
from container import Container

from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080

state = Data()


def upload_image(image_file: Path, image_name: str, image_tag: str = "latest"):
    if not image_file.exists():
        print(f"Warning: Image file {image_file} does not exist. Skipping.")
        return
    
    image = Image(image_name, image_tag)
    image.unpack_from(image_file)
    state.add_image(image)
    print(f"Added image: {image_name}:{image_tag}")


def start_container_from_image(image_id: str) -> str:
    """Start a container from an image"""
    image = state.get_image_by_id(image_id)    
    if image is None:
        raise ValueError(f"Image with ID {image_id} not found")
    
    container = Container(status="running", cpu=5, memory=64)
    container_id = container.prepare(image)
    container.start()
    
    state.add_container(container)
    print(f"Started container {container_id} from image {image.name}:{image.tag}")
    
    return container_id


def start_container(container_id: str) -> str:
    """Start an existing container by ID"""
    target_container = state.get_container_by_id(container_id)
    if target_container is None:
        raise ValueError(f"Container with ID {container_id} not found")
    
    if target_container.status == "running":
        print(f"Container {container_id} is already running")
        return container_id
    
    container.status = "running"
    container.cpu = 5
    container.memory = 64
    
    if hasattr(target_container, 'runner') and target_container.runner:
        target_container.start()
    else:
        print(f"Container {container_id} has no runner. Aborting.")
    
    print(f"Started container {container_id}")
    return container_id


def stop_container(container_id: str):
    """Stop a running container"""
    target_container = state.get_container_by_id(container_id)
    if target_container is None:
        raise ValueError(f"Container with ID {container_id} not found")    
    if target_container.status == "stopped":
        print(f"container {container_id} is already stopped")
        return
    
    if hasattr(target_container, 'process') and container.process:
        target_container.stop()
    
    target_container.status = "stopped"
    target_container.cpu = 0
    target_container.memory = 0
    
    print(f"Stopped container {container_id}")


def create_container(image_id: str, name: str) -> str:
    """Create a new container from an image"""
    target_image = state.get_image_by_id(image_id)
    if target_image is None:
        raise ValueError(f"Image with ID {image_id} not found")
    
    container = Container(status="stopped", cpu=0, memory=0)
    container.prepare(target_image)
    
    state.add_container(container)
    print(f"Created container {container.id} from image {image.name}:{image.tag}")
    
    return container.id


def ensure_directories():
    """Create necessary directories for QNXtainer"""
    home_dir = Path().home()
    qnx_dir = home_dir / ".qnxtainer"
    images_dir = qnx_dir / "images"
    containers_dir = qnx_dir / "containers"
    
    for directory in [qnx_dir, images_dir, containers_dir]:
        directory.mkdir(exist_ok=True, parents=True)
    
    print(f"QNXtainer directories initialized at {qnx_dir}")


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if args[1].startswith('4') or args[1].startswith('5'):
            print(f"ERROR: {args[0]} - {args[1]}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_GET(self):
        if self.path == "/state":
            response_json = json.dumps(state.to_json()).encode()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(response_json)
            return
        
        self.send_response(404)
        self.send_header("Content-type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            if content_length > 0:
                post_json = json.loads(post_data)
            else:
                post_json = {}
        except json.JSONDecodeError:
            post_json = {}
        
        if self.path == "/upload-image":
            response_data = {"status": "uploaded"}
        
        elif self.path == "/create-container":
            if "image_id" not in post_json or "name" not in post_json:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing image_id or name"}).encode())
                return
            
            try:
                container_id = create_container(post_json["image_id"], post_json["name"])
                response_data = {"status": "created", "container_id": container_id}
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        elif re.match(r"^/start-from-image/([\w-]+)$", self.path):
            image_id = self.path.split("/")[-1]
            try:
                container_id = start_container_from_image(image_id)
                response_data = {"status": "started", "container_id": container_id}
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        elif re.match(r"^/start/([\w-]+)$", self.path):
            container_id = self.path.split("/")[-1]
            try:
                start_container(container_id)
                response_data = {"status": "started", "container_id": container_id}
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        elif re.match(r"^/stop/([\w-]+)$", self.path):
            container_id = self.path.split("/")[-1]
            try:
                stop_container(container_id)
                response_data = {"status": "stopped", "container_id": container_id}
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
            return
        
        response_json = json.dumps(response_data).encode()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response_json)


def run(server_class=HTTPServer, handler_class=RequestHandler, port=PORT):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    ip = get_ip_address()
    print(f"QNXtainer Server running at http://{ip}:{port}")
    print(f"Connect QNXtainer-Studio to this address")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down QNXtainer Server...")
        httpd.server_close()


if __name__ == "__main__":
<<<<<<< HEAD
    ensure_directories()
    
    mock_image_path = Path().home() / ".qnxtainer" / "images" / "mock-app.tar.gz"
    if mock_image_path.exists():
        upload_image(mock_image_path, "mock-app")
    else:
        print(f"Mock image not found at {mock_image_path}. Starting with empty state.")
        mock_image = Image("mock-app", "latest")
        state.add_image(mock_image)
        print("Added mock image to state.")
    
    run()
=======
    new_image = upload_image(
        Path().home() / ".qnxtainer" / "images" / "mock-app.tar.gz", "mock-app"
    )
    run()
>>>>>>> 53dbcf2 (fleshing out start and stop commands)
