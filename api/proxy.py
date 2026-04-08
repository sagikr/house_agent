import os, json
import urllib.request
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=body,
            headers={
                'x-api-key':          os.environ['ANTHROPIC_KEY'],
                'anthropic-version':  '2023-06-01',
                'content-type':       'application/json',
                'accept':             'text/event-stream',
            },
            method='POST',
        )

        with urllib.request.urlopen(req) as res:
            self.send_response(res.status)
            self._cors()
            self.send_header('Content-Type', res.headers.get('Content-Type', 'text/event-stream'))
            self.end_headers()
            while True:
                chunk = res.read(1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
