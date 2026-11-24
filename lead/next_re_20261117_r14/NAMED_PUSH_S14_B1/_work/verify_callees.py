# -*- coding: utf-8 -*-
"""① 被调返回约定全文；② 候选行 site 两路各 20 条。输出 _work/verify.txt"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(WORK, "verify.txt"), "w", encoding="utf-8")
def P(*a): print(*a, file=out)

CALLEES = [0x410380, 0x410320, 0x7C8E17, 0x523C90, 0x7C9CC2, 0x528A10, 0x524CB0,
           0x5117D0, 0x747370, 0x41CAA0, 0x727CF0, 0x7C8D20]
P("=" * 90); P("CALLEES")
for c in CALLEES:
    key = R.hx(c)
    size = R.ATLAS.get(key, {}).get("size")
    P("-" * 90)
    P("callee %s atlas_size=%s" % (key, size))
    if not size:
        P("  (no atlas size)")
        continue
    raw = R.read_va(c, size)
    P("  bytes[0:16]=%s" % raw[:16].hex(" "))
    for ins in R.disasm(c, raw):
        P("   %08X: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))

P("=" * 90); P("SITE PATHS")
SITES = [(0x41E540, 0x41E54B), (0x41FFF0, 0x420023), (0x4FB9B0, 0x4FBA49),
         (0x5024F0, 0x502506), (0x503040, 0x5031C9),
         (0x512290, 0x5122D0), (0x512480, 0x512491), (0x512760, 0x51279A),
         (0x65AC40, 0x65AC52), (0x691630, 0x69163B), (0x691690, 0x69169F),
         (0x691D90, 0x691D9B), (0x41F580, 0x41F783)]
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
for entry, callva in SITES:
    rec = AN["%08X" % entry]
    size = rec["ring1"].get("atlas_size") or 512
    insns = R.disasm(entry, R.read_va(entry, size))
    sites = [s for s in (rec.get("chA") or {}).get("sites", []) if callva is None or s["call_addr"] == callva]
    P("-" * 90)
    P("ROW %08X size=%d" % (entry, size))
    for s in sites:
        P("  site call=%08X test=%s imm=%s jcc=%s->%s" % (
            s["call_addr"], s["test_kind"], s["test_imm"], s["jcc_mnemonic"],
            "%08X" % s["jcc_target"] if s["jcc_target"] else "-"))
        for lbl, tva in (("taken", s["jcc_target"]), ("fall", s["fallthrough"])):
            P("   [%s]" % lbl)
            for ins in R.disasm(tva, R.read_va(tva, 96))[:22]:
                P("     %08X: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
out.close()
print("ok")
