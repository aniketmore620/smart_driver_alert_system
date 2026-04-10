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

# ✅ COPY BACKEND
COPY backend/ .

# ✅ COPY FRONTEND (IMPORTANT FIX)
COPY frontend/ /frontend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
