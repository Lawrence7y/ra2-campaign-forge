import sys, json, re
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
hits16 = [int(h["va"],16) for h in res["q3"]["a"]["all_hits"]]
# build a map va->index for the whole .text decode (single pass, lite)
seq = [(a, sz, mn, op) for (a, sz, mn, op) in md.disasm_lite(TB, TVA)]
idx = {a: i for i, (a, sz, mn, op) in enumerate(seq)}
ZLO, ZHI = 0x812000, 0x880000
report = []
for h in hits16:
    i = idx[h]
    ctx = []
    for j in range(max(0, i-12), min(len(seq), i+3)):
        a, sz, mn, op = seq[j]
        b = TB[a-TVA:a-TVA+sz]
        for m in re.finditer(r"0x([0-9a-fA-F]+)", op):
            v = int(m.group(1), 16)
            if ZLO <= v < ZHI:
                ctx.append({"instr_va": hex(a), "mnem": mn, "ops": op, "bytes": b.hex(" "),
                            "imm": hex(v), "offset_from_hit": j - i})
    report.append({"hit_va": hex(h), "imm_in_zone_in_context": ctx})
yes = [r for r in report if r["imm_in_zone_in_context"]]
res["q3"]["e"] = {
  "question": "any 16x hit whose base register was loaded from an address in .data GUID zone 0x812000..0x880000",
  "method": "single-pass disasm_lite over .text; for each hit, scan operands of instructions [i-12, i+3] for an immediate in [0x812000,0x880000). Operand-level, not raw-byte (raw-byte window scan produced 1 false positive: 0x40ac9f window contains bytes 8d 85 14 00 00 ... where 0x85148d is a displacement fragment, not an immediate).",
  "answer": "yes" if yes else "no",
  "n_hits_with_zone_imm_in_context": len(yes),
  "detail": report}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print("answer:", res["q3"]["e"]["answer"], len(yes))
for r in yes: print(r["hit_va"], [(c["mnem"],c["ops"],c["offset_from_hit"]) for c in r["imm_in_zone_in_context"]])
