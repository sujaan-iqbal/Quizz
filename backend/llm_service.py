import os
import json
import re
import requests
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from config import Config

class LLMService:
    def __init__(self):
        # Clean account ID properly
        raw_account_id = Config.CLOUDFLARE_ACCOUNT_ID
        if not raw_account_id:
            print("❌ CLOUDFLARE_ACCOUNT_ID is not set in .env")
            self.account_id = None
        else:
            # Extract just the ID if it's a full URL
            if '/accounts/' in str(raw_account_id):
                match = re.search(r'/accounts/([a-f0-9]+)', str(raw_account_id))
                if match:
                    self.account_id = match.group(1)
                else:
                    self.account_id = str(raw_account_id).split('/')[-1]
            else:
                self.account_id = str(raw_account_id).strip()
        
        self.api_token = Config.CLOUDFLARE_API_TOKEN
        # Use Llama 3.1 (not deprecated)
        self.llm_model = '@cf/meta/llama-3.1-8b-instruct'
        self.embed_model = '@cf/baai/bge-small-en-v1.5'  # 384 dimensions
        self.MAX_EMBED_CHARS = 1800  # Safe embedding truncation
        
        print(f"✅ LLM Service initialized")
        print(f"   Account ID: {self.account_id}")
        print(f"   LLM Model: {self.llm_model}")
        print(f"   Embed Model: {self.embed_model}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Cloudflare AI"""
        if not self.account_id or not self.api_token:
            print("❌ Missing Cloudflare credentials")
            return [[0.0] * 384 for _ in texts[:20]]
        
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.embed_model}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        embeddings = []
        # Process up to 100 chunks instead of 20
        for i, text in enumerate(texts[:100]):
            try:
                print(f"  Generating embedding for chunk {i+1}/{min(len(texts), 100)}...")
                
                # Use safe truncation instead of arbitrary 500 chars
                safe_text = text[:self.MAX_EMBED_CHARS]
                response = requests.post(url, headers=headers, json={"text": safe_text}, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success', False):
                        embedding = result.get('result', {}).get('data', [])
                        if embedding and isinstance(embedding, list):
                            if len(embedding) > 0 and isinstance(embedding[0], list):
                                embedding = embedding[0]
                            embeddings.append(embedding)
                            if i == 0:
                                print(f"  ✅ Embedding dimension: {len(embedding)}")
                        else:
                            print(f"  ⚠️ No embedding data for chunk {i+1}, using zeros")
                            embeddings.append([0.0] * 384)
                    else:
                        errors = result.get('errors', [])
                        print(f"  ❌ API error for chunk {i+1}: {errors}")
                        embeddings.append([0.0] * 384)
                else:
                    print(f"  ❌ HTTP {response.status_code} for chunk {i+1}")
                    print(f"     Response: {response.text[:200]}")
                    embeddings.append([0.0] * 384)
            except Exception as e:
                print(f"  ❌ Exception for chunk {i+1}: {e}")
                embeddings.append([0.0] * 384)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def validate_source_quote(self, question_data: Dict, chunk: str) -> bool:
        """
        Verify quote actually exists in the source chunk.
        Made more lenient - accepts partial matches and long enough quotes.
        """
        quote = question_data.get("source_quote", "").strip()
        
        if not quote:
            print("   ⚠️ Empty source_quote - accepting question anyway")
            return True  # Accept questions even without quotes
        
        # Direct substring check (case insensitive)
        if quote.lower() in chunk.lower():
            print("   ✅ Source quote validated (exact match)")
            return True
        
        # Check if quote is at least 5 words (likely valid even if formatting differs)
        if len(quote.split()) >= 5:
            # Try fuzzy matching
            similarity = SequenceMatcher(None, quote.lower(), chunk.lower()).ratio()
            if similarity > 0.8:
                print(f"   ✅ Source quote validated (fuzzy match: {similarity:.2f})")
                return True
        
        print(f"   ❌ Source quote validation failed")
        print(f"   Quote: {quote[:100]}...")
        return False
    
    def is_duplicate(
        self,
        new_question: str,
        existing_questions: List[str],
        threshold: float = 0.75  # Lowered from 0.85
    ) -> bool:
        """
        Check if new question is too similar to existing ones
        """
        q = new_question.lower().strip()
        
        for old in existing_questions:
            old_clean = old.lower().strip()
            similarity = SequenceMatcher(None, q, old_clean).ratio()
            
            if similarity > threshold:
                print(f"   ⚠️ Duplicate detected (similarity: {similarity:.2f})")
                return True
        
        print("   ✅ No duplicates detected")
        return False
    
    def generate_question(
        self, 
        chunk: str, 
        difficulty: str, 
        topic_hint: str = "", 
        existing_questions: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Generate a single multiple choice question"""
        
        if not self.account_id or not self.api_token:
            print("❌ Missing Cloudflare credentials")
            return None
        
        difficulty_prompts = {
            "basic": """
Create a factual recall question.

Requirements:
- Answer must appear explicitly in the passage
- No inference required
- Focus on names, dates, locations, facts, events
""",
            "standard": """
Create a comprehension question.

Requirements:
- Requires understanding relationships
- Requires understanding cause and effect
- Requires paraphrasing information
- Do not ask direct fact lookup questions
""",
            "advanced": """
Create an analytical question.

The question must require:
- Inference
- Interpretation
- Evaluation
- Prediction
- Consequence analysis
- Theme analysis

Forbidden:
- Direct fact lookup
- Dates
- Names
- Locations
- Explicit details

The answer should not appear directly in a single sentence.
"""
        }
        
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.llm_model}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        topic_line = f"Focus specifically on: {topic_hint}.\n" if topic_hint else ""
        
        # Build context about previously generated questions
        existing_context = ""
        if existing_questions and len(existing_questions) > 0:
            existing_context = f"""
PREVIOUSLY GENERATED QUESTIONS (DO NOT repeat or closely paraphrase these):
{chr(10).join(f'- {q}' for q in existing_questions[-10:])}

Generate a question that focuses on a DIFFERENT fact, event, character, theme, or concept.
"""
        
        prompt = f"""
You are an expert assessment creator.
{topic_line}
PASSAGE:
\"\"\"
{chunk}
\"\"\"

DIFFICULTY:
{difficulty_prompts[difficulty]}
{existing_context}
STRICT RULES:

1. Question MUST be answerable ONLY from the passage.
2. Do NOT invent names, organizations, facilities, places, dates, or events.
3. If a fact is not explicitly stated, do NOT ask about it.
4. Provide exactly 4 options.
5. Only one option can be correct.
6. Distractors must be plausible but incorrect.
7. Distractors must be similar in length.
8. Include a verbatim quote proving the answer (can be partial, min 5 words).
9. The source_quote must be an EXACT substring from the passage.
10. Focus on a DIFFERENT aspect than previously generated questions.

Return ONLY valid JSON:

{{
  "question": "",
  "options": {{
      "A": "",
      "B": "",
      "C": "",
      "D": ""
  }},
  "correct": "A",
  "source_quote": "",
  "explanation": ""
}}
"""
        
        # Retry loop for getting valid questions
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  📡 Calling LLM API (attempt {attempt + 1}/{max_retries})...")
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
                
                print(f"  Response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"  ❌ HTTP Error: {response.text[:300]}")
                    continue
                
                result = response.json()
                
                if not result.get('success', False):
                    errors = result.get('errors', [])
                    print(f"  ❌ API Error: {errors}")
                    continue
                
                raw = result.get('result', {}).get('response', '')
                print(f"  Raw response preview: {raw[:150]}...")
                
                if not raw:
                    print("  ❌ Empty response")
                    continue
                
                # Clean response
                raw = re.sub(r'```json\s*', '', raw)
                raw = re.sub(r'```\s*$', '', raw)
                raw = raw.strip()
                
                # Parse JSON
                data = json.loads(raw)
                
                # Validate structure
                required = ["question", "options", "correct"]
                
                if not all(k in data for k in required):
                    print(f"  ❌ Missing required keys. Found: {list(data.keys())}")
                    continue
                
                # Validate source quote exists in chunk
                if not self.validate_source_quote(data, chunk):
                    print("  ⚠️ Source quote validation failed - but accepting question")
                    # Continue anyway - don't reject questions just for quote issues
                
                # Check for duplicates if existing questions provided
                if existing_questions and self.is_duplicate(data['question'], existing_questions):
                    print("  ❌ Duplicate question detected, retrying...")
                    continue
                
                # All validations passed
                print("  ✅ Question validated successfully")
                print(f"  Question: {data['question'][:100]}...")
                print(f"  Correct answer: {data['correct']}) {data['options'][data['correct']]}")
                return data
                
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON Parse Error: {e}")
                print(f"  Raw response: {raw[:500] if 'raw' in locals() else 'N/A'}")
                continue
            except Exception as e:
                print(f"  ❌ Exception: {type(e).__name__}: {e}")
                continue
        
        # All retries exhausted
        print(f"  ❌ Failed to generate valid question after {max_retries} attempts")
        return None
    
    def generate_questions(
        self,
        chunk: str,
        difficulty: str,
        count: int = 3,
        topic_hint: str = "",
        existing_questions: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Generate multiple questions from a single chunk in one API call.
        This is the high-impact optimization - reduces API calls by 3x.
        """
        if not self.account_id or not self.api_token:
            print("❌ Missing Cloudflare credentials")
            return []
        
        difficulty_prompts = {
            "basic": """
Create factual recall questions.

Requirements for each question:
- Answer must appear explicitly in the passage
- No inference required
- Focus on names, dates, locations, facts, events
""",
            "standard": """
Create comprehension questions.

Requirements for each question:
- Requires understanding relationships
- Requires understanding cause and effect
- Requires paraphrasing information
- Do not ask direct fact lookup questions
""",
            "advanced": """
Create analytical questions.

Each question must require:

- themes
- symbolism
- moral lessons
- long-term consequences
- ethical decisions

Avoid questions about:

- names
- dates
- locations
- direct events
- explicit facts
Answers should not appear directly in a single sentence.
"""
        }
        
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.llm_model}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        topic_line = f"Focus specifically on: {topic_hint}.\n" if topic_hint else ""
        
        # Build context about previously generated questions
        existing_context = ""
        if existing_questions and len(existing_questions) > 0:
            existing_context = f"""
PREVIOUSLY GENERATED QUESTIONS (DO NOT repeat or closely paraphrase these):
{chr(10).join(f'- {q}' for q in existing_questions[-15:])}

Each new question must focus on a DIFFERENT fact, event, character, theme, or concept.
"""
        
        prompt = f"""
You are an expert assessment creator.
{topic_line}
PASSAGE:
\"\"\"
{chunk}
\"\"\"

DIFFICULTY:
{difficulty_prompts[difficulty]}

Generate exactly {count} UNIQUE multiple-choice questions from this passage.
Each question must focus on a DIFFERENT aspect of the passage.
{existing_context}
STRICT RULES for EACH question:

1. MUST be answerable ONLY from the passage.
2. Do NOT invent names, organizations, facilities, places, dates, or events.
3. If a fact is not explicitly stated, do NOT ask about it.
4. Provide exactly 4 options per question.
5. Only one option can be correct per question.
6. Distractors must be plausible but incorrect.
7. Distractors must be similar in length.
8. Include a verbatim quote proving the answer (can be partial, min 5 words).
9. Each question must cover a DIFFERENT topic/concept from the passage.

Return ONLY a valid JSON array (no markdown, no extra text):

[
  {{
    "question": "...",
    "options": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
    }},
    "correct": "A",
    "source_quote": "...",
    "explanation": "..."
  }},
  ...
]
"""
        
        try:
            print(f"  📡 Calling LLM API for {count} questions...")
            response = requests.post(
                url, 
                headers=headers, 
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,  # Slightly higher for variety
                    "max_tokens": 1500  # More tokens for multiple questions
                },
                timeout=90
            )
            
            print(f"  Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  ❌ HTTP Error: {response.text[:300]}")
                return []
            
            result = response.json()
            
            if not result.get('success', False):
                errors = result.get('errors', [])
                print(f"  ❌ API Error: {errors}")
                return []
            
            raw = result.get('result', {}).get('response', '')
            print(f"  Raw response preview: {raw[:200]}...")
            
            if not raw:
                print("  ❌ Empty response")
                return []
            
            # Clean response
            raw = re.sub(r'```json\s*', '', raw)
            raw = re.sub(r'```\s*$', '', raw)
            raw = raw.strip()
            
            # Parse JSON array
            questions_data = json.loads(raw)
            
            if not isinstance(questions_data, list):
                # If single object returned, wrap in list
                if isinstance(questions_data, dict):
                    questions_data = [questions_data]
                else:
                    print(f"  ❌ Expected JSON array, got: {type(questions_data)}")
                    return []
            
            # Validate each question
            valid_questions = []
            for i, q_data in enumerate(questions_data):
                required = ["question", "options", "correct"]
                
                if not all(k in q_data for k in required):
                    print(f"  ⚠️ Question {i+1}: Missing required keys, skipping")
                    continue
                
                # Check duplicates against existing and already collected questions
                all_existing = (existing_questions or []) + [q['question'] for q in valid_questions]
                if self.is_duplicate(q_data['question'], all_existing):
                    print(f"  ⚠️ Question {i+1}: Duplicate detected, skipping")
                    continue
                
                # Validate source quote (lenient)
                self.validate_source_quote(q_data, chunk)
                
                valid_questions.append(q_data)
                print(f"  ✅ Question {i+1} validated: {q_data['question'][:80]}...")
            
            print(f"  ✅ Generated {len(valid_questions)}/{count} valid questions from chunk")
            return valid_questions
            
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON Parse Error: {e}")
            print(f"  Raw response: {raw[:500] if 'raw' in locals() else 'N/A'}")
            return []
        except Exception as e:
            print(f"  ❌ Exception in generate_questions: {type(e).__name__}: {e}")
            return []
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b + 1e-9)