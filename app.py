import os
import json
import datetime
import time
import functools
import markdown
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_flash_messages'

# ================= 設定區 =================
SPREADSHEET_NAME = 'DiaryDB'  # 請確認與您的試算表名稱一致
CREDENTIALS_FILE = 'credentials.json'
MODEL_NAME = 'gemini-flash-latest' 

# 初始化 Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ================= 優化 4: Google Sheets 連線快取 =================
gc = None  # 全域變數，用來暫存連線物件

def get_sheet():
    global gc
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # 若 gc 還是空的，先建立第一次連線
    if gc is None:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        gc = gspread.authorize(creds)
    
    try:
        # 嘗試開啟試算表，測試連線是否還活著
        return gc.open(SPREADSHEET_NAME).sheet1
    except Exception:
        # 如果失敗 (例如 Token 過期)，就強制重新連線
        print("連線失效，正在重連 Google Sheets...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        gc = gspread.authorize(creds)
        return gc.open(SPREADSHEET_NAME).sheet1

def save_to_sheet(title, content, ai_result):
    try:
        sheet = get_sheet()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        corrections_str = json.dumps(ai_result.get('corrections', []), ensure_ascii=False)
        vocab_str = json.dumps(ai_result.get('vocabulary', []), ensure_ascii=False)
        
        row = [
            timestamp,
            title,
            content,
            ai_result.get('polished_version', ''),
            corrections_str,
            vocab_str,
            ai_result.get('comment', '')
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Sheet Error: {e}")
        return False

# ================= Helper: 自動重試裝飾器 =================
def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)
                    if "503" in error_msg or "429" in error_msg:
                        if x == retries:
                            print(f"達到最大重試次數，放棄。錯誤: {error_msg}")
                            raise e
                        sleep = (backoff_in_seconds * 2 ** x)
                        print(f"伺服器忙碌 ({error_msg})，{sleep} 秒後重試... (第 {x+1} 次)")
                        time.sleep(sleep)
                        x += 1
                    else:
                        raise e
        return wrapper
    return decorator

# ================= Helper: AI 處理邏輯 =================
SYSTEM_PROMPT = """
You are a unique English teacher. The user will input a diary entry.
Your goal is to maximize the user's writing experience with a specific persona.

**Your Persona & Rules:**
1.  **Corrections (Part 1):** List grammatical or vocabulary errors. 
    * **Tone:** Be casual and colloquial. Focus on fluency over strict textbook grammar.
    * **Style:** It is okay to use words like 'fxxk', 'shit', etc., if it makes the sentence sound more natural or expressive.
    * **Format:** Explain the fix in a spoken, reasonable manner (can be in Traditional Chinese or English).
2.  **Polished Version (Part 2):** Rewrite the entire diary from a Native English Speaker's perspective. Use diverse sentence structures and authentic idioms.
3.  **Comment (Part 3):** Give a short, personal response/opinion to the diary content (like a friend replying).
4.  **Vocabulary (Part 4):** Teach exactly 5 NEW words related to the diary content.
    * Avoid duplicates from common knowledge.
    * Must provide **Traditional Chinese (中文)** meaning.
    * Must provide an example sentence.

**Output Format:**
You MUST return the result in **STRICT JSON format**. Do not use markdown code blocks. Just the raw JSON string.
The JSON structure must be:
{
  "corrections": [
    {
      "original": "User's wrong phrase",
      "correction": "Better phrase",
      "explanation": "Your casual explanation here"
    }
  ],
  "polished_version": "The full native rewrite text...",
  "comment": "Your short personal reply...",
  "vocabulary": [
    {
      "word": "New Word",
      "meaning": "中文意思",
      "example": "Example sentence using the word."
    }
  ]
}
"""

@retry_with_backoff(retries=3)
def analyze_diary(content):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type='application/json',
                temperature=0.7,
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Critical Error: {e}")
        return None

# ================= Flask Routes =================
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            return render_template('index.html', error="請輸入日記內容！")
        
        # 1. AI 分析
        ai_result = analyze_diary(content)
        
        if ai_result:
            title = content[:30] + "..."
            
            # 2. 存檔
            if save_to_sheet(title, content, ai_result):
                ai_result['polished_html'] = markdown.markdown(ai_result['polished_version'])
                return render_template('result.html', entry=content, feedback=ai_result)
            else:
                return render_template('index.html', error="AI 分析成功，但寫入 Google Sheet 失敗。請檢查 credentials.json 權限。")
        else:
            return render_template('index.html', error="AI 目前忙線中，已重試但仍失敗，請稍後再試。")

    return render_template('index.html')

@app.route('/history')
def history():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        
        # ================= 優化 3: 限制只顯示最近 20 筆 =================
        # records 是 list of dicts，reversed() 反轉讓最新的在前面
        # [:20] 只取前 20 筆
        recent_records = list(reversed(records))[:20]
        
        return render_template('history.html', records=recent_records)
    except Exception as e:
        return f"讀取失敗: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)