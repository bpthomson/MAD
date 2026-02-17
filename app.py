from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import markdown
import json
from config import Config
from services.ai_service import ai_service
from services.db_service import db_service

Config.validate()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        custom_date = request.form.get('date')
        old_timestamp = request.form.get('old_timestamp') # [新增] 檢查是否為編輯模式

        if not content:
            return render_template('index.html', error="請輸入日記內容！")
        
        past_context = db_service.get_context_for_ai(limit=3)
        ai_result = ai_service.analyze_diary(content, past_context)
        
        if ai_result:
            raw_polished = ai_result.get('polished_version', '')
            ai_result['polished_html'] = markdown.markdown(raw_polished)
            title = ai_result.get('title', content[:30] + "...")
            
            save_success = False
            try:
                # [新增] 判斷是「更新」還是「新增」
                if old_timestamp:
                    print(f"Updating entry: {old_timestamp}")
                    if db_service.update_entry(old_timestamp, title, content, ai_result, custom_date):
                        save_success = True
                else:
                    if db_service.save_entry(title, content, ai_result, custom_date):
                        save_success = True
            except Exception as e:
                print(f"Save Error: {e}")

            if not save_success:
                ai_result['system_warning'] = "注意：日記未成功寫入資料庫。"

            return render_template('result.html', entry=content, feedback=ai_result)
        else:
            return render_template('index.html', error="AI 分析失敗", content=content)

    return render_template('index.html')

# --- [新增] 編輯路由 ---
@app.route('/edit/<path:timestamp>')
def edit_entry(timestamp):
    entry = db_service.get_entry(timestamp)
    if not entry:
        return "Entry not found", 404
    
    # 處理日期格式，因為 input[type=date] 需要 YYYY-MM-DD
    ts = entry.get('Timestamp', '')
    date_val = ts.split(' ')[0] if ts else ''
    
    # 渲染首頁，但帶入舊資料
    return render_template('index.html', 
                           content=entry.get('Original', ''), 
                           date_value=date_val, 
                           old_timestamp=ts,
                           is_edit=True)

# --- [新增] 刪除路由 ---
@app.route('/delete/<path:timestamp>')
def delete_entry(timestamp):
    db_service.delete_entry(timestamp)
    return redirect('/history')

@app.route('/entry/<path:timestamp>')
def view_entry(timestamp):
    entry = db_service.get_entry(timestamp)
    if not entry:
        return "Entry not found", 404
    
    try:
        corrections = json.loads(entry.get('Corrections', '[]'))
        vocabulary = json.loads(entry.get('Vocabulary', '[]'))
        mood = json.loads(entry.get('Mood', '{}'))
    except:
        corrections, vocabulary, mood = [], [], {}

    marked_content = entry.get('MarkedHTML', entry.get('Original', ''))

    ai_result = {
        'mood': mood,
        'comment': entry.get('Comment', ''),
        'marked_html': marked_content, 
        'polished_html': markdown.markdown(entry.get('Polished', '')),
        'corrections': corrections,
        'vocabulary': vocabulary,
        'timestamp': timestamp # 傳入 timestamp 以便顯示編輯/刪除按鈕
    }

    return render_template('result.html', entry=entry.get('Original', ''), feedback=ai_result)

@app.route('/history')
def history():
    query = request.args.get('q')
    if query:
        records = db_service.search_diaries(query)
    else:
        records = db_service.get_recent_diaries(limit=20)
    return render_template('history.html', records=records, search_query=query)

@app.route('/api/dates')
def get_dates():
    calendar_data = db_service.get_calendar_data()
    return jsonify(calendar_data)

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True, port=5000)