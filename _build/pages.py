#!/usr/bin/env python3
"""Текстовые страницы и новости: _build/content/*.md и _build/content/news/*.md → src/.

Запускается из _build/build.py (или отдельно: python3 _build/pages.py).
Формат файла: шапка между строками «---» (path, title, h1, eyebrow, lead, description, hero, hero_alt, lang, source),
дальше текст: «## » и «### » — заголовки, «- » и «1. » — списки, «> » — врезка, строка с «<» — готовый HTML,
[текст](адрес) — ссылка, [текст](адрес){.btn} — кнопка, **жирный**, два пробела в конце строки — перенос.
Новости: шапка id, date (ГГГГ-ММ-ДД), title, image, gallery (адреса через пробел); адрес страницы — /news/{id}/.
В Битриксе: текстовые страницы — обычные страницы сайта, новости — инфоблок «Новости».
"""
import glob, html, json, os, re
import salony as S

C = os.path.join(S.HERE, 'content')
OUT = os.path.join(S.ROOT, 'src')
CSS = ('/salony/salony.css', '/uslugi/uslugi.css', '/_ac/text.css')
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

def parse(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)

def inline(t):
    t = html.escape(t, quote=False)
    def link(mm):
        text, url, cls = mm.group(1), html.unescape(mm.group(2)), (mm.group(3) or '')[1:-1]
        ext = ' target="_blank" rel="noopener"' if url.startswith('http') else ''
        c = {'.btn': ' class="sl-btn"', '.phone': ' class="sl-phone"'}.get(cls, '')
        return f'<a href="{html.escape(url)}"{c}{ext}>{text}</a>'
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)(\{\.\w+\})?', link, t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return t

def render(md):
    out, para, lst, lt = [], [], [], None
    def flush_p():
        if para:
            out.append('<p>' + ''.join(para).strip() + '</p>')
            para.clear()
    def flush_l():
        nonlocal lt
        if lst:
            out.append(f'<{lt}>' + ''.join(f'<li>{x}</li>' for x in lst) + f'</{lt}>')
            lst.clear()
        lt = None
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        l = raw.strip()
        if not l:
            flush_p(); flush_l(); i += 1; continue
        if l.startswith('<'):
            flush_p(); flush_l()
            block = [raw]
            while i + 1 < len(lines) and lines[i + 1].strip():
                i += 1; block.append(lines[i])
            out.append('\n'.join(block))
        elif l.startswith('### '):
            flush_p(); flush_l(); out.append(f'<h3>{inline(l[4:].strip())}</h3>')
        elif l.startswith('## '):
            flush_p(); flush_l(); out.append(f'<h2>{inline(l[3:])}</h2>')
        elif l.startswith('> '):
            flush_p(); flush_l(); out.append(f'<p class="tx-note">{inline(l[2:])}</p>')
        elif l.startswith('- '):
            flush_p()
            if lt != 'ul': flush_l(); lt = 'ul'
            lst.append(inline(l[2:]))
        elif re.match(r'\d+\. ', l) and (lt == 'ol' or not para):
            flush_p()
            if lt != 'ol': flush_l(); lt = 'ol'
            lst.append(inline(re.sub(r'^\d+\. ', '', l)))
        else:
            flush_l()
            br = raw.endswith('  ')
            para.append(inline(l) + ('<br>' if br else ' '))
        i += 1
    flush_p(); flush_l()
    return '\n'.join(out)

def crumbs_for(path, h1):
    parts = [p for p in path.strip('/').split('/') if p]
    items, acc = [], '/'
    names = {'o-brende': 'О бренде', 'news': 'Новости'}
    for p in parts[:-1]:
        acc += p + '/'
        items.append((names.get(p, p), acc))
    items.append((h1, None))
    return items

def text_page(meta, body):
    path = meta['path']
    hero = f'<figure class="tx-hero"><img src="{meta["hero"]}" alt="{S.esc(meta.get("hero_alt", ""))}" width="1600" height="900" fetchpriority="high"></figure>' if meta.get('hero') else ''
    content = f'''<div class="wrap">
  {S.crumbs(crumbs_for(path, meta["h1"]))}
  <header class="sl-head">
    <p class="eyebrow">{S.esc(meta.get("eyebrow", ""))}</p>
    <h1>{S.esc(meta["h1"])}</h1>
    {f'<p class="us-lead">{S.esc(meta["lead"])}</p>' if meta.get("lead") else ''}
  </header>
  {hero}
  <div class="tx">
{render(body)}
  </div>
</div>'''
    items = [(t, u or path) for t, u in crumbs_for(path, meta['h1'])]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': meta['title'], 'url': S.SITE + path, 'inLanguage': meta.get('lang', 'ru')}, S.bc_ld(items)]}
    s = S.page(path, meta['title'], meta.get('description', meta.get('lead', '')), content, ld, meta.get('hero'), css=CSS, js=())
    if meta.get('lang') == 'en':
        s = s.replace('<html lang="ru">', '<html lang="en">', 1).replace('<meta property="og:locale" content="ru_RU">', '<meta property="og:locale" content="en_US">', 1)
        s = s.replace('Перейти к содержимому', 'Skip to content', 1)
    return s

