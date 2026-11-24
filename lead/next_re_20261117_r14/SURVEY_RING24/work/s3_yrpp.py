
import json,collections,re,time
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
YR=ROOT/'YRpp'
t0=time.time()
files=[]
for p in YR.rglob('*'):
    if p.is_file() and p.suffix.lower() in ('.h','.hpp','.cpp') and '.git' not in p.parts:
        files.append(p)
BIND=re.compile(r'\b(CALL|JMP_THIS|JMP_STD|THISCALL|JMP)\s*\(\s*(0x[0-9A-Fa-f]{5,8})\s*\)')
CLASS=re.compile(r'^\s*(?:class|struct)\s+(?:\w+\s+)*(?P<n>[A-Za-z_]\w*)')
bindings=collections.defaultdict(list)   # entry -> [[file,line,macro,class]]
class_addrs=collections.defaultdict(set) # class -> set of absolute addrs
nb=0
for p in files:
    txt=p.read_text(encoding='utf-8',errors='replace').splitlines()
    cur=None
    for i,l in enumerate(txt):
        m=CLASS.match(l)
        if m and not l.strip().startswith('//') : cur=m.group('n')
        for mm in BIND.finditer(l):
            nb+=1
            e=int(mm.group(2),16)
            bindings[e].append([str(p.relative_to(ROOT)),i+1,mm.group(1),cur])
        if cur:
            for hm in re.finditer(r'0x([0-9A-Fa-f]{5,8})u?', l):
                v=int(hm.group(1),16)
                if 0x800000<=v<0xB80000: class_addrs[cur].add(v)
print('bindings',nb,'distinct entries',len(bindings),'classes w/ addrs',len(class_addrs),'t=%.1f'%(time.time()-t0))
top=sorted(bindings.items(), key=lambda kv:-len(kv[1]))[:5]
print('sample', [(hex(k),v[0]) for k,v in top])
json.dump({'bindings':{hex(k):v for k,v in bindings.items()},
           'class_addrs':{k:sorted(v) for k,v in class_addrs.items()}},
          open(OUT/'work'/'yrpp.json','w'),indent=0)
print('saved', (OUT/'work'/'yrpp.json').stat().st_size)
