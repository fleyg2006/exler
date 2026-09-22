"""Check attribution, parent links and text hashes for the selected public comments.

Requires beautifulsoup4. Example:
    python verify_sources.py --cache-dir /path/to/raw
    python verify_sources.py --cache-dir ./raw --download

This does not establish the fairness or technical execution of a ban.
"""
import argparse
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

from parse_exler import parse


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache-dir', required=True, type=pathlib.Path)
    cli.add_argument('--download', action='store_true')
    args = cli.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    data = json.loads((root/'cases.json').read_text())
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    errors, checked, warnings = [], 0, []
    for case in data['cases']:
        url = case['page_url']
        if urllib.parse.urlsplit(url).hostname != 'exler.es':
            raise ValueError('Unexpected source host')
        path = args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
        if not path.exists() and args.download:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                if urllib.parse.urlsplit(response.geturl()).hostname != 'exler.es':
                    raise ValueError('Unexpected redirect host')
                path.write_bytes(response.read())
        if not path.exists():
            errors.append({'case':case['id'], 'error':'missing cached page'})
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != case['page_sha256']:
            warnings.append({'case':case['id'], 'warning':'whole page changed; checking comment text'})
        rows = {c['anchor']:c for c in parse(path, url)}
        for expected in case['comments']:
            actual = rows.get(expected['anchor'])
            if actual is None:
                errors.append({'case':case['id'], 'anchor':expected['anchor'], 'error':'missing comment'})
                continue
            matches = (actual['author']==expected['author'] and
                       actual['reply_to_anchor']==expected['parent_anchor'] and
                       hashlib.sha256(actual['own_text'].encode()).hexdigest()==expected['body_sha256'])
            if not matches:
                errors.append({'case':case['id'], 'anchor':expected['anchor'], 'error':'attribution, parent or text changed'})
            checked += 1
    print(json.dumps({'checked_comments':checked, 'cases':len(data['cases']),
                      'errors':errors, 'warnings':warnings}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
