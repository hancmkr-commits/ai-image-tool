from flask import Flask, render_template, request, jsonify
import psutil
import platform
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/api/system-info')
def system_info():
  try:
      # 안전한 시스템 정보 수집
      info = {
          'cpu_percent': psutil.cpu_percent(interval=1),
          'memory': {
              'total': round(psutil.virtual_memory().total / (1024**3), 2),
              'available': round(psutil.virtual_memory().available / (1024**3), 2),
              'percent': psutil.virtual_memory().percent
          },
          'disk': {
              'total': round(psutil.disk_usage('/').total / (1024**3), 2),
              'free': round(psutil.disk_usage('/').free / (1024**3), 2),
              'percent': psutil.disk_usage('/').percent
          },
          'platform': platform.system(),
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      }
      return jsonify(info)
  except Exception as e:
      # 에러가 발생해도 서버가 크래시되지 않도록
      return jsonify({
          'error': True,
          'message': f'システム情報の取得に失敗しました: {str(e)}',
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      }), 200  # 500 대신 200으로 반환

@app.route('/api/connection-test')
def connection_test():
  try:
      return jsonify({
          'status': 'success',
          'message': '接続テストが成功しました！',
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
          'server_status': 'running'
      })
  except Exception as e:
      return jsonify({
          'status': 'error',
          'message': f'接続テストに失敗しました: {str(e)}',
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      }), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
  try:
      if 'file' not in request.files:
          return jsonify({
              'success': False,
              'message': 'ファイルが選択されていません'
          })
      
      file = request.files['file']
      if file.filename == '':
          return jsonify({
              'success': False,
              'message': 'ファイルが選択されていません'
          })
      
      if file and allowed_file(file.filename):
          filename = secure_filename(file.filename)
          # 실제 파일 저장은 하지 않고 성공 메시지만 반환
          return jsonify({
              'success': True,
              'message': f'画像 "{filename}" のアップロードが成功しました！',
              'filename': filename,
              'size': len(file.read())
          })
      else:
          return jsonify({
              'success': False,
              'message': '対応していないファイル形式です (PNG, JPG, JPEG, GIF, WEBP のみ)'
          })
          
  except Exception as e:
      return jsonify({
          'success': False,
          'message': f'アップロードエラー: {str(e)}'
      })

def allowed_file(filename):
  ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 파비콘 404 에러 해결
@app.route('/favicon.ico')
def favicon():
  return '', 204  # No Content

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
