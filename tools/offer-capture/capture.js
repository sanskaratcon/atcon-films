// Captures v10's offer page for the WebGL fly-over (run: node capture.js http://localhost:8765/v10/ out, then convert
// out/*.png to public/assets/offer-fly/*.webp with ffmpeg -c:v libwebp): the page without its lifting pieces, each piece alone on
// transparent with 28px padding, and every piece's place on the page (CSS px) in layers.json
const { chromium } = require('playwright-core');
const fs = require('fs'), path = require('path');
const URL = process.argv[2] || 'http://localhost:8765/v10/';
const OUT = process.argv[3] || path.join(__dirname, 'out');
const DS = 1.5, PAD = 28;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: DS });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  // scroll to the offer once so the page builds its copy of the offer windows
  await page.evaluate(async () => {
    const t = document.querySelector('[data-atc=track]'), span = t.offsetHeight - innerHeight;
    window.scrollTo(0, Math.round(2080 / 2454 * span + t.offsetTop));
    for (let i = 0; i < 40 && !document.querySelector('.ofp .ofp-win .cvm'); i++) { window.dispatchEvent(new Event('scroll')); await new Promise(r => setTimeout(r, 100)); }
  });
  // a still copy of the page, flat, at the top left of an otherwise empty document
  const info = await page.evaluate((PAD) => {
    const src = document.querySelector('.ofp');
    const pg = src.cloneNode(true);
    pg.removeAttribute('data-atc'); pg.querySelectorAll('[data-atc]').forEach(e => e.removeAttribute('data-atc'));
    pg.querySelectorAll('.ofp-shadow').forEach(e => e.remove());
    pg.style.cssText = 'transform:none;height:3980px;overflow:visible;border-radius:0;box-shadow:none;position:absolute;left:0;top:0';
    pg.querySelectorAll('[data-lift]').forEach(e => { e.style.transform = 'none'; e.style.filter = 'none'; });
    const fade = pg.querySelector('.ofp-fade'); if (fade) fade.remove();
    const wrap = document.createElement('div'); wrap.className = 'atc'; wrap.id = 'capwrap';
    wrap.innerHTML = '<div class="atc-offer" style="position:static;display:block;opacity:1;visibility:visible;padding:0;margin:0;transform:none;clip-path:none"><div class="ofly" style="position:static;background:none;overflow:visible;visibility:visible;opacity:1;inset:auto;left:0;top:0"></div></div>';
    wrap.querySelector('.ofly').appendChild(pg);
    document.body.appendChild(wrap);
    // gradients referenced by the copy live in the hidden page; copy them so the A mark keeps its colours
    const g = document.getElementById('sol-amark'); if (g) { const sv = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); sv.setAttribute('width', '0'); sv.setAttribute('height', '0'); sv.style.position = 'absolute'; const d = document.createElementNS('http://www.w3.org/2000/svg', 'defs'); const c = g.cloneNode(true); d.appendChild(c); sv.appendChild(d); g.id = 'sol-amark-src'; wrap.appendChild(sv); }
    const st = document.createElement('style'); st.id = 'capst';
    st.textContent = 'html,body{overflow:visible!important;height:auto!important;background:transparent!important}body>*:not(#capwrap){display:none!important}' +
      '#capwrap{position:absolute;left:0;top:0;width:1440px;height:3980px;background:none!important;padding:0!important;margin:0!important}#capwrap .ofly{width:1440px;height:3980px;position:relative!important}';
    document.head.appendChild(st);
    return Array.prototype.map.call(pg.querySelectorAll('[data-lift]'), (e) => ({ id: e.getAttribute('data-lift'), x: e.offsetLeft, y: e.offsetTop, w: e.offsetWidth, h: e.offsetHeight }));
  }, PAD);
  await page.setViewportSize({ width: 1440, height: 3980 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  // the page with the pieces hidden
  await page.addStyleTag({ content: '#capwrap [data-lift]{visibility:hidden!important}' });
  await page.screenshot({ path: path.join(OUT, 'page.png'), clip: { x: 0, y: 0, width: 1440, height: 3980 } });
  // each piece alone
  await page.addStyleTag({ content: '#capwrap .ofp{background:transparent!important}#capwrap .ofp *{visibility:hidden!important}' });
  for (const l of info) {
    await page.evaluate((id) => {
      let s = document.getElementById('solo'); if (!s) { s = document.createElement('style'); s.id = 'solo'; document.head.appendChild(s); }
      s.textContent = '#capwrap [data-lift="' + id + '"],#capwrap [data-lift="' + id + '"] *{visibility:visible!important}#capwrap [data-lift="' + id + '"] .ofp-edge{visibility:hidden!important}';
    }, l.id);
    await page.screenshot({ path: path.join(OUT, 'piece-' + l.id + '.png'), omitBackground: true, clip: { x: l.x - PAD, y: l.y - PAD, width: l.w + PAD * 2, height: l.h + PAD * 2 } });
  }
  fs.writeFileSync(path.join(OUT, 'layers.json'), JSON.stringify({ width: 1440, height: 3980, scale: DS, pad: PAD, layers: info }));
  console.log('captured', info.length, 'pieces');
  await browser.close();
})();
