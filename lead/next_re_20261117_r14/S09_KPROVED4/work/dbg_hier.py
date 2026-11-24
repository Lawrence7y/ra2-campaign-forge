import json,sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4\work')
from s09lib import u32,cstr,is_ro
from pathlib import Path
EV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4\EVIDENCE')
cols=[]
with (EV/'VTABLES_ALL.tsv').open(encoding='utf-8') as f:
    next(f)
    for ln in f:
        p=ln.rstrip('\n').split('\t')
        cols.append(dict(vt=int(p[0],16),col=int(p[1],16),td=int(p[2],16),name=p[3]))
# For a set of names, print CHD info
targets=['.?AVDisplayClass@@','.?AVMouseClass@@','.?AVPowerClass@@','.?AVRadarClass@@',
         '.?AVScrollClass@@','.?AVSidebarClass@@','.?AVTabClass@@','.?AVGadgetClass@@',
         '.?AVControlClass@@','.?AVListClass@@','.?AVColorListClass@@']
td_by_name={}
for c in cols: td_by_name.setdefault(c['name'],c['td'])
for nm in targets:
    td=td_by_name.get(nm)
    c=next((x for x in cols if x['name']==nm),None)
    if not c: print(nm,'NO COL'); continue
    col=c['col']; chd=u32(col+0x10)
    nb=u32(chd+8) if chd else None; pba=u32(chd+0xC) if chd else None
    bases=[]
    if pba and is_ro(pba):
        for i in range(min(nb or 0,6)):
            bcd=u32(pba+4*i)
            btd=u32(bcd) if bcd else None
            bases.append(cstr(btd+8) if btd else None)
    print('%-30s td=%08X col=%08X chd=%08X nb=%s bases=%s'%(nm,td,col,chd,nb,bases))
