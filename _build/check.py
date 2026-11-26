#!/usr/bin/env python3
"""Проверка собранного сайта _site/: битые внутренние ссылки и картинки, метки, которые не заменились.

Запуск после сборки:  python3 _build/check.py [--base /aldo-coppola-home/]
"""
import os, re, sys, collections
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '_site')
BASE = '/aldo-coppola-home/'
if '--base' in sys.argv:
    BASE = sys.argv[sys.argv.index('--base') + 1]

ATTR = re.compile(r'\s(?:href|src|poster|data-tour|data-poster)=["\']([^"\']+)["\']')
bad = collections.defaultdict(set)
left = []
n = 0
for d, _, files in os.walk(OUT):
    for f in files:
        if not f.endswith('.html'):
            continue
        full = os.path.join(d, f)
        page = '/' + os.path.relpath(full, OUT).replace(os.sep, '/')
        if page.startswith('/v2/'):
            continue
        s = re.sub(r'<!--(?!#site-).*?-->', '', open(full, encoding='utf-8').read(), flags=re.S)
        n += 1
        if '<!--#site-' in s:
            left.append(page)
        for u in ATTR.findall(s):
            if u.startswith(('http:', 'https:', '//', 'mailto:', 'tel:', 'data:', 'javascript:', '#', '${', "'+", '{')):
                continue
            if '/' not in u and '.' not in u:
                continue  # ключ, а не адрес (например data-tour="vesna" на главной)
            path = unquote(urlsplit(u).path)
            if not path:
                continue
            if path.startswith('/'):
                if not path.startswith(BASE):
                    bad['/' + path.strip('/').split('/')[0] + '/ (без префикса превью)'].add(page)
                    continue
                target = os.path.join(OUT, path[len(BASE):])
            else:
                target = os.path.normpath(os.path.join(os.path.dirname(full), path))
            if path.endswith('/') or os.path.isdir(target):
                target = os.path.join(target, 'index.html')
            if not os.path.exists(target):
                bad[u].add(page)
print(f'Проверено страниц: {n}')
if left:
    print('Не заменены метки общих блоков:', *left[:20], sep='\n  ')
if bad:
    print(f'Битые ссылки ({len(bad)}):')
    for u, pages in sorted(bad.items()):
        print(f'  {u}  ← {len(pages)} стр., напр. {sorted(pages)[0]}')
else:
    print('Битых внутренних ссылок нет')
sys.exit(1 if (bad or left) else 0)
