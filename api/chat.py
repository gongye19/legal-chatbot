from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters. Please provide concise and clear responses.'''

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        query = data.get('message')

        if not query:
            self._send_error(400, "No message provided")
            return

        try:
            # 限制输入长度
            if len(query) > 500:
                self._send_error(400, "Query too long. Please limit to 500 characters.")
                return

            # 设置较短的超时时间
            response = client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                stream=False,
                timeout=10,  # 设置10秒超时
                max_tokens=500  # 限制响应长度
            )

            answer = response.choices[0].message.content
            self._send_response({"response": answer})

        except Exception as e:
            print(f"Error: {str(e)}")
            self._send_error(500, str(e))

    def do_OPTIONS(self):
        self._send_cors_headers()
        self.send_response(200)
        self.end_headers()

    def _send_response(self, data):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status_code, message):
        self.send_response(status_code)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    def _send_cors_headers(self):
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

def main(req, res):
    if req.method == 'OPTIONS':
        handler().do_OPTIONS()
    elif req.method == 'POST':
        handler().do_POST()
    else:
        res.status = 405
        res.body = "Method Not Allowed"