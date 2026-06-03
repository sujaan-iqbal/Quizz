# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Clean account ID
    raw_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
    if '/accounts/' in raw_account_id:
        import re
        match = re.search(r'/accounts/([a-f0-9]+)', raw_account_id)
        if match:
            raw_account_id = match.group(1)
    CLOUDFLARE_ACCOUNT_ID = raw_account_id
    
    CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # USE SUPPORTED MODELS (NOT deprecated ones)
    # Option 1: Llama 3.1 8B (current, recommended)
    LLM_MODEL = '@cf/meta/llama-3.1-8b-instruct'
    
    # Option 2: Llama 3.3 70B (more capable, but slower on free tier)
    # LLM_MODEL = '@cf/meta/llama-3.3-70b-instruct'
    
    # Option 3: Mistral (good alternative)
    # LLM_MODEL = '@cf/mistral/mistral-7b-instruct-v0.1'
    
    # Option 4: Gemma (Google's model)
    # LLM_MODEL = '@cf/google/gemma-7b-it-lora'
    
    # Embedding model (still works)
    # EMBED_MODEL = '@cf/baai/bge-base-en-v1.5'  # 768 dimensions
    # OR for 384 dimensions:
    EMBED_MODEL = '@cf/baai/bge-small-en-v1.5'