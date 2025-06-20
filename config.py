import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')  # Add this line
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')  # Add ElevenLabs API key
    UPLOAD_FOLDER = 'data/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # AI Model Configuration
    AI_MODEL = 'mixtral-8x7b-32768'  # Groq's fast model
    GEMINI_MODEL = 'gemini-1.5-flash'  # Gemini's fast model
    # Alternative models: 'llama2-70b-4096', 'gemma-7b-it' 