import json, re, collections, pathlib, html, urllib.parse
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / 'product_analysis'
OUT.mkdir(exist_ok=True)
class Node:
    def __init__(self, tag='', attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or []), parent, []
    def has(self, cls): return cls in self.attrs.get('class','').split()
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Node): yield from c.walk()
    def text(self, skip_quotes=False):
        if self.tag in ('script','style') or (skip_quotes and (self.tag=='blockquote' or self.has('quote'))): return ''
        return ' '.join(c.text(skip_quotes) if isinstance(c,Node) else c for c in self.children)

class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root=Node(); self.cur=self.root
    def handle_starttag(self, tag, attrs):
        n=Node(tag,attrs,self.cur); self.cur.children.append(n)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'): self.cur=n
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs); self.handle_endtag(tag)
    def handle_endtag(self,tag):
        p=self.cur
        while p.parent:
            if p.tag==tag: self.cur=p.parent; return
            p=p.parent
    def handle_data(self,data): self.cur.children.append(data)

def clean(s): return re.sub(r'\s+',' ',s).strip()
def normlink(s):
    u=urllib.parse.urlsplit(html.unescape(s)); host=u.netloc.lower().removeprefix('www.')
    m=re.search(r'/item/(?:[^/]+/)?(\d+)\.html',u.path)
    if m and 'aliexpress' in host: return 'aliexpress:item:'+m[1]
    return host+u.path.rstrip('/')+('?' +u.query if not any(x in host for x in ['aliexpress','ali.pub','alii.pub','ali.ski','aliclick']) else '')

def category(t):
    rules=[
      ('Вино и бар',r'декантер|аэратор|вин[аоыуе]|штопор|бокал|винн'),
      ('Вентиляторы и охлаждение',r'вентилятор|охладител'),
      ('Наушники и аудио',r'наушник|earbuds|buds|колонк|усилител.*звук|микрофон|цап'),
      ('Часы и браслеты',r'час(?:ы|ов|ам|ики)|браслет|smartwatch'),
      ('Смартфоны, планшеты, ридеры',r'смартфон|планшет|ридер|poco|redmi|kindle'),
      ('Зарядка, питание и кабели',r'заряд|пауэрбанк|повербанк|power.?bank|кабел|батаре|аккумулятор|сетевой фильтр|удлинител'),
      ('Массаж, здоровье и уход',r'массаж|тонометр|термометр|зубн|ирригатор|бритв|триммер|стрижк|маникюр|пульсоксиметр|колен|ортопед'),
      ('Кухня и хранение продуктов',r'кухон|нож|ножниц|сковород|кастрюл|контейнер|бан(?:ка|ки|ок|ку)|вакуум|продукт|овощ|фрукт|кофе|чайник|термос|соковыжим|мельниц|точил|чеснок|посуда|разделоч|форм.*выпеч'),
      ('Сумки, одежда и поездки',r'рюкзак|сумк|кошелек|кошелёк|чемодан|кроссов|кросов|куртк|футбол|носк|зонт|спальн|одежд|обув|ремень|перчат|очк'),
      ('Компьютеры и периферия',r'компьютер|ноутбук|клавиатур|мыш[ьи]|ssd|накопител|монитор|usb.?хаб|концентратор|роутер|маршрутизатор|веб.?камер'),
      ('Инструменты и автомобиль',r'отвертк|отвёртк|шуруповерт|шуруповёрт|инструмент|пассатиж|паяль|дрел|автомоб|машин|компрессор|насос|мультиметр|держател'),
      ('Дом, свет и организация',r'светильник|ламп|фонар|освещ|органайзер|пылесос|уборк|диффузор|увлажнител|крюч|полк|сушил|стирк|чистк|чистящ|коврик|скотч|липуч|лента|ванн|унитаз|туалет|замок|щетк|щёт'),
    ]
    for label,pat in rules:
        if re.search(pat,t,re.I): return label
    return 'Прочее / ручная разметка'

posts=[]
for path in sorted((ROOT/'html_batches').glob('*.json')):
    posts.extend(json.loads(path.read_text())['posts'])
