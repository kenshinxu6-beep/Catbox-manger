from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

CATBOX_API = "https://catbox.moe/user/api.php"
USER_HASH = "d0dde6e994892d6097a588de2"  # 🔑 Teri Catbox user hash
MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catbox Uploader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0d1117;
            color: #c9d1d9;
            font-family: 'Segoe UI', system-ui, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 480px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 { color: #58a6ff; font-size: 26px; margin-bottom: 6px; }
        .header p { color: #8b949e; font-size: 14px; }
        .upload-box {
            border: 2px dashed #30363d;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
            position: relative;
        }
        .upload-box:hover, .upload-box.dragover {
            border-color: #58a6ff;
            background: rgba(88,166,255,0.05);
        }
        .upload-box input {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
            width: 100%;
            height: 100%;
        }
        .upload-box .icon { font-size: 40px; margin-bottom: 10px; }
        .upload-box .text { font-size: 15px; color: #8b949e; }
        .upload-box .file-name {
            margin-top: 10px;
            color: #58a6ff;
            font-weight: 500;
            display: none;
        }
        .btn {
            width: 100%;
            padding: 14px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn:hover { background: #2ea043; }
        .btn:disabled { background: #30363d; cursor: not-allowed; }
        .info {
            text-align: center;
            margin-top: 15px;
            font-size: 12px;
            color: #484f58;
        }
        .result {
            margin-top: 20px;
            padding: 16px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            display: none;
        }
        .result.success { border-color: #238636; }
        .result.error { border-color: #f85149; }
        .result label {
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .result .link {
            color: #58a6ff;
            word-break: break-all;
            margin-top: 6px;
            font-size: 14px;
        }
        .result .link a { color: #58a6ff; }
        .preview {
            margin-top: 12px;
            max-width: 100%;
            border-radius: 8px;
            display: none;
        }
        .spinner {
            display: none;
            text-align: center;
            margin-top: 15px;
            color: #8b949e;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>📤 Catbox Uploader</h1>
            <p>Upload PFP, Banner & Videos</p>
        </div>
        
        <form id="form" enctype="multipart/form-data">
            <div class="upload-box" id="dropZone">
                <input type="file" name="file" id="fileInput" accept="image/*,video/*" required>
                <div class="icon">☁️</div>
                <div class="text">Click or drag file here</div>
                <div class="file-name" id="fileName"></div>
            </div>
            
            <button type="submit" class="btn" id="btn">Upload File</button>
        </form>
        
        <div class="info">Max file size: 8MB | Supported: JPG, PNG, GIF, MP4, WEBM</div>
        
        <div class="spinner" id="spinner">⏳ Uploading to Catbox...</div>
        
        <div class="result" id="result">
            <label>Uploaded URL</label>
            <div class="link"><a id="link" href="" target="_blank"></a></div>
            <img class="preview" id="previewImg" alt="preview">
            <video class="preview" id="previewVid" controls></video>
        </div>
    </div>

    <script>
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const dropZone = document.getElementById('dropZone');
        const form = document.getElementById('form');
        const btn = document.getElementById('btn');
        const spinner = document.getElementById('spinner');
        const result = document.getElementById('result');
        const link = document.getElementById('link');
        const previewImg = document.getElementById('previewImg');
        const previewVid = document.getElementById('previewVid');

        fileInput.onchange = () => {
            if (fileInput.files[0]) {
                fileName.textContent = fileInput.files[0].name;
                fileName.style.display = 'block';
                dropZone.querySelector('.text').textContent = 'File selected';
            }
        };

        ['dragenter','dragover','dragleave','drop'].forEach(e => {
            dropZone.addEventListener(e, (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
            });
        });
        ['dragenter','dragover'].forEach(e => {
            dropZone.addEventListener(e, () => dropZone.classList.add('dragover'));
        });
        ['dragleave','drop'].forEach(e => {
            dropZone.addEventListener(e, () => dropZone.classList.remove('dragover'));
        });
        dropZone.addEventListener('drop', (e) => {
            fileInput.files = e.dataTransfer.files;
            fileInput.onchange();
        });

        form.onsubmit = async (e) => {
            e.preventDefault();
            const file = fileInput.files[0];
            if (!file) return;

            btn.disabled = true;
            spinner.style.display = 'block';
            result.style.display = 'none';
            result.className = 'result';

            const fd = new FormData();
            fd.append('file', file);

            try {
                const res = await fetch('/upload', { method: 'POST', body: fd });
                const data = await res.json();

                spinner.style.display = 'none';
                btn.disabled = false;

                if (data.success) {
                    result.classList.add('success');
                    link.href = data.url;
                    link.textContent = data.url;
                    result.style.display = 'block';

                    previewImg.style.display = 'none';
                    previewVid.style.display = 'none';
                    if (file.type.startsWith('image/')) {
                        previewImg.src = data.url;
                        previewImg.style.display = 'block';
                    } else if (file.type.startsWith('video/')) {
                        previewVid.src = data.url;
                        previewVid.style.display = 'block';
                    }
                } else {
                    result.classList.add('error');
                    link.textContent = data.error || 'Upload failed';
                    result.style.display = 'block';
                }
            } catch (err) {
                spinner.style.display = 'none';
                btn.disabled = false;
                result.classList.add('error');
                link.textContent = err.message;
                result.style.display = 'block';
            }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"success": False, "error": "File exceeds 8MB limit"}), 413

    try:
        r = requests.post(
            CATBOX_API,
            data={
                "reqtype": "fileupload",
                "userhash": USER_HASH  # 🔑 Teri user hash yahan
            },
            files={"fileToUpload": (file.filename, file.stream, file.content_type)},
            timeout=120
        )
        url = r.text.strip()
        if r.status_code == 200 and url.startswith('https://'):
            return jsonify({"success": True, "url": url, "filename": file.filename})
        return jsonify({"success": False, "error": f"Catbox error: {url}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
