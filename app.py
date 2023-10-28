from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import csv
import xlrd

app = Flask(__name__)
app.static_folder = 'static'

# Настройки для подключения к базе данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/self_analitic/database/my_database.db'  # Укажите свой путь к базе данных SQLite
db = SQLAlchemy(app)

# Создать базу данных (если не существует)
with app.app_context():
    db.create_all()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class MyTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Определите поля таблицы здесь

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        print(f"Uploaded file: {filename}")  # Отладочная информация
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename})
    else:
        return jsonify({'error': 'Invalid file type'}), 400

def execute_sql_query(file_path, sql_query):
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            data = read_xlsx(file_path)
        elif file_path.endswith('.xls'):
            data = read_xls(file_path)
        else:
            return []

        print(f"Reading file: {file_path}")  # Отладочная информация
        # Выполнить SQL-запрос
        result = db.session.execute(sql_query)  # Используется SQLAlchemy
        return [dict(row) for row in result]
    except Exception as e:
        error_message = str(e)
        print(f"Error executing SQL query: {error_message}")
        # Добавляем информацию об ошибке в ответ
        return [{'error': error_message}]

def read_xlsx(file_path):
    try:
        data = pd.read_excel(file_path)
        return data.to_dict(orient='records')
    except Exception as e:
        error_message = str(e)
        print(f"Error reading XLSX file: {error_message}")
        # Добавляем информацию об ошибке в ответ
        return [{'error': error_message}]

def read_xls(file_path):
    try:
        data = pd.read_excel(file_path)
        return data.to_dict(orient='records')
    except Exception as e:
        error_message = str(e)
        print(f"Error reading XLS file: {error_message}")
        # Добавляем информацию об ошибке в ответ
        return [{'error': error_message}]

@app.route('/execute_query/<filename>', methods=['POST'])
def execute_query(filename):
    sql_query = request.json.get('sql_query')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(file_path):
        results = execute_sql_query(file_path, sql_query)
        print(f"Executed SQL query for file: {file_path}")  # Отладочная информация
        # Используем JSONP для отправки данных клиенту
        callback = request.args.get('callback')
        json_data = jsonify(results).get_data(as_text=True)
        if callback:
            jsonp_response = make_response(f"{callback}({json_data});")
            jsonp_response.headers['Content-Type'] = 'application/javascript'
            return jsonp_response
        return json_data
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/get_uploaded_files', methods=['GET'])
def get_uploaded_files():
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({'files': file_list})

@app.route('/get_file_data/<filename>', methods=['GET'])
def get_file_data(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        if filename.endswith('.csv'):
            with open(file_path, 'r') as csvfile:
                data = list(csv.DictReader(csvfile))
        elif filename.endswith('.xlsx'):
            data = read_xlsx(file_path)
        elif filename.endswith('.xls'):
            data = read_xls(file_path)
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        print(f"Reading file data: {file_path}")  # Отладочная информация
        # Используем JSONP для отправки данных клиенту
        callback = request.args.get('callback')
        json_data = jsonify(data).get_data(as_text=True)
        if callback:
            jsonp_response = make_response(f"{callback}({json_data});")
            jsonp_response.headers['Content-Type'] = 'application/javascript'
            return jsonp_response
        return json_data
    else:
        return jsonify({'error': 'File not found'}), 404

@app.errorhandler(404)
def page_not_found(e):
    return "404 Error - Page Not Found", 404

@app.errorhandler(500)
def internal_server_error(e):
    # Подробное сообщение об ошибке 500
    return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # Запуск приложения на порту 8080
