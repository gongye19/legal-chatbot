# api/chat.py
from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

def handle_request(request_body):
    try:
        data = json.loads(request_body)
        query = data.get('message')
        history = data.get('history', [])

        if not query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No message provided"})
            }

        # 构建完整的消息历史
        messages = [{"role": "system", "content": system_prompt}]
        recent_history = history[-10:]
        
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
            stream=False  # Vercel 函数需要使用非流式响应
        )

        answer = response.choices[0].message.content

        return {
            "statusCode": 200,
            "body": json.dumps({"response": answer})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        }
    
    if event.get('httpMethod') != 'POST':
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }

    return handle_request(event.get('body', ''))