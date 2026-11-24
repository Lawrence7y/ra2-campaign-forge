# -*- coding: utf-8 -*-
"""Broad harvest: ALL YRpp (root + ref/yrpp) address macros in 0x770000..0x7E0000."""
import os, re, json
ROOT = r"D:\Project\ra2-campaign-forge"
DIRS = [os.path.join(ROOT,"YRpp"), os.path.join(ROOT,"ref","yrpp")]
MACRO_RE = re.compile(r'\b(JMP_STD|JMP|CALL_STD|CALL|SET_REG|JMP_VFUNC|CALL_VFUNC|VTABLE|INLINE)\s*\(\s*0x([0-9A-Fa-f]{1,8})\b')
hits = {}
for base in DIRS:
    if not os.path.isdir(base): continue
    for root,dirs,files in os.walk(base):
        for fn in files:
            if not fn.lower().endswith(('.h','.hpp','.cpp','.inl','.c')): continue
            path=os.path.join(root,fn)
            try: lines=open(path,encoding='utf-8',errors='replace').read().splitlines()
            except: continue
            for i,line in enumerate(lines):
                for m in MACRO_RE.finditer(line):
                    addr=m.group(2).upper().zfill(8)
                    va=int(addr,16)
                    if not (0x770000<=va<=0x7E0000): continue
                    prev=[]
                    j=i-1
                    while j>=0 and len(prev)<4:
                        s=lines[j].strip()
                        if s: prev.append((j+1,s))
                        j-=1
                    name=None
                    for ln,s in reversed(prev):
                        s2=re.sub(r'//.*$','',s)
                        for nm in re.finditer(r'\b([A-Za-z_]\w*)\s*\(',s2):
                            c=nm.group(1)
                            if c in ('JMP_STD','JMP','CALL_STD','CALL','if','for','while','switch','sizeof','__declspec'): continue
                            name=c; break
                        if name: break
                    rel=os.path.relpath(path,ROOT)
                    hits.setdefault(addr,[]).append((rel,i+1,m.group(1),name,line.strip()))
print("unique addrs in 0x77-0x7E:",len(hits))
for a in sorted(hits):
    names=sorted(set(h[3] for h in hits[a] if h[3]))
    print("0x%s %-28s %s"%(a,",".join(names),[(h[0],h[1]) for h in hits[a]][:2]))
