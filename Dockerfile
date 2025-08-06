# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend, assets, frontend
COPY backend/ ./backend/
COPY assets/   ./assets/
COPY frontend/ ./frontend/

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] ffmpeg-python yolov5 torch torchvision openai

# Download YOLOv5 model for perception
RUN python - << 'EOF'
from yolov5 import YOLOv5
YOLOv5(model_path='yolov5s.pt', device='cpu')
EOF

# Expose port
EXPOSE 8000

# Launch application
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]