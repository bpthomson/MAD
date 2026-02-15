import gspread
import json
import datetime
from google.oauth2.service_account import Credentials
from config import Config

class DBService:
    def __init__(self):
        self.gc = None
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

    def _get_connection(self):
        if self.gc is None:
            try:
                creds = Credentials.from_service_account_file(
                    Config.CREDENTIALS_FILE, 
                    scopes=self.scope
                )
                self.gc = gspread.authorize(creds)
            except Exception as e:
                print(f"Auth Error: {e}")
                raise e
        
        try:
            return self.gc.open(Config.SPREADSHEET_NAME).sheet1
        except Exception:
            print("連線重試中...")
            creds = Credentials.from_service_account_file(
                Config.CREDENTIALS_FILE, 
                scopes=self.scope
            )
            self.gc = gspread.authorize(creds)
            return self.gc.open(Config.SPREADSHEET_NAME).sheet1

    def save_entry(self, title, content, ai_result, custom_date=None):
        try:
            sheet = self._get_connection()
            
            if custom_date:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                timestamp = f"{custom_date} {current_time}"
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            corrections_str = json.dumps(ai_result.get('corrections', []), ensure_ascii=False)
            vocab_str = json.dumps(ai_result.get('vocabulary', []), ensure_ascii=False)
            mood_str = json.dumps(ai_result.get('mood', {'label': 'Neutral', 'color': '#6c757d'}), ensure_ascii=False)
            
            row = [
                timestamp,
                title,
                content,
                ai_result.get('polished_version', ''),
                corrections_str,
                vocab_str,
                ai_result.get('comment', ''),
                mood_str  # 第 8 欄：情緒資料
            ]
            sheet.append_row(row)
            return True
        except Exception as e:
            print(f"DB Error (Save): {e}")
            return False

    def get_recent_diaries(self, limit=20):
        try:
            sheet = self._get_connection()
            records = sheet.get_all_records()
            return list(reversed(records))[:limit]
        except Exception as e:
            print(f"DB Error (Fetch): {e}")
            return []

    def get_calendar_data(self):
        """取得月曆資料：日期對應顏色 { 'YYYY-MM-DD': '#color' }"""
        try:
            sheet = self._get_connection()
            # 讀取所有資料 (建議未來改為 Cache 機制，目前先直接讀)
            rows = sheet.get_all_values()
            
            calendar_data = {}
            
            # 跳過標題列，從第 2 行開始
            for row in rows[1:]:
                if len(row) < 1: continue
                
                try:
                    # 解析日期
                    ts = row[0] 
                    date_part = ts.split(' ')[0]
                    
                    # 解析情緒顏色 (第 8 欄，索引 7)
                    color = '#6c757d' # 預設灰色
                    if len(row) >= 8 and row[7]:
                        try:
                            mood_data = json.loads(row[7])
                            color = mood_data.get('color', '#6c757d')
                        except:
                            pass
                    
                    # 存入字典 (如果同一天有多篇，後面會覆蓋前面，這符合顯示最新心情的邏輯)
                    calendar_data[date_part] = color
                    
                except Exception as e:
                    continue
            
            return calendar_data
        except Exception as e:
            print(f"DB Error (Get Calendar Data): {e}")
            return {}

db_service = DBService()