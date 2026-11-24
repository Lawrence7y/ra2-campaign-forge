import csv,re,hashlib
from pathlib import Path
B=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13')
d=B/'coverage_delta.tsv'
lines=[x for x in d.read_text(encoding='utf-8').splitlines() if x.strip()]
L=['DELTA_VALIDATE']
L.append('LINES='+str(len(lines)))
entries=[];names=[];ok=True
for i,line in enumerate(lines,1):
 z=line.split('\t')
 L.append(f'ROW{i}_COLS={len(z)}')
 if len(z)!=9:ok=False;continue
 if not re.fullmatch(r'[0-9A-Fa-f]{8}',z[0]):ok=False;L.append(f'ROW{i}_BAD_ENTRY={z[0]}')
 if not re.fullmatch(r'[已证]|\[已证\]',z[4]): pass
 if z[4]!='[已证]':ok=False;L.append(f'ROW{i}_BAD_GRADE={z[4]}')
 if z[8] not in ('symbolic','behavioral','placeholder'):ok=False;L.append(f'ROW{i}_BAD_KIND={z[8]}')
 if 'sub_' in z[2].lower() or 'slot' in z[2].lower() or 'placeholder' in z[2].lower():ok=False;L.append(f'ROW{i}_PLACEHOLDER={z[2]}')
 ep=B/z[5].split('#')[0]
 if not ep.exists():ok=False;L.append(f'ROW{i}_MISSING_EVIDENCE={ep}')
 else:
  txt=ep.read_text(encoding='utf-8')
  anchor=z[5].split('#')[1] if '#' in z[5] else z[0]
  if anchor not in txt:ok=False;L.append(f'ROW{i}_ANCHOR_MISSING={anchor}')
 entries.append(z[0].lower());names.append(z[2].lower())
L.append('UNIQUE_ENTRIES='+str(len(set(entries))==len(entries)))
L.append('UNIQUE_NAMES='+str(len(set(names))==len(names)))
L.append('NO_PLACEHOLDER='+str(not any(('sub_' in n or 'slot' in n or 'placeholder' in n) for n in names)))
pr=(B/'PROGRESS.md').read_text(encoding='utf-8').splitlines()
L.append('PROGRESS_LINES='+str(len(pr)))
L.append('RESULT='+('PASS' if ok and len(lines)==2 and len(set(entries))==len(entries) and len(set(names))==len(names) and len(pr)<=60 else 'FAIL'))
out=B/'EVIDENCE/DELTA_VALIDATE.txt';out.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
