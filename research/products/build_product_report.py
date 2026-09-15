"""Research checkpoint: reproducible corpus counts and manually reviewed model roles.

Run next to exler-products-page1.json and product_analysis/placements.json.
Uses only the author's article body, never reader comments. No network or secrets.
"""
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'product_report'
OUT.mkdir(exist_ok=True)
posts = {int(p['id']): p for p in json.loads((ROOT / 'exler-products-page1.json').read_text())['posts']
         if '/aliexpress/' in p['url']}
rows = json.loads((ROOT / 'product_analysis/placements.json').read_text())

patterns = {
    'Планшеты': r'\bпланшет\w*',
    'Наушники': r'\bнаушник\w*',
    'Внешние аккумуляторы': r'\bвнешн\w*\s+аккумулятор\w*|\bпауэрбанк\w*|\bповербанк\w*|\bpower\s*bank\b',
    'Кабели': r'\bкабел\w*',
    'Зарядные адаптеры': r'\bGaN\b|\bзарядн\w*\s+(?:адаптер|устройств)\w*|\bадаптер\w*\s+(?:для\s+)?зарядк\w*',
    'Светильники': r'\bсветильник\w*',
    'Пылесосы': r'\bпылесос\w*',
    'Вентиляторы': r'\bвентилятор\w*',
    'Зубные щётки': r'\bзубн\w*\s+щ[её]тк\w*',
    'Бритвы': r'\b(?:электро)?бритв\w*',
    'Массаж': r'\bмассаж\w*',
    'Декантеры': r'\bдекант[ео]р\w*',
}
theme_counts = []
for title, pattern in patterns.items():
    ids = sorted(pid for pid, p in posts.items() if re.search(pattern, p['body'].split('У меня на сегодня все')[0], re.I))
    theme_counts.append({'theme': title, 'editions': len(ids), 'post_ids': ids, 'pattern': pattern})
theme_counts.sort(key=lambda x: -x['editions'])

# Each event reviewed in the source text. Roles are exclusive; ownership is a
# separate self-report flag. Count one model per edition, not anchors or links.
models = [
 ('soocas-x3u', 'Soocas X3U, обычная версия', r'\bX3U\b', {
   9901: ('recommendation', False, 'Представлена новая модификация; пользование относится к прежней X3.'),
   9827: ('recommendation', True, 'Приехала, испытана; старая X3 ещё работает.'),
   8868: ('recommendation', True, 'Повторная рекомендация со скидкой.'),
   7832: ('recommendation', True, 'Почти год использования, такая же у сына.'),
   7414: ('secondary_recommendation', True, 'Похвала X3U в блоке о держателе щётки.'),
   5903: ('secondary_recommendation', True, 'Положительное сравнение с дешёвой Gollinio и Philips.'),
   3185: ('background', False, 'X3U названа в истории модификаций; новая покупка — X3S.'),
   1976: ('background', True, 'Своя X3U — фон для рекомендации бюджетной T100.'),
   2699: ('different_variant', False, 'Специальная серия Van Gogh, считать отдельно.')},
  'Физический экземпляр и версия корпуса не устанавливаются по рассказу о семействе X3.'),
 ('mijia-t700', 'Xiaomi Mijia T700', r'\bT700\b', {6032:('recommendation',False,''),5146:('recommendation',False,''),958:('recommendation',False,'')}, 'Одинаковое модельное имя; аппаратные ревизии не проверены.'),
 ('mijia-t100', 'Xiaomi Mijia T100', r'\bT100\b', {3333:('recommendation',False,''),1976:('recommendation',False,'')}, ''),
 ('soocas-x3s', 'Soocas X3S', r'\bX3S\b', {3185:('recommendation',False,'Выбирает замену повреждённой щётке; получение в этом выпуске не подтверждено.')}, ''),
 ('soocas-d3', 'Soocas D3', r'\bSoocas\s+D3\b', {4685:('recommendation',False,'Модель со стерилизатором.')}, ''),
 ('movespeed-m25pro', 'MOVESPEED M25 Pro', r'\bM25\s*Pro\b', {1976:('recommendation',False,'140 Вт; порты 140/45/22,5.'),1157:('recommendation',False,'140 Вт; намерение купить, свой E20 упомянут отдельно.'),676:('recommendation',False,'145 Вт; собственное владение относится к прежней модели 20000/65.')}, 'Одно название, но разные описания мощностей. Три публикации о модельном имени, не доказательство одной аппаратной версии.'),
 ('movespeed-msp17', 'MOVESPEED MSP17', r'\bMSP17\b', {1003:('recommendation',False,''),10655:('recommendation',False,'Повтор того же модельного имени и характеристик.')}, ''),
 ('qoovi-20000-45', 'QOOVI 20000 мАч PD 45 Вт', r'QOOVI.{0,25}45', {1894:('recommendation',True,'Куплен и проверен: ноутбук с 8 до 68%.'),1555:('background',True,'Опыт во время блэкаута; новая покупка в блоке — MOVESPEED для сына.'),1436:('secondary_recommendation',True,'Прямо советует для ноутбука вместо QOOVI 60000/22,5.')}, 'Идентичность по марке, ёмкости, мощности и авторской отсылке к тесту, без артикула.'),
 ('movespeed-e20', 'MOVESPEED E20', r'\bE20\b', {2282:('recommendation',False,''),1157:('background',True,'Уже есть и проверял; рекомендуемая новинка в блоке — M25 Pro.')}, 'В июльском тексте E20 имеет 2000 мАч, в декабрьском — 20000. Сохраняем расхождение; возможная опечатка.'),
]
events = []
ranking = []
for key, title, pattern, labels, caveat in models:
    found = {pid for pid,p in posts.items() if re.search(pattern,p['body'],re.I)}
    assert found == set(labels), (key, found ^ set(labels))
    for pid, (role, owned, note) in labels.items():
        p = posts[pid]
        match = re.search(pattern, p['body'], re.I)
        events.append({'model_key':key,'model':title,'post_id':pid,'date':p['published_at'],
                       'url':p['url'],'role':role,'self_reported_use':owned,'note':note,
                       'excerpt':p['body'][max(0,match.start()-170):match.end()+330]})
    count = collections.Counter(v[0] for v in labels.values())
    rec = count['recommendation'] + count['secondary_recommendation']
    ranking.append({'model':title,'key':key,'all_named_mentions':len(labels),
                    'recommendation_editions':rec,'primary':count['recommendation'],
                    'secondary':count['secondary_recommendation'],
                    'background':count['background'],'different_variant':count['different_variant'],
                    'self_reported_use_editions':sum(v[1] for v in labels.values()),'caveat':caveat})
