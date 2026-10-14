(function () {
    const root = document.getElementById("ix-physics");
    if (!root) return;
    root.innerHTML = '<p>U we R üýtgedeniňde tok I = U / R täzelenýär.</p><label>U, V <input id="ix-u" type="range" min="1" max="24" value="12"></label> <label>R, Om <input id="ix-r" type="range" min="1" max="20" value="4"></label><p id="ix-phys-out" style="font-size:1.3rem"></p><svg id="ix-phys-svg" viewBox="0 0 320 120" style="width:100%;background:#04140f;border-radius:12px"></svg>';
    function draw() {
        const u = parseFloat(document.getElementById("ix-u").value);
        const r = parseFloat(document.getElementById("ix-r").value);
        const i = u / r;
        document.getElementById("ix-phys-out").textContent = "I = " + i.toFixed(2) + " A  (nusga: 12 V / 4 Om = 3 A)";
        const glow = Math.min(12, i);
        document.getElementById("ix-phys-svg").innerHTML = '<rect x="20" y="30" width="280" height="60" fill="none" stroke="#4ade80" stroke-width="' + (1 + glow / 4) + '"/><text x="40" y="66" fill="#ecfdf5">U=' + u + 'V</text><text x="150" y="66" fill="#ecfdf5">R=' + r + 'Ω</text><text x="240" y="66" fill="#86efac">I=' + i.toFixed(2) + 'A</text>';
    }
    root.querySelectorAll("input").forEach((el) => el.addEventListener("input", draw));
    draw();
})();
