#!/usr/bin/env python3
"""Exact data graphic; no inferred alcohol, sleep or online-presence variables."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'summary.json').read_text());r=json.loads((ROOT/'reactions-summary.json').read_text())
BG='#f5f0e6';INK='#163b37';MUTED='#66736a';TEAL='#167969';ORANGE='#d28347';WINE='#a84048';PALE='#e6b8b5';LINE='#d7d0bf'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':INK,'axes.facecolor':BG,'svg.fonttype':'none'})
fig=plt.figure(figsize=(16,23),facecolor=BG)
def txt(x,y,t,size=14,weight='normal',color=INK,**kw):return fig.text(x,y,t,fontsize=size,fontweight=weight,color=color,va='top',**kw)
def rule(y):fig.add_artist(plt.Line2D([.065,.935],[y,y],transform=fig.transFigure,color=LINE,lw=1))
def tag(y,n,title,subtitle):
    txt(.065,y,n,13,'bold',ORANGE);txt(.105,y+.002,title,23,'bold');txt(.105,y-.028,subtitle,12,color=MUTED)
def clean(ax):
    for sp in ax.spines.values():sp.set_visible(False)
    ax.set_axisbelow(True);ax.tick_params(length=0,pad=8)
txt(.065,.973,'EXLER  /  ПОЛГОДА ПО МИНУТАМ',13,'bold',TEAL)
txt(.065,.944,'Отложка закончилась.\nАлекс ещё здесь.',45,'bold',linespacing=1.08)
txt(.066,.887,'23 марта — 22 сентября 2026  ·  1 125 обсуждений  ·  время на часах сайта',13,color=MUTED)
cards=[(.065,'1 753','временные отметки ответов'),(.365,'22:13','медиана последнего ответа¹'),(.665,'117','вечерних возвращений')]
for x,value,cap in cards:
    fig.add_artist(FancyBboxPatch((x,.817),.27,.049,boxstyle='round,pad=0.012,rounding_size=0.006',transform=fig.transFigure,facecolor='#e6eadd',edgecolor='none'))
    txt(x+.009,.858,value,31,'bold',TEAL);txt(x+.009,.828,cap,11,color=MUTED)
tag(.783,'01','Алекс вышел, стендалон остался','Два разных ритма. Доля всех публикаций и ответов в каждый час, %')
ax=fig.add_axes([.082,.615,.84,.126]);clean(ax)
h=np.arange(24);cp=np.array(s['hourly_comments'])/s['comments_total']*100;pp=np.array(s['hourly_publications'])/1122*100
ax.axvspan(21.5,23.5,color='#e4e8dc',zorder=0)
ax.bar(h-.18,pp,.34,color=ORANGE,label='Публикации · 1 122',zorder=3)
ax.bar(h+.18,cp,.34,color=TEAL,label='Ответы · 1 753',zorder=3)
ax.set(xlim=(-.65,23.7),ylim=(0,19),xticks=[0,4,8,10,12,14,16,18,20,22,23],yticks=[0,5,10,15])
ax.set_xticklabels(['00','04','08','10','12','14','16','18','20','22','23'],fontsize=11);ax.tick_params(axis='y',labelsize=10)
ax.grid(axis='y',color=LINE,lw=.6);ax.legend(loc='upper left',frameon=False,fontsize=12,ncol=2)
ax.text(21.6,17.5,'ВТОРАЯ\nСМЕНА',color=TEAL,fontweight='bold',fontsize=10,ha='left',va='top')
txt(.083,.592,'49 дней',21,'bold',ORANGE);txt(.235,.589,'105 постов после последнего ответа;\n97 из них на ровной сетке.',12)
txt(.59,.592,'122 дня',21,'bold',TEAL);txt(.752,.589,'ответы продолжались\nпосле последнего поста.',12)
txt(.083,.553,'¹ По 171 дню с ответами. Ещё 13 дней без найденных ответов не превращены в «уход».',11,color=MUTED)
rule(.536)
tag(.519,'02','Вернулся раздать послевкусие','Возврат с 18:00 после паузы ≥ 3 часов между ответами в тот же день')
ax=fig.add_axes([.087,.37,.53,.098]);clean(ax)
hours=list(range(18,24));values=[r['returns']['hours'].get(str(h),0) for h in hours]
colors=[ORANGE]*4+[TEAL]*2;ax.bar(hours,values,.64,color=colors,zorder=3)
ax.set(xlim=(17.4,23.6),ylim=(0,54),xticks=hours,yticks=[0,20,40]);ax.set_xticklabels([f'{h}:00' for h in hours],fontsize=11);ax.tick_params(axis='y',labelsize=10);ax.grid(axis='y',color=LINE,lw=.6)
for h,v in zip(hours,values):ax.text(h,v+1.5,str(v),ha='center',va='bottom',fontsize=16,fontweight='bold')
txt(.69,.465,'75 из 117',29,'bold',TEAL);txt(.69,.43,'возвращений — после 22:00\nв пределах тех же суток.',13)
txt(.69,.392,'16 из 117',20,'bold',WINE);txt(.69,.369,'начинаются с резкого ответа.\nОстальные 101 — без этой метки.',11)
txt(.087,.343,'«Вторая смена: читатель ещё не знает, как он неправ».',14,weight='bold')
txt(.087,.326,'Вымышленная подпись. Занятия автора в промежутках неизвестны.',10.5,color=MUTED)
rule(.307)
tag(.29,'03','Час повышенной раздражительности?','Все 1 749 текущих ответов прочитаны. 39 строгих случаев входят в 193 широких.')
ax=fig.add_axes([.15,.119,.775,.123]);clean(ax)
bands=[r['bands'][1],r['bands'][2],r['bands'][3],r['bands'][0]];ys=np.arange(4)
for y,b in zip(ys,bands):
    ax.barh(y,b['broad_pct'],.52,color=PALE,zorder=2,hatch='///' if y==3 else None,edgecolor=LINE if y==3 else 'none')
    ax.barh(y,b['strict_pct'],.52,color=WINE,zorder=3)
    label=f"{b['broad']}/{b['n']} · {b['broad_pct']:.1f}%".replace('.',',')
    detail=f"личное: {b['strict']}/{b['n']} · {b['strict_pct']:.1f}%".replace('.',',')
    ax.text(25,y-.10,label,fontsize=12,va='center',fontweight='bold');ax.text(25,y+.18,detail,fontsize=10.5,va='center',color=MUTED)
ax.set(xlim=(0,38),ylim=(3.6,-.65),xticks=[0,5,10,15,20,25],yticks=ys)
ax.set_yticklabels(['08–12','12–18','18–24','00–08*'],fontsize=12);ax.grid(axis='x',color=LINE,lw=.6);ax.tick_params(axis='x',labelsize=10)
ax.text(.0,1.04,'Резкость и насмешки',transform=ax.transAxes,color='#ad7b7d',fontsize=11)
ax.text(.40,1.04,'■ Персональное унижение',transform=ax.transAxes,color=WINE,fontsize=11)
txt(.083,.102,'Вечером 14,4% против 9,5% днём. Для строгого критерия перевес менее устойчив.',12,'bold')
txt(.083,.082,'* Всего 22 ответа; пять резких — в двух датах. Ночной «час срыва» по ним не определяется.',10.5,color=MUTED)
rule(.068)
txt(.065,.055,'«Декантер в модель не вошёл: отказался раскрывать часовой пояс».',13,'bold',TEAL)
txt(.065,.036,'Вымышленная реплика. Данные описывают время и текст ответов; причины пауз и употребление алкоголя не установлены.\nОхват: лента полугодия + 3 старые ветки из архива. Четыре архивные метки учтены только во времени. Источники и коды — в отчёте.',9.3,color=MUTED,linespacing=1.5)
fig.savefig(ROOT/'comment-clock.svg',facecolor=BG)
fig.savefig(ROOT/'exler-comment-clock.png',dpi=200,facecolor=BG)
print(ROOT/'exler-comment-clock.png')
