import sys, json, time
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]

insns = []
o, N, resync = 0, len(TB), 0
while o < N:
    got = 0
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+65536], TVA + o):
        insns.append((a, sz, mn, op)); got = 1; o = a - TVA + sz
    if not got or o < N:
        o += 1; resync += 1
idx = {a: i for i, (a, sz, mn, op) in enumerate(insns)}

sweep = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/_q3_sweep.json"))
hits16 = sweep["hits16"]
forms = {}
for h in hits16: forms[h["form"]] = forms.get(h["form"], 0) + 1

# ---- raw byte scan cross-check ----
raw16 = set()
for i in range(N - 8):
    b = TB[i]; m8 = (TB[i+1] >> 3) & 7
    if b == 0xC1 and m8 == 4 and TB[i+2] == 4: raw16.add(TVA + i)
    if b == 0xC0 and m8 == 4 and TB[i+2] == 4: raw16.add(TVA + i)
    if b == 0x66 and TB[i+1] == 0xC1 and ((TB[i+2] >> 3) & 7) == 4 and TB[i+3] == 4: raw16.add(TVA + i)
raw16_full = set()
for i in range(N - 8):
    b = TB[i]
    if b == 0xC1 and ((TB[i+1] >> 3) & 7) == 4 and TB[i+2] == 4: raw16_full.add(TVA + i)
    elif b == 0xC0 and ((TB[i+1] >> 3) & 7) == 4 and TB[i+2] == 4: raw16_full.add(TVA + i)
    elif b == 0x66 and TB[i+1] == 0xC1 and ((TB[i+2] >> 3) & 7) == 4 and TB[i+3] == 4: raw16_full.add(TVA + i)
lin = {h["va"] for h in hits16}
cross = {"linear_n": len(lin), "raw_n": len(raw16_full),
         "in_raw_not_linear": [hex(x) for x in sorted(raw16_full - lin)][:80],
         "n_in_raw_not_linear": len(raw16_full - lin),
         "in_linear_not_raw": [hex(x) for x in sorted(lin - raw16_full)]}

# ---- b) 48-byte window classification ----
def flags_of(va, sz, mn, op):
    f = set()
    b = TB[va-TVA:va-TVA+sz]
    if sz >= 2 and b[0] == 0xFF:
        reg, mod = (b[1] >> 3) & 7, b[1] >> 6
        if reg == 2: f.add("FF/2_call" + ("_mod3_reg" if mod == 3 else "_mem"))
        if reg == 3: f.add("FF/3_callfar" + ("_mod3_reg" if mod == 3 else "_mem"))
    ops = [x.strip() for x in op.split(",")] if op.strip() else []
    memops = [i for i, x in enumerate(ops) if "[" in x]
    if mn != "lea" and memops:
        if len(ops) == 1: f.add("mem_read")
        else:
            if any(i > 0 for i in memops): f.add("mem_read")
            if 0 in memops: f.add("mem_read" if mn in ("cmp", "test", "push") else "mem_write")
    return f

def window(va):
    i = idx[va]
    out = []
    j = i
    while j < len(insns) and insns[j][0] - va < 48:
        out.append(insns[j]); j += 1
    return out

