#!/usr/bin/env python3
"""Сборка раздела «Статьи»: journal/_src/*.md → статичные HTML-страницы.

Запуск из корня репозитория:  python3 journal/_build.py
Результат: journal/index.html (обложка), journal/{рубрика}/index.html,
journal/{рубрика}/{slug}/index.html, journal/rss.xml, journal/sitemap.xml.

Формат исходника — в journal/_src/README.md. Только стандартная библиотека Python.
В Битриксе эти же поля ложатся в инфоблок «Журнал» (свойства = поля шапки).
"""
import html, json, os, re, datetime, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, '_src')
SITE = 'https://aldocoppola.ru'
BASE = '/journal/'
JOURNAL = 'Статьи'
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

RUBRICS = {
    'volosy': ('Волосы', 'Цвет, стрижки и техники итальянской школы.'),
    'kosmetologiya': ('Кожа', 'Косметология с врачом: что работает и как выбрать.'),
    'uhod': ('Уход', 'Домашний уход между визитами в салон.'),
    'moda': ('Подиум', 'Мода, показы и архив бренда.'),
    'lyudi': ('Салон', 'Как устроены центры красоты Aldo Coppola.'),
}

# ---------------------------------------------------------------- разбор исходника
def parse_file(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
    meta, body = {}, raw
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    meta['body'] = body
    meta['words'] = len(re.findall(r'\w+', re.sub(r'[!:#>*|_\[\]()]', ' ', body)))
    meta['read'] = max(3, round(meta['words'] / 180))
    return meta

def esc(s):
    return html.escape(s, quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*([^*]+)\*(?!\w)', r'<em>\1</em>', s)
    s = s.replace(' -- ', ' — ')
    return s

def slugify(t):
    t = t.lower()
    tr = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя', ['a','b','v','g','d','e','e','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','c','ch','sh','sch','','y','','e','yu','ya']))
    t = ''.join(tr.get(c, c) for c in t)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:48] or 'razdel'

def render_body(body, ctx):
    """Возвращает (html, toc, faq). Блоки ::: name … ::: — врезки."""
    out, toc, faq = [], [], []
    lines = body.strip('\n').split('\n')
    i, para, first_p = 0, [], [True]

    def flush():
        if para:
            text = ' '.join(x.strip() for x in para)
            cls = ' class="lede"' if first_p[0] else ''
            first_p[0] = False
            out.append(f'<p{cls}>{inline(text)}</p>')
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith(':::'):
            flush()
            head = s[3:].strip()
            kind, _, arg = head.partition(' ')
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != ':::':
                block.append(lines[i]); i += 1
            i += 1
            out.append(render_block(kind, arg, block, faq, ctx))
            continue
        if s.startswith('## '):
            flush()
            t = s[3:].strip()
            sid = slugify(t)
            toc.append((sid, t))
            out.append(f'<h2 id="{sid}">{inline(t)}</h2>')
        elif s.startswith('### '):
            flush(); out.append(f'<h3>{inline(s[4:])}</h3>')
        elif s.startswith('> '):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                q.append(lines[i].strip()[1:].strip()); i += 1
            who = ''
            if q and q[-1].startswith('— '):
                who = q.pop()[2:]
            out.append(f'<figure class="pull"><blockquote>{inline(" ".join(q))}</blockquote>' + (f'<figcaption>{inline(who)}</figcaption>' if who else '') + '</figure>')
            continue
        elif s.startswith('- ') or re.match(r'\d+\. ', s):
            flush()
            ordered = not s.startswith('- ')
            items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or re.match(r'\d+\. ', lines[i].strip())):
                items.append(re.sub(r'^(- |\d+\. )', '', lines[i].strip())); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
            continue
        elif s.startswith('!img '):
            flush()
            parts = [p.strip() for p in s[5:].split('|')]
            src, alt = med(parts[0]), parts[1]
            cap = parts[2] if len(parts) > 2 else ''
            mod = parts[3] if len(parts) > 3 else ''
            w, h = img_size(src, ctx)
            cls = 'fig' + (' wide' if 'wide' in mod else '') + (' contain' if 'contain' in mod else '')
            out.append(f'<figure class="{cls}"><img src="{esc(src)}" alt="{esc(alt)}" loading="lazy" decoding="async"{w}{h}>' + (f'<figcaption>{inline(cap)}</figcaption>' if cap else '') + '</figure>')
        elif s.startswith('!video '):
            flush()
            parts = [p.strip() for p in s[7:].split('|')]
            src, poster, cap = med(parts[0]), med(parts[1]), parts[2] if len(parts) > 2 else ''
            out.append(f'<figure class="fig wide vid"><video controls playsinline preload="none" poster="{esc(poster)}"><source src="{esc(src)}" type="video/mp4"></video>' + (f'<figcaption>{inline(cap)}</figcaption>' if cap else '') + '</figure>')
        else:
            para.append(s)
        i += 1
    flush()
    return '\n'.join(out), toc, faq

