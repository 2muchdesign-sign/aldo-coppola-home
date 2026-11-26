#!/usr/bin/env python3
"""Раздел «Специалисты»: _build/data/specialists.json → src/specialisty/.

Запускается из _build/build.py (или отдельно: python3 _build/specialisty.py).
Публикуются только записи с "publish": true. Вёрстка — общая с разделом салонов (src/salony/salony.css)
плюс src/specialisty/specialisty.css. В Битриксе: инфоблок «Специалисты», привязка к инфоблоку «Салоны».
"""
import json, os
import salony as S

OUT = os.path.join(S.ROOT, 'src', 'specialisty')
CSS = ('/salony/salony.css', '/specialisty/specialisty.css')
PEOPLE = S.PEOPLE
GROUPS = S.SP['groups']

def salon_of(p):
    return S.BY.get(p.get('salon') or '')

def photo(p, w=480, h=600, cls='sp-ph'):
    style = ' style="object-fit:contain;background:#fff"' if p.get('photo_contain') else ''
    if p.get('photo'):
        return f'<img class="{cls}" src="{p["photo"]}" alt="{S.esc(p["name"])}" width="{w}" height="{h}"{style} loading="lazy" decoding="async">'
    return f'<span class="{cls} sl-mono" role="img" aria-label="{S.esc(p["name"])}">{p["name"][0]}</span>'

def person_ld(p, full=False):
    d = {'@type': 'Person', '@id': f'{S.SITE}/specialisty/{p["slug"]}/#person', 'name': p['name'], 'jobTitle': p['role'],
         'url': f'{S.SITE}/specialisty/{p["slug"]}/'}
    if p.get('name_en'):
        d['alternateName'] = p['name_en']
    if p.get('photo'):
        d['image'] = S.SITE + p['photo']
    sal = salon_of(p)
    d['worksFor'] = {'@id': f'{S.SITE}/salony/{sal["slug"]}/#salon'} if sal else {'@id': S.SITE + '/#organization'}
    if full:
        d['description'] = p['lead']
        if p.get('work'):
            d['knowsAbout'] = p['work']
    return d

def person_page(p):
    sal = salon_of(p)
    where = f'<a href="/salony/{sal["slug"]}/">Aldo Coppola {S.esc(sal["name"])}</a>' if sal else 'Академия Aldo Coppola'
    facts = ''.join(f'<li>{S.esc(x)}</li>' for x in p.get('facts', []))
    work = ''.join(f'<li>{S.esc(x)}</li>' for x in p.get('work', []))
    quote = ''
    if p.get('quote'):
        it = f'<p class="sp-q-it" lang="it">{S.esc(p["quote_it"])}</p>' if p.get('quote_it') else ''
        quote = f'<figure class="sp-q"><blockquote><p>«{S.esc(p["quote"])}»</p></blockquote>{it}</figure>'
    acad = f'<p class="sp-acad">В Академии: <a href="/akademiya/#treningi">{S.esc(p["academy"])}</a></p>' if p.get('academy') else ''
    acts = ''
    if sal:
        acts = f'<a class="sl-btn" href="{sal["booking"]}" target="_blank" rel="noopener">Записаться в {S.esc(sal["short"])}</a><a class="sl-btn sl-btn--line" href="tel:{S.tel(sal["phone"])}">{S.esc(sal["phone"])}</a>'
    else:
        acts = f'<a class="sl-btn" href="/akademiya/">Обучение в Академии</a>'
    others = [x for x in PEOPLE if x is not p][:6]
    oth = ''.join(f'<li><a class="sl-person" href="/specialisty/{x["slug"]}/">{photo(x, 160, 200, "")}<span><b>{S.esc(x["name"])}</b><small>{S.esc(x["role"])}</small></span></a></li>' for x in others)
    body = f'''<div class="wrap">
  {S.crumbs([("Специалисты", "/specialisty/"), (p["name"], None)])}
  <article class="sp">
    <div class="sp-media">{photo(p)}</div>
    <div class="sp-b">
      <p class="eyebrow">{S.esc(p["role"])}</p>
      <h1>{S.esc(p["name"])}</h1>
      {f'<p class="sp-en" lang="it">{S.esc(p["name_en"])}</p>' if p.get("name_en") else ''}
      <p class="sp-where">{where}</p>
      <p class="sp-lead">{S.esc(p["lead"])}</p>
      {f'<ul class="sl-feats">{facts}</ul>' if facts else ''}
      {f'<h2>Чем занимается</h2><ul class="sp-work">{work}</ul>' if work else ''}
      {acad}
      <div class="sp-act">{acts}</div>
    </div>
  </article>
  {quote}
</div>
<section class="sl-sec wrap" aria-labelledby="oth-h">
  <h2 id="oth-h">Другие специалисты</h2>
  <ul class="sl-team">{oth}</ul>
  <p class="sl-more"><a class="sl-link" href="/specialisty/">Все специалисты</a></p>
</section>'''
    items = [('Специалисты', '/specialisty/'), (p['name'], f'/specialisty/{p["slug"]}/')]
    ld = {'@context': 'https://schema.org', '@graph': [person_ld(p, True), S.bc_ld(items)]}
    title = f'{p["name"]} — {p["role"].lower()} Aldo Coppola' + (f' {sal["name"]}' if sal else '')
    desc = f'{p["name"]}, {p["role"].lower()} Aldo Coppola' + (f' {sal["name"]}' if sal else '') + f'. {p["lead"]}'
    return S.page(f'/specialisty/{p["slug"]}/', title, desc[:300], body, ld, p.get('photo'), css=CSS, js=())

