"""Extract address->name evidence from re_atlas KB markdown files.
Looks for table rows containing a hex address 0x0040xxxx..0x0045xxxx in my slice
and a name token in **bold** or `backtick` within the same row.
"""
import os, re, json
HERE=os.path.dirname(os.path.abspath(__file__))
PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
KB=os.path.join(PROJECT,'re_atlas','kb')
ADDR_RE=re.compile(r'0x(004[0-5][0-9A-Fa-f]{4})')
NAME_BOLD=re.compile(r'\*\*([^*`|]{2,60})\*\*')
NAME_TICK=re.compile(r'`([^`|]{2,60})`')
FILES=['00_global_skeleton.md','10_map_triggers.md','11_class_layouts.md','20_vtable_contract.md',
       '21_swizzle_and_object_fields.md','22_abstractclass_vtable_slots.md','30_ini_subsystem.md']
out={}
for fn in FILES:
    path=os.path.join(KB,fn)
    if not os.path.exists(path): continue
    for ln,line in enumerate(open(path,encoding='utf-8',errors='replace'),1):
        am=ADDR_RE.search(line)
        if not am: continue
        addr=int(am.group(1),16)
        # collect name candidates: prefer first bold, else code ticks that look like identifiers
        cands=NAME_BOLD.findall(line)+NAME_TICK.findall(line)
        # filter out addresses/disasm fragments
        good=[]
        for c in cands:
            c=c.strip()
            if re.match(r'^0x[0-9A-Fa-f]+$',c): continue
            if re.match(r'^[\d\s;,\-]+$',c): continue
            if len(c)>1 and re.search(r'[A-Za-z_]{2}',c):
                good.append(c)
        out.setdefault(addr,[]).append(dict(file=fn,line=ln,cands=good[:4],raw=line.strip()[:160]))
with open(os.path.join(HERE,'kb_names.json'),'w',encoding='utf-8') as f:
    json.dump({str(k):v for k,v in out.items()},f,ensure_ascii=False,indent=1)
print('addresses with KB refs in slice range:',len(out))
# Focus on vtable slot doc: print clean addr->name
n=0
for a in sorted(out):
    if 0x410000<=a<=0x410600:
        recs=[r for r in out[a] if r['file']=='22_abstractclass_vtable_slots.md']
        if recs:
            print('%08X'%a, recs[0]['cands'], '|', recs[0]['raw'][:100]); n+=1
print('vtable region addresses:',n)
