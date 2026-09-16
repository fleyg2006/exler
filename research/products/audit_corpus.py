"""Offline census of saved author HTML. No merchant requests; no network code.

python audit_corpus.py --input-dir /path/to/raw --output-dir /path/to/data/census
Input: html_batches/*.json and product_analysis/placements.json.
Heuristic status is NOT a manually verified product or recommendation count.
"""
import argparse, collections, csv, json, re
from pathlib import Path
from html.parser import HTMLParser

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag,self.attrs,self.parent,self.children=tag,dict(attrs),parent,[]
    def has(self,c):return c in self.attrs.get('class','').split()
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c,Node):yield from c.walk()
    def text(self):
        if self.tag in ('script','style'):return ''
        return ' '.join(c.text() if isinstance(c,Node) else c for c in self.children)
class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.root=Node();self.cur=self.root
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.cur);self.cur.children.append(n)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.cur=n
    def handle_endtag(self,tag):
        p=self.cur
        while p.parent:
            if p.tag==tag:self.cur=p.parent;return
            p=p.parent
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_data(self,data):self.cur.children.append(data)
def clean(s):return re.sub(r'\s+',' ',s).strip()

# Manually read origin-bearing passages. Strict reader-origin exclusion also
# applies when the author later purchased/tested the reader's suggestion.
READER={(2664,5),(2896,4),(3297,2),(5458,6),(6499,0),(6903,4),(8518,1),
        (9179,3),(9321,0),(9355,1),(9355,3),(9525,1),(9525,11),(9645,10),
        (9688,9),(9734,8),(9785,8),(9866,0),(9866,6)}
THIRD_PARTY={(1157,9),(3372,8),(4048,4),(4438,0),(4685,8),(6104,2),(6421,8)}
MIXED={(9607,0),(8947,1)}
NON_ORIGIN={(676,2),(797,7),(2552,9),(2633,4),(4011,0),(4048,1),
            (4166,8),(4964,7),(7273,9),(9495,3),(9645,8),(10211,9),(9143,10)}
RECOVERED={(5412,2):'Электронасос Xiaomi',(5412,3):'Резинки для занятий спортом',
 (5412,5):'Перезаряжаемые аккумуляторы PKCell',(5412,6):'Реверсивные зонты',
 (5412,7):'Поддержка головы для автомобилей',(5412,8):'Дополнительный ящик для стола',
 (5412,9):'Массажная насадка',(5412,10):'Квадратные стаканы',
 (5276,10):'Чехлы из искусственной замши для ноутбука',(4718,5):'Крючки и вешалки',
 (4358,3):'Конструкторы строений',(2282,2):'Музыкальная шкатулка',(10502,4):'Удлинители с USB и дисплеем'}
SERVICE={(pid,0) for pid in [9734,9688,9645,9525,9179,9018,8781,8749,8715,8518,8348,8218,7832,6641,5412,5276,3734,2936,2811,1938,1854,1787,1747,1399,1311,457,417,377,337,299,259,
 9972,9495,9143,9098,8905,8868,8832,8600,8163,8066,6457,6104,5822,4398,3764,3372,2699,2517,2411,10112,
 8986,8947,8673,8637,8562,7093,6592,3261,9076,9458,9827]}
SERVICE|={(8562,1),(6104,1),(9688,1),(5276,11)}

