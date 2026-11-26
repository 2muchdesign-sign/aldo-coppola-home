#!/usr/bin/env python3
"""Сборка финального сайта Aldo Coppola: src/ → _site/.

Запуск из корня репозитория:
  python3 _build/build.py               # превью для GitHub Pages (/aldo-coppola-home/, noindex)
  python3 _build/build.py --prod        # версия для aldocoppola.ru (адреса от корня, индексация открыта)
  python3 _build/build.py --skip-kosm   # не пересобирать косметологию (взять прошлую сборку)

Как устроено (то же самое переносится в шаблон Битрикса):
  * У каждой страницы свой <head> (title, description, разметка) и своё содержимое.
  * Метки <!--#site-head-->, <!--#site-header-->, <!--#site-footer--> сборщик заменяет общими
    подключениями, шапкой и подвалом. В Битриксе это header.php / footer.php шаблона.
  * Меню шапки и подвала — один список NAV / FOOTER ниже. Он же — карта сайта.
  * Ссылки пишутся от корня (/salony/); для превью сборщик добавляет префикс /aldo-coppola-home/.
  * Косметология собирается своим проектом (../aldo-coppola-cosmetology, Astro) в /kosmetologiya/.
  * Разделы, которые ещё не свёрстаны, получают страницу-заглушку из STUBS.
Только стандартная библиотека Python (+ Node для косметологии).
"""
import html, os, re, shutil, subprocess, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, '_site')
KOSM_SRC = os.path.normpath(os.path.join(ROOT, '..', 'aldo-coppola-cosmetology'))
KOSM_CACHE = os.path.join(ROOT, '.cache', 'kosmetologiya')

PROD = '--prod' in sys.argv
SKIP_KOSM = '--skip-kosm' in sys.argv
BASE = '/' if PROD else '/aldo-coppola-home/'
SITE = 'https://aldocoppola.ru'                      # канонические адреса всегда боевые
HOST = SITE if PROD else 'https://2muchdesign-sign.github.io'

YCL = 'https://w2217426.yclients.com/'
SHOP = 'https://beautybar.pro/'
GIFT = 'https://gift.aldocoppola.ru/'
PLASTIC = 'https://beautybar.aldocoppola.ru/collection/podarochnye-sertifikaty-na-uslugi-v-tsentrah-krasoty-i-kosmetologii-aldo-coppola'
TEL, TEL_H = '+74956465879', '+7 (495) 646-58-79'

# ------------------------------------------------------------------ меню
# (подпись, адрес, [подменю]) ; адрес None — пункт только раскрывает подменю
NAV = [
    ('Центры красоты', '/salony/', [('Онлайн-запись', YCL), ('Спецпредложения', '/special/'), ('Система лояльности', '/loyalty/')]),
    ('Услуги и цены', '/uslugi/', []),
    ('Косметология', '/kosmetologiya/', []),
    ('Специалисты', '/specialisty/', []),
    ('О бренде', '/o-brende/', []),
    ('Статьи', '/stati/', []),
    ('Академия', '/akademiya/', []),
    ('Карьера', '/karera/', []),
    ('Сертификаты', None, [('Электронный сертификат', GIFT), ('Пластиковый сертификат с доставкой', PLASTIC)]),
    ('Интернет-магазин', SHOP, []),
]
FOOTER = [
    ('Клиентам', [('Онлайн-запись', YCL), ('Центры красоты', '/salony/'), ('Услуги и цены', '/uslugi/'), ('Косметология', '/kosmetologiya/'),
                  ('Спецпредложения', '/special/'), ('Система лояльности', '/loyalty/'), ('Подарочные сертификаты', GIFT), ('Интернет-магазин', SHOP)]),
    ('О бренде', [('История бренда', '/o-brende/'), ('Статьи', '/stati/'), ('Новости', '/news/'), ('Тенденции 2026', '/tendencii-2026/'),
                  ('Art: календари и артбуки', '/o-brende/art/'), ('Аксессуары Aldo Coppola', '/accessories/'), ('Aldo Coppola Worldwide', 'https://www.aldocoppola.com/')]),
    ('Партнёрам и мастерам', [('Карьера', '/karera/'), ('Академия', '/akademiya/'), ('Реклама на экранах в салонах', '/reklama-v-salonah/'),
                  ('Франшиза', '/franchise/'), ('Дистрибьюция', '/distribution/'), ('Контакты', '/contacts-partners/')]),
]
LEGAL = [('Политика конфиденциальности', '/policy/'), ('Политика cookie', '/policy-cookies/'), ('Эквайринг', '/internet-acquiring/'),
         ('Карта сайта', '/sitemap/'), ('English', '/en/')]
