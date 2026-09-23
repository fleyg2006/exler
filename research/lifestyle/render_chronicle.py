"""Render a factual editorial chronology. Pillow + Matplotlib, no income interpolation."""
from pathlib import Path
from io import BytesIO
import json,sys
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'cases.json' if (ROOT/'cases.json').exists() else ROOT.parent/'deliverable/research/lifestyle/cases.json'
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'exler-chronicle.png'
cs={c['id']:c for c in json.loads(DATA.read_text())}
W,H,S=1600,2310,2
PAPER='#F5F1E8';INK='#242823';MUTED='#64685F';RED='#873D44';GREEN='#397362';LINE='#DAD7CC';WHITE='#FFFDF8'
im=Image.new('RGB',(W*S,H*S),PAPER);d=ImageDraw.Draw(im)
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def f(n,b=False):return ImageFont.truetype(BOLD if b else REG,round(n*S))
def text(x,y,t,n=24,c=INK,b=False):d.text((x*S,y*S),t,font=f(n,b),fill=c)
def line(x,y,x2,y2,c=LINE,w=1):d.line((x*S,y*S,x2*S,y2*S),fill=c,width=w*S)
def box(x,y,w,h,c=WHITE):d.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S),radius=14*S,fill=c)
def para(x,y,t,n=22,width=420,c=INK,b=False):
 for p in t.split('\n'):
  row=''
  for word in p.split():
   s=(row+' '+word).strip()
   if d.textlength(s,font=f(n,b))>width*S and row:text(x,y,row,n,c,b);y+=n*1.35;row=word
   else:row=s
  text(x,y,row,n,c,b);y+=n*1.35
 return y
text(56,32,'EXLER  /  ПОКУПКИ, ВКУС И ДЕНЬГИ',21,MUTED)
text(52,72,'ХРОНИКА ДЕГРАДАЦИИ',73,INK,True)
text(58,169,'Цена меняется. Экспертная уверенность остаётся.',29,RED)
text(58,220,'2007–2026  •  60 карточек  •  92 первоисточника  •  срез 23 сентября 2026',21,MUTED)
line(56,272,1544,272,INK,2)
text(56,300,'01  ОБОЗРЕВАТЕЛЬ С ЛИМИТОМ',32,INK,True)
for x,year,big,body,cid in [
 (56,'2007','16 800 ₽','HTC куплен на следующий день. Тысяча рублей переплаты ради скорости.','LIFE-033'),
 (564,'2022','Вернул флагманы','После начала войны вернул дорогие Samsung: такой бюджет обзоров больше не потянет.','LIFE-019'),
 (1072,'2025','€470 — отказ','Sony XM6: «не потяну». Аренда за €222 тоже не устраивает.','LIFE-039')]:
 box(x,361,472,249);text(x+24,381,year,22,RED,True);text(x+24,420,big,29,INK,True);para(x+24,468,body,21,424);text(x+24,574,cid,16,MUTED)
text(56,646,'02  ИЗ ДЕКАНТЕРА — В ПАКЕТ',32,INK,True)
box(56,706,1040,387);text(81,723,'ЕВРО ЗА БУТЫЛКУ  /  ВЫБРАННЫЕ ПОКУПКИ И ОБЫЧНЫЕ ДИАПАЗОНЫ',17,MUTED)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
fig,ax=plt.subplots(figsize=(10,3.06),dpi=200);fig.patch.set_facecolor(WHITE);ax.set_facecolor(WHITE);fig.subplots_adjust(left=.055,right=.98,bottom=.16,top=.87)
ax.set_xlim(2010.35,2020.4);ax.set_ylim(0,25);ax.set_xticks([2011,2013,2018,2019]);ax.set_xticklabels(['2011','2013','2018','2019'],fontsize=13,fontweight='bold');ax.set_yticks([0,5,10,15,20]);ax.tick_params(length=0,pad=8,colors=MUTED);ax.spines[['top','left','right']].set_visible(False);ax.spines['bottom'].set_color(LINE);ax.grid(axis='y',color=LINE);ax.set_axisbelow(True)
for year,val,label in [(2011,10,'€10'),(2018,3.65,'€3,65')]:
 ax.scatter(year,val,s=100,color=RED,zorder=3);ax.annotate(label,(year,val),xytext=(-10 if year==2018 else 0,16),textcoords='offset points',ha='right' if year==2018 else 'center',fontsize=17,fontweight='bold',color=RED)
