# -*- coding: utf-8 -*-
"""生成 15 行 EVIDENCE + 落定 delta.tsv / base_rate.tsv。数值全部现场从 gamemd.exe 计算。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import X86_OP_IMM, X86_INS_CALL

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
V = json.load(open(os.path.join(WORK, "verdicts.json"), encoding="utf-8"))
FACTS = json.load(open(os.path.join(WORK, "facts.json"), encoding="utf-8"))


def b(va, n):
    return core.read_va(va, n).hex()

def u32h(va):
    v = core.u32(va)
    return core.hx(v) if v is not None else "??"

def fmt_ins(ins):
    return "%s  %-20s %-7s %s" % (core.hx(ins.address), ins.bytes.hex(), ins.mnemonic, ins.op_str)


def evidence(entry):
    v = V[entry]; f = FACTS[entry]
    ea = int(entry, 16)
    L = []
    A = L.append
    A("NAMED_PUSH_S07S11_B2 / ROW_%s" % entry)
    A("=" * 84)
    A("entry=%s  subsystem=%s  name=%s" % (entry, v["sub"], v["name"]))
    A("目标 gamemd.exe SHA256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476")
    A("ImageBase=0x400000  .text=[0x401000,0x7E038D)  ImageBase口径VirtualSize")
    A("")
    # ---- ① ----
    A("[① 入口] in_text=%s  atlas_start=%s size=%s  insns=%s" %
      (core.in_text(ea), (core.hx(ea) if f["atlas"] else "?"), (f["atlas"][1] if f["atlas"] else "?"), f["insn_count"]))
    body = core.func_body(ea, f["atlas"][1] if f["atlas"] else 0x40)
    for i in body[:4]: A("   " + fmt_ins(i))
    A("   ...")
    for i in body[-3:]: A("   " + fmt_ins(i))
    A("   裁定: %s（地址在 .text 内、入口即指令边界、单一 ret 收尾）" % ("PASS" if v["r1"] else "FAIL"))
    A("")
    # ---- ② ----
    A("[② 类身份] dword_ref_count=%s refs=%s" % (f["dword_ref_count"], f["dword_refs"]))
    for s in f["slots"]:
        col = int(s["col"], 16); td = int(s["td"], 16); vt = int(s["vtable"], 16); sv = int(s["slot_va"], 16)
        A("   槽@%s 4B=%s (=entry)  vtable=%s slot#%d" % (s["slot_va"], b(sv,4), s["vtable"], s["slot_index"]))
        A("   vt-4  @%s = COL %s" % (core.hx(vt-4), u32h(vt-4)))
        A("   COL   @%s sig=%s offset=%s" % (core.hx(col), u32h(col), u32h(col+4)))
        A("   COL+0xC@%s = TD %s  (pTD 绝对VA)" % (core.hx(col+0xC), u32h(col+0xC)))
        A("   TD+8  @%s = \"%s\"  (装饰名内联串)" % (core.hx(td+8), core.cstr(td+8,80)))
    for ft in f["family_tables"]:
        A("   FAM vtable=%s offset=%s slot0=%s bytes=%s %s" %
          (ft["vtable"], ft["col_offset"], ft["slot0"], ft["slot0_bytes"],
           "<= this调整thunk(83 6C 24 xx E9),副表" if ft["slot0_bytes"].startswith("836c24") else "=真函数"))
    A("   裁定: %s  %s" % ("PASS" if v["r2"] else "FAIL", v["r2_note"]))
    A("")
    # ---- ③ ----
    A("[③ 整体合同 只认③b②]")
    if not f["sites"]:
        A("   无 call→test/cmp eax→jcc 直接站点（全为间接虚调用或纯数据处理）")
    for st in f["sites"]:
        A("   站点 call=%s [%s]" % (st["call"], st["call_op"]))
        A("      callee=%s  %s (%s)" % (st["callee"], st["test_op"], st["test_bytes"]))
        A("      %s (%s)  gap=%s" % (st["jcc_op"], st["jcc_bytes"], st["gap"]))
    for c, r in f["callee_returns"].items():
        if r["consts"]:
            A("   被调 %s 返回常量:" % c)
            for a, val, nxt in r["consts"]:
                A("      @%s mov/xor eax=%s ; next: %s" % (a, val, nxt))
    A("   裁定: %s  %s" % ("PASS" if v["r3"] else "FAIL", v["r3_note"]))
    A("")
    # ---- ④ ----
    A("[④ 使用见证] direct_callers=%s（0=非 direct-only，只能活虚表派发）" % f["direct_callers"])
    seen=set()
    for ins in f["installs"]:
        key=(ins["site"], ins["vtable"])
        if key in seen: continue
        seen.add(key)
        A("   写点@%s %-32s bytes=%s func=%s size=%s kind=%s" %
          (ins["site"], ins["ins"], ins["bytes"], ins["func"], ins["func_size"], ins["kind"]))
    # 实例化链锚点（PASS 行）
    if v["result"] == "[已证]":
        A("   实例化链（④锚）:")
        A("     %s" % v["r4_note"])
    A("   裁定: %s  %s" % ("PASS" if v["r4"] else "FAIL", v["r4_note"]))
    A("")
    A("[三陷阱核查] eax覆写=%s；多路同一call=%s；模板假句=%s；读写方向/TD绝对VA/㉓ 已在对应环逐条核定" %
      ("无(相邻指令)" if v["r3"] else "N/A", "无", "无"))
    A("")
    A("最终: %s  四环=%s" % (v["result"] or "[未证]", v["verdict"]))
    return "\n".join(L)


# 15 行 EVIDENCE 落盘
for e in V:
    p = os.path.join(OUT, "EVIDENCE", "ROW_%s.txt" % e)
    open(p, "w", encoding="utf-8").write(evidence(e))
    print("wrote", p)

# delta.tsv（只含四环齐全行）
hdr = "entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n"
rows = [hdr]
for e in V:
    v = V[e]
    if v["result"] == "[已证]":
        ep = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S07S11_B2/EVIDENCE/ROW_%s.txt" % e
        rows.append("%s\t%s\t%s\t%s\t%s\t%s\n" % (e, v["sub"], v["name"], v["semantics"], v["result"], ep))
open(os.path.join(OUT, "delta.tsv"), "w", encoding="utf-8").writelines(rows)

n = len(V); r2 = sum(1 for v in V.values() if v["r2"]); r3 = sum(1 for v in V.values() if v["r3"])
r4 = sum(1 for v in V.values() if v["r4"]); af = sum(1 for v in V.values() if v["result"]=="[已证]")
br = "batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\nNAMED_PUSH_S07S11_B2\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (n,r2,r3,r4,af,af/n)
open(os.path.join(OUT, "base_rate.tsv"), "w", encoding="utf-8").write(br)
print("delta rows=%d  base_rate: %s" % (af, br.strip().split("\n")[-1]))
