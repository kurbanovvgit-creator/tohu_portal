(function () {
    const root = document.getElementById("ix-math");
    if (!root) return;
    root.innerHTML = '<p>a, b, c üýtgedeniňde grafik täzelenýär: y = ax² + bx + c</p><label>a <input id="ix-a" type="range" min="-3" max="3" value="1" step="0.1"></label> <label>b <input id="ix-b" type="range" min="-5" max="5" value="0" step="0.1"></label> <label>c <input id="ix-c" type="range" min="-5" max="5" value="0" step="0.1"></label><canvas id="ix-math-cv" width="640" height="360" style="width:100%;background:#04140f;border-radius:12px;margin-top:12px"></canvas><p id="ix-math-out"></p>';
    const cv = document.getElementById("ix-math-cv");
    const ctx = cv.getContext("2d");
    function draw() {
        const a = parseFloat(document.getElementById("ix-a").value);
        const b = parseFloat(document.getElementById("ix-b").value);
        const c = parseFloat(document.getElementById("ix-c").value);
        ctx.clearRect(0, 0, cv.width, cv.height);
        ctx.strokeStyle = "#14532d";
        ctx.beginPath();
        ctx.moveTo(0, 180); ctx.lineTo(640, 180);
        ctx.moveTo(320, 0); ctx.lineTo(320, 360);
        ctx.stroke();
        ctx.strokeStyle = "#4ade80";
        ctx.beginPath();
        for (let px = 0; px <= 640; px++) {
            const x = (px - 320) / 40;
            const y = a * x * x + b * x + c;
            const py = 180 - y * 40;
            if (px === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
        document.getElementById("ix-math-out").textContent = "y = " + a.toFixed(1) + "x² + " + b.toFixed(1) + "x + " + c.toFixed(1);
    }
    root.querySelectorAll("input").forEach((el) => el.addEventListener("input", draw));
    draw();
})();
