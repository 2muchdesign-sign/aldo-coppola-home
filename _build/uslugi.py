#!/usr/bin/env python3
"""Каталог услуг: _build/data/uslugi.json + uslugi-prices.json → src/uslugi/** и src/ceny/.

Запускается из _build/build.py (или отдельно: python3 _build/uslugi.py).
Цены, длительность, салоны и ID услуг для записи — из прайсов YClients (обновить: _build/salon_services.py).
Вёрстка — src/_ac/pages.css.
В Битриксе: инфоблок «Услуги» (поля uslugi.json) + цены из YClients по ID услуги.
"""
import json, os, re
import salony as S

OUT = os.path.join(S.ROOT, 'src')
U = json.load(open(os.path.join(S.HERE, 'data', 'uslugi.json'), encoding='utf-8'))
PR = json.load(open(os.path.join(S.HERE, 'data', 'uslugi-prices.json'), encoding='utf-8'))
P = PR['prices']
DIRS = U['directions']
DBY = {d['slug']: d for d in DIRS}
SV = U['services']
SBY = {s['slug']: s for s in SV}
CSS = ('/_ac/pages.css',)
JS = ()
NB = ' '
BUILT = f'{PR["built"][8:10]}.{PR["built"][5:7]}.{PR["built"][:4]}'

def rub(n):
    return f'{n:,}'.replace(',', NB) + NB + '₽'

def rng(a, b):
    if a is None:
        return '—'
    return rub(a) if a == b or b is None else f'{a:,}'.replace(',', NB) + '–' + rub(b)

def book(sal, sid):
    return f'{sal["booking"].rstrip("/")}/company/{sal["branch"]}/personal/select-time?o=s{sid}'

def lines(s):
    return [m for m in s['match'] + s.get('extra_match', []) if m in P]

def stats(s):
    lo = hi = dlo = dhi = None
    salons = set()
    for m in s['match']:
        for slug, e in P.get(m, {}).items():
            salons.add(slug)
            if e['min'] is not None:
                lo = e['min'] if lo is None else min(lo, e['min'])
                hi = e['max'] if hi is None else max(hi, e['max'])
            if e['dur']:
                dlo = e['dur'] if dlo is None else min(dlo, e['dur'])
                dhi = e['dur'] if dhi is None else max(dhi, e['dur'])
    return lo, hi, dlo, dhi, [x for x in S.SALONS if x['slug'] in salons]

def minutes(a, b):
    def f(m):
        h, mm = divmod(m, 60)
        return (f'{h}{NB}ч' if h else '') + (f' {mm}{NB}мин' if mm and h else f'{mm}{NB}мин' if mm else '')
    if a is None:
        return None
    return f(a) if a == b else f'от {f(a)} до {f(b)}'

