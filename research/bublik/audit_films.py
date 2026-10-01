"""Recount the Bublik film manifest; optionally verify saved or freshly fetched HTML.

Default: no network, standard library only. HTML verification: beautifulsoup4.
Downloaded copyrighted source pages remain in the explicitly selected local cache.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


def sha(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def summarize(rows):
    selected = [r for r in rows if r['corpus'] == 'database_films_468']
    signatures = [s for r in selected for s in r['bublik_attribution_labels']]
    return {
        'database_pages': len(selected),
        'strict_attribution_pages': sum(bool(r['bublik_attribution_labels']) for r in selected),
        'including_verified_typo_pages': sum(bool(r['bublik_attribution_labels']) or bool(r['manually_verified_variant']) for r in selected),
        'body_mention_pages': sum(r['bublik_body_stem_occurrences'] > 0 for r in selected),
        'strict_signature_occurrences': len(signatures),
        'strict_signature_variants': len(set(signatures)),
        'by_year': dict(sorted(Counter(r['date'][6:10] for r in selected).items())),
    }


def verify(row, cache, refresh):
    from bs4 import BeautifulSoup

    url = row['url']
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or parts.netloc != 'exler.es' or not parts.path.startswith('/films/'):
        raise ValueError('Manifest URL is outside the film-source allowlist: ' + url)
    target = cache / (sha(url)[:20] + '.html')
    if refresh:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.netloc not in {'exler.es', 'www.exler.es'}:
                raise ValueError('Unexpected source redirect: ' + response.geturl())
            raw = response.read()
        target.write_bytes(raw)
    else:
        raw = target.read_bytes()
    soup = BeautifulSoup(raw, 'html.parser')
    body = soup.select_one('.film-item-content')
    if body is None:
        raise ValueError('Missing article container: ' + url)
    body_text = body.get_text(' ', strip=True)
    labels = [e.get_text(' ', strip=True) for e in soup.select('.post-section .film-review-text i, .post-section .film-review-text em')
              if re.search('бублик', e.get_text(' ', strip=True), re.I)]
    variant = None
    if row['manually_verified_variant']:
        literal = row['manually_verified_variant']['literal_label']
        if literal in [e.get_text(' ', strip=True) for e in soup.select('.post-section .film-review-text i, .post-section .film-review-text em')]:
            variant = row['manually_verified_variant']
    result = dict(row,
        bublik_attribution_labels=labels,
        bublik_body_stem_occurrences=len(re.findall('бублик', body_text, re.I)),
        manually_verified_variant=variant,
        html_sha256=sha(raw), body_sha256=sha(body_text))
    changed = [field for field in ['bublik_attribution_labels', 'bublik_body_stem_occurrences', 'manually_verified_variant', 'html_sha256', 'body_sha256']
               if result[field] != row[field]]
    return result, {'url': url, 'changed_fields': changed} if changed else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('film-corpus-audit.json'))
    parser.add_argument('--html-cache', type=Path)
    parser.add_argument('--refresh', action='store_true', help='Fetch the manifest URLs into the explicit cache directory')
    args = parser.parse_args()
    if args.refresh and not args.html_cache:
        parser.error('--refresh requires --html-cache')
    manifest = json.loads(args.manifest.read_text())
    rows = manifest['rows']
    output = {'manifest_counts': summarize(rows)}
    if args.html_cache:
        args.html_cache.mkdir(parents=True, exist_ok=True)

        def task(row):
            try:
                return verify(row, args.html_cache, args.refresh)
            except Exception as error:
                return None, {'url': row['url'], 'error': type(error).__name__ + ': ' + str(error)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(task, rows))
        parsed = [row for row, _ in results if row is not None]
        output.update(checked_pages=len(parsed), observed_counts=summarize(parsed),
                      changes_or_errors=[item for _, item in results if item])
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
