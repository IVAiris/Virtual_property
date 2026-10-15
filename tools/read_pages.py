"""Дословное чтение страницы-ориентира (распространённость, новости) без архивирования.

Одна страница — одно обращение. Сразу после запуска — строка в журнале через tools/log.py
с фактическим результатом (CLAUDE.md, раздел 4).

Запуск из корня проекта:
    env/venv/bin/python -I tools/read_pages.py "https://…" "ключ1|ключ2"
Выводит строки страницы, содержащие ключевые слова, — дословно, как их показывает браузер.
"""

import re
import sys

from playwright.sync_api import sync_playwright

TIMEOUT = 40_000   # мс на загрузку страницы
SETTLE = 3_000     # мс на отрисовку скриптами

if len(sys.argv) != 3:
    sys.exit(__doc__)
url, keywords = sys.argv[1:]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    response = page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
    page.wait_for_timeout(SETTLE)
    status = response.status if response else "нет ответа"
    text = re.sub(r"[ \t ]+", " ", page.inner_text("body"))
    browser.close()

found = [m.group(0).strip() for m in re.finditer(rf"[^\n]*(?:{keywords})[^\n]*", text, re.I)]
print(f"{url} — статус {status}, {len(text)} символов, строк с ключевыми словами: {len(found)}")
for line in found:
    print("  >", line[:400])
