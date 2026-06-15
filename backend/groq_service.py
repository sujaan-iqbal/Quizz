import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from groq import Groq

class GroqService:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        self.request_count = 0
        self.last_request_time = 0
        print(f"✅ Groq Service initialized | Model: {self.model}")

    def _is_quality_question(self, question_data: Dict, difficulty: str) -> bool:
        """Validate question quality based on difficulty level"""
        q = question_data.get('question', '').lower()
        
        # Reject questions that are too short
        if len(q.split()) < 8:
            return False
        
        # Level-specific quality checks
        if difficulty == "basic":
            # Basic should have recall stems
            recall_stems = ['what is', 'who', 'when', 'where', 'which', 'how many']
            if not any(stem in q for stem in recall_stems):
                return False
                
        elif difficulty == "standard":
            # Standard should avoid simple recall
            recall_stems = ['what is', 'who', 'when', 'where', 'which', 'how many']
            if any(stem in q for stem in recall_stems):
                return False
            
            # Must have comprehension stems
            comprehension_stems = ['why did', 'what caused', 'what led to', 'why was', 'how did', 'what role', 'contribute', 'purpose', 'significant', 'turning point']
            if not any(stem in q for stem in comprehension_stems):
                return False
            
            # Reject evaluation-level questions (those belong in Advanced)
            evaluation_stems = ['which factor most', 'compare', 'contrast', 'evaluate', 'most significant factor']
            if any(stem in q for stem in evaluation_stems):
                return False
                
        elif difficulty == "advanced":
            # Advanced should have analysis stems
            analysis_stems = [
                'which factor', 'contributed more', 'compare', 'contrast', 
                'most significant', 'primary', 'critical turning point', 
                'indirectly lead', 'consequence', 'advantage', 'difference',
                'pattern', 'missing', 'rank', 'depend', 'evidence', 'critical step'
            ]
            if not any(stem in q for stem in analysis_stems):
                if len(q.split()) < 12:
                    return False
                    
        elif difficulty == "deep_dive":
            # Deep Dive should have synthesis/evaluation stems
            deep_stems = [
                'if', 'counterfactual', 'tradeoff', 'system', 'reinforce', 
                'best supported', 'least supported', 'broader lesson', 
                'recurring theme', 'work together', 'what if', 'feedback',
                'criticism', 'limitation', 'assumption', 'predict', 'combination',
                'alternative interpretation', 'second-order', 'unintended',
                'beneficial despite', 'knowledge gap', 'analogous', 'strategy'
            ]
            if not any(stem in q for stem in deep_stems):
                if len(q.split()) < 15:
                    return False
        
        return True

    def generate_question(self, chunk: str, difficulty: str, topic_hint: str = "", retry_count: int = 0) -> Optional[Dict]:
        """Generate questions based on Bloom's Taxonomy levels"""
        
        # Rate limiting
        current_time = time.time()
        if self.request_count >= 8 and (current_time - self.last_request_time) < 60:
            wait_time = 3
            print(f"  ⏳ Rate limit approaching, waiting {wait_time}s...")
            time.sleep(wait_time)
            self.request_count = 0
        
        # ============================================================
        # BLOOM'S TAXONOMY PROMPTS FOR EACH DIFFICULTY LEVEL
        # ============================================================
        
            if difficulty == "basic":
                prompt = f"""You are creating a BASIC (Remember level) question for a quiz.

RULE: The answer must be found in a SINGLE sentence. This is pure recall.

CONTENT:
{chunk[:600]}

QUESTION TYPES (use ONLY these stems):
- Who [person/entity from text]?
- What [fact/concept from text]?
- When [time/date from text]?
- Where [location from text]?
- Which [item/option from text]?
- How many [number from text]?

REQUIREMENTS:
- Test a SPECIFIC fact from the text (name, date, number, definition, event)
- Answer must be VERBATIM in the text
- ONE correct answer, THREE plausible distractors
- Distractors should be related to the topic but clearly wrong

FORBIDDEN:
- "Why" questions
- "How did" questions
- Any question requiring understanding or connection of ideas

Return ONLY this JSON format:
{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "Direct quote from text showing the exact answer"}}"""

        elif difficulty == "standard":
            prompt = f"""You are creating a STANDARD (Comprehension level) question for a quiz.

    DEFINITION: Standard tests UNDERSTANDING. The student must grasp WHY something happened, WHAT it meant, or HOW things connect.

    RULE: Answer requires understanding MULTIPLE sentences or a CAUSE-EFFECT relationship.

    CONTENT:
    {chunk[:600]}

    QUESTION TYPES (use these EXACT patterns – rotate evenly):

    TYPE 1 – CAUSE & EFFECT (30%):
    - Why did [event/change from text] happen?
    - What caused [outcome from text] to occur?
    - What led to [development from text]?

    TYPE 2 – SIGNIFICANCE (25%):
    - Why was [X from text] significant/important?
    - What made [X from text] a turning point?
    - Why did [X from text] matter?

    TYPE 3 – BASIC CONNECTIONS (25%):
    - How did [X from text] affect [Y from text]?
    - What role did [X from text] play in [Y from text]?
    - How did [X from text] contribute to [Y from text]?

    TYPE 4 – PURPOSE/REASON (20%):
    - What was the purpose of [X from text]?
    - Why was [X from text] created/established?
    - What problem did [X from text] solve?

    REQUIREMENTS:
    - Test UNDERSTANDING, not recall
    - Answer requires grasping relationships or causes from the text
    - Distractors must be PLAUSIBLE but wrong (based on common misconceptions)
    - Avoid yes/no questions

    FORBIDDEN:
    - Fact recall (Who, What, When, Where, How many) – those are BASIC
    - Multi-factor evaluation – that's ADVANCED
    - Counterfactuals or tradeoffs – that's DEEP DIVE
    - Questions answerable from a single sentence

    GOOD STANDARD QUESTIONS (examples with placeholders – adapt to actual text):
    ✓ "Why did [significant event from text] happen?"
    ✓ "What caused [important outcome from text] to occur?"
    ✓ "How did [concept A from text] affect [concept B from text]?"
    ✓ "Why was [key development from text] significant?"
    ✓ "What role did [element from text] play in [process from text]?"

    BAD STANDARD QUESTIONS:
    ✗ Fact recall questions (Who, What, When, Where)
    ✗ Multi-factor evaluation questions
    ✗ Counterfactual or tradeoff questions

    Return ONLY this JSON format:
    {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "Explain the cause-effect or significance relationship from the text"}}"""

        elif difficulty == "advanced":
            prompt = f"""You are creating an ADVANCED (Analyze level) question for a quiz.

RULE: The answer requires CONNECTING MULTIPLE IDEAS and ANALYZING relationships, causes, or significance.

CONTENT:
{chunk[:600]}

QUESTION TYPES (rotate among these 12 types – use placeholders from actual text, avoid repetition):

TYPE 1 – CAUSE ANALYSIS:
- Which factor most contributed to [outcome from text]?
- What was the primary driver of [development from text]?
- Which element played the strongest role in [result from text]?

TYPE 2 – COMPARATIVE ANALYSIS:
- Which contributed more to [result]: [concept A] or [concept B]?
- How did [approach A] differ from [approach B] in achieving [goal]?
- What advantage did [X] have over [Y] in [context]?

TYPE 3 – CONSEQUENCE ANALYSIS:
- What was the most significant consequence of [event/decision]?
- Which outcome resulted directly from [action]?
- What long-term effect did [development] create?

TYPE 4 – MULTI-STEP REASONING:
- How did [event A] indirectly lead to [event B]?
- What chain of events connected [X] to [Y]?
- Which sequence best explains how [X] resulted in [Y]?

TYPE 5 – DECISION ANALYSIS:
- Why was [choice] selected instead of [alternative]?
- What reasoning likely justified [decision]?
- Which factor most influenced [decision-maker] to choose [X]?

TYPE 6 – PRIORITIZATION:
- Which problem was most urgent based on the text?
- What should have been addressed first according to the passage?
- Which concern took priority and why?

TYPE 7 – PATTERN IDENTIFICATION:
- What pattern emerges from [examples in the text]?
- Which trend is most clearly supported by the evidence?
- What common characteristic appears across [items/events]?

TYPE 8 – GAP ANALYSIS:
- What is missing from the explanation provided?
- Which aspect is not adequately addressed?
- What assumption does the text make without evidence?

TYPE 9 – HIERARCHY ANALYSIS:
- Which factor was most important? Second most?
- How would you rank the [items/concepts] by [criteria]?
- What order best represents [sequence/priority from text]?

TYPE 10 – DEPENDENCY ANALYSIS:
- Which outcome depended most heavily on [prerequisite]?
- What condition was necessary for [result] to occur?
- How did [X] and [Y] depend on each other?

TYPE 11 – EVIDENCE WEIGHTING:
- Which piece of evidence most strongly supports [claim]?
- What information provides the weakest support for [conclusion]?
- Which data point is most critical to [argument]?

TYPE 12 – PROCESS BREAKDOWN:
- What was the critical step in [process from text]?
- Which stage had the greatest impact on [outcome]?
- Where in the process did [key change] occur?

REQUIREMENTS:
- Test ANALYSIS, not just understanding
- Require comparing, contrasting, ranking, or evaluating factors
- Create challenging options that require careful reasoning
- Distractors should be plausible but miss key nuances
- Each question should use a DIFFERENT type from the list above

FORBIDDEN:
- Questions answerable from 2 sentences or less
- Simple cause-effect (that's Standard level)
- "What was the result" patterns (too simple)

Return ONLY this JSON format:
{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "Show the analytical reasoning chain from the text", "cognitive_level": "analyze", "question_type": "cause_analysis|comparative|consequence|multi_step|decision|prioritization|pattern|gap|hierarchy|dependency|evidence|process"}}"""

        else:  # deep_dive
            prompt = f"""You are creating a DEEP DIVE (Synthesize + Evaluate level) question for a quiz.

CRITICAL: This is the HIGHEST difficulty level. Do NOT create Basic/Standard/Advanced questions here.

CONTENT:
{chunk[:600]}

QUESTION TYPES (rotate among these 15 types – use placeholders from actual text, NEVER repeat a type in the same quiz):

TYPE 1 – SYSTEM THINKING:
- How did [concept A], [concept B], and [concept C] work together to produce [outcome]?
- What feedback loops existed between [X] and [Y]?
- How would changing [component] affect the entire system described?

TYPE 2 – COUNTERFACTUAL REASONING:
- If [event] had not occurred, which outcome would most likely change?
- What would have happened differently if [condition] was reversed?
- How would the outcome differ if [key factor] was removed?

TYPE 3 – TRADEOFF ANALYSIS:
- What tradeoff emerged when [decision/action] was taken?
- What was gained and what was lost by choosing [X] over [Y]?
- Which sacrifice was most significant in achieving [goal]?

TYPE 4 – SYNTHESIS:
- How did seemingly unrelated factors [X], [Y], and [Z] combine to create [result]?
- What overarching principle explains multiple outcomes in the text?
- How do [A], [B], and [C] reinforce each other?

TYPE 5 – EVIDENCE EVALUATION:
- Which claim about [topic] is best supported by the passage?
- Which explanation is LEAST supported by the evidence presented?
- What counterargument would most weaken the author's conclusion?

TYPE 6 – THEME ANALYSIS:
- What broader lesson about [domain] can be drawn from the passage?
- What recurring theme connects [event A], [event B], and [event C]?
- What universal principle does this case illustrate?

TYPE 7 – CRITICAL EVALUATION:
- What is the strongest criticism of the approach described?
- Which limitation of the [method/solution] is most concerning?
- What assumption, if false, would invalidate the conclusion?

TYPE 8 – PREDICTION/EXTENSION:
- Based on patterns in the text, what is most likely to happen next?
- If the trend continues, what outcome would you predict?
- What future development would most logically follow?

TYPE 9 – MULTI-FACTOR CAUSATION:
- Which combination of factors best explains [complex outcome]?
- How did [economic], [social], and [political] factors interact?
- What was the minimal set of conditions needed for [result]?

TYPE 10 – COMPETING EXPLANATIONS:
- Which explanation for [phenomenon] is most convincing given the evidence?
- Why would someone argue the opposite conclusion?
- What alternative interpretation of the data is plausible?

TYPE 11 – IMPLICATION TRACING:
- What are the second-order effects of [decision]?
- How might [event] indirectly affect [unrelated area]?
- What unintended consequence is most likely to result?

TYPE 12 – VALUE JUDGMENT:
- Which outcome was most beneficial despite its costs?
- What tradeoff was most justified given the circumstances?
- How would you evaluate the success of [initiative] based on the text?

TYPE 13 – META-COGNITION:
- What knowledge gap does the passage reveal?
- What would an expert need to know beyond this text?
- What question does the passage leave unanswered?

TYPE 14 – ANALOGY TRANSFER:
- What other situation follows the same pattern described?
- Which scenario is most analogous to [situation in text]?
- What principle from the text applies to a different domain?

TYPE 15 – STRATEGIC RECOMMENDATION:
- Based on the text, what strategy would be most effective for [similar goal]?
- What advice would you give someone facing [similar challenge]?
- Which approach should be prioritized and why?

REQUIREMENTS:
- Test SYNTHESIS or EVALUATION of multiple concepts
- Require connecting 3+ ideas from the text
- Challenge assumptions or consider alternatives
- Create sophisticated options requiring deep understanding
- Each question must use a DIFFERENT type from the list above

COMPLETELY FORBIDDEN:
- "What relationship exists between..." (too vague)
- "What can be inferred about..." (overused)
- "How did X contribute..." (this is Standard/Advanced level)
- Questions answerable from 3 sentences or less
- Repeating the same question type

Return ONLY this JSON format:
{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "Detailed synthesis/evaluation reasoning with text citations", "cognitive_level": "synthesize|evaluate", "question_type": "system_thinking|counterfactual|tradeoff|synthesis|evidence_evaluation|theme|critical_evaluation|prediction|multi_factor|competing_explanations|implication|value_judgment|meta_cognition|analogy|strategic", "topic_tag": "main theme from text"}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.45,
                max_tokens=750
            )
            
            self.request_count += 1
            self.last_request_time = time.time()
            
            result = response.choices[0].message.content
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if all(k in data for k in ['question', 'options', 'correct']):
                    # Quality check based on difficulty
                    if self._is_quality_question(data, difficulty):
                        return data
                    elif retry_count < 1:
                        print(f"  ⚠️ Question failed quality check for {difficulty}, retrying...")
                        time.sleep(1)
                        return self.generate_question(chunk, difficulty, topic_hint, retry_count + 1)
                    else:
                        print(f"  ⚠️ Quality check failed twice, returning anyway")
                        return data
            return None
        except Exception as e:
            if "rate_limit" in str(e).lower():
                print(f"  ⏳ Rate limit hit, waiting 5 seconds...")
                time.sleep(5)
                return self.generate_question(chunk, difficulty, topic_hint, retry_count)
            print(f"  ❌ Groq error: {e}")
            return None

    def generate_deep_dive_question(self, chunk: str, topic_focus: str = "") -> Optional[Dict]:
        """Expert-level questions for deep dive"""
        return self.generate_question(chunk, "deep_dive", topic_focus)

    def generate_parallel(self, chunks: List[str], difficulty: str, topic_hint: str = "", max_workers: int = 3) -> List[Dict]:
        """Generate questions in parallel"""
        questions = []
        
        # Shuffle chunks for variety
        import random
        shuffled_chunks = random.sample(chunks, min(len(chunks), len(chunks)))
        
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self.generate_question, c, difficulty, topic_hint) for c in shuffled_chunks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    questions.append(result)
        return questions