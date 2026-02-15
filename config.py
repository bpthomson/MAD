import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_fallback_secret")
    
    # Google Sheets
    CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    SPREADSHEET_NAME = os.getenv("GOOGLE_SHEETS_NAME", "DiaryDB")
    
    # AI Model
    # 修正：直接使用具體的版本 ID，避免使用 'latest' 導致解析卡住
    MODEL_NAME = 'gemini-2.5-flash'

    @staticmethod
    def validate():
        if not Config.GEMINI_API_KEY:
            raise ValueError("缺少 GEMINI_API_KEY，請檢查 .env 檔案")