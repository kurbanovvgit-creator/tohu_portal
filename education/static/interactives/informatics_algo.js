(function () {
    const root = document.getElementById("ix-info");
    if (!root) return;
    root.innerHTML = '<p>1-den n-e çenli sanlaryň jemini algoritm ädimme-ädim görkezýär.</p><label>n <input id="ix-n" type="number" min="1" max="10" value="4"></label><ol id="ix-info-steps"></ol><p id="ix-info-out"></p>';
    function draw() {
        const n = Math.max(1, Math.min(10, parseInt(document.getElementById("ix-n").value, 10) || 1));
        const list = document.getElementById("ix-info-steps");
        list.innerHTML = "";
        let sum = 0;
        for (let i = 1; i <= n; i++) {
            sum += i;
            const li = document.createElement("li");
            li.textContent = "i = " + i + ", jem = " + sum;
            list.appendChild(li);
        }
        document.getElementById("ix-info-out").textContent = "Netije: " + sum + ". Nusga: n=4 bolanda jem 10.";
    }
    document.getElementById("ix-n").addEventListener("input", draw);
    draw();
})();
