"""Compute correct ② attribution: for each candidate, enumerate ALL RTTI tables holding
the entry, and determine the deepest common base class via MSVC BaseClassArray (index 0
is the class itself; index 1.. are all bases, flat list). This implements 错源⑯ / M1:
2+ tables at the same slot -> attribute to base-class level; name column must match.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import rtti_tables, tables_holding, u32, cstr, is_ro

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
WORK = OUT/'work'
eligible = json.load(open(WORK/'s09_A_eligible.json',encoding='utf-8'))
tables = rtti_tables()

# Build class ancestor set from each COL's CHD BaseClassArray (all entries, skip self at [0]).
# ancset_incl[name] = {name} U all base names from BaseClassArray
ancset = {}
col_of = {}
for t in tables:
    col_of.setdefault(t['name'], t['col'])
for name, col in col_of.items():
    chd = u32(col + 0x10)
    s = {name}
    if chd and is_ro(chd):
        nb = u32(chd + 8); pba = u32(chd + 0xC)
        if pba and is_ro(pba) and nb:
            for i in range(min(nb, 32)):
                bcd = u32(pba + 4 * i)
                if not bcd: continue
                btd = u32(bcd)
                bn = cstr(btd + 8) if btd else None
                if bn: s.add(bn)
    ancset[name] = s

def strip(n): return n.replace('.?AV','').replace('.?AU','').replace('@@','')
def common_base(names):
    names = sorted(set(names))
    if not names: return None
    if any(n not in ancset for n in names):
        return None
    inter = set(ancset[names[0]])
    for n in names[1:]:
        inter &= set(ancset[n])
    if not inter: return None
    # deepest common = member whose own ancset is a superset of the others (most derived),
    # equivalently the one with the largest ancset within the intersection
    best = max(inter, key=lambda x: len(ancset.get(x, {x})))
    return best

out={}
for r in eligible:
    eh=r['entry']; e=int(eh,16)
    hits=tables_holding(tables,e)
    ht=[dict(vt='%08X'%t['vt'],slot=slot,col='%08X'%t['col'],td='%08X'%t['td'],name=t['name']) for t,slot in hits]
    names=[h['name'] for h in ht]
    cb=common_base(names)
    out[eh]=dict(hits=ht,n_hits=len(ht),common_base=cb,
                 slots=sorted(set(h['slot'] for h in ht)),names=sorted(set(names)))
json.dump(out,open(WORK/'attrib_fixed.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# report for strict-③b candidates
feat=json.load(open(WORK/'features_cfg.json',encoding='utf-8'))
print('%-8s %-4s %-16s %-12s %s'%('entry','nhit','common_base','slots','holding-classes'))
for eh in sorted(out):
    if not feat.get(eh,{}).get('strict'): continue
    a=out[eh]
    print('%-8s %-4d %-16s %-12s %s'%(
        eh,a['n_hits'],strip(a['common_base']) if a['common_base'] else 'None',
        str(a['slots']), ','.join(strip(n) for n in a['names'])))
