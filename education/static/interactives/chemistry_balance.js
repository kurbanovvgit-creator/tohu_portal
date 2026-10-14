(function () {
    const root = document.getElementById("ix-chem");
    if (!root) return;
    root.innerHTML = '<p>H₂ + O₂ → H₂O. Koeffisiýentleri saýlaň. Dogry nusga: 2, 1, 2.</p><label>H₂ <input id="ix-h" type="number" min="1" max="6" value="1"></label> <label>O₂ <input id="ix-o" type="number" min="1" max="6" value="1"></label> <label>H₂O <input id="ix-w" type="number" min="1" max="6" value="1"></label><p id="ix-chem-out"></p>';
    function draw() {
        const h = parseInt(document.getElementById("ix-h").value, 10);
        const o = parseInt(document.getElementById("ix-o").value, 10);
        const w = parseInt(document.getElementById("ix-w").value, 10);
        const hOk = h === 2 * w / 2 && h === 2;
        const balanced = h === 2 && o === 1 && w === 2;
        const atomsH = h * 2 === w * 2;
        const atomsO = o * 2 === w;
        document.getElementById("ix-chem-out").textContent = balanced
            ? "Deňlenen. H atomlary: " + (h * 2) + " = " + (w * 2) + ", O atomlary: " + (o * 2) + " = " + w
            : "Heniz deň däl. H " + (atomsH ? "dogry" : "ýalňyş") + ", O " + (atomsO ? "dogry" : "ýalňyş") + ".";
        if (hOk) { /* marker for balanced hydrogen pair */ }
    }
    root.querySelectorAll("input").forEach((el) => el.addEventListener("input", draw));
    draw();
})();
