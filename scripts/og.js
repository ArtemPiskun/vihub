// Генерирует OG-картинки 1200x630 для всех страниц: node scripts/og.js (нужен playwright)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..'), OUT = path.join(ROOT, 'assets', 'og');
fs.mkdirSync(OUT, { recursive: true });
function guides(lang) {
  const dir = path.join(ROOT, 'content', 'guides', lang === 'ru' ? '' : lang);
  return fs.readdirSync(dir).filter(f => f.endsWith('.md')).map(f => {
    const t = fs.readFileSync(path.join(dir, f), 'utf8');
    const g = k => ((t.match(new RegExp('^' + k + ':\\s*(.+)$', 'm')) || [])[1] || '');
    return { name: `${lang}-g-${f.replace('.md', '')}`, title: g('title'), kicker: g('category') };
  });
}
const pages = [
  { name: 'default', title: 'GTA 6: новости, гайды, время релиза', kicker: '19.11.2026' },
  { name: 'ru-home', title: 'GTA 6: всё о Леониде в одном месте', kicker: 'Релиз 19 ноября 2026' },
  { name: 'ru-news', title: 'Новости GTA 6 каждые 15 минут', kicker: 'Новости' },
  { name: 'ru-guides', title: 'Гайды и прохождение GTA 6', kicker: 'Гайды' },
  { name: 'ru-videos', title: 'Что стреляет на YouTube по GTA 6', kicker: 'Видео' },
  { name: 'ru-creators', title: 'Рейтинг блогеров GTA 6', kicker: 'Рейтинг' },
  { name: 'ru-game', title: 'GTA 6: дата, цена, карта, персонажи', kicker: 'Об игре' },
  { name: 'en-home', title: 'GTA 6: everything about Leonida', kicker: 'Launch Nov 19, 2026' },
  { name: 'en-news', title: 'GTA 6 news every 15 minutes', kicker: 'News' },
  { name: 'en-guides', title: 'GTA 6 guides and walkthrough', kicker: 'Guides' },
  { name: 'en-videos', title: 'Trending GTA 6 videos', kicker: 'Videos' },
  { name: 'en-creators', title: 'Top GTA 6 YouTubers', kicker: 'Creators' },
  { name: 'en-game', title: 'GTA 6 release date, price, map', kicker: 'The game' },
  { name: 'uk-home', title: 'GTA 6: усе про Леоніду в одному місці', kicker: 'Реліз 19 листопада 2026' },
  { name: 'uk-news', title: 'Новини GTA 6 кожні 15 хвилин', kicker: 'Новини' },
  { name: 'uk-guides', title: 'Гайди та проходження GTA 6', kicker: 'Гайди' },
  { name: 'uk-videos', title: 'Що стріляє на YouTube про GTA 6', kicker: 'Відео' },
  { name: 'uk-creators', title: 'Рейтинг блогерів GTA 6', kicker: 'Рейтинг' },
  { name: 'uk-game', title: 'GTA 6: дата, ціна, карта, персонажі', kicker: 'Про гру' },
  ...guides('ru'), ...guides('en'), ...guides('uk'),
];
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const tpl = p => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600&family=Unbounded:wght@800&display=swap" rel="stylesheet">
<style>*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;background:#0b0a12;color:#f3eefc;font-family:Inter,sans-serif;overflow:hidden;position:relative}
.bg{position:absolute;inset:0;background:radial-gradient(900px 420px at 85% 115%,rgba(255,62,154,.45),transparent 60%),radial-gradient(700px 360px at 0% -10%,rgba(139,92,246,.35),transparent 60%)}
.sun{position:absolute;right:-90px;bottom:-250px;width:620px;height:620px;border-radius:50%;background:repeating-linear-gradient(180deg,transparent 0 24px,#0b0a12 24px 33px),linear-gradient(100deg,#ff3e9a,#ff9a3c);opacity:.7;-webkit-mask:linear-gradient(180deg,#000 40%,transparent)}
.in{position:absolute;inset:64px 72px;display:flex;flex-direction:column;justify-content:space-between}
.logo{font-family:Unbounded;font-size:34px}.logo b{background:linear-gradient(100deg,#ff3e9a,#ff9a3c);-webkit-background-clip:text;color:transparent}.logo span{font-size:18px;letter-spacing:.2em;margin-left:8px}
.k{color:#2de2d0;font-size:26px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:18px}
h1{font-family:Unbounded;font-size:${p.title.length > 48 ? 50 : 62}px;line-height:1.08;max-width:900px}</style></head>
<body><div class="bg"></div><div class="sun"></div><div class="in"><div class="logo"><b>VI</b><span>HUB</span></div>
<div><div class="k">${esc(p.kicker)}</div><h1>${esc(p.title)}</h1></div></div></body></html>`;
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const p of pages) {
    await pg.setContent(tpl(p), { waitUntil: 'networkidle' }).catch(() => pg.setContent(tpl(p)));
    await pg.screenshot({ path: path.join(OUT, p.name + '.jpg'), type: 'jpeg', quality: 82 });
  }
  await b.close(); console.log('og:', pages.length);
})();
