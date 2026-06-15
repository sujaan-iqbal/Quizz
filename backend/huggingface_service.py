

import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import os
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

class HuggingFaceService:
    def __init__(self, api_token: str, model: Optional[str] = None):
        # load .env if python-dotenv is available, otherwise rely on environment
        try:
            load_dotenv()
        except Exception:
            pass

        env_model = os.getenv("HUGGINGFACE_MODEL")

        if model is None and not env_model:
            raise ValueError("HUGGINGFACE_MODEL not set in environment and no model was provided")

        self.api_token = api_token
        self.model = model or env_model
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.timeout = 60
        print(f"✅ Hugging Face Service initialized | Model: {self.model}")

    def _call(self, prompt: str) -> Optional[str]:
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 400,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                verify=False 
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    return result.get("generated_text", "")
            elif response.status_code == 503:
                import time
                time.sleep(2)
                return self._call(prompt)
            else:
                print(f"  ❌ HF API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ HF error: {e}")
            return None

    def generate_question(self, chunk: str, difficulty: str, topic_hint: str = "") -> Optional[Dict]:
        difficulty_prompts = {
            "basic": "Create a SIMPLE factual recall question. The answer must be directly in the text.",
            "standard": "Create a COMPREHENSION question. Requires understanding, not just copying.",
            "advanced": "Create an ANALYTICAL question. Requires reasoning or cause-effect."
        }
        
        prompt = f"""{difficulty_prompts.get(difficulty, "standard")}

Text: {chunk[:600]}

Generate ONE multiple choice question. Return ONLY valid JSON:
{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "..."}}"""

        response = self._call(prompt)
        if not response:
            return None
            
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if all(k in data for k in ['question', 'options', 'correct']):
                    return data
            except:
                pass
        return None

    def generate_parallel(self, chunks: List[str], difficulty: str, topic_hint: str = "", max_workers: int = 3) -> List[Dict]:
        questions = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self.generate_question, c, difficulty, topic_hint) for c in chunks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    questions.append(result)
        return questions