def index_page():
    blocks = ''
    for key, label in GROUPS:
        ppl = [x for x in PEOPLE if x['group'] == key]
        if not ppl:
            continue
        cards = ''
        for x in ppl:
            sal = salon_of(x)
            cards += f'''<li class="spc">
        <a href="/specialisty/{x["slug"]}/">{photo(x, 480, 600, "spc-ph")}
          <span class="spc-b"><b>{S.esc(x["name"])}</b><small>{S.esc(x["role"])}{" · " + S.esc(sal["name"]) if sal else ""}</small></span></a>
      </li>'''
        blocks += f'<section class="sl-group" aria-labelledby="g-{key}"><h2 id="g-{key}">{label}</h2><ul class="spc-list">{cards}</ul></section>'
    body = f'''<div class="wrap">
  {S.crumbs([("Специалисты", None)])}
  <header class="sl-head">
    <p class="eyebrow">Стилисты, колористы, врачи</p>
    <h1>Специалисты Aldo Coppola</h1>
    <p class="sl-tagline">Арт-директора салонов учились в Милане, работали на показах итальянских модных домов и сами преподают в Академии Aldo Coppola.</p>
  </header>
  {blocks}
</div>
<section class="sl-sec wrap" aria-labelledby="bk-h">
  <h2 id="bk-h">Запись к мастеру</h2>
  <p class="sl-note">В онлайн-записи каждого салона видны все мастера и их свободное время. Выберите салон:</p>
  <ul class="sl-others">{''.join(f'<li><a href="{s["booking"]}" target="_blank" rel="noopener"><b>{S.esc(s["name"])}</b><span>{S.esc(s["area"])}</span></a></li>' for s in S.SALONS)}</ul>
</section>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': 'Специалисты Aldo Coppola', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'item': person_ld(x)} for i, x in enumerate(PEOPLE, 1)]},
        S.bc_ld([('Специалисты', '/specialisty/')])]}
    return S.page('/specialisty/', 'Специалисты Aldo Coppola — арт-директора, стилисты, врачи',
                  'Арт-директора и стилисты центров красоты Aldo Coppola в Москве: опыт, салон, услуги, обучение в Академии. Онлайн-запись к мастеру.',
                  body, ld, css=CSS, js=())

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

if __name__ == '__main__':
    write('index.html', index_page())
    for p in PEOPLE:
        write(f'{p["slug"]}/index.html', person_page(p))
    hidden = [x['name'] for x in S.SP['people'] if not x.get('publish')]
    print(f'Специалисты: {len(PEOPLE)} страниц' + (f'; ждут подтверждения: {", ".join(hidden)}' if hidden else ''))
