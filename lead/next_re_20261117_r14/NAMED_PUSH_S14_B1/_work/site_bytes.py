# -*- coding: utf-8 -*-
"""在每个候选站点给出精确指令序列（含原字节），用于 FAIL 行定性。输出 _work/site_bytes.txt"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import *

WORK = os.path.dirname(os.path.abspath(__file__))
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
out = open(os.path.join(WORK, "site_bytes.txt"), "w", encoding="utf-8")
def P(*a): print(*a, file=out)

for entry, rec in AN.items():
    size = rec["ring1"].get("atlas_size") or 256
    raw = R.read_va(int(entry, 16), size)
    P("=" * 96)
    P("ROW %s %s  body=[%s,+%d)" % (entry, rec["name"], entry, size))
    P("  entry16=%s" % raw[:16].hex(" "))
    sites = (rec.get("chA") or {}).get("sites", [])
    if not sites:
        P("  [no ③b② site]  chA=%s" % ({k: (rec.get("chA") or {}).get(k) for k in ("p1", "p2", "p3")}))
    for s in sites:
        P("  site call=%08X callee=%s" % (s["call_addr"], s["callee"] and "%08X" % s["callee"]))
        for addr in (s["call_addr"], s["test_addr"], s["jcc_addr"]):
            ins = list(R.disasm(addr, R.read_va(addr, 16)))[:1]
            if ins:
                i = ins[0]
                P("     %08X: %-8s %-28s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(" ")))
out.close()
print("ok")
