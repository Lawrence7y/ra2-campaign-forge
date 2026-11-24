# -*- coding: utf-8 -*-
"""④ 安装点宿主分类：对每行 vt 的全部安装点，dump 宿主函数首 18 条与末 10 条，
并给机械判定（是否 atexit、是否含序列 `mov [reg],vt` 前的基类 ctor call、是否含
`test byte [esp+x],1` + `call 0x7C8B3D` 的标量删除析构尾巴）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
SUR = json.load(open(os.path.join(WORK, "survey.json"), encoding="utf-8"))


def classify(host_va):
    hk = C.hx(host_va)
    sz = C.ATLAS.get(hk, {}).get("size") or 0
    if not sz:
        return {"key": hk, "size": None, "note": "atlas 无边界"}
    insns = C.disasm_body(host_va, sz)
    calls = [C.hx(i.operands[0].imm) for i in insns
             if i.mnemonic == "call" and i.operands and i.operands[0].type == 2]
    has_delete = any(i.mnemonic == "test" and "byte ptr [esp" in i.op_str for i in insns)
    has_free = any(i.mnemonic == "call" and i.operands and i.operands[0].type == 2
                   and i.operands[0].imm == 0x7C8B3D for i in insns)
    head = insns[:14]
    tail = insns[-10:]
    return {"key": hk, "size": sz, "n_insn": len(insns), "n_calls": len(calls),
            "first_calls": calls[:4], "has_delete_test": has_delete,
            "has_free": has_free, "atexit": C.is_atexit(host_va),
            "head": ["%08X %-8s %s" % (i.address, i.mnemonic, i.op_str) for i in head],
            "tail": ["%08X %-8s %s" % (i.address, i.mnemonic, i.op_str) for i in tail]}


seen = {}
out = {}
for s in SUR:
    r4 = s.get("ring4")
    if not r4:
        continue
    keys = []
    for st in r4["stores"]:
        if st["in_func_va"]:
            keys.append(st["in_func_va"])
    out[s["entry"]] = {"vt": r4["vt"], "hosts": sorted(set(keys))}
    for h in sorted(set(keys)):
        if h not in seen:
            seen[h] = classify(h)

lines = []
for e, v in out.items():
    lines.append("ROW %s vt=%s" % (e, v["vt"]))
    for h in v["hosts"]:
        c = seen[h]
        lines.append("  host %s size=%s n_insn=%s atexit=%s del_test=%s free=%s first_calls=%s" % (
            c["key"], c["size"], c.get("n_insn"), c.get("atexit"),
            c.get("has_delete_test"), c.get("has_free"), c.get("first_calls")))
        if c.get("head"):
            lines.append("    HEAD: " + " | ".join(c["head"][:8]))
            lines.append("    TAIL: " + " | ".join(c["tail"][-6:]))
lines.append("")
lines.append("# 未知边界宿主")
for h, c in sorted(seen.items()):
    if c.get("size") is None:
        lines.append(C.dump(h, 64, "## host %s (无 atlas 边界) 前后窗口" % C.hx(h)))

txt = "\n".join(lines) + "\n"
open(os.path.join(WORK, "hosts.txt"), "w", encoding="utf-8").write(txt)
print(txt)
