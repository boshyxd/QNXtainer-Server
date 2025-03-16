import json
from pathlib import Path
import re

from image import Image
from data import Data

from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080

state = Data()


def upload_image(image_file: Path, image_name: str, image_tag: str = "latest"):
    image = Image(image_name, image_tag)
    image.unpack_from(image_file)


def start_container(image_name: str, image_tag: str = "latest") -> str:
    pass


def stop_container(container_id: str):
    pass


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
        if self.path == "/upload-image":
            response_data = {"status": "uploaded"}
        elif re.match(r"^/start/([\w-]+)$", self.path):
            image_id = self.path.split("/")[-1]
            response_data = {"status": "starting", "image_id": image_id}
        elif re.match(r"^/stop/([\w-]+)$", self.path):
            container_id = self.path.split("/")[-1]
            response_data = {"status": "starting", "image_id": container_id}
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
    upload_image(
        Path().home() / ".qnxtainer" / "images" / "mock-app.tar.gz", "mock-app"
    )
    run()