SOCIAL = [('Telegram', 'https://t.me/aldocoppola'), ('ВКонтакте', 'https://vk.com/aldocoppolarussia'), ('Дзен', 'https://dzen.ru/id/61025c84b96e55451d445413')]

# Разделы со своей закреплённой панелью: общая шапка у них не прилипает к верху экрана
OWN_BAR = ('o-brende', 'akademiya', 'stati', 'karera', 'reklama-v-salonah', 'kosmetologiya')

# ------------------------------------------------------------------ заглушки разделов (этап 2 заменит их страницами)
# путь: (заголовок H1, что будет на странице, старый адрес на действующем сайте или None)
STUBS = {
}

# ------------------------------------------------------------------ старые адреса прототипов и сайта → новые
LINK_PREFIX = [   # префикс → префикс
    ('https://2muchdesign-sign.github.io/aldo-coppola-home/journal/', '/stati/'),
    ('https://2muchdesign-sign.github.io/aldo-coppola-home/', '/'),
    ('https://2muchdesign-sign.github.io/aldo-coppola-cosmetology/', '/kosmetologiya/'),
]
LINK_EXACT = {    # адрес целиком (без #якоря) → новый адрес
    'https://2muchdesign-sign.github.io/HRcareers/': '/karera/',
    'https://2muchdesign-sign.github.io/IndoorTV/': '/reklama-v-salonah/',
    'https://2muchdesign-sign.github.io/aldo-coppola-top-stylist-v2/': '/karera/top-stilist/',
    'https://2muchdesign-sign.github.io/aldo-coppola-top-stylist-v3/': '/karera/top-stilist/',
    '/beauty-centers/': '/salony/', 'https://aldocoppola.ru/beauty-centers/': '/salony/',
    '/price/': '/uslugi/', '/career/': '/karera/', '/about-company/about/': '/o-brende/', '/articles/': '/stati/',
    '/eng/art/calendars/': '/o-brende/art/', '/upload/tendency_2026.pdf': '/tendencii-2026/', '/eng/about-company.pdf': '/en/',
    '/journal/': '/stati/',
    '/news/6182/': 'https://aldocoppola.ru/news/6182/',  # новости нет в веб-архиве — текст взять с сайта при переносе
}
LINK_REGEX = [    # пока раздел не перенесён — ссылка на действующий сайт
]
# адреса, которые на новом сайте отдают переадресацию (на Битриксе — 301 из redirects.csv)
REDIRECT_PAGES = {'/beauty-centers/': '/salony/', '/price/': '/uslugi/', '/career/': '/karera/', '/about-company/about/': '/o-brende/',
                  '/articles/': '/stati/', '/eng/art/calendars/': '/o-brende/art/'}

BOOK_CLS = ' class="ms_booking"'
EN_ATTR = ' lang="en" hreflang="en"'
esc = lambda s: html.escape(s, quote=True)
is_ext = lambda u: u.startswith('http')

def ext_attr(u):
    return ' target="_blank" rel="noopener"' if is_ext(u) else ''

