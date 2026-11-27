#!/bin/zsh
# Публикация превью на GitHub Pages (та же ссылка https://2muchdesign-sign.github.io/aldo-coppola-home/).
# Исходники — ветка main, собранный сайт _site/ — ветка gh-pages (из неё Pages и показывает сайт).
# Запуск из корня репозитория:  zsh _build/publish.sh [--skip-kosm]
set -e
export PATH="$HOME/bin:$HOME/.local/node/bin:$PATH"
cd "$(dirname "$0")/.."
REPO=2muchdesign-sign/aldo-coppola-home

python3 _build/build.py "$@"
python3 _build/check.py

git -c http.postBuffer=524288000 -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main

# _site → gh-pages: поверх прошлой сборки, чтобы отправлялись только изменения (полная заливка упирается в таймаут GitHub)
GIT=(git -c http.postBuffer=524288000 -c credential.helper= -c credential.helper='!gh auth git-credential')
TMP=$(mktemp -d)
cd "$TMP"
git init -q
git remote add origin "https://github.com/$REPO.git"
if "${GIT[@]}" fetch -q --depth 1 origin gh-pages 2>/dev/null; then
  git checkout -q -b gh-pages FETCH_HEAD
else
  git checkout -q -b gh-pages
fi
cd - >/dev/null
rsync -a --delete --exclude .git _site/ "$TMP/"
cd "$TMP"
git add -A
if git diff --cached --quiet; then
  echo "gh-pages: изменений нет"
else
  git commit -qm "Сборка сайта $(date '+%d.%m.%Y %H:%M')"
  "${GIT[@]}" push origin gh-pages
fi
cd - >/dev/null
rm -rf "$TMP"

# Pages: источник — ветка gh-pages, корень
SRC=$(gh api "repos/$REPO/pages" --jq '.source.branch' 2>/dev/null || echo none)
if [[ "$SRC" != "gh-pages" ]]; then
  gh api -X PUT "repos/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null
  gh api -X POST "repos/$REPO/pages/builds" >/dev/null   # после смены источника сборка сама не запускается
  echo "Pages переключены на ветку gh-pages"
fi
echo "Опубликовано: https://2muchdesign-sign.github.io/aldo-coppola-home/"
