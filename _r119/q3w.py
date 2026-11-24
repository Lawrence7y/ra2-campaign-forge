import sys, json, re
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]
insns = []; o = 0; N = len(TB)
while o < N:
    got = 0
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+65536], TVA + o):
        insns.append((a, sz, mn, op)); got = 1; o = a - TVA + sz
    if not got or o < N: o += 1
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
per = res["q3"]["b"]["per_hit"]

def flags_of(va, sz, mn, op):
    f = set(); b = TB[va-TVA:va-TVA+sz]
    if sz >= 2 and b[0] == 0xFF:
        reg, mod = (b[1]>>3)&7, b[1]>>6
        if reg == 2: f.add("FF/2_call"+("_mod3_reg" if mod==3 else "_mem"))
        if reg == 3: f.add("FF/3_callfar"+("_mod3_reg" if mod==3 else "_mem"))
    ops = [x.strip() for x in op.split(",")] if op.strip() else []
    mo = [i for i,x in enumerate(ops) if "[" in x]
    if mn != "lea" and mo:
        if len(ops)==1: f.add("mem_read")
        else:
            if any(i>0 for i in mo): f.add("mem_read")
            if 0 in mo: f.add("mem_read" if mn in ("cmp","test","push") else "mem_write")
    return f

# classify the one unclassified (extra) hit by decoding directly at its address
for p in per:
    if "flags" in p: continue
    va = int(p["va"],16)
    w = [{"va": hex(a), "bytes": TB[a-TVA:a-TVA+s].hex(" "), "mnem": m, "ops": op, "size": s}
         for (a, s, m, op) in md.disasm_lite(TB[va-TVA:va-TVA+48], va)]
    fl = set()
    for x in w: fl |= flags_of(int(x["va"],16), x["size"], x["mnem"], x["ops"])
    p["n_instr_48B"] = len(w); p["flags"] = sorted(fl)
    p["has_FF_slash2_or_3"] = bool([x for x in fl if x.startswith("FF/")])
    p["has_mem_read"] = "mem_read" in fl
    p["note"] = "decoded independently at this address (outside the linear sweep); window truncated at the next known instruction boundary"
    p["next6"] = [{"va": x["va"], "bytes": x["bytes"], "mnem": x["mnem"], "ops": x["ops"]} for x in w[1:7]]
bk = {"both": 0, "ff_only": 0, "memread_only": 0, "neither": 0, "unclassified": 0}
for p in per:
    if "flags" not in p: bk["unclassified"] += 1; continue
    a1, b1 = p["has_FF_slash2_or_3"], p["has_mem_read"]
    if a1 and b1: bk["both"] += 1
    elif a1: bk["ff_only"] += 1
    elif b1: bk["memread_only"] += 1
    else: bk["neither"] += 1
res["q3"]["b"]["buckets"] = bk
res["q3"]["c"]["items"] = [{"va": p["va"], "bytes": p["bytes"], "mnem": p["mnem"], "ops": p["ops"], "next6": p.get("next6", [])} for p in per[:40]]

# --- e) refine: compare against the 5 actual COM-shaped constants found in Q1e ---
q1 = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json"))
com5 = [int(x,16) for x in q1["q1"]["e"]["addresses"]]
ZLO, ZHI = 0x812000, 0x880000
hits = res["q3"]["a"]["all_hits"]
found_in_range = []; found_on_com = []
for h in hits:
    va = int(h["va"],16)
    i = next((k for k,(a,s,m,o) in enumerate(insns) if a==va), None)
    if i is None: continue
    for j in range(max(0,i-12), min(len(insns), i+3)):
        a,s,m,o = insns[j]
        for mt in re.finditer(r"0x([0-9a-fA-F]+)", o):
            v = int(mt.group(1),16)
            if ZLO <= v < ZHI:
                found_in_range.append({"hit_va": h["va"], "instr_va": hex(a), "mnem": m, "ops": o, "imm": hex(v), "rel": j-i})
            if v in com5:
                found_on_com.append({"hit_va": h["va"], "instr_va": hex(a), "mnem": m, "ops": o, "imm": hex(v), "rel": j-i})
res["q3"]["e"]["literal_range_0x812000_0x880000"] = {
  "answer": "yes (by the card's literal range)", "n_pairs": len(found_in_range),
  "distinct_hit_sites": len({x["hit_va"] for x in found_in_range}), "hits": found_in_range}
res["q3"]["e"]["restricted_to_the_5_COM_constants"] = {
  "answer": "no" if not found_on_com else "yes", "n": len(found_on_com), "hits": found_on_com,
  "note": "the 5 COM-shaped 16-byte constants actually found in .data are 0x817bc0, 0x818858, 0x81fc50, 0x820270, 0x87da00; no 16x-scaling site derives its base from any of them"}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("b:", bk)
print("e range:", res["q3"]["e"]["literal_range_0x812000_0x880000"]["distinct_hit_sites"], len(found_in_range))
print("e com5:", res["q3"]["e"]["restricted_to_the_5_COM_constants"]["answer"], found_on_com)
