(function () {
  var b = document.querySelector('.burger'), n = document.querySelector('.nav');
  if (b && n) b.addEventListener('click', function () {
    var o = n.classList.toggle('open'); b.setAttribute('aria-expanded', o);
  });

  // обратный отсчёт до полуночи 19 ноября по местному времени зрителя
  var W = {
    ru: { d: ['день', 'дня', 'дней'], h: ['час', 'часа', 'часов'], m: ['минута', 'минуты', 'минут'], s: ['секунда', 'секунды', 'секунд'] },
    en: { d: ['day', 'days'], h: ['hour', 'hours'], m: ['minute', 'minutes'], s: ['second', 'seconds'] }
  };
  function form(lang, k, v) {
    if (lang === 'en') return W.en[k][v === 1 ? 0 : 1];
    var n = v % 100, n1 = n % 10;
    return W.ru[k][(n > 10 && n < 20) ? 2 : n1 === 1 ? 0 : (n1 > 1 && n1 < 5) ? 1 : 2];
  }
  document.querySelectorAll('.countdown').forEach(function (el) {
    var lang = el.getAttribute('data-lang') === 'en' ? 'en' : 'ru';
    var iso = el.getAttribute('data-release') || '';
    var m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
    var target = m ? new Date(+m[1], +m[2] - 1, +m[3], 0, 0, 0) : new Date(iso);
    var grid = el.querySelector('.cd-grid'), done = el.querySelector('.cd-done');
    function pad(x) { return (x < 10 ? '0' : '') + x; }
    function tick() {
      var s = Math.floor((target - Date.now()) / 1000);
      if (s <= 0) { grid.hidden = true; el.querySelector('.cd-label').hidden = true; done.hidden = false; return; }
      var v = { d: Math.floor(s / 86400), h: Math.floor(s / 3600) % 24, m: Math.floor(s / 60) % 60, s: s % 60 };
      for (var k in v) {
        var x = el.querySelector('[data-u="' + k + '"]'); if (!x) continue;
        x.textContent = k === 'd' ? v[k] : pad(v[k]);
        x.nextElementSibling.textContent = form(lang, k, v[k]);
      }
      setTimeout(tick, 1000);
    }
    tick();
  });

  // фильтр новостей
  document.querySelectorAll('.chips').forEach(function (bar) {
    var list = document.querySelector(bar.getAttribute('data-target'));
    bar.addEventListener('click', function (ev) {
      var c = ev.target.closest('.chip'); if (!c || !list) return;
      bar.querySelectorAll('.chip').forEach(function (x) { x.classList.toggle('active', x === c); });
      var f = c.getAttribute('data-f');
      list.querySelectorAll('[data-cat]').forEach(function (card) {
        card.hidden = !(f === 'all' || card.getAttribute('data-cat') === f);
      });
    });
  });

  // лёгкая вставка YouTube: iframe грузится только по клику (быстрее LCP)
  document.querySelectorAll('.yt').forEach(function (el) {
    el.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + el.getAttribute('data-id') + '?autoplay=1';
      f.allow = 'autoplay; encrypted-media; picture-in-picture'; f.allowFullscreen = true; f.title = 'YouTube';
      el.innerHTML = ''; el.appendChild(f);
    }, { once: true });
  });
  // мобильная плашка Telegram: появляется после прокрутки, закрывается навсегда
  var bar = document.querySelector('.tg-bar'), closed = false;
  try { closed = localStorage.getItem('tgbar') === '1'; } catch (e) {}
  if (bar && !closed) {
    window.addEventListener('scroll', function onS() {
      if (window.scrollY > 600) { bar.hidden = false; window.removeEventListener('scroll', onS); }
    }, { passive: true });
    bar.querySelector('.tg-x').addEventListener('click', function () {
      bar.hidden = true; try { localStorage.setItem('tgbar', '1'); } catch (e) {}
    });
  }
})();
