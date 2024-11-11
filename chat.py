# api/chat.py
from zhipuai import ZhipuAI
import json
import os

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

def handle_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

def handle(request):
    """
    Vercel serverless function handler
    """
    try:
        # 解析请求体
        body = json.loads(request.get('body', '{}'))
        query = body.get('message')
        history = body.get('history', [])

        if not query:
            return {
                "statusCode": 400,
                "headers": handle_cors_headers(),
                "body": json.dumps({"error": "No message provided"})
            }

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

        # 调用 API
        response = client.chat.completions.create(
            model="glm-4",
            messages=messages,
            stream=False
        )

        answer = response.choices[0].message.content

        return {
            "statusCode": 200,
            "headers": handle_cors_headers(),
            "body": json.dumps({"response": answer})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": handle_cors_headers(),
            "body": json.dumps({"error": str(e)})
        }

def handler(request, context):
    """
    Main handler function for Vercel
    """
    if request.get('method', '').upper() == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": handle_cors_headers(),
            "body": ""
        }
    
    if request.get('method', '').upper() != 'POST':
        return {
            "statusCode": 405,
            "headers": handle_cors_headers(),
            "body": json.dumps({"error": "Method Not Allowed"})
        }

    return handle(request)