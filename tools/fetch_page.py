"""Сохранение страницы источника в архив sources/<ID>/ (spec.md §5.3).

Два режима:
    fetch   — одно обращение к сайту через Playwright (Chromium), сохраняет page.html и meta.txt;
    extract — без сети: из сохранённого page.html собирает text.md (метаданные + текст).

Запуск из корня проекта:
    env/venv/bin/python -I tools/fetch_page.py fetch N-01 <URL>
    env/venv/bin/python -I tools/fetch_page.py extract N-01 [--selector "CSS"] [--drop "CSS"]

Для открытых страниц КонсультантПлюс:
    --selector "div.document-page__title-link, div.document-page__content"
    --drop "div.note-external, div.doc-insert, div.info-link"
"""

import argparse
import datetime
import pathlib
import sys

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SOURCES = pathlib.Path(__file__).resolve().parent.parent / "sources"
TIMEOUT = 40_000   # мс на загрузку страницы


def fetch(source_id, url):
    """Одно обращение к сайту: HTML после отрисовки скриптами + URL и дата обращения."""
    folder = SOURCES / source_id
    html_path = folder / "page.html"
    if html_path.exists():
        sys.exit(f"{html_path} уже есть — повторное обращение не выполняется. "
                 "Чтобы сохранить новую версию, переименуйте старую с датой.")
    folder.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        response = page.goto(url, timeout=TIMEOUT, wait_until="networkidle")
        status = response.status if response else "нет ответа"
        html = page.content()
        browser.close()

    html_path.write_text(html, encoding="utf-8")
    accessed = datetime.date.today().isoformat()
    (folder / "meta.txt").write_text(f"url: {url}\naccessed: {accessed}\nstatus: {status}\n", encoding="utf-8")
    print(f"{source_id}: статус {status}, {len(html)} символов HTML → {html_path}")


INLINE = ["a", "span", "b", "i", "em", "strong", "sup", "sub", "nobr"]


def extract(source_id, selector, drop):
    """Без сети: текст из page.html (весь body или блоки по CSS-селектору) → text.md.

    drop — CSS-селекторы блоков, которые выбрасываются (навигация, реклама сайта).
    Встроенные теги (ссылки и т.п.) склеиваются с соседним текстом, чтобы ссылка
    внутри фразы не разрывала её на строки.
    """
    folder = SOURCES / source_id
    soup = BeautifulSoup((folder / "page.html").read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    if drop:
        for tag in soup.select(drop):
            tag.decompose()
    for tag in soup.find_all(INLINE):
        tag.unwrap()
    soup.smooth()

    nodes = soup.select(selector) if selector else [soup.body]
    if not nodes:
        sys.exit(f"селектор {selector!r} ничего не нашёл")

    lines = [line.strip() for node in nodes for line in node.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line)

    meta = dict(line.split(": ", 1) for line in (folder / "meta.txt").read_text(encoding="utf-8").splitlines())
    title = soup.title.get_text(strip=True) if soup.title else ""
    header = (f"# {source_id}: {title}\n\n"
              f"- URL: {meta['url']}\n"
              f"- Дата обращения: {meta['accessed']}\n"
              f"- Извлечено из: page.html{f' (селектор `{selector}`)' if selector else ''}"
              f"{f'; исключено: `{drop}`' if drop else ''}\n\n---\n\n")
    (folder / "text.md").write_text(header + text + "\n", encoding="utf-8")
    print(f"{source_id}: {len(text)} символов текста → {folder / 'text.md'}")


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("mode", choices=["fetch", "extract"])
parser.add_argument("source_id")
parser.add_argument("url", nargs="?")
parser.add_argument("--selector", help="CSS-селекторы блоков с текстом (через запятую)")
parser.add_argument("--drop", help="CSS-селекторы блоков, которые выбросить (через запятую)")
args = parser.parse_args()

if args.mode == "fetch":
    if not args.url:
        sys.exit("для fetch нужен URL")
    fetch(args.source_id, args.url)
else:
    extract(args.source_id, args.selector, args.drop)
