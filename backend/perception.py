# Simplified perception using Ultralytics YOLO to avoid pickle issues
from ultralytics import YOLO
import subprocess
import tempfile
import cv2

# Load model (downloads weights if not present)
model = YOLO('yolov5s.pt')

# Classes we treat as surfaces
SURFACE_CLASSES = {'chair','couch','tvmonitor','book','cell phone','mouse','keyboard'}

def analyze_video(path: str) -> dict:
    """
    Sample a frame at 1s, detect a surface, return metadata for ad slot.
    """
    # extract frame
    frame_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
    subprocess.run([
        'ffmpeg', '-y', '-i', path,
        '-ss', '00:00:01', '-vframes', '1', frame_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # run detection (Ultralytics returns list of Results)
    results = model.predict(source=frame_path, imgsz=640)
    if results and len(results) > 0:
        res = results[0]
        for box in res.boxes:
            cls = res.names[int(box.cls[0])]
            if cls in SURFACE_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                return {
                    'type': 'object_replacement',
                    'timestamp': [0, 5],
                    'tags': [cls],
                    'overlay_region': {'x': x1, 'y': y1, 'w': x2-x1, 'h': y2-y1}
                }
    # fallback: center region
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    return {
        'type': 'object_replacement',
        'timestamp': [0, 5],
        'tags': [],
        'overlay_region': {'x': w//4, 'y': h//4, 'w': w//2, 'h': h//2}
    }


---

### backend/intelligence.py
```python
import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

ADS = [
    {'id': 'AD-001', 'file': 'logitech_gpro_mouse.png', 'keywords': ['gaming','tech','performance','pc']},
    {'id': 'AD-002', 'file': 'redbull_can.png',       'keywords': ['gaming','energy','drink']},
]

def rank_ad(persona: dict, opportunity: dict) -> dict:
    prompt = (
        f"Persona interests: {persona.get('interests')}\n"
        f"Scene tags: {opportunity.get('tags')}\n"
        "Ads:\n"
    ) + ''.join([f"- {ad['id']}: keywords={ad['keywords']}\n" for ad in ADS])
    prompt += "\nPlease return only the best ad ID."
    try:
        res = openai.Completion.create(
            model='gpt-4o-mini',
            prompt=prompt,
            max_tokens=5,
            temperature=0.2
        )
        choice = res.choices[0].text.strip().split()[0]
        return next(ad for ad in ADS if ad['id'] == choice)
    except Exception:
        # Fallback to simple keyword overlap
        context = set(persona.get('interests', [])) | set(opportunity.get('tags', []))
        best, score = None, -1
        for ad in ADS:
            s = len(context & set(ad['keywords']))
            if s > score:
                best, score = ad, s
        return best