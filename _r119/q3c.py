import sys, json
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
    return [{"va": a, "size": sz, "mn": mn, "op": op}
            for (a, sz, mn, op) in md.disasm_lite(TB[o:o+nbytes], va)]

WRITE_MN = {"mov","movzx","movsx","add","sub","and","or","xor","inc","dec","shl","shr","sar","sal","not","neg","xchg","lea","stos","cmpxchg","adc","sbb","imul","mul"}

def flags_of(ins):
    f = set()
    b = TB[ins["va"]-TVA:ins["va"]-TVA+ins["size"]]
    if len(b) >= 2 and b[0] == 0xFF:
        reg = (b[1] >> 3) & 7
        mod = b[1] >> 6
        if reg == 2: f.add("FF_slash2" + ("_mod3_reg" if mod == 3 else "_mem"))
        if reg == 3: f.add("FF_slash3" + ("_mod3_reg" if mod == 3 else "_mem"))
    if ins["mn"] in ("call","jmp") and "[" in ins["op"]: f.add("call_indirect_mem")
    if ins["mn"] in ("call","jmp") and "[" not in ins["op"] and ins["op"].strip() in \
       {"eax","ebx","ecx","edx","esi","edi","ebp","esp"}: f.add("call_indirect_reg")
    ops = [x.strip() for x in ins["op"].split(",")]
    memops = [i for i, x in enumerate(ops) if "[" in x]
    if ins["mn"] != "lea":
        if len(ops) == 1:
            if memops: f.add("mem_read")
        else:
            if any(i > 0 for i in memops): f.add("mem_read")
            if 0 in memops:
                f.add("mem_read" if ins["mn"] in ("cmp","test","push") else "mem_write")
    return f

per = []
for h in hits16:
    seq = decode_at(h["va"])
    fl = set()
    for ins in seq: fl |= flags_of(ins)
    per.append({"va": hex(h["va"]), "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"],
                "n_instr_48B": len(seq), "flags": sorted(fl),
                "has_ff2_or_ff3": bool({"FF_slash2_mod3_reg","FF_slash2_mem","FF_slash3_mod3_reg","FF_slash3_mem"} & fl),
                "has_mem_read": "mem_read" in fl,
                "next6": [{"va": hex(x["va"]), "bytes": TB[x["va"]-TVA:x["va"]-TVA+x["size"]].hex(" "),
                           "mnem": x["mn"], "ops": x["op"]} for x in seq[1:7]]})
b = {"both": 0, "indirect_call_ff2_or_ff3_only": 0, "mem_read_only": 0, "neither": 0}
for p in per:
    a1, b1 = p["has_ff2_or_ff3"], p["has_mem_read"]
    if a1 and b1: b["both"] += 1
    elif a1: b["indirect_call_ff2_or_ff3_only"] += 1
    elif b1: b["mem_read_only"] += 1
    else: b["neither"] += 1
res["q3"]["b"] = {"window_definition": "48 bytes from hit address, instruction-aligned decode",
                  "any_ff2_or_ff3_instruction_in_window": sum(1 for p in per if p["has_ff2_or_ff3"]),
                  "any_mem_read_in_window": sum(1 for p in per if p["has_mem_read"]),
                  "buckets": b, "per_hit": per}
res["q3"]["c"]["items"] = [{"va": p["va"], "bytes": p["bytes"], "mnem": p["mnem"], "ops": p["ops"], "next6": p["next6"]} for p in per[:40]]
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("buckets:", b)
print("ff2or3 in window:", res["q3"]["b"]["any_ff2_or_ff3_instruction_in_window"], "memread:", res["q3"]["b"]["any_mem_read_in_window"])
for p in per[:8]: print(p["va"], p["ops"], p["flags"])
