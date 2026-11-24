# -*- coding: utf-8 -*-
"""B3 复核：① 带非栈写的循环上下文(③b④ 判定) ② slot值==entry 与 RTTI名 ③ 特殊常量 callee 调用点全上下文。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
def hx(x): return "%08X" % (x & 0xFFFFFFFF)
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
by = {r["entry"]: r for r in data}
def dis(adr,n): return list(MD.disasm(R.read_va(adr,n), adr))

print("########## ① 带非栈写的循环上下文 (③b④ 严格判定) ##########")
for e, lo, hi in [("00774CD0",0x774E20,0x774EF5), ("007A3100",0x7A31C0,0x7A3225),
                  ("007A5890",0x7A6630,0x7A6680)]:
    print("\n=== %s  region [%s,%s) ===" % (e, hx(lo), hx(hi)))
    for i in dis(lo, hi-lo):
        print("  %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))

print("\n\n########## ② slot 值==entry 与 RTTI 名逐行确认 ##########")
for r in data:
    e = r["entry"]; ea = int(e,16)
    ok=[]
    for s in r["slots"]:
        if s.get("rtti_name"):
            sv = R.u32(int(s["slot_va"],16))
            ok.append("vt=%s off=%+d slotval=%s [%s] %s" % (s["vtable_base"], s["slot_off"],
                        hx(sv) if sv else None, "==entry" if sv==ea else "MISMATCH",
                        s["rtti_name"]))
    print("%s %-24s : %s" % (e, r["hint_name"][:24], " | ".join(ok)))

print("\n\n########## ③ 特殊常量 callee 调用点全上下文（最强 ③b② 希望） ##########")
# 0x889f64 used at 007A5890 007A6A74, 007A7110 007A75AD, 007A8260 007A8410
for e, calladr in [("007A5890",0x7A6A5E),("007A7110",0x7A7598),("007A8260",0x7A83FB),
                   ("007A41C0",0x7A4BA5)]:  # 0x84583c at 007A4BBB
    print("\n=== %s around call-site (front +/-) ===" % e)
    for i in dis(calladr, 0x50):
        mark = " <CALL>" if i.id==0xE8 else ""
        print("  %08X %-7s %-30s | %s%s" % (i.address,i.mnemonic,i.op_str,i.bytes.hex(),mark))
