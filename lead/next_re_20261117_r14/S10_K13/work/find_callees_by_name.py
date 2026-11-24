import csv,re
from pathlib import Path
COV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
with COV.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'))
for pat in ['GetHealth','GetWeapon','FireError','CanFire','GetAmmo','SetAmmo','HasAmmo','Veter','Experien','Promot','Rank','Upgrade','DamageState','ReceiveDamage','GetTotalDamage','SetTargetForPassengers','UpdateThreat','CanFireAt','GetWeaponRange']:
 print('\n###',pat)
 n=0
 for r in rows:
  blob=(r['name']+' '+r['one_line_semantics'])
  if pat.lower() in blob.lower() and r['grade'].strip()=='[已证]':
   print(r['entry'],r['subsystem'],r['grade'],r['name'],'|',r['one_line_semantics'][:120]); n+=1
   if n>=20:break
