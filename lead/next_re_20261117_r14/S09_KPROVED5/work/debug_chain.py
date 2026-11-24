import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import rtti_tables, u32, cstr, is_ro

tables = rtti_tables()
cols=[dict(vt=t['vt'],col=t['col'],td=t['td'],name=t['name']) for t in tables]
parent_map={}
for c in cols:
    if c['td'] in parent_map: continue
    col=c['col']; chd=u32(col+0x10)
    if not chd or not is_ro(chd): continue
    nb=u32(chd+8); pba=u32(chd+0xC)
    if not pba or not is_ro(pba) or nb is None or nb<1: continue
    bcd1=u32(pba+0)
    if not bcd1: continue
    btd=u32(bcd1); bn=cstr(btd+8) if btd else None
    parent_map[c['td']]=(c['name'],bn)
td_by_name={}
for c in cols: td_by_name.setdefault(c['name'],c['td'])
print('cols=',len(cols),'parent_map=',len(parent_map),'td_by_name=',len(td_by_name))
for n in ['.?AVMouseClass@@','.?AVDisplayClass@@','.?AVTabClass@@','.?AVPowerClass@@','.?AVRadarClass@@','.?AVScrollClass@@','.?AVSidebarClass@@','.?AVListClass@@','.?AVColorListClass@@','.?AVGaugeClass@@','.?AVTriColorGaugeClass@@','.?AVMapClass@@','.?AVGScreenClass@@','.?AVControlClass@@','.?AVCheckListClass@@','.?AVShapeButtonClass@@','.?AVStaticButtonClass@@','.?AVToolTipManager@@']:
    td=td_by_name.get(n)
    pr=parent_map.get(td) if td else None
    chain=[n]; cur=n; seen={n}
    for _ in range(12):
        td2=td_by_name.get(cur)
        pr2=parent_map.get(td2) if td2 else None
        if not pr2 or not pr2[1] or pr2[1] in seen: break
        cur=pr2[1]; chain.append(cur); seen.add(cur)
    print(n,'td=%s'%td,'parent=',pr,'chain=',' -> '.join(x.replace('.?AV','').replace('@@','') for x in chain))
