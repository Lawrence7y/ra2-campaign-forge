# -*- coding: utf-8 -*-
import os,re
base=r"D:\Project\ra2-campaign-forge"
bind={}
for root,dirs,files in os.walk(base+r"\YRpp"):
  dirs[:]=[d for d in dirs if d not in ('.mimosa','.git')]
  for f in files:
    if not f.lower().endswith(('.h','.html','.cpp')):continue
    try:s=open(os.path.join(root,f),encoding='utf8',errors='ignore').read()
    except:continue
    for m in re.finditer(r'0x([0-9A-Fa-f]{6})\b',s): bind.setdefault(int(m.group(1),16),[]).append(f)
SUBS=[0x00430BA0,0x00539EB0,0x0053A0E0,0x0053A6C0,0x0053AE00,0x0053AE50,0x0053B410,
      0x0053D8E0,0x0053DDA0,0x0065E660,0x006CE240,0x006CE270,0x006CE280,0x006CE2C0,
      0x006CE2D0,0x006CE320,0x0071AB60]
for a in SUBS:
  print("%08X"%a, "YRpp-mention=" + str(a in bind), "files=", sorted(set(bind.get(a,[])))[:4])
