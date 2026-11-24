# -*- coding: utf-8 -*-
"""验证 B2 两个 ③b② 候选的细节 + 复核边界行的 ②（虚表槽/RTTI）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
def hx(x): return "%08X" % (x & 0xFFFFFFFF)
def dis(va, n=80):
    return list(MD.disasm(R.read_va(va, n), va))

print("=== 0071F8C0 full body ===")
for i in dis(0x71F8C0, 111):
    print("  %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))

print("\n=== vtable 0x7F5578 slots ===")
for k in range(16):
    v = R.u32(0x7F5578 + 4*k)
    print("  +0x%02X slot%d @%08X = %s" % (4*k, k, 0x7F5578+4*k, hx(v) if v else None))
col = R.u32(0x7F5574)
print("  COL@vt-4 =", hx(col) if col else None)
if col:
    td = R.u32(col+0xC)
    print("  TD =", hx(td) if td else None, "name=", W.read_cstr(td+8, 200) if td else None)

print("\n=== callee 0x410380 body ===")
for i in dis(0x410380, 96):
    print("  %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))

print("\n=== 0064A0C0 witness ===")
refs = W.find_dword_refs(0x64A0C0)
print("  find_dword_refs:", [(hx(v), s) for v,s in refs])
w = W.witness_entry("0064A0C0")
print("  slots:", json.dumps(w["slots"], ensure_ascii=False))
print("  direct_callers:", w["direct_callers"])

for e in ["005C44E0","005C46E0","005C4CA0","005CAAC0"]:
    ea=int(e,16); refs=W.find_dword_refs(ea)
    print("\n=== %s refs: %s ===" % (e, [(hx(v),s) for v,s in refs]))
    for v,s in refs:
        print("   ref@%s resolve_slot=%s" % (hx(v), W.resolve_slot(v)))
        print("   context dwords: " + " ".join(hx(R.u32(v-16+4*k) or 0) for k in range(9)))
