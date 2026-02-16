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
        # 快取機制：將資料暫存在伺服器記憶體中
        self._records_cache = None
        self._last_fetch_time = None
        self._cache_ttl = datetime.timedelta(minutes=15) # 每 15 分鐘自動刷新一次

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

    def _fetch_all_records(self, force=False):
        """內部方法：取得所有資料 (優先讀快取)"""
        now = datetime.datetime.now()
        
        # 如果快取有效，直接回傳 (0秒延遲)
        if not force and self._records_cache is not None:
            if self._last_fetch_time and (now - self._last_fetch_time) < self._cache_ttl:
                return self._records_cache

        try:
            sheet = self._get_connection()
            self._records_cache = sheet.get_all_records()
            self._last_fetch_time = now
            print(f"DEBUG: Cache refreshed. {len(self._records_cache)} records loaded.")
            return self._records_cache
        except Exception as e:
            print(f"DB Error (Fetch All): {e}")
            return []

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
                mood_str
            ]
            sheet.append_row(row)
            
            # 重要：寫入新日記後，讓快取失效，確保下次讀到最新的
            self._records_cache = None 
            return True
        except Exception as e:
            print(f"DB Error (Save): {e}")
            return False

    def get_recent_diaries(self, limit=20):
        records = self._fetch_all_records()
        return list(reversed(records))[:limit]

    def search_diaries(self, query):
        """全文搜尋功能"""
        if not query:
            return self.get_recent_diaries()
        
        records = self._fetch_all_records()
        query = query.lower().strip()
        results = []
        
        # 倒序搜尋
        for row in reversed(records):
            # 將標題、內容、評語串在一起搜尋
            text_corpus = (
                str(row.get('Title', '')) + 
                str(row.get('Original', '')) + 
                str(row.get('Comment', ''))
            ).lower()
            
            if query in text_corpus:
                results.append(row)
        
        return results

    def get_calendar_data(self):
        """從快取解析月曆顏色"""
        records = self._fetch_all_records()
        calendar_data = {}
        
        for row in records:
            try:
                # 處理 Timestamp 欄位 (假設是第一欄或 key='Timestamp')
                # gspread get_all_records 使用 header 作為 key
                # 請確保 Google Sheet 第一列包含 'Timestamp' 和 'Mood'
                ts = str(row.get('Timestamp', '') or list(row.values())[0]) 
                date_part = ts.split(' ')[0]
                
                # 解析情緒顏色
                mood_raw = row.get('Mood', '') 
                # 如果找不到 Mood key (例如舊資料)，使用預設色
                
                color = '#6c757d'
                if mood_raw:
                    try:
                        if isinstance(mood_raw, str) and mood_raw.startswith('{'):
                            mood_data = json.loads(mood_raw)
                            color = mood_data.get('color', '#6c757d')
                    except:
                        pass
                
                calendar_data[date_part] = color
            except:
                continue
                
        return calendar_data

db_service = DBService()