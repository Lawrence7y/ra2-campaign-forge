#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-4 精测：0x7775C0 的真实函数边界，以及「窗口无关性」到底能不能断言。

§398 §五 只说了「依赖窗口」，没量化。本脚本给出可直接落成断言的三个量：
  1. 函数真实尾部（最后一个 ret 的指令结束位置 + 其后填充 + 跳转表起点）
  2. 各窗口下「跟随分派表」的可达 ret 集
  3. 窗口越界后会捡到哪些**别的函数**的 ret（这就是必须设边界的理由）
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import capstone

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
ENTRY = 0x7775C0
JT_DWORDS = 0x777A80
JT_BYTES = 0x777A98
NTAB = 20


def pe_sections(b: bytes):
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    opt = pe + 24
    ib = struct.unpack_from("<I", b, opt + 28)[0]
    secs = []
    so = opt + optsz
    for k in range(nsec):
        o = so + k * 40
        vs, va, rs, ra = struct.unpack_from("<IIII", b, o + 8)
        secs.append((va, vs, ra, rs))
    return ib, secs


def main() -> int:
    b = EXE.read_bytes()
    ib, secs = pe_sections(b)

    def va2off(va):
        rva = va - ib
        for v, vs, ra, rs in secs:
            if v <= rva < v + max(vs, rs):
                return ra + (rva - v)
        return None

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    def linear(va, n):
        o = va2off(va)
        return list(md.disasm(b[o:o + n], va))

    dword_tbl = [struct.unpack_from("<I", b, va2off(JT_DWORDS) + 4 * i)[0]
                 for i in range(NTAB)]
    idx_tbl = list(b[va2off(JT_BYTES):va2off(JT_BYTES) + NTAB])
    table_targets = sorted({dword_tbl[e] for e in idx_tbl if e < NTAB})
    print("=" * 92)
    print("H-4 精测：0x%08X 函数边界与窗口无关性" % ENTRY)
    print("=" * 92)
    print("  分派表实际被索引到的目标（%d 个）: %s"
          % (len(table_targets), ["0x%08X" % t for t in table_targets]))

    # ---------- 1. 真实尾部 ----------
    print()
    print("--- 1. 函数体内的 ret，直到线性解码遇到**表数据**为止 ---")
    body = []
    for i in linear(ENTRY, JT_DWORDS - ENTRY):
        body.append(i)
    rets = [(i.address, i.op_str or "0", i.size) for i in body if i.mnemonic == "ret"]
    print("    线性解码 0x%08X..0x%08X 共 %d 条指令，其中 ret %d 个"
          % (ENTRY, JT_DWORDS, len(body), len(rets)))
    for a, s, sz in rets:
        print("      0x%08X  ret %-4s  指令止于 0x%08X" % (a, s, a + sz))
    last_addr, last_sz_s, last_sz = rets[-1]
    last_end = last_addr + last_sz
    pad = b[va2off(last_end):va2off(JT_DWORDS)]
    print("    最后一个 ret @0x%08X (ret %s) 止于 0x%08X" % (last_addr, last_sz_s, last_end))
    print("    它与跳转表 0x%08X 之间的 %d 字节：%s" % (JT_DWORDS, len(pad), pad.hex()))
    print("      （解码：%s）" % "; ".join("%s %s" % (i.mnemonic, i.op_str)
                                          for i in linear(last_end, len(pad))))

    # ---------- 2. 各窗口可达 ret（跟随分派表）----------
    print()
    print("--- 2. 跟随分派表的可达 ret 集 vs 窗口 ---")

    def reach(va, n, follow_table):
        code = {i.address: i for i in linear(va, n)}
        seen, oow = set(), set()
        work = [va]
        while work:
            a = work.pop()
            if a in seen:
                continue
            seen.add(a)
            i = code.get(a)
            if i is None:
                oow.add(a)
                continue
            if i.mnemonic == "ret":
                continue
            nxt = a + i.size
            if i.mnemonic == "jmp":
                op = i.op_str.replace(" ", "")
                if op.startswith("0x"):
                    work.append(int(op, 16))
                elif follow_table and "edx*4" in op:
                    work.extend(table_targets)
                continue
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                work.append(int(i.op_str, 16))
                work.append(nxt)
                continue
            work.append(nxt)
        sizes = {}
        for a in seen:
            i = code.get(a)
            if i is not None and i.mnemonic == "ret":
                s = int(i.op_str, 16) if i.op_str else 0
                sizes.setdefault(s, []).append(a)
        return sizes, seen, oow

    print("    %-8s %-6s %-6s %-26s %s"
          % ("窗口", "可达", "跳窗", "可达 ret 尺寸->地址", "跟随表"))
    for n in (0x40, 0x80, 0x100, 0x200, 0x300, 0x400, 0x4BD, 0x600, 0x1000, 0x2000):
        for ft in (False, True):
            sizes, seen, oow = reach(ENTRY, n, ft)
            desc = "; ".join("%s×%d(%s)" % (hex(k), len(v), " ".join("0x%X" % x for x in v[:3]))
                            for k, v in sorted(sizes.items()))
            print("    0x%-6X %-6d %-6d %-26s %s"
                  % (n, len(seen), len(oow), desc or "∅", "是" if ft else "否"))
        if n >= 0x400:
            print()

    # ---------- 3. 越界后捡到的外部 ret ----------
    print("--- 3. 窗口 0x2000 相对真实尾部（0x%08X）多捡了什么 ---" % last_end)
    sizes_big, _, _ = reach(ENTRY, 0x2000, True)
    for s, addrs in sorted(sizes_big.items()):
        outside = [a for a in addrs if a >= last_end]
        inside = [a for a in addrs if a < last_end]
        print("    ret %-4s 共 %2d 个：函数体内 %d（%s），函数体外 %d（%s）"
              % (hex(s), len(addrs), len(inside),
                 " ".join("0x%X" % a for a in inside) or "-", len(outside),
                 " ".join("0x%X" % a for a in outside[:4]) or "-"))
    print()
    print("    ⇒ 只要窗口越过 0x%08X，就会把**别的函数**的 ret 算进来，"
          % last_end)
    print("      「可达 ret 唯一」立刻从 {0x10} 变成多值 —— 这才是 H-4 的实质。")

    # ---------- 4. 现交付件 STEP 2 的窗口是否覆盖函数体 ----------
    print()
    print("--- 4. 现交付件 STEP 2 的窗口 0x400 覆盖到哪里 ---")
    win_end = ENTRY + 0x400
    inside = [a for a, _s, _z in rets if a < win_end]
    outside = [a for a, _s, _z in rets if a >= win_end]
    print("    窗口 0x%08X..0x%08X" % (ENTRY, win_end))
    print("    函数体内 %d 个 ret：窗口内 %d，窗口外 %d %s"
          % (len(rets), len(inside), len(outside),
             ["0x%08X" % a for a in outside]))
    print("    ⇒ %s" % ("窗口**截断**了函数体，尾部 ret 未参与判定"
                       if outside else "窗口覆盖完整函数体"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
