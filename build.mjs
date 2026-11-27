// Baut aus src/*.js die Schnellleisten-Links und die Download-Seite (_site/).
// Aufruf: npm run build
import { minify } from "terser";
import { readFile, writeFile, mkdir } from "node:fs/promises";

const SKRIPTE = [
  {
    datei: "raubzug-rechner",
    name: "Raubzug-Rechner",
    text: "Teilt deine Truppen optimal auf die Raubzug-Stufen auf: Ress pro Lauf, Ress pro Stunde oder gleiche Laufzeit, optional mit max. Laufzeit. Trägt die Truppen ein – abschicken tust du selbst.",
    wo: "Überall im Spiel klicken – öffnet den Raubzug mit dem Rechner.",
  },
  {
    datei: "spaeh-notiz",
    name: "Späh-Notiz",
    text: "Schreibt aus einem Spähbericht eine einzeilige Dorfnotiz: 🟢/🟡/🔴 Ampel, HG-Stufe, Wall, Ress/h, Minen und Spähzeitpunkt.",
    wo: "Im geöffneten Spähbericht klicken. Braucht einen Premium-Account (Dorfnotizen).",
  },
];
const MAX = 10000; // Längengrenze für Schnellleisten-Links

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

await mkdir("_site", { recursive: true });
const karten = [];
for (const s of SKRIPTE) {
  const quelle = await readFile(`src/${s.datei}.js`, "utf8");
  const { code } = await minify(quelle, { ecma: 2020, compress: true, mangle: true, format: { ascii_only: false } });
  // Browser dekodieren javascript:-Links wie URLs: aus "t%3600" würde sonst "t600".
  const link = "javascript:" + code.replace(/%/g, "%25");
  if (link.length > MAX) throw new Error(`${s.datei}: ${link.length} Zeichen, erlaubt sind ${MAX}`);
  await writeFile(`_site/${s.datei}.txt`, link + "\n");
  console.log(`${s.datei}: ${link.length} Zeichen`);
  karten.push(`
  <section>
    <h2>${esc(s.name)}</h2>
    <p>${esc(s.text)}</p>
    <p class="wo">${esc(s.wo)}</p>
    <div class="knoepfe">
      <button data-code="${esc(link)}">Code kopieren</button>
      <a class="bm" href="${esc(link)}" title="In die Lesezeichenleiste ziehen">⭐ ${esc(s.name)}</a>
      <span class="info">${link.length.toLocaleString("de-DE")} Zeichen · <a href="${s.datei}.txt">als Text</a> · <a href="https://github.com/Datata1/ds-skripte/blob/main/src/${s.datei}.js">Quelltext</a></span>
    </div>
  </section>`);
}

const seite = `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DS-Skripte</title>
<style>
:root{--bg:#f4e4bc;--karte:#fff8e5;--rand:#c1a264;--text:#3b2a14;--leise:#7a6440;--akzent:#804000}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 Verdana,Arial,sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px}
h1{font-size:1.6em;margin:0 0 4px}
.unter{color:var(--leise);margin:0 0 24px}
section{background:var(--karte);border:1px solid var(--rand);border-radius:6px;padding:16px;margin-bottom:16px}
h2{margin:0 0 6px;font-size:1.2em;color:var(--akzent)}
p{margin:0 0 8px}.wo{color:var(--leise);font-size:.9em}
.knoepfe{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
button{background:var(--akzent);color:#fff;border:0;border-radius:4px;padding:9px 16px;font:inherit;cursor:pointer}
button.ok{background:#2e7d32}
.bm{border:1px dashed var(--rand);border-radius:4px;padding:7px 12px;color:var(--text);text-decoration:none;cursor:grab}
.info{color:var(--leise);font-size:.85em}.info a{color:var(--akzent)}
ol{padding-left:20px;margin:0}li{margin-bottom:4px}
</style>
</head>
<body>
<main>
<h1>DS-Skripte</h1>
<p class="unter">Immer die aktuelle Version – direkt aus dem Quelltext gebaut.</p>
<section>
  <h2>So kommt ein Skript in die Schnellleiste</h2>
  <ol>
    <li>Unten bei einem Skript auf <b>Code kopieren</b> klicken.</li>
    <li>Im Spiel: <b>Einstellungen → Schnellleiste bearbeiten → Link hinzufügen</b>.</li>
    <li>Einen Namen eintragen, den Code bei <b>Ziel-URL</b> einfügen, speichern.</li>
  </ol>
  <p class="wo">Alternativ den ⭐-Knopf in die Lesezeichenleiste des Browsers ziehen.</p>
</section>
${karten.join("\n")}
<p class="wo">Die Skripte lesen nur die offene Seite und machen eine Aktion pro Klick. Sie sind nicht offiziell in der Skript-Bibliothek freigegeben – Nutzung auf eigene Verantwortung.</p>
</main>
<script>
document.querySelectorAll("button[data-code]").forEach(b=>b.onclick=async()=>{
  try{await navigator.clipboard.writeText(b.dataset.code)}catch(e){const t=document.createElement("textarea");t.value=b.dataset.code;document.body.append(t);t.select();document.execCommand("copy");t.remove()}
  b.textContent="Kopiert ✓";b.classList.add("ok");setTimeout(()=>{b.textContent="Code kopieren";b.classList.remove("ok")},1800)});
document.querySelectorAll("a.bm").forEach(a=>a.onclick=e=>{e.preventDefault();alert("Diesen Knopf in die Lesezeichenleiste ziehen – oder im Spiel anklicken.")});
</script>
</body>
</html>
`;
await writeFile("_site/index.html", seite);
console.log("_site/index.html geschrieben");
