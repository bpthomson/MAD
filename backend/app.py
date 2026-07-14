from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import markdown
import json
import functools
from config import Config
from services.ai_service import ai_service
from services.db_service import db_service

Config.validate()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
# Enable CORS for the frontend application
CORS(app, supports_credentials=True)

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    password = data.get('password')
    if password == Config.DIARY_PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'error': '密碼錯誤'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    if session.get('logged_in'):
        return jsonify({'logged_in': True})
    return jsonify({'logged_in': False})

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'OK'}), 200

@app.route('/api/diary', methods=['POST'])
@login_required
def create_or_update_diary():
    data = request.get_json() or {}
    content = data.get('content')
    custom_date = data.get('date')
    old_timestamp = data.get('old_timestamp')
    model_name = data.get('model')

    if not content:
        return jsonify({'error': '請輸入日記內容！'}), 400
    
    past_context = db_service.get_context_for_ai(limit=3)
    ai_result = ai_service.analyze_diary(content, past_context, model_name)
    
    if ai_result:
        raw_polished = ai_result.get('polished_version', '')
        ai_result['polished_html'] = markdown.markdown(raw_polished)
        title = ai_result.get('title', content[:30] + "...")
        
        save_success = False
        try:
            if old_timestamp:
                print(f"Updating entry: {old_timestamp}")
                new_ts = db_service.update_entry(old_timestamp, title, content, ai_result, custom_date)
                if new_ts:
                    save_success = True
                    ai_result['timestamp'] = new_ts
            else:
                new_ts = db_service.save_entry(title, content, ai_result, custom_date)
                if new_ts:
                    save_success = True
                    ai_result['timestamp'] = new_ts
        except Exception as e:
            print(f"Save Error: {e}")

        if not save_success:
            ai_result['system_warning'] = "注意：日記未成功寫入資料庫。"

        return jsonify({'success': True, 'entry': content, 'feedback': ai_result})
    else:
        return jsonify({'error': 'AI 分析失敗', 'content': content}), 500

@app.route('/api/diary/<path:timestamp>', methods=['GET'])
@login_required
def get_diary(timestamp):
    entry = db_service.get_entry(timestamp)
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    ts = entry.get('Timestamp', '')
    date_val = ts.split(' ')[0] if ts else ''
    
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

    return jsonify({
        'content': entry.get('Original', ''), 
        'date_value': date_val, 
        'old_timestamp': ts,
        'feedback': ai_result
    })

@app.route('/api/diary/<path:timestamp>', methods=['DELETE'])
@login_required
def delete_entry(timestamp):
    db_service.delete_entry(timestamp)
    return jsonify({'success': True})

@app.route('/api/history', methods=['GET'])
@login_required
def history():
    query = request.args.get('q')
    if query:
        records = db_service.search_diaries(query)
    else:
        records = db_service.get_recent_diaries(limit=20)
    return jsonify({'records': records, 'search_query': query})

@app.route('/api/dates', methods=['GET'])
@login_required
def get_dates():
    calendar_data = db_service.get_calendar_data()
    return jsonify(calendar_data)

@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    return jsonify(ai_service.get_available_models())

if __name__ == '__main__':
    app.run(debug=True, port=5000)