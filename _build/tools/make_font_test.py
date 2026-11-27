import re, sys
root = sys.argv[1]
s = open(root + '/src/index.html', encoding='utf-8').read()
# относительные пути -> на уровень выше
def fix(m):
    a, v = m.group(1), m.group(2)
    if re.match(r'(https?:|tel:|mailto:|#|/|data:|javascript:)', v) or v == '':
        return m.group(0)
    return f'{a}="../{v}"'
s = re.sub(r'\b(src|href|poster|data-src|data-poster)="([^"]*)"', fix, s)
s = s.replace("'media/tour/'", "'../media/tour/'")
s = s.replace('content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"', 'content="noindex, nofollow"')
s = re.sub(r'<link rel="canonical"[^>]*>', '', s)
s = s.replace('<title>', '<title>Тест шрифтов — ', 1)
fonts = 'family=Cormorant+Garamond:wght@500&family=Montserrat:wght@300;400;500;600&family=PT+Sans+Narrow:wght@400;700&family=Raleway:wght@300;400;500;600&family=Roboto+Condensed:wght@300;400;500&family=IBM+Plex+Sans+Condensed:wght@300;400;500&family=Fira+Sans+Condensed:wght@300;400;500'
s = re.sub(r'<link href="https://fonts.googleapis.com/css2\?[^"]*" rel="stylesheet">',
           f'<link href="https://fonts.googleapis.com/css2?{fonts}&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">', s, 1)