# ------------------------------------------------------------------ общие блоки
def header_html(path):
    sec = '/' + path.strip('/').split('/')[0] + '/' if path.strip('/') else '/'
    items = []
    for label, url, sub in NAV:
        cur = ' data-section' if url and url == sec else ''
        if sub:
            top = f'<a href="{url}"{cur}>{label}</a>' if url else f'<button type="button" class="ach-sb" aria-haspopup="true">{label}</button>'
            subs = ''.join(f'<li><a href="{u}"{ext_attr(u)}{BOOK_CLS if u == YCL else ""}>{t}</a></li>' for t, u in sub)
            items.append(f'<li class="ach-has">{top}<ul class="ach-sub">{subs}</ul></li>')
        else:
            cls = ' class="ach-ext"' if is_ext(url) else ''
            items.append(f'<li><a href="{url}"{cls}{ext_attr(url)}{cur}>{label}</a></li>')
    sticky = '' if sec.strip('/') in OWN_BAR else ' data-sticky'
    return f'''<header class="ach" data-ach{sticky}>
  <div class="ach-w">
    <a class="ach-logo" href="/" aria-label="Aldo Coppola — на главную"><img src="/_ac/logo.png" width="56" height="56" alt="Aldo Coppola"></a>
    <nav class="ach-nav" id="ach-nav" aria-label="Главное меню"><ul>{''.join(items)}</ul></nav>
    <div class="ach-side">
      <a class="ach-tel" href="tel:{TEL}">{TEL_H}</a>
      <a class="ach-btn ms_booking" href="{YCL}" target="_blank" rel="noopener">Онлайн-запись</a>
    </div>
    <button class="ach-burger" type="button" aria-label="Открыть меню" aria-expanded="false" aria-controls="ach-nav"><span></span></button>
  </div>
</header>'''

def footer_html():
    cols = ''.join(f'''
      <nav aria-labelledby="acf{i}">
        <h2 id="acf{i}">{t}</h2>
        <ul>{''.join(f'<li><a href="{u}"{ext_attr(u)}>{l}</a></li>' for l, u in links)}</ul>
      </nav>''' for i, (t, links) in enumerate(FOOTER, 1))
    legal = ''.join(f'<li><a href="{u}"{EN_ATTR if u == "/en/" else ""}>{l}</a></li>' for l, u in LEGAL)
    social = ''.join(f'<li><a href="{u}" target="_blank" rel="noopener">{l}</a></li>' for l, u in SOCIAL)
    return f'''<footer class="acf">
  <div class="acf-w">
    <div class="acf-top">
      <div class="acf-brand">
        <img src="/_ac/logo.png" width="72" height="72" alt="Aldo Coppola" loading="lazy">
        <p>Итальянские центры красоты и косметологии в Москве и Московской области.</p>
        <a class="acf-tel" href="tel:{TEL}">{TEL_H}</a>
      </div>{cols}
      <div class="acf-sub">
        <h2 id="acf-s">Подписка на новости</h2>
        <!-- В Битриксе: компонент bitrix:sender.subscribe -->
        <form class="acf-form" data-acf-form aria-labelledby="acf-s">
          <input type="email" name="SENDER_SUBSCRIBE_EMAIL" placeholder="Ваш e-mail" aria-label="Ваш e-mail" autocomplete="email" required>
          <button type="submit">Подписаться</button>
        </form>
        <p class="acf-note">Нажимая «Подписаться», вы соглашаетесь с <a href="/policy/">политикой конфиденциальности</a>.</p>
        <ul class="acf-social" aria-label="Мы в социальных сетях">{social}</ul>
      </div>
    </div>
    <div class="acf-bottom">
      <p>© 1994–2026 Aldo Coppola Russia</p>
      <ul>{legal}</ul>
    </div>
    <p class="acf-legal">Имеются противопоказания, необходима консультация специалиста. Сведения о юридических лицах и медицинских лицензиях — на странице <a href="/salony/">«Центры красоты»</a>.</p>
  </div>
</footer>'''

HEAD_INC = '''<link rel="icon" type="image/png" href="/_ac/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/_ac/site.css">'''
FOOT_JS = '<script src="/_ac/site.js" defer></script>'

