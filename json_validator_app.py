from flask import Flask, render_template_string, request, jsonify
import json
import os
from pathlib import Path

app = Flask(__name__)

# 配置图片路径
PROJECT_PATH = r"./book_covers/art"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Cover JSON 校验编辑器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
        }
        h1 { font-size: 24px; margin-bottom: 5px; }
        .subtitle { opacity: 0.8; font-size: 14px; }
        .main-content {
            display: flex;
            height: calc(100vh - 140px);
        }
        .file-list {
            width: 300px;
            border-right: 1px solid #e0e0e0;
            overflow-y: auto;
            background: #fafafa;
        }
        .file-item {
            padding: 12px 20px;
            cursor: pointer;
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.2s;
        }
        .file-item:hover { background: #e8f4f8; }
        .file-item.active { background: #3498db; color: white; }
        .file-name { font-weight: 500; }
        .file-status {
            font-size: 12px;
            margin-top: 4px;
            opacity: 0.7;
        }
        .editor-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .preview-area {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            background: #f9f9f9;
        }
        .preview-image {
            max-width: 300px;
            max-height: 400px;
            border: 2px solid #ddd;
            border-radius: 4px;
        }
        .form-area {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        input, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
        }
        textarea {
            min-height: 80px;
            resize: vertical;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-save {
            background: #27ae60;
            color: white;
        }
        .btn-save:hover { background: #229954; }
        .btn-cancel {
            background: #95a5a6;
            color: white;
        }
        .btn-cancel:hover { background: #7f8c8d; }
        .message {
            padding: 12px 20px;
            margin: 20px 30px;
            border-radius: 4px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .validation-error {
            color: #e74c3c;
            font-size: 12px;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Book Cover JSON 校验编辑器</h1>
            <div class="subtitle">人工校验和编辑大模型生成的书籍封面元数据</div>
        </div>
        <div id="message" class="message"></div>
        <div class="main-content">
            <div class="file-list" id="fileList">
                <div style="padding: 20px; text-align: center; color: #7f8c8d;">
                    加载中...
                </div>
            </div>
            <div class="editor-panel">
                <div class="preview-area" id="previewArea" style="display: none;">
                    <img id="previewImage" class="preview-image" alt="封面预览">
                </div>
                <div class="form-area" id="formArea">
                    <div style="text-align: center; padding: 50px; color: #7f8c8d;">
                        ← 请从左侧选择一个JSON文件开始编辑
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentFile = null;
        let files = [];

        async function loadFileList() {
            try {
                const response = await fetch('/api/files');
                files = await response.json();
                renderFileList();
            } catch (error) {
                showMessage('加载文件列表失败: ' + error.message, 'error');
            }
        }

        function renderFileList() {
            const fileList = document.getElementById('fileList');
            if (files.length === 0) {
                fileList.innerHTML = '<div style="padding: 20px; text-align: center; color: #7f8c8d;">未找到JSON文件</div>';
                return;
            }
            
            fileList.innerHTML = files.map(file => `
                <div class="file-item" onclick="loadFile('${file}')">
                    <div class="file-name">${file}</div>
                    <div class="file-status">点击编辑</div>
                </div>
            `).join('');
        }

        async function loadFile(filename) {
            try {
                const response = await fetch(`/api/file/${filename}`);
                const data = await response.json();
                currentFile = filename;
                renderEditor(data);
                
                // 更新选中状态
                document.querySelectorAll('.file-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.querySelector('.file-name').textContent === filename) {
                        item.classList.add('active');
                    }
                });
                
                // 显示图片预览
                const imagePath = filename.replace('.json', '.png');
                document.getElementById('previewImage').src = `/api/image/${imagePath}`;
                document.getElementById('previewArea').style.display = 'block';
            } catch (error) {
                showMessage('加载文件失败: ' + error.message, 'error');
            }
        }

        function renderEditor(data) {
            const formArea = document.getElementById('formArea');
            formArea.innerHTML = `
                <div class="form-group">
                    <label>推理类型 (reasoning)</label>
                    <input type="text" id="reasoning" value="${data.reasoning || ''}" readonly style="background: #f0f0f0;">
                </div>
                <div class="form-group">
                    <label>翻译者 (translator)</label>
                    <input type="text" id="translator" value="${data.translator || 'null'}">
                </div>
                <div class="form-group">
                    <label>主标题 (main_title) *</label>
                    <input type="text" id="main_title" value="${data.main_title || ''}" required>
                    <div id="error_main_title" class="validation-error"></div>
                </div>
                <div class="form-group">
                    <label>出版社 (publisher) *</label>
                    <input type="text" id="publisher" value="${data.publisher || ''}" required>
                    <div id="error_publisher" class="validation-error"></div>
                </div>
                <div class="form-group">
                    <label>腰封文字 (belly_band)</label>
                    <input type="text" id="belly_band" value="${data.belly_band || ''}">
                </div>
                <div class="form-group">
                    <label>作者 (author) *</label>
                    <input type="text" id="author" value="${data.author || ''}" required>
                    <div id="error_author" class="validation-error"></div>
                </div>
                <div class="form-group">
                    <label>副标题 (subtitle)</label>
                    <input type="text" id="subtitle" value="${data.subtitle || ''}">
                </div>
                <div class="form-group">
                    <label>封面描述 (cover_description)</label>
                    <textarea id="cover_description">${data.cover_description || ''}</textarea>
                </div>
                <div class="button-group">
                    <button class="btn-save" onclick="saveFile()">💾 保存修改</button>
                    <button class="btn-cancel" onclick="loadFile(currentFile)">↻ 重置</button>
                </div>
            `;
        }

        function validateForm() {
            let isValid = true;
            const requiredFields = ['main_title', 'publisher', 'author'];
            
            requiredFields.forEach(field => {
                const input = document.getElementById(field);
                const error = document.getElementById(`error_${field}`);
                if (!input.value.trim()) {
                    error.textContent = '此字段为必填项';
                    isValid = false;
                } else {
                    error.textContent = '';
                }
            });
            
            return isValid;
        }

        async function saveFile() {
            if (!validateForm()) {
                showMessage('请填写所有必填字段', 'error');
                return;
            }

            const data = {
                reasoning: document.getElementById('reasoning').value,
                translator: document.getElementById('translator').value,
                main_title: document.getElementById('main_title').value,
                publisher: document.getElementById('publisher').value,
                belly_band: document.getElementById('belly_band').value,
                author: document.getElementById('author').value,
                subtitle: document.getElementById('subtitle').value,
                cover_description: document.getElementById('cover_description').value
            };

            try {
                const response = await fetch(`/api/file/${currentFile}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    showMessage('保存成功!', 'success');
                } else {
                    throw new Error('保存失败');
                }
            } catch (error) {
                showMessage('保存失败: ' + error.message, 'error');
            }
        }

        function showMessage(text, type) {
            const message = document.getElementById('message');
            message.textContent = text;
            message.className = `message ${type}`;
            message.style.display = 'block';
            setTimeout(() => {
                message.style.display = 'none';
            }, 3000);
        }

        // 初始化
        loadFileList();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/files')
def get_files():
    """获取所有JSON文件列表"""
    try:
        path = Path(PROJECT_PATH)
        json_files = sorted([f.name for f in path.glob('*.json')])
        return jsonify(json_files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>')
def get_file(filename):
    """读取JSON文件内容"""
    try:
        file_path = Path(PROJECT_PATH) / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>', methods=['POST'])
def save_file(filename):
    """保存JSON文件"""
    try:
        data = request.json
        file_path = Path(PROJECT_PATH) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/image/<filename>')
def get_image(filename):
    """获取对应的PNG图片"""
    try:
        from flask import send_file
        image_path = Path(PROJECT_PATH) / filename
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)