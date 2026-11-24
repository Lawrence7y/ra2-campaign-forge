# -*- coding: utf-8 -*-
"""深核指定 entry 的 ③b② 站点：打印 hex 地址、call→jcc 反汇编窗口、taken/fall 路径、被调返回 profile。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
data = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
def va(x): return int(x, 16) if isinstance(x, str) else int(x)
def hx(x): return "%08X" % (x & 0xFFFFFFFF)
def dump(insns, i, j, tag):
    if j <= i: return
    print("   --- %s @%08X..%08X ---" % (tag, insns[i].address, insns[min(j,len(insns))-1].address))
    for k in range(i, min(j, len(insns))):
        print("     %08X %-7s %-30s | %s" % (insns[k].address, insns[k].mnemonic, insns[k].op_str, insns[k].bytes.hex()))

for e in sys.argv[1:]:
    r = data[e]; ea = va(e); size = r["atlas"].get("size", 512)
    insns = list(MD.disasm(R.read_va(ea, size), ea))
    idx = {ins.address: i for i, ins in enumerate(insns)}
    print("=" * 108)
    print("%s %s size=%s" % (e, r["hint_name"], size))
    for si, s in enumerate(r["chA_sites"]):
        ca = va(s["call_addr"]); ja = va(s["jcc_addr"]); jt = va(s["jcc_target"])
        cal = s.get("callee"); cal = va(cal) if cal else None
        print("-- site%d call=%s callee=%s test=%s imm=%s jcc=%s->%s form=%s falsy=%s" % (
            si, s["call_addr"], hx(cal) if cal else "None(indirect)", s["test_addr"], s["test_imm"],
            s["jcc_mnemonic"], hx(jt), s["p3_form"], s.get("call_site_falsy")))
        ci = idx.get(ca)
        if ci is not None:
            dump(insns, max(0, ci-3), min(len(insns), idx.get(ja, ci)+2), "call..jcc")
        ti = idx.get(jt)
        if ti is not None:
            dump(insns, ti, min(len(insns), ti+14), "TAKEN")
        dump(insns, idx.get(ja, 0)+1, min(len(insns), idx.get(ja, 0)+14), "FALLTHRU")
        if cal and R.in_text(cal):
            csz = R.ATLAS.get(hx(cal), {}).get("size", 160)
            cins = list(MD.disasm(R.read_va(cal, csz), cal))
            print("   CALLEE %s profile=%s" % (hx(cal), R.callee_return_profile(cal)))
            for ins in cins:
                if ins.mnemonic == "ret" or (ins.mnemonic in ("mov","or") and ins.op_str.startswith("eax,")):
                    print("      %08X %-6s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