# ------------------------------------------------------------------ простые страницы (заглушки, карта сайта, 404)
PLAIN_CSS = '''<style>
:root{--ink:#141414;--muted:#5E5C5A;--line:rgba(20,20,20,.14);--red:#C8102E;--ivory:#F4F3F1}
body{margin:0;background:#fff;color:var(--ink);font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Arial,sans-serif;font-size:18px;line-height:1.6}
.pg{max-width:1100px;margin:0 auto;padding:clamp(40px,7vw,96px) max(clamp(20px,4vw,56px),env(safe-area-inset-right,0px)) clamp(56px,8vw,120px) max(clamp(20px,4vw,56px),env(safe-area-inset-left,0px))}
.crumbs{display:flex;flex-wrap:wrap;gap:6px 10px;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 28px}
.crumbs a{color:inherit;text-decoration:none}.crumbs a:hover{color:var(--red)}
h1{font-weight:500;text-transform:uppercase;letter-spacing:.01em;line-height:1.12;font-size:clamp(30px,4.6vw,56px);margin:0;max-width:18em;text-wrap:balance}
.lead{margin:24px 0 0;max-width:40em;font-size:clamp(18px,1.6vw,21px)}
.note{margin:40px 0 0;padding:22px 24px;background:var(--ivory);max-width:44em;font-size:16px}
.note b{display:block;font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--red);margin-bottom:6px}
.note a,.map a{color:inherit;text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:3px}
.map{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:40px 48px;margin:48px 0 0}
.map h2{font-size:13px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;margin:0 0 14px}
.map ul{margin:0;padding:0;list-style:none;display:grid;gap:8px;font-size:16px}
.map ul ul{margin:8px 0 0 14px;font-size:15px;color:var(--muted)}
</style>'''

def plain_page(path, title, h1, body, desc, crumbs=True, noindex=False):
    parts = [p for p in path.strip('/').split('/') if p]
    cr = ''
    if crumbs and parts:
        cr = '<nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Aldo Coppola</a>'
        acc = '/'
        for p in parts[:-1]:
            acc += p + '/'
            cr += f'<span>/</span><a href="{acc}">{esc(TITLES.get(acc, p))}</a>'
        cr += '</nav>'
    robots = 'noindex, follow' if noindex else 'index, follow'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'url': SITE + path, 'inLanguage': 'en' if path == '/en/' else 'ru',
         'isPartOf': {'@type': 'WebSite', 'name': 'Aldo Coppola', 'url': SITE + '/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Aldo Coppola', 'item': SITE + '/'}] +
         [{'@type': 'ListItem', 'position': i + 2, 'name': TITLES.get('/' + '/'.join(parts[:i + 1]) + '/', parts[i]), 'item': SITE + '/' + '/'.join(parts[:i + 1]) + '/'} for i in range(len(parts))]}]}
    lang = 'en' if path == '/en/' else 'ru'
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Aldo Coppola">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{path}">
<!--#site-head-->
{PLAIN_CSS}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<!--#site-header-->
<main class="pg" id="main">
{cr}
<h1>{h1}</h1>
{body}
</main>
<!--#site-footer-->
</body>
</html>
'''

TITLES = {u: l for l, u, _ in NAV if u and not is_ext(u)}
TITLES.update({u: l for _, links in FOOTER for l, u in links if not is_ext(u)})
TITLES.update({u: l for l, u in LEGAL})
TITLES['/o-brende/'] = 'О бренде'

def stub(path, h1, about, old):
    note = ''
    if old:
        old_url = SITE + old
        note = f'<p class="note"><b>Страница в работе</b>Пока эта информация на <a href="{old_url}" target="_blank" rel="noopener">действующем сайте</a>.</p>'
    else:
        note = '<p class="note"><b>Страница в работе</b>Раздел появится вместе с новым сайтом.</p>'
    if path == '/en/':
        note = f'<p class="note"><b>In progress</b>Company profile: <a href="{SITE}/eng/about-company.pdf" target="_blank" rel="noopener">about-company.pdf</a>.</p>'
    if path == '/tendencii-2026/':
        note = f'<p class="note"><b>PDF</b><a href="{SITE}/upload/tendency_2026.pdf" target="_blank" rel="noopener">Тенденции парикмахерского искусства 2026</a></p>'
    title = f'{h1} — Aldo Coppola' if path != '/en/' else 'Aldo Coppola Russia — Italian beauty centres in Moscow'
    return plain_page(path, title, esc(h1), f'<p class="lead">{esc(about)}</p>\n{note}', about)

def redirect_page(to):
    t = BASE.rstrip('/') + to
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Страница переехала</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{to}"><meta http-equiv="refresh" content="0; url={t}">
</head><body><p>Страница переехала: <a href="{t}">{SITE}{to}</a></p><script>location.replace({json.dumps(t)}+location.hash)</script></body></html>'''

