from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import cv2
import numpy as np
import sqlite3
import smtplib
from email.message import EmailMessage
from tensorflow.keras.models import load_model
import time
import requests
import os

# Flask setup
app = Flask(__name__, static_folder="../frontend/assets")
CORS(app)

# ---------- MODEL ----------
MODEL_PATH = "model.h5"
MODEL_URL = "https://your-bucket-name.s3.amazonaws.com/model.h5"  # 🔴 UPDATE THIS

def download_model():
    try:
        print("Downloading model...")
        r = requests.get(MODEL_URL, timeout=30)
        r.raise_for_status()
        with open(MODEL_PATH, "wb") as f:
            f.write(r.content)
        print("Model downloaded ✅")
    except Exception as e:
        print("Error downloading model:", e)
        raise

if not os.path.exists(MODEL_PATH):
    download_model()

model = load_model(MODEL_PATH)

# ---------- CASCADE ----------
face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
leye = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_lefteye_2splits.xml')
reye = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_righteye_2splits.xml')

# ---------- GLOBAL ----------
score = 0
yawn_start = 0

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------- EMAIL ----------
def send_email():
    try:
        loc = requests.get("http://ip-api.com/json").json()

        msg = EmailMessage()
        msg['Subject'] = "Drowsiness Alert"
        msg['From'] = "your_email@gmail.com"   # 🔴 UPDATE
        msg['To'] = "receiver@gmail.com"       # 🔴 UPDATE

        msg.set_content(f"Drowsiness detected!\nLocation: {loc['lat']},{loc['lon']}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("your_email@gmail.com", "your_app_password")  # 🔴 UPDATE
            smtp.send_message(msg)

    except Exception as e:
        print("Email error:", e)

# ---------- FRONTEND ROUTES ----------
@app.route("/")
def serve_login():
    return send_from_directory("../frontend/assets", "login.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("../frontend/assets", path)

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

# ---------- MODEL FUNCTIONS ----------
def predict_eye(img):
    img = cv2.resize(img, (24, 24))
    img = img / 255.0
    img = img.reshape(1, 24, 24, 1)

    pred = model.predict(img)
    return np.argmax(pred)

def detect_yawn(frame, x, y, w, h):
    global yawn_start

    mouth = frame[y + int(0.6*h):y + h, x + int(0.25*w):x + int(0.75*w)]
    gray = cv2.cvtColor(mouth, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        area = max(contours, key=cv2.contourArea)
        if cv2.contourArea(area) > 1500:
            if yawn_start == 0:
                yawn_start = time.time()
            elif time.time() - yawn_start > 2:
                yawn_start = 0
                return True
        else:
            yawn_start = 0

    return False

# ---------- MAIN PREDICT ----------
@app.route('/predict', methods=['POST'])
def predict():
    global score

    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face.detectMultiScale(gray, 1.1, 5)

    status = "Open"
    yawn_flag = False

    for (x, y, w, h) in faces:

        if detect_yawn(frame, x, y, w, h):
            yawn_flag = True

        left_eye = leye.detectMultiScale(gray)
        right_eye = reye.detectMultiScale(gray)

        lpred, rpred = 1, 1

        for (lx, ly, lw, lh) in left_eye:
            l_eye = gray[ly:ly+lh, lx:lx+lw]
            lpred = predict_eye(l_eye)
            break

        for (rx, ry, rw, rh) in right_eye:
            r_eye = gray[ry:ry+rh, rx:rx+rw]
            rpred = predict_eye(r_eye)
            break

        if lpred == 0 and rpred == 0:
            score += 1
            status = "Closed"
        else:
            score = 0
            status = "Open"

        if score > 5 or yawn_flag:
            send_email()

    return jsonify({
        "result": status,
        "score": score,
        "yawn": yawn_flag
    })

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)