import json
import logging
from pathlib import Path
import re
import os
import uuid
import cgi
from socketserver import ThreadingMixIn

from image import Image
from data import Data
from container import Container

from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080

state = Data()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_image(image_file: Path, image_name: str, image_tag: str = "latest"):
    if not os.path.isfile(image_file):
        print(f"Warning: Image file {image_file} does not exist. Skipping.")
        return

    image = Image(image_name, image_tag)
    image.unpack_from(image_file)
    state.add_image(image)
    print(f"Added image: {image_name}:{image_tag}")


def start_container_from_image(
    image_id: str, cpu: float = 5, memory: float = 64
) -> str:
    """Start a container from an image"""
    image = state.get_image_by_id(image_id)
    if image is None:
        raise ValueError(f"Image with ID {image_id} not found")

    container = Container(status="running", cpu=cpu, memory=memory)
    container_id = container.prepare(image)
    container.start()

    state.add_container(container)
    print(f"Started container {container_id} from image {image.name}:{image.tag}")

    return container_id


def start_container(container_id: str, cpu: float = 5, memory: float = 64) -> str:
    """Start an existing container by ID"""
    target_container = state.get_container_by_id(container_id)
    if target_container is None:
        raise ValueError(f"Container with ID {container_id} not found")

    if target_container.status == "running":
        print(f"Container {container_id} is already running")
        return container_id

    target_container.status = "running"
    target_container.cpu = cpu
    target_container.memory = memory

    if hasattr(target_container, "runner") and target_container.runner:
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

    if hasattr(target_container, "process") and target_container.process:
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
    print(
        f"Created container {container.id} from image {target_image.name}:{target_image.tag}"
    )

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
    def send_error(self, code, message=None):
        self.send_response(code)
        self.send_cors_headers()
        self.send_header("Content-type", "application/json")
        self.end_headers()
        error_response = json.dumps({"error": message or "Unknown error"}).encode()
        self.wfile.write(error_response)

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
        form = cgi.FieldStorage(
            fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"}
        )

        if self.path == "/upload-image":
            content_type = self.headers.get("Content-Type")
            if not content_type or "multipart/form-data" not in content_type:
                self.send_error(400, "Invalid Content-Type")
                return

            name = form.getvalue("name")
            if not name:
                self.send_error(400, "Missing 'name' parameter")
                return
            tag = form.getvalue("tag")
            if not tag:
                tag = uuid.uuid4().hex
            file_item = form["file"]
            if file_item.filename.endswith(".tar.gz."):
                self.send_error(
                    400, f"Only .tar.gz files are allowed. Now {file_item.filename}"
                )
                return

            tmp_dir = Path.home() / "server" / "tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)

            file_path = tmp_dir / f"{name}.tar.gz"
            with open(file_path, "wb") as output_file:
                output_file.write(file_item.file.read())
            print(f"File saved: {file_path}")
            logger.info("File saved, processing.")

            upload_image(file_path, name, tag)

            logger.info("Image processed.")
            os.remove(file_path)
            print(f"File deleted: {file_path}")

            response_data = {
                "status": "uploaded",
                "filename": f"{name}.tar.gz",
                "path": str(file_path),
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        elif self.path == "/create-container":
            print(form)
            if not form.getvalue("image_id") or not form.getvalue("name"):
                self.send_error(400, "Missing image_id or name")
                return

            try:
                container_id = create_container(
                    form.getvalue("image_id"), form.getvalue("name")
                )
                response_data = {"status": "created", "container_id": container_id}
            except ValueError as e:
                self.send_error(400, str(e))
                return
        elif re.match(r"^/start-from-image/([\w-]+)$", self.path):
            image_id = self.path.split("/")[-1]
            try:
                container_id = start_container_from_image(image_id)
                response_data = {"status": "started", "container_id": container_id}
            except ValueError as e:
                self.send_error(400, str(e))
                return
        elif re.match(r"^/start/([\w-]+)$", self.path):
            container_id = self.path.split("/")[-1]
            try:
                logger.info("Attempting to start container %s", container_id)
                start_container(container_id)
                response_data = {"status": "started", "container_id": container_id}
            except ValueError as e:
                self.send_error(400, str(e))
                return
        elif re.match(r"^/stop/([\w-]+)$", self.path):
            container_id = self.path.split("/")[-1]
            try:
                stop_container(container_id)
                response_data = {"status": "stopped", "container_id": container_id}
            except ValueError as e:
                self.send_error(400, str(e))
                return
        else:
            self.send_error(404, "Invalid path")
            return

        response_json = json.dumps(response_data).encode()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response_json)


class ThreadedSimpleServer(ThreadingMixIn, HTTPServer):
    pass


def run(server_class=ThreadedSimpleServer, handler_class=RequestHandler):
    server_address = ("", PORT)
    httpd = server_class(server_address, handler_class)
    print(f"QNXtainer Server running at http://0.0.0.0:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    ensure_directories()
    run()
