import os
import uuid
import shutil
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from perception import analyze_video
from intelligence import rank_ad
from augmentation import blend_uploaded

# Directories
BASE_DIR    = os.path.dirname(__file__)
ASSETS_DIR  = os.path.join(BASE_DIR, '..', 'assets')
UPLOAD_DIR  = os.path.join(ASSETS_DIR, 'uploads')
BLENDED_DIR = os.path.join(ASSETS_DIR, 'blended')

# Ensure folders exist
ios.makedirs(UPLOAD_DIR, exist_ok=True)
ios.makedirs(BLENDED_DIR, exist_ok=True)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(BASE_DIR, '..', 'frontend', 'index.html')).read()

@app.post("/api/upload_video")
async def upload_video(file: UploadFile = File(...)):
    # Save upload
    ext = os.path.splitext(file.filename)[1]
    vid_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{vid_id}{ext}")
    with open(path, 'wb') as buf:
        shutil.copyfileobj(file.file, buf)
    # Analyze for default slot
    meta = analyze_video(path)
    return {"video_id": vid_id, "ext": ext, "metadata": meta}

@app.post("/api/rank_and_blend")
async def rank_and_blend(req: Request):
    data    = await req.json()
    vid_id  = data["video_id"]
    ext     = data.get("ext", ".mp4")
    persona = data["persona"]
    slot    = data.get("slot", {"start":0, "duration":5})

    src     = os.path.join(UPLOAD_DIR, f"{vid_id}{ext}")
    meta    = analyze_video(src)
    best_ad = rank_ad(persona, meta)

    out_fn  = blend_uploaded(src, vid_id, best_ad, slot, meta.get('overlay_region', {}))
    return {
        "video_url": f"/assets/blended/{out_fn}",
        "decision":  f"Chose {best_ad['id']} at {slot['start']}s"
    }

@app.get("/assets/blended/{fn}")
def serve_video(fn: str):
    return FileResponse(os.path.join(BLENDED_DIR, fn), media_type="video/mp4")