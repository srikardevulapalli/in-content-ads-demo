# Base image
FROM python:3.11-slim

# Install system dependencies for OpenCV and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY backend/ ./backend/
COPY assets/   ./assets/
COPY frontend/ ./frontend/

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] ffmpeg-python ultralytics torch torchvision openai

# Expose port
EXPOSE 8000

# Launch application
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
