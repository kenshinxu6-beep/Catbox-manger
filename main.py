from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import os
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Kenshin Anime File Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CATBOX_API = "https://catbox.moe/user.php"
USERHASH = os.getenv("CATBOX_USERHASH", "")  # optional: for account uploads
MAX_SIZE_MB = 8
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

STORAGE_FILE = "uploaded_files.json"

def load_files():
    if Path(STORAGE_FILE).exists():
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

def save_files(files):
    with open(STORAGE_FILE, "w") as f:
        json.dump(files, f, indent=2)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(default="other")
):
    # Read file
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {MAX_SIZE_MB}MB. Your file: {file_size / (1024*1024):.2f}MB"
        )
    
    # Allowed types
    allowed_types = {
        "pfp": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "banner": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "video": ["video/mp4", "video/webm", "video/mkv", "video/avi", "video/mov"],
        "other": None  # allow all
    }
    
    content_type = file.content_type or "application/octet-stream"
    
    if category in allowed_types and allowed_types[category]:
        if content_type not in allowed_types[category]:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid file type '{content_type}' for category '{category}'"
            )
    
    # Upload to Catbox
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            form_data = {
                "reqtype": "fileupload",
            }
            if USERHASH:
                form_data["userhash"] = USERHASH
            
            response = await client.post(
                CATBOX_API,
                data=form_data,
                files={"fileToUpload": (file.filename, content, content_type)}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Catbox upload failed")
            
            url = response.text.strip()
            if not url.startswith("https://"):
                raise HTTPException(status_code=502, detail=f"Catbox error: {url}")
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upload timed out. Try again.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    
    # Save to local storage
    files = load_files()
    entry = {
        "id": len(files) + 1,
        "name": file.filename,
        "url": url,
        "category": category,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "type": content_type,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    files.append(entry)
    save_files(files)
    
    return JSONResponse({
        "success": True,
        "url": url,
        "name": file.filename,
        "category": category,
        "size_mb": entry["size_mb"]
    })

@app.delete("/delete/{file_id}")
async def delete_file(file_id: int, url: str = ""):
    files = load_files()
    file_entry = next((f for f in files if f["id"] == file_id), None)
    
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found in records")
    
    # Delete from Catbox (only works with userhash)
    catbox_deleted = False
    if USERHASH and file_entry.get("url"):
        filename = file_entry["url"].split("/")[-1]
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(CATBOX_API, data={
                    "reqtype": "deletefiles",
                    "userhash": USERHASH,
                    "files": filename
                })
                catbox_deleted = response.status_code == 200
        except:
            pass
    
    # Remove from local records
    files = [f for f in files if f["id"] != file_id]
    save_files(files)
    
    return JSONResponse({
        "success": True,
        "catbox_deleted": catbox_deleted,
        "message": "Removed from records" + (" and Catbox" if catbox_deleted else " (Catbox delete needs userhash)")
    })

@app.get("/files")
async def get_files(category: str = ""):
    files = load_files()
    if category:
        files = [f for f in files if f.get("category") == category]
    return JSONResponse({"files": files, "total": len(files)})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Kenshin Anime File Manager"}