rows=[]; comments=[]; domains=collections.Counter(); editions=[]; failures=[]
for post in posts:
    if not post['url'].split('/')[3]=='aliexpress': continue
    tree=Tree(); tree.feed(post.get('html') or '')
    article=next((n for n in tree.root.walk() if n.has('article-item-content')),None)
    if article is None:
        article=next((n for n in tree.root.walk() if n.has('blog-item-content')),None)
    if article is None:
        failures.append(post['id']); continue
    sections=[[]]
    for c in article.children:
        if isinstance(c,Node) and c.tag=='hr': sections.append([])
        else: sections[-1].append(c)
    seen=set(); postrows=[]
    for si,section in enumerate(sections):
        sn=Node();sn.children=section
        st=clean(sn.text())
        for a in sn.walk():
            if a.tag!='a': continue
            href=a.attrs.get('href',''); label=clean(a.text())
            host=urllib.parse.urlsplit(href).netloc.lower()
            if host: domains[host]+=1
            if not label or not host or any(x in host for x in ['exler.','youtube','youtu.be','wikipedia','t.me']): continue
            if not re.search(r'ali|alli\.pub|banggood|gearbest|amazon|ozon|wildberries|jd\.com|joom|temu|cafago|geekbuying|dhgate|tomtop',host): continue
            if re.search(r'распродаж|промокод|к[эе]шб[эе]к|страниц.*акци',label,re.I): continue
            key=normlink(href)
            if key in seen: continue
            seen.add(key)
            p=a.parent
            while p.parent and p.tag not in ('p','li'): p=p.parent
            context=clean(p.text())
            if len(context)>2500: context=st[:1500]
            row=dict(post_id=int(post['id']),date=post['published_at'],post_url=post['url'],section=si,label=label,link=href,link_key=key,context=context,category=category(context[:220]),personal_marker=bool(re.search(r'я (?:себе |это |его |её |ее )?(?:купил|заказал|использую|пользуюсь)|у меня|себе купил|заказал себе|пользуюсь|использую|мне подарили',st,re.I)))
            rows.append(row);postrows.append(row)
    editions.append(dict(id=int(post['id']),date=post['published_at'],url=post['url'],placements=len(postrows)))
    seen_comments=set()
    for n in tree.root.walk():
        if not n.has('comments-item'): continue
        # Exclude nested comments when locating the author and body.
        nodes=[]
        def ownwalk(x):
            for c in x.children:
                if isinstance(c,Node):
                    if c.has('comments-item'): continue
                    nodes.append(c);ownwalk(c)
        ownwalk(n)
        author=next((x for x in nodes if x.has('profile-link')),None)
        if author is None or clean(author.text())!='Alex Exler': continue
        body=next((x for x in nodes if x.has('comments-item-title')),None)
        link=next((x for x in nodes if x.has('link-comm')),None)
        if body is None: continue
        anchor=link.attrs.get('href','') if link else ''
        text=clean(body.text(skip_quotes=True))
        if (anchor,text) in seen_comments:continue
        seen_comments.add((anchor,text))
        links=[dict(label=clean(a.text()),link=a.attrs.get('href','')) for a in body.walk() if a.tag=='a' and a.attrs.get('href','').startswith('http')]
        comments.append(dict(post_id=int(post['id']),post_url=post['url'],anchor=anchor,text=text,links=links))

groups=collections.defaultdict(list)
for r in rows:groups[r['link_key']].append(r)
ranking=[]
for key, rr in groups.items():
    ranking.append(dict(key=key,editions=len(set(x['post_id'] for x in rr)),labels=list(dict.fromkeys(x['label'] for x in rr)),first=min(x['date'] for x in rr),last=max(x['date'] for x in rr),examples=[dict(post_id=x['post_id'],url=x['post_url'],context=x['context']) for x in rr]))
ranking.sort(key=lambda r:-r['editions'])
stats=dict(matched_posts=len(posts),editions=len(editions),placements=len(rows),distinct_link_keys=len(groups),categories=dict(collections.Counter(x['category'] for x in rows)),years=dict(collections.Counter(x['date'][:4] for x in rows)),personal_marker_placements=sum(x['personal_marker'] for x in rows),alex_comments=len(comments),alex_comments_with_links=sum(bool(x['links']) for x in comments),missing_html=failures,domains=domains.most_common(30))
for name,data in [('placements',rows),('editions',editions),('repeat_links',ranking),('alex_comments',comments),('stats',stats)]:
    (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False,indent=2))
print('\nTOP REPEATS')
for r in ranking[:40]: print(r['editions'],r['labels'][:4],r['key'])
