"""Serve the repo for local play with the two headers the page needs.

The page uses SharedArrayBuffer (the speed slider pauses the Python thread between actions,
and Stop interrupts it), which browsers only allow on a cross-origin isolated page: the server
must send Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy. Everything the page
loads is same-origin, so the strict values are fine. In production nginx sends the same two
headers for /mower/.

    python3 web/serve.py          # then open http://localhost:8077/web/
"""
import http.server
import mimetypes
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8077
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('text/javascript', '.mjs')


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        if '/pyodide/' not in fmt % args:   # the runtime's files are noise
            super().log_message(fmt, *args)


if __name__ == '__main__':
    with http.server.ThreadingHTTPServer(('', PORT), Handler) as httpd:
        sys.stdout.write(f'Mowbot at http://localhost:{PORT}/web/\n')
        sys.stdout.flush()
        httpd.serve_forever()
