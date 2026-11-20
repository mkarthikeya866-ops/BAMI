import http.server
import socketserver
import os
import sys

PORT = 5501
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Frontend")

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    try:
        with ThreadingTCPServer(("0.0.0.0", PORT), NoCacheHTTPRequestHandler) as httpd:
            print(f"Serving {DIRECTORY} on http://0.0.0.0:{PORT} with no-cache headers", flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
