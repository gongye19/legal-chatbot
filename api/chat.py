from zhipuai import ZhipuAI
import json
import os
import traceback

# 获取 API 密钥
ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")

# 初始化客户端
def init_client():
    try:
        if not ZHIPUAI_API_KEY:
            print("Error: ZHIPUAI_API_KEY environment variable is not set")
            return None
        client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
        # 测试客户端是否正常工作
        test_response = client.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": "test"}],
            stream=False
        )
        if test_response:
            print("API client initialized successfully")
            return client
    except Exception as e:
        print(f"Error initializing ZhipuAI client: {e}")
        traceback.print_exc()
    return None

client = init_client()
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance on legal matters.'''

def handler(request):
    # 打印环境变量（不包含敏感信息）
    print("Environment variables:", {k: '***' if 'KEY' in k else v for k, v in os.environ.items()})
    
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

    try:
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
                    "details": "Please check environment variables configuration"
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
                    "details": "Please check server logs for details"
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
            print(f"Received response: {answer[:100]}...")

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
            traceback.print_exc()
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