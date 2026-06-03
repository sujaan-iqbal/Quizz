import os
import json
import re
import requests
from typing import List, Dict, Optional
from config import Config


class LLMService:
    def __init__(self):
        self.account_id = Config.CLOUDFLARE_ACCOUNT_ID
        self.api_token = Config.CLOUDFLARE_API_TOKEN
        self.llm_model = Config.LLM_MODEL
        self.embed_model = Config.EMBED_MODEL

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Cloudflare AI"""
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.embed_model}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        embeddings = []
        for text in texts[:20]:  # Limit to 20 chunks for performance
            try:
                response = requests.post(url, headers=headers, json={"text": text}, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get('result', {}).get('data', [])
                    if embedding:
                        embeddings.append(embedding[0] if isinstance(embedding, list) else embedding)
                    else:
                        embeddings.append([0.0] * 384)
                else:
                    embeddings.append([0.0] * 384)
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0] * 384)

        return embeddings

    def generate_question(self, chunk: str, difficulty: str, topic_hint: str = "") -> Optional[Dict]:
        """Generate a single multiple choice question"""

        difficulty_prompts = {
            "basic": "Ask a simple factual recall question. The answer should appear almost verbatim in the text.",
            "standard": "Ask a comprehension question that requires understanding or paraphrasing the text.",
            "advanced": "Ask an analytical question that requires reasoning about implications or comparing concepts."
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.llm_model}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        topic_line = f"Focus specifically on: {topic_hint}.\n" if topic_hint else ""

        prompt = f"""{topic_line}Difficulty level: {difficulty_prompts[difficulty]}

        Generate ONE multiple-choice question from this passage:

        PASSAGE:
        {chunk[:1500]}

        Requirements:
        - Question must be answerable only from the passage
        - All options must be plausible
        - Only one correct answer
        - Explanation must cite the passage

        Return ONLY valid JSON in this exact format (no markdown, no extra text):
        {{"question": "Your question here?", "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}}, "correct": "A", "explanation": "Explanation citing the passage"}}"""

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                raw = result.get('result', {}).get('response', '')

                # Clean response
                raw = re.sub(r'```json\s*', '', raw)
                raw = re.sub(r'```\s*$', '', raw)
                raw = raw.strip()

                # Parse JSON
                data = json.loads(raw)

                # Validate structure
                if all(k in data for k in ['question', 'options', 'correct']):
                    data['source_chunk'] = chunk[:500]
                    return data

        except Exception as e:
            print(f"Question generation error: {e}")

        return None

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b + 1e-9)
