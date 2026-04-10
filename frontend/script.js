const API = "";  // ✅ IMPORTANT FIX (no localhost)

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
            window.location.href = "dashboard.html";  // ✅ FIX
        } else {
            alert("Login failed");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
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
        window.location.href = "login.html";
    })
    .catch(err => {
        console.error(err);
        alert("Error");
    });
}

function goRegister() {
    window.location.href = "register.html";
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

                let isDrowsy = (data.score >= 3 || data.yawn);

                if (isDrowsy) {
                    drowsyFrames++;
                    normalFrames = 0;
                } else {
                    normalFrames++;
                    drowsyFrames = 0;
                }

                if (drowsyFrames >= 2 && !alarmCooldown) {
                    if (lastState !== "drowsy") {
                        document.getElementById("alarm").play();
                        document.getElementById("wakeup").play();

                        lastState = "drowsy";
                        alarmCooldown = true;

                        setTimeout(() => {
                            alarmCooldown = false;
                        }, 4000);
                    }
                }

                if (normalFrames >= 3) {
                    if (lastState === "drowsy") {
                        document.getElementById("safe").play();
                        lastState = "normal";
                    }
                }

            });

        });

    }, 2000);
}
