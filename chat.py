from http.server import HTTPServer, BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

# 创建线程池
executor = ThreadPoolExecutor(max_workers=4)

class RequestHandler(BaseHTTPRequestHandler):
    async def call_api(self, messages):
        # 在线程池中运行API调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            executor,
            lambda: client.chat.completions.create(
                model="glm-4",
                messages=messages,
                stream=False
            )
        )
        return response

    def do_POST(self):
        try:
            # 1. 读取请求内容
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            print(f"Received raw data: {post_data}")
            
            data = json.loads(post_data.decode('utf-8'))
            print(f"Parsed data: {data}")
            
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
            print(f"Final messages: {messages}")

            # 3. 异步调用 API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.call_api(messages))
            loop.close()

            answer = response.choices[0].message.content
            print(f"Got response: {answer}")

            # 4. 发送响应头
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            # 5. 发送响应内容
            response_data = {
                "response": answer
            }
            response_json = json.dumps(response_data)
            print(f"Sending response: {response_json}")
            self.wfile.write(response_json.encode('utf-8'))
            print("Response sent successfully")

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({"error": str(e)})
                self.wfile.write(error_response.encode('utf-8'))
            except:
                print("Failed to send error response")
                traceback.print_exc()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8233):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    print("Starting server with API key:", "***" + ZHIPUAI_API_KEY[-4:])
    run_server() 