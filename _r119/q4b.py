import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]

# single-pass resynced decode (same as q3)
insns = []; o = 0; N = len(TB)
while o < N:
    got = 0
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+65536], TVA + o):
        insns.append((a, sz, mn, op)); got = 1; o = a - TVA + sz
    if not got or o < N: o += 1
starts = {a: (sz, mn, op) for (a, sz, mn, op) in insns}

res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q4.json"))

def verify(imm, addr):
    """is `addr` the address of the immediate field of a real instruction?"""
    for a in range(addr-8, addr+1):
        if a in starts:
            sz, mn, op = starts[a]
            if a + sz == addr + 4 and hex(imm) in op:
                return {"instr_va": hex(a), "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "mnem": mn, "ops": op,
                        "imm_field_offset": addr - a, "verdict": "REAL_IMMEDIATE"}
    hit = addr in starts
    return {"verdict": "COINCIDENTAL_BYTES" if not hit else "INSTRUCTION_START_BUT_NO_IMM", 
            "note": "no enclosing instruction has this field as its tail immediate"}

for imm, key in ((0x818858, "0x818858"), (0x820270, "0x820270")):
    lst = res["q4"]["targets"][key]["unaligned_addrs"]
    v = [{"addr": x, **verify(imm, int(x, 16))} for x in lst]
    res["q4"]["targets"][key]["instruction_level_verification"] = v
    res["q4"]["targets"][key]["n_real_immediate"] = sum(1 for x in v if x["verdict"] == "REAL_IMMEDIATE")
    res["q4"]["targets"][key]["n_coincidental"] = sum(1 for x in v if x["verdict"] != "REAL_IMMEDIATE")
    print(key, "real:", res["q4"]["targets"][key]["n_real_immediate"], "/", len(v))
    for x in v: print("   ", x)
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q4.json","w"), indent=1)
