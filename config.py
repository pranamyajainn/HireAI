import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    UPLOAD_FOLDER = 'data/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # AI Model Configuration
    AI_MODEL = 'mixtral-8x7b-32768'  # Groq's fast model
    # Alternative models: 'llama2-70b-4096', 'gemma-7b-it' 