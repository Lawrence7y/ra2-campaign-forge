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
idx = {a: i for i, (a, sz, mn, op) in enumerate(insns)}

res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
lin = [h for h in res["q3"]["a"]["all_hits"]]
linset = {int(h["va"],16) for h in lin}

# adjudicated extra site (genuine, missed by linear sweep due to resync overrun)
EXTRA = 0x59bdaa
def ins_at(va):
    sz = None
    for (a, s, m, op) in md.disasm_lite(TB[va-TVA:va-TVA+16], va):
        return {"va": hex(a), "bytes": TB[a-TVA:a-TVA+s].hex(" "), "mn": m, "op": op, "size": s}
print("EXTRA decode:", ins_at(EXTRA))
print("in linear?", EXTRA in linset)

all16 = [dict(h) for h in lin]
e = ins_at(EXTRA)
all16.append({"va": hex(EXTRA), "bytes": e["bytes"], "mn": e["mn"], "op": e["op"], "form": "shl_rm32_imm4_C1/4"})
all16.sort(key=lambda h: int(h["va"], 16))
forms = {}
for h in all16: forms[h["form"]] = forms.get(h["form"], 0) + 1

# --- b) window classification on the reconciled set ---
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
per = []
for h in all16:
    va = int(h["va"],16); i = idx.get(va)
    if i is None:
        per.append({"va": h["va"], "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"],
                    "note": "outside linear decode; window/buckets not computed", "next6": []})
        continue
    w, j = [], i
    while j < len(insns) and insns[j][0]-va < 48: w.append(insns[j]); j += 1
    fl = set()
    for (a,sz,mn,op) in w: fl |= flags_of(a,sz,mn,op)
    n6 = []; j = i+1
    while j < len(insns) and len(n6) < 6:
        a,sz,mn,op = insns[j]; n6.append({"va": hex(a), "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "mnem": mn, "ops": op}); j += 1
    per.append({"va": h["va"], "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"], "form": h["form"],
                "n_instr_48B": len(w), "flags": sorted(fl),
                "has_FF_slash2_or_3": bool([x for x in fl if x.startswith("FF/")]),
                "has_mem_read": "mem_read" in fl, "next6": n6})
bk = {"both": 0, "ff_only": 0, "memread_only": 0, "neither": 0, "unclassified": 0}
for p in per:
    if "flags" not in p: bk["unclassified"] += 1; continue
    a1, b1 = p["has_FF_slash2_or_3"], p["has_mem_read"]
    if a1 and b1: bk["both"] += 1
    elif a1: bk["ff_only"] += 1
    elif b1: bk["memread_only"] += 1
    else: bk["neither"] += 1

res["q3"]["a"]["total_mul16_hits"] = len(all16)
res["q3"]["a"]["forms_used"] = {
  "shl r/m32, imm8==4  (C1 /4 04)": forms.get("shl_rm32_imm4_C1/4", 0),
  "shl r/m8, imm8==4   (C0 /4 04)": forms.get("shl_rm8_imm4_C0/4", 0),
  "shl r/m16, imm8==4  (66 C1 /4 04)": forms.get("shl_rm16_imm4_66C1/4", 0),
  "imul r32, r/m32, imm==0x10  (6B /r 10)": 0,
  "imul r32, r/m32, imm32==0x10 (69 /r 10000000)": 0,
  "lea-based x16": 0,
  "TOTAL": len(all16)}
res["q3"]["a"]["reconciliation"] = {
  "linear_sweep_extracted": 615,
  "raw_byte_scan_extracted": 623,
  "adjudication": "8 raw-only addresses: 3 are ModRM bytes inside other instructions (0x6ffd76 within '81 c1 a0 04 00 00', 0x72ecf3 within '0f 94 c1', 0x77e730 within '81 c1 24 6c b7 00'); 4 are the C1 byte of a 66-prefixed shl already counted at the 0x66 address (0x7c6aaa/0x7c76ca/0x7c7a8e/0x7c7e62); 1 is a genuine instruction the linear sweep overran during a resync (0x59bdaa 'c1 e0 04 shl eax,4'). Final count = 615 + 1 = 616.",
  "final_count": len(all16)}
res["q3"]["a"]["all_hits"] = all16
res["q3"]["b"]["buckets"] = bk
res["q3"]["b"]["per_hit"] = per
res["q3"]["c"]["items"] = [{"va": p["va"], "bytes": p["bytes"], "mnem": p["mnem"], "ops": p["ops"], "next6": p.get("next6", [])} for p in per[:40]]

# --- e) strict backward def-use on reconciled set ---
BRANCH = {"jmp","je","jne","jz","jnz","jl","jle","jg","jge","jb","jbe","ja","jae","js","jns","jc","jnc","jo","jno","jp","jnp","loop","ret","retn"}
AL = {"eax":"eax","ax":"eax","al":"eax","ah":"eax","ebx":"ebx","bx":"ebx","bl":"ebx","bh":"ebx",
      "ecx":"ecx","cx":"ecx","cl":"ecx","ch":"ecx","edx":"edx","dx":"edx","dl":"edx","dh":"edx",
      "esi":"esi","si":"esi","edi":"edi","di":"edi","ebp":"ebp","bp":"ebp","esp":"esp","sp":"esp"}
ZLO, ZHI = 0x812000, 0x880000
def regs_in(op): return set(re.findall(r"\b(eax|ebx|ecx|edx|esi|edi|ebp|esp|ax|bx|cx|dx|si|di|bp|sp|al|ah|bl|bh|cl|ch|dl|dh)\b", op))
strict = []
for h in all16:
    va = int(h["va"],16); i = idx.get(va)
    if i is None: continue
    a, sz, mn, op = insns[i]
    d = op.split(",")[0].strip()
    if d not in AL: continue
    b32 = AL[d]; found = None; j = i-1; steps = 0
    while j >= 0 and steps < 40:
        a2, sz2, mn2, op2 = insns[j]
        if mn2 in BRANCH: break
        d2 = op2.split(",")[0].strip() if op2.strip() else ""
        if d2 in AL and AL[d2] == b32:
            for m in re.finditer(r"0x([0-9a-fA-F]+)", op2):
                v = int(m.group(1), 16)
                if ZLO <= v < ZHI:
                    found = {"def_instr_va": hex(a2), "bytes": TB[a2-TVA:a2-TVA+sz2].hex(" "), "mnem": mn2, "ops": op2, "imm": hex(v), "dist": i-j}
            break
        j -= 1; steps += 1
    strict.append({"hit_va": h["va"], "hit_ops": h["op"], "reg": d, "def_instr": found})
yes = [s for s in strict if s["def_instr"]]
res["q3"]["e"] = {
 "question": "does any 16x scaling site consume a value defined by an instruction that loads from an absolute immediate address inside .data 0x812000..0x880000",
 "strict_backward_def_use": {"n_analyzed": len(strict), "answer": "yes" if yes else "no", "n_yes": len(yes), "yes": yes},
 "caveat": "only direct absolute immediates are followed; register/indirect bases (struct field loads, [reg+disp]) are NOT resolved, so 'no' would not have meant absent.",
 "loose_n": len(res["q3"]["e"].get("hits", []))}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("final16:", len(all16), forms)
print("b:", bk)
print("e:", res["q3"]["e"]["strict_backward_def_use"])
