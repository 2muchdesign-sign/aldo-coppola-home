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

# _site → gh-pages. Постоянная копия ветки в .cache/gh-pages: сборка кладётся поверх прошлой,
# на GitHub уходят только изменения (полная заливка 200+ МБ упирается в таймаут GitHub)
GIT=(git -c http.postBuffer=524288000 -c credential.helper= -c credential.helper='!gh auth git-credential')
GP=.cache/gh-pages
if [[ ! -d $GP/.git ]]; then
  "${GIT[@]}" clone --depth 1 -b gh-pages "https://github.com/$REPO.git" $GP
else
  (cd $GP && "${GIT[@]}" fetch -q --depth 1 origin gh-pages && git reset -q --hard FETCH_HEAD)
fi
rsync -a --delete --exclude .git _site/ $GP/
cd $GP
git add -A
if git diff --cached --quiet; then
  echo "gh-pages: изменений нет"
else
  git commit -qm "Сборка сайта $(date '+%d.%m.%Y %H:%M')"
  "${GIT[@]}" push origin gh-pages
fi
cd - >/dev/null

# Pages: источник — ветка gh-pages, корень
SRC=$(gh api "repos/$REPO/pages" --jq '.source.branch' 2>/dev/null || echo none)
if [[ "$SRC" != "gh-pages" ]]; then
  gh api -X PUT "repos/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null
  gh api -X POST "repos/$REPO/pages/builds" >/dev/null   # после смены источника сборка сама не запускается
  echo "Pages переключены на ветку gh-pages"
fi
echo "Опубликовано: https://2muchdesign-sign.github.io/aldo-coppola-home/"
