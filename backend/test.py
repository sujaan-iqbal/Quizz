import requests
import os
from config import Config

def test_model(model_name):
    url = f"https://api.cloudflare.com/client/v4/accounts/{Config.CLOUDFLARE_ACCOUNT_ID}/ai/run/{model_name}"
    headers = {
        "Authorization": f"Bearer {Config.CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    response = requests.post(
        url,
        headers=headers,
        json={
            "messages": [{"role": "user", "content": "Say 'hello'"}],
            "max_tokens": 10,
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"✅ {model_name} - WORKING")
        return True
    else:
        print(f"❌ {model_name} - FAILED: {response.status_code}")
        return False

# Test models
models = [
    '@cf/meta/llama-3.3-70b-instruct',
    '@cf/meta/llama-4-scout-17b-16e-instruct', 
    '@cf/google/gemma-4-26b-a4b-it',
    '@cf/mistral/mistral-7b-instruct-v0.2-fp8',
]

print("Testing Cloudflare models...")
for model in models:
    test_model(model)