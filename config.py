import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 修改為讀取 GROQ_API_KEY
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_fallback_secret")
    
    # Google Sheets
    CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    SPREADSHEET_NAME = os.getenv("GOOGLE_SHEETS_NAME", "DiaryDB")
    
    # 更新為 Kimi 模型 (由 Groq 託管)
    MODEL_NAME = 'moonshotai/kimi-k2-instruct-0905'

    @staticmethod
    def validate():
        if not Config.GROQ_API_KEY:
            raise ValueError("缺少 GROQ_API_KEY，請檢查 .env 檔案")