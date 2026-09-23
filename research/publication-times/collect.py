#!/usr/bin/env python3
"""Collect publication labels from Exler's unfiltered blog feed; no article bodies.

Usage: python collect.py --pages 1 24 --workers 4
Dependencies: beautifulsoup4. Raw responses and hashes are cached beside this file.
No AliExpress or linked third-party URLs are followed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
RAW.mkdir(exist_ok=True)
DATE_RE = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})')

def get_page(page, force=False):
    url = f'https://exler.es/blog/?page={page}&per-page=50'
    path = RAW / f'list-{page:03d}.html'
    meta_path = path.with_suffix('.meta.json')
    if force or not path.exists():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            raw = response.read()
            meta = {'page': page, 'url': url, 'final_url': response.url,
                    'status': response.status,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'sha256': hashlib.sha256(raw).hexdigest()}
        path.write_bytes(raw)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    raw = path.read_bytes()
    meta = json.loads(meta_path.read_text())
    soup = BeautifulSoup(raw, 'html.parser')
    items, errors = [], []
    for i, entry in enumerate(soup.select('.blog-item')):
        title = entry.select_one('.blog-item-title')
        anchor = title if title and title.name == 'a' else title.select_one('a') if title else None
        date = entry.select_one('.blog-item-date')
        match = DATE_RE.search(date.get_text(' ', strip=True)) if date else None
        if not anchor or not match:
            errors.append({'item': i, 'reason': 'missing title URL or date/time'})
            continue
        dt = datetime.strptime(' '.join(match.groups()), '%d.%m.%Y %H:%M')
        items.append({'url': urldefrag(urljoin(url, anchor['href']))[0],
                      'title': title.get_text(' ', strip=True),
                      'published_at': dt.isoformat(timespec='minutes'),
                      'displayed_at': ' '.join(match.groups()),
                      'source_page': page})
    if not items:
        raise ValueError(f'Page {page}: no publication labels')
    meta.update({'page': page, 'items': len(items), 'parse_errors': errors,
                 'newest': max(x['published_at'] for x in items),
                 'oldest': min(x['published_at'] for x in items)})
    return {'meta': meta, 'items': items}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, nargs=2, default=[1,24])
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_pages = {pool.submit(get_page, p): p for p in range(args.pages[0],args.pages[1]+1)}
        for f in as_completed(future_pages):
            p = future_pages[f]
            try:
                r = f.result(); results.append(r)
                print(json.dumps(r['meta'], ensure_ascii=False), flush=True)
            except Exception as e:
                failures.append({'page':p,'error':str(e)})
                print(json.dumps(failures[-1]), flush=True)
    results.sort(key=lambda x: x['meta']['page'])
    (ROOT / 'pages.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    (ROOT / 'fetch-failures.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2))
    print('FINISHED', len(results), 'pages;', len(failures), 'failures', flush=True)

if __name__ == '__main__':
    main()
