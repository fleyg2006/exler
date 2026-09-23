#!/usr/bin/env python3
"""Reproduce publication-time aggregates from collected feed labels."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from statistics import median, mean
import numpy as np

ROOT = Path(__file__).resolve().parent
START, END = date(2026, 3, 23), date(2026, 9, 23)  # END is exclusive: today is incomplete.
WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def clock(value):
    v = int(round(value))
    return f'{v//60:02d}:{v%60:02d}'

def main():
    pages = json.loads((ROOT/'pages.json').read_text())
    assert pages and all(not p['meta']['parse_errors'] for p in pages)
    assert [p['meta']['page'] for p in pages] == list(range(1, len(pages)+1))
    all_rows = [i for p in pages for i in p['items']]
    assert all(a['published_at'] >= b['published_at'] for a,b in zip(all_rows, all_rows[1:])), 'feed not ordered'
    unique = {}
    for row in all_rows:
        unique.setdefault((row['published_at'], row['url']), row)
    rows = sorted((dict(r) for r in unique.values() if START <= datetime.fromisoformat(r['published_at']).date() < END), key=lambda r:(r['published_at'],r['url']))
    assert datetime.fromisoformat(min(r['published_at'] for r in all_rows)).date() < START
    days = [START + timedelta(days=i) for i in range((END-START).days)]
    by_day = defaultdict(list)
    for r in rows:
        dt = datetime.fromisoformat(r['published_at'])
        r.update({'date':dt.date().isoformat(),'weekday':dt.weekday(),'hour':dt.hour,'minute':dt.minute,'minute_of_day':dt.hour*60+dt.minute})
        by_day[r['date']].append(r)
    daily = []
    for day in days:
        values = by_day[day.isoformat()]
        mins = [r['minute_of_day'] for r in values]
        daily.append({'date':day.isoformat(),'weekday':day.weekday(),'posts':len(values),
            'first_minute':min(mins) if mins else None,'last_minute':max(mins) if mins else None,
            'first':clock(min(mins)) if mins else None,'last':clock(max(mins)) if mins else None,
            'span_minutes':max(mins)-min(mins) if mins else None})
    hourly = [{'hour':h, 'posts':sum(r['hour']==h for r in rows)} for h in range(24)]
    weekday = []
    for w in range(7):
        ds = [d for d in daily if d['weekday']==w]
        active = [d for d in ds if d['posts']]
        rs = [r for r in rows if r['weekday']==w]
        weekday.append({'weekday':w,'label':WEEKDAYS[w], 'calendar_days':len(ds),'active_days':len(active),
            'posts':len(rs),'posts_per_day':len(rs)/len(ds),
            'first_median_minute':median([d['first_minute'] for d in active]),
            'last_median_minute':median([d['last_minute'] for d in active]),
            'last_median':clock(median([d['last_minute'] for d in active])),
            'hourly_counts':[sum(r['hour']==h for r in rs) for h in range(24)]})
    monthly = []
    for m in sorted({d['date'][:7] for d in daily}):
        ds=[d for d in daily if d['date'].startswith(m)]
        rs=[r for r in rows if r['date'].startswith(m)]
        active=[d for d in ds if d['posts']]
        monthly.append({'month':m,'calendar_days':len(ds),'active_days':len(active),'posts':len(rs),
            'posts_per_day':len(rs)/len(ds),'median_post_minute':median(r['minute_of_day'] for r in rs),
            'median_first_minute':median(d['first_minute'] for d in active),
            'median_last_minute':median(d['last_minute'] for d in active),
            'before_12_share':sum(r['minute_of_day']<720 for r in rs)/len(rs),
            'at_or_after_18_share':sum(r['minute_of_day']>=1080 for r in rs)/len(rs)})
    active=[d for d in daily if d['posts']]
    complete_weeks=[]
    for d in days:
        if d.weekday()==0 and d+timedelta(days=6)<END:
            ds=[x for x in daily if d.isoformat()<=x['date']<=(d+timedelta(days=6)).isoformat()]
            complete_weeks.append({'start':d.isoformat(),'posts':sum(x['posts'] for x in ds)})
    gaps=[]
    for a,b in zip(rows,rows[1:]):
        gap=(datetime.fromisoformat(b['published_at'])-datetime.fromisoformat(a['published_at'])).total_seconds()/3600
        gaps.append({'hours':gap,'from':{k:a[k] for k in ('published_at','url','title')},'to':{k:b[k] for k in ('published_at','url','title')}})
    gaps.sort(key=lambda x:-x['hours'])
    groups={}
    for name,condition in [('weekdays',lambda w:w<5),('weekends',lambda w:w>=5)]:
        ds=[d for d in daily if condition(d['weekday'])]
        ac=[d for d in ds if d['posts']]
        groups[name]={'days':len(ds),'posts':sum(d['posts'] for d in ds),'posts_per_day':mean(d['posts'] for d in ds),
           'first_median':clock(median(d['first_minute'] for d in ac)),
           'last_median':clock(median(d['last_minute'] for d in ac)),
           'last_median_minute':median(d['last_minute'] for d in ac)}
    times=Counter(r['published_at'][11:16] for r in rows)
    recurring={
       'friday_song':[r for r in rows if r['title']=='Пятнишная песенка' and r['weekday']==4],
       'bannizm':[r for r in rows if '/bannizm/' in r['url']],
       'ali':[r for r in rows if '/aliexpress/' in r['url']],
       'films':[r for r in rows if '/films/' in r['url']],
    }
    recurring_summary={name:{'posts':len(rs),'weekday_counts':dict(Counter(r['weekday'] for r in rs)),
          'clock_counts':dict(Counter(r['published_at'][11:] for r in rs)),
          'examples':[{'url':r['url'],'title':r['title'],'published_at':r['published_at']} for r in rs]}
          for name,rs in recurring.items()}
    friday_regular=len(recurring['friday_song'])+sum(r['weekday']==4 for r in recurring['bannizm'])
    grid_models={}
    for name,test in [('minute_00',lambda m:m==0),('minute_00_30',lambda m:m in (0,30)),('every_ten_minutes',lambda m:m%10==0)]:
        remainder=[r for r in rows if not test(r['minute'])]
        rem_days=defaultdict(list)
        for r in remainder: rem_days[r['date']].append(r)
        monthly_remainder=[]
        for month in monthly:
            ac=[v for k,v in rem_days.items() if k.startswith(month['month'])]
            vals=[max(r['minute_of_day'] for r in rs) for rs in ac]
            monthly_remainder.append({'month':month['month'],'days_with_remainder':len(ac),
                'posts':sum(len(v) for v in ac),'median_last_minute':median(vals) if vals else None})
        vals=[max(r['minute_of_day'] for r in rs) for rs in rem_days.values()]
        grid_models[name]={'grid_posts':len(rows)-len(remainder),'remaining_posts':len(remainder),
           'days_with_remainder':len(rem_days),'days_without_remainder':len(days)-len(rem_days),
           'remaining_last_median_minute':median(vals),'remaining_last_median':clock(median(vals)),
           'remaining_before_14':sum(r['minute_of_day']<840 for r in remainder),
           'remaining_at_or_after_18':sum(r['minute_of_day']>=1080 for r in remainder),
           'remaining_sections':dict(Counter(r['url'].split('/')[3] for r in remainder)),
           'remaining_hourly':[sum(r['hour']==h for r in remainder) for h in range(24)],
           'remaining_weekday_hourly':[[sum(r['hour']==h and r['weekday']==w for r in remainder) for h in range(24)] for w in range(7)],
           'monthly':monthly_remainder}
    summary={
       'period':{'start_inclusive':START.isoformat(),'end_exclusive':END.isoformat(),'last_complete_day':(END-timedelta(days=1)).isoformat()},
       'scope':'All entries in the public unfiltered /blog/ feed, including article announcements; comments excluded.',
       'time_basis':'Displayed site time; no explicit time zone or UTC offset established. No timezone conversion.',
       'posts':len(rows),'calendar_days':len(days),'active_days':len(active),'zero_days':[d['date'] for d in daily if d['posts']==0],
       'posts_per_day':len(rows)/len(days),'median_posts_per_day':median(d['posts'] for d in daily),
       'first_median':clock(median(d['first_minute'] for d in active)),
       'last_median':clock(median(d['last_minute'] for d in active)),
       'median_span_minutes':median(d['span_minutes'] for d in active),
       'minute_zero':sum(r['minute']==0 for r in rows),'minute_zero_or_thirty':sum(r['minute'] in (0,30) for r in rows),
       'minute_multiple_ten':sum(r['minute']%10==0 for r in rows),
       'before_12':sum(r['minute_of_day']<720 for r in rows),
       'at_or_after_18':sum(r['minute_of_day']>=1080 for r in rows),
       'at_or_after_20':sum(r['minute_of_day']>=1200 for r in rows),
       'between_8_and_18':sum(480<=r['minute_of_day']<1080 for r in rows),
       'earliest_clock':min(rows,key=lambda r:r['minute_of_day']),
       'latest_clock':max(rows,key=lambda r:r['minute_of_day']),
       'busiest_days':sorted(daily,key=lambda d:(-d['posts'],d['date']))[:10],
       'top_exact_times':[{'time':t,'posts':n} for t,n in times.most_common(12)],
       'hourly':hourly,'weekday':weekday,'monthly':monthly,'groups':groups,
       'sections':dict(Counter(r['url'].split('/')[3] for r in rows)),
       'grid_models':grid_models,
       'friday_without_song_and_bannizm':{
           'excluded':friday_regular, 'posts':weekday[4]['posts']-friday_regular,
           'posts_per_friday':(weekday[4]['posts']-friday_regular)/weekday[4]['calendar_days'],
           'other_weekdays_posts_per_day':sum(x['posts'] for x in weekday[:4])/sum(x['calendar_days'] for x in weekday[:4])},
       'complete_weeks':complete_weeks,'longest_gaps':gaps[:12],
       'daily_first_quantiles_minutes':np.quantile([d['first_minute'] for d in active],[0,.25,.5,.75,1]).tolist(),
       'daily_last_quantiles_minutes':np.quantile([d['last_minute'] for d in active],[0,.25,.5,.75,1]).tolist()
    }
    url_counts=Counter(r['url'] for r in rows)
    audit={'pages':[p['meta'] for p in pages], 'fetched_labels':len(all_rows),'unique_labels':len(unique),
       'duplicate_labels':len(all_rows)-len(unique),'period_labels':len(rows),
       'repeated_urls':{u:n for u,n in url_counts.items() if n>1},
       'outside_period':len(unique)-len(rows),'current_day_excluded':[r for r in unique.values() if r['published_at'].startswith(END.isoformat())],
       'boundary_before_start':[r for r in sorted(unique.values(),key=lambda r:r['published_at'],reverse=True) if r['published_at']<START.isoformat()][:3]}
    write('publications.json',rows);write('daily.json',daily);write('summary.json',summary);write('coverage.json',audit);write('recurring.json',recurring_summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('weekday','hourly','complete_weeks','longest_gaps')},ensure_ascii=False,indent=2))
    print('WEEKDAY',json.dumps(weekday,ensure_ascii=False))
    print('AUDIT',json.dumps({k:v for k,v in audit.items() if k!='pages'},ensure_ascii=False))

if __name__=='__main__':
    main()
