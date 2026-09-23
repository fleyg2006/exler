#!/usr/bin/env python3
"""Render the source-based publication-time poster. No generated data or imagery."""
from pathlib import Path
from datetime import datetime, timedelta
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parent
S=json.loads((ROOT/'summary.json').read_text())
R=json.loads((ROOT/'publications.json').read_text())
D=json.loads((ROOT/'daily.json').read_text())
BG='#F4F0E7'; INK='#1B302F'; MUTED='#61716C'; GRID='#D9DFD4'
TEAL='#226C62'; LIGHT='#82ACA1'; ORANGE='#DB743F'; WINE='#8B3C54'; WHITE='#FFFCF5'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':INK,
    'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,
    'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
    'axes.spines.bottom':False,'axes.facecolor':BG,'figure.facecolor':BG,
    'svg.fonttype':'none'})
fig=plt.figure(figsize=(16,23),dpi=200)

def txt(x,y,text,size=12,color=INK,weight='normal',**kwargs):
    return fig.text(x,y,text,fontsize=size,color=color,fontweight=weight,**kwargs)
def card(x,y,w,h):
    fig.add_artist(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.006',
        transform=fig.transFigure,facecolor=WHITE,edgecolor='none',zorder=-1))
def panel_label(y,n,title,sub):
    txt(.055,y,n,13,ORANGE,'bold');txt(.094,y,title,20,INK,'bold')
    txt(.094,y-.016,sub,11,MUTED)
def simple(ax):
    ax.set_axisbelow(True);ax.grid(axis='y',color=GRID,lw=.7)
    ax.tick_params(length=0,pad=7)

txt(.055,.969,'АЛЕКС УШЁЛ. САЙТ ПИШЕТ.*',33,INK,'bold')
txt(.057,.946,'Отложка на смене. У декантера — свой график.*',19,WINE)
txt(.057,.927,'23 марта — 22 сентября 2026  /  время, указанное на сайте  /  вся доступная лента',11,MUTED)
for x,val,label,detail in [
    (.062,'1 122','ПУБЛИКАЦИИ','6,1 в среднем за календарный день'),
    (.370,'94,6%','НА СЕТКЕ ИЗ 10 МИНУТ','1 061 метка: :00, :10, :20, :30, :40, :50'),
    (.677,'61','ПУБЛИКАЦИЯ ВНЕ ЭТОЙ СЕТКИ','Из них 38 — анонсы разделов сайта')]:
    card(x,.847,.262,.062)
    txt(x+.011,.878,val,31,TEAL,'bold')
    txt(x+.012,.862,label,10,INK,'bold')
    txt(x+.012,.850,detail,9,MUTED)

panel_label(.816,'01','ВЕЩАНИЕ ПРОДОЛЖАЕТСЯ','Все публикации по часам: светлые — сетка из 10 минут; оранжевые — остальные метки')
ax=fig.add_axes([.071,.658,.875,.130])
hrs=np.arange(24);counts=np.array([h['posts'] for h in S['hourly']])
rest=np.array(S['grid_models']['every_ten_minutes']['remaining_hourly'])
ax.bar(hrs,counts-rest,width=.76,color=LIGHT,zorder=3)
ax.bar(hrs,rest,bottom=counts-rest,width=.76,color=ORANGE,zorder=3)
ax.set_xlim(-.7,23.7);ax.set_ylim(0,233)
ax.set_xticks(hrs);ax.set_xticklabels([f'{h:02}' for h in hrs],fontsize=10)
ax.set_yticks([0,50,100,150,200]);simple(ax)
for h in (9,10,11,12,13,18):ax.text(h,counts[h]+5,str(counts[h]),ha='center',fontsize=11,fontweight='bold')
ax.text(.15,183,'До 08:00 — всего 2 поста',fontsize=13,color=MUTED)
ax.text(.15,160,'Таймер тоже хочет поспать.*',fontsize=11,color=MUTED,style='italic')
ax.text(15.6,193,'20:00–24:00: всего 21 пост',fontsize=14,fontweight='bold',color=WINE)
ax.text(15.6,170,'1,9% от всей ленты',fontsize=12,color=WINE)
ax.text(15.6,141,'«Я уже с ВПБ. Это отложка».*',fontsize=14,color=WINE,fontweight='bold')
txt(.074,.637,'Ровная сетка — рабочий признак отложки по замечанию пользователя, не журнал планировщика.',10.4,INK)
txt(.074,.622,'По всей ленте последний пост дня — в медиане 17:30. Время ухода автора из этого не следует.',10,MUTED)

