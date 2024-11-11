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
    def do_POST(self):
        try:
            # 1. 读取请求内容
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('message')
            history = data.get('history', [])

            # 2. 构建消息历史
            messages = [{"role": "system", "content": system_prompt}]
            recent_history = history[-10:]
            
            for msg in recent_history:
                if msg.get('isComplete', True):
                    messages.append({
                        "role": "user" if msg["sender"] == "user" else "assistant",
                        "content": msg["text"]
                    })

            messages.append({"role": "user", "content": query})

            # 3. 调用 API
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                stream=False,
                timeout=30  # 设置30秒超时
            )

            answer = response.choices[0].message.content

            # 4. 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            response_data = {
                "response": answer
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except Exception as e:
            print(f"Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_data = {"error": str(e)}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main(request):
    if request.get('method') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        }
    elif request.get('method') == 'POST':
        handler().do_POST()
    else:
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }