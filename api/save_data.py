import os, json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                self._error(500, 'Supabase not configured in environment variables')
                return

            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)

            session_id = data.get('session_id')

            row = {
                'username': data.get('username'),
                'consent':  data.get('consent'),
                'mode':     data.get('mode'),
                'options':  data.get('options'),
                'messages': data.get('messages'),
                'profile':  data.get('profile'),
                'scores':   data.get('scores'),
                'report':   data.get('report'),
                'phase':    data.get('phase'),
            }

            if session_id:
                # Update existing row
                url    = f'{SUPABASE_URL}/rest/v1/sessions?id=eq.{session_id}'
                method = 'PATCH'
                # Don't overwrite username/consent on update
                row.pop('username', None)
                row.pop('consent', None)
            else:
                # Insert new row
                url    = f'{SUPABASE_URL}/rest/v1/sessions'
                method = 'POST'

            req = urllib.request.Request(
                url,
                data=json.dumps(row).encode(),
                headers={
                    'apikey':        SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type':  'application/json',
                    'Prefer':        'return=representation',
                },
                method=method,
            )

            with urllib.request.urlopen(req) as res:
                result = res.read()
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)

        except urllib.error.HTTPError as e:
            self._error(e.code, e.read().decode('utf-8', errors='replace'))
        except Exception as e:
            self._error(500, str(e))

    def _error(self, code, message):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