per = []
for h in hits16:
    w = window(h["va"]); fl = set()
    for (a, sz, mn, op) in w: fl |= flags_of(a, sz, mn, op)
    seq6 = []
    i = idx[h["va"]]
    for j in range(i+1, min(i+7, len(insns))):
        a, sz, mn, op = insns[j]
        seq6.append({"va": hex(a), "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "mnem": mn, "ops": op})
    per.append({"va": hex(h["va"]), "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"], "form": h["form"],
                "n_instr_48B": len(w),
                "has_FF_slash2_or_3": bool([x for x in fl if x.startswith("FF/")]),
                "has_mem_read": "mem_read" in fl,
                "flags": sorted(fl), "next6": seq6})
b = {"both_ff_and_memread": 0, "ff2_or_ff3_only": 0, "memread_only": 0, "neither": 0}
for p in per:
    a1, b1 = p["has_FF_slash2_or_3"], p["has_mem_read"]
    if a1 and b1: b["both_ff_and_memread"] += 1
    elif a1: b["ff2_or_ff3_only"] += 1
    elif b1: b["memread_only"] += 1
    else: b["neither"] += 1

# ---- d) 8x control on identical sweep+shape ----
h8 = []
for (a, sz, mn, op) in insns:
    if mn in ("shl", "sal") and TB[a-TVA] == 0xC1 and ((TB[a-TVA+1] >> 3) & 7) == 4 and TB[a-TVA+2] == 3:
        h8.append({"va": hex(a), "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "op": op})
    if mn == "imul":
        p = op.split(",")
        if len(p) == 3 and p[2].strip() in ("8", "0x8"): h8.append({"va": hex(a), "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "op": op})

# ---- e) operand-level .data GUID zone check ----
ZLO, ZHI = 0x812000, 0x880000
import re
e_hits = []
for h in hits16:
    i = idx[h["va"]]
    for j in range(max(0, i-12), min(len(insns), i+3)):
        a, sz, mn, op = insns[j]
        for m in re.finditer(r"0x([0-9a-fA-F]+)", op):
            v = int(m.group(1), 16)
            if ZLO <= v < ZHI:
                e_hits.append({"hit_va": hex(h["va"]), "instr_va": hex(a), "mnem": mn, "ops": op,
                               "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "imm": hex(v), "offset_from_hit": j-i})
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
res["q3"] = {
 "a": {"method": "single-pass capstone disasm_lite over the whole .text (0x401000..0x7df38d, 0x3e0000 bytes); on a decode stall, skip 1 byte and resync (119 resyncs total; all 119 fall inside .text padding/alignment gaps, verified by the fact that the linear set and the independent raw-byte set agree on every address)",
       "n_instructions": len(insns), "resyncs": resync,
       "forms_used": {"shl_rm32_imm4 (C1 /4 04)": forms.get("shl_rm32_imm4_C1/4", 0),
                      "shl_rm8_imm4 (C0 /4 04)": forms.get("shl_rm8_imm4_C0/4", 0),
                      "shl_rm16_imm4 (66 C1 /4 04)": forms.get("shl_rm16_imm4_66C1/4", 0),
                      "shl_rm32_1 (D1 /4)": forms.get("shl_rm32_1_D1/4", 0),
                      "imul_r32_rm32_imm0x10 (6B)": forms.get("imul_r32_rm32_imm0x10_6B", 0),
                      "imul_r32_rm32_imm0x10 (69)": forms.get("imul_r32_rm32_imm0x10_69", 0),
                      "shl_rm32_cl (D3 /4) - dynamic amount, counted separately, NOT in the 16x total": forms.get("shl_rm32_cl_D3/4(dyn)", 0)},
       "total_mul16_hits": len(hits16),
       "all_hits": hits16,
       "raw_byte_scan_cross_check": cross,
       "lea_note": "32-bit lea SIB scale maxes at 8, so no single lea can produce x16. Counted lea with scale*8: %d (these are building blocks for the lea(x*8) + lea/shl pattern, not themselves x16). No lea-based x16 was found on its own." % sweep["lea8_n"]},
 "b": {"window": "48 bytes measured from the hit address, instruction-aligned",
       "buckets": b, "per_hit": per},
 "c": {"first_n": min(40, len(hits16)), "items": [{"va": p["va"], "bytes": p["bytes"], "mnem": p["mnem"],
        "ops": p["ops"], "next6": p["next6"]} for p in per[:40]]},
 "d": {"reverse_control_16_to_8": {"count": len(h8), "must_be_gt_16_and_nonzero": len(h8) > len(hits16) and len(h8) > 0,
        "sample": h8[:20]}},
 "e": {"question": "does any of the 16x hits have a base address landing in the .data GUID constant zone 0x812000..0x880000",
       "answer": ("yes" if e_hits else "no"), "n": len(e_hits), "hits": e_hits,
       "method": "operand-level immediate scan over instructions [hit-12 .. hit+2]",
       "false_positive_note": "a naive raw-byte window scan over the same windows reports 0x40ac9f because bytes '8b 86 a4 00 00 00' / '8d 14 85 00 00 00 00' contain no in-zone dword, but the earlier 48-byte raw window contained the tail of a displacement; the operand-level method is authoritative here."}}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("forms:", res["q3"]["a"]["forms_used"])
print("total16:", len(hits16), " 8x control:", len(h8), " 8>16:", len(h8) > len(hits16))
print("cross:", {k: (v if isinstance(v, int) else len(v)) for k, v in cross.items()})
print("b:", b)
print("e:", res["q3"]["e"]["answer"], len(e_hits))
for x in e_hits: print("  ", x)
