import sys, json, re
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
T = PE_.sec_by_name(".text")
TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]
TVA = T["va"]
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
hits16 = [{"va": int(h["va"],16), "bytes": h["bytes"], "mn": h["mn"], "op": h["op"], "form": h["form"]}
          for h in res["q3"]["a"]["all_hits"]]

def decode_at(va, nbytes=48):
    o = va - TVA
    out = []
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+nbytes], va):
        out.append({"va": a, "size": sz, "mn": mn, "op": op})
    return out

CALL_REG = {"eax","ebx","ecx","edx","esi","edi","ebp","esp"}
def cls(ins):
    op = ins["op"]
    mn = ins["mn"]
    flags = set()
    if mn == "call":
        if "[" in op: flags.add("call_indirect_mem")
        elif op.strip() in CALL_REG: flags.add("call_indirect_reg")
        else: flags.add("call_direct")
    o0 = ins["va"] - TVA
    sz = ins["size"]
    for i in range(sz-1):
        if TB[o0+i] == 0xFF:
            reg = (TB[o0+i+1] >> 3) & 7
            if reg == 2: flags.add("ff_slash2_call")
            if reg == 3: flags.add("ff_slash3_callfar")
    if mn != "lea" and "[" in op:
        head = op.split(",")[0]
        tail = op.split(",")[-1]
        # memory as destination only?
        if "[" in head and "[" not in tail:
            flags.add("mem_write_dst")
        else:
            flags.add("mem_read")
    return flags

per = []
for h in hits16:
    seq = decode_at(h["va"])
    win = seq                       # seq[0] is the hit itself; window is 48 bytes from hit
    fl = set()
    for ins in win:
        fl |= cls(ins)
    per.append({"va": hex(h["va"]), "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"],
                "n_instr_in_48B": len(win), "flags": sorted(fl),
                "has_ff_slash2_or_3": bool({"ff_slash2_call","ff_slash3_callfar"} & fl),
                "has_mem_read": "mem_read" in fl,
                "next6": [{"va": hex(x["va"]), "bytes": TB[x["va"]-TVA:x["va"]-TVA+x["size"]].hex(" "),
                           "mnem": x["mn"], "ops": x["op"]} for x in seq[1:7]]})
buckets = {"both": 0, "indirect_call_only(FF/2 or /3)": 0, "mem_read_only": 0, "neither": 0}
for p in per:
    a = p["has_ff_slash2_or_3"]; b = p["has_mem_read"]
    if a and b: buckets["both"] += 1
    elif a: buckets["indirect_call_only(FF/2 or /3)"] += 1
    elif b: buckets["mem_read_only"] += 1
    else: buckets["neither"] += 1
res["q3"]["b"] = {"window_definition": "48 bytes starting at the hit address, decoded instruction-aligned",
                  "buckets": buckets,
                  "per_hit": per}
res["q3"]["c"]["items"] = [{"va": hex(h["va"]), "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"],
                            "next6": [{"va": hex(x["va"]), "bytes": TB[x["va"]-TVA:x["va"]-TVA+x["size"]].hex(" "),
                                       "mnem": x["mn"], "ops": x["op"]} for x in decode_at(h["va"])[1:7]]}
                           for h in hits16[:40]]
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("buckets:", buckets)
for p in per[:6]: print(p["va"], p["op"], p["flags"], p["n_instr_in_48B"])
