import json, os, pathlib, urllib.request, urllib.parse, concurrent.futures, time

root = pathlib.Path(__file__).parent
posts = json.loads((root / 'exler-products-page1.json').read_text())['posts']
posts.sort(key=lambda p: int(p['id']))
cache = root / 'html_batches'
cache.mkdir(exist_ok=True)

def fetch(start):
    path = cache / ('batch-%03d.json' % start)
    if path.exists():
        try:
            d = json.loads(path.read_text())
            if d.get('ok') and len(d['posts']) == len(posts[start:start+5]):
                return start, len(d['posts'])
        except Exception:
            pass
    params = dict(action='posts', q='Делимся находками', limit=5, include_html=1)
    if start:
        params['after_id'] = posts[start-1]['id']
    request = urllib.request.Request('https://exler.tech/exler_archive_gateway.php?' + urllib.parse.urlencode(params), headers={'X-API-Key': os.environ['EXLER_API_TOKEN']})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            d = json.loads(data)
            assert d.get('ok') and [p['id'] for p in d['posts']] == [p['id'] for p in posts[start:start+5]]
            path.write_bytes(data)
            return start, len(d['posts'])
        except Exception as e:
            if attempt == 2:
                raise RuntimeError('Batch %s: %s' % (start, e))
    return start, 0

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for start, count in pool.map(fetch, range(0, len(posts), 5)):
        print('Downloaded', start, count, flush=True)
