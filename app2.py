from flask import Flask, render_template, request, jsonify
from datetime import datetime
import platform
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/api/system-info')
def system_info():
  try:
      info = {
          'platform': platform.system(),
          'platform_release': platform.release(),
          'platform_version': platform.version(),
          'architecture': platform.machine(),
          'processor': platform.processor(),
          'python_version': platform.python_version(),
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
          'status': 'サーバーは正常に動作しています',
          'message': 'システム情報を取得しました'
      }
      return jsonify(info)
  except Exception as e:
      return jsonify({
          'error': True,
          'message': f'システム情報の取得に失敗: {str(e)}',
          'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      })

@app.route('/api/connection-test')
def connection_test():
  return jsonify({
      'status': 'success',
      'message': '接続テストが成功しました！',
      'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
      'server_status': 'running'
  })

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
          file_content = file.read()
          return jsonify({
              'success': True,
              'message': f'画像 "{filename}" のアップロードが成功しました！',
              'filename': filename,
              'size': f'{len(file_content)} bytes'
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

@app.route('/favicon.ico')
def favicon():
  return '', 204

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
