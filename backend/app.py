from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import numpy as np
import sqlite3
from tensorflow.keras.models import load_model
import requests
import os

# ✅ Flask config (correct)
app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# ---------- MODEL ----------
MODEL_PATH = "model.h5"
MODEL_URL = "https://model-drowsiness.s3.us-east-1.amazonaws.com/model.h5"

def download_model():
    try:
        print("Downloading model from S3...")
        r = requests.get(MODEL_URL, timeout=30)
        r.raise_for_status()

        with open(MODEL_PATH, "wb") as f:
            f.write(r.content)

        print("Model downloaded ✅")

    except Exception as e:
        print("❌ Error downloading model:", e)
        exit(1)

if not os.path.exists(MODEL_PATH):
    download_model()

model = load_model(MODEL_PATH)

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------- FRONTEND ----------
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "login.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# ---------- AUTH ----------
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?,?)",
              (data['username'], data['password']))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Registered"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (data['username'], data['password']))

    user = c.fetchone()
    conn.close()

    return jsonify({"msg": "success" if user else "fail"})

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
