# -*- coding: utf-8 -*-
"""逐行 dump ③b② 站点上下文 + ② 槽/RTTI 细节，供人工裁定。输出 _work/dump.txt（UTF-8）。"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
OUT = open(os.path.join(WORK, "dump.txt"), "w", encoding="utf-8")

def P(*a):
    print(*a, file=OUT)

def dis_range(va, n, size=64):
    ins = R.disasm(va, R.read_va(va, size))
    return ins[:n]

def eax_clobber(insns, test_addr, jcc_addr):
    """test 与 jcc 之间是否覆写 eax。"""
    res = []
    for ins in insns:
        if ins.address <= test_addr or ins.address >= jcc_addr:
            continue
        w = False
        if ins.operands:
            o0 = ins.operands[0]
            if o0.type == X86_OP_REG and o0.reg == X86_REG_EAX:
                w = True
        if ins.id == X86_INS_CALL:
            w = True
        if w:
            res.append("%08X: %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return res

for rec in AN:
    entry = rec["entry"]
    P("=" * 100)
    P("ROW %s  %s   (idx %d)" % (entry, rec["name"], rec["idx"]))
    r1 = rec["ring1"]
    P("  ① in_text=%s atlas_size=%s n_disasm=%s skip=%s first=%s last=%s end_ok=%s" % (
        r1["in_text"], r1["atlas_size"], r1.get("n_disasm"), r1.get("n_skipdata"),
        r1.get("first"), r1.get("last"), r1.get("ends_with_ret_or_jmp")))
    # ②
    cueslot = None
    m = re.search(r"(?:v?slot)(\d+)$", rec["name"])
    if m:
        cueslot = int(m.group(1))
    P("  ② 线索槽号=%s" % cueslot)
    for s in rec["ring2_slots"]:
        if not s.get("rtti_name"):
            # 无 RTTI 的槽（可能是纯数据引用）
            P("     slot %s [%s] RTTI=None" % (s["slot_va"], s["section"]))
            continue
        off = s["slot_off"]
        P("     slot %s [%s] vtable=%s slot_off=+%d (slot#=%d) COL=%s TD=%s name=%s" % (
            s["slot_va"], s["section"], s["vtable_base"], off, off // 4, s["col"], s["td"], s["rtti_name"]))
        gw = s.get("global_writes") or []
        P("        ctor/install writes: %d" % len(gw))
        for g in gw[:12]:
            P("          write %s global=%s in_func=%s atexit=%s" % (
                g.get("write_va"), g.get("global"), g.get("in_func"), g.get("atexit")))
    P("  ④ direct callers: %s" % (rec["ring4_direct"][:12] or "none"))
    # ③
    chA = rec.get("chA") or {}
    P("  ③ chA p1=%s p2=%s p3=%s   chB=%s" % (chA.get("p1"), chA.get("p2"), chA.get("p3"), rec.get("chB")))
    size = r1.get("atlas_size") or 512
    insns = R.disasm(int(entry, 16), R.read_va(int(entry, 16), size))
    for s in chA.get("sites", []):
        P("  --- site call=%08X test=%08X(%s imm=%s) jcc=%08X %s -> %s" % (
            s["call_addr"], s["test_addr"], s["test_kind"], s["test_imm"],
            s["jcc_addr"], s["jcc_mnemonic"], ("%08X" % s["jcc_target"]) if s["jcc_target"] else None))
        P("      sig_taken=%s" % (s["sig_taken"],))
        P("      sig_fall =%s" % (s["sig_fallthrough"],))
        cp = s["callee_profile"]
        P("      callee=%s consts=%s n_rets=%s origins=%s" % (cp.get("callee_key"), cp.get("all_consts"), cp.get("n_rets"), cp.get("origins")))
        cl = eax_clobber(insns, s["test_addr"], s["jcc_addr"])
        P("      eax clobber in (test,jcc): %s" % (cl or "none"))
        # 上下文：call 前 3 条 到 call+14 条
        start = max(0, s["call_addr"])
        ctx = [i for i in insns if s["call_addr"] - 24 <= i.address <= s["call_addr"] + 64]
        for ins in ctx:
            P("        %08X: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
        # 两路各自前 12 条
        for lbl, tva in (("taken", s["jcc_target"]), ("fall", s["fallthrough"])):
            P("      [%s path]" % lbl)
            if tva:
                for ins in dis_range(tva, 12, 64):
                    P("        %08X: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
OUT.close()
print("dump -> dump.txt")
