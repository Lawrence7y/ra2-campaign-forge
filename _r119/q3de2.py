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
hits16 = res["q3"]["a"]["all_hits"]

# ---- d) 8x control, identical method, imm == 8 ----
h8 = []
for (a, sz, mn, op) in insns:
    b = TB[a-TVA:a-TVA+sz]
    if mn in ("shl", "sal") and b[0] == 0xC1 and ((b[1] >> 3) & 7) == 4 and b[2] == 8:
        h8.append({"va": hex(a), "bytes": b.hex(" "), "op": op, "kind": "shl_rm32_imm8==8"})
    if mn in ("shl", "sal") and b[0] == 0xC0 and ((b[1] >> 3) & 7) == 4 and b[2] == 8:
        h8.append({"va": hex(a), "bytes": b.hex(" "), "op": op, "kind": "shl_rm8_imm8==8"})
    if mn == "imul":
        p = op.split(",")
        if len(p) == 3 and p[2].strip() in ("8", "0x8"):
            h8.append({"va": hex(a), "bytes": b.hex(" "), "op": op, "kind": "imul_imm8"})
res["q3"]["d"] = {"reverse_control_16_to_8": {
  "method": "identical single-pass sweep + identical form matching, multiplier 16 replaced by 8",
  "count_8x": len(h8), "count_16x": len(hits16),
  "by_kind": {k: sum(1 for x in h8 if x["kind"] == k) for k in sorted({x['kind'] for x in h8})},
  "pass_condition_8_gt_16_and_nonzero": len(h8) > len(hits16) and len(h8) > 0,
  "sample": h8[:20]}}

# ---- e) strict backward def-use on the shifted register ----
BRANCH = {"jmp","je","jne","jz","jnz","jl","jle","jg","jge","jb","jbe","ja","jae","js","jns","jc","jnc","jo","jno","jp","jnp","loop","ret","call","retn"}
def dest_reg(mn, op):
    if not op.strip(): return None
    return op.split(",")[0].strip()

def regs_in(op):
    return set(re.findall(r"\b(eax|ebx|ecx|edx|esi|edi|ebp|esp|[abcd]l|[abcd]h|si|di|bp|sp|al|bl|cl|dl)\b", op))

ZLO, ZHI = 0x812000, 0x880000
strict = []
for h in hits16:
    i = idx[h["va"]]
    a, sz, mn, op = insns[i]
    tgt = dest_reg(mn, op)
    if not tgt: continue
    # aliasing: treat 32-bit reg and its 16/8-bit forms as the same for writes
    base32 = {"eax":"eax","ax":"eax","al":"eax","ah":"eax","ebx":"ebx","bx":"ebx","bl":"ebx","bh":"ebx",
              "ecx":"ecx","cx":"ecx","cl":"ecx","ch":"ecx","edx":"edx","dx":"edx","dl":"edx","dh":"edx",
              "esi":"esi","si":"esi","edi":"edi","di":"edi","ebp":"ebp","bp":"ebp","esp":"esp","sp":"esp"}[tgt]
    found = None
    j = i - 1
    steps = 0
    while j >= 0 and steps < 40:
        a2, sz2, mn2, op2 = insns[j]
        if mn2 in BRANCH: break
        d2 = dest_reg(mn2, op2)
        if d2 and base32 in regs_in(d2): 
            # this instruction defines the register: is it a load from an absolute in-zone address?
            for m in re.finditer(r"0x([0-9a-fA-F]+)", op2):
                v = int(m.group(1), 16)
                if ZLO <= v < ZHI:
                    found = {"def_instr_va": hex(a2), "bytes": TB[a2-TVA:a2-TVA+sz2].hex(" "),
                             "mnem": mn2, "ops": op2, "imm": hex(v), "dist": i - j}
            break
        # keep searching only across instructions that do not touch the reg
        j -= 1; steps += 1
    strict.append({"hit_va": h["va"], "hit_ops": h["op"], "tracked_reg": tgt,
                   "def_instr": found,
                   "def_loads_from_data_guid_zone": bool(found)})
yes = [s for s in strict if s["def_loads_from_data_guid_zone"]]
res["q3"]["e"] = {
 "question": "does any 16x-scaling site operate on a value whose defining instruction loads from an absolute address inside .data 0x812000..0x880000",
 "strict_backward_def_use": {"window": "up to 40 instructions backwards, stops at any branch/call/ret and at the first write to the scaled register (8/16/32-bit aliases merged)",
   "n_hits": len(strict), "answer": "yes" if yes else "no", "n_yes": len(yes), "yes": yes,
   "detail": strict},
 "loose_immediate_in_context": {"definition": "any instruction within [hit-12 .. hit+2] whose operand contains an immediate in 0x812000..0x880000",
   "n": len(res["q3"]["e"]["hits"]) if "hits" in res["q3"]["e"] else None,
   "note": "looser than the question; kept only as a sanity aid"},
 "caveat": "indirect/aliased bases (e.g. ebp-relative struct field then scaled) are NOT resolved; only direct absolute immediates are."
}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("8x:", len(h8), "16x:", len(hits16), "pass:", len(h8) > len(hits16))
print("e strict:", res["q3"]["e"]["strict_backward_def_use"]["answer"], len(yes))
for s in yes[:10]: print("  ", s)
print("non-yes sample:", strict[:5])
