// Exporta la presentación y el informe a archivos que se pueden entregar:
//   - cada diapositiva de docs/presentacion/fuente/ a PNG de 1920 × 1080 (docs/presentacion/png/)
//   - docs/presentacion/presentacion-fase2.pdf (una página por diapositiva)
//   - docs/informe-fase2.pdf (desde el HTML que genera pandoc)
// El PPTX lo arma exportar_pptx.py a partir de los PNG y las notas.
//
//   NODE_PATH=$(npm root -g) node exportar_documentos.js <informe.html>
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const RAIZ = path.join(__dirname, "..");
const DECK = path.join(RAIZ, "docs", "presentacion");
const FUENTE = path.join(DECK, "fuente");
const IMG = path.join(RAIZ, "img");

async function main() {
  const indice = JSON.parse(fs.readFileSync(path.join(FUENTE, "deck.json"), "utf8"));
  const imagenes = JSON.parse(fs.readFileSync(path.join(FUENTE, "imagenes.json"), "utf8"));
  const fuentes = fs.readFileSync(path.join(DECK, "fuentes-tipograficas", "fonts-local.css"), "utf8")
    .replace(/url\((f\d+\.woff2)\)/g, (_, f) => `url(file://${path.join(DECK, "fuentes-tipograficas", f)})`);
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage({ viewport: { width: 1920, height: 1080 } });
  fs.mkdirSync(path.join(DECK, "png"), { recursive: true });
  const notas = {};
  let todas = "";
  for (const [i, id] of indice.order.entries()) {
    let html = fs.readFileSync(path.join(FUENTE, "slides", `${id}.html`), "utf8");
    html = html.replace(/\/_blob\/([0-9a-f]{32})/g, (_, b) => `file://${path.join(IMG, imagenes[b])}`);
    const nota = html.match(/<aside>([\s\S]*?)<\/aside>/);
    notas[id] = nota ? nota[1].trim() : "";
    html = html.replace(/<aside>[\s\S]*?<\/aside>/, "");
    const estilo = `<style>${fuentes}
      *{margin:0;box-sizing:border-box} html,body{width:1920px;height:1080px;overflow:hidden}
      section{width:1920px;height:1080px;position:relative;overflow:hidden}
      ol,ul{padding-left:40px} th,td{padding:0.35em 0.6em;text-align:left;border-bottom:1px solid #cfd4dd}
      table{border-collapse:collapse} h1,h2,h3{font-weight:600}</style>`;
    const doc = `<!doctype html><html><head><meta charset="utf-8">${estilo}</head><body>${html}</body></html>`;
    // se abre como archivo: una página hecha con setContent no puede cargar imágenes ni fuentes locales
    const tmp = path.join(DECK, "png", `_tmp.html`);
    fs.writeFileSync(tmp, doc);
    await pagina.goto("file://" + tmp, { waitUntil: "load" });
    await pagina.evaluate(() => document.fonts.ready);
    const salida = path.join(DECK, "png", `${String(i + 1).padStart(2, "0")}-${id}.png`);
    await pagina.screenshot({ path: salida });
    todas += `<img src="file://${salida}" style="width:1920px;height:1080px;display:block;page-break-after:always">`;
    console.log("PNG", path.basename(salida));
  }
  fs.writeFileSync(path.join(DECK, "notas.json"), JSON.stringify({ orden: indice.order, notas }, null, 1));
  // PDF de la presentación: una página de 1920 × 1080 px por diapositiva
  const tmp = path.join(DECK, "png", "_tmp.html");
  fs.writeFileSync(tmp, `<!doctype html><html><head><style>*{margin:0}@page{size:1920px 1080px;margin:0}</style></head><body>${todas}</body></html>`);
  await pagina.goto("file://" + tmp, { waitUntil: "load" });
  fs.unlinkSync(tmp);
  await pagina.pdf({ path: path.join(DECK, "presentacion-fase2.pdf"), width: "1920px", height: "1080px", printBackground: true });
  console.log("PDF presentacion-fase2.pdf");
  // PDF del informe
  const informe = process.argv[2];
  if (informe) {
    const p2 = await navegador.newPage();
    await p2.goto("file://" + informe, { waitUntil: "load" });
    await p2.pdf({ path: path.join(RAIZ, "docs", "informe-fase2.pdf"), format: "Letter", printBackground: true,
      margin: { top: "18mm", bottom: "18mm", left: "18mm", right: "18mm" } });
    console.log("PDF informe-fase2.pdf");
  }
  await navegador.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
