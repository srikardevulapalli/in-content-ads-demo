import os
import uuid
import shutil
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from perception import analyze_video
from intelligence import rank_ad
from augmentation import blend_uploaded

# Directories
BASE_DIR    = os.path.dirname(__file__)
ASSETS_DIR  = os.path.join(BASE_DIR, '..', 'assets')
UPLOAD_DIR  = os.path.join(ASSETS_DIR, 'uploads')
BLENDED_DIR = os.path.join(ASSETS_DIR, 'blended')

# Ensure folders exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BLENDED_DIR, exist_ok=True)

app = FastAPI()

# Serve frontend static files (index.html, script.js, etc.)
app.mount(
    "/",
    StaticFiles(directory=os.path.join(BASE_DIR, '..', 'frontend'), html=True),
    name="frontend"
)

@app.post("/api/upload_video")
async def upload_video(file: UploadFile = File(...)):
    # Save uploaded file
    ext = os.path.splitext(file.filename)[1]
    vid_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{vid_id}{ext}")
    with open(save_path, 'wb') as buf:
        shutil.copyfileobj(file.file, buf)
    meta = analyze_video(save_path)
    return {"video_id": vid_id, "ext": ext, "metadata": meta}

@app.post("/api/rank_and_blend")
async def rank_and_blend(req: Request):
    data = await req.json()
    vid_id  = data.get("video_id")
    ext     = data.get("ext", ".mp4")
    persona = data.get("persona", {})
    slot    = data.get("slot", {"start": 0, "duration": 5})

    src_path = os.path.join(UPLOAD_DIR, f"{vid_id}{ext}")
    meta = analyze_video(src_path)
    best_ad = rank_ad(persona, meta)

    out_fn = blend_uploaded(src_path, vid_id, best_ad, slot, meta.get('overlay_region', {}))
    return {
        "video_url": f"/assets/blended/{out_fn}",
        "decision": f"Chose {best_ad['id']} at {slot['start']}s"
    }

@app.get("/assets/blended/{fn}")
def serve_blended(fn: str):
    return FileResponse(os.path.join(BLENDED_DIR, fn), media_type="video/mp4")