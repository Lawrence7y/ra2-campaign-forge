# -*- coding: utf-8 -*-
"""B3 深度取证：① 跳转表(007A5290)逐路地址+字节+写指令；② 特殊常量 callee 返回 profile；
③ 全批查 signed-jcc(HRESULT) 与非 bool 错误码站点。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_RET, X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_OR
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
def hx(x): return "%08X" % (x & 0xFFFFFFFF)
def va(x): return int(x,16) if isinstance(x,str) else int(x)
def dis(adr, n): return list(MD.disasm(R.read_va(adr, n), adr))

data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
by = {r["entry"]: r for r in data}

print("########## A. 全批 callee 返回常量汇总（找非 bool 错误码） ##########")
seen = {}
for r in data:
    for s in r["chA_sites"]:
        cp = s["callee_profile"]; c = s.get("callee")
        consts = cp.get("all_consts") or []
        for cc in consts:
            seen.setdefault(cc, []).append((r["entry"], hx(va(s["call_addr"])), s["test_kind"], s["test_imm"], s["jcc_mnemonic"]))
for cc in sorted(seen):
    print("const %-12s used %d times: %s" % (cc, len(seen[cc]), seen[cc][:6]))

print("\n########## B. 特殊 callee body 逐 ret 反查 ##########")
for c in [0x7B5440, 0x7B5400, 0x734E60, 0x7B46F0, 0xCAF30, 0x7CAF30, 0x40C0 if False else 0x4068E0]:
    if not c: continue
    print("\n=== callee %s ===" % hx(c))
    code = R.read_va(c, 160)
    if not code:
        print("  (no code)"); continue
    eax = "?"
    for i in dis(c, 160):
        if i.id == 0: continue
        if i.mnemonic in ("xor","sub") and i.op_str == "eax, eax": eax="0"
        elif i.mnemonic == "mov" and i.op_str.startswith("eax, "): eax=i.op_str.split(",",1)[1].strip()
        elif i.mnemonic == "or" and i.op_str.startswith("eax, "): eax="OR "+i.op_str.split(",",1)[1].strip()
        mark = ""
        if i.id == X86_INS_RET: mark = "   <<< RET eax=%s" % eax
        print("  %08X %-7s %-32s | %s%s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(), mark))
        if i.id == X86_INS_RET: eax="?"

print("\n########## C. 007A5290 跳转表逐路 ##########")
r = by["007A5290"]
for t in r["chB"]:
    print("jmp@%s %s bound=%s ncase=%s table_va=%s" % (t["jmp_addr"], t["op_str"], t["bound"], t["ncase"], t["table_va"]))
    # 打印跳表前边界检查
    print("  --- 边界检查上下文 (jmp 前) ---")
    ja = va(t["jmp_addr"])
    for i in dis(ja-32, 40):
        print("    %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
    tv = va(t["table_va"]) if t.get("table_va") else None
    # 从 analysis 中 targets 已知；再直接读表
    if tv:
        print("  --- 跳表条目 ---")
        for k in range(int(t["ncase"])):
            print("    case%2d @%s -> %s" % (k, hx(tv+4*k), hx(R.u32(tv+4*k) or 0)))
    print("  --- 各 target 前 12 条指令（找写内存/边界） ---")
    for tg in t["targets"]:
        ta = va(tg["target"])
        print("    == case%s target %s ==" % (tg["case"], hx(ta)))
        for i in dis(ta, 44)[:12]:
            print("       %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