css = '''<style id="ft-css">
:root{--f2:"Cormorant Garamond",serif;--f2w:500;--f2k:1;--f2ls:-.005em;--f2tt:none}
h3,.facts b,.tour-close,.sal-n,.stamp p,.faq summary::after{font-family:var(--f2)!important}
h3,.facts b,.stamp b,.sal-n{font-weight:var(--f2w)!important;letter-spacing:var(--f2ls)!important}
h3,.sal-n{text-transform:var(--f2tt)}
.dir h3{font-size:calc(clamp(26px,2.4vw,36px)*var(--f2k))}
.news h3{font-size:calc(clamp(23px,1.9vw,28px)*var(--f2k))}
.salon h3{font-size:calc(clamp(25px,2.1vw,32px)*var(--f2k))}
.sal-n{font-size:calc(clamp(23px,2vw,30px)*var(--f2k))}
.faq summary h3{font-size:calc(clamp(23px,2vw,29px)*var(--f2k))}
.facts b{font-size:calc(clamp(44px,5vw,72px)*var(--f2k))}
.stamp b{font-size:calc(clamp(64px,7vw,92px)*var(--f2k))}
.ft{position:fixed;z-index:9999;left:16px;bottom:16px;width:min(900px,calc(100vw - 170px));background:#fff;border:1px solid rgba(20,20,20,.14);box-shadow:0 8px 30px rgba(20,20,20,.12);padding:12px 14px;font:500 13px/1.3 "Manrope",sans-serif;color:#141414}
.ft-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.ft-row+.ft-row{margin-top:8px}
.ft b{font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:11px;margin-right:6px;color:#5E5C5A}
.ft button{font:inherit;cursor:pointer;border:1px solid rgba(20,20,20,.2);background:#fff;color:#141414;padding:7px 11px;line-height:1}
.ft button[aria-pressed="true"]{background:#C8102E;border-color:#C8102E;color:#fff}
.ft-note{margin:8px 0 0;color:#5E5C5A;font-size:12px}
.ft-x{margin-left:auto}
.ft.min .ft-row:not(:first-child),.ft.min .ft-note{display:none}
@media(max-width:600px){.ft{left:8px;bottom:8px;width:calc(100vw - 16px);padding:10px}.ft button{padding:6px 8px;font-size:12px}}
</style>
'''
s = s.replace('</head>', css + '</head>', 1)
panel = '''
<div class="ft" id="ft" role="region" aria-label="Тест шрифтов">
  <div class="ft-row" id="ft-f"><b>Шрифт</b></div>
  <div class="ft-row" id="ft-w"><b>Насыщенность</b></div>
  <div class="ft-row" id="ft-c"><b>Регистр</b><button data-tt="none" aria-pressed="true">Как есть</button><button data-tt="uppercase" aria-pressed="false">Заглавные</button><button class="ft-x" id="ft-min" aria-pressed="false">Свернуть</button></div>
  <p class="ft-note" id="ft-n"></p>
</div>
<script>
(function(){
var F=[
 {k:'cormorant',n:'Сейчас: Cormorant',f:'"Cormorant Garamond",serif',w:[500],k2:1,ls:'-.005em',t:'Текущий шрифт с засечками — для сравнения.'},
 {k:'manrope',n:'Только Manrope',f:'"Manrope",sans-serif',w:[300,400,500],d:400,k2:.84,ls:'-.01em',t:'Без второго шрифта: акценты только размером и насыщенностью.'},
 {k:'montserrat',n:'Montserrat',f:'"Montserrat",sans-serif',w:[300,400,500],d:400,k2:.82,ls:'-.01em',t:'Фирменный шрифт бренда. Широкий, геометричный, рядом с Manrope близок по характеру.'},
 {k:'ptnarrow',n:'PT Sans Narrow',f:'"PT Sans Narrow",sans-serif',w:[400,700],d:400,k2:.98,ls:'0',t:'Узкий, любимый собственником. Только 400 и 700.'},
 {k:'raleway',n:'Raleway',f:'"Raleway",sans-serif',w:[300,400,500],d:400,k2:.86,ls:'0',t:'Элегантный, с тонкими начертаниями; характерные цифры «старого стиля».'},
 {k:'roboto',n:'Roboto Condensed',f:'"Roboto Condensed",sans-serif',w:[300,400,500],d:400,k2:.94,ls:'0',t:'Узкий, нейтральный, хорошо читается мелко и крупно.'},
 {k:'plex',n:'IBM Plex Sans Condensed',f:'"IBM Plex Sans Condensed",sans-serif',w:[300,400,500],d:400,k2:.9,ls:'0',t:'Узкий, строгий, с лёгким «техническим» характером.'},
 {k:'fira',n:'Fira Sans Condensed',f:'"Fira Sans Condensed",sans-serif',w:[300,400,500],d:400,k2:.9,ls:'0',t:'Узкий, мягче Roboto, хорошая кириллица.'}
];
var R=document.documentElement.style,ff=document.getElementById('ft-f'),fw=document.getElementById('ft-w'),nt=document.getElementById('ft-n');
var q=new URLSearchParams(location.search),cur=F.find(function(x){return x.k===q.get('f')})||F[0],wt=+q.get('w')||0,tt=q.get('tt')||'none';
function btn(p,txt,on,fn){var b=document.createElement('button');b.textContent=txt;b.setAttribute('aria-pressed',on);b.onclick=fn;p.appendChild(b);return b}
function apply(){
 var w=cur.w.indexOf(wt)>-1?wt:(cur.d||cur.w[0]);
 R.setProperty('--f2',cur.f);R.setProperty('--f2w',w);R.setProperty('--f2k',cur.k2);R.setProperty('--f2ls',tt==='uppercase'?'.04em':cur.ls);R.setProperty('--f2tt',tt);
 ff.querySelectorAll('button').forEach(function(b){b.remove()});fw.querySelectorAll('button').forEach(function(b){b.remove()});
 F.forEach(function(x){btn(ff,x.n,x===cur,function(){cur=x;wt=0;apply()})});
 cur.w.forEach(function(v){btn(fw,String(v),v===w,function(){wt=v;apply()})});
 document.querySelectorAll('#ft-c [data-tt]').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.tt===tt)});
 nt.textContent=cur.t;
 var u=new URL(location.href);u.searchParams.set('f',cur.k);u.searchParams.set('w',w);u.searchParams.set('tt',tt);history.replaceState(null,'',u);
}
document.querySelectorAll('#ft-c [data-tt]').forEach(function(b){b.onclick=function(){tt=b.dataset.tt;apply()}});
document.getElementById('ft-min').onclick=function(){var p=document.getElementById('ft');var m=p.classList.toggle('min');this.textContent=m?'Развернуть':'Свернуть'};
apply();
})();
</script>
'''
i = s.rfind('</body>')
s = s[:i] + panel + s[i:]
import os
os.makedirs(root + '/src/test-shrift', exist_ok=True)
open(root + '/src/test-shrift/index.html', 'w', encoding='utf-8').write(s)
print('ok', len(s))
