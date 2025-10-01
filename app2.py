from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import base64
import io
from PIL import Image
import time

app = Flask(__name__)
CORS(app)

# 업로드 폴더 생성
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
  return '''
  <!DOCTYPE html>
  <html lang="ja">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AI画像ツール</title>
      <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎨</text></svg>">
      <style>
          body { 
              font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif; 
              max-width: 800px; 
              margin: 0 auto; 
              padding: 20px; 
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              min-height: 100vh;
              color: #333;
          }
          .container { 
              background: white;
              border-radius: 15px;
              padding: 30px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.2);
              text-align: center; 
          }
          .upload-area { 
              border: 3px dashed #007bff; 
              padding: 60px 20px; 
              margin: 30px 0; 
              border-radius: 15px;
              background: #f8f9ff;
              transition: all 0.3s ease;
              cursor: pointer;
          }
          .upload-area:hover { 
              border-color: #0056b3; 
              background: #e3f2fd;
              transform: translateY(-2px);
          }
          .upload-area.dragover {
              border-color: #28a745;
              background: #d4edda;
          }
          .btn { 
              background: linear-gradient(45deg, #007bff, #0056b3);
              color: white; 
              padding: 12px 25px; 
              border: none; 
              border-radius: 25px; 
              cursor: pointer; 
              margin: 10px; 
              font-size: 16px;
              transition: all 0.3s ease;
              box-shadow: 0 4px 15px rgba(0,123,255,0.3);
          }
          .btn:hover { 
              transform: translateY(-2px);
              box-shadow: 0 6px 20px rgba(0,123,255,0.4);
          }
          .status { 
              margin: 20px 0; 
              padding: 15px; 
              border-radius: 10px; 
              font-weight: bold;
          }
          .success { 
              background: #d4edda; 
              color: #155724; 
              border: 1px solid #c3e6cb;
          }
          .error { 
              background: #f8d7da; 
              color: #721c24; 
              border: 1px solid #f5c6cb;
          }
          .info { 
              background: #d1ecf1; 
              color: #0c5460; 
              border: 1px solid #bee5eb;
          }
          .image-preview {
              max-width: 100%;
              max-height: 400px;
              margin: 20px 0;
              border-radius: 10px;
              box-shadow: 0 4px 15px rgba(0,0,0,0.2);
          }
          .image-info {
              background: #f8f9fa;
              padding: 15px;
              border-radius: 10px;
              margin: 10px 0;
              text-align: left;
          }
          .controls {
              margin: 20px 0;
          }
          .slider-container {
              margin: 15px 0;
              text-align: left;
          }
          .slider {
              width: 100%;
              margin: 10px 0;
          }
          #fileInput {
              display: none;
          }
      </style>
  </head>
  <body>
      <div class="container">
          <h1>🎨 AI画像ツール</h1>
          <p>高機能画像処理・編集ツール</p>
          
          <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
              <h2>📁 画像をアップロード</h2>
              <p>クリックしてファイルを選択するか、<br>ここにドラッグ&ドロップしてください</p>
              <small>対応形式: JPG, PNG, GIF, WebP</small>
          </div>
          
          <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)">
          
          <div id="imageContainer" style="display: none;">
              <h3>📷 アップロードされた画像</h3>
              <img id="imagePreview" class="image-preview">
              <div id="imageInfo" class="image-info"></div>
              
              <div class="controls">
                  <h4>🎛️ 画像編集</h4>
                  <div class="slider-container">
                      <label>明度: <span id="brightnessValue">100</span>%</label>
                      <input type="range" id="brightnessSlider" class="slider" min="0" max="200" value="100" oninput="adjustImage()">
                  </div>
                  <div class="slider-container">
                      <label>コントラスト: <span id="contrastValue">100</span>%</label>
                      <input type="range" id="contrastSlider" class="slider" min="0" max="200" value="100" oninput="adjustImage()">
                  </div>
                  <div class="slider-container">
                      <label>彩度: <span id="saturationValue">100</span>%</label>
                      <input type="range" id="saturationSlider" class="slider" min="0" max="200" value="100" oninput="adjustImage()">
                  </div>
                  
                  <button class="btn" onclick="resetImage()">🔄 リセット</button>
                  <button class="btn" onclick="downloadImage()">💾 ダウンロード</button>
              </div>
          </div>
          
          <div id="statusArea"></div>
      </div>

      <script>
          let originalImageData = null;
          let currentImageData = null;

          // ドラッグ&ドロップ機能
          const uploadArea = document.getElementById('uploadArea');
          
          uploadArea.addEventListener('dragover', (e) => {
              e.preventDefault();
              uploadArea.classList.add('dragover');
          });
          
          uploadArea.addEventListener('dragleave', () => {
              uploadArea.classList.remove('dragover');
          });
          
          uploadArea.addEventListener('drop', (e) => {
              e.preventDefault();
              uploadArea.classList.remove('dragover');
              const files = e.dataTransfer.files;
              if (files.length > 0) {
                  handleFile(files[0]);
              }
          });

          function handleFileSelect(event) {
              const file = event.target.files[0];
              if (file) {
                  handleFile(file);
              }
          }

          function handleFile(file) {
              if (!file.type.startsWith('image/')) {
                  showStatus('error', '❌ エラー', '画像ファイルを選択してください。');
                  return;
              }

              showStatus('info', '🔄 アップロード中...', 'ファイルを処理しています...');

              const formData = new FormData();
              formData.append('image', file);

              fetch('/api/upload', {
                  method: 'POST',
                  body: formData
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      displayImage(data);
                      showStatus('success', '✅ アップロード成功', `ファイル名: ${file.name}<br>サイズ: ${(file.size/1024/1024).toFixed(2)} MB`);
                  } else {
                      showStatus('error', '❌ アップロード失敗', data.message);
                  }
              })
              .catch(error => {
                  showStatus('error', '❌ エラー', 'アップロードに失敗しました。');
              });
          }

          function displayImage(data) {
              const imageContainer = document.getElementById('imageContainer');
              const imagePreview = document.getElementById('imagePreview');
              const imageInfo = document.getElementById('imageInfo');

              imagePreview.src = 'data:image/jpeg;base64,' + data.image_data;
              originalImageData = data.image_data;
              currentImageData = data.image_data;

              imageInfo.innerHTML = `
                  <strong>ファイル情報:</strong><br>
                  サイズ: ${data.width} × ${data.height} px<br>
                  フォーマット: ${data.format}<br>
                  ファイルサイズ: ${data.file_size}
              `;

              imageContainer.style.display = 'block';
              resetSliders();
          }

          function adjustImage() {
              const brightness = document.getElementById('brightnessSlider').value;
              const contrast = document.getElementById('contrastSlider').value;
              const saturation = document.getElementById('saturationSlider').value;

              document.getElementById('brightnessValue').textContent = brightness;
              document.getElementById('contrastValue').textContent = contrast;
              document.getElementById('saturationValue').textContent = saturation;

              const imagePreview = document.getElementById('imagePreview');
              imagePreview.style.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`;
          }

          function resetImage() {
              resetSliders();
              adjustImage();
              showStatus('info', '🔄 リセット', '画像を元の状態に戻しました。');
          }

          function resetSliders() {
              document.getElementById('brightnessSlider').value = 100;
              document.getElementById('contrastSlider').value = 100;
              document.getElementById('saturationSlider').value = 100;
              document.getElementById('brightnessValue').textContent = '100';
              document.getElementById('contrastValue').textContent = '100';
              document.getElementById('saturationValue').textContent = '100';
          }

          function downloadImage() {
              const canvas = document.createElement('canvas');
              const ctx = canvas.getContext('2d');
              const img = document.getElementById('imagePreview');

              canvas.width = img.naturalWidth;
              canvas.height = img.naturalHeight;

              // Apply filters
              const brightness = document.getElementById('brightnessSlider').value;
              const contrast = document.getElementById('contrastSlider').value;
              const saturation = document.getElementById('saturationSlider').value;

              ctx.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`;
              ctx.drawImage(img, 0, 0);

              canvas.toBlob((blob) => {
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'edited_image.jpg';
                  a.click();
                  URL.revokeObjectURL(url);
                  showStatus('success', '💾 ダウンロード', '編集済み画像をダウンロードしました。');
              }, 'image/jpeg', 0.9);
          }

          function showStatus(type, title, message) {
              const statusArea = document.getElementById('statusArea');
              statusArea.innerHTML = `
                  <div class="status ${type}">
                      <h4>${title}</h4>
                      <p>${message}</p>
                  </div>
              `;
              
              if (type === 'success' || type === 'info') {
                  setTimeout(() => {
                      statusArea.innerHTML = '';
                  }, 5000);
              }
          }

          // 초기 메시지
          window.onload = function() {
              showStatus('success', '🎉 準備完了！', '画像をアップロードして編集を始めましょう！');
          };
      </script>
  </body>
  </html>
  '''