def art_title(path):
    p = os.path.join(S.ROOT, 'src', path.strip('/'), 'index.html')
    if not os.path.exists(p):
        return None
    m = re.search(r'<h1[^>]*>(.*?)</h1>', open(p, encoding='utf-8').read(), re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else None

def price_table(s):
    cols = [x for x in S.SALONS if any(x['slug'] in P[m] for m in lines(s))]
    head = ''.join(f'<th scope="col"><a href="/salony/{x["slug"]}/">{S.esc(x["short"])}</a></th>' for x in cols)
    rows = ''
    for m in lines(s):
        cells = ''
        for x in cols:
            e = P[m].get(x['slug'])
            cells += f'<td>{rng(e["min"], e["max"]) if e else "—"}</td>'
        rows += f'<tr><th scope="row">{S.esc(m)}</th>{cells}</tr>'
    return f'<div class="sl-mx us-mx" tabindex="0" role="region" aria-label="Цены по салонам"><table><thead><tr><th scope="col">Услуга</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'

def faq_html(items):
    return '<div class="us-faq">' + ''.join(f'<details><summary>{S.esc(q)}</summary><p>{S.esc(a)}</p></details>' for q, a in items) + '</div>'

def card(s):
    lo, hi, *_ = stats(s)
    return f'<li><a class="us-card" href="/uslugi/{s["dir"]}/{s["slug"]}/"><b>{S.esc(s["card"])}</b><span>{"от " + rub(lo) if lo else ""}</span></a></li>'

def articles_html(paths):
    items = [(p, art_title(p)) for p in paths or []]
    items = [(p, t) for p, t in items if t]
    if not items:
        return ''
    return '<section class="sl-sec wrap" aria-labelledby="art-h"><h2 id="art-h">Статьи по теме</h2><ul class="sl-others">' + ''.join(
        f'<li><a href="{p}"><b>{S.esc(t)}</b><span>Статьи Aldo Coppola</span></a></li>' for p, t in items) + '</ul></section>'

# ------------------------------------------------------------------ страница услуги
def service_page(s):
    d = DBY[s['dir']]
    lo, hi, dlo, dhi, sals = stats(s)
    dur = minutes(dlo, dhi)
    facts = f'<div class="us-facts"><div><span>Цена</span><b>от {rub(lo)}</b></div>' if lo else '<div class="us-facts">'
    facts += f'<div><span>Длительность</span><b>{dur}</b></div>' if dur else ''
    facts += f'<div><span>Салоны</span><b>{len(sals)} из {len(S.SALONS)}</b></div></div>'
    how = ''.join(f'<li>{S.esc(x)}</li>' for x in s.get('how', []))
    # запись сразу на услугу: первая строка прайса, которая есть в салоне
    bk = ''
    for x in sals:
        sid = next((P[m][x['slug']]['id'] for m in s['match'] if x['slug'] in P.get(m, {})), None)
        bk += f'<li><a href="{book(x, sid)}" target="_blank" rel="noopener"><b>{S.esc(x["name"])}</b><span>{S.esc(x["area"])}</span></a></li>'
    auto_faq = []
    if lo:
        auto_faq.append((f'Сколько стоит {s["card"][0].lower() + s["card"][1:]} в Aldo Coppola?',
                         f'От {rub(lo)} до {rub(hi)} в зависимости от салона, длины волос или объёма работы и категории мастера. Цены по салонам — в таблице выше, точную стоимость покажет онлайн-запись.'))
    if dur:
        auto_faq.append(('Сколько длится процедура?', f'По прайсу салонов — {dur}.'))
    auto_faq.append(('В каких салонах можно записаться?', ', '.join(x['name'] for x in sals) + '.'))
    faqs = s.get('faq', []) + auto_faq
    rel = [SBY[r] for r in s.get('related', []) if r in SBY]
    rel += [SBY[c.split('/')[1]] for c in s.get('cross', []) if c.split('/')[1] in SBY and SBY[c.split('/')[1]] not in rel]
    links = ''.join(f'<li><a href="{u}"><b>{S.esc(t)}</b><span>Косметология Aldo Coppola</span></a></li>' for t, u, *_ in s.get('links', []))
    body = f'''<div class="wrap">
  {S.crumbs([("Услуги и цены", "/uslugi/"), (d["name"], f"/uslugi/{d['slug']}/"), (s["card"], None)])}
  <header class="sl-head">
    <p class="eyebrow">{S.esc(d["name"])}</p>
    <h1>{S.esc(s["name"])}</h1>
    <p class="us-lead">{S.esc(s["lead"])}</p>
    {facts}
    <p class="sl-headact"><a class="sl-btn" href="#zapis">Записаться на услугу</a><a class="sl-phone" href="tel:{S.TEL}">{S.TEL_H}</a></p>
  </header>
</div>
<section class="sl-sec wrap" aria-labelledby="pr-h">
  <h2 id="pr-h">Цены по салонам</h2>
  <p class="sl-note">По прайсам салонов в YClients на {BUILT}. Цена зависит от категории мастера{", длины волос" if s["dir"] == "volosy" else ""} и объёма работы.</p>
  {price_table(s)}
</section>
{f'<section class="sl-sec wrap" aria-labelledby="how-h"><h2 id="how-h">Как проходит</h2><ol class="us-how">{how}</ol></section>' if how else ''}
<section class="sl-sec wrap" id="zapis" aria-labelledby="bk-h">
  <h2 id="bk-h">Записаться</h2>
  <p class="sl-note">Онлайн-запись откроется сразу на этой услуге в выбранном салоне.</p>
  <ul class="sl-others">{bk}</ul>
</section>
<section class="sl-sec wrap" aria-labelledby="faq-h">
  <h2 id="faq-h">Вопросы и ответы</h2>
  {faq_html(faqs)}
</section>
{articles_html(s.get("articles"))}
{f'<section class="sl-sec wrap" aria-labelledby="ln-h"><h2 id="ln-h">Смотрите также</h2><ul class="sl-others">{links}</ul></section>' if links else ''}
<section class="sl-sec wrap" aria-labelledby="rel-h">
  <h2 id="rel-h">Другие услуги</h2>
  <ul class="us-cards">{"".join(card(r) for r in rel)}</ul>
  <p class="sl-more"><a class="sl-link" href="/uslugi/{d["slug"]}/">Все услуги: {S.esc(d["name"].lower())}</a><a class="sl-link" href="/ceny/">Все цены</a></p>
</section>'''
    path = f'/uslugi/{d["slug"]}/{s["slug"]}/'
    items = [('Услуги и цены', '/uslugi/'), (d['name'], f'/uslugi/{d["slug"]}/'), (s['card'], path)]
    svc = {'@type': 'Service', '@id': S.SITE + path + '#service', 'name': s['name'], 'description': s['lead'], 'url': S.SITE + path,
           'serviceType': d['name'], 'provider': {'@id': S.SITE + '/#organization'},
           'areaServed': [{'@type': 'City', 'name': 'Москва'}, {'@type': 'AdministrativeArea', 'name': 'Московская область'}],
           'availableChannel': {'@type': 'ServiceChannel', 'serviceUrl': S.YCL}}
    if lo:
        svc['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'RUB', 'lowPrice': lo, 'highPrice': hi, 'offerCount': len(sals),
                         'availableAtOrFrom': [{'@id': f'{S.SITE}/salony/{x["slug"]}/#salon'} for x in sals]}
    ld = {'@context': 'https://schema.org', '@graph': [svc,
          {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
          S.bc_ld(items)]}
    title = f'{s["name"]} в Москве — цены в салонах Aldo Coppola'
    desc = (f'{s["name"]} в Aldo Coppola: от {rub(lo)}. ' if lo else '') + s['lead']
    return S.page(path, title, desc[:280], body, ld, css=CSS, js=JS)

# ------------------------------------------------------------------ направление
def direction_page(d):
    svs = [s for s in SV if s['dir'] == d['slug']]
    links = ''.join(f'<li><a class="us-card us-card--ext" href="{u}"><b>{S.esc(t)}</b><span>{S.esc(n)}</span></a></li>' for t, u, n in d.get('links', []))
    body = f'''<div class="wrap">
  {S.crumbs([("Услуги и цены", "/uslugi/"), (d["name"], None)])}
  <header class="sl-head">
    <p class="eyebrow">Услуги и цены</p>
    <h1>{S.esc(d["title"])}</h1>
    <p class="us-lead">{S.esc(d["lead"])}</p>
  </header>
  <ul class="us-cards us-cards--big">{"".join(card(s) for s in svs)}{links}</ul>
</div>
{articles_html(d.get("articles"))}
<section class="sl-sec wrap" aria-labelledby="bk-h">
  <h2 id="bk-h">Где сделать</h2>
  <p class="sl-note">Все семь салонов работают ежедневно с 10:00 до 22:00. Цены по салонам — на странице каждой услуги и в общей таблице цен.</p>
  <p class="sl-more"><a class="sl-link" href="/salony/">Центры красоты</a><a class="sl-link" href="/ceny/">Все цены</a><a class="sl-link sl-link--red" href="{S.YCL}" target="_blank" rel="noopener">Записаться онлайн</a></p>
</section>'''
    path = f'/uslugi/{d["slug"]}/'
    items = [('Услуги и цены', '/uslugi/'), (d['name'], path)]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': d['title'], 'url': S.SITE + path, 'hasPart': [{'@id': f'{S.SITE}/uslugi/{s["dir"]}/{s["slug"]}/#service'} for s in svs]},
        S.bc_ld(items)]}
    return S.page(path, f'{d["title"]} в Москве — услуги и цены Aldo Coppola', d['lead'][:280], body, ld, css=CSS, js=JS)

