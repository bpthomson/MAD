import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_fallback_secret")
    DIARY_PASSWORD = os.getenv("DIARY_PASSWORD", "default_password")
    
    CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    SPREADSHEET_NAME = os.getenv("GOOGLE_SHEETS_NAME", "DiaryDB")
    
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    MODEL_NAME = 'moonshotai/kimi-k2-instruct-0905'

    @staticmethod
    def validate():
        if not Config.GROQ_API_KEY:
            print("警告: 缺少 GROQ_API_KEY")