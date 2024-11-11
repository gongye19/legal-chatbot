from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        query = data.get('message')
        history = data.get('history', [])

        if not query:
            self._send_error(400, "No message provided")
            return

        try:
            # 构建消息历史
            messages = [{"role": "system", "content": system_prompt}]
            recent_history = history[-10:]
            
            for msg in recent_history:
                if msg.get('isComplete', True):
                    messages.append({
                        "role": "user" if msg["sender"] == "user" else "assistant",
                        "content": msg["text"]
                    })

            messages.append({"role": "user", "content": query})

            # 设置超时时间
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                stream=False,
                timeout=25  # 设置25秒超时
            )

            answer = response.choices[0].message.content
            self._send_response({"response": answer})

        except Exception as e:
            print(f"Error in handler: {str(e)}")  # 添加错误日志
            self._send_error(500, str(e))

    def _send_response(self, data):
        self.send_response(200)
        self._send_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status_code, message):
        self.send_response(status_code)
        self._send_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    def _send_headers(self):
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main(req, res):
    try:
        if req.method == 'OPTIONS':
            handler().do_OPTIONS()
        elif req.method == 'POST':
            handler().do_POST()
        else:
            res.status = 405
            res.body = "Method Not Allowed"
    except Exception as e:
        print(f"Error in main: {str(e)}")  # 添加错误日志
        res.status = 500
        res.body = str(e)