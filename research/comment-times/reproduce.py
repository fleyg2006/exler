#!/usr/bin/env python3
"""Recompute numerical findings from public metadata and saved human labels."""
import argparse,json
from pathlib import Path
from datetime import datetime,date,timedelta
from collections import defaultdict
from statistics import median
import numpy as np
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--publications',type=Path,default=ROOT.parent/'publication-times/publications.json');args=ap.parse_args()
    comments=[json.loads(x) for x in (ROOT/'observations.jsonl').read_text().splitlines()]
    threads=[json.loads(x) for x in (ROOT/'threads.jsonl').read_text().splitlines()]
    posts=json.loads(args.publications.read_text());comments.sort(key=lambda x:(x['time'],x['url']))
    assert len({c['url'] for c in comments})==len(comments)
    assert len({t['id'] for t in threads})==len(threads)==1125
    assert all(c['thread'] in {t['id'] for t in threads} for c in comments)
    live=[c for c in comments if c['origin']=='live_html'];assert all(c['severity'] in (0,1,2) for c in live)
    assert all(c['severity'] is None for c in comments if c['origin']!='live_html')
    byday=defaultdict(list);postday=defaultdict(list)
    for c in comments:byday[c['time'][:10]].append(c)
    for p in sorted(posts,key=lambda p:p['published_at']):postday[p['date']].append(p)
    def minute(v):return int(v[11:13])*60+int(v[14:16])
    tails=[];daily=[]
    for i in range(184):
        d=(date(2026,3,23)+timedelta(days=i)).isoformat();cs=byday[d];ps=postday[d]
        later=[p for p in ps if cs and p['published_at']>cs[-1]['time']]
        if later:tails.append((d,later,minute(ps[-1]['published_at'])-minute(cs[-1]['time'])))
        daily.append({'date':d,'last_reply':minute(cs[-1]['time']) if cs else None,'last_post':minute(ps[-1]['published_at'])})
    sensitivities=[];returns=[]
    for threshold in [120,180,240]:
        found=[]
        for a,b in zip(comments,comments[1:]):
            if a['time'][:10]!=b['time'][:10] or int(b['time'][11:13])<18:continue
            gap=(datetime.fromisoformat(b['time'])-datetime.fromisoformat(a['time'])).total_seconds()/60
            if gap>=threshold:found.append((a,b,gap))
        sensitivities.append({'gap_hours':threshold//60,'events':len(found),'days':len({b['time'][:10] for a,b,g in found})})
        if threshold==180:returns=found
    bands=[]
    for lo,hi in [(0,8),(8,12),(12,18),(18,24)]:
        group=[c for c in live if lo<=int(c['time'][11:13])<hi]
        bands.append({'n':len(group),'broad':sum(c['severity']>0 for c in group),'strict':sum(c['severity']==2 for c in group)})
    observed=sorted({c['time'][:10] for c in comments});mat=[]
    for d in observed:
        row=[]
        for lo,hi in [(8,18),(18,24)]:
            group=[c for c in live if c['time'][:10]==d and lo<=int(c['time'][11:13])<hi]
            row.extend([len(group),sum(c['severity']>0 for c in group),sum(c['severity']==2 for c in group)])
        mat.append(row)
    mat=np.asarray(mat);rng=np.random.default_rng(20260923)
    boot=mat[rng.integers(0,len(mat),size=(20000,len(mat)))].sum(axis=1)
    boot=boot[(boot[:,0]>0)&(boot[:,3]>0)]
    ci={k:np.quantile(100*(boot[:,j+3]/boot[:,3]-boot[:,j]/boot[:,0]),[.025,.975]).tolist() for k,j in [('broad',1),('strict',2)]}
    med=round(median(d['last_reply'] for d in daily if d['last_reply'] is not None))
    result={'comments_total':len(comments),'live_comments':len(live),'days_with_comments':len(observed),
      'last_reply_median':f'{med//60:02d}:{med%60:02d}',
      'days_with_publication_tail':len(tails),'publications_in_tails':sum(len(ps) for d,ps,g in tails),
      'grid_publications_in_tails':sum(int(p['published_at'][14:16])%10==0 for d,ps,g in tails for p in ps),
      'tail_median_minutes':median(g for d,ps,g in tails),'return_sensitivity':sensitivities,
      'replies_after_last_post_days':sum(d['last_reply'] is not None and d['last_reply']>d['last_post'] for d in daily),
      'bands':bands,'bootstrap_95':ci,'sharp_first_return':sum((b['severity'] or 0)>0 for a,b,g in returns),
      'strict_first_return':sum(b['severity']==2 for a,b,g in returns)}
    saved=json.loads((ROOT/'summary.json').read_text());reactions=json.loads((ROOT/'reactions-summary.json').read_text())
    for k in result:
        if k in saved:assert result[k]==saved[k],(k,result[k],saved[k])
    for found,expected in zip(bands,reactions['bands']):
        for k in found:assert found[k]==expected[k]
    assert ci==reactions['day_cluster_bootstrap']['percentile_95']
    print(json.dumps(result,ensure_ascii=False,indent=2));print('Verified against saved summaries.')
if __name__=='__main__':main()
