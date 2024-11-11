from http.server import BaseHTTPRequestHandler
from zhipuai import ZhipuAI
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY environment variable is not set")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
system_prompt = '''You are a helpful assistant in the field of law. You are designed to provide advice and assistance to users on legal matters.'''

# 创建线程池
executor = ThreadPoolExecutor(max_workers=4)

async def call_api(messages):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    response = await loop.run_in_executor(
        executor,
        lambda: client.chat.completions.create(
            model="glm-4",
            messages=messages,
            stream=False
        )
    )
    return response

def handler(request):
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
        # 解析请求体
        body = json.loads(request.get('body', '{}'))
        query = body.get('message')
        history = body.get('history', [])

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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(call_api(messages))
        loop.close()

        answer = response.choices[0].message.content

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
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }