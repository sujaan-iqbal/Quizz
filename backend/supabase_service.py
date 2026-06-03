# backend/supabase_service.py
from supabase import create_client, Client
from config import Config
import json

class SupabaseService:
    def __init__(self):
        print(f"Connecting to Supabase at: {Config.SUPABASE_URL}")
        self.supabase: Client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )
        print("✅ Supabase connected successfully")
    
    def create_source(self, data: dict) -> dict | None:
        """Create a new source"""
        try:
            result = self.supabase.table('sources').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating source: {e}")
            return None
    
    def create_chunk(self, data: dict) -> dict | None:
        """Create a new PDF chunk"""
        try:
            result = self.supabase.table('pdf_chunks').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating chunk: {e}")
            return None
    
    def get_chunks(self, source_id: str) -> list:
        """Get all chunks for a source"""
        try:
            result = self.supabase.table('pdf_chunks')\
                .select('*')\
                .eq('source_id', source_id)\
                .order('chunk_index')\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting chunks: {e}")
            return []
    
    def create_session(self, data: dict) -> dict | None:
        """Create a PDF processing session"""
        try:
            result = self.supabase.table('pdf_sessions').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    def create_quiz(self, data: dict) -> dict | None:
        """Create a new quiz"""
        try:
            result = self.supabase.table('quizzes').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating quiz: {e}")
            return None
    
    def create_attempt(self, data: dict) -> dict | None:
        """Create a quiz attempt"""
        try:
            result = self.supabase.table('quiz_attempts').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating attempt: {e}")
            return None
    
    def get_user_quizzes(self, user_id: str) -> list:
        """Get all quizzes for a user"""
        try:
            result = self.supabase.table('quizzes')\
                .select('*, sources(title)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting quizzes: {e}")
            return []