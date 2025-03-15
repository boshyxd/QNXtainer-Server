import json
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080
MOCK_RESPONSE = {"message": "Hello, this is a GET response!"}


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/state" or self.path == "/":
            response_json = json.dumps(MOCK_RESPONSE).encode()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response_json)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def do_POST(self):
        pass


def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"http://0.0.0.0:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()