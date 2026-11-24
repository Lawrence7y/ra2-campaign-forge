import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify2.json", encoding="utf-8"))

# 1) per-row CLSID
print("### per-row registration CLSID")
clsid = {}
for d in rows:
    ct = int(d["factory_ctor_callers"][0], 16)
    ins = list(dis(ct, 60))
    cid = None
    reg = None
    for i in ins:
        if i.mnemonic == "push" and i.op_str.startswith("0x7e9"):
            cid = int(i.op_str, 16)
        if i.mnemonic == "call" and i.op_str.startswith("esi"):
            reg = i.address
            break
    clsid[d["entry"]] = cid
    d["clsid"] = f"{cid:08X}" if cid else None
    print(f"  {d['entry']} {d['expected_class']:<26} CLSID={d['clsid']} "
          f"register@{(reg or 0):08X} guid_bytes={hexs(cid,16) if cid else None}")

json.dump(rows, open("verify3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 2) CoCreateInstance sites: which CLSID is passed?
print()
print("### CoCreateInstance sites and the CLSID/imm pushed before")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
p = blob.find((0x7E15FC).to_bytes(4, "little"))
sites = []
while p >= 0:
    sites.append(sva + p - 2)  # ff 15 xx xx xx xx
    p = blob.find((0x7E15FC).to_bytes(4, "little"), p + 1)
allclsid = {v for v in clsid.values() if v}
for s in sites:
    ctx = dis(s - 30, 48)
    pushes = [i for i in ctx if i.mnemonic == "push" and i.op_str.startswith("0x")]
    cids = [i.op_str for i in pushes if i.op_str.startswith("0x7e9") or i.op_str.startswith("0x7fa") or i.op_str.startswith("0x7fb")]
    hit = [c for c in cids if c.upper().replace("0X", "0x")[2:] in {a for a in allclsid}]
    after = dis(s + 6, 24)
    print(f"  {s:08X} pushes={[i.op_str for i in pushes]} family_hit={hit} "
          f"after={' | '.join(j.mnemonic + ' ' + j.op_str for j in after[:3])}")

# 3) enclosing fn of 007CD8EA + its callers
print()
print("### context around 007CD8EA (caller of init 006BB9A0)")
for i in dis(0x7CD890, 140):
    print("   " + fmt(i))
