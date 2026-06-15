import os
import json
import re
import math
import random
import requests
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from config import Config

class LLMService:
    def __init__(self):
        raw_account_id = Config.CLOUDFLARE_ACCOUNT_ID
        if not raw_account_id:
            print("❌ CLOUDFLARE_ACCOUNT_ID is not set in .env")
            self.account_id = None
        else:
            if "/accounts/" in str(raw_account_id):
                match = re.search(r"/accounts/([a-f0-9]+)", str(raw_account_id))
                self.account_id = match.group(1) if match else str(raw_account_id).split("/")[-1]
            else:
                self.account_id = str(raw_account_id).strip()

        self.api_token = Config.CLOUDFLARE_API_TOKEN
        self.llm_model = Config.LLM_MODEL
        self.embed_model = Config.EMBED_MODEL
        self.max_embed_chars = Config.MAX_EMBED_CHARS
        self.timeout = Config.LLM_TIMEOUT
        self.temperature = Config.LLM_TEMPERATURE
        self.max_tokens = Config.LLM_MAX_TOKENS

        print("✅ LLM Service initialized (Cloudflare for embeddings)")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.account_id or not self.api_token:
            print("❌ Missing Cloudflare credentials")
            return [[0.0] * 384 for _ in texts[:20]]

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.embed_model}"
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

        embeddings = []
        for i, text in enumerate(texts[:100]):
            try:
                print(f"  Generating embedding {i+1}/{min(len(texts), 100)}...")
                safe_text = text[: self.max_embed_chars]
                response = requests.post(url, headers=headers, json={"text": safe_text}, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", False):
                        embedding = result.get("result", {}).get("data", [])
                        if embedding and isinstance(embedding, list):
                            if isinstance(embedding[0], list):
                                embedding = embedding[0]
                            embeddings.append(embedding)
                            if i == 0:
                                print(f"  ✅ Embedding dimension: {len(embedding)}")
                        else:
                            embeddings.append([0.0] * 384)
                    else:
                        embeddings.append([0.0] * 384)
                else:
                    embeddings.append([0.0] * 384)
            except Exception as e:
                print(f"  ❌ Embedding exception: {e}")
                embeddings.append([0.0] * 384)

        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings

    def analyze_document(self, full_text: str) -> Dict:
        """Simple document analysis for deep dive"""
        return {
            "major_topics": [],
            "key_facts": [],
            "key_concepts": [],
            "cross_cutting_themes": [],
        }

    def generate_deep_dive_quiz(self, chunks: List[str], num_questions: int, document_analysis: Dict, existing_questions_text: Optional[List[str]] = None) -> List[Dict]:
        """Fallback deep dive generation"""
        return []