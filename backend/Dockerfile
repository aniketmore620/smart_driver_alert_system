FROM python:3.10-slim

WORKDIR /app

# Install dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# ✅ Install Python dependencies FIRST (cache optimization)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy backend code
COPY backend/ .

# ✅ Copy frontend correctly (IMPORTANT FIX)
COPY frontend/ ./frontend

EXPOSE 5000

CMD ["python", "app.py"]
