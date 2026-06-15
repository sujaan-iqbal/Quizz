import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}
    
    # Supabase configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Cloudflare credentials
    CLOUDFLARE_ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    CLOUDFLARE_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    # LLM Configuration
    LLM_MODEL = os.environ.get('LLM_MODEL', '@cf/meta/llama-4-scout-17b-16e-instruct')
    EMBED_MODEL = os.environ.get('EMBED_MODEL', '@cf/baai/bge-small-en-v1.5')
    MAX_EMBED_CHARS = int(os.environ.get('MAX_EMBED_CHARS', 1800))
    LLM_TIMEOUT = int(os.environ.get('LLM_TIMEOUT', 90))
    LLM_TEMPERATURE = float(os.environ.get('LLM_TEMPERATURE', 0.3))
    LLM_MAX_TOKENS = int(os.environ.get('LLM_MAX_TOKENS', 1500))
    
    # Fallback models
    FALLBACK_MODELS = [
        '@cf/google/gemma-4-26b-a4b-it',
        '@cf/meta/llama-3.3-70b-instruct',
    ]
        # Hugging Face only (no fallbacks)
        
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    USE_HUGGINGFACE = os.environ.get('USE_HUGGINGFACE', 'true').lower() == 'true'
    HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN')
    HUGGINGFACE_MODEL = os.environ.get('HUGGINGFACE_MODEL', 'meta-llama/Llama-3.1-8B-Instruct')