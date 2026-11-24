# -*- coding: utf-8 -*-
"""Final: every CALL/JMP_THIS/JMP_STD line in YRpp cross-referenced to S01 entries (incl. +IB form)."""
import os,re
YRPP=r"D:\Project\ra2-campaign-forge\YRpp"
S01=['00409030','00409100','004091C0','004092F0','00409320','00409360','004093F0','00409880','00409C40','00409D90','00430250','0048C8B0','0048CCC0','004E2450','004E2460','004E24A0','004F1AA0','0052FC20','00554400','0055AF60','0055CFD0','0055D360','0055E420','0055F1E0','005A89D0','005B1D90','005B1E40','005CAF70','005CAFC0','005D2410','005D2530','005D5870','005D5880','005D5890','0063D810','00643E80','00646DF0','00647040','006470F0','006471A0','006521C0','006640E0','00697AD0','0069AE90','0069BAB0','006BB9A0','007240B0','007241A0','00724200','00732CA0','00734120','00734210','007CD80F']
forms={}
for e in S01:
  for f in [e, e.lstrip('0'), e.lower(), '0x'+e, '0x'+e.lstrip('0'), hex(int(e,16)), hex(int(e,16)+0x400000)]:
    forms[f.upper()]=e
matches={e:[] for e in S01}
binding_lines=[]
for root,dirs,files in os.walk(YRPP):
  for fn in files:
    if not re.search(r'\.(h|hpp|cpp|c|cc)$',fn,re.I): continue
    fp=os.path.join(root,fn)
    try: lines=open(fp,encoding='utf-8',errors='replace').read().splitlines()
    except: continue
    for ln,line in enumerate(lines,1):
      if re.search(r'\b(CALL|JMP_THIS|JMP_STD)\s*\(',line):
        binding_lines.append((os.path.relpath(fp,YRPP),ln,line.strip()))
        for tok in re.findall(r'0[xX][0-9A-Fa-f]+',line):
          key=tok.upper()
          if key in forms: matches[forms[key]].append((os.path.relpath(fp,YRPP),ln,line.strip()))
print('total CALL/JMP_THIS/JMP_STD binding lines in YRpp:',len(binding_lines))
print('\nS01 entries with a YRpp address binding:')
for e in S01:
  if matches[e]:
    u=list(dict.fromkeys(matches[e]))
    print(f'  {e}:')
    for f,ln,line in u: print(f'     {f}:{ln}: {line}')
