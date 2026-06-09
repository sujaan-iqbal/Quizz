# backend/app.py
import os
import uuid
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile

from config import Config
from pdf_processor import PDFProcessor
from llm_service import LLMService
from supabase_service import SupabaseService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app"])

# Initialize services
pdf_processor = PDFProcessor()
llm_service = LLMService()
supabase_service = SupabaseService()

# ============================================
# HEALTH CHECK ENDPOINT (MAKE SURE THIS EXISTS)
# ============================================
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'pdf-quiz-backend',
        'model': Config.LLM_MODEL if hasattr(Config, 'LLM_MODEL') else 'qwen'
    })

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Upload and process PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    user_id = request.headers.get('X-User-Id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be PDF'}), 400
    
    try:
        session_id = str(uuid.uuid4())
        
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), f"{session_id}_{filename}")
        file.save(temp_path)
        
        # Extract text
        with open(temp_path, 'rb') as f:
            text = pdf_processor.extract_text(f)
        
        if not text or len(text.strip()) < 100:
            os.remove(temp_path)
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Create chunks
        chunks = pdf_processor.chunk_text(text)
        
        if len(chunks) < 2:
            os.remove(temp_path)
            return jsonify({'error': 'PDF text too short'}), 400
        
        # Save source to Supabase
        source_data = {
            'user_id': user_id,
            'type': 'pdf',
            'title': filename,
            'content': text[:5000],
            'metadata': {
                'original_filename': filename,
                'chunks_count': len(chunks),
                'session_id': session_id
            }
        }
        
        source = supabase_service.create_source(source_data)
        
        if not source:
            os.remove(temp_path)
            return jsonify({'error': 'Failed to save source'}), 500
        
        # Generate embeddings for chunks
        embeddings = llm_service.generate_embeddings(chunks)
        
        # Save chunks to Supabase
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            supabase_service.create_chunk({
                'source_id': source['id'],
                'chunk_index': i,
                'content': chunk,
                'embedding': embedding
            })
        
        # Create session record
        supabase_service.create_session({
            'session_id': session_id,
            'user_id': user_id,
            'source_id': source['id'],
            'chunks_count': len(chunks),
            'status': 'completed'
        })
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'session_id': session_id,
            'source_id': source['id'],
            'num_chunks': len(chunks),
            'preview': text[:500]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    """Generate quiz from uploaded PDF"""
    import traceback
    import random

    # Safely parse JSON body
    data = request.get_json(silent=True)
    if data is None:
        try:
            raw = request.data.decode('utf-8') if request.data else ''
            data = json.loads(raw) if raw else None
        except Exception as e:
            print('Failed to parse JSON body:', repr(request.data), e)
            data = None

    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    # Log incoming request
    try:
        print('generate_quiz called. headers=', dict(request.headers))
        print('generate_quiz payload=', json.dumps(data, ensure_ascii=False))
    except Exception:
        print('generate_quiz: could not serialize incoming payload for logging')

    source_id = data.get('source_id')
    user_id = request.headers.get('X-User-Id')
    difficulty = data.get('difficulty', 'standard')
    try:
        num_questions = min(int(data.get('num_questions', 5)), 30)
    except Exception:
        num_questions = 5
    topic_focus = data.get('topic_focus', '')

    if not source_id or not user_id:
        return jsonify({'error': 'Source ID and User ID required'}), 400

    try:
        # Get chunks from Supabase
        chunks_data = supabase_service.get_chunks(source_id)
        print(f'Fetched {len(chunks_data) if chunks_data else 0} chunks from Supabase for source_id={source_id}')
        
        if chunks_data and len(chunks_data) > 0:
            try:
                sample = chunks_data[:2]
                print('chunks sample:', sample)
            except Exception:
                print('chunks_data present but could not print sample')

        if not chunks_data:
            return jsonify({'error': 'No chunks found for this source'}), 404

        chunks = [c.get('content') for c in chunks_data if c.get('content')]
        
        print(f"📊 TOTAL CHUNKS AVAILABLE = {len(chunks)}")
        print(f"📊 REQUESTED QUESTIONS = {num_questions}")

        # Calculate optimal questions per chunk
        if len(chunks) >= num_questions:
            # More chunks than questions: select diverse chunks
            selected_chunks = random.sample(chunks, min(num_questions, len(chunks)))
            questions_per_chunk = 1
            use_batch_generation = False  # 1 question per chunk is fine
        else:
            # Fewer chunks than questions: use batch generation
            selected_chunks = random.sample(chunks, len(chunks))
            questions_per_chunk = max(2, (num_questions // len(chunks)) + 1)
            use_batch_generation = True  # Multiple questions per chunk
        
        print(f"📊 Selected {len(selected_chunks)} chunks")
        if use_batch_generation:
            print(f"📊 Using batch generation: {questions_per_chunk} questions per chunk")

        # Track generated questions
        existing_questions_text = []
        questions = []
        
        # Shuffle chunks for variety
        random.shuffle(selected_chunks)
        
        for idx, chunk in enumerate(selected_chunks):
            if len(questions) >= num_questions:
                break
                
            try:
                # Ensure chunk is a string
                if not isinstance(chunk, str):
                    try:
                        chunk = str(chunk)
                    except Exception:
                        print(f'Skipping non-string chunk at index {idx}')
                        continue
                
                remaining = num_questions - len(questions)
                
                if use_batch_generation:
                    # Generate multiple questions in one API call
                    batch_size = min(questions_per_chunk, remaining)
                    print(f"  Generating {batch_size} questions from chunk {idx + 1}/{len(selected_chunks)}...")
                    
                    batch_questions = llm_service.generate_questions(
                        chunk,
                        difficulty,
                        count=batch_size,
                        topic_hint=topic_focus,
                        existing_questions=existing_questions_text
                    )
                    
                    if batch_questions:
                        for q in batch_questions:
                            if len(questions) >= num_questions:
                                break
                            questions.append(q)
                            existing_questions_text.append(q['question'])
                        
                        print(f"  ✅ Added {len(batch_questions)} questions from batch (total: {len(questions)})")
                    else:
                        print(f"  ⚠️ Batch generation failed for chunk {idx + 1}, falling back to single generation")
                        # Fallback: generate one at a time
                        for _ in range(batch_size):
                            if len(questions) >= num_questions:
                                break
                            question = llm_service.generate_question(
                                chunk, difficulty, topic_focus,
                                existing_questions=existing_questions_text
                            )
                            if question:
                                questions.append(question)
                                existing_questions_text.append(question['question'])
                else:
                    # Generate single question per chunk
                    print(f"  Generating question {len(questions) + 1}/{num_questions} from chunk {idx + 1}/{len(selected_chunks)}")
                    
                    question = llm_service.generate_question(
                        chunk, 
                        difficulty, 
                        topic_focus,
                        existing_questions=existing_questions_text
                    )
                    
                    if question:
                        questions.append(question)
                        existing_questions_text.append(question['question'])
                        print(f"  ✅ Question {len(questions)}: {question['question'][:80]}...")
                    else:
                        print(f"  ⚠️ Failed to generate question from chunk {idx + 1}")
                        
            except Exception as e:
                print(f'Error generating question for chunk index {idx}: {e}')
                import traceback as _tb
                _tb.print_exc()

        print(f"✅ Generated {len(questions)}/{num_questions} questions")

        if not questions:
            return jsonify({'error': 'Failed to generate questions (LLM returned none)'}), 500

        # If still short, try filling remaining with single questions from random chunks
        if len(questions) < num_questions:
            print(f"⚠️ Only got {len(questions)}/{num_questions} questions, filling remaining...")
            remaining = num_questions - len(questions)
            
            for attempt in range(remaining * 3):
                if len(questions) >= num_questions:
                    break
                    
                try:
                    chunk = random.choice(chunks)
                    if not isinstance(chunk, str):
                        chunk = str(chunk)
                    
                    print(f"  Retry {attempt + 1}: generating additional question...")
                    question = llm_service.generate_question(
                        chunk,
                        difficulty,
                        topic_focus,
                        existing_questions=existing_questions_text
                    )
                    
                    if question:
                        questions.append(question)
                        existing_questions_text.append(question['question'])
                        print(f"  ✅ Additional question {len(questions)}: {question['question'][:80]}...")
                        
                except Exception as e:
                    print(f'Error in retry {attempt + 1}: {e}')

        print(f"📊 Final question count: {len(questions)}/{num_questions}")

        # Save quiz to Supabase
        quiz_data = {
            'source_id': source_id,
            'user_id': user_id,
            'difficulty': difficulty,
            'topic_focus': topic_focus,
            'questions': questions,
            'total_questions': len(questions)
        }

        quiz = supabase_service.create_quiz(quiz_data)

        return jsonify({
            'quiz_id': quiz['id'] if quiz else None,
            'questions': questions,
            'total': len(questions)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500
        
@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    """Submit quiz answers and save results"""
    data = request.json
    quiz_id = data.get('quiz_id')
    user_id = request.headers.get('X-User-Id')
    answers = data.get('answers', {})
    questions = data.get('questions', [])
    
    if not quiz_id or not user_id:
        return jsonify({'error': 'Quiz ID and User ID required'}), 400
    
    # Calculate score
    score = 0
    for i, q in enumerate(questions):
        if answers.get(str(i)) == q.get('correct'):
            score += 1
    
    total = len(questions)
    percentage = (score / total) * 100 if total > 0 else 0
    
    # Save attempt
    attempt_data = {
        'quiz_id': quiz_id,
        'user_id': user_id,
        'answers': answers,
        'score': score,
        'total_questions': total,
        'percentage': percentage
    }
    
    attempt = supabase_service.create_attempt(attempt_data)
    
    return jsonify({
        'attempt_id': attempt['id'] if attempt else None,
        'score': score,
        'total': total,
        'percentage': percentage
    })

@app.route('/api/user/quizzes', methods=['GET'])
def get_user_quizzes():
    """Get user's quiz history"""
    user_id = request.headers.get('X-User-Id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    quizzes = supabase_service.get_user_quizzes(user_id)
    
    return jsonify({'quizzes': quizzes})

# ============================================
# ROOT ENDPOINT (for testing)
# ============================================
@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'PDF Quiz API is running', 'endpoints': ['/api/health', '/api/upload', '/api/generate-quiz', '/api/submit-quiz']})

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)