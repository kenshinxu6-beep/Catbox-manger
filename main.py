from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USERHASH = "d0dde6e994892d6097a588de2"

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Kenshin Upload</title>
<style>
  body { background:#0d1f15; color:#f0f5f1; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; padding:20px; }
  h2 { color:#6fcf8f; margin-bottom:24px; }
  input[type=file] { background:#162a1e; border:1px solid #2d6b3e; color:#f0f5f1; padding:10px; border-radius:8px; width:100%; max-width:400px; margin-bottom:14px; }
  button { background:#2d6b3e; color:#fff; border:none; padding:12px 32px; border-radius:8px; font-size:1rem; font-weight:700; cursor:pointer; width:100%; max-width:400px; }
  button:hover { background:#4caf72; }
  #result { margin-top:20px; background:#162a1e; border:1px solid #2d6b3e; border-radius:10px; padding:14px 18px; width:100%; max-width:400px; display:none; word-break:break-all; }
  #result a { color:#6fcf8f; font-weight:600; }
  #status { margin-top:12px; color:#8aaa97; font-size:0.85rem; }
  .copy { background:#1a3d2b; color:#6fcf8f; padding:8px; border-radius:6px; font-size:0.8rem; margin-top:10px; width:100%; }
</style>
</head>
<body>
<h2>⚔️ Kenshin File Upload</h2>
<input type="file" id="f" />
<button onclick="upload()">Upload & Get Link</button>
<div id="status"></div>
<div id="result">
  <div style="font-size:0.75rem;color:#8aaa97;margin-bottom:6px;">Your Link:</div>
  <a id="link" href="#" target="_blank"></a>
  <br/>
  <button class="copy" onclick="copy()">📋 Copy Link</button>
</div>
<script>
async function upload() {
  const file = document.getElementById('f').files[0];
  if (!file) return alert('File select karo pehle!');
  document.getElementById('status').textContent = '⏳ Uploading... please wait';
  document.getElementById('result').style.display = 'none';
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/upload', { method:'POST', body:form });
    const data = await res.json();
    if (data.url && data.url.startsWith('https://')) {
      document.getElementById('link').textContent = data.url;
      document.getElementById('link').href = data.url;
      document.getElementById('result').style.display = 'block';
      document.getElementById('status').textContent = '✅ Done!';
      navigator.clipboard.writeText(data.url).catch(()=>{});
    } else {
      document.getElementById('status').textContent = '❌ Error: ' + JSON.stringify(data);
    }
  } catch(e) {
    document.getElementById('status').textContent = '❌ Request failed: ' + e.message;
  }
}
function copy() {
  navigator.clipboard.writeText(document.getElementById('link').textContent);
  alert('Copied!');
}
</script>
</body>
</html>
"""

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    
    # Try with userhash first
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            "https://catbox.moe/user.php",
            data={
                "reqtype": "fileupload",
                "userhash": USERHASH
            },
            files={"fileToUpload": (file.filename, content, file.content_type)}
        )
    
    url = res.text.strip()
    
    # If response is not a valid URL, try anonymous upload as fallback
    if not url.startswith("https://files.catbox.moe"):
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                "https://catbox.moe/user.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (file.filename, content, file.content_type)}
            )
        url = res.text.strip()
    
    if not url.startswith("https://"):
        return JSONResponse({"error": "Upload failed", "catbox_response": url}, status_code=500)
    
    return JSONResponse({"url": url})

@app.get("/health")
async def health():
    return {"status": "ok"}