# ------------------------------------------------------------------ хаб
TASKS = [
    ('Посветлеть мягко, без полос', 'volosy/okrashivanie-shatush', 'Шатуш'),
    ('Закрасить седину бережно', 'volosy/okrashivanie-infusion', 'Окрашивание травами Infusion'),
    ('Восстановить волосы после осветления', 'volosy/lechenie-volos', 'Лечение волос'),
    ('Волосы выпадают', 'volosy/profilaktika-vypadeniya', 'Профилактика выпадения'),
    ('Образ на вечер или свадьбу', 'volosy/vechernyaya-pricheska', 'Причёска и макияж'),
    ('Брови каждое утро без геля', 'brovi-resnicy/dolgovremennaya-ukladka-brovey', 'Долговременная укладка'),
    ('Выразительный взгляд без туши', 'brovi-resnicy/keratinovaya-zavivka-resnic', 'Кератиновая завивка'),
    ('Тонкие, ломкие ногти', 'nogti/ukreplenie-nogtey', 'Укрепление ногтей'),
    ('Седина у мужчины — незаметно', 'muzhchinam/kamuflyazh-sediny', 'Камуфляж седины'),
]

def hub_page():
    tiles = ''
    for d in DIRS:
        n = len([s for s in SV if s['dir'] == d['slug']])
        sub = f'{n} {S.plural(n, "услуга", "услуги", "услуг")}' if n else 'в разделе косметологии'
        tiles += f'<li><a class="us-dir" href="/uslugi/{d["slug"]}/"><b>{S.esc(d["name"])}</b><span>{sub}</span></a></li>'
    tiles += '<li><a class="us-dir us-dir--k" href="/kosmetologiya/"><b>Косметология</b><span>аппаратная, инъекционная, уходы, тело</span></a></li>'
    tasks = ''.join(f'<tr><th scope="row">{S.esc(t)}</th><td><a href="/uslugi/{p}/">{S.esc(n)}</a></td></tr>' for t, p, n in TASKS)
    body = f'''<div class="wrap">
  {S.crumbs([("Услуги и цены", None)])}
  <header class="sl-head">
    <p class="eyebrow">Семь салонов в Москве и Подмосковье</p>
    <h1>Услуги и цены</h1>
    <p class="us-lead">Волосы, ногти, брови и ресницы, макияж, перманент и услуги для мужчин. У каждой услуги — цены по салонам и запись сразу на неё. До шести услуг можно совместить в один визит.</p>
  </header>
  <ul class="us-dirs">{tiles}</ul>
</div>
<section class="sl-sec wrap" aria-labelledby="t-h">
  <h2 id="t-h">С чего начать</h2>
  <div class="us-tasks"><table><thead><tr><th scope="col">Задача</th><th scope="col">Услуга</th></tr></thead><tbody>{tasks}</tbody></table></div>
</section>
<section class="sl-sec wrap" aria-labelledby="c-h">
  <h2 id="c-h">Цены</h2>
  <p class="sl-note">Все цены по салонам в одной таблице — по прайсам YClients на {BUILT}.</p>
  <p class="sl-more"><a class="sl-link" href="/ceny/">Все цены</a><a class="sl-link" href="/kosmetologiya/ceny/">Цены на косметологию</a></p>
</section>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': 'Услуги и цены Aldo Coppola', 'url': S.SITE + '/uslugi/'}, S.bc_ld([('Услуги и цены', '/uslugi/')])]}
    return S.page('/uslugi/', 'Услуги и цены Aldo Coppola — стрижки, окрашивание, маникюр, брови, макияж',
                  'Услуги центров красоты Aldo Coppola в Москве и Подмосковье: стрижки, шатуш, окрашивание Infusion, маникюр, брови и ресницы, макияж, перманент, услуги для мужчин. Цены по салонам и онлайн-запись.',
                  body, ld, css=CSS, js=JS)

# ------------------------------------------------------------------ все цены
CENY = [('Волосы', ['СТРИЖКИ И УКЛАДКИ', 'ОКРАШИВАНИЯ', 'ЛЕЧЕНИЕ ВОЛОС']), ('Детям до 10 лет', ['ДЛЯ ДЕТЕЙ (до 10 лет)']),
        ('Ногти', ['НОГТЕВОЙ СЕРВИС']), ('Брови и ресницы', ['БРОВИ-РЕСНИЦЫ', 'НАРАЩИВАНИЕ РЕСНИЦ']), ('Макияж', ['МАКИЯЖИ']),
        ('Перманентный макияж', ['ПЕРМАНЕНТНЫЙ МАКИЯЖ'])]

def link_for(name):
    for s in SV:
        if name in s['match']:
            return f'/uslugi/{s["dir"]}/{s["slug"]}/'
    return None

def ceny_page():
    head = ''.join(f'<th scope="col"><a href="/salony/{x["slug"]}/">{S.esc(x["short"])}</a></th>' for x in S.SALONS)
    secs = ''
    groups = CENY + [('Мужчинам', None)]
    for i, (title, cats) in enumerate(groups):
        if cats:
            names = [n for n, v in P.items() if any(e['cat'] in cats for e in v.values()) and not n.startswith('Комплекс')]
            names.sort(key=lambda n: (min(cats.index(e['cat']) for e in P[n].values() if e['cat'] in cats), n))
        else:
            names = [m for s in SV if s['dir'] == 'muzhchinam' for m in s['match']]
        rows = ''
        for n in names:
            cells = ''.join(f'<td>{rng(P[n][x["slug"]]["min"], P[n][x["slug"]]["max"]) if x["slug"] in P[n] else "—"}</td>' for x in S.SALONS)
            u = link_for(n)
            nm = f'<a href="{u}">{S.esc(n)}</a>' if u else S.esc(n)
            rows += f'<tr><th scope="row">{nm}</th>{cells}</tr>'
        secs += f'<section class="sl-sec wrap" aria-labelledby="c{i}"><h2 id="c{i}">{title}</h2><div class="sl-mx us-mx" tabindex="0" role="region" aria-label="{title}: цены по салонам"><table><thead><tr><th scope="col">Услуга</th>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>'
    nav = ''.join(f'<a class="us-chip" href="#c{i}">{t}</a>' for i, (t, _) in enumerate(groups)) + '<a class="us-chip" href="/kosmetologiya/ceny/">Косметология</a>'
    body = f'''<div class="wrap">
  {S.crumbs([("Цены", None)])}
  <header class="sl-head">
    <p class="eyebrow">Прайс всех салонов</p>
    <h1>Цены Aldo Coppola</h1>
    <p class="us-lead">Цены по семи салонам по прайсам YClients на {BUILT}. Диапазон «от–до» — разница по категории мастера и длине волос. Точную стоимость покажет онлайн-запись.</p>
    <nav class="us-chips" aria-label="Разделы прайса">{nav}</nav>
  </header>
</div>
{secs}'''
    ld = {'@context': 'https://schema.org', '@graph': [{'@type': 'WebPage', 'name': 'Цены Aldo Coppola', 'url': S.SITE + '/ceny/'}, S.bc_ld([('Цены', '/ceny/')])]}
    return S.page('/ceny/', 'Цены Aldo Coppola — прайс центров красоты по салонам',
                  'Цены на стрижки, окрашивание, маникюр, педикюр, брови, ресницы, макияж и перманент во всех салонах Aldo Coppola. Прайс по салонам.',
                  body, ld, css=CSS, js=JS)

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

if __name__ == '__main__':
    write('uslugi/index.html', hub_page())
    for d in DIRS:
        write(f'uslugi/{d["slug"]}/index.html', direction_page(d))
    for s in SV:
        write(f'uslugi/{s["dir"]}/{s["slug"]}/index.html', service_page(s))
    write('ceny/index.html', ceny_page())
    print(f'Услуги: хаб, {len(DIRS)} направлений, {len(SV)} услуг, /ceny/')
