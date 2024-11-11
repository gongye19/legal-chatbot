from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os
import time
import traceback

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        start_time = time.time()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print(f"Request received. Content length: {content_length}")
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('message')
            query_length = len(query) if query else 0
            print(f"Query received. Length: {query_length}")

            if not query:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No message provided"}).encode())
                return

            print(f"Making API request at {time.time() - start_time:.2f}s")
            try:
                response = client.chat.completions.create(
                    model="glm-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    stream=False,
                    timeout=25  # 添加超时设置
                )

                answer = response.choices[0].message.content
                print(f"API response received at {time.time() - start_time:.2f}s")

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "response": answer,
                    "debug_info": {
                        "total_time": f"{time.time() - start_time:.2f}s",
                        "query_length": query_length,
                        "response_length": len(answer)
                    }
                }).encode())
                
            except Exception as api_error:
                print(f"API Error at {time.time() - start_time:.2f}s: {str(api_error)}")
                print(f"API Error traceback: {traceback.format_exc()}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "API Error",
                    "details": str(api_error),
                    "traceback": traceback.format_exc(),
                    "debug_info": {
                        "time_elapsed": f"{time.time() - start_time:.2f}s",
                        "query_length": query_length
                    }
                }).encode())

        except Exception as e:
            print(f"General Error at {time.time() - start_time:.2f}s: {str(e)}")
            print(f"General Error traceback: {traceback.format_exc()}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "General Error",
                "details": str(e),
                "traceback": traceback.format_exc(),
                "debug_info": {
                    "time_elapsed": f"{time.time() - start_time:.2f}s"
                }
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
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
            res.body = json.dumps({
                "error": "Method Not Allowed",
                "allowed_methods": ["POST", "OPTIONS"]
            })
    except Exception as e:
        print(f"Fatal Error: {str(e)}")
        print(f"Fatal Error traceback: {traceback.format_exc()}")
        res.status = 500
        res.body = json.dumps({
            "error": "Fatal Error",
            "details": str(e),
            "traceback": traceback.format_exc()
        })