# ------------------------------------------------------------------ обработка страниц
ATTR_RE = re.compile(r'(\s(?:href|src|poster|action|data-src|data-tour|data-poster))=(["\'])([^"\']*)\2')
SRCSET_RE = re.compile(r'(\ssrcset)=(["\'])([^"\']*)\2')

def map_url(u):
    if not u or u.startswith(('#', 'mailto:', 'tel:', 'data:', 'javascript:')):
        return u, False
    core, _, frag = u.partition('#')
    frag = '#' + frag if frag else ''
    if core in LINK_EXACT:
        return LINK_EXACT[core] + frag, True
    for a, b in LINK_PREFIX:
        if core.startswith(a):
            return b + core[len(a):] + frag, True
    for rx, rep in LINK_REGEX:
        if rx.match(core):
            return rx.sub(rep, core) + frag, True
    return u, False

def with_base(u):
    if u.startswith('/') and not u.startswith('//') and BASE != '/' and not u.startswith(BASE):
        return BASE.rstrip('/') + u
    return u

def rewrite_links(s, prefix_root=True):
    def fix(u):
        u2, mapped = map_url(u)
        return with_base(u2) if (prefix_root or mapped) else u2
    s = ATTR_RE.sub(lambda m: f'{m.group(1)}={m.group(2)}{fix(m.group(3))}{m.group(2)}', s)
    s = SRCSET_RE.sub(lambda m: f'{m.group(1)}={m.group(2)}' + ', '.join(
        ' '.join([fix(p.strip().split(' ')[0])] + p.strip().split(' ')[1:]) for p in m.group(3).split(',')) + m.group(2), s)
    return s

def set_robots(s):
    if PROD:
        return s
    tag = '<meta name="robots" content="noindex, nofollow">'
    s2, n = re.subn(r'<meta\s+name=["\']robots["\'][^>]*>', tag, s, count=1)
    return s2 if n else s.replace('</head>', tag + '\n</head>', 1)

def assemble(s, path, kosm=False):
    inc = rewrite_links(HEAD_INC)
    s = s.replace('<!--#site-head-->', inc, 1) if '<!--#site-head-->' in s else s.replace('</head>', inc + '\n</head>', 1)
    hdr = rewrite_links(header_html(path))
    if '<!--#site-header-->' in s:
        s = s.replace('<!--#site-header-->', hdr, 1)
    else:
        s = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1) + '\n' + hdr, s, count=1)
    ftr = rewrite_links(footer_html())
    if '<!--#site-footer-->' in s:
        s = s.replace('<!--#site-footer-->', ftr, 1)
    elif kosm:
        i = s.rfind('<footer')
        j = s.find('</footer>', i)
        if i != -1 and j != -1:
            s = s[:i] + ftr + s[j + len('</footer>'):]
        else:
            s = s.replace('</body>', ftr + '\n</body>', 1)
    s = s.replace('</body>', rewrite_links(FOOT_JS) + '\n</body>', 1)
    s = set_robots(s)
    # ссылки страницы (общие блоки уже переписаны; повторная обработка безопасна — префикс не дублируется)
    s = rewrite_links(s, prefix_root=not kosm)
    return s

