#!/usr/bin/env python3
"""Спецпредложения и программа лояльности: _build/data/special.json → src/special/** и src/loyalty/.

Запускается из _build/build.py (или отдельно: python3 _build/special.py).
Предложение с publish:false или с прошедшей датой until на сайт не попадает.
В Битриксе: инфоблок «Акции» (активность по датам) и страница «Система лояльности».
"""
import datetime, json, os, shutil
import salony as S
from uslugi import rub

OUT = os.path.join(S.ROOT, 'src')
D = json.load(open(os.path.join(S.HERE, 'data', 'special.json'), encoding='utf-8'))
TODAY = datetime.date.today().isoformat()
OFFERS = [o for o in D['offers'] if o.get('publish') and (not o.get('until') or o['until'] >= TODAY)]
CSS = ('/salony/salony.css', '/uslugi/uslugi.css', '/special/special.css')
MED = 'Имеются противопоказания, необходима консультация специалиста.'

def ru_date(iso):
    y, m, d = iso.split('-')
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    return f'{int(d)} {months[int(m) - 1]} {y}'

def badge(o):
    if o.get('discount'):
        return f'<span class="sp-price"><b>{o["discount"]}</b></span>'
    if o.get('price'):
        old = f'<s>{rub(o["old_price"])}</s>' if o.get('old_price') else ''
        return f'<span class="sp-price"><b>{"от " if o.get("price_from") else ""}{rub(o["price"])}</b>{old}</span>'
    return ''

def where(o):
    if o.get('where'):
        return o['where']
    if not o.get('salons'):
        return 'Во всех салонах, где есть услуга'
    return ', '.join(S.BY[x]['name'] for x in o['salons'])

def offer_page(o):
    body_p = ''.join(f'<p>{S.esc(x)}</p>' for x in o.get('body', []))
    eff = ''.join(f'<li>{S.esc(x)}</li>' for x in o.get('effects', []))
    items = ''
    if o.get('items'):
        rows = ''.join(f'<li class="sp-item"><div><b>{S.esc(n)}</b><p>{S.esc(t)}</p></div><span class="sp-price"><b>{rub(p)}</b>{f"<s>{rub(old)}</s>" if old else ""}</span></li>' for n, t, p, old in o['items'])
        items = f'<ul class="sp-items">{rows}</ul>'
    links = ''.join(f'<li><a href="{u}"><b>{S.esc(t)}</b><span>Подробнее об услуге</span></a></li>' for t, u in o.get('links', []))
    until = f'Действует до {ru_date(o["until"])}.' if o.get('until') else 'Сроки действия и условия уточняйте у администратора.'
    others = [x for x in OFFERS if x is not o]
    cta = f'<a class="sl-btn" href="tel:{S.TEL}">Заказать по телефону</a>' if o.get('cta') == 'phone' else f'<a class="sl-btn" href="{S.YCL}" target="_blank" rel="noopener">Записаться онлайн</a>'
    body = f'''<div class="wrap">
  {S.crumbs([("Спецпредложения", "/special/"), (o["title"].split(":")[0].strip("«»"), None)])}
  <header class="sl-head">
    <p class="eyebrow">Спецпредложение · {S.esc(o["tag"])}</p>
    <h1>{S.esc(o["title"])}</h1>
    <p class="us-lead">{S.esc(o["short"])}</p>
    {badge(o)}
    <p class="sl-headact">{cta}<a class="sl-phone" href="tel:{S.TEL}">{S.TEL_H}</a></p>
  </header>
  <div class="sp-body">
    {f'<div class="sl-about">{body_p}</div>' if body_p else ''}
    {items}
    {f'<h2>Эффект</h2><ul class="sl-feats">{eff}</ul>' if eff else ''}
    {f'<p class="sp-note">{S.esc(o["note"])}</p>' if o.get("note") else ''}
    <p class="sl-note sp-terms">{where(o)}. {until}{" " + MED if o.get("medical") else ""}</p>
  </div>
</div>
{f'<section class="sl-sec wrap" aria-labelledby="ln-h"><h2 id="ln-h">Об услугах</h2><ul class="sl-others">{links}</ul></section>' if links else ''}
<section class="sl-sec wrap" aria-labelledby="oth-h">
  <h2 id="oth-h">Другие предложения</h2>
  <ul class="sp-list">{"".join(card(x) for x in others)}</ul>
  <p class="sl-more"><a class="sl-link" href="/special/">Все спецпредложения</a><a class="sl-link" href="/loyalty/">Система лояльности</a></p>
</section>'''
    path = f'/special/{o["slug"]}/'
    ld = {'@context': 'https://schema.org', '@graph': [S.bc_ld([('Спецпредложения', '/special/'), (o['title'], path)])]}
    if o.get('price'):
        off = {'@type': 'Offer', 'name': o['title'], 'price': o['price'], 'priceCurrency': 'RUB', 'url': S.SITE + path,
               'seller': {'@id': S.SITE + '/#organization'}}
        if o.get('until'):
            off['priceValidUntil'] = o['until']
        ld['@graph'].insert(0, off)
    return S.page(path, f'{o["title"]} — спецпредложение Aldo Coppola', o['short'], body, ld, css=CSS, js=())

