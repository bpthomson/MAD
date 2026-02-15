from flask import Flask, render_template, request, jsonify
import markdown
from config import Config
from services.ai_service import ai_service
from services.db_service import db_service

# 初始化檢查
Config.validate()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        custom_date = request.form.get('date') # 獲取使用者選擇的日期

        if not content:
            return render_template('index.html', error="請輸入日記內容！")
        
        # 1. 執行 AI 分析
        ai_result = ai_service.analyze_diary(content)
        
        if ai_result:
            raw_polished = ai_result.get('polished_version', '')
            ai_result['polished_html'] = markdown.markdown(raw_polished)

            # 2. 嘗試存檔 (傳入 custom_date)
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
            return render_template('index.html', 
                                 error="AI 分析失敗，請檢查 Terminal 錯誤訊息。", 
                                 content=content)

    return render_template('index.html')

@app.route('/history')
def history():
    recent_records = db_service.get_recent_diaries(limit=20)
    return render_template('history.html', records=recent_records)

# 新增 API：獲取有日記的日期
@app.route('/api/dates')
def get_dates():
    dates = db_service.get_existing_dates()
    return jsonify(dates)

if __name__ == '__main__':
    app.run(debug=True, port=5000)