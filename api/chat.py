from zhipuai import ZhipuAI
import json
import os
import traceback

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    print("Warning: ZHIPUAI_API_KEY is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY) if ZHIPUAI_API_KEY else None
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

def handler(request):
    try:
        print("Received request:", request)
        
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

        if not ZHIPUAI_API_KEY:
            raise ValueError("ZHIPUAI_API_KEY is not set in environment variables")

        if not client:
            raise ValueError("ZhipuAI client is not initialized")

        # 解析请求体
        body = request.get('body', '{}')
        print("Request body:", body)
        
        data = json.loads(body)
        query = data.get('message')
        history = data.get('history', [])

        if not query:
            raise ValueError("No message provided in request")

        # 构建消息历史
        messages = [{"role": "system", "content": system_prompt}]
        recent_history = history[-4:]
        
        for msg in recent_history:
            if msg.get('isComplete', True):
                messages.append({
                    "role": "user" if msg["sender"] == "user" else "assistant",
                    "content": msg["text"]
                })

        messages.append({"role": "user", "content": query})
        print("Prepared messages:", messages)

        # 调用 API
        response = client.chat.completions.create(
            model="glm-4",
            messages=messages,
            stream=False,
            timeout=25
        )

        answer = response.choices[0].message.content
        print("Got response:", answer)

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

    except Exception as e:
        print("Error occurred:", str(e))
        print("Traceback:")
        traceback.print_exc()
        
        error_message = f"Server error: {str(e)}"
        if "ZHIPUAI_API_KEY" in str(e):
            error_message = "API key not configured properly"

        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": error_message,
                "details": traceback.format_exc()
            })
        }