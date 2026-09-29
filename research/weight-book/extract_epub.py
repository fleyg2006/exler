"""Локально извлечь нумерованные блоки официального EPUB для проверки ссылок P.

Требование: beautifulsoup4. Полный текст не предназначен для коммита в репозиторий.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("epub", type=Path)
parser.add_argument("--out", required=True, type=Path)
args = parser.parse_args()
raw = args.epub.read_bytes()
rows = []
chapter = 0
block = 0
with ZipFile(args.epub) as archive:
    for name in sorted(n for n in archive.namelist() if n.startswith("index_split_")):
        soup = BeautifulSoup(archive.read(name), "html.parser")
        for element in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = element.get_text(" ", strip=True)
            if not text:
                continue
            if element.name == "h1":
                chapter += 1
                block = 0
            block += 1
            rows.append({"n": len(rows) + 1, "file": name,
                         "chapter": chapter, "chapter_block": block,
                         "tag": element.name, "text": text,
                         "sha256": hashlib.sha256(text.encode()).hexdigest()})
args.out.mkdir(parents=True, exist_ok=True)
(args.out / "paragraphs.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(args.out / "numbered.txt").write_text(
    "\n".join(f"P{r['n']:04d} {r['text']}" for r in rows) + "\n", encoding="utf-8")
print(json.dumps({"epub_sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw), "chapters": chapter, "blocks": len(rows),
                  "characters": sum(len(r["text"]) for r in rows)}, indent=2))
