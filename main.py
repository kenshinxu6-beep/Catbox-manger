from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

USERHASH = "58d2aa145609ebabc8b351530"
CATBOX_API = "https://catbox.moe/user.php"

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(CATBOX_API, data={
            "reqtype": "fileupload",
            "userhash": USERHASH
        }, files={"fileToUpload": (file.filename, content, file.content_type)})
    url = res.text.strip()
    if not url.startswith("https://"):
        return JSONResponse({"error": url}, status_code=500)
    return JSONResponse({"url": url})

@app.get("/health")
async def health():
    return {"status": "ok"}
