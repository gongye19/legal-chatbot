from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance on legal matters.'''

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        query = data.get('message')
        history = data.get('history', [])

        if not query:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No message provided"}).encode())
            return

        try:
            # 构建消息历史
            messages = [{"role": "system", "content": system_prompt}]
            recent_history = history[-4:]  # 保留最近的2轮对话
            
            for msg in recent_history:
                if msg.get('isComplete', True):
                    messages.append({
                        "role": "user" if msg["sender"] == "user" else "assistant",
                        "content": msg["text"]
                    })

            messages.append({"role": "user", "content": query})

            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                stream=False
            )

            answer = response.choices[0].message.content

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"response": answer}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main(req, res):
    if req.method == 'POST':
        handler().do_POST()
    else:
        res.status = 405
        res.body = "Method Not Allowed"