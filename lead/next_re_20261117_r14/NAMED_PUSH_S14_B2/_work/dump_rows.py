# -*- coding: utf-8 -*-
"""转储某批 entry 的完整反汇编（含字节），供逐行人工判 ③b②。用法: python dump_rows.py 19 24"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 19
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 36
# 卡片口径的全局序号 19..36 -> 本地 1..18
lo -= 18
hi -= 18

outp = os.path.join(WORK, "dump_%02d_%02d.txt" % (lo, hi))
f = open(outp, "w", encoding="utf-8")
def P(*a):
    print(*a, file=f)

for i, r in enumerate(ROWS, 1):
    if not (lo <= i <= hi):
        continue
    e = r["entry"]
    ea = int(e, 16)
    size = AN[e]["ring1"].get("atlas_size") or 0
    code = R.read_va(ea, size)
    P("=" * 100)
    P("ROW %02d  %s  name=%s  size=%d  in_text=%s" % (i, e, r["name"], size, R.in_text(ea)))
    P("=" * 100)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    for ins in md.disasm(code, ea):
        P("  %08X  %-22s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    # chA sites detail
    chA = AN[e]["chA"]
    P("  -- chA p1=%d p2=%d p3=%d --" % (chA["p1"], chA["p2"], chA["p3"]))
    for s in chA["sites"]:
        P("  SITE call@%08X -> %s" % (s["call_addr"], ("%08X" % s["callee"]) if s["callee"] else "INDIRECT"))
        P("       test@%08X %s imm=%s   jcc@%08X %s -> %s  (fallthrough %08X)" % (
            s["test_addr"], s["test_kind"], s["test_imm"], s["jcc_addr"], s["jcc_mnemonic"],
            ("%08X" % s["jcc_target"]) if s["jcc_target"] else "?", s["fallthrough"]))
        P("       falsy=%s form=%s" % (s["call_site_falsy"], s["p3_form"]))
        cp = s["callee_profile"]
        P("       callee_profile key=%s consts=%s n_rets=%s origins=%s" % (
            cp["callee_key"], cp["all_consts"], cp["n_rets"], cp["origins"]))
        P("       sig_taken      = %s" % (s["sig_taken"],))
        P("       sig_fallthrough= %s" % (s["sig_fallthrough"],))
f.close()
print("->", outp)
