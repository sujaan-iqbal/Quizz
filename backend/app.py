import os, time
import uuid
import json
import random
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from pdf_processor import PDFProcessor
from llm_service import LLMService
from supabase_service import SupabaseService
from groq_service import GroqService

app = Flask(__name__)
app.config.from_object(Config)

# Enhanced CORS configuration
CORS(app, 
     origins=["http://localhost", "http://localhost:80", "http://localhost:5173", "http://localhost:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "X-User-Id", "Authorization", "Accept"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Initialize services
pdf_processor = PDFProcessor()
llm_service = LLMService()  # For embeddings and deep dive
supabase_service = SupabaseService()
groq_service = GroqService(Config.GROQ_API_KEY)

DIFFICULTY_MAP = {
    "basic": "basic",
    "intermediate": "standard",
    "advanced": "advanced",
    "standard": "standard",
    "deep_dive": "deep_dive",
}

# ------------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------------
@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    return jsonify({
        "status": "healthy",
        "service": "pdf-quiz-backend",
        "active_llm": "groq (llama-3.1-8b-instant)",
    })

# ------------------------------------------------------------------
# UPLOAD
# ------------------------------------------------------------------
@app.route("/api/upload", methods=["POST", "OPTIONS"])
def upload_pdf():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    user_id = request.headers.get("X-User-Id")

    print(f"📥 Upload request - User ID: {user_id}, File: {file.filename if file else 'None'}")

    if not user_id:
        return jsonify({"error": "User ID required"}), 401
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "File must be PDF"}), 400

    try:
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), f"{session_id}_{filename}")
        file.save(temp_path)

        with open(temp_path, "rb") as f:
            text = pdf_processor.extract_text(f)

        if not text or len(text.strip()) < 100:
            os.remove(temp_path)
            return jsonify({"error": "Could not extract text from PDF"}), 400

        chunks = pdf_processor.chunk_text(text)

        if len(chunks) < 2:
            os.remove(temp_path)
            return jsonify({"error": "PDF text too short"}), 400

        document_analysis = llm_service.analyze_document(text)

        source_data = {
            "user_id": user_id,
            "type": "pdf",
            "title": filename,
            "content": text[:5000],
            "metadata": {
                "original_filename": filename,
                "chunks_count": len(chunks),
                "session_id": session_id,
                "document_analysis": document_analysis,
            },
        }

        source = supabase_service.create_source(source_data)

        if not source:
            os.remove(temp_path)
            return jsonify({"error": "Failed to save source"}), 500

        embeddings = llm_service.generate_embeddings(chunks)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            supabase_service.create_chunk({
                "source_id": source["id"],
                "chunk_index": i,
                "content": chunk,
                "embedding": embedding,
            })

        supabase_service.create_session({
            "session_id": session_id,
            "user_id": user_id,
            "source_id": source["id"],
            "chunks_count": len(chunks),
            "status": "completed",
        })

        os.remove(temp_path)

        return jsonify({
            "session_id": session_id,
            "source_id": source["id"],
            "num_chunks": len(chunks),
            "preview": text[:500],
            "document_analysis": document_analysis,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# GENERATE QUIZ
# ------------------------------------------------------------------
@app.route("/api/generate-quiz", methods=["POST", "OPTIONS"])
def generate_quiz():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json(silent=True)
    if data is None:
        try:
            raw = request.data.decode("utf-8") if request.data else ""
            data = json.loads(raw) if raw else None
        except Exception as e:
            print("Failed to parse JSON body:", e)
            data = None

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    print("generate_quiz payload:", json.dumps(data, ensure_ascii=False))

    source_id   = data.get("source_id")
    user_id     = request.headers.get("X-User-Id")
    difficulty  = data.get("difficulty", "standard").lower()
    topic_focus = data.get("topic_focus", "")

    try:
        num_questions = min(int(data.get("num_questions", 5)), 30)
    except Exception:
        num_questions = 5

    if not source_id or not user_id:
        return jsonify({"error": "Source ID and User ID required"}), 400

    try:
        chunks_data = supabase_service.get_chunks(source_id)
        print(f"Fetched {len(chunks_data) if chunks_data else 0} chunks for source_id={source_id}")

        if not chunks_data:
            return jsonify({"error": "No chunks found for this source"}), 404

        chunks = [c.get("content") for c in chunks_data if c.get("content")]
        print(f"📊 Total chunks available: {len(chunks)}")
        print(f"📊 Requested questions:    {num_questions}")
        print(f"📊 Difficulty:             {difficulty}")

        if difficulty == "deep_dive":
            questions = _generate_deep_dive(chunks, num_questions, source_id, topic_focus)
        else:
            questions = _generate_standard_quiz(chunks, num_questions, difficulty, topic_focus)

        print(f"📊 Final question count: {len(questions)}/{num_questions}")

        if not questions:
            return jsonify({"error": "Failed to generate questions (LLM returned none)"}), 500

        quiz_data = {
            "source_id":      source_id,
            "user_id":        user_id,
            "difficulty":     difficulty,
            "topic_focus":    topic_focus,
            "questions":      questions,
            "total_questions": len(questions),
        }
        quiz = supabase_service.create_quiz(quiz_data)

        return jsonify({
            "quiz_id":   quiz["id"] if quiz else None,
            "questions": questions,
            "total":     len(questions),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

# ------------------------------------------------------------------
# GENERATION HELPERS
# ------------------------------------------------------------------
def _generate_standard_quiz(chunks: list, num_questions: int, difficulty: str, topic_focus: str) -> list:
    """Generate questions using Groq with parallel processing"""
    import random
    selected_chunks = random.sample(chunks, min(num_questions, len(chunks)))
    
    print(f"🚀 Using Groq (llama-3.1-8b-instant) for {difficulty} questions")
    questions = groq_service.generate_parallel(
        selected_chunks[:num_questions],
        difficulty,
        topic_focus,
        max_workers=3
    )
    
    return questions[:num_questions]

def _generate_deep_dive(chunks: list, num_questions: int, source_id: str, topic_focus: str) -> list:
    """Deep dive questions using Groq with Bloom's Taxonomy"""
    import random
    selected_chunks = random.sample(chunks, min(num_questions, len(chunks)))
    
    print(f"🚀 Using Groq for DEEP DIVE (Synthesis/Evaluation level)")
    questions = []
    for chunk in selected_chunks[:num_questions]:
        q = groq_service.generate_deep_dive_question(chunk, topic_focus)
        if q:
            questions.append(q)
            # Add delay between deep dive questions for better quality
            time.sleep(0.5)
    
    return questions

# ------------------------------------------------------------------
# SUBMIT QUIZ
# ------------------------------------------------------------------
@app.route("/api/submit-quiz", methods=["POST", "OPTIONS"])
def submit_quiz():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.json
    quiz_id   = data.get("quiz_id")
    user_id   = request.headers.get("X-User-Id")
    answers   = data.get("answers", {})
    questions = data.get("questions", [])

    if not quiz_id or not user_id:
        return jsonify({"error": "Quiz ID and User ID required"}), 400

    score = sum(1 for i, q in enumerate(questions) if answers.get(str(i)) == q.get("correct"))
    total = len(questions)
    percentage = (score / total * 100) if total > 0 else 0

    attempt = supabase_service.create_attempt({
        "quiz_id": quiz_id,
        "user_id": user_id,
        "answers": answers,
        "score": score,
        "total_questions": total,
        "percentage": percentage,
    })

    return jsonify({
        "attempt_id": attempt["id"] if attempt else None,
        "score": score,
        "total": total,
        "percentage": percentage,
    })

# ------------------------------------------------------------------
# USER QUIZ HISTORY
# ------------------------------------------------------------------
@app.route("/api/user/quizzes", methods=["GET", "OPTIONS"])
def get_user_quizzes():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 401
    quizzes = supabase_service.get_user_quizzes(user_id)
    return jsonify({"quizzes": quizzes})

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "PDF Quiz API is running",
        "endpoints": ["/api/health", "/api/upload", "/api/generate-quiz", "/api/submit-quiz"],
    })

def _build_cors_preflight_response():
    """Build CORS preflight response"""
    response = jsonify({"message": "CORS preflight"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, X-User-Id, Authorization, Accept")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)