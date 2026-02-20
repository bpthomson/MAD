from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
import markdown
import json
import functools
from config import Config
from services.ai_service import ai_service
from services.db_service import db_service

Config.validate()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == Config.DIARY_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="密碼錯誤")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/', methods=['GET', 'POST'])
@login_required
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

@app.route('/edit/<path:timestamp>')
@login_required
def edit_entry(timestamp):
    entry = db_service.get_entry(timestamp)
    if not entry:
        return "Entry not found", 404
    
    ts = entry.get('Timestamp', '')
    date_val = ts.split(' ')[0] if ts else ''
    
    return render_template('index.html', 
                           content=entry.get('Original', ''), 
                           date_value=date_val, 
                           old_timestamp=ts,
                           is_edit=True)

@app.route('/delete/<path:timestamp>')
@login_required
def delete_entry(timestamp):
    db_service.delete_entry(timestamp)
    return redirect('/history')

@app.route('/entry/<path:timestamp>')
@login_required
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
        'timestamp': timestamp
    }

    return render_template('result.html', entry=entry.get('Original', ''), feedback=ai_result)

@app.route('/history')
@login_required
def history():
    query = request.args.get('q')
    if query:
        records = db_service.search_diaries(query)
    else:
        records = db_service.get_recent_diaries(limit=20)
    return render_template('history.html', records=records, search_query=query)

@app.route('/api/dates')
@login_required
def get_dates():
    calendar_data = db_service.get_calendar_data()
    return jsonify(calendar_data)

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True, port=5000)