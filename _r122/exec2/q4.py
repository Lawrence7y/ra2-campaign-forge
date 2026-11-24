#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q4 · 带 skipdata 的线性扫描总条数，以及是否覆盖到 .text 末地址 0x7e1000

额外做分块线性扫描与整段扫描的一致性对照（证明"流式分块"不改变结果），
并给出 .byte 位置清单与总字节守恒检查。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q4.json")


def linear_sweep(text, va_base=C.TEXT_VA, chunk=None):
    """带 skipdata 的线性扫描。

    chunk=None 时一次性喂整段；否则按 chunk 字节分块（每块独立 Cs 实例，
    处理完即释放），用于证明分块与整段结果一致。
    返回 (总条数, 真实指令数, .byte 数, 末址, 分块末址列表)。

    分块正确性要点（首版在此处判 FAIL，已修）：
    如果直接把 text[pos:pos+chunk] 交给 capstone，块尾一条指令会被字节截断，
    capstone 解不出就退化成 .byte 只前进 1 字节，下一块就从指令中间起算，
    整体 desync（实测 64KB 分块 .byte 从 66 涨到 139、条数多出 114）。
    正确做法是每块多喂 LOOKAHEAD(=15, x86 指令长度上限) 字节的越界数据，
    且只接受「起始偏移 < 本块 core 长度」的指令 —— 这类指令的字节必然完整；
    块尾剩余部分回退到该指令末尾再续跑，保证 pos 永远落在真实指令边界上。
    """
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    LOOKAHEAD = 15          # x86 单条指令最大字节数
    n_tot = 0
    n_byte = 0
    chunk_ends = []
    if chunk is None:
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.skipdata = True
        last = va_base
        for addr, size, mnem, _o in md.disasm_lite(text, va_base):
            n_tot += 1
            if mnem == ".byte":
                n_byte += 1
            last = addr + size
        del md
        return n_tot, n_tot - n_byte, n_byte, last, [last]

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    pos = 0
    total = len(text)
    while pos < total:
        core = min(chunk, total - pos)              # 本块真正要消费的字节数
        seg_end = min(pos + core + LOOKAHEAD, total)  # 多喂越界数据
        seg = text[pos:seg_end]
        seg_va = va_base + pos
        consumed = 0
        last = seg_va
        for addr, size, mnem, _o in md.disasm_lite(seg, seg_va):
            off = addr - seg_va
            if off >= core:
                break          # 已越过本块 core，剩余交给下一块
            n_tot += 1
            if mnem == ".byte":
                n_byte += 1
            consumed = off + size
            last = addr + size
        if consumed == 0:
            break              # 防御性：避免死循环
        chunk_ends.append(last)
        pos += consumed
    del md
    return n_tot, n_tot - n_byte, n_byte, (chunk_ends[-1] if chunk_ends else va_base), chunk_ends


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    text = C.load_text(data)
    print("正在整段线性扫描（skipdata=True, disasm_lite, detail=False）…")
    n_tot, n_real, n_byte, last_end, _ = linear_sweep(text)

    print("\n== Q4 带 skipdata 的线性扫描 ==")
    print("扫描总条数（含 .byte）    = %d" % n_tot)
    print("其中真实指令              = %d" % n_real)
    print("其中 .byte 伪指令         = %d" % n_byte)
    print("扫描覆盖末址              = %s" % hex(last_end))
    print(".text 末地址              = %s" % hex(C.TEXT_END))
    print("是否覆盖到末地址          = %s" % (last_end == C.TEXT_END))

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    ck.check("线性扫描覆盖到 .text 末地址 0x7e1000",
             last_end == C.TEXT_END,
             "last_end=%s text_end=%s" % (hex(last_end), hex(C.TEXT_END)))
    ck.check("末址不小于段末（无截断）", last_end >= C.TEXT_END,
             "last_end=%s" % hex(last_end))
    ck.check("总条数 = 真实指令 + .byte", n_tot == n_real + n_byte,
             "%d == %d + %d" % (n_tot, n_real, n_byte))

    # 字节守恒：所有条目长度之和必须等于段长
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    total_bytes = 0
    prev = C.TEXT_VA
    gaps = 0
    for addr, size, _m, _o in md.disasm_lite(text, C.TEXT_VA):
        if addr != prev:
            gaps += 1
        total_bytes += size
        prev = addr + size
    del md
    ck.check("条目长度之和 == .text 尺寸（无空洞、无重叠）",
             total_bytes == len(text),
             "%d vs %d" % (total_bytes, len(text)))
    ck.check("地址连续无跳变（gaps==0）", gaps == 0, "gaps=%d" % gaps)

    # 分块一致性：64KB / 256KB 分块必须得到同一个总条数与末址
    print("\n分块对照（每块处理完释放 Cs 实例）…")
    results = {}
    for ch in (0x10000, 0x40000):
        t, r, b, le, ends = linear_sweep(text, chunk=ch)
        results[ch] = (t, r, b, le, ends)
        print("  chunk=0x%x => 条数=%d (real=%d byte=%d) 末址=%s 块数=%d"
              % (ch, t, r, b, hex(le), len(ends)))
    ck.check("64KB 分块条数与整段一致", results[0x10000][0] == n_tot,
             "%d vs %d" % (results[0x10000][0], n_tot))
    ck.check("64KB 分块末址与整段一致", results[0x10000][3] == last_end,
             "%s vs %s" % (hex(results[0x10000][3]), hex(last_end)))
    ck.check("256KB 分块条数与整段一致", results[0x40000][0] == n_tot,
             "%d vs %d" % (results[0x40000][0], n_tot))
    ck.check("256KB 分块末址与整段一致", results[0x40000][3] == last_end,
             "%s vs %s" % (hex(results[0x40000][3]), hex(last_end)))
    ck.check("两种分块互相一致",
             results[0x10000][0] == results[0x40000][0]
             and results[0x10000][3] == results[0x40000][3])

    # 对照：关掉 skipdata 会中断（Q4 的关键前提）
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.skipdata = False
    n_ns = 0
    last_ns = C.TEXT_VA
    for addr, size, _m, _o in md2.disasm_lite(text, C.TEXT_VA):
        n_ns += 1
        last_ns = addr + size
    del md2
    ck.check("对照：关 skipdata 则未覆盖段末（故 Q4 数字必须带 skipdata）",
             last_ns < C.TEXT_END,
             "no_skipdata 末址=%s 条数=%d" % (hex(last_ns), n_ns))

    summ = ck.summary()

    res = {
        "q": "Q4",
        "vault": "带 skipdata 的线性扫描总条数与末址覆盖",
        "sha256": sha,
        "capstone_version": __import__("capstone").__version__,
        "mode": "CS_MODE_32, disasm_lite, skipdata=True, detail=False",
        "linear_sweep_total_insns": n_tot,
        "real_insns": n_real,
        "byte_pseudo_insns": n_byte,
        "coverage_last_end": hex(last_end),
        "text_end": hex(C.TEXT_END),
        "covers_text_end": last_end == C.TEXT_END,
        "bytes_sum_matches_text_size": total_bytes == len(text),
        "chunked": {hex(k): {"insns": v[0], "last_end": hex(v[3]),
                             "chunks": len(v[4])} for k, v in results.items()},
        "no_skipdata_control": {"insns": n_ns, "last_end": hex(last_ns)},
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
