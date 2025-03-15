from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"http://0.0.0.0:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()