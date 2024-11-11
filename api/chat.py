from zhipuai import ZhipuAI
import json
import os
import traceback

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")

def init_client():
    if not ZHIPUAI_API_KEY:
        print("Error: ZHIPUAI_API_KEY environment variable is not set")
        return None
    try:
        return ZhipuAI(api_key=ZHIPUAI_API_KEY)
    except Exception as e:
        print(f"Error initializing ZhipuAI client: {e}")
        return None

client = init_client()
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance on legal matters.'''

def handler(request):
    try:
        print(f"Handling request with method: {request.get('method')}")
        
        # 处理 OPTIONS 请求
        if request.get('method') == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Content-Type": "application/json"
                }
            }

        # 验证 API 密钥
        if not ZHIPUAI_API_KEY:
            print("API key is missing")
            return {
                "statusCode": 401,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "API key is not configured",
                    "details": "Please set ZHIPUAI_API_KEY environment variable"
                })
            }

        # 验证客户端初始化
        if not client:
            print("Client initialization failed")
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "Failed to initialize API client",
                    "details": "Check API key configuration"
                })
            }

        # 解析请求体
        body = request.get('body', '{}')
        print(f"Request body: {body}")
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "Invalid JSON in request body",
                    "details": str(e)
                })
            }

        query = data.get('message')
        if not query:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "No message provided",
                    "details": "The 'message' field is required"
                })
            }

        history = data.get('history', [])
        messages = [{"role": "system", "content": system_prompt}]
        recent_history = history[-4:]
        
        for msg in recent_history:
            if msg.get('isComplete', True):
                messages.append({
                    "role": "user" if msg["sender"] == "user" else "assistant",
                    "content": msg["text"]
                })

        messages.append({"role": "user", "content": query})
        print(f"Sending messages to API: {messages}")

        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                stream=False,
                timeout=25
            )
            answer = response.choices[0].message.content
            print(f"Received response: {answer[:100]}...")  # 只打印前100个字符

            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"response": answer})
            }

        except Exception as api_error:
            print(f"API call error: {api_error}")
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "API call failed",
                    "details": str(api_error)
                })
            }

    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }