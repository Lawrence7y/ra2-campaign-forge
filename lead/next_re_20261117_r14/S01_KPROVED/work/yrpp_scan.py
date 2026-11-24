# -*- coding: utf-8 -*-
import os,re
YRPP=r"D:\Project\ra2-campaign-forge\YRpp"
S01=['00409030','00409100','004091C0','004092F0','00409320','00409360','004093F0','00409880','00409C40','00409D90','00430250','0048C8B0','0048CCC0','004E2450','004E2460','004E24A0','004F1AA0','0052FC20','00554400','0055AF60','0055CFD0','0055D360','0055E420','0055F1E0','005A89D0','005B1D90','005B1E40','005CAF70','005CAFC0','005D2410','005D2530','005D5870','005D5880','005D5890','0063D810','00643E80','00646DF0','00647040','006470F0','006471A0','006521C0','006640E0','00697AD0','0069AE90','0069BAB0','006BB9A0','007240B0','007241A0','00724200','00732CA0','00734120','00734210','007CD80F']
# build address forms: with 0x (6 or 8 hex), bare 6/8 hex
hits={e:[] for e in S01}
for root,dirs,files in os.walk(YRPP):
  for fn in files:
    if not re.search(r'\.(h|hpp|cpp|c|cc|txt)$',fn,re.I): continue
    fp=os.path.join(root,fn)
    try: lines=open(fp,encoding='utf-8',errors='replace').read().splitlines()
    except: continue
    for ln,line in enumerate(lines,1):
      # find all hex tokens 6-8 digits (with or without 0x)
      for m in re.finditer(r'(?<![\w])0[xX]([0-9a-fA-F]{6,8})(?![\w])',line):
        h=m.group(1).upper().zfill(8)[-8:]
        e8=None
        for e in S01:
          if e.lstrip('0').upper()==h.lstrip('0').upper() or e==h[-6:].zfill(8): e8=e
        if e8: hits[e8].append((os.path.relpath(fp,YRPP),ln,line.strip()))
      for m in re.finditer(r'(?<![\w])([0-9A-Fa-f]{6})(?![\w])',line):
        h=m.group(1).upper()
        for e in S01:
          if e[-6:]==h: hits[e].append((os.path.relpath(fp,YRPP),ln,line.strip()))
print("YRpp comprehensive hits:")
for e in S01:
  if hits[e]:
    uniq=list(dict.fromkeys(hits[e]))
    print(f"\n{e} ({len(uniq)}):")
    for f,ln,line in uniq[:10]: print(f"  {f}:{ln}: {line}")
# D-41 precedents
print("\n=== D-41 precedent macros ===")
for addr in ['53AF40','595740','599650','539760','53AB50','40B880','5F3E30']:
  found=[]
  for root,dirs,files in os.walk(YRPP):
    for fn in files:
      if not re.search(r'\.(h|hpp|cpp|c|cc)$',fn,re.I): continue
      fp=os.path.join(root,fn)
      try: txt=open(fp,encoding='utf-8',errors='replace').read()
      except: continue
      for ln,line in enumerate(txt.splitlines(),1):
        if re.search(r'0[xX]0*'+addr+r'\b',line,re.I): found.append((os.path.basename(fp),ln,line.strip()))
  print(f" 0x{addr}: {found[:5]}")
