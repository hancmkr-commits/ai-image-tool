from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
  return '''
  <!DOCTYPE html>
  <html>
  <head>
      <title>AI Image Tool</title>
      <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          .container { text-align: center; }
          .upload-area { border: 2px dashed #ccc; padding: 40px; margin: 20px 0; }
          .upload-area:hover { border-color: #007bff; }
          .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; }
          .btn:hover { background: #0056b3; }
          .image-preview { max-width: 100%; margin: 20px 0; }
          .controls { margin: 20px 0; }
          .slider { width: 200px; margin: 0 10px; }
      </style>
  </head>
  <body>
      <div class="container">
          <h1>🎨 AI Image Tool</h1>
          <p>이미지 업로드 및 기본 편집 도구</p>
          
          <div class="upload-area" onclick="document.getElementById('fileInput').click()">
              <p>📁 클릭하여 이미지 업로드</p>
              <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="uploadImage()">
          </div>
          
          <div id="imageContainer" style="display: none;">
              <img id="imagePreview" class="image-preview">
              
              <div class="controls">
                  <h3>이미지 편집</h3>
                  <div>
                      <label>밝기: </label>
                      <input type="range" class="slider" min="0.5" max="2" step="0.1" value="1" onchange="adjustImage()">
                  </div>
                  <div>
                      <label>대비: </label>
                      <input type="range" class="slider" min="0.5" max="2" step="0.1" value="1" onchange="adjustImage()">
                  </div>
                  <div>
                      <label>채도: </label>
                      <input type="range" class="slider" min="0" max="2" step="0.1" value="1" onchange="adjustImage()">
                  </div>
              </div>
              
              <div>
                  <button class="btn" onclick="applyBlur()">🌫️ 블러 효과</button>
                  <button class="btn" onclick="applySharpen()">✨ 선명하게</button>
                  <button class="btn" onclick="resetImage()">🔄 원본으로</button>
                  <button class="btn" onclick="downloadImage()">💾 다운로드</button>
              </div>
          </div>
      </div>

      <script>
          let originalImageData = null;
          let currentImageData = null;

          function uploadImage() {
              const fileInput = document.getElementById('fileInput');
              const file = fileInput.files[0];
              
              if (file) {
                  const formData = new FormData();
                  formData.append('image', file);
                  
                  fetch('/upload', {
                      method: 'POST',
                      body: formData
                  })
                  .then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          originalImageData = data.image;
                          currentImageData = data.image;
                          displayImage(data.image);
                          document.getElementById('imageContainer').style.display = 'block';
                      }
                  })
                  .catch(error => console.error('Error:', error));
              }
          }

          function displayImage(imageData) {
              const img = document.getElementById('imagePreview');
              img.src = 'data:image/png;base64,' + imageData;
          }

          function adjustImage() {
              const sliders = document.querySelectorAll('.slider');
              const brightness = sliders[0].value;
              const contrast = sliders[1].value;
              const saturation = sliders[2].value;
              
              fetch('/adjust', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({
                      image: originalImageData,
                      brightness: parseFloat(brightness),
                      contrast: parseFloat(contrast),
                      saturation: parseFloat(saturation)
                  })
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      currentImageData = data.image;
                      displayImage(data.image);
                  }
              });
          }

          function applyBlur() {
              fetch('/blur', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({image: currentImageData})
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      currentImageData = data.image;
                      displayImage(data.image);
                  }
              });
          }

          function applySharpen() {
              fetch('/sharpen', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({image: currentImageData})
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      currentImageData = data.image;
                      displayImage(data.image);
                  }
              });
          }

          function resetImage() {
              currentImageData = originalImageData;
              displayImage(originalImageData);
              // Reset sliders
              const sliders = document.querySelectorAll('.slider');
              sliders[0].value = 1; // brightness
              sliders[1].value = 1; // contrast
              sliders[2].value = 1; // saturation
          }

          function downloadImage() {
              const link = document.createElement('a');
              link.href = 'data:image/png;base64,' + currentImageData;
              link.download = 'edited_image.png';
              link.click();
          }
      </script>
  </body>
  </html>
  '''

@app.route('/upload', methods=['POST'])
def upload_image():
  try:
      file = request.files['image']
      image = Image.open(file.stream)
      
      # Convert to RGB if necessary
      if image.mode != 'RGB':
          image = image.convert('RGB')
      
      # Convert to base64
      buffer = io.BytesIO()
      image.save(buffer, format='PNG')
      img_base64 = base64.b64encode(buffer.getvalue()).decode()
      
      return jsonify({'success': True, 'image': img_base64})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)})

@app.route('/adjust', methods=['POST'])
def adjust_image():
  try:
      data = request.json
      img_data = base64.b64decode(data['image'])
      image = Image.open(io.BytesIO(img_data))
      
      # Apply adjustments
      if data.get('brightness', 1) != 1:
          enhancer = ImageEnhance.Brightness(image)
          image = enhancer.enhance(data['brightness'])
      
      if data.get('contrast', 1) != 1:
          enhancer = ImageEnhance.Contrast(image)
          image = enhancer.enhance(data['contrast'])
      
      if data.get('saturation', 1) != 1:
          enhancer = ImageEnhance.Color(image)
          image = enhancer.enhance(data['saturation'])
      
      # Convert back to base64
      buffer = io.BytesIO()
      image.save(buffer, format='PNG')
      img_base64 = base64.b64encode(buffer.getvalue()).decode()
      
      return jsonify({'success': True, 'image': img_base64})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)})

@app.route('/blur', methods=['POST'])
def blur_image():
  try:
      data = request.json
      img_data = base64.b64decode(data['image'])
      image = Image.open(io.BytesIO(img_data))
      
      # Apply blur
      blurred = image.filter(ImageFilter.GaussianBlur(radius=2))
      
      # Convert back to base64
      buffer = io.BytesIO()
      blurred.save(buffer, format='PNG')
      img_base64 = base64.b64encode(buffer.getvalue()).decode()
      
      return jsonify({'success': True, 'image': img_base64})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)})

@app.route('/sharpen', methods=['POST'])
def sharpen_image():
  try:
      data = request.json
      img_data = base64.b64decode(data['image'])
      image = Image.open(io.BytesIO(img_data))
      
      # Apply sharpen
      sharpened = image.filter(ImageFilter.SHARPEN)
      
      # Convert back to base64
      buffer = io.BytesIO()
      sharpened.save(buffer, format='PNG')
      img_base64 = base64.b64encode(buffer.getvalue()).decode()
      
      return jsonify({'success': True, 'image': img_base64})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
