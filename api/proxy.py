import os, json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            api_key = os.environ.get('ANTHROPIC_KEY', '').strip()
            if not api_key:
                self._error(500, 'ANTHROPIC_KEY is not configured in Vercel environment variables')
                return

            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)

            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=body,
                headers={
                    'x-api-key':         api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type':      'application/json',
                    'accept':            'text/event-stream',
                },
                method='POST',
            )

            with urllib.request.urlopen(req) as res:
                self.send_response(res.status)
                self._cors()
                self.send_header('Content-Type', res.headers.get('Content-Type', 'text/event-stream'))
                self.end_headers()
                while True:
                    chunk = res.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()

        except urllib.error.HTTPError as e:
            self._error(e.code, e.read().decode('utf-8', errors='replace'))
        except Exception as e:
            self._error(500, str(e))

    def _error(self, code, message):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': {'message': message}}).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
