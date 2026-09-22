"""Separate attributed comment text from quoted readers in public HTML."""
import copy, hashlib, json, pathlib, urllib.parse
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent

def parse(path, url):
    soup = BeautifulSoup(pathlib.Path(path).read_bytes(), 'html.parser')
    out = []
    for item in soup.select('.comments-item'):
        body = item.select_one('.comments-item-title.comments-text')
        actions = item.select_one('.blog-item-actions')
        if not body or not actions:
            continue
        link = actions.select_one('a.link-comm')
        author = next((a for a in actions.select('a.profile-link') if 'reply-to' not in a.get('class', [])), None)
        if not link or not author:
            continue
        clean = copy.deepcopy(body)
        quotes = [e.get_text('\n', strip=True) for e in clean.select('.comments-item-reply')]
        for e in clean.select('.comments-item-reply'):
            e.decompose()
        parent = actions.select_one('a.reply-to')
        href = urllib.parse.urljoin(url, link['href'])
        out.append({
            'anchor': urllib.parse.urlsplit(href).fragment,
            'url': href,
            'author': author.get_text(' ', strip=True),
            'author_banned_at_fetch': 'banned-link' in author.get('class', []),
            'reply_to_anchor': (parent.get('href', '').split('#')[-1] if parent else None),
            'reply_to_author': parent.get_text(' ', strip=True) if parent else None,
            'reply_to_banned_at_fetch': ('banned-link' in parent.get('class', []) if parent else None),
            'own_text': clean.get_text('\n', strip=True),
            'quoted_text': quotes,
            'links': [urllib.parse.urljoin(url, a['href']) for a in clean.select('a[href]')],
            'actions_text': actions.get_text(' ', strip=True),
        })
    return out

