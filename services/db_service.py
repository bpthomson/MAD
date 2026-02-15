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
        """取得 Google Sheets 連線"""
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
        """儲存日記 (支援自訂日期)"""
        try:
            sheet = self._get_connection()
            
            # 如果有提供 custom_date (YYYY-MM-DD)，則使用該日期加上當前時間
            # 如果沒有，則使用當前完整時間
            if custom_date:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                timestamp = f"{custom_date} {current_time}"
            else:
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

    def get_existing_dates(self):
        """取得所有已經寫過日記的日期 (YYYY-MM-DD)"""
        try:
            sheet = self._get_connection()
            # 只抓取第一欄 (Timestamp) 以提升效能
            timestamps = sheet.col_values(1)
            dates = set()
            
            # 跳過標題列 (假設第一列是標題)
            for ts in timestamps[1:]:
                try:
                    # 假設格式為 YYYY-MM-DD HH:MM:SS
                    date_part = ts.split(' ')[0]
                    dates.add(date_part)
                except:
                    continue
            
            return list(dates)
        except Exception as e:
            print(f"DB Error (Get Dates): {e}")
            return []

db_service = DBService()