def url_path(rel):
    rel = rel.replace(os.sep, '/')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel

# ------------------------------------------------------------------ шаги сборки
def build_stati():
    subprocess.run([sys.executable, os.path.join(HERE, 'stati.py')], check=True)
    subprocess.run([sys.executable, os.path.join(HERE, 'salony.py')], check=True)
    subprocess.run([sys.executable, os.path.join(HERE, 'specialisty.py')], check=True, cwd=HERE)
    subprocess.run([sys.executable, os.path.join(HERE, 'uslugi.py')], check=True, cwd=HERE)
    subprocess.run([sys.executable, os.path.join(HERE, 'special.py')], check=True, cwd=HERE)
    subprocess.run([sys.executable, os.path.join(HERE, 'pages.py')], check=True, cwd=HERE)

def build_kosm():
    if SKIP_KOSM and os.path.isdir(KOSM_CACHE):
        print('Косметология: взята прошлая сборка')
        return
    if not os.path.isdir(KOSM_SRC):
        print('Косметология: папка проекта не найдена —', KOSM_SRC)
        return
    env = dict(os.environ, BASE_PATH=BASE + 'kosmetologiya/', SITE_URL=HOST,
               PATH=os.path.expanduser('~/.local/node/bin') + os.pathsep + os.environ.get('PATH', ''))
    shutil.rmtree(KOSM_CACHE, ignore_errors=True)
    subprocess.run(['npx', 'astro', 'build', '--outDir', KOSM_CACHE], cwd=KOSM_SRC, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    print('Косметология: собрана')

def copy_src():
    shutil.rmtree(OUT, ignore_errors=True)
    def ignore(d, names):
        return [n for n in names if n in ('_src', '.DS_Store') or n.endswith('.md')]
    shutil.copytree(SRC, OUT, ignore=ignore)

def write(path, s):
    full = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(s)

def page_title(s):
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    return html.unescape(m.group(1).strip()) if m else ''

def main():
    build_stati()
    build_kosm()
    copy_src()
    # косметология → /kosmetologiya/
    if os.path.isdir(KOSM_CACHE):
        dst = os.path.join(OUT, 'kosmetologiya')
        shutil.copytree(KOSM_CACHE, dst)
        for f in ('robots.txt',):
            p = os.path.join(dst, f)
            if os.path.exists(p): os.remove(p)
    # заглушки разделов, которых ещё нет
    for path, (h1, about, old) in STUBS.items():
        if not os.path.exists(os.path.join(OUT, path.strip('/'), 'index.html')):
            write(path, stub(path, h1, about, old))
    # переадресации со старых адресов
    for old, new in REDIRECT_PAGES.items():
        write(old, redirect_page(new))
    stati_dir = os.path.join(OUT, 'stati')
    for d, _, files in os.walk(stati_dir):
        if 'index.html' in files:
            rel = os.path.relpath(d, stati_dir).replace(os.sep, '/')
            sub = '' if rel == '.' else rel + '/'
            write('/journal/' + sub, redirect_page('/stati/' + sub))

    # сборка каждой страницы: общие блоки + ссылки
    pages = []
    for d, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith('.html'):
                continue
            full = os.path.join(d, f)
            rel = os.path.relpath(full, OUT)
            path = url_path(rel)
            s = open(full, encoding='utf-8').read()
            if 'http-equiv="refresh"' in s:
                continue
            first = path.strip('/').split('/')[0]
            if first == 'v2':           # альтернативная главная — архив, не часть сайта
                s = set_robots(s.replace('<meta name="robots" content="index', '<meta name="robots" content="noindex', 1))
                open(full, 'w', encoding='utf-8').write(s)
                continue
            kosm = first == 'kosmetologiya'
            if kosm and '<body' not in s:
                continue
            s = assemble(s, path, kosm=kosm)
            open(full, 'w', encoding='utf-8').write(s)
            if 'noindex' not in (re.search(r'<meta name="robots" content="([^"]*)"', s) or [None, ''])[1] or not PROD:
                if not (kosm and '/dizayn/' in path):
                    pages.append((path, page_title(s)))

    pages.sort()
    # карта сайта для людей /sitemap/
    groups = {}
    for p, t in pages:
        k = '/' + p.strip('/').split('/')[0] + '/' if p != '/' else '/'
        groups.setdefault(k, []).append((p, t))
    order = ['/'] + [u for _, u, _ in NAV if u and not is_ext(u)] + [u for _, links in FOOTER for _, u in links if not is_ext(u)] + [u for _, u in LEGAL]
    seen, blocks = set(), []
    for k in order + sorted(groups):
        k = '/' + k.strip('/').split('/')[0] + '/' if k != '/' else '/'
        if k in seen or k not in groups: continue
        seen.add(k)
        items = groups[k]
        name = 'Главная' if k == '/' else TITLES.get(k, items[0][1].split(' — ')[0].split(' | ')[0])
        inner = ''.join(f'<li><a href="{p}">{esc(t.split(" | ")[0].split(" — ")[0])}</a></li>' for p, t in items if p != k)
        if len(items) > 25:
            inner = ''.join(f'<li><a href="{p}">{esc(t.split(" | ")[0].split(" — ")[0])}</a></li>' for p, t in items if p != k and p.count('/') <= 3)
        blocks.append(f'<section><h2><a href="{k}">{esc(name)}</a></h2>' + (f'<ul>{inner}</ul>' if inner else '') + '</section>')
    sm = plain_page('/sitemap/', 'Карта сайта — Aldo Coppola', 'Карта сайта',
                    f'<p class="lead">Все разделы и страницы сайта Aldo Coppola.</p><div class="map">{"".join(blocks)}</div>',
                    'Все разделы и страницы сайта Aldo Coppola.')
    write('/sitemap/', assemble(sm, '/sitemap/'))
    nf = plain_page('/404/', 'Страница не найдена — Aldo Coppola', 'Страница не найдена',
                    '<p class="lead">Такой страницы нет или она переехала. Начните с <a href="/">главной</a> или откройте <a href="/sitemap/">карту сайта</a>.</p>',
                    'Страница не найдена', crumbs=False, noindex=True)
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(assemble(nf, '/404/'))

    # для поисковиков и нейросетей
    urls = [p for p, _ in pages] + ['/sitemap/']
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'<url><loc>{SITE}{u}</loc></url>\n' for u in sorted(set(urls))) + '</urlset>\n')
    robots_prod = f'User-agent: *\nAllow: /\nDisallow: /*?*\n\nSitemap: {SITE}/sitemap.xml\n'
    open(os.path.join(OUT, 'robots-production.txt'), 'w').write(robots_prod)
    open(os.path.join(OUT, 'robots.txt'), 'w').write(robots_prod if PROD else 'User-agent: *\nDisallow: /\n')
    llms = open(os.path.join(HERE, 'llms-head.md'), encoding='utf-8').read()
    llms += '\n## Разделы сайта\n' + ''.join(f'- [{l}]({u if is_ext(u) else SITE + u})\n' for l, u, _ in NAV if u)
    llms += ''.join(f'- [{l}]({u if is_ext(u) else SITE + u})\n' for _, links in FOOTER for l, u in links if u not in [x[1] for x in NAV])
    llms += f'- [Косметология: процедуры и цены для нейросетей]({SITE}/kosmetologiya/llms.txt)\n- [Карта сайта]({SITE}/sitemap.xml)\n'
    open(os.path.join(OUT, 'llms.txt'), 'w', encoding='utf-8').write(llms)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f'Готово: {len(pages)} страниц → {OUT} (адреса от {BASE})')

if __name__ == '__main__':
    main()
