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
        self._records_cache = None
        self._last_fetch_time = None
        self._cache_ttl = datetime.timedelta(minutes=15)

    def _get_connection(self):
        if self.gc is None:
            try:
                # [雲端部署邏輯] 優先檢查環境變數中的 JSON 字串
                if Config.GOOGLE_CREDENTIALS_JSON:
                    print("Using Google Credentials from Environment Variable")
                    creds_dict = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
                    creds = Credentials.from_service_account_info(
                        creds_dict, 
                        scopes=self.scope
                    )
                else:
                    # [本地開發邏輯] 讀取實體檔案
                    print(f"Using Google Credentials from File: {Config.CREDENTIALS_FILE}")
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
            # 重試邏輯 (保持一致性)
            if Config.GOOGLE_CREDENTIALS_JSON:
                creds_dict = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            else:
                creds = Credentials.from_service_account_file(Config.CREDENTIALS_FILE, scopes=self.scope)
            
            self.gc = gspread.authorize(creds)
            return self.gc.open(Config.SPREADSHEET_NAME).sheet1

    def _fetch_all_records(self, force=False):
        now = datetime.datetime.now()
        if not force and self._records_cache is not None:
            if self._last_fetch_time and (now - self._last_fetch_time) < self._cache_ttl:
                return self._records_cache
        try:
            sheet = self._get_connection()
            self._records_cache = sheet.get_all_records()
            self._last_fetch_time = now
            return self._records_cache
        except Exception as e:
            print(f"DB Error (Fetch All): {e}")
            return []

    # --- [CRUD] 刪除功能 ---
    def delete_entry(self, timestamp):
        try:
            sheet = self._get_connection()
            cell = sheet.find(timestamp, in_column=1)
            if cell:
                sheet.delete_rows(cell.row)
                self._records_cache = None
                return True
            return False
        except Exception as e:
            print(f"Delete Error: {e}")
            return False

    # --- [CRUD] 更新功能 ---
    def update_entry(self, old_timestamp, title, content, ai_result, custom_date=None):
        try:
            sheet = self._get_connection()
            cell = sheet.find(old_timestamp, in_column=1)
            if not cell:
                return False
            
            if custom_date:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                new_timestamp = f"{custom_date} {current_time}"
            else:
                new_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            corrections_str = json.dumps(ai_result.get('corrections', []), ensure_ascii=False)
            vocab_str = json.dumps(ai_result.get('vocabulary', []), ensure_ascii=False)
            mood_str = json.dumps(ai_result.get('mood', {'label': 'Neutral', 'color': '#6c757d'}), ensure_ascii=False)
            
            row_data = [
                new_timestamp, 
                title, 
                content, 
                ai_result.get('polished_version', ''), 
                corrections_str, 
                vocab_str, 
                ai_result.get('comment', ''), 
                mood_str,
                ai_result.get('marked_html', '')
            ]
            
            # 更新該列 (A到I欄)
            sheet.update(range_name=f"A{cell.row}:I{cell.row}", values=[row_data])
            self._records_cache = None
            return True
        except Exception as e:
            print(f"Update Error: {e}")
            return False

    # --- [CRUD] 新增功能 ---
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
                mood_str,
                ai_result.get('marked_html', '')
            ]
            sheet.append_row(row)
            self._records_cache = None 
            return True
        except Exception as e:
            print(f"DB Error (Save): {e}")
            return False

    def _parse_row_data(self, row):
        new_row = row.copy()
        if 'Mood' in new_row and isinstance(new_row['Mood'], str):
            try:
                new_row['Mood'] = json.loads(new_row['Mood'])
            except:
                new_row['Mood'] = {'label': 'Neutral', 'color': '#6c757d'}
        return new_row

    def get_recent_diaries(self, limit=20):
        records = self._fetch_all_records()
        parsed_records = [self._parse_row_data(row) for row in list(reversed(records))[:limit]]
        return parsed_records

    def search_diaries(self, query):
        if not query: return self.get_recent_diaries()
        records = self._fetch_all_records()
        query = query.lower().strip()
        results = []
        for row in reversed(records):
            text_corpus = (str(row.get('Title', '')) + str(row.get('Original', '')) + str(row.get('Comment', ''))).lower()
            if query in text_corpus:
                results.append(self._parse_row_data(row))
        return results

    def get_entry(self, timestamp):
        records = self._fetch_all_records()
        for row in records:
            if str(row.get('Timestamp', '')) == timestamp:
                return row
        return None

    def get_calendar_data(self):
        records = self._fetch_all_records()
        calendar_data = {}
        for row in records:
            try:
                ts = str(row.get('Timestamp', '') or list(row.values())[0]) 
                date_part = ts.split(' ')[0]
                mood_raw = row.get('Mood', '') 
                color = '#6c757d'
                if mood_raw:
                    try:
                        if isinstance(mood_raw, str) and mood_raw.startswith('{'):
                            mood_data = json.loads(mood_raw)
                            color = mood_data.get('color', '#6c757d')
                    except: pass
                calendar_data[date_part] = color
            except: continue
        return calendar_data

    def get_context_for_ai(self, limit=3):
        try:
            records = self._fetch_all_records()
            recent = list(reversed(records))[:limit]
            context_list = []
            for row in recent:
                date = str(row.get('Timestamp', '')).split(' ')[0]
                summary = str(row.get('Title', ''))
                mood_label = ""
                mood_raw = row.get('Mood', '')
                if mood_raw and isinstance(mood_raw, str) and mood_raw.startswith('{'):
                     try:
                         mood_data = json.loads(mood_raw)
                         mood_label = f" (Mood: {mood_data.get('label', 'Neutral')})"
                     except: pass
                if summary and summary != "No Title":
                    context_list.append(f"- {date}{mood_label}: {summary}")
            return "\n".join(reversed(context_list))
        except Exception:
            return ""

db_service = DBService()