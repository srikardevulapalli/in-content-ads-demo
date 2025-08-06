from yolov5 import YOLOv5
import subprocess, tempfile, cv2

yolo = YOLOv5(model_path='yolov5s.pt', device='cpu')

def analyze_video(path: str) -> dict:
    """
    Sample frame at 1s, detect a surface, return ad slot metadata.
    """
    # extract frame
    frame = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
    subprocess.run([
        'ffmpeg', '-y', '-i', path,
        '-ss', '00:00:01', '-vframes', '1', frame
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # run detection
    results = yolo.predict(frame, imgsz=640)
    surfaces = {'chair','couch','tvmonitor','book','cell phone','mouse','keyboard'}
    for det in results.pred[0]:
        cls = results.names[int(det[5])]
        if cls in surfaces:
            x1,y1,x2,y2 = map(int, det[:4])
            return {
                'type': 'object_replacement',
                'timestamp': [0,5],
                'tags': [cls],
                'overlay_region': {'x':x1,'y':y1,'w':x2-x1,'h':y2-y1}
            }
    # fallback center box
    img = cv2.imread(frame)
    h,w = img.shape[:2]
    return {
        'type': 'object_replacement',
        'timestamp': [0,5],
        'tags': [],
        'overlay_region': {'x':w//4,'y':h//4,'w':w//2,'h':h//2}
    }