def med(src):
    return src if '/' in src else '../../media/' + src

def render_block(kind, arg, block, faq, ctx):
    text = [b.strip() for b in block if b.strip()]
    if kind == 'kratko':
        items = [re.sub(r'^- ', '', t) for t in text]
        return '<aside class="kratko" aria-label="Коротко"><p class="k-h">Коротко</p><ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul></aside>'
    if kind == 'my':
        body, links = [], []
        for t in text:
            m = re.match(r'^\[([^\]]+)\]\(([^)]+)\)$', t)
            if m: links.append(m.groups())
            else: body.append(t)
        b = ''.join(f'<p>{inline(x)}</p>' for x in body)
        l = ''.join(f'<a class="btn" href="{esc(u)}">{esc(lbl)}</a>' for lbl, u in links)
        return f'<aside class="my"><p class="k-h">Что делаем мы</p><h3>{inline(arg)}</h3>{b}<div class="my-l">{l}</div></aside>'
    if kind == 'faq':
        q = None; html_ = ['<section class="faq" aria-labelledby="faq-h"><h2 id="faq-h">Вопросы и ответы</h2>']
        for t in text:
            if t.startswith('Q: '): q = t[3:]
            elif t.startswith('A: ') and q:
                a = t[3:]
                faq.append((q, a))
                html_.append(f'<details><summary>{inline(q)}</summary><p>{inline(a)}</p></details>')
                q = None
        html_.append('</section>')
        return ''.join(html_)
    if kind == 'sources':
        items = [re.sub(r'^- ', '', t) for t in text]
        return '<section class="sources"><p class="k-h">Источники</p><ol>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol></section>'
    if kind == 'table':
        rows = [[c.strip() for c in t.strip('|').split('|')] for t in text if not re.match(r'^\|?\s*-', t)]
        head, rest = rows[0], rows[1:]
        cap = f'<caption>{inline(arg)}</caption>' if arg else ''
        return ('<div class="tbl"><table>' + cap + '<thead><tr>' + ''.join(f'<th scope="col">{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                + ''.join('<tr>' + ''.join((f'<th scope="row">{inline(c)}</th>' if k == 0 else f'<td>{inline(c)}</td>') for k, c in enumerate(r)) + '</tr>' for r in rest) + '</tbody></table></div>')
    if kind == 'note':
        return '<p class="med">' + inline(' '.join(text)) + '</p>'
    return ''

_size_cache = {}
def img_size(src, ctx):
    """width/height из файла (WebP/JPEG/PNG), чтобы страница не прыгала."""
    path = os.path.normpath(os.path.join(ctx['dir'], src))
    if path in _size_cache: return _size_cache[path]
    w = h = None
    try:
        b = open(path, 'rb').read(64 * 1024)
        if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
            ch = b[12:16]
            if ch == b'VP8X': w = 1 + int.from_bytes(b[24:27], 'little'); h = 1 + int.from_bytes(b[27:30], 'little')
            elif ch == b'VP8 ': w = int.from_bytes(b[26:28], 'little') & 0x3fff; h = int.from_bytes(b[28:30], 'little') & 0x3fff
            elif ch == b'VP8L':
                v = int.from_bytes(b[21:25], 'little'); w = (v & 0x3fff) + 1; h = ((v >> 14) & 0x3fff) + 1
        elif b[:8] == b'\x89PNG\r\n\x1a\n':
            w = int.from_bytes(b[16:20], 'big'); h = int.from_bytes(b[20:24], 'big')
        elif b[:2] == b'\xff\xd8':
            j = 2
            while j < len(b) - 9:
                if b[j] != 0xFF: j += 1; continue
                mk = b[j + 1]
                if mk in (0xC0, 0xC1, 0xC2):
                    h = int.from_bytes(b[j + 5:j + 7], 'big'); w = int.from_bytes(b[j + 7:j + 9], 'big'); break
                j += 2 + int.from_bytes(b[j + 2:j + 4], 'big')
    except OSError:
        pass
    r = (f' width="{w}"', f' height="{h}"') if w and h else ('', '')
    _size_cache[path] = r
    return r

def ru_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f'{d.day} {MONTHS[d.month - 1]} {d.year}'

def title_html(t):
    return re.sub(r'\*([^*]+)\*', r'<em>\1</em>', esc(t))

def title_plain(t):
    return t.replace('*', '')

# ---------------------------------------------------------------- шаблоны
HEAD_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400;1,500&family=Cormorant+Garamond:ital,wght@1,500&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">'

def page(depth, title, desc, canonical, body, jsonld, og_image, og_type='website', extra_head=''):
    up = '../' * depth
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="{JOURNAL} Aldo Coppola" href="{SITE}{BASE}rss.xml">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Aldo Coppola">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}../media/logo.png">
{HEAD_FONTS}
<link rel="stylesheet" href="{up}journal.css">
{extra_head}
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Перейти к тексту</a>
<header class="jh">
  <div class="wrap">
    <a class="jh-logo" href="{up}../" aria-label="Aldo Coppola — на главную"><img src="{up}../media/logo.png" width="44" height="44" alt="Aldo Coppola"></a>
    <a class="jh-name" href="{up}">{JOURNAL}<small>Aldo Coppola</small></a>
    <nav class="jh-nav" aria-label="Рубрики">{''.join(f'<a href="{up}{k}/">{v[0]}</a>' for k, v in RUBRICS.items())}</nav>
    <a class="jh-book" href="https://w2217426.yclients.com/" target="_blank" rel="noopener">Записаться</a>
  </div>
  <div class="progress" aria-hidden="true"><i></i></div>
</header>
<main id="main">
{body}
</main>
<footer class="jf">
  <div class="wrap">
    <div class="jf-top">
      <div><p class="jf-name">{JOURNAL}</p><p>Статьи Aldo Coppola о волосах, коже и моде. Пишем вместе с колористами, стилистами и врачами наших центров красоты.</p></div>
      <nav aria-label="Рубрики"><p class="k-h">Рубрики</p>{''.join(f'<a href="{up}{k}/">{v[0]}</a>' for k, v in RUBRICS.items())}</nav>
      <nav aria-label="Сайт"><p class="k-h">Aldo Coppola</p><a href="{up}../">Главная</a><a href="{up}../o-brende/">История бренда</a><a href="{up}../akademiya/">Академия</a><a href="{up}../#salons">Центры красоты</a><a href="https://t.me/aldocoppola" rel="noopener">Telegram</a></nav>
    </div>
    <p class="jf-legal">© 1994–2026 Aldo Coppola Russia. Материалы раздела не заменяют консультацию специалиста. <a href="/policy/">Политика конфиденциальности</a></p>
  </div>
</footer>
<script src="{up}journal.js" defer></script>
</body>
</html>
'''

def card(a, depth, size=''):
    up = '../' * depth
    href = f'{up}{a["rubric"]}/{a["slug"]}/'
    cover = f'{up}media/{a["cover"]}'
    fit = ' contain' if a.get('cover_fit') == 'contain' else ''
    return f'''<article class="card {size}" data-rubric="{a['rubric']}">
  <a class="card-img{fit}" href="{href}" tabindex="-1" aria-hidden="true"><img src="{cover}" alt="" loading="lazy" decoding="async"></a>
  <div class="card-b">
    <p class="card-k"><a href="{up}{a['rubric']}/">{RUBRICS[a['rubric']][0]}</a><span>{a['read']} мин</span></p>
    <h3><a href="{href}">{title_html(a['title'])}</a></h3>
    <p class="card-d">{esc(a['dek'])}</p>
  </div>
</article>'''

def build():
    arts = []
    for f in sorted(glob.glob(os.path.join(SRC, '*.md'))):
        if os.path.basename(f).lower() == 'readme.md': continue
        a = parse_file(f)
        a.setdefault('updated', a['date'])
        arts.append(a)
    arts.sort(key=lambda a: (a.get('order', '99'), a['date']), reverse=False)
    arts.sort(key=lambda a: int(a.get('order', 99)))
    by_slug = {a['slug']: a for a in arts}

    for a in arts:
        d = os.path.join(ROOT, a['rubric'], a['slug'])
        os.makedirs(d, exist_ok=True)
        ctx = {'dir': d}
        body, toc, faq = render_body(a['body'], ctx)
        url = f'{SITE}{BASE}{a["rubric"]}/{a["slug"]}/'
        cover_abs = f'{SITE}{BASE}media/{a["cover"]}'
        rel = [by_slug[s] for s in a.get('related', '').split(',') if s.strip() in by_slug][:3]
        if len(rel) < 3:
            rel += [x for x in arts if x is not a and x not in rel and x['rubric'] == a['rubric']][:3 - len(rel)]
        if len(rel) < 3:
            rel += [x for x in arts if x is not a and x not in rel][:3 - len(rel)]
        medical = a.get('medical') == 'yes'
        reviewer = a.get('reviewer', '')
        toc_html = ''.join(f'<li><a href="#{i}">{inline(t)}</a></li>' for i, t in toc)
        w, h = img_size(med(a['cover']), ctx)
        fit = ' contain' if a.get('cover_fit') == 'contain' else ''
        cover_html = f'''<figure class="cover{fit}"><img src="{esc(med(a['cover']))}" alt="{esc(a['cover_alt'])}" fetchpriority="high"{w}{h}><figcaption>{inline(a.get('cover_caption', ''))}</figcaption></figure>'''
        art_html = f'''
<article class="art" itemscope itemtype="https://schema.org/Article">
  <header class="art-h wrap">
    <nav class="crumbs" aria-label="Хлебные крошки"><a href="../../../">Aldo Coppola</a><span>/</span><a href="../../">{JOURNAL}</a><span>/</span><a href="../">{RUBRICS[a['rubric']][0]}</a></nav>
    <p class="art-k">{RUBRICS[a['rubric']][0]}<span>·</span>{esc(a.get('format', 'Гайд'))}</p>
    <h1 itemprop="headline">{title_html(a['title'])}</h1>
    <p class="dek">{esc(a['dek'])}</p>
    <ul class="meta">
      <li>Текст: <b>{esc(a.get('author', 'Редакция Aldo Coppola'))}</b></li>
      {f'<li>Проверено: <b>{esc(reviewer)}</b></li>' if reviewer else ''}
      <li><time datetime="{a['date']}" itemprop="datePublished">{ru_date(a['date'])}</time>{f' · обновлено <time datetime="{a["updated"]}" itemprop="dateModified">{ru_date(a["updated"])}</time>' if a['updated'] != a['date'] else ''}</li>
      <li>{a['read']} мин чтения</li>
    </ul>
  </header>
  <div class="wrap">{cover_html}</div>
  <div class="art-grid wrap">
    <aside class="toc-a">
      <details class="toc" open><summary>Содержание</summary><ol>{toc_html}</ol></details>
    </aside>
    <div class="art-body" itemprop="articleBody">
{body}
{'<p class="med">Имеются противопоказания. Необходима консультация специалиста.</p>' if medical else ''}
      <aside class="tg"><p>Короткие советы колористов и врачей — в нашем Telegram.</p><a class="btn ghost" href="https://t.me/aldocoppola" rel="noopener">Читать в Telegram</a></aside>
    </div>
  </div>
  <section class="more wrap" aria-labelledby="more-h">
    <h2 id="more-h">Читайте <em>также</em></h2>
    <div class="feed three">{''.join(card(r, 2) for r in rel)}</div>
  </section>
</article>'''
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'Article', 'headline': title_plain(a['title']), 'description': a['dek'], 'image': [cover_abs],
             'datePublished': a['date'], 'dateModified': a['updated'], 'inLanguage': 'ru',
             'author': {'@type': 'Organization', 'name': 'Редакция Aldo Coppola', 'url': SITE + BASE},
             'publisher': {'@type': 'Organization', 'name': 'Aldo Coppola', 'logo': {'@type': 'ImageObject', 'url': SITE + '/media/logo.png'}},
             'mainEntityOfPage': url, 'articleSection': RUBRICS[a['rubric']][0], 'wordCount': a['words']},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Aldo Coppola', 'item': SITE + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': JOURNAL, 'item': SITE + BASE},
                {'@type': 'ListItem', 'position': 3, 'name': RUBRICS[a['rubric']][0], 'item': f'{SITE}{BASE}{a["rubric"]}/'},
                {'@type': 'ListItem', 'position': 4, 'name': title_plain(a['title']), 'item': url}]}]}
        if medical:
            ld['@graph'][0]['@type'] = 'MedicalWebPage' if False else 'Article'
        if faq:
            ld['@graph'].append({'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', x)}} for q, x in faq]})
        title = a.get('seo_title') or f'{title_plain(a["title"])} | {JOURNAL} Aldo Coppola'
        out = page(2, title, a.get('description', a['dek']), url, art_html, ld, cover_abs, 'article',
                   f'<meta property="article:published_time" content="{a["date"]}"><meta property="article:modified_time" content="{a["updated"]}">')
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)

    # обложка журнала
    lead = arts[0]
    second = arts[1:3]
    rest = arts[3:]
    chips = '<a class="chip" href="./" aria-current="page">Все</a>' + ''.join(f'<a class="chip" href="{k}/">{v[0]}</a>' for k, v in RUBRICS.items())
    lead_cover = f'media/{lead["cover"]}'
    index_body = f'''
<section class="jcover wrap">
  <p class="issue"><span>Aldo Coppola</span><span>Выпуск · ноябрь 2026</span><span>{len(arts)} материалов</span></p>
  <h1 class="jmast">{JOURNAL}<span class="sr"> Aldo Coppola о волосах, коже и моде</span></h1>
  <p class="jlead">О волосах, коже и моде — словами колористов, стилистов и врачей наших центров красоты. Без «чудо-средств» и обещаний: что работает, сколько держится и кому подходит.</p>
  <nav class="chips" aria-label="Рубрики">{chips}</nav>
</section>
<section class="story wrap" aria-label="Главная история выпуска">
  <a class="story-img{' contain' if lead.get('cover_fit') == 'contain' else ''}" href="{lead['rubric']}/{lead['slug']}/" tabindex="-1" aria-hidden="true"><img src="{lead_cover}" alt="" fetchpriority="high"></a>
  <div class="story-b">
    <p class="card-k"><a href="{lead['rubric']}/">{RUBRICS[lead['rubric']][0]}</a><span>{lead['read']} мин</span></p>
    <h2><a href="{lead['rubric']}/{lead['slug']}/">{title_html(lead['title'])}</a></h2>
    <p class="card-d">{esc(lead['dek'])}</p>
    <a class="link" href="{lead['rubric']}/{lead['slug']}/">Читать</a>
  </div>
</section>
<section class="wrap" aria-label="Свежие материалы">
  <div class="feed two">{''.join(card(a, 0, 'big') for a in second)}</div>
  <div class="feed list">{''.join(card(a, 0) for a in rest)}</div>
</section>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Blog', 'name': f'{JOURNAL} Aldo Coppola', 'url': SITE + BASE, 'inLanguage': 'ru',
         'publisher': {'@type': 'Organization', 'name': 'Aldo Coppola', 'url': SITE + '/'},
         'blogPost': [{'@type': 'BlogPosting', 'headline': title_plain(a['title']), 'url': f'{SITE}{BASE}{a["rubric"]}/{a["slug"]}/', 'datePublished': a['date']} for a in arts]}]}
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(
        page(0, f'{JOURNAL} Aldo Coppola о волосах, коже и моде', 'Экспертные статьи колористов, стилистов и врачей-косметологов Aldo Coppola: окрашивание, уход, косметология, мода и история итальянского бренда.', SITE + BASE, index_body, ld, SITE + BASE + lead_cover))

    # рубрики
    for k, (name, about) in RUBRICS.items():
        items = [a for a in arts if a['rubric'] == k]
        d = os.path.join(ROOT, k); os.makedirs(d, exist_ok=True)
        chips = '<a class="chip" href="../">Все</a>' + ''.join(f'<a class="chip" href="../{kk}/"' + (' aria-current="page"' if kk == k else '') + f'>{v[0]}</a>' for kk, v in RUBRICS.items())
        body = f'''
<section class="jcover wrap small">
  <nav class="crumbs" aria-label="Хлебные крошки"><a href="../../">Aldo Coppola</a><span>/</span><a href="../">{JOURNAL}</a></nav>
  <h1 class="jmast">{name}<span class="sr"> — рубрика раздела «{JOURNAL}» Aldo Coppola</span></h1>
  <p class="jlead">{about}</p>
  <nav class="chips" aria-label="Рубрики">{chips}</nav>
</section>
<section class="wrap"><div class="feed list">{''.join(card(a, 1) for a in items) or '<p>Материалы скоро появятся.</p>'}</div></section>'''
        ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': f'{name} — {JOURNAL.lower()} Aldo Coppola', 'url': f'{SITE}{BASE}{k}/'}
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
            page(1, f'{name} — {JOURNAL.lower()} Aldo Coppola', f'{about} Статьи рубрики «{name}» на сайте Aldo Coppola.', f'{SITE}{BASE}{k}/', body, ld, SITE + '/media/og-home.jpg'))

    # RSS и sitemap
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    items = ''.join(f'<item><title>{esc(title_plain(a["title"]))}</title><link>{SITE}{BASE}{a["rubric"]}/{a["slug"]}/</link><guid>{SITE}{BASE}{a["rubric"]}/{a["slug"]}/</guid><pubDate>{datetime.datetime.fromisoformat(a["date"]).strftime("%a, %d %b %Y 09:00:00 +0300")}</pubDate><description>{esc(a["dek"])}</description></item>' for a in arts)
    open(os.path.join(ROOT, 'rss.xml'), 'w', encoding='utf-8').write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{JOURNAL} Aldo Coppola</title><link>{SITE}{BASE}</link><description>О волосах, коже и моде</description><language>ru</language><lastBuildDate>{now}</lastBuildDate>{items}</channel></rss>')
    urls = [SITE + BASE] + [f'{SITE}{BASE}{k}/' for k in RUBRICS] + [f'{SITE}{BASE}{a["rubric"]}/{a["slug"]}/' for a in arts]
    lm = {f'{SITE}{BASE}{a["rubric"]}/{a["slug"]}/': a['updated'] for a in arts}
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc>' + (f'<lastmod>{lm[u]}</lastmod>' if u in lm else '') + '</url>' for u in urls) + '</urlset>')
    print(f'Собрано: {len(arts)} статей, {len(RUBRICS)} рубрик')
    for a in arts: print(f'  {a["rubric"]}/{a["slug"]}  {a["words"]} слов, {a["read"]} мин')

if __name__ == '__main__':
    build()
