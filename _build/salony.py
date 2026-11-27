#!/usr/bin/env python3
"""Раздел «Центры красоты»: _build/data/salons.json + salon-services.json → src/salony/.

Запускается из _build/build.py (или отдельно: python3 _build/salony.py).
Результат: src/salony/index.html, src/salony/{slug}/index.html, src/salony/regiony/index.html.
Стили — src/_ac/pages.css (общие для информационных страниц), скрипт галереи — src/salony/salony.js. Фото — src/salony/media/{slug}/NN-1600.webp и NN-800.webp.
В Битриксе: инфоблок «Салоны», поля = ключи salons.json.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'src', 'salony')
SITE = 'https://aldocoppola.ru'
D = json.load(open(os.path.join(HERE, 'data', 'salons.json'), encoding='utf-8'))
SV = json.load(open(os.path.join(HERE, 'data', 'salon-services.json'), encoding='utf-8'))
SALONS = D['salons']
SP = json.load(open(os.path.join(HERE, 'data', 'specialists.json'), encoding='utf-8'))
PEOPLE = [x for x in SP['people'] if x.get('publish')]
BY = {s['slug']: s for s in SALONS}
DIRS = SV['directions']
YCL = 'https://w2217426.yclients.com/'
TEL, TEL_H = '+74956465879', '+7 (495) 646-58-79'

FP, LZ = ' fetchpriority="high"', ' loading="lazy"'
esc = lambda s: html.escape(s or '', quote=True)
tel = lambda p: '+' + re.sub(r'\D', '', p)
wa = lambda p: 'https://wa.me/' + re.sub(r'\D', '', p)

def plural(n, one, few, many):
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many

def photos(s):
    d = os.path.join(OUT, 'media', s['slug'])
    if not os.path.isdir(d):
        return []
    return sorted(f[:2] for f in os.listdir(d) if f.endswith('-1600.webp'))

def img(s, n, w=800):
    return f'/salony/media/{s["slug"]}/{n}-{w}.webp'

def page(path, title, desc, body, ld, og_image=None, extra_head='', css=('/_ac/pages.css',), js=('/salony/salony.js',)):
    og = f'<meta property="og:image" content="{SITE}{og_image}">' if og_image else ''
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Aldo Coppola"><meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{path}">{og}
<meta name="twitter:card" content="summary_large_image">
<!--#site-head-->
<link href="https://fonts.googleapis.com/css2?family=PT+Sans+Narrow:wght@400;700&display=swap" rel="stylesheet">
{''.join(f'<link rel="stylesheet" href="{c}">' for c in css)}
{extra_head}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Перейти к содержимому</a>
<!--#site-header-->
<main id="main" class="sl">
{body}
</main>
<!--#site-footer-->
{''.join(f'<script src="{j}" defer></script>' for j in js)}
</body>
</html>
'''

def crumbs(items):
    out = '<nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Aldo Coppola</a>'
    for t, u in items:
        out += f'<span aria-hidden="true">/</span>' + (f'<a href="{u}">{esc(t)}</a>' if u else f'<span aria-current="page">{esc(t)}</span>')
    return out + '</nav>'

def bc_ld(items):
    els = [{'@type': 'ListItem', 'position': 1, 'name': 'Aldo Coppola', 'item': SITE + '/'}]
    for i, (t, u) in enumerate(items, 2):
        els.append({'@type': 'ListItem', 'position': i, 'name': t, 'item': SITE + u})
    return {'@type': 'BreadcrumbList', 'itemListElement': els}

def salon_ld(s, full=False):
    d = {'@type': ['BeautySalon'] + (['MedicalClinic'] if s['cosmetology'] and full else []),
         '@id': f'{SITE}/salony/{s["slug"]}/#salon', 'name': f'Aldo Coppola {s["name"]}',
         'url': f'{SITE}/salony/{s["slug"]}/', 'telephone': tel(s['phone']),
         'address': {'@type': 'PostalAddress', 'streetAddress': s['street'], 'addressLocality': s['locality'], 'addressCountry': 'RU'},
         'openingHours': D['hours_schema'], 'hasMap': s['map'],
         'parentOrganization': {'@id': SITE + '/#organization'}}
    ph = photos(s)
    if ph:
        d['image'] = [SITE + img(s, n, 1600) for n in ph[:3]]
    if full:
        d['description'] = s['about']
        d['potentialAction'] = {'@type': 'ReserveAction', 'target': s['booking']}
    return d

# ------------------------------------------------------------------ страница салона
def salon_page(s):
    ph = photos(s)
    region = 'Москва' if s['region'] == 'Москва' else 'Подмосковье'
    tour = ''
    if s.get('tour'):
        tour = f'<button class="sl-btn sl-btn--line" type="button" data-tour="/media/tour/{s["tour"]}.mp4" data-poster="/media/tour/{s["tour"]}.jpg" data-title="Видеотур: Aldo Coppola {esc(s["name"])}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>Видеотур</button>'
    card = f'''<aside class="sl-card" aria-label="Адрес и запись">
      <address><b>{esc(s["address"])}</b><br>{esc(s["place"])}</address>
      <p class="sl-hours">{esc(D["hours"])}</p>
      <p class="sl-tel"><a href="tel:{tel(s["phone"])}">{esc(s["phone"])}</a><a class="sl-wa" href="{wa(s["mobile"])}" target="_blank" rel="noopener">WhatsApp {esc(s["mobile"])}</a></p>
      <div class="sl-actions">
        <a class="sl-btn" href="{s["booking"]}" target="_blank" rel="noopener">Записаться онлайн</a>
        <a class="sl-btn sl-btn--line" href="{s["map"]}" target="_blank" rel="noopener">Маршрут</a>
        {tour}
      </div>
    </aside>'''
    gal = ''
    if ph:
        figs = ''.join(f'<figure><img src="{img(s, n)}" srcset="{img(s, n)} 800w, {img(s, n, 1600)} 1600w" sizes="(min-width:1000px) 60vw, 88vw" alt="Aldo Coppola {esc(s["name"])}: интерьер, фото {i}" width="1600" height="1066"{FP if i == 1 else LZ} decoding="async"></figure>' for i, n in enumerate(ph, 1))
        gal = f'''<div class="sl-gal" data-gal>
      <div class="sl-gal__track" tabindex="0" aria-label="Фотографии салона, листайте">{figs}</div>
      <div class="sl-gal__nav"><button type="button" data-prev aria-label="Предыдущее фото">←</button><span data-count>1 / {len(ph)}</span><button type="button" data-next aria-label="Следующее фото">→</button></div>
    </div>'''
    feats = ''.join(f'<li>{esc(f)}</li>' for f in s.get('features', []))
    feats = f'<ul class="sl-feats">{feats}</ul>' if feats else ''
    sv = SV['salons'].get(s['slug'], {})
    tiles = []
    for k, name in DIRS:
        if k not in sv:
            continue
        n = sv[k]['count']
        cnt = f'{n} {plural(n, "услуга", "услуги", "услуг")}'
        if k == 'kosmetologiya':
            tiles.append(f'<a class="sl-dir sl-dir--link" href="/kosmetologiya/salony/{s["slug"]}/"><b>{name}</b><span>{cnt} · процедуры и цены</span></a>')
        else:
            tiles.append(f'<div class="sl-dir"><b>{name}</b><span>{cnt}</span></div>')
    if not s['cosmetology'] and s.get('nearest'):
        nb = BY[s['nearest']]
        tiles.append(f'<a class="sl-dir sl-dir--link sl-dir--note" href="/salony/{nb["slug"]}/"><b>Косметология</b><span>в этом салоне нет — ближайшая в {esc(nb["name"])}</span></a>')
    ppl = [x for x in PEOPLE if x.get('salon') == s['slug']]
    team = ''
    if ppl:
        cards = ''.join(f'<li><a class="sl-person" href="/specialisty/{x["slug"]}/">' + (f'<img src="{x["photo"]}" alt="" width="160" height="200" loading="lazy">' if x.get('photo') else f'<span class="sl-mono" aria-hidden="true">{x["name"][0]}</span>') + f'<span><b>{esc(x["name"])}</b><small>{esc(x["role"])}</small></span></a></li>' for x in ppl)
        team = f'''<section class="sl-sec wrap" aria-labelledby="team-h">
  <h2 id="team-h">Специалисты салона</h2>
  <ul class="sl-team">{cards}</ul>
  <p class="sl-more"><a class="sl-link" href="/specialisty/">Все специалисты</a></p>
</section>
'''
    others = ''.join(f'<li><a href="/salony/{o["slug"]}/"><b>{esc(o["name"])}</b><span>{esc(o["area"])}</span></a></li>' for o in SALONS if o is not s)
    body = f'''<div class="wrap">
  {crumbs([("Центры красоты", "/salony/"), (s["name"], None)])}
  <header class="sl-head">
    <p class="eyebrow">Центр красоты · {region}, {esc(s["area"])}</p>
    <h1>Aldo Coppola {esc(s["name"])}</h1>
    <p class="sl-tagline">{esc(s["tagline"])}</p>
  </header>
  <div class="sl-top">
    {card}
    {gal}
  </div>
</div>
<section class="sl-sec wrap" aria-labelledby="about-h">
  <h2 id="about-h">О салоне</h2>
  <div class="sl-about"><p>{esc(s["about"])}</p>{feats}</div>
</section>
<section class="sl-sec wrap" aria-labelledby="dirs-h">
  <h2 id="dirs-h">Услуги в салоне</h2>
  <p class="sl-note">По прайсу салона в YClients. Цены зависят от категории мастера — точную стоимость покажет онлайн-запись.</p>
  <div class="sl-dirs">{"".join(tiles)}</div>
</section>
{team}<section class="sl-sec wrap" aria-labelledby="oth-h">
  <h2 id="oth-h">Другие центры красоты</h2>
  <ul class="sl-others">{others}</ul>
  <p class="sl-more"><a class="sl-link" href="/salony/">Все салоны и адреса</a> <a class="sl-link" href="/salony/regiony/">Салоны в регионах</a></p>
</section>
<dialog class="sl-tour" data-tour-dialog aria-label="Видеотур"><div class="sl-tour__in"><p class="sl-tour__t" data-tour-title></p><video controls playsinline preload="none"></video><button type="button" class="sl-tour__x" data-tour-close aria-label="Закрыть">✕</button></div></dialog>'''
    items = [('Центры красоты', '/salony/'), (s['name'], f'/salony/{s["slug"]}/')]
    ld = {'@context': 'https://schema.org', '@graph': [salon_ld(s, True), bc_ld(items)]}
    title = f'Aldo Coppola {s["name"]} — центр красоты, {s["area"]}'
    desc = f'Центр красоты Aldo Coppola {s["name"]}: {s["address"]}, {s["place"]}. {D["hours"]}. Телефон {s["phone"]}, онлайн-запись.'
    return page(f'/salony/{s["slug"]}/', title, desc, body, ld, img(s, ph[0], 1600) if ph else None)

# ------------------------------------------------------------------ все салоны
def index_page():
    groups = ''
    for reg, label in (('Москва', 'Москва'), ('Московская область', 'Московская область')):
        cards = ''
        for s in [x for x in SALONS if x['region'] == reg]:
            ph = photos(s)
            pic = f'<img src="{img(s, ph[0])}" alt="" width="800" height="533" loading="lazy" decoding="async">' if ph else ''
            cards += f'''<li class="sc">
        <a class="sc-img" href="/salony/{s["slug"]}/" tabindex="-1" aria-hidden="true">{pic}</a>
        <div class="sc-b">
          <h3><a href="/salony/{s["slug"]}/">{esc(s["name"])}</a></h3>
          <p class="sc-a">{esc(s["address"])}, {esc(s["place"])}</p>
          <p class="sc-c"><a href="tel:{tel(s["phone"])}">{esc(s["phone"])}</a>{"" if s["cosmetology"] else '<span class="sc-tag">без косметологии</span>'}</p>
          <p class="sc-l"><a class="sl-link" href="/salony/{s["slug"]}/">О салоне</a><a class="sl-link sl-link--red" href="{s["booking"]}" target="_blank" rel="noopener">Записаться</a></p>
        </div>
      </li>'''
        groups += f'<section class="sl-group" aria-labelledby="g-{reg[:3]}"><h2 id="g-{reg[:3]}">{label}</h2><ul class="sc-list">{cards}</ul></section>'
    # матрица услуг
    head = ''.join(f'<th scope="col"><a href="/salony/{s["slug"]}/">{esc(s["short"])}</a></th>' for s in SALONS)
    rows = ''
    for k, name in DIRS:
        cells = ''.join('<td>' + ('<span class="yes" aria-label="есть">●</span>' if k in SV['salons'].get(s['slug'], {}) else '<span class="no" aria-label="нет">—</span>') + '</td>' for s in SALONS)
        rows += f'<tr><th scope="row">{name}</th>{cells}</tr>'
    body = f'''<div class="wrap">
  {crumbs([("Центры красоты", None)])}
  <header class="sl-head">
    <p class="eyebrow">Москва и Подмосковье</p>
    <h1>Центры красоты Aldo Coppola</h1>
    <p class="sl-tagline">Семь салонов: четыре в Москве и три на Рублёво-Успенском и Новорижском шоссе. {esc(D["hours"])}.</p>
    <p class="sl-headact"><a class="sl-btn" href="{YCL}" target="_blank" rel="noopener">Записаться онлайн</a><a class="sl-phone" href="tel:{TEL}">{TEL_H}</a></p>
  </header>
  {groups}
</div>
<section class="sl-sec wrap" aria-labelledby="mx-h">
  <h2 id="mx-h">Какие услуги где</h2>
  <p class="sl-note">По прайсам салонов в YClients, {SV["built"][8:10]}.{SV["built"][5:7]}.{SV["built"][:4]}.</p>
  <div class="sl-mx" tabindex="0" role="region" aria-label="Таблица услуг по салонам"><table><thead><tr><th scope="col">Направление</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section class="sl-sec wrap" aria-labelledby="rg-h">
  <h2 id="rg-h">Салоны в регионах</h2>
  <p class="sl-about"><span>Aldo Coppola работает в Краснодаре, Сочи, Новосибирске, Перми, Ростове-на-Дону, Махачкале и Астане.</span></p>
  <p class="sl-more"><a class="sl-link" href="/salony/regiony/">Адреса и телефоны</a></p>
</section>
<section class="sl-sec wrap" aria-labelledby="doc-h">
  <h2 id="doc-h">Лицензии и юридические лица</h2>
  <p class="sl-note">Реквизиты юридических лиц и медицинские лицензии салонов появятся здесь после согласования с юристом.</p>
</section>'''
    items = [('Центры красоты', '/salony/')]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': 'Центры красоты Aldo Coppola', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'item': salon_ld(s)} for i, s in enumerate(SALONS, 1)]},
        bc_ld(items)]}
    first = photos(BY['zhukovka'])
    return page('/salony/', 'Центры красоты Aldo Coppola в Москве и Подмосковье — адреса и телефоны',
                'Семь центров красоты Aldo Coppola: BoscoVesna, Времена года, ВЭБ РФ, Лотте Отель, Жуковка, Барвиха, Юнимолл. Адреса, телефоны, услуги, онлайн-запись.',
                body, ld, img(BY['zhukovka'], first[0], 1600) if first else None)

def regions_page():
    rows = ''
    for r in D['regions']:
        city = r['city'] + (f', {r["country"]}' if r.get('country') else '')
        ph = f'<a href="tel:{tel(r["phone"])}">{esc(r["phone"])}</a>' if r.get('phone') else ''
        rows += f'<li class="rg"><h3>{esc(city)}</h3><p>{esc(r["address"])}</p><p>{ph}</p></li>'
    body = f'''<div class="wrap">
  {crumbs([("Центры красоты", "/salony/"), ("Регионы", None)])}
  <header class="sl-head">
    <p class="eyebrow">Россия и Казахстан</p>
    <h1>Aldo Coppola в регионах</h1>
    <p class="sl-tagline">Центры красоты партнёров Aldo Coppola. Запись и цены — по телефону салона.</p>
  </header>
  <ul class="rg-list">{rows}</ul>
  <aside class="sl-cta"><p>{esc(D.get("franchise_note", ""))} Хотите открыть Aldo Coppola в своём городе?</p><a class="sl-link sl-link--red" href="/franchise/">Франшиза</a></aside>
</div>'''
    items = [('Центры красоты', '/salony/'), ('Регионы', '/salony/regiony/')]
    ld = {'@context': 'https://schema.org', '@graph': [bc_ld(items)]}
    return page('/salony/regiony/', 'Aldo Coppola в регионах — адреса центров красоты',
                'Центры красоты Aldo Coppola в Краснодаре, Сочи, Новосибирске, Перми, Ростове-на-Дону, Махачкале и Астане.', body, ld)

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

if __name__ == '__main__':
    write('index.html', index_page())
    write('regiony/index.html', regions_page())
    for s in SALONS:
        write(f'{s["slug"]}/index.html', salon_page(s))
    print(f'Салоны: {len(SALONS)} страниц, регионов {len(D["regions"])}')
