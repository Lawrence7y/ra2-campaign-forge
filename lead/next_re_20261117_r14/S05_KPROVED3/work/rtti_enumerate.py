"""Enumerate ALL RTTI vtable holders for each S05 A-set entry, from exe bytes.
Checks 错源⑯: same slot in >1 table; and DV slot(7+k)==V slot k alias.
Vtable boundary: slots are contiguous .text pointers; COL sits immediately before slot0.
Card S05-KPROVED3."""
import sys, struct, csv, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work")
from pe_helpers import *

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
rows = list(csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'))
A = [r for r in rows if r['subsystem']=='S05' and r['has2_rtti']=='1' and r['has4_strict']=='1']
entries = [int(r['entry'],16) for r in A]
name_by_entry = {int(r['entry'],16): r['name'] for r in A}
print("A rows:", len(A))

from collections import defaultdict
pos_by_val = defaultdict(list)
for va in range(RDATA_LO, RDATA_HI-3, 4):
    v = u32(va)
    if v is not None:
        pos_by_val[v].append(va)

def valid_col_at(colva):
    if va2off(colva) is None: return None
    td = u32(colva+0xC)
    if td is None or va2off(td) is None: return None
    nm = cstr(td+8)
    if nm is None or not (nm.startswith('.?AV') or nm.startswith('.?AU')): return None
    return nm

def find_holders(entry):
    """For each position p with u32(p)==entry, walk back over contiguous .text
    slot pointers to find vt (slot0); COL at vt-4; read RTTI name."""
    out = {}
    for p in pos_by_val.get(entry, []):
        cur = p
        while cur-4 >= RDATA_LO and is_text(u32(cur-4) or 0):
            cur -= 4
        vt = cur
        col = u32(vt-4)
        if col is None: continue
        nm = valid_col_at(col)
        if nm is None: continue
        slot = (p - vt)//4
        out[(vt, slot, nm)] = col
    return sorted([(vt,k,nm,col) for (vt,k,nm),col in out.items()])

result = {}
for e in entries:
    h = find_holders(e)
    result[f'{e:08X}'] = [{'vt':f'{vt:08X}','slot':k,'name':nm,'col':f'{col:08X}'} for vt,k,nm,col in h]
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\rtti_holders.json",'w',encoding='utf-8') as f:
    json.dump(result,f,indent=1)

# cross-check against prior card outputs (read-only)
try:
    prior=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\rtti_holders.json"))
    diffs=[k for k in result if set((h['vt'],h['slot'],h['name']) for h in result[k])!=set((h['vt'],h['slot'],h['name']) for h in prior.get(k,[]))]
    print("PRIOR_CROSSCHECK diffs:", len(diffs), diffs[:10])
except Exception as ex:
    print("prior crosscheck skip:",ex)

for e in entries:
    h = find_holders(e)
    key=f'{e:08X}'
    classes = sorted(set(nm for _,_,nm,_ in h))
    print(f"{key} [{name_by_entry[e]}] holders={len(h)} distinct_classes={len(classes)}")
    for vt,k,nm,col in h:
        print(f"    vt={vt:08X} slot={k} col={col:08X} {nm}")
