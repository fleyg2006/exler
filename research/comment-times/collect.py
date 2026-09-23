#!/usr/bin/env python3
"""Read visible public comment threads, retaining author replies and their ancestors.

Targets are the saved six-month feed plus older threads identified in the archive.
No login, posting, rating, moderation, or third-party product links are used.
"""
import argparse, copy, gzip, hashlib, json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag
from lxml import html

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw';RAW.mkdir(exist_ok=True)
RESULTS=ROOT/'threads';RESULTS.mkdir(exist_ok=True)
START='2026-03-23T00:00';END='2026-09-23T00:00'
DATE=re.compile(r'(\d{2}\.\d{2}\.\d{2,4})\s+(\d{2}:\d{2})')

def cls(name):
    return 'contains(concat(" ",normalize-space(@class)," ")," '+name+' ")'
def nodes(el,name):return el.xpath('.//*['+cls(name)+']')
def first(el,name):
    xs=nodes(el,name);return xs[0] if xs else None
def text(el):return ' '.join(el.text_content().split()) if el is not None else ''
def clean_body(el):
    if el is None:return '',[]
    quotes=[text(x) for x in nodes(el,'comments-item-reply')]
    clean=copy.deepcopy(el)
    for x in nodes(clean,'comments-item-reply'):x.drop_tree()
    return text(clean),quotes

def parse(raw,url):
    doc=html.fromstring(raw)
    items=nodes(doc,'comments-item')
    by_anchor={};metadata=[];errors=[]
    for item in items:
        actions=first(item,'blog-item-actions')
        if actions is None:continue
        authors=[a for a in nodes(actions,'profile-link') if 'reply-to' not in a.get('class','').split()]
        link=first(actions,'link-comm');date=first(actions,'blog-item-date')
        if not authors or link is None:
            errors.append('missing attribution/link');continue
        match=DATE.search(text(date))
        if not match:
            errors.append('missing date '+link.get('href',''));continue
        ds,ts=match.groups();fmt='%d.%m.%Y %H:%M' if len(ds)==10 else '%d.%m.%y %H:%M'
        dt=datetime.strptime(ds+' '+ts,fmt).isoformat(timespec='minutes')
        author=authors[0];href=urljoin(url,link.get('href'));anchor=urlsplit(href).fragment
        parent=first(actions,'reply-to')
        record={'anchor':anchor,'url':href,'commented_at':dt,'author':text(author),
                'author_href':urljoin(url,author.get('href','')),
                'owner_mark': 'owner-link' in author.get('class','').split(),
                'author_banned_at_fetch':'banned-link' in author.get('class','').split(),
                'reply_to_anchor':urlsplit(parent.get('href','')).fragment if parent is not None else None,
                'reply_to_author':text(parent) if parent is not None else None,
                'reply_to_banned_at_fetch':('banned-link' in parent.get('class','').split()) if parent is not None else None}
        by_anchor[anchor]=(item,record);metadata.append(record)
    kept=[]
    def complete(anchor):
        item,record=by_anchor[anchor];r=dict(record)
        body=first(item,'comments-text');r['own_text'],r['quoted_text']=clean_body(body)
        r['own_text_sha256']=hashlib.sha256(r['own_text'].encode()).hexdigest()
        return r
    for m in metadata:
        if m['author']!='Alex Exler' or not START<=m['commented_at']<END:continue
        r=complete(m['anchor']);parents=[];p=m['reply_to_anchor'];seen={m['anchor']}
        while p and p in by_anchor and p not in seen and len(parents)<5:
            seen.add(p);par=complete(p);parents.append(par);p=par['reply_to_anchor']
        r['context']=parents;r['parent_present']=not m['reply_to_anchor'] or m['reply_to_anchor'] in by_anchor
        kept.append(r)
    header=first(doc,'comments-header-title')
    match=re.search(r'(\d[\d\s]*)$',text(header));declared=int(re.sub(r'\s','',match.group(1))) if match else None
    containers=nodes(doc,'comments-list')
    pagination=[]
    for container in containers:
        for a in container.xpath('.//a[@href]'):
            # A malformed URL pasted by a reader is not a pagination link.
            try:u=urldefrag(urljoin(url,a.get('href')))[0]
            except ValueError:continue
            if 'page=' in urlsplit(u).query and urlsplit(u).netloc=='exler.es' and u not in pagination:pagination.append(u)
    return {'title':text(doc.find('.//title')),'declared_comments':declared,
            'visible_items':len(items),'parsed_items':len(metadata),'parse_errors':errors,
            'all_visible_alex':sum(m['author']=='Alex Exler' for m in metadata),
            'alex_in_period':len(kept),'comments':kept,'pagination':pagination,
            'comment_time_min':min((m['commented_at'] for m in metadata),default=None),
            'comment_time_max':max((m['commented_at'] for m in metadata),default=None)}

def fetch(target,retry=False):
    url=target['url'];key=hashlib.sha256(url.encode()).hexdigest()[:20]
    rp=RESULTS/(key+'.json');hp=RAW/(key+'.html.gz');mp=RAW/(key+'.meta.json')
    if rp.exists():
        old=json.loads(rp.read_text())
        if 'error' not in old or not retry:return old
    try:
        if hp.exists() and mp.exists():
            raw=gzip.decompress(hp.read_bytes());meta=json.loads(mp.read_text())
        else:
            started=time.monotonic()
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(request,timeout=30) as response:
                raw=response.read();final=response.url;status=response.status
            meta={'url':url,'final_url':final,'status':status,'bytes':len(raw),
                'fetched_at':datetime.now(timezone.utc).isoformat(),
                'sha256':hashlib.sha256(raw).hexdigest(),'seconds':round(time.monotonic()-started,3)}
            hp.write_bytes(gzip.compress(raw));mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        result={'target':target,'source':meta,**parse(raw,url)}
    except Exception as exc:
        result={'target':target,'error':str(exc),'error_type':type(exc).__name__}
    rp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=10)
    ap.add_argument('--limit',type=int);ap.add_argument('--retry',action='store_true');args=ap.parse_args()
    targets=[{k:r[k] for k in ['url','title','published_at','scope']} for r in map(json.loads,(ROOT/'threads.jsonl').read_text().splitlines())]
    # Newest threads first to resolve the archive's missing months early.
    leads=ROOT/'archive-reaction-leads.json'
    priority={r['post_url'] for r in json.loads(leads.read_text())} if leads.exists() else set()
    targets.sort(key=lambda t:(t['url'] in priority,t['published_at']),reverse=True)
    if args.limit:targets=targets[:args.limit]
    started=time.monotonic();done=errors=comments=0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(fetch,t,args.retry):t for t in targets}
        for f in as_completed(jobs):
            r=f.result();done+=1;errors+=int('error' in r);comments+=r.get('alex_in_period',0)
            if 'error' in r:print(json.dumps({'ERROR':r},ensure_ascii=False),flush=True)
            if done%25==0 or done==len(targets):
                print(json.dumps({'done':done,'total':len(targets),'errors':errors,'alex_comments':comments,
                   'minutes':round((time.monotonic()-started)/60,2),'latest_done':r['target']['published_at']},ensure_ascii=False),flush=True)
    print('COLLECTION COMPLETE',flush=True)

if __name__=='__main__':main()
