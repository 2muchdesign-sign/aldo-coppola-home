#!/usr/bin/env python3
"""Прайсы YClients → _build/data/salon-services.json (направления по салонам)
и _build/data/uslugi-prices.json (каждая услуга: ID, цена от–до, длительность по салонам).

Нужен xlrd (есть в ../aldo-coppola-cosmetology/.venv):
  ../aldo-coppola-cosmetology/.venv/bin/python _build/salon_services.py
Запускать при обновлении прайсов; сайт собирается из готового JSON.
"""
import collections, datetime, json, os, xlrd

HERE = os.path.dirname(os.path.abspath(__file__))
PRICES = os.path.normpath(os.path.join(HERE, '..', '..', 'Work Claude', '13 Прайс листы', 'Прайс листы всех салонов для YClients_nov2026'))
FILES = {'zhukovka': 'Жуковка', 'barvikha': 'Барвиха', 'veb-rf': 'Новинский', 'vremena-goda': 'Времена года',
         'boscovesna': 'Весна', 'unimall': 'Юнимолл', 'lotte': 'Лотте'}
# направление: (название, категории прайса)
DIRS = [
    ('volosy', 'Волосы', ['СТРИЖКИ И УКЛАДКИ', 'ОКРАШИВАНИЯ', 'ЛЕЧЕНИЕ ВОЛОС']),
    ('kosmetologiya', 'Косметология', ['УХОДЫ ДЛЯ ЛИЦА', 'АППАРАТНАЯ КОСМЕТОЛОГИЯ', 'БОТУЛИНОТЕРАПИЯ', 'КОНТУРНАЯ ПЛАСТИКА',
        'МЕЗОТЕРАПИЯ И БИОРЕВИТАЛИЗАЦИЯ', 'ПЛАЗМОТЕРАПИЯ', 'НИТЕВОЙ ЛИФТИНГ', 'ЛИПОЛИТИКИ', 'SPRS-ТЕРАПИЯ',
        'ВИТАМИННЫЕ КАПЕЛЬНЫЕ КОКТЕЙЛИ', 'МОДЕЛИРОВАНИЕ КОНТУРОВ ТЕЛА', 'АВТОРСКИЙ МАССАЖ ЛИЦА FACE FITNESS BY ALDO COPPOLA']),
    ('nogti', 'Ногти', ['НОГТЕВОЙ СЕРВИС']),
    ('brovi-resnicy', 'Брови и ресницы', ['БРОВИ-РЕСНИЦЫ', 'НАРАЩИВАНИЕ РЕСНИЦ']),
    ('makiyazh', 'Макияж', ['МАКИЯЖИ']),
    ('permanent', 'Перманентный макияж', ['ПЕРМАНЕНТНЫЙ МАКИЯЖ']),
    ('epilyaciya', 'Эпиляция', ['ВОСКОВАЯ ДЕПИЛЯЦИЯ', 'ЛАЗЕРНАЯ ЭПИЛЯЦИЯ']),
    ('massazh', 'Массаж и уход за телом', ['МАССАЖИ И ОБЁРТЫВАНИЯ']),
    ('muzhchinam', 'Мужчинам', ['ДЛЯ МУЖЧИН']),
    ('detyam', 'Детям до 10 лет', ['ДЛЯ ДЕТЕЙ (до 10 лет)']),
]

out = {'source': os.path.basename(PRICES), 'built': datetime.date.today().isoformat(), 'directions': [[k, n] for k, n, _ in DIRS], 'salons': {}}
for slug, name in FILES.items():
    sh = xlrd.open_workbook(os.path.join(PRICES, name + '.xls'), ignore_workbook_corruption=True).sheet_by_index(0)
    ids, mins = collections.defaultdict(set), {}
    for r in range(1, sh.nrows):
        cat, sid, price = sh.cell_value(r, 0), sh.cell_value(r, 1), sh.cell_value(r, 6)
        ids[cat].add(sid)
        if isinstance(price, float) and price > 0:
            mins[cat] = min(mins.get(cat, price), price)
    res = {}
    for k, _, cats in DIRS:
        n = sum(len(ids[c]) for c in cats if c in ids)
        p = [mins[c] for c in cats if c in mins]
        if n:
            res[k] = {'count': n, 'from': int(min(p)) if p else None}
    out['salons'][slug] = res
json.dump(out, open(os.path.join(HERE, 'data', 'salon-services.json'), 'w'), ensure_ascii=False, indent=1)
# цены по каждой услуге
prices = {}
for slug, name in FILES.items():
    sh = xlrd.open_workbook(os.path.join(PRICES, name + '.xls'), ignore_workbook_corruption=True).sheet_by_index(0)
    for r in range(1, sh.nrows):
        cat, sid, title, price, dur = sh.cell_value(r, 0), sh.cell_value(r, 1), sh.cell_value(r, 2).strip(), sh.cell_value(r, 6), sh.cell_value(r, 11)
        e = prices.setdefault(title, {}).setdefault(slug, {'id': int(sid), 'cat': cat, 'min': None, 'max': None, 'dur': None})
        if isinstance(price, float) and price > 0:
            e['min'] = int(price) if e['min'] is None else min(e['min'], int(price))
            e['max'] = int(price) if e['max'] is None else max(e['max'], int(price))
        if isinstance(dur, float) and dur > 0:
            e['dur'] = int(dur // 60) if e['dur'] is None else max(e['dur'], int(dur // 60))
json.dump({'source': out['source'], 'built': out['built'], 'prices': prices}, open(os.path.join(HERE, 'data', 'uslugi-prices.json'), 'w'), ensure_ascii=False, indent=0)
print('услуг в прайсах:', len(prices))
print(json.dumps(out['salons'], ensure_ascii=False)[:1500])
