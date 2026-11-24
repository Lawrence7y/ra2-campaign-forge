# -*- coding: utf-8 -*-
import os,re
b=r"D:\Project\ra2-campaign-forge"
roots=[r"D:\Project\ra2-campaign-forge\docs\re", r"D:\Project\ra2-campaign-forge\YRpp", r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14", r"D:\Project\ra2-campaign-forge\re_atlas"]
addrs = ["53A6C0","53D8E0","53DDA0","65E660","71AB60","430BA0","6CE240","6CE270","6CE280","6CE2C0","6CE2D0","6CE320","53A0E0","53AE50","53B410","539EB0"]
pats = {a:re.compile(r'0[xX]0*'+a+r'\b|(?<![0-9A-Fa-f])0*'+a+r'(?![0-9A-Fa-f])',re.I) for a in addrs}
hits = {a:[] for a in addrs}
for root0 in roots:
  if not os.path.isdir(root0): continue
  for root,dirs,files in os.walk(root0):
    dirs[:] = [d for d in dirs if d not in ('.git','venv','node_modules','_backup','M4_merge','M5_merge')]
    for f in files:
        if not f.lower().endswith(('.md','.txt','.tsv','.py','.json','.h','.cpp')): continue
        p=os.path.join(root,f)
        try: s=open(p,encoding='utf8',errors='ignore').read()
        except: continue
        for a,pat in pats.items():
            c=len(pat.findall(s))
            if c: hits[a].append((p.replace(b,''),c))
for a in addrs:
    print("=== "+a+" hits="+str(sum(c for _,c in hits[a])))
    for p,c in hits[a][:12]: print("  ",c,p)
