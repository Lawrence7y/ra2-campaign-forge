# -*- coding: utf-8 -*-
"""③ 形态扫描：对每行找
 - 跳转表（jmp [reg*4+disp]，③b①）
 - 回边（backward jcc/jmp → 循环，③b④ 候选）：给循环体起止、体内是否有非栈写
 - 站点（call→test/cmp eax→jcc）的被调返回常量
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))

STACKISH = ("[esp", "[ebp", "byte ptr [esp", "byte ptr [ebp")


def loops(insns, entry, size):
    out = []
    for i, ins in enumerate(insns):
        if ins.mnemonic not in C.JCC and ins.mnemonic != "jmp":
            continue
        if not ins.operands or ins.operands[0].type != 2:
            continue
        tgt = ins.operands[0].imm
        if tgt <= ins.address and entry <= tgt < entry + size:
            # 回边：循环体 = [tgt, ins.address+size)
            body = [x for x in insns if tgt <= x.address <= ins.address]
            writes = []
            for x in body:
                if x.mnemonic == "mov" and len(x.operands) == 2 and x.operands[0].type == 3:
                    dst = x.op_str.split(",")[0]
                    if not dst.startswith("byte ptr [esp") and not dst.startswith("byte ptr [ebp") \
                       and not dst.startswith("dword ptr [esp") and not dst.startswith("dword ptr [ebp") \
                       and not dst.startswith("word ptr [esp"):
                        writes.append(("%08X" % x.address, x.op_str))
            out.append({"latch": "%08X" % ins.address, "mn": ins.mnemonic,
                        "head": "%08X" % tgt, "n_body": len(body),
                        "writes": writes[:6], "n_writes": len(writes)})
    return out


for r in ROWS:
    e = r["entry"]
    ea = int(e, 16)
    size = C.ATLAS.get(e, {}).get("size") or 0
    insns = C.disasm_body(ea, size)
    jt = []
    for ins in insns:
        if ins.mnemonic == "jmp" and len(ins.operands) == 1 and ins.operands[0].type == 3:
            op = ins.operands[0].mem
            if op.scale == 4 and op.index != 0:
                jt.append(("%08X" % ins.address, ins.op_str))
    lp = loops(insns, ea, size)
    print("%s %-30s size=%-5d insn=%-5d 跳表=%d 回边=%d" % (e, r["name"], size, len(insns), len(jt), len(lp)))
    for x in jt:
        print("    JT %s %s" % x)
    for x in lp:
        print("    LOOP latch=%s(%s) head=%s n_body=%d nonstack_writes=%d %s" % (
            x["latch"], x["mn"], x["head"], x["n_body"], x["n_writes"],
            x["writes"][:3]))