for yr,lo,hi in [(2013,14,20),(2019,5,6)]:
 ax.plot([yr,yr],[lo,hi],lw=5,color=RED,solid_capstyle='round');ax.annotate(f'€{lo}–{hi}',(yr,hi),xytext=(13 if yr==2019 else 0,20 if yr==2019 else 12),textcoords='offset points',ha='left' if yr==2019 else 'center',fontsize=17,fontweight='bold',color=RED)
ax.text(2013,11.3,'обычно в Москве',ha='center',fontsize=10,color=MUTED);ax.text(2011,1.15,'La Planta',ha='center',fontsize=10,color=MUTED)
buf=BytesIO();fig.savefig(buf,dpi=200,facecolor=WHITE);plt.close(fig);buf.seek(0);chart=Image.open(buf).convert('RGB').resize((1000*S,306*S),Image.Resampling.LANCZOS);im.paste(chart,(76*S,765*S))
box(1120,706,424,387);text(1146,730,'2025  /  ОТДЕЛЬНАЯ ЕДИНИЦА',17,MUTED);text(1144,777,'€1 / литр',52,RED,True);para(1148,860,'Купил и похвалил пакет белого вина: €5 за 5 литров.',25,364);para(1148,965,'Это проба. Постоянный переход только на пакеты не установлен.',19,364,MUTED)
text(56,1112,'Ряды не соединены: разные вина, страны и единицы. LIFE-001, 003, 005, 006, 008.',18,MUTED)
text(56,1166,'03  РЕАЛЬНЫЕ ПОКУПКИ И ИХ РАЗВЯЗКИ',32,INK,True)
for x,tag,big,body,cid in [
 (56,'ХОЛОДИЛЬНИК','€850 + €50','После ремонта и новой поломки куплен основной холодильник. Аппарат за €130 остался резервным.','LIFE-028'),
 (564,'ЧАСЫ ULTRA','Купил за €260','Выбрал модель 2024 после выхода следующей. €350–360 из обзора — рыночный ориентир, не его чек.','LIFE-044'),
 (1072,'РАБОЧЕЕ КРЕСЛО','Купил за €159','Планировал около €150. После обхода магазинов выбрал IKEA MARKUS.','LIFE-043')]:
 box(x,1228,472,277);text(x+24,1249,tag,18,RED,True);text(x+24,1293,big,35,INK,True);para(x+24,1353,body,21,423);text(x+24,1470,cid,16,MUTED)
text(56,1544,'04  КУПОН КАК СЮЖЕТ',32,INK,True)
text(56,1594,'Уплаченные суммы и найденные альтернативы — по собственным публикациям.',23,MUTED)
for x,tag,paid,paid_note,offer,offer_note,cid in [
 (56,'НОУТБУК  /  ДЕКАБРЬ 2024','€1092','заплатил с купоном','от €1800','его оценка похожей\nконфигурации в Испании','LIFE-047'),
 (564,'ВЕСЫ HUAWEI  /  ОКТЯБРЬ 2025','€86','купил китайскую версию','€199','предложение Amazon;\nза эту цену не стал бы брать','LIFE-042'),
 (1072,'CMF PHONE  /  НОЯБРЬ 2024','€239','купил накануне','€173','позднее найденная цена\nс купоном: поторопился','LIFE-041')]:
 box(x,1644,472,308)
 text(x+24,1664,tag,17,RED,True)
 text(x+24,1705,paid,38,INK,True)
 text(x+24,1760,paid_note,21,MUTED)
 text(x+24,1800,offer,32,RED,True)
 para(x+24,1848,offer_note,20,422,MUTED)
 text(x+24,1920,cid,16,MUTED)
text(56,1971,'Разные площадки, версии и условия покупки. Разница цен не приравнивается к полученной скидке.',18,MUTED)
line(56,2023,1544,2023,LINE,2)
text(56,2054,'Что теперь можно сказать уверенно',25,INK,True)
para(56,2104,'Есть прямые ограничения обзорного бюджета, покупки по акциям и выбор более доступных версий. При этом крупные покупки, поездки и доплаты за удовольствие продолжаются.',24,1440)
text(56,2238,'ДАННЫЕ: github.com/fleyg2006/exler  →  research/lifestyle   •   название сатирическое',18,MUTED)
OUT.parent.mkdir(parents=True,exist_ok=True);im.save(OUT,optimize=True)
print(json.dumps({'path':str(OUT),'width':W*S,'height':H*S,'bytes':OUT.stat().st_size}))