panel_label(.590,'02','НЕДЕЛЯ СТРОГОГО РЕЖИМА','Слева — плотность по часам; справа — среднее число публикаций за такой день недели')
heat=np.array([w['hourly_counts'] for w in S['weekday']],float)
heat=heat/np.array([w['calendar_days'] for w in S['weekday']])[:,None]
cmap=LinearSegmentedColormap.from_list('editorial',[BG,'#CADAC8','#7AB59D',TEAL,INK])
axh=fig.add_axes([.08,.438,.589,.124])
im=axh.imshow(heat,aspect='auto',cmap=cmap,vmin=0,vmax=1.5,interpolation='nearest')
axh.set_xticks(range(0,24,2));axh.set_xticklabels([f'{h:02}' for h in range(0,24,2)],fontsize=10)
axh.set_yticks(range(7));axh.set_yticklabels([w['label'] for w in S['weekday']],fontweight='bold',fontsize=12)
axh.tick_params(length=0,pad=8)
axh.set_xticks(np.arange(-.5,24,1),minor=True);axh.set_yticks(np.arange(-.5,7,1),minor=True)
axh.grid(which='minor',color=BG,linewidth=2);axh.tick_params(which='minor',length=0)
axh.add_patch(Rectangle((17.5,3.5),1,1,fill=False,edgecolor=ORANGE,lw=2.4))
axh.add_patch(Rectangle((8.5,5.5),1,1,fill=False,edgecolor=ORANGE,lw=2.4))
cax=fig.add_axes([.083,.420,.283,.006])
cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.5,1,1.5]);cb.outline.set_visible(False)
cb.ax.tick_params(length=0,labelsize=8)
txt(.388,.417,'Постов на день в часовой ячейке',9,MUTED)
axb=fig.add_axes([.735,.438,.19,.124])
rates=[w['posts_per_day'] for w in S['weekday']]
axb.barh(range(7),rates,height=.65,color=[ORANGE if i==4 else TEAL if i<5 else LIGHT for i in range(7)])
axb.invert_yaxis();axb.set_ylim(6.5,-.5);axb.set_xlim(0,8.5)
axb.set_yticks(range(7));axb.set_yticklabels([w['label'] for w in S['weekday']],fontsize=10)
axb.set_xticks([0,2,4,6,8]);axb.tick_params(length=0,pad=6,labelsize=9)
for i,v in enumerate(rates):axb.text(v+.13,i,f'{v:.1f}'.replace('.',','),va='center',fontsize=11,fontweight='bold')
txt(.081,.394,'Пятница, 18:00: песенка.',13,WINE,'bold')
txt(.081,.380,'23 из 25 — ровно в 18:00. Песенка играет, автора не требует.*',9.8,MUTED)
txt(.680,.394,'Воскресенье, 09:00: Ali.',12,TEAL,'bold')
txt(.680,.380,'24 из 25 выпусков — по будильнику.*',9,MUTED)

panel_label(.347,'03','ОТЛОЖКА И ТО, ЧТО НЕ ПО СЕТКЕ','1 061 светлая точка — шаг 10 минут; 61 оранжевая — другие минуты. Весь ряд, без исключений')
axc=fig.add_axes([.078,.174,.866,.145])
dates=[datetime.fromisoformat(r['published_at']).replace(hour=0,minute=0) for r in R]
hours=[r['minute_of_day']/60 for r in R]
axc.axhspan(20,24,color='#EBDCE0',zorder=0)
axc.axhspan(8,18,color='#E4EADD',zorder=0)
for d in D:
    if d['weekday']>=5:
        x=datetime.fromisoformat(d['date']);axc.axvspan(x,x+timedelta(days=1),color='white',alpha=.3,lw=0)
on=[i for i,r in enumerate(R) if r['minute']%10==0];off=[i for i,r in enumerate(R) if r['minute']%10!=0]
axc.scatter([dates[i] for i in on],[hours[i] for i in on],s=10,alpha=.65,c=LIGHT,linewidths=0,zorder=2)
axc.scatter([dates[i] for i in off],[hours[i] for i in off],s=26,alpha=.95,c=ORANGE,linewidths=.3,edgecolors=BG,zorder=3)
axc.set_ylim(-.65,24);axc.set_xlim(datetime(2026,3,22),datetime(2026,9,23))
axc.set_yticks([0,4,8,12,16,20,24]);axc.set_yticklabels(['00:00','04:00','08:00','12:00','16:00','20:00','24:00'],fontsize=9)
ticks=[datetime(2026,m,1) for m in range(4,10)]
axc.set_xticks(ticks);axc.set_xticklabels(['1 апр','1 мая','1 июн','1 июл','1 авг','1 сен'],fontsize=10)
simple(axc);axc.grid(axis='x',color=GRID,lw=.7)
axc.annotate('20 июля, 00:20 — пост о футболе',xy=(datetime(2026,7,20),1/3),xytext=(datetime(2026,6,3),4.5),
    color=WINE,fontsize=10,arrowprops={'arrowstyle':'-','color':WINE,'lw':1},
    bbox={'facecolor':BG,'edgecolor':'none','pad':3},zorder=4)
axc.text(datetime(2026,3,26),4.9,'Между постами жизнь не видна.',fontsize=12,color=MUTED,style='italic')

panel_label(.139,'04','ЧАСЫ УХОДА — НЕ ВЫЧИСЛЕНЫ','Медиана последней оставшейся публикации дня меняется вместе с фильтром')
for x,val,lab,sub in [(.08,'17:30','Все публикации','184 дня с записями'),
                      (.34,'16:30','Убраны :00 и :30','Осталось 140 дней'),
                      (.60,'11:51','Убран шаг 10 минут','Осталось 55 дней')]:
    txt(x,.086,val,29,TEAL if x<.6 else ORANGE,'bold')
    txt(x,.070,lab,11,INK,'bold');txt(x,.056,sub,10,MUTED)
txt(.08,.040,'Это разные выборки дней. Ни 17:30, ни 11:51 не означают «перестал писать» или «начал пить».',10,WINE)

txt(.057,.022,'* Заголовок и реплики про ВПБ, декантер и таймер — сатира. Неровное время тоже не гарантирует ручную публикацию.',8.6,MUTED)
txt(.057,.012,'Источник: exler.es/blog/ · 24 страницы ленты · 581 метка совпала с БД · Часовой пояс сайта явно не установлен · EXLER / 23.09.2026',8.3,MUTED)

fig.savefig(ROOT/'exler-publication-clock.png',dpi=200,facecolor=BG)
fig.savefig(ROOT/'publication-clock.svg',facecolor=BG)
print('Rendered',ROOT/'exler-publication-clock.png')
