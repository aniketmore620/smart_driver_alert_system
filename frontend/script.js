const API = "http://127.0.0.1:5000";

// ---------- GLOBAL STATE ----------
let lastState = "normal";
let drowsyFrames = 0;
let normalFrames = 0;
let alarmCooldown = false;

// ---------- LOGIN ----------
function login() {
    fetch(API + "/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.msg === "success") {
            window.location = "dashboard.html";
        } else {
            alert("Login failed");
        }
    });
}

// ---------- REGISTER ----------
function register() {
    fetch(API + "/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.msg);
        window.location = "login.html";
    });
}

function goRegister() {
    window.location = "register.html";
}

// ---------- CAMERA ----------
const video = document.getElementById("video");

if (video) {
    navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => video.srcObject = stream);
}

// ---------- TEST ALARM ----------
function testAlarm() {
    document.getElementById("alarm").play();
}

// ---------- DETECTION ----------
function startDetection() {

    setInterval(() => {

        let canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        let ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        canvas.toBlob(blob => {

            let formData = new FormData();
            formData.append("image", blob);

            fetch(API + "/predict", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {

                document.getElementById("result").innerText =
                    `Status: ${data.result} | Score: ${data.score} | Yawn: ${data.yawn}`;

                let isDrowsy = (data.score >= 3 || data.yawn); // 🔥 LOWERED THRESHOLD

                // ---------- SMOOTHING ----------
                if (isDrowsy) {
                    drowsyFrames++;
                    normalFrames = 0;
                } else {
                    normalFrames++;
                    drowsyFrames = 0;
                }

                // ---------- TRIGGER DROWSY ----------
                if (drowsyFrames >= 2 && !alarmCooldown) {  // 🔥 REDUCED

                    if (lastState !== "drowsy") {
                        document.getElementById("alarm").play();
                        document.getElementById("wakeup").play();

                        lastState = "drowsy";
                        alarmCooldown = true;

                        setTimeout(() => {
                            alarmCooldown = false;
                        }, 4000); // 🔥 shorter cooldown
                    }
                }

                // ---------- BACK TO NORMAL ----------
                if (normalFrames >= 3) {  // 🔥 REDUCED

                    if (lastState === "drowsy") {
                        document.getElementById("safe").play();
                        lastState = "normal";
                    }
                }

            });

        });

    }, 2000);
}