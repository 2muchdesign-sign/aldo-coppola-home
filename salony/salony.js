/* Центры красоты: листание галереи и видеотур. */
(function () {
  document.querySelectorAll('[data-gal]').forEach(function (g) {
    var t = g.querySelector('.sl-gal__track'), figs = t.children, n = figs.length;
    var prev = g.querySelector('[data-prev]'), next = g.querySelector('[data-next]'), cnt = g.querySelector('[data-count]');
    var cur = 0, busy = false, timer;
    function idx() { return Math.max(0, Math.min(n - 1, Math.round(t.scrollLeft / (figs[0].offsetWidth + 8)))); }
    function upd() { cnt.textContent = (cur + 1) + ' / ' + n; prev.disabled = cur <= 0; next.disabled = cur >= n - 1; }
    function go(d) {
      cur = Math.max(0, Math.min(n - 1, cur + d)); busy = true; upd();
      t.scrollTo({ left: figs[cur].offsetLeft - figs[0].offsetLeft, behavior: 'smooth' });
    }
    prev.addEventListener('click', function () { go(-1); });
    next.addEventListener('click', function () { go(1); });
    /* листание пальцем: номер кадра обновляется, когда прокрутка остановилась */
    t.addEventListener('scroll', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { if (!busy || idx() === cur) { cur = idx(); upd(); } busy = false; }, 140);
    }, { passive: true });
    t.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') { e.preventDefault(); go(1); } if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); } });
    upd();
  });
  var dlg = document.querySelector('[data-tour-dialog]');
  if (!dlg) return;
  var v = dlg.querySelector('video'), title = dlg.querySelector('[data-tour-title]');
  document.querySelectorAll('[data-tour]').forEach(function (b) {
    b.addEventListener('click', function () {
      v.poster = b.dataset.poster; v.src = b.dataset.tour; title.textContent = b.dataset.title;
      dlg.showModal(); v.play().catch(function () {});
    });
  });
  function close() { v.pause(); dlg.close(); }
  dlg.querySelector('[data-tour-close]').addEventListener('click', close);
  dlg.addEventListener('click', function (e) { if (e.target === dlg) close(); });
  dlg.addEventListener('close', function () { v.pause(); });
})();
