# -*- coding: utf-8 -*-
"""W173 [+0x94] 精确分析：
 A) 全部 mov dword [basereg+0x94], src，按 base 分 stack(esp/ebp) 与 object
 B) object 字段写按写入值分类：-1 / 0..4 / 其它imm / reg
 C) 每个 object 字段写的 base reg 回溯 + 源 reg 回溯
 D) 层号 0..4 / -1 写点全列出
"""
from __future__ import annotations
import os
import sys
import bisect
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID


def find_writes(ins, lo, hi, reg):
    out = []
    for j in range(lo, hi):
        r = ins[j]
        if r["mn"] in ("cmp", "test", "push", "nop"):
            continue
        if r["ops"] and r["ops"][0]["kind"] == "reg" and r["ops"][0]["name"] == reg:
            out.append(j)
    return out


def trace(ins, lo, hi, reg, depth=0, maxdepth=4, seen=None):
    if seen is None:
        seen = set()
    pad = "  " * depth
    if depth > maxdepth:
        return [pad + "...(depth limit)"]
    ws = find_writes(ins, lo, hi, reg)
    if not ws:
        return [pad + "%s: 区间内无写点(参数/进入前已置/返回值)" % reg]
    out = []
    for j in ws[-6:]:
        r = ins[j]
        out.append(pad + "W %08X %s" % (r["va"], C.fmt(r).split("  ", 1)[-1]))
        for op in r["ops"][1:]:
            if op["kind"] == "reg" and op["name"] != reg and (op["name"], j) not in seen:
                seen.add((op["name"], j))
                out.extend(trace(ins, lo, j, op["name"], depth + 1, maxdepth, seen))
            elif op["kind"] == "mem" and op["base"] and (op["base"], j) not in seen:
                seen.add((op["base"], j))
                out.extend(trace(ins, lo, j, op["base"], depth + 1, maxdepth, seen))
    if any(ins[k]["mn"] == "call" for k in range(ws[-1] + 1, hi)):
        out.append(pad + "!! 最后写点后有 call：eax/ecx/edx 可能被 caller-saved 破坏")
    return out


def main():
    ins = C.text_insns()
    v = C.vas()
    all_rows = []
    for j, r in enumerate(ins):
        if r["mn"] != "mov" or len(r["ops"]) < 2:
            continue
        d, s = r["ops"][0], r["ops"][1]
        if d["kind"] != "mem" or d["base"] is None:
            continue
        if d["disp"] != C.W94_OFF:
            continue
        all_rows.append((j, r, d, s))

    L = ["=" * 95, "W173 [+0x94] 全量分析（capstone skipdata=True; .text 全扫）",
         " mov [basereg+0x94], src 原始命中(所有宽度): %d" % len(all_rows)]
    dword_rows = [(j, r, d, s) for j, r, d, s in all_rows if d["size"] == 4]
    stack_rows = [(j, r, d, s) for j, r, d, s in dword_rows if d["base"] in ("esp", "ebp")]
    obj_rows = [(j, r, d, s) for j, r, d, s in dword_rows if d["base"] not in ("esp", "ebp")]
    L.append(" 其中 size=4 (dword): %d" % len(dword_rows))
    L.append("  base=esp/ebp (栈槽,非对象字段): %d" % len(stack_rows))
    L.append("  base=其它寄存器 (对象字段候选): %d" % len(obj_rows))

    def cls(s):
        if s["kind"] == "imm":
            x = s["val"] & 0xFFFFFFFF
            if x == 0xFFFFFFFF:
                return "-1"
            if 0 <= x <= 4:
                return "L%d" % x
            return "imm:0x%X" % x
        if s["kind"] == "reg":
            return "reg:" + s["name"]
        if s["kind"] == "mem":
            return "mem"
        return "?"

    cnt = Counter(cls(s) for j, r, d, s in obj_rows)
    L.append("")
    L.append("对象字段写按值分类: %r" % dict(cnt))
    L.append("（L0..L4 = 立即数 0..4 即层号；-1 = 无层；reg = 寄存器值；imm:0xX = 其它立即数）")

    L.append("")
    L.append("=" * 95)
    L.append("★ 层号立即数 L0..L4 写点（对象字段 + 栈槽都列出以核对）")
    for j, r, d, s in all_rows:
        if s["kind"] == "imm" and 0 <= (s["val"] & 0xFFFFFFFF) <= 4:
            o = C.owner(r["va"], "atlas")
            L.append("  %08X  %s  base=%s size=%s fn=%s" % (
                r["va"], C.fmt(r), d["base"], d["size"],
                ("%08X" % o[0]) if o else "NONE"))

    L.append("")
    L.append("=" * 95)
    L.append("★ -1 (0xffffffff) 写点")
    for j, r, d, s in all_rows:
        if s["kind"] == "imm" and (s["val"] & 0xFFFFFFFF) == 0xFFFFFFFF:
            o = C.owner(r["va"], "atlas")
            L.append("  %08X  %s  base=%s size=%s fn=%s" % (
                r["va"], C.fmt(r), d["base"], d["size"],
                ("%08X" % o[0]) if o else "NONE"))

    L.append("")
    L.append("=" * 95)
    L.append("★ 对象字段写逐点明细（base!=esp/ebp）：base 回溯 + 源 回溯")
    for j, r, d, s in obj_rows:
        va = r["va"]
        o = C.owner(va, "atlas")
        lo = bisect.bisect_left(v, o[0]) if o else max(0, j - 100)
        c = cls(s)
        L.append("-" * 90)
        L.append("W %08X  %s  [%s]" % (va, C.fmt(r), c))
        L.append("  fn(atlas)=%s  fn(synth)=%s" % (
            ("%08X" % o[0]) if o else "NONE",
            ("%08X" % C.owner(va, "synth")[0]) if C.owner(va, "synth") else "NONE"))
        L.append("  base=%s 回溯:" % d["base"])
        L.extend("    " + x for x in trace(ins, lo, j, d["base"]))
        if s["kind"] == "reg":
            L.append("  源=%s 回溯:" % s["name"])
            L.extend("    " + x for x in trace(ins, lo, j, s["name"]))
        L.append("  上下文(前10后4):")
        for k in range(max(0, j - 10), min(len(ins), j + 5)):
            L.append("    %s %s" % (">>" if k == j else "  ", C.fmt(ins[k])))

    L.append("")
    L.append("=" * 95)
    L.append("★ 栈槽 [esp/ebp+0x94] 全列（纪律6：栈参数判断须给取值集合与最大值）")
    for j, r, d, s in stack_rows:
        L.append("  %08X %s" % (r["va"], C.fmt(r)))

    C.write_text(os.path.join(E, "w173_w94_precise.txt"), L)
    print("w94 precise: all=%d dword=%d stack=%d obj=%d L0..4=%d neg1=%d" % (
        len(all_rows), len(dword_rows), len(stack_rows), len(obj_rows),
        sum(1 for x in cnt if x.startswith("L")),
        sum(1 for x in cnt if x == "-1")))


if __name__ == "__main__":
    main()
