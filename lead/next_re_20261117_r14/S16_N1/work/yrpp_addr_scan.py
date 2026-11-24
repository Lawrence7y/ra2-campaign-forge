# -*- coding: utf-8 -*-
import os,re
b=r"D:\Project\ra2-campaign-forge\YRpp"
pats=[re.compile(r'(?:(?:CALL|JMP_THIS|JMP_STD|SET_REG32)\s*\(\s*)?0x(5[34][0-9A-Fa-f]{4}|6[5C][0-9A-Fa-f]{4}|71[0-9A-Fa-f]{4})\b')]
targets={x.lower() for x in ["53A6C0","53D8E0","53DDA0","65E660","71AB60","430BA0","6CE240","6CE280","6CE2D0","6CE320","6CE270","53A0E0","53AE50","539EB0","53B410","53AE00"]}
hits={a:[] for a in targets}
for root,dirs,files in os.walk(b):
  dirs[:] = [d for d in dirs if d!='.git']
  for f in files:
    p=os.path.join(root,f)
    try:s=open(p,encoding='utf8',errors='ignore').read()
    except:continue
    for m in re.finditer(r'0x([0-9A-Fa-f]{6})\b',s):
      a=m.group(1).lower()
      if a in targets:
        # get 250 chars before, strip tags
        ctx=re.sub(r'<[^>]*>',' ',s[max(0,m.start()-400):m.start()+80])
        ctx=re.sub(r'\s+',' ',ctx)[-300:]
        hits[a].append((p.replace(b,''),ctx))
for a in sorted(targets):
  print("=== "+a.upper()+" hits="+str(len(hits[a])))
  for p,c in hits[a][:5]: print("  ",p,"::",c[:250])
