# -*- coding: utf-8 -*-
import sys,re,os
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
root=Path(r'D:\\Project\\ra2-campaign-forge')
self=root/'lead'/'next_re_20261117_r14'/'S15_K7'
addrs=['006E6310','006F1920','00727AA0']
names=['TagTypeClass::FindOrAllocate','TeamTypeClass::FindOrAllocate','TriggerTypeClass::FindOrAllocate']
exts={'.md','.txt','.tsv','.csv','.json','.h','.cpp','.py'}
roots=[root/'docs'/'re',root/'re_atlas'/'kb',root/'lead'/'next_re_20261117_r14'/'COVERAGE',root/'lead'/'next_re_20261117_r14',root/'YRpp']
seen=set(); files=[]
for r in roots:
 if not r.exists(): continue
 for p in r.rglob('*'):
  try:
   if p.is_file() and p.suffix.lower() in exts and self not in p.parents and p not in seen:
    seen.add(p); files.append(p)
  except Exception: pass
print('scanned_files',len(files))
for a in addrs:
 pats=[re.compile(r'(?<![0-9A-Fa-f])'+a+r'(?![0-9A-Fa-f])',re.I),re.compile(r'0x0*'+a+r'(?![0-9A-Fa-f])',re.I)]
 rows=[]
 for p in files:
  try: txt=p.read_text(encoding='utf-8',errors='replace')
  except Exception: continue
  for i,l in enumerate(txt.splitlines(),1):
   if any(q.search(l) for q in pats): rows.append((str(p.relative_to(root)),i,l.strip()))
 print(f'\\n=== ENTRY {a} hits {len(rows)} ===')
 for pth,i,l in rows[:60]: print(f'{pth}:{i}: {l[:300]}')
for n in names:
 rows=[]
 for p in files:
  try: txt=p.read_text(encoding='utf-8',errors='replace')
  except Exception: continue
  for i,l in enumerate(txt.splitlines(),1):
   if n.lower() in l.lower(): rows.append((str(p.relative_to(root)),i,l.strip()))
 print(f'\\n=== NAME {n} hits {len(rows)} ===')
 for pth,i,l in rows[:40]: print(f'{pth}:{i}: {l[:300]}')
