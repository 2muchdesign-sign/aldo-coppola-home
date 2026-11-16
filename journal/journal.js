/* Журнал «Ателье»: полоса прочтения, активный пункт оглавления, мягкое появление, прототипные ссылки. */
(function(){
  if(!/(^|\.)aldocoppola\.ru$/.test(location.hostname)){
    document.querySelectorAll('a[href^="/"]').forEach(function(a){a.href='https://aldocoppola.ru'+a.getAttribute('href')});
    var rb=document.querySelector('meta[name="robots"]');if(rb)rb.setAttribute('content','noindex, nofollow');
  }
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var bar=document.querySelector('.progress i'),body=document.querySelector('.art-body');
  if(bar&&body){
    var tick=false;
    function upd(){tick=false;var r=body.getBoundingClientRect(),h=r.height-innerHeight*.6;var p=Math.min(1,Math.max(0,-r.top/(h>0?h:1)));bar.style.transform='scaleX('+p.toFixed(4)+')'}
    addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(upd)}},{passive:true});upd();
  }
  /* оглавление: на телефоне свёрнуто */
  var toc=document.querySelector('.toc');
  if(toc&&matchMedia('(max-width:1100px)').matches)toc.open=false;
  if(toc&&'IntersectionObserver' in window){
    var links={};toc.querySelectorAll('a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a});
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){toc.querySelectorAll('a.on').forEach(function(a){a.classList.remove('on')});var l=links[e.target.id];if(l)l.classList.add('on')}})},{rootMargin:'-20% 0px -70% 0px'});
    document.querySelectorAll('.art-body h2[id]').forEach(function(h){io.observe(h)});
  }
  if(!reduce&&'IntersectionObserver' in window){
    document.documentElement.classList.add('fx');
    var ro=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');ro.unobserve(e.target)}})},{threshold:.12});
    document.querySelectorAll('.card,.fig,.pull,.story').forEach(function(el){el.classList.add('rv');ro.observe(el)});
  }
})();
