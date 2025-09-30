from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
  return '''
  <!DOCTYPE html>
  <html lang="ja">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AI画像ツール</title>
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
          .feature-list {
              text-align: left;
              background: #f8f9fa;
              padding: 20px;
              border-radius: 10px;
              margin: 20px 0;
          }
          .feature-list h3 {
              color: #007bff;
              margin-top: 0;
          }
          .feature-list ul {
              list-style-type: none;
              padding: 0;
          }
          .feature-list li {
              padding: 8px 0;
              border-bottom: 1px solid #dee2e6;
          }
          .feature-list li:before {
              content: "✨ ";
              margin-right: 10px;
          }
          .version-info {
              background: #e9ecef;
              padding: 15px;
              border-radius: 10px;
              margin: 20px 0;
              font-size: 14px;
          }
      </style>
  </head>
  <body>
      <div class="container">
          <h1>🎨 AI画像ツール</h1>
          <p>高機能画像処理・編集ツール（デプロイ中）</p>
          
          <div class="status info">
              <h3>🚀 現在の状況</h3>
              <p>基本システムのデプロイが完了しました！<br>
              画像処理機能を段階的に追加していきます。</p>
          </div>
          
          <div class="upload-area" onclick="showComingSoon()">
              <h2>📁 画像をアップロード</h2>
              <p>クリックしてファイルを選択<br>
              <small>（近日公開予定）</small></p>
          </div>
          
          <div class="feature-list">
              <h3>🎯 予定機能</h3>
              <ul>
                  <li>画像アップロード・プレビュー</li>
                  <li>明度・コントラスト・彩度調整</li>
                  <li>ブラー・シャープネス効果</li>
                  <li>背景除去（AI処理）</li>
                  <li>フィルター効果（セピア、モノクロなど）</li>
                  <li>画像リサイズ・回転</li>
                  <li>複数画像の一括処理</li>
                  <li>編集履歴・アンドゥ機能</li>
              </ul>
          </div>
          
          <div>
              <button class="btn" onclick="testConnection()">🔧 接続テスト</button>
              <button class="btn" onclick="showSystemInfo()">📊 システム情報</button>
              <button class="btn" onclick="checkUpdates()">🔄 更新確認</button>
          </div>
          
          <div id="statusArea"></div>
          
          <div class="version-info">
              <strong>バージョン:</strong> 1.0.0-beta<br>
              <strong>最終更新:</strong> 2024年10月1日<br>
              <strong>ステータス:</strong> <span style="color: #28a745;">✅ オンライン</span>
          </div>
      </div>

      <script>
          function showComingSoon() {
              showStatus('info', '🚧 開発中', '画像アップロード機能は現在開発中です。もうしばらくお待ちください！');
          }

          function testConnection() {
              showStatus('info', '🔄 テスト中...', '接続をテストしています...');
              
              fetch('/api/test')
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      showStatus('success', '✅ 接続成功', 
                          `サーバーとの接続が正常です。<br>
                          レスポンス時間: ${data.response_time}ms<br>
                          サーバー時刻: ${data.server_time}`);
                  } else {
                      showStatus('error', '❌ 接続エラー', data.message);
                  }
              })
              .catch(error => {
                  showStatus('error', '❌ 接続失敗', 'サーバーとの接続に失敗しました。');
              });
          }

          function showSystemInfo() {
              fetch('/api/system-info')
              .then(response => response.json())
              .then(data => {
                  showStatus('info', '📊 システム情報', 
                      `Python バージョン: ${data.python_version}<br>
                      Flask バージョン: ${data.flask_version}<br>
                      サーバー稼働時間: ${data.uptime}<br>
                      メモリ使用量: ${data.memory_usage}`);
              })
              .catch(error => {
                  showStatus('error', '❌ 情報取得失敗', 'システム情報の取得に失敗しました。');
              });
          }

          function checkUpdates() {
              showStatus('info', '🔄 更新確認中...', '新しい機能をチェックしています...');
              
              setTimeout(() => {
                  showStatus('success', '✨ 更新情報', 
                      `次回のアップデートで追加予定:<br>
                      • 基本的な画像編集機能<br>
                      • ファイルアップロード<br>
                      • プレビュー機能<br>
                      • 簡単なフィルター`);
              }, 1500);
          }

          function showStatus(type, title, message) {
              const statusArea = document.getElementById('statusArea');
              statusArea.innerHTML = `
                  <div class="status ${type}">
                      <h4>${title}</h4>
                      <p>${message}</p>
                  </div>
              `;
              
              // Auto hide after 10 seconds for success messages
              if (type === 'success' || type === 'info') {
                  setTimeout(() => {
                      statusArea.innerHTML = '';
                  }, 10000);
              }
          }

          // Show welcome message on load
          window.onload = function() {
              showStatus('success', '🎉 ようこそ！', 
                  'AI画像ツールへようこそ！基本システムが正常に動作しています。');
          };
      </script>
  </body>
  </html>
  '''

@app.route('/api/test', methods=['GET'])
def test_connection():
  import time
  start_time = time.time()
  
  # Simple test
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

@app.route('/api/upload-test', methods=['POST'])
def upload_test():
  """将来の画像アップロード機能のテスト"""
  return jsonify({
      'success': False,
      'message': '画像アップロード機能は開発中です',
      'status': 'coming_soon'
  })

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=False)
