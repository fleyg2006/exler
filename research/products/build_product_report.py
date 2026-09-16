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
models.extend([
 ('mijia-s700','Xiaomi Mijia S700',r'\bS700\b',{
  4324:('recommendation',False,'Заказана; доставка ещё не подтверждена.'),
  4284:('recommendation',True,'Приехала; первое бритьё и положительный вердикт.'),
  3372:('recommendation',True,'Повторная рекомендация со снижением цены.'),
  2811:('secondary_recommendation',True,'Сильная похвала внутри рассказа о замене скрежещущей головки.'),
  2411:('secondary_recommendation',True,'Названа классной и долговечной при рекомендации S500.'),
  1715:('background',True,'Собственная S700 — фон для S302.'),
  586:('secondary_recommendation',True,'Повторная похвала долговечности в блоке S500.'),
  337:('background',True,'Только владение и цена при рекомендации S500.')},
  'Основных предложений 3, дополнительных положительных оценок 3. S700 не объединена с головкой. В истории предшественника расходятся S500/S300 и даты покупки.'),
 ('mijia-s500','Xiaomi Mijia S500',r'\bS500\b',{
  4324:('background',True,'Ретроспектива: нравилась, но быстро выходила из строя; не новая рекомендация.'),
  2411:('recommendation',False,'Предлагается более дешёвая модель.'),
  586:('recommendation',False,'Повторное предложение со скидкой.'),
  337:('recommendation',False,'Положительная рекомендация по сниженной цене.')},
  'Отрицательная история 2023 года сохранена; позднее проблемный предшественник называется S300. Не исправляем название за автора.'),
 ('mijia-s100','Xiaomi Mijia S100',r'\bS100\b',{
  5859:('recommendation',True,'Сообщает о трёх годах использования в поездках.'),
  1195:('recommendation',True,'Сообщает о пяти годах использования.')},''),
 ('xiaomi-pad7','Xiaomi Pad 7',r'\bXiaomi\s+Pad\s+7\b(?!\s+Pro)',{
  543:('background',True,'Сравнение с рекомендуемым Pad 7 Pro; ссылка на свой обзор.'),
  457:('recommendation',True,'Стартовая комплектация; ссылка на свой обзор.'),
  136:('recommendation',True,'Повторная рекомендация; ссылка на свой обзор.'),
  10655:('recommendation',True,'Рекомендация; 8/128 или больше.'),
  10445:('recommendation',True,'Предыдущее поколение выгоднее Pad 8.')},
  'Pad 7 Pro исключён. Комплектации памяти могут различаться; опыт обзора не доказывает покупку.'),
 ('amazfit-gts2mini','Amazfit GTS 2 mini',r'\bGTS\s+2\s+mini\b',{
  7414:('recommendation',False,''),7230:('recommendation',False,'Названа новой версией.'),
  7043:('recommendation',False,'Названа новой версией; собственный обзор относится к GTS 2e.'),
  6104:('recommendation',False,'Собственный обзор относится к GTS 2e.')},
  'Повторы модельного имени; ревизии не отождествлены. Обзоры GTS 2/GTS 2e не доказывают испытание mini.'),
 ('mijia-bedside2','Xiaomi Mijia Bedside Lamp 2',r'\bBedside\s+Lamp\s+2\b',{
  6032:('recommendation',False,'Владение относится к первой версии.'),
  629:('recommendation',True,'Сообщает о четырёх годах использования именно этой лампы.')},
  'В 2023 году своей названа первая версия, в 2025 — именно Lamp 2; непрерывность владения одной моделью не установлена.'),
 ('ilife-a30pro','ILIFE A30 PRO',r'\bILIFE\s+A30\s*PRO\b',{
  90:('recommendation',False,'Сравнивает с лично обозревавшимся TP-Link, не смешивать опыт.'),
  10655:('recommendation',False,'Повторная рекомендация; авторство упомянутого обзора не установлено.')},''),
 ('honor-padx9a','HONOR Pad X9a',r'\bHONOR\s+Pad\s+X9a\b',{
  18:('recommendation',False,'6/128 ГБ.'),10841:('recommendation',False,'8/256 ГБ.')},
  'Одна модельная линейка, две разные комплектации памяти; разрешение экрана в текстах расходится.')
])
models.extend([
 ('70mai-a400','70mai Dash Cam A400',r'\b70mai\s+Dash\s+Cam\s+A400\b',{
  6193:('recommendation',False,'Параметры и варианты комплектации.'),5033:('recommendation',False,'Повторное предложение.')},
  'A400 у Pictrey и DDPai — другие марки, исключены. Угол обзора в описаниях 142/145 градусов; комплектации различаются.'),
 ('soundcore-sport-x10','Anker Soundcore Sport X10',r'\bSport\s+X10\b',{
  4284:('recommendation',False,''),1084:('recommendation',False,'Повторное описание с сообщением о снижении цены.'),
  797:('secondary_recommendation',False,'Предлагает как более дешёвую альтернативу другой модели.')},
  'Ищется модельное сочетание Sport X10; бренд и контекст проверены во всех найденных абзацах.'),
 ('azdome-gs63h','AZDOME GS63H',r'\bGS63H\b',{
  7093:('recommendation',True,'Ссылка на собственный обзор; указано 4K.'),
  5314:('recommendation',True,'Ссылка на собственный обзор; указано 2K.'),
  1517:('recommendation',False,'Указано 4K; повторная рекомендация без нового сообщения об испытании.')},
  'В текстах расходится разрешение 4K/2K. Не выбираем правильную спецификацию и не доказываем одну аппаратную версию.'),
 ('baseus-a5','Baseus A5',r'\bBaseus\s+A5\b',{
  1715:('recommendation',False,'Заказ после отказа старого пылесоса; новый ещё не испытан.'),
  1042:('recommendation',False,'Повторное предложение, без подтверждения получения или результата теста.')},
  'Два предложения не доказывают две покупки или успешное испытание A5.'),
 ('baseus-ds10','Baseus DS10',r'\bBaseus\s+DS10\b',{
  3333:('recommendation',False,'Версии со встроенным аккумулятором и без него.'),
  2112:('recommendation',False,'Заказ на замену другой колонке; испытание планируется.')},
  'В первом посте две версии питания; конкретная купленная комплектация не установлена.'),
 ('baseus-f02','Baseus F02',r'\bBaseus\s+F02\b',{
  3082:('recommendation',False,'Указаны 7 настраиваемых кнопок.'),
  2772:('recommendation',False,'Указаны 7 кнопок, одна настраиваемая.')},
  'Различаются утверждения о настройке кнопок. Сохранено расхождение, без проверки карточки продавца.'),
 ('ddpai-mola-n3pro','DDPAI Mola N3 Pro',r'\bMola\s+N3\s+Pro\b',{
  3844:('recommendation',False,'Личный обзор относится к Mini5, а не к N3 Pro.'),
  3536:('recommendation',False,'Описаны комплекты с GPS и без GPS.')},
  'Модельные имена Mini5 и N3 Pro не объединены; наборы комплектации различаются.'),
 ('deerma-xs100','Deerma XS100',r'\bDeerma\s+XS100\b',{
  8986:('recommendation',False,'Предложение со скидкой.'),5586:('recommendation',False,'Повторное предложение.')},''),
 ('laimeng-6621','Laimeng 6621',r'\bLaimeng\s+6621\b',{
  9688:('secondary_recommendation',True,'Хвалит свою модель при сравнении с дешёвым вакууматором.'),
  5235:('secondary_recommendation',True,'Почти ежедневное использование три года; цена оправдана, но предлагается дешёвая альтернатива.'),
  3703:('secondary_recommendation',True,'Удачная модель, четвёртый год использования, внутри предложения пакетов.')},
  'Три дополнительных положительных оценки. Не три покупки; устойчивый положительный опыт сохранён как контрпример.'),
 ('oneplus-watch3','OnePlus Watch 3',r'\bOnePlus\s+Watch\s+3\b',{
  1126:('recommendation',False,'Предложение глобальной версии.'),
  417:('secondary_recommendation',True,'Положительная оценка своего обзора внутри предложения Watch 2R.'),
  10579:('recommendation',True,'После обзора часы забрал сын; отдельно советует цвет.')},
  'Свой тест и использование сыном не доказывают оплату или покупку часов автором.'),
 ('poco-m8pro','POCO M8 Pro 5G',r'\bPOCO\s+M8\s+Pro\b',{
  10445:('recommendation',False,''),10396:('recommendation',False,'Повтор через неделю, названа память 8/256.')},
  'Две публикации об одной модельной линейке; первая комплектация памяти не установлена.'),
 ('ugreen-max5c','UGREEN HiTune Max5c',r'\bHiTune\s+Max5c\b',{
  1436:('recommendation',True,'Рекомендация со ссылкой на собственный обзор.'),
  1003:('background',False,'Предшественник при предложении Studio Pro; отдельного положительного предложения Max5c нет.')},
  'Повтор названия — не обязательно повтор рекомендации.'),
 ('ugreen-t3','UGREEN HiTune T3',r'\bHiTune\s+T3\b',{
  8113:('recommendation',False,'Намерение заказать и потестировать.'),
  7672:('secondary_recommendation',True,'Сообщает об испытании и положительном результате, сравнивает с H3.'),
  7366:('recommendation',False,'Повторная рекомендация без нового заявления о личном тесте.')},
  'H3 — отдельная модель; намерение заказа не равно покупке.'),
 ('xiaomi-airpump2','Xiaomi Mijia Air Pump 2',r'\bAir\s+Pump\s+2\b',{
  4166:('recommendation',False,'Сам использует Air Pump 1S; Pump 2 — новое предложение.'),
  1938:('recommendation',False,'Предлагает новую версию; многолетнее использование относится к старому насосу с microUSB.')},
  'Оборот «которым пользуюсь» не приписан автоматически Pump 2: ниже автор противопоставляет старый насос и возможный заказ нового.'),
 ('redmi-buds3lite','Xiaomi Redmi Buds 3 Lite',r'\bRedmi\s+Buds\s+3\s+Lite\b',{
  7145:('recommendation',False,''),6421:('recommendation',False,'Совет выбирать Global Version, несколько комплектаций.')},
  'Характеристики пересказаны автором; здесь не проверяются по производителю.'),
 ('ugreen-studiopro','UGREEN Studio Pro',r'\bUGREEN\s+Studio\s+Pro\b',{
  1555:('recommendation',False,'Представлены как новые.'),1003:('recommendation',False,'Снова названа новой моделью; сравнение с Max5c.')},
  'Повтор обозначения «новая» через несколько месяцев не доказывает обман: возраст модели относителен.')
])
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
                       'recommendation_origin':'author' if role in ('recommendation','secondary_recommendation') else 'not_counted',
                       'review_basis':'saved_author_post; no merchant page opened',
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
