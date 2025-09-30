from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import os
import io
import base64
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from rembg import remove
import tempfile
from PIL import Image, ImageDraw

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def enhance_image_quality(image, enhancement_type="all"):
  """画像品質向上関数"""
  if isinstance(image, np.ndarray):
      if len(image.shape) == 3 and image.shape[2] == 4:
          pil_image = Image.fromarray(image, 'RGBA')
      else:
          pil_image = Image.fromarray(image, 'RGB')
  else:
      pil_image = image

  if enhancement_type in ["all", "sharpen"]:
      enhancer = ImageEnhance.Sharpness(pil_image)
      pil_image = enhancer.enhance(1.5)

  if enhancement_type in ["all", "contrast"]:
      enhancer = ImageEnhance.Contrast(pil_image)
      pil_image = enhancer.enhance(1.2)

  if enhancement_type in ["all", "color"]:
      enhancer = ImageEnhance.Color(pil_image)
      pil_image = enhancer.enhance(1.1)

  if enhancement_type in ["all", "unsharp"]:
      pil_image = pil_image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

  return pil_image

def upscale_image(image, scale_factor=2):
  """画像アップスケーリング関数"""
  width, height = image.size
  new_width = int(width * scale_factor)
  new_height = int(height * scale_factor)
  
  upscaled = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
  return upscaled

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI高画質画像処理ツール</title>
  <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      
      body {
          font-family: 'Segoe UI', 'Hiragino Sans', 'Yu Gothic UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
          padding: 20px;
      }
      
      .container {
          max-width: 1200px;
          margin: 0 auto;
          background: rgba(255, 255, 255, 0.95);
          border-radius: 20px;
          padding: 30px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
      }
      
      .header {
          text-align: center;
          margin-bottom: 40px;
      }
      
      .header h1 {
          color: #333;
          font-size: 2.5em;
          margin-bottom: 10px;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
      }
      
      .version {
          background: linear-gradient(45deg, #ff6b6b, #ee5a24);
          color: white;
          padding: 5px 15px;
          border-radius: 20px;
          font-size: 0.9em;
          display: inline-block;
          margin-bottom: 10px;
      }
      
      .header p {
          color: #666;
          font-size: 1.2em;
          line-height: 1.5;
      }
      
      .upload-section {
          background: #f8f9fa;
          border-radius: 15px;
          padding: 30px;
          margin-bottom: 30px;
          border: 2px dashed #ddd;
          text-align: center;
          transition: all 0.3s ease;
      }
      
      .upload-section:hover {
          border-color: #667eea;
          background: #f0f4ff;
      }
      
      .upload-btn {
          background: linear-gradient(45deg, #667eea, #764ba2);
          color: white;
          border: none;
          padding: 15px 30px;
          border-radius: 50px;
          font-size: 1.1em;
          cursor: pointer;
          transition: all 0.3s ease;
          margin: 10px;
      }
      
      .upload-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
      }
      
      .options-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
      }
      
      .option-card {
          background: white;
          border-radius: 15px;
          padding: 25px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
          border: 2px solid transparent;
          transition: all 0.3s ease;
      }
      
      .option-card:hover {
          border-color: #667eea;
          transform: translateY(-2px);
      }
      
      .option-card h3 {
          color: #333;
          margin-bottom: 15px;
          font-size: 1.3em;
          display: flex;
          align-items: center;
          gap: 10px;
          line-height: 1.4;
      }
      
      .option-btn {
          width: 100%;
          padding: 12px;
          border: none;
          border-radius: 10px;
          font-size: 1em;
          cursor: pointer;
          transition: all 0.3s ease;
          margin: 5px 0;
          font-weight: 600;
          line-height: 1.3;
      }
      
      .bg-remove { background: #ff6b6b; color: white; }
      .enhance { background: #4ecdc4; color: white; }
      .upscale { background: #45b7d1; color: white; }
      .sharpen { background: #96ceb4; color: white; }
      .combo { background: linear-gradient(45deg, #f093fb, #f5576c); color: white; }
      .inpaint-edit { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
      
      .option-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 5px 15px rgba(0,0,0,0.2);
      }
      
      .result-section {
          display: none;
          text-align: center;
          margin-top: 30px;
      }
      
      .image-container {
          display: flex;
          justify-content: space-around;
          flex-wrap: wrap;
          gap: 20px;
          margin: 20px 0;
      }
      
      .image-box {
          background: white;
          border-radius: 15px;
          padding: 20px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
          max-width: 400px;
          flex: 1;
          min-width: 300px;
      }
      
      .image-box h4 {
          color: #333;
          margin-bottom: 15px;
          font-size: 1.2em;
      }
      
      .image-box img {
          max-width: 100%;
          max-height: 300px;
          border-radius: 10px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
      }
      
      .download-btn {
          background: linear-gradient(45deg, #11998e, #38ef7d);
          color: white;
          border: none;
          padding: 12px 25px;
          border-radius: 25px;
          font-size: 1em;
          cursor: pointer;
          margin-top: 15px;
          transition: all 0.3s ease;
          font-weight: 600;
      }
      
      .download-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px rgba(17, 153, 142, 0.3);
      }
      
      .loading {
          display: none;
          text-align: center;
          margin: 20px 0;
          padding: 30px;
          background: rgba(255, 255, 255, 0.9);
          border-radius: 15px;
      }
      
      .spinner {
          border: 4px solid #f3f3f3;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          width: 60px;
          height: 60px;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
      }
      
      @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
      }
      
      .feature-badge {
          background: linear-gradient(45deg, #ffeaa7, #fdcb6e);
          color: #2d3436;
          padding: 3px 8px;
          border-radius: 10px;
          font-size: 0.8em;
          font-weight: bold;
      }
  </style>
</head>
<body>
  <div class="container">
      <div class="header">
          <div class="version">🚀 Enhanced Version 2.0</div>
          <h1>AI高画質画像処理ツール</h1>
          <p>背景除去・画質改善・アップスケーリング・鮮明度向上</p>
      </div>
      
      <div class="upload-section">
          <h3>📸 画像アップロード</h3>
          <p>PNG、JPG、JPEGファイルを選択してください（最大10MB）</p>
          <input type="file" id="imageInput" accept="image/*" style="display: none;">
          <button class="upload-btn" onclick="document.getElementById('imageInput').click()">
              🖼️ 画像を選択
          </button>
          <div id="fileName" style="margin-top: 10px; color: #666; font-weight: 600;"></div>
      </div>
      
      <div class="options-section">
          <div class="option-card">
              <h3>🎭 背景除去 <span class="feature-badge">AI</span></h3>
              <button class="option-btn bg-remove" onclick="processImage('remove_bg')">
                  🗑️ 背景を完全除去
              </button>
          </div>
          
          <div class="option-card">
              <h3>🖌️ インペインティング <span class="feature-badge">HOT</span></h3>
              <button class="option-btn inpaint-edit" onclick="window.location.href='/inpaint_page'">
                  🖌️ 部分修復・編集
              </button>
          </div>
          
          <div class="option-card">
              <h3>✨ 画質改善 <span class="feature-badge">NEW</span></h3>
              <button class="option-btn enhance" onclick="processImage('enhance')">
                  🌟 全体品質向上
              </button>
              <button class="option-btn sharpen" onclick="processImage('sharpen')">
                  🔍 鮮明度のみ改善
              </button>
          </div>
          
          <div class="option-card">
              <h3>🔍 サイズ拡大 <span class="feature-badge">HD</span></h3>
              <button class="option-btn upscale" onclick="processImage('upscale_2x')">
                  📈 2倍拡大 (HD)
              </button>
              <button class="option-btn upscale" onclick="processImage('upscale_4x')">
                  🚀 4倍拡大 (4K)
              </button>
          </div>
          
          <div class="option-card">
              <h3>🎯 総合処理 <span class="feature-badge">PRO</span></h3>
              <button class="option-btn combo" onclick="processImage('bg_and_enhance')">
                  🎭✨ 背景除去+画質改善
              </button>
              <button class="option-btn combo" onclick="processImage('all_in_one')">
                  🌟 全機能を一度に
              </button>
          </div>
      </div>
      
      <div class="loading" id="loading">
          <div class="spinner"></div>
          <h3>🤖 AIが画像を処理しています</h3>
          <p>高品質処理のため少々お待ちください...</p>
      </div>
      
      <div class="result-section" id="resultSection">
          <h3>🎉 処理完了！</h3>
          <div class="image-container" id="imageContainer">
          </div>
      </div>
  </div>

  <script>
      let selectedFile = null;
      
      document.getElementById('imageInput').addEventListener('change', function(e) {
          selectedFile = e.target.files[0];
          if (selectedFile) {
              const fileSize = (selectedFile.size / 1024 / 1024).toFixed(2);
              document.getElementById('fileName').innerHTML = `
                  ✅ 選択されたファイル: <strong>${selectedFile.name}</strong><br>
                  📏 ファイルサイズ: ${fileSize}MB
              `;
          }
      });
      
      async function processImage(processType) {
          if (!selectedFile) {
              alert('🚨 まず画像を選択してください！');
              return;
          }
          
          if (selectedFile.size > 10 * 1024 * 1024) {
              alert('🚨 ファイルサイズが10MBを超えています。より小さなファイルを選択してください。');
              return;
          }
          
          const formData = new FormData();
          formData.append('image', selectedFile);
          formData.append('process_type', processType);
          
          document.getElementById('loading').style.display = 'block';
          document.getElementById('resultSection').style.display = 'none';
          
          try {
              const response = await fetch('/process', {
                  method: 'POST',
                  body: formData
              });
              
              if (response.ok) {
                  const result = await response.json();
                  displayResults(result);
              } else {
                  const error = await response.json();
                  alert(`🚨 処理中エラー: ${error.error}`);
              }
          } catch (error) {
              alert('🚨 ネットワークエラーが発生しました');
              console.error(error);
          }
          
          document.getElementById('loading').style.display = 'none';
      }
      
      function displayResults(result) {
          const container = document.getElementById('imageContainer');
          container.innerHTML = '';
          
          if (result.original) {
              const originalBox = createImageBox('📸 元画像', result.original, null);
              container.appendChild(originalBox);
          }
          
          if (result.processed) {
              const processedBox = createImageBox('✨ 処理完了', result.processed, result.download_url);
              container.appendChild(processedBox);
          }
          
          document.getElementById('resultSection').style.display = 'block';
      }
      
      function createImageBox(title, imageSrc, downloadUrl) {
          const box = document.createElement('div');
          box.className = 'image-box';
          
          box.innerHTML = `
              <h4>${title}</h4>
              <img src="data:image/png;base64,${imageSrc}" alt="${title}">
              ${downloadUrl ? `<br><button class="download-btn" onclick="downloadImage('${downloadUrl}')">💾 高画質ダウンロード</button>` : ''}
          `;
          
          return box;
      }
      
      function downloadImage(url) {
          const a = document.createElement('a');
          a.href = url;
          a.download = `enhanced_image_${Date.now()}.png`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
      }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
  return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process_image():
  """画像処理エンドポイント"""
  try:
      if 'image' not in request.files:
          return jsonify({'error': '画像がアップロードされていません'}), 400
      
      file = request.files['image']
      process_type = request.form.get('process_type', 'remove_bg')
      
      if file.filename == '':
          return jsonify({'error': 'ファイルが選択されていません'}), 400
      
      image_data = file.read()
      original_image = Image.open(io.BytesIO(image_data))
      
      original_buffer = io.BytesIO()
      original_image.save(original_buffer, format='PNG')
      original_b64 = base64.b64encode(original_buffer.getvalue()).decode()
      
      processed_image = None
      
      if process_type == 'remove_bg':
          processed_data = remove(image_data)
          processed_image = Image.open(io.BytesIO(processed_data))
          
      elif process_type == 'enhance':
          processed_image = enhance_image_quality(original_image, "all")
          
      elif process_type == 'sharpen':
          processed_image = enhance_image_quality(original_image, "sharpen")
          
      elif process_type == 'upscale_2x':
          processed_image = upscale_image(original_image, 2)
          
      elif process_type == 'upscale_4x':
          processed_image = upscale_image(original_image, 4)
          
      elif process_type == 'bg_and_enhance':
          bg_removed_data = remove(image_data)
          bg_removed_image = Image.open(io.BytesIO(bg_removed_data))
          processed_image = enhance_image_quality(bg_removed_image, "all")
          
      elif process_type == 'all_in_one':
          bg_removed_data = remove(image_data)
          bg_removed_image = Image.open(io.BytesIO(bg_removed_data))
          enhanced_image = enhance_image_quality(bg_removed_image, "all")
          processed_image = upscale_image(enhanced_image, 2)
      
      processed_buffer = io.BytesIO()
      processed_image.save(processed_buffer, format='PNG', quality=95)
      processed_b64 = base64.b64encode(processed_buffer.getvalue()).decode()
      
      temp_filename = f"enhanced_{process_type}_{file.filename.split('.')[0]}.png"
      temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
      processed_image.save(temp_path, format='PNG', quality=95)
      
      return jsonify({
          'success': True,
          'original': original_b64,
          'processed': processed_b64,
          'download_url': f'/download/{temp_filename}'
      })
      
  except Exception as e:
      return jsonify({'error': f'処理中エラーが発生しました: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
  """ファイルダウンロードエンドポイント"""
  file_path = os.path.join(OUTPUT_FOLDER, filename)
  if os.path.exists(file_path):
      return send_file(file_path, as_attachment=True)
  else:
      return jsonify({'error': 'ファイルが見つかりません'}), 404

if __name__ == '__main__':
  print("AI高画質画像処理ツール v2.0 が開始されました！")
  print("📍 アドレス: http://localhost:5000")
  print("🚀 新機能: 高級画質改善・4Kアップスケーリング・総合処理")
  app.run(debug=True, host='0.0.0.0', port=5000)