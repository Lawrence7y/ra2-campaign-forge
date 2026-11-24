import sys, json, re
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

T = PE_.sec_by_name(".text")
TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]
TVA = T["va"]
print("text raw", hex(T["raw"]), "size", hex(len(TB)), "va", hex(TVA))

def form_of(mn, op):
    """classify multiply-by-16 forms from lite disasm text"""
    ops = op.replace(" ", "")
    if mn == "shl" or mn == "sal":
        if ops.endswith(",4") or ops.endswith(",0x4"):
            return "shl_reg_imm4" if not ops.startswith("byte") else None
    if mn == "imul":
        parts = op.split(",")
        if len(parts) == 3:
            v = parts[2].strip()
            if v in ("0x10", "16"):
                return "imul_r_rm_imm0x10"
    return None

def mnem_of_bytes(off, size):
    return TB[off:off+size].hex(" ")

def scan(imm_forms):
    """imm_forms: list of accepted (text) values for the multiplier"""
    hits = []
    for (a, sz, mn, op) in md.disasm_lite(TB, TVA):
        o = a - TVA
        f = None
        ops = op.replace(" ", "")
        if mn in ("shl", "sal"):
            if ops.endswith("," + imm_forms[0]) or ops.endswith("," + imm_forms[1]):
                f = "shl_rm32_imm8(/4)"
        elif mn == "imul":
            p = op.split(",")
            if len(p) == 3 and p[2].strip() in imm_forms:
                f = ("imul_r32_rm32_imm8(6B)" if p[2].strip() in (imm_forms[0], imm_forms[1]) and len(TB[o:o+3])==3 else "imul_r32_rm32_imm32(69)")
        if f:
            hits.append({"va": a, "bytes": TB[o:o+sz].hex(" "), "mn": mn, "op": op, "form": f})
    return hits

# ---- a) 16x forms ----
hits16 = scan(("4", "0x4"))
hits8  = scan(("8", "0x8"))

# also count shl/imm-by-1-cl and lea scale forms for reporting
cnt_cl = 0; cnt_lea_scale8 = 0; cnt_lea_scale_any = 0
for (a, sz, mn, op) in md.disasm_lite(TB, TVA):
    if mn in ("shl", "sal") and op.replace(" ", "").endswith(",cl"):
        cnt_cl += 1
    if mn == "lea":
        if re.search(r"\*\s*8", op): cnt_lea_scale8 += 1
        if re.search(r"\*\s*[1248]", op): cnt_lea_scale_any += 1

print("16x hits:", len(hits16), " 8x hits:", len(hits8), " shl,cl:", cnt_cl, " lea*8:", cnt_lea_scale8, " lea scale:", cnt_lea_scale_any)

# ---- b) window classification (forward 48 bytes, decoded from the hit, alignment-true) ----
CALL_IND = re.compile(r"^(dword ptr \[|qword ptr \[|eax|ebx|ecx|edx|esi|edi|ebp|esp|ax|bx|cx|dx)$")
def classify_windows():
    hit_addr = {h["va"]: h for h in hits16}
    h["win48"] = None
    for (a, sz, mn, op) in md.disasm_lite(TB, TVA):
        if a not in hit_addr: continue
        h = hit_addr[a]
        seq = [(a, sz, mn, op)]
        nxt = None
    return

# second pass, self-contained: collect for each hit the following instructions
window = {}
nexts = {}
targets = {h["va"] for h in hits16}
for (a, sz, mn, op) in md.disasm_lite(TB, TVA):
    if a in targets:
        window[a] = []
        nexts[a] = []
    for t in list(window.keys()):
        if a - t < 48:
            window[t].append((a, sz, mn, op))
        if len(nexts[t]) < 6 and a != t:
            nexts[t].append({"va": hex(a), "bytes": mnem_of_bytes(a-TVA, sz), "mnem": mn, "ops": op})
        if a - t >= 48:
            del window[t]

