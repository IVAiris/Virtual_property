"""Добавить строку в research/SEARCH_LOG.md (перед разделом «Протокол отсутствия находок»).

Запуск из корня проекта:
    env/venv/bin/python -I tools/log.py S-58 "база или сайт" "точный запрос" "период" "результат" "связанные ID" "следующее действие"
Дата ставится автоматически, исполнитель — «IA (EDI)». Номер S-… не должен повторяться.
"""

import datetime
import pathlib
import sys

LOG = pathlib.Path(__file__).resolve().parent.parent / "research" / "SEARCH_LOG.md"
SECTION = "\n## Протокол отсутствия находок"

if len(sys.argv) != 8:
    sys.exit(__doc__)
fields = [f.replace("|", "\\|") for f in sys.argv[1:]]   # «|» внутри текста ломает таблицу
sid = fields[0]

text = LOG.read_text(encoding="utf-8")
if f"| {sid} |" in text:
    sys.exit(f"{sid} уже есть в журнале — запись не добавлена")
head, tail = text.split(SECTION, 1)
date = datetime.date.today().strftime("%d.%m.%Y")
row = f"| {sid} | {date} | IA (EDI) | " + " | ".join(fields[1:]) + " |"
LOG.write_text(head.rstrip("\n") + "\n" + row + "\n" + SECTION + tail, encoding="utf-8")
print("записано:", sid)
