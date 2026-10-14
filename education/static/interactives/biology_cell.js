(function () {
    const root = document.getElementById("ix-bio");
    if (!root) return;
    const parts = [
        ["Ýadro", "Nesil maglumatyny saklaýar we öýjügi dolandyrýar."],
        ["Mitohondriýa", "Dem alyş arkaly energiýa öndürýär."],
        ["Membrana", "Maddalaryň girip-çykmagyny dolandyrýar."],
        ["Sitoplazma", "Organoidleriň ýerleşýän suwuk gurşawy."]
    ];
    root.innerHTML = '<p>Bölegi saýlaň — wezipesi açylýar.</p><div id="ix-bio-btns" style="display:flex;flex-wrap:wrap;gap:8px"></div><p id="ix-bio-out">Bölek saýlanmady.</p>';
    const box = document.getElementById("ix-bio-btns");
    parts.forEach((part) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = part[0];
        btn.addEventListener("click", () => {
            document.getElementById("ix-bio-out").textContent = part[0] + ": " + part[1];
        });
        box.appendChild(btn);
    });
})();
