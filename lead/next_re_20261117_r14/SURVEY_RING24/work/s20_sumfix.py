
import json,collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows2.json', encoding='utf-8'))
unamb=len(json.load(open(OUT/'work'/'A_unanimous.json', encoding='utf-8')))
# recompute strict A from classification.tsv
import csv
cls=list(csv.DictReader(open(OUT/'EVIDENCE'/'classification.tsv', encoding='utf-8'), delimiter='\t'))
A=sum(1 for r in cls if r['class_PRIMARY']=='A')
B=sum(1 for r in cls if r['class_PRIMARY']=='B')
C=sum(1 for r in cls if r['class_PRIMARY']=='C')
D=sum(1 for r in cls if r['class_PRIMARY']=='D')
AL=sum(1 for r in cls if r['class_loose4']=='A')
rej=sum(1 for r in cls if r['has2_rtti']=='1' and r['n_direct_out']=='0' and int(r['n_livevt'])>0 and r['livevt_valid']=='0')
s=json.load(open(OUT/'work'/'summary.json', encoding='utf-8'))
s['A_primary_strict']=A; s['A_loose']=AL; s['livevt_rejected']=rej
s['totals']=dict(n=len(cls),A=A,B=B,C=C,D=D)
s['note_ring4']='④ 严格档 = direct call（非自环、站点在函数体外）或 livevt 且该 slot 在 g 上全部已装 vtable 中取值一致（无歧义）。④ 宽松档 = 另含 111 行「槽号匹配但 g 上装过多张表、slot 取值不唯一」的 livevt。'
json.dump(s, open(OUT/'work'/'summary.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(s['totals'],ensure_ascii=False), 'looseA',AL,'rejected',rej)
