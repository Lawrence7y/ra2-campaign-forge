import csv,os,re,collections,json
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
with open(COV,'r',encoding='utf-8-sig',newline='') as f: rows=[r for r in csv.reader(f,delimiter='\t')]
if rows and rows[0][0]=='entry,subsystem': rows=rows[1:]
with open(ATL,'r',encoding='utf-8',newline='') as f: atl={r[0].lower():r for r in csv.reader(f,delimiter='\t') if r}
s10=[r for r in rows if len(r)>=8 and r[1]=='S10' and r[0].lower() in atl]
print('S10',len(s10))
cls=collections.Counter()
for r in s10:
 n=r[2]; c=n.split('::')[0] if '::' in n else '(none)'; cls[(r[4],c)]+=1
print('\nCLASS COUNTS TOP')
for (g,c),v in sorted(cls.items(), key=lambda x:(-x[1],x[0])):
 if v>=2: print(g,c,v)
terms=['ROF','rof','Ready','Fire','Cooldown','CoolDown','Scatter','Guard','Hunt','Queue','Production','Produce','Build','Place','Spend','Money','Credit','CanBuild','GetBuildable','Weapon','Ammo','Reload','Mission','TechnoClass','BuildingClass','HouseClass','FootClass','InfantryClass','UnitClass','AircraftClass']
print('\nTERMS IN S10 NAMES/SEMANTICS')
for term in terms:
 hits=[r for r in s10 if term.lower() in (r[2]+' '+r[3]).lower()]
 print(term,len(hits),'proved',sum(1 for r in hits if r[4]=='[已证]'))
print('\nALL S10 NONPROVED NAMED')
for r in s10:
 if r[4]!='[已证]' and r[2] and not r[2].startswith('sub_'):
  print('\t'.join([r[0],r[4],r[2],r[3][:180],atl[r[0].lower()][1]]))
