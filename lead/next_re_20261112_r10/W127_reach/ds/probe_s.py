import json
m=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"))
print("top-level keys:", list(m.keys())[:10])
vt2=m.get("vt2name",{})
print("vt2name entries:", len(vt2))
for k in ("0x7F1094","0x7ea8a0","0x7EDFB4","0x7edfb4","0x7EA8A0"):
    for kk in (k,k.upper(),k.lower()):
        if kk in vt2: print("  %s -> %s" % (kk, vt2[kk]))
# normalise keys
def norm(s): return int(s,16) if isinstance(s,str) else int(s)
kv={}
for k,v in vt2.items():
    try: kv[norm(k)]=v
    except Exception: pass
for a in (0x007F1094,0x007EA8A0,0x007EDFB4):
    print("  %08X -> %s" % (a, kv.get(a,"(absent)")))
print()
print("=== any class named Scroll / House in the map? ===")
seen=set()
for k,v in kv.items():
    if isinstance(v,str) and ("Scroll" in v or "House" in v): seen.add((k,v))
for k,v in sorted(seen)[:20]: print("  %08X %s" % (k,v))