# Match product labels, not the entire paragraph's technical specifications.
# Categories are multi-label and explicitly provisional.
CATEGORIES={
 'Питание и кабели':r'\b(?:кабел\w*|заряд\w*|пауэрбанк\w*|повербанк\w*|аккумулятор\w*|удлинител\w*|тройник\w*|батаре\w*|GaN\w*)',
 'Аудио':r'\b(?:наушник\w*|колонк\w*|микрофон\w*|саундбар\w*|аудио\w*|ЦАП|earbuds|buds)',
 'Часы':r'\b(?:час(?:ы|ов|ики|ами)|браслет\w*|smartwatch|watch)',
 'Смартфоны и планшеты':r'\b(?:смартфон\w*|планшет\w*|ридер\w*|Kindle|POCO|iPad)',
 'Компьютеры и периферия':r'\b(?:ноутбук\w*|компьютер\w*|клавиатур\w*|мыш[ьи]\w*|SSD|накопител\w*|флешк\w*|роутер\w*|хаб\w*|веб.?камер\w*)',
 'Уход и гигиена':r'\b(?:бритв\w*|электробритв\w*|зубн\w*|ирригатор\w*|триммер\w*|маникюр\w*|массаж\w*|беруш\w*)',
 'Вино и бар':r'\b(?:декант[ео]р\w*|аэратор\w*|штопор\w*|бокал\w*|винн\w*)|\bдля вина\b',
 'Кухня':r'\b(?:кухон\w*|нож\w*|ножниц\w*|сковород\w*|кастрюл\w*|кофе\w*|чайник\w*|термос\w*|вакууматор\w*|овощ\w*|фрукт\w*|салат\w*|чеснок\w*|тарелк\w*|миск\w*|кружк\w*|ложк\w*|посуда|разделоч\w*)',
 'Одежда, сумки и поездки':r'\b(?:сумк\w*|рюкзак\w*|чемодан\w*|кошел[её]к\w*|куртк\w*|футболк\w*|носк\w*|зонт\w*|обув\w*|кроссов\w*|рем(?:ень|ни|ней)|фартук\w*|перчат\w*)',
 'Инструменты и автомобиль':r'\b(?:инструмент\w*|отв[её]ртк\w*|дрел\w*|шурупов[её]рт\w*|компрессор\w*|насос\w*|мультиметр\w*|автомобил\w*|автомагнитол\w*|видеорегистратор\w*)',
 'Дом, свет и организация':r'\b(?:светильник\w*|ламп\w*|фонар\w*|пылесос\w*|уборк\w*|увлажнител\w*|органайзер\w*|сушил\w*|полк\w*|крюч\w*|коврик\w*|вентилятор\w*|ночник\w*)'
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    links=json.loads((a.input_dir/'product_analysis/placements.json').read_text())
    by_section=collections.defaultdict(list)
    for r in links:by_section[(r['post_id'],r['section'])].append(r)
    posts={}
    for path in sorted((a.input_dir/'html_batches').glob('*.json')):
        for p in json.loads(path.read_text())['posts']:
            if '/aliexpress/' in p['url']:
                pid=int(p['id']);assert pid not in posts,('duplicate post',pid);posts[pid]=p
    records=[];missing=[];missing_link_blocks=[]
    for pid,p in sorted(posts.items(),key=lambda x:x[1]['published_at']):
        tr=Tree();tr.feed(p.get('html') or '')
        article=next((n for n in tr.root.walk() if n.has('article-item-content') or n.has('blog-item-content')),None)
        if article is None:missing.append(pid);continue
        sections=[[]]
        for n in article.children:
            if isinstance(n,Node) and n.tag=='hr':sections.append([])
            else:sections[-1].append(n)
        for si,children in enumerate(sections):
            n=Node();n.children=children;t=clean(n.text());key=(pid,si);lr=by_section.get(key,[])
            if not t and not lr:continue
            labels=list(dict.fromkeys(r['label'] for r in lr))
            before_footer=re.split(r'У меня (?:на сегодня )?вс[её][.!]',t,maxsplit=1)[0]
            if key in RECOVERED:labels=[RECOVERED[key]]
            reader_hint=bool(re.search(r'читател|коммент|комментах|посоветовал|порекомендовал|прислал',before_footer,re.I))
            origin='no_explicit_external_origin_detected'
            if key in READER:origin='reader_origin_excluded'
            elif key in THIRD_PARTY:origin='external_or_unknown_origin_review'
            elif key in MIXED:origin='mixed_author_reader_review'
            elif reader_hint and key not in NON_ORIGIN:origin='origin_hint_review'
            service=bool((not before_footer.strip()) or re.search(r'^(?:Всем привет.{0,120})?(?:Полезные ссылочки|Партнерская программа)',t,re.I))
            label_service=bool(labels) and all(re.search(r'хиты|распродаж|скидк|купон|доставк|подарки|продаж|backit|зарегистрир|товары|подборк|школе|featured products|новогодние',s,re.I) for s in labels)
            if not before_footer.strip():status='footer_excluded'
            elif key in SERVICE:status='service_excluded'
            elif key==(4166,8):status='author_ironic_offer_review'
            elif key in RECOVERED:status='recovered_product_block_review'
            elif not lr:status='no_candidate_links_review'
            elif service or label_service:status='service_or_promotion_review'
            elif origin=='reader_origin_excluded':status='reader_origin_excluded'
            elif origin.endswith('_review'):status='origin_review'
            else:status='author_text_candidate_not_verified'
            cats=[name for name,pat in CATEGORIES.items() if any(re.search(pat,label,re.I) for label in labels)]
            flags=[]
            for name,pat in {
                'order_report':r'заказал|заказала|заказали|прикуплю|куплю',
                'purchase_report':r'\bкупил|\bпокупал|\bприкупил',
                'use_report':r'\bпользуюсь|\bиспользую|\bу меня|\bмне служит',
                'comparison':r'\bпредыдущ|\bсравнен|\bвместо|\bдороже|\bдешевле',
                'failure_or_service':r'сломал|выш[её]л из строя|скреж|перестал|затуп|помер|помира|замен|сломает',
                'explicit_endorsement':r'\bрекомендую|\bсоветую|\bнравится|\bдоволен',
            }.items():
                if re.search(pat,before_footer,re.I):flags.append(name)
            rec={'block_id':f'{pid}:{si}','post_id':pid,'section':si,'date':p['published_at'],'source_url':p['url'],
                 'candidate_links':len(lr),'labels':labels,'status':status,'origin':origin,'category_hints':cats,
                 'text_flags':flags,'review_level':'manual_targeted_triage' if key in READER|THIRD_PARTY|MIXED|NON_ORIGIN|SERVICE|set(RECOVERED) else 'heuristic',
                 'excerpt':before_footer[:420],'exact_product_count':None,'exact_unique_model_count':None}
            records.append(rec)
            if not lr and before_footer and any(x.tag=='a' for x in n.walk()):missing_link_blocks.append(rec['block_id'])
    assert not missing,missing
    assert sum(r['candidate_links'] for r in records)==len(links)
    indexed={r['block_id']:r for r in records}
    for key in READER|THIRD_PARTY|MIXED|NON_ORIGIN|SERVICE|set(RECOVERED):
        assert f'{key[0]}:{key[1]}' in indexed,('stale annotation',key)
    for key in ['2772:5','10306:7','10253:5']:
        assert indexed[key]['status']=='author_text_candidate_not_verified',('price anchor is not a promotion',key)
    assert indexed['5412:2']['status']=='recovered_product_block_review'
    assert indexed['9355:1']['status']=='reader_origin_excluded'
    assert indexed['9972:12']['status']=='footer_excluded'
    counts=collections.Counter(r['status'] for r in records)
    candidate=[r for r in records if r['status']=='author_text_candidate_not_verified']
    categories={name:{'candidate_blocks':sum(name in r['category_hints'] for r in candidate),
                      'post_ids':sorted({r['post_id'] for r in candidate if name in r['category_hints']})} for name in CATEGORIES}
    summaries={'posts':len(posts),'nonempty_html_sections':len(records),'linked_sections':sum(bool(r['candidate_links']) for r in records),
               'candidate_links':len(links),'status_counts':dict(counts),'category_hints':categories,
               'exact_total_author_recommendations':None,'exact_unique_products':None,
               'no_candidate_links_with_anchor':missing_link_blocks,
               'method':'All saved article sections enumerated. Heuristic triage, not complete manual semantic review. Categories overlap and use anchor labels only. Reader-origin blocks excluded conservatively.'}
    repeats=collections.defaultdict(list)
    eligible={r['block_id'] for r in candidate}
    for x in links:
        if f"{x['post_id']}:{x['section']}" in eligible:
            label=clean(x['label']).casefold()
            if len(label)>=8 and not re.match(r'^(?:вот|так|друг|ссыл|для рф|купить|достав)',label):repeats[label].append(x)
    repeated=[{'label':k,'edition_count':len({x['post_id'] for x in v}),'source_urls':list(dict.fromkeys(x['post_url'] for x in v)),
               'identity_status':'same_label_only_not_same_product'} for k,v in repeats.items() if len({x['post_id'] for x in v})>1]
    repeated.sort(key=lambda x:(-x['edition_count'],x['label']))
    for year in sorted({r['date'][:4] for r in records}):
        with (a.output_dir/('blocks_'+year+'.jsonl')).open('w') as f:
            for r in records:
                if r['date'].startswith(year):f.write(json.dumps(r,ensure_ascii=False)+'\n')
    for name,value in [('summary',summaries),('repeated_labels',repeated)]:
        (a.output_dir/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    review=[r for r in records if r['status'] not in ('author_text_candidate_not_verified','footer_excluded','service_excluded')]
    (a.output_dir/'review_queue.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summaries.items() if k not in ('category_hints','no_candidate_links_with_anchor')},ensure_ascii=False,indent=2))
    print('Category hints:',{k:v['candidate_blocks'] for k,v in categories.items()})
    print('Repeated labels:',len(repeated))
if __name__=='__main__':main()
