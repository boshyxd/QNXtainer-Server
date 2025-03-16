import json
from pathlib import Path
import re
import os

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
    image = None
    for img_id, img in state.images.items():
        if img_id == image_id:
            image = img
            break
    
    if not image:
        raise ValueError(f"Image with ID {image_id} not found")
    
    container = Container(status="running", cpu=5, memory=64)
    container_id = container.prepare(image)
    container.start()
    
    state.add_container(container)
    print(f"Started container {container_id} from image {image.name}:{image.tag}")
    
    return container_id


def start_container(container_id: str) -> str:
    """Start an existing container by ID"""
    if container_id not in state.containers:
        raise ValueError(f"Container with ID {container_id} not found")
    
    container = state.containers[container_id]
    
    if container.status == "running":
        print(f"Container {container_id} is already running")
        return container_id
    
    container.status = "running"
    container.cpu = 5
    container.memory = 64
    
    if hasattr(container, 'runner') and container.runner:
        container.start()
    
    print(f"Started container {container_id}")
    return container_id


def stop_container(container_id: str):
    """Stop a running container"""
    if container_id not in state.containers:
        raise ValueError(f"Container with ID {container_id} not found")
    
    container = state.containers[container_id]
    
    if container.status == "stopped":
        print(f"Container {container_id} is already stopped")
        return
    
    if hasattr(container, 'process') and container.process:
        container.stop()
    
    container.status = "stopped"
    container.cpu = 0
    container.memory = 0
    
    print(f"Stopped container {container_id}")


def create_container(image_id: str, name: str) -> str:
    """Create a new container from an image"""
    image = None
    for img_id, img in state.images.items():
        if img_id == image_id:
            image = img
            break
    
    if not image:
        raise ValueError(f"Image with ID {image_id} not found")
    
    container = Container(status="stopped", cpu=0, memory=0)
    container.name = name
    container.image = image
    container.id = f"container-{len(state.containers) + 1}"
    
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


class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Add CORS headers to allow cross-origin requests"""
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


def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = ("", PORT)
    httpd = server_class(server_address, handler_class)
    print(f"QNXtainer Server running at http://0.0.0.0:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
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
