import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
api_token = os.getenv('CLOUDFLARE_API_TOKEN')

# Clean account ID
if '/accounts/' in account_id:
    import re
    match = re.search(r'/accounts/([a-f0-9]+)', account_id)
    if match:
        account_id = match.group(1)

print(f"Account ID: {account_id}")

# Test with Llama 3.1 (current model)
models_to_test = [
    '@cf/meta/llama-3.1-8b-instruct',
    '@cf/mistral/mistral-7b-instruct-v0.1',
    '@cf/google/gemma-7b-it-lora'
]

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

prompt = "Say 'Hello, Cloudflare AI is working!'"

for model in models_to_test:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 100
    }
    
    print(f"\nTesting model: {model}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Response: {result.get('result', {}).get('response', 'No response')[:100]}")
            print(f"✅ This model works! Use: {model}")
            break
        else:
            print(f"❌ Failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")