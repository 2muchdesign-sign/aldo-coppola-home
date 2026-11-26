# Сайт Aldo Coppola — финальная версия

Превью: https://2muchdesign-sign.github.io/aldo-coppola-home/ (закрыто от индексации).
Боевой адрес после переноса подрядчиками на Битрикс: https://aldocoppola.ru/

## Как устроено

| Папка | Что |
| --- | --- |
| `src/` | страницы сайта: у каждой свой `<head>` и содержимое; медиа рядом со страницей |
| `src/_ac/` | дизайн-система: `tokens.css` (цвета, шрифты, размеры), `site.css`/`site.js` (шапка и подвал), `pages.css` (информационные страницы), `align.css` (приводит ранние разделы к общей палитре) |
| `src/dizayn-sistema/` | справочник дизайн-системы с живыми примерами (закрыт от поисковиков) |
| `_build/data/`, `_build/content/` | данные и тексты: салоны, специалисты, услуги, акции, правовые страницы, новости |
| `src/stati/_src/` | исходники статей в Markdown; страницы раздела собирает `_build/stati.py` |
| `_build/build.py` | сборщик: меню и подвал (`NAV`, `FOOTER`), заглушки разделов, переадресации, sitemap, robots, llms.txt |
| `_build/check.py` | проверка собранного сайта: битые ссылки, незаменённые метки |
| `_build/publish.sh` | сборка + публикация превью (исходники → `main`, сайт → `gh-pages`) |
| `../aldo-coppola-cosmetology` | раздел «Косметология» (Astro), встраивается в `/kosmetologiya/` |

Метки в страницах: `<!--#site-head-->` (общие подключения), `<!--#site-header-->` (шапка), `<!--#site-footer-->` (подвал).
В Битриксе они соответствуют `header.php` / `footer.php` шаблона сайта.

```bash
python3 _build/build.py            # превью: адреса от /aldo-coppola-home/
python3 _build/build.py --prod     # для aldocoppola.ru: адреса от корня, индексация открыта
python3 _build/check.py
zsh _build/publish.sh              # опубликовать превью
```

Карта сайта и таблица редиректов: `../aldo-coppola-redesign/karta-saita.html`, `redirects.csv` (копия в репозитории).
