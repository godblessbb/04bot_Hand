#!/usr/bin/env python3
import os
from groq import Groq

api_key = os.environ.get("GROQ_API_KEY")
print(f"API Key 长度: {len(api_key) if api_key else 0}")
print(f"API Key 前缀: {api_key[:10] if api_key else 'None'}")

if not api_key:
    print("错误: GROQ_API_KEY 环境变量未设置!")
    exit(1)

try:
    client = Groq(api_key=api_key)
    # 简单测试
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say 'API key works!'"}],
        max_tokens=10
    )
    print("✓ API 密钥有效!")
    print(f"响应: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ API 密钥无效或有其他错误: {e}")
