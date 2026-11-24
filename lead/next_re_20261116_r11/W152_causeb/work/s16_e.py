import json, w152_core as C
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
d=json.load(open(ATLAS,encoding='utf-8'))
KNOWN={0x404E0000,0xA2529D39,0x3F91DF46}
def slots_of(vt):
    out=[]
    for i in range(400):
        try: v=C.u32(vt+4*i)
        except Exception: break
        if v in KNOWN or v==0: break
        nm,_,_,_=C.sec_of(v)
        if nm!='.text': break
        out.append(v)
    return out
WANT={0x004151E0}
res={k:[] for k in WANT}
for ent in d['vtables']:
    for i,t in enumerate(slots_of(ent['vt'])):
        if t in res: res[t].append((ent['class'],i,4*i,ent['vt']))
for f,label in ((0x004151E0,"calls BOTH wrappers directly + slot73"),):
    print("=== %08X  %s ==="%(f,label))
    for cls,i,bo,vt in sorted(res[f]): print("   %-40s slot %3d (0x%03X) vt=%08X"%(cls,i,bo,vt))
print("")
inss=C.disas_fn(0x4151E0)
print("=== 0x4151E0 first 90 instructions (size=%s) ==="%C.fn_size(0x4151E0))
for j in range(min(90,len(inss))): print("   "+C.fmt(inss[j]))
