from flask import Flask, render_template, request, jsonify, send_from_directory
import markdown
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

        if not content:
            return render_template('index.html', error="請輸入日記內容！")
        
        ai_result = ai_service.analyze_diary(content)
        
        if ai_result:
            raw_polished = ai_result.get('polished_version', '')
            ai_result['polished_html'] = markdown.markdown(raw_polished)

            title = content[:30] + "..."
            save_success = False
            try:
                if db_service.save_entry(title, content, ai_result, custom_date):
                    save_success = True
                else:
                    print("警告: DB 存檔回傳 False")
            except Exception as e:
                print(f"警告: DB 存檔發生例外: {e}")

            if not save_success:
                ai_result['system_warning'] = "注意：日記未成功寫入資料庫，但 AI 分析已完成。"

            return render_template('result.html', entry=content, feedback=ai_result)
        else:
            return render_template('index.html', error="AI 分析失敗", content=content)

    return render_template('index.html')

@app.route('/history')
def history():
    # 接收搜尋關鍵字
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

# PWA: 提供 Service Worker 檔案
@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True, port=5000)