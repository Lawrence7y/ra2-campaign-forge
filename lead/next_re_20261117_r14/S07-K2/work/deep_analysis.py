"""Deep analysis of +0x94 writes and +0x80 writes with context.
Produces EVIDENCE/analysis_94.tsv, analysis_80_categories.tsv, read_samples.
"""
import os, sys, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, md32, load_func_atlas
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S07-K2\EVIDENCE")

b = Bin()
t = b.text
data = b.pe.__data__[t["raw"]:t["rawsize"]+t["raw"]]
m = md32(skipdata=True)
insns = [i for i in m.disasm(data, t["va"]) if i.id != 0]
addrs = [i.address for i in insns]

atlas_rows, _ = load_func_atlas()
atlas_entries = [va for va, _ in atlas_rows]
atlas_map = {va: rec for va, rec in atlas_rows}
def func_of(va):
    i = bisect.bisect_right(atlas_entries, va) - 1
    if i < 0: return None
    e = atlas_entries[i]; rec = atlas_map[e]
    try: sz = int(rec.get("size","0"))
    except: sz = 0
    return e if (sz and va < e+sz) else None

def ctx(va, before=8, after=4):
    i = bisect.bisect_left(addrs, va)
    out = []
    for j in range(max(0,i-before), min(len(insns), i+after)):
        ins = insns[j]
        out.append("%08X  %s %s%s" % (ins.address, ins.mnemonic, ins.op_str,
                   "  <<<" if ins.address==va else ""))
    return out

# ---- +0x94: find all writes, categorize object-field vs other ----
# A write to [reg+0x94] is "object field" if reg is derived from a this pointer
# (ecx/esi/edi/ebx/ebp typically), "other" if reg is esp-based stack.
# We approximate: if the func itself contains a cmp with -1 on [reg+0x94] or a
# subsequent [reg+0x80]/[reg+0x74] etc, it's an ObjectClass. Use a heuristic + report raw.
p94 = os.path.join(OUTDIR, "sweep_0x94_access.tsv")
rows94 = []
with open(p94, encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        rows94.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))

writes94 = [r for r in rows94 if r["is_write"]=="1"]
reads94 = [r for r in rows94 if r["is_write"]=="0"]
print("+0x94 writes:", len(writes94), " reads:", len(reads94))
# value dist of writes
from collections import Counter
print("write val dist:", Counter(r["valstr"] for r in writes94).most_common(8))

# Given R14_COMMON §939: 49 object-field / 112 other (total 172 originally, now 519 raw access).
# My raw dword [reg+0x94] access count is 519 (all reads+writes). But §939 counts "写点 172 -> 49 object / 112 other".
# Let me count WRITE sites only among 0x94 and classify by base reg.
def base_reg(hins):
    # extract base reg from "mov dword ptr [esi + 0x94], ..."
    import re
    mm = re.search(r"\[(\w+)", hins)
    return mm.group(1) if mm else "?"
print("write base-reg dist:", Counter(base_reg(r["hins"]) for r in writes94).most_common())

# write context summary for -1 (0xffffffff) writes
print("\n-- +0x94 writes with value -1/0xffffffff --")
for r in writes94:
    if r["valstr"] in ("0xffffffff",) or ("-1" in r["valstr"]):
        print("  ", r["va"], r["hins"], "fn="+r["func"])