def ru_date(iso):
    y, m, d = iso.split('-')
    return f'{int(d)} {MONTHS[int(m) - 1]} {y}'

def news_pages():
    items = []
    for f in glob.glob(os.path.join(C, 'news', '*.md')):
        meta, body = parse(f)
        items.append((meta, body))
    items.sort(key=lambda x: x[0]['date'], reverse=True)
    pages = {}
    for meta, body in items:
        path = f'/news/{meta["id"]}/'
        img = f'<figure class="tx-hero"><img src="{meta["image"]}" alt="" loading="eager"></figure>' if meta.get('image') else ''
        gal = meta.get('gallery', '').split()
        gal = f'<div class="tx-gal">' + ''.join(f'<img src="{g}" alt="" loading="lazy">' for g in gal) + '</div>' if gal else ''
        other = ''.join([f'<li><a href="/news/{m["id"]}/"><b>{S.esc(m["title"])}</b><span>{ru_date(m["date"])}</span></a></li>' for m, _ in items if m is not meta][:4])
        content = f'''<div class="wrap">
  {S.crumbs([("Новости", "/news/"), (meta["title"][:60], None)])}
  <article>
  <header class="sl-head">
    <p class="eyebrow"><time datetime="{meta["date"]}">{ru_date(meta["date"])}</time></p>
    <h1 class="tx-h1-news">{S.esc(meta["title"])}</h1>
  </header>
  {img}
  <div class="tx">
{render(body)}
  {gal}
  </div>
  </article>
</div>
<section class="sl-sec wrap" aria-labelledby="mo-h">
  <h2 id="mo-h">Другие новости</h2>
  <ul class="sl-others">{other}</ul>
  <p class="sl-more"><a class="sl-link" href="/news/">Все новости</a></p>
</section>'''
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'NewsArticle', 'headline': meta['title'], 'datePublished': meta['date'], 'url': S.SITE + path,
             'image': [meta['image']] if meta.get('image') else [], 'publisher': {'@id': S.SITE + '/#organization'}, 'inLanguage': 'ru'},
            S.bc_ld([('Новости', '/news/'), (meta['title'], path)])]}
        first = re.sub(r'\s+', ' ', body.strip().split('\n\n')[0])[:200]
        pages[path] = S.page(path, f'{meta["title"]} — новости Aldo Coppola', first, content, ld, None, css=CSS, js=())
    cards = ''.join(f'''<li class="tx-news"><a href="/news/{m["id"]}/">{f'<img src="{m["image"]}" alt="" width="600" height="400" loading="lazy">' if m.get("image") else '<span class="tx-news-ph" aria-hidden="true"></span>'}<time datetime="{m["date"]}">{ru_date(m["date"])}</time><b>{S.esc(m["title"])}</b></a></li>''' for m, _ in items)
    content = f'''<div class="wrap">
  {S.crumbs([("Новости", None)])}
  <header class="sl-head">
    <p class="eyebrow">О бренде</p>
    <h1>Новости Aldo Coppola</h1>
    <p class="us-lead">События центров красоты, партнёрства, новые линии ухода и праздники бренда. Короткие новости — в нашем <a href="https://t.me/aldocoppola" target="_blank" rel="noopener">Telegram</a>.</p>
  </header>
  <ul class="tx-newslist">{cards}</ul>
</div>'''
    ld = {'@context': 'https://schema.org', '@graph': [{'@type': 'CollectionPage', 'name': 'Новости Aldo Coppola', 'url': S.SITE + '/news/'}, S.bc_ld([('Новости', '/news/')])]}
    pages['/news/'] = S.page('/news/', 'Новости Aldo Coppola', 'Новости сети центров красоты Aldo Coppola: события, партнёрства, новые линии ухода.', content, ld, None, css=CSS, js=())
    return pages

def write(path, s):
    p = os.path.join(OUT, path.strip('/'), 'index.html')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

if __name__ == '__main__':
    n = 0
    for f in sorted(glob.glob(os.path.join(C, '*.md'))):
        meta, body = parse(f)
        write(meta['path'], text_page(meta, body)); n += 1
    nw = news_pages()
    for path, s in nw.items():
        write(path, s)
    print(f'Текстовые страницы: {n}, новости: {len(nw) - 1}')
