from supabase import create_client, Client
from config import Config
import json
import time

class SupabaseService:
    def __init__(self):
        print(f"Connecting to Supabase at: {Config.SUPABASE_URL}")
        try:
            self.supabase: Client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY
            )
            # Test connection with a simple query
            self.supabase.table('sources').select('count').limit(1).execute()
            print("✅ Supabase connected successfully")
        except Exception as e:
            print(f"❌ Supabase connection error: {e}")
            print("   Please check your SUPABASE_URL and SUPABASE_KEY in .env")
            self.supabase = None
    
    def _retry_operation(self, operation, max_retries=3, delay=1):
        """Retry an operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                if self.supabase is None:
                    print("❌ Supabase not connected")
                    return None
                return operation()
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Retry {attempt + 1}/{max_retries} after error: {e}")
                    time.sleep(delay * (2 ** attempt))
                else:
                    print(f"❌ Operation failed after {max_retries} attempts: {e}")
                    return None
    
    def create_source(self, data: dict) -> dict | None:
        """Create a new source"""
        return self._retry_operation(
            lambda: self.supabase.table('sources').insert(data).execute().data[0]
        )
    
    def create_chunk(self, data: dict) -> dict | None:
        """Create a new PDF chunk"""
        return self._retry_operation(
            lambda: self.supabase.table('pdf_chunks').insert(data).execute().data[0]
        )
    
    def get_chunks(self, source_id: str) -> list:
        """Get all chunks for a source"""
        result = self._retry_operation(
            lambda: self.supabase.table('pdf_chunks')\
                .select('*')\
                .eq('source_id', source_id)\
                .order('chunk_index')\
                .execute()
        )
        return result.data if result else []
    
    def create_session(self, data: dict) -> dict | None:
        """Create a PDF processing session"""
        return self._retry_operation(
            lambda: self.supabase.table('pdf_sessions').insert(data).execute().data[0]
        )
    
    def create_quiz(self, data: dict) -> dict | None:
        """Create a new quiz"""
        return self._retry_operation(
            lambda: self.supabase.table('quizzes').insert(data).execute().data[0]
        )
    
    def create_attempt(self, data: dict) -> dict | None:
        """Create a quiz attempt"""
        return self._retry_operation(
            lambda: self.supabase.table('quiz_attempts').insert(data).execute().data[0]
        )
    
    def get_user_quizzes(self, user_id: str) -> list:
        """Get all quizzes for a user"""
        result = self._retry_operation(
            lambda: self.supabase.table('quizzes')\
                .select('*, sources(title)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
        )
        return result.data if result else []