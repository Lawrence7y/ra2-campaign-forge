# -*- coding: utf-8 -*-
"""复核：005C46E0 的 ③b① 跳表；0071F8C0 与 0064A0C0 的 ③b② 最终判定要素。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
data = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
def hx(x): return "%08X" % (int(x)&0xFFFFFFFF)

print("=== 005C46E0 chB jump tables ===")
r = data["005C46E0"]
for t in r["chB"]:
    print("  jmp@%s %s %s table=%s bound=%s ncase=%s targets=%d" % (
        t["jmp_addr"], t["mnemonic"], t["op_str"], t["table_va"], t["bound"], t["ncase"], len(t["targets"])))
    for x in t["targets"][:40]:
        print("     case%-3d -> %s (slot_va %s)" % (x["case"], x["target"], x["slot_va"]))
    # 打印 jmp 前的边界检查反汇编
    ja = int(t["jmp_addr"],16)
    print("     --- 20 insn before jmp ---")
    ins = list(MD.disasm(R.read_va(ja-60, 70), ja-60))
    for i in ins:
        print("       %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))

print("\n=== 0071F8C0 ③b②要素 ===")
r = data["0071F8C0"]
print("  chA:", r["chA"], "eax_trap:", r["chA_eax_trap"])
for s in r["chA_sites"]:
    print("  call=%s callee=%s test=%s jcc=%s->%s p3form=%s" % (
        s["call_addr"], s.get("callee"), s["test_addr"], s["jcc_mnemonic"], s.get("jcc_target"), s["p3_form"]))
    print("    callee_profile:", s["callee_profile"])
    print("    T=", s["sig_taken"])
    print("    F=", s["sig_fallthrough"])
print("  slot:", [(s.get("slot_va"), s.get("slot_off"), s.get("rtti_name"), len(s.get("dispatch_sites",[])), len(s.get("global_writes",[]))) for s in r["slots"]])

print("\n=== 0064A0C0 ③b②要素(②FAIL但如实判③) ===")
r = data["0064A0C0"]
print("  chA:", r["chA"])
for s in r["chA_sites"]:
    print("  call=%s callee=%s test=%s imm=%s jcc=%s->%s p3form=%s" % (
        s["call_addr"], s.get("callee"), s["test_addr"], s["test_imm"], s["jcc_mnemonic"], s.get("jcc_target"), s["p3_form"]))