for h in hits16:
    w = window.get(h["va"], [])
    ind = [x for x in w if x[2] == "call" and ("[" in x[3] or CALL_IND.match(x[3].replace(" ", "")))]
    memread = [x for x in w if x[2] != "lea" and "[" in x[3] and ("," not in x[3] or "[" not in x[3].split(",")[0])]
    # raw FF /2,/3 byte scan in the window
    o0 = h["va"] - TVA
    win = TB[o0:o0+48]
    ff23 = []
    for i in range(len(win)-1):
        if win[i] == 0xFF:
            reg = (win[i+1] >> 3) & 7
            mod = win[i+1] >> 6
            if reg in (2, 3) and mod == 3:
                ff23.append(h["va"]+i)
    h["win48"] = {"n_instr": len(w),
                  "indirect_calls": [{"va": hex(x[0]), "mnem": x[2], "ops": x[3]} for x in ind],
                  "mem_reads": [{"va": hex(x[0]), "mnem": x[2], "ops": x[3]} for x in memread],
                  "raw_FF_modrm_reg2or3_mod3_bytes": [hex(x) for x in ff23],
                  "has_indirect_call": len(ind) > 0,
                  "has_mem_read": len(memread) > 0}
    h["next6"] = nexts.get(h["va"], [])

buckets = {"both": 0, "indirect_call_only": 0, "mem_read_only": 0, "neither": 0}
for h in hits16:
    w = h["win48"]
    if w["has_indirect_call"] and w["has_mem_read"]: buckets["both"] += 1
    elif w["has_indirect_call"]: buckets["indirect_call_only"] += 1
    elif w["has_mem_read"]: buckets["mem_read_only"] += 1
    else: buckets["neither"] += 1
print("b buckets:", buckets)

# ---- e) base lands in .data GUID const zone 0x812000..0x880000 ----
def imm_in_zone(h):
    o = h["va"] - TVA
    bs = TB[o:o+16]
    found = []
    for i in range(len(bs)-3):
        v = int.from_bytes(bs[i:i+4], "little")
        if 0x812000 <= v < 0x880000: found.append((h["va"]+i, hex(v)))
    return found
e_hits = []
for h in hits16:
    f = imm_in_zone(h)
    if f: e_hits.append({"va": hex(h["va"]), "bytes": h["bytes"], "op": h["op"], "imm_in_zone": f})

res = {"q3": {
  "a": {"text": {"va": hex(TVA), "raw": hex(T["raw"]), "rawsize": hex(T["rawsize"])},
        "forms_used": {
          "shl_sal r/m32, imm8==4  (C1 /4 04)": sum(1 for h in hits16 if h["form"].startswith("shl")),
          "imul r32, r/m32, imm==0x10 (6B /r 10 or 69 /r 10000000)": sum(1 for h in hits16 if h["form"].startswith("imul")),
          "shl_sal r/m32, cl (D3 /4) counted but shift amount not static": cnt_cl,
          "lea with SIB scale any (max 8 in 32-bit, cannot make 16 alone)": cnt_lea_scale_any,
          "lea with SIB scale *8": cnt_lea_scale8,
        },
        "total_mul16_hits": len(hits16),
        "all_hits": [{"va": hex(h["va"]), "bytes": h["bytes"], "mn": h["mn"], "op": h["op"], "form": h["form"]} for h in hits16]},
  "b": {"window": "forward 48 bytes decoded from the hit address, instruction-aligned",
        "buckets": buckets,
        "per_hit": [{"va": hex(h["va"]), **h["win48"]} for h in hits16]},
  "c": {"first_n": min(40, len(hits16)),
        "items": [{"va": hex(h["va"]), "bytes": h["bytes"], "mnem": h["mn"], "ops": h["op"], "next6": h["next6"]} for h in hits16[:40]]},
  "d": {"reverse_control_8x": {"total": len(hits8),
                                "must_be_gt_16x_and_nonzero": (len(hits8) > len(hits16) and len(hits8) > 0),
                                "sample": [{"va": hex(h["va"]), "bytes": h["bytes"], "op": h["op"]} for h in hits8[:20]]}},
  "e": {"question": "any hit whose base/immediate lands in .data GUID const zone 0x812000..0x880000",
        "answer": ("yes" if e_hits else "no"),
        "hits": e_hits,
        "method": "scan the hit instruction's own bytes for a little-endian dword in [0x812000,0x880000)"},
}}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("e:", res["q3"]["e"]["answer"], e_hits[:10])
print("first hits:", [(h['va'], h['op']) for h in hits16[:10]])