@app.route('/api/upload', methods=['POST'])
def upload_image():
  try:
      if 'image' not in request.files:
          return jsonify({'success': False, 'message': 'ファイルが選択されていません'})
      
      file = request.files['image']
      if file.filename == '':
          return jsonify({'success': False, 'message': 'ファイルが選択されていません'})
      
      # 画像を開いて処理
      image = Image.open(file.stream)
      
      # RGB変換（必要に応じて）
      if image.mode != 'RGB':
          image = image.convert('RGB')
      
      # 画像情報取得
      width, height = image.size
      format_name = image.format or 'JPEG'
      
      # Base64エンコード
      buffer = io.BytesIO()
      image.save(buffer, format='JPEG', quality=90)
      image_data = base64.b64encode(buffer.getvalue()).decode()
      
      # ファイルサイズ計算
      file_size = f"{len(buffer.getvalue()) / 1024 / 1024:.2f} MB"
      
      return jsonify({
          'success': True,
          'message': 'アップロード成功',
          'image_data': image_data,
          'width': width,
          'height': height,
          'format': format_name,
          'file_size': file_size
      })
      
  except Exception as e:
      return jsonify({'success': False, 'message': f'エラー: {str(e)}'})

@app.route('/api/test', methods=['GET'])
def test_connection():
  import time
  start_time = time.time()
  
  response_time = round((time.time() - start_time) * 1000, 2)
  
  return jsonify({
      'success': True,
      'message': '接続テスト成功',
      'response_time': response_time,
      'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
      'status': 'online'
  })

@app.route('/api/system-info', methods=['GET'])
def system_info():
  import sys
  import time
  import psutil
  
  try:
      memory_info = psutil.virtual_memory()
      memory_usage = f"{memory_info.percent}%"
  except:
      memory_usage = "取得不可"
  
  return jsonify({
      'success': True,
      'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
      'flask_version': '2.3.3',
      'uptime': time.strftime('%H:%M:%S', time.gmtime(time.time())),
      'memory_usage': memory_usage,
      'platform': sys.platform
  })

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=False)
