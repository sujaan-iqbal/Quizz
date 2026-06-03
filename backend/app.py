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
    data = request.json
    source_id = data.get('source_id')
    user_id = request.headers.get('X-User-Id')
    difficulty = data.get('difficulty', 'standard')
    num_questions = min(data.get('num_questions', 5), 20)
    topic_focus = data.get('topic_focus', '')
    
    if not source_id or not user_id:
        return jsonify({'error': 'Source ID and User ID required'}), 400
    
    # Get chunks from Supabase
    chunks_data = supabase_service.get_chunks(source_id)
    
    if not chunks_data:
        return jsonify({'error': 'No chunks found for this source'}), 404
    
    chunks = [c['content'] for c in chunks_data]
    
    # Select chunks based on topic focus
    if topic_focus and len(chunks) > num_questions:
        import random
        selected_chunks = random.sample(chunks, min(num_questions, len(chunks)))
    else:
        selected_chunks = chunks[:num_questions]
    
    # Generate questions
    questions = []
    for chunk in selected_chunks:
        question = llm_service.generate_question(chunk, difficulty, topic_focus)
        if question:
            questions.append(question)
        
        if len(questions) >= num_questions:
            break
    
    if not questions:
        return jsonify({'error': 'Failed to generate questions'}), 500
    
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