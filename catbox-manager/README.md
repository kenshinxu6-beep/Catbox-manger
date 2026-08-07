# ⚔️ Kenshin Anime — File Vault

Catbox.moe powered file manager for storing PFPs, Banners, and Videos for your website.

## Files
- `main.py` — FastAPI backend
- `index.html` — Frontend UI (served by FastAPI)
- `requirements.txt` — Python dependencies
- `render.yaml` — Render deploy config

## Deploy on Render (Web Service)

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — just click **Deploy**
5. Done! Your vault is live.

## Optional: Catbox Account (for Delete support)

1. Create account on [catbox.moe](https://catbox.moe)
2. Go to your profile → copy your **userhash**
3. In Render dashboard → Environment → set `CATBOX_USERHASH` = your hash
4. Now delete button will also remove files from Catbox servers

Without userhash: files upload anonymously (still works, just can't delete from Catbox servers)

## Limits
- Max file size: **8MB** (enforced on both frontend + backend)
- Supported: PNG, JPG, GIF, WEBP, MP4, MKV, WebM, AVI
- Categories: PFP, Banner, Video, Other

## Local Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Open http://localhost:8000
```
