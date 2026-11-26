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

# _site → gh-pages (отдельная история, только собранный сайт)
TMP=$(mktemp -d)
rsync -a _site/ "$TMP/"
cd "$TMP"
git init -q -b gh-pages
git add -A
git commit -qm "Сборка сайта $(date '+%d.%m.%Y %H:%M')"
git remote add origin "https://github.com/$REPO.git"
git -c http.postBuffer=524288000 -c credential.helper= -c credential.helper='!gh auth git-credential' push -f origin gh-pages
cd - >/dev/null
rm -rf "$TMP"

# Pages: источник — ветка gh-pages, корень
SRC=$(gh api "repos/$REPO/pages" --jq '.source.branch' 2>/dev/null || echo none)
if [[ "$SRC" != "gh-pages" ]]; then
  gh api -X PUT "repos/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null
  echo "Pages переключены на ветку gh-pages"
fi
echo "Опубликовано: https://2muchdesign-sign.github.io/aldo-coppola-home/"