ranking.sort(key=lambda x:(-x['recommendation_editions'],-x['all_named_mentions']))

stats = {'editions':len(posts),'period':[min(p['published_at'] for p in posts.values()),max(p['published_at'] for p in posts.values())],
         'link_candidates':len(rows),'distinct_link_keys':len({r['link_key'] for r in rows}),
         'extracted_sections_with_links':len({(r['post_id'],r['section']) for r in rows}),
         'reviewed_model_names':len(models),'reviewed_model_edition_events':len(events),
         'verified_recommendation_events_in_reviewed_set':sum(x['recommendation_editions'] for x in ranking),
         'all_corpus_exact_recommendations':None,'all_corpus_unique_products':None,
         'limitations':'Reviewed model set is purposive, not a global top. Keyword themes include comparisons and accessories. Link extraction can miss links; source article names independently checked for reviewed models.'}

for name,data in [('summary',stats),('theme_counts',theme_counts),('model_ranking',ranking),('model_events',sorted(events,key=lambda x:(x['model_key'],x['date']))),
                  ('corpus_index',[{'post_id':pid,'date':p['published_at'],'url':p['url'],'title':p['title']} for pid,p in sorted(posts.items(),key=lambda x:x[1]['published_at'])])]:
    (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
for year in sorted({r['date'][:4] for r in rows}):
    with (OUT/('link_candidates_'+year+'.tsv')).open('w') as f:
        w=csv.writer(f,delimiter='\t');w.writerow(['post_id','date','section','label','url','link','review_status'])
        for r in rows:
            if r['date'].startswith(year):
                w.writerow([r['post_id'],r['date'],r['section'],r['label'],r['post_url'],r['link'],'unreviewed_link_not_product'])
print(json.dumps(stats,ensure_ascii=False,indent=2))
print([(x['theme'],x['editions']) for x in theme_counts])
print([(x['model'],x['recommendation_editions'],x['all_named_mentions']) for x in ranking])
