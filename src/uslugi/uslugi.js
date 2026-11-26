/* Услуги: на странице цен открывается вопрос из адреса (#faq), остальное — без скриптов. */
(function () {
  var h = location.hash && document.getElementById(location.hash.slice(1));
  if (h && h.tagName === 'DETAILS') h.open = true;
})();
