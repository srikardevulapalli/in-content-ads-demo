from ultralytics import YOLO
import subprocess
import tempfile
import cv2

# Load YOLO model (downloads if needed)
model = YOLO('yolov5s.pt')
SURFACE_CLASSES = {'chair','couch','tvmonitor','book','cell phone','mouse','keyboard'}

def analyze_video(path: str) -> dict:
    # Extract frame at 1s
    frame_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
    subprocess.run([
        'ffmpeg', '-y', '-i', path,
        '-ss', '00:00:01', '-vframes', '1', frame_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Detect surfaces
    results = model.predict(source=frame_path, imgsz=640)
    if results:
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

    # Fallback center region
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    return {
        'type': 'object_replacement',
        'timestamp': [0, 5],
        'tags': [],
        'overlay_region': {'x': w//4, 'y': h//4, 'w': w//2, 'h': h//2}
    }