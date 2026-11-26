/* Aldo Coppola — общие шапка и подвал: меню на телефоне, подменю, подписка. */
(function () {
  var html = document.documentElement;
  var head = document.querySelector('[data-ach]');
  if (head) {
    var burger = head.querySelector('.ach-burger');
    if (burger) burger.addEventListener('click', function () {
      var open = html.classList.toggle('ach-open');
      html.classList.toggle('ach-lock', open && matchMedia('(max-width:1100px)').matches && !!head.closest('[data-sticky]'));
      burger.setAttribute('aria-expanded', open);
      burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && html.classList.contains('ach-open')) burger.click();
    });
  }
  /* Подписка: в Битриксе — компонент bitrix:sender.subscribe. В превью форма ничего не отправляет. */
  var f = document.querySelector('[data-acf-form]');
  if (f) f.addEventListener('submit', function (e) {
    e.preventDefault();
    var ok = document.createElement('p');
    ok.className = 'acf-ok';
    ok.setAttribute('role', 'status');
    ok.textContent = 'Спасибо! Подписка оформится, когда сайт заработает на aldocoppola.ru.';
    f.replaceWith(ok);
  });
})();