def card(o):
    return f'''<li><a class="sp-card" href="/special/{o["slug"]}/">
      <span class="sp-tag">{S.esc(o["tag"])}</span>
      <b>{S.esc(o["title"])}</b>
      <span class="sp-short">{S.esc(o["short"])}</span>
      {badge(o)}
    </a></li>'''

def index_page():
    lst = ''.join(card(o) for o in OFFERS) or '<li class="sl-note">Сейчас действующих предложений нет. Следите за новостями в Telegram.</li>'
    body = f'''<div class="wrap">
  {S.crumbs([("Спецпредложения", None)])}
  <header class="sl-head">
    <p class="eyebrow">Акции и программы</p>
    <h1>Спецпредложения Aldo Coppola</h1>
    <p class="us-lead">Действующие предложения центров красоты. Скидки не суммируются с персональной скидкой клиента, если не указано иное.</p>
  </header>
  <ul class="sp-list">{lst}</ul>
</div>
<section class="sl-sec wrap" aria-labelledby="lo-h">
  <h2 id="lo-h">Бонусы за каждый визит</h2>
  <div class="sp-loy-teaser"><p>{S.esc(D["loyalty"]["welcome"])} Дальше — 5% или 10% бонусами в зависимости от статуса.</p><a class="sl-link sl-link--red" href="/loyalty/">Система лояльности</a></div>
</section>
<section class="sl-sec wrap" aria-labelledby="gi-h">
  <h2 id="gi-h">Подарочные сертификаты</h2>
  <p class="sl-note">Электронный сертификат с выбором дизайна и моментальной доставкой или пластиковый — в любом центре красоты и с доставкой из интернет-магазина.</p>
  <p class="sl-more"><a class="sl-link" href="https://gift.aldocoppola.ru/" target="_blank" rel="noopener">Электронный сертификат</a><a class="sl-link" href="https://beautybar.aldocoppola.ru/collection/podarochnye-sertifikaty-na-uslugi-v-tsentrah-krasoty-i-kosmetologii-aldo-coppola" target="_blank" rel="noopener">Пластиковый сертификат</a></p>
</section>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': 'Спецпредложения Aldo Coppola', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'url': f'{S.SITE}/special/{o["slug"]}/', 'name': o['title']} for i, o in enumerate(OFFERS, 1)]},
        S.bc_ld([('Спецпредложения', '/special/')])]}
    return S.page('/special/', 'Спецпредложения и акции Aldo Coppola', 'Действующие акции центров красоты Aldo Coppola: специальные цены на уходы, параллельный сервис, выездные сеты для свадьбы и событий.', body, ld, css=CSS, js=())

def loyalty_page():
    L = D['loyalty']
    lv = ''.join(f'<li class="sp-lv sp-lv--{n.lower()}"><b>{n}</b><span class="sp-lv-p">{p}</span><span>бонусами с каждого чека {S.esc(c)}</span></li>' for n, p, c in L['levels'])
    rules = ''.join(f'<li>{S.esc(r)}</li>' for r in L['rules'])
    body = f'''<div class="wrap">
  {S.crumbs([("Система лояльности", None)])}
  <header class="sl-head">
    <p class="eyebrow">Бонусная программа</p>
    <h1>Система лояльности Aldo Coppola</h1>
    <p class="us-lead">Бонусы возвращаются на счёт с каждого визита и не сгорают. Ими можно оплатить до 100% чека.</p>
  </header>
  <ol class="sp-steps">
    <li><b>Приветственный бонус</b><span>{S.esc(L["welcome"])}</span></li>
    <li><b>Статус</b><span>Чем больше сумма визитов за 12 месяцев, тем больше бонусов.</span></li>
    <li><b>Оплата бонусами</b><span>До 100% чека — на услуги, включая косметологию, и на товары.</span></li>
  </ol>
</div>
<section class="sl-sec wrap" aria-labelledby="lv-h">
  <h2 id="lv-h">Статусы</h2>
  <ul class="sp-lvs">{lv}</ul>
</section>
<section class="sl-sec wrap" aria-labelledby="ru-h">
  <h2 id="ru-h">Правила</h2>
  <ul class="sl-feats sp-rules">{rules}</ul>
  <p class="sl-more"><a class="sl-link" href="/special/">Спецпредложения</a><a class="sl-link sl-link--red" href="{S.YCL}" target="_blank" rel="noopener">Записаться онлайн</a></p>
</section>'''
    ld = {'@context': 'https://schema.org', '@graph': [S.bc_ld([('Система лояльности', '/loyalty/')])]}
    return S.page('/loyalty/', 'Система лояльности Aldo Coppola — бонусы и статусы RED и BLACK',
                  'Бонусная программа Aldo Coppola: 10% от первого чека, статусы RED (5%) и BLACK (10%), оплата бонусами до 100% чека, бонусы не сгорают.', body, ld, css=CSS, js=())

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

if __name__ == '__main__':
    # снятые предложения удаляются из src/special/
    keep = {o['slug'] for o in OFFERS}
    sp = os.path.join(OUT, 'special')
    if os.path.isdir(sp):
        for n in os.listdir(sp):
            if os.path.isdir(os.path.join(sp, n)) and n not in keep:
                shutil.rmtree(os.path.join(sp, n))
    write('special/index.html', index_page())
    for o in OFFERS:
        write(f'special/{o["slug"]}/index.html', offer_page(o))
    write('loyalty/index.html', loyalty_page())
    print(f'Спецпредложения: {len(OFFERS)}, система лояльности')
