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