#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-4 归属核查：到底是**哪个**脚本的 ret 尺寸结论依赖窗口边界。

§398 §五 把 H-4 登记成「`_todo7_creation_trigger.py` 的 ret 尺寸结论依赖窗口边界」，
但它引的证据是 `0x6930A0` / `0x778030` 在不同窗口下变化 —— 这两个函数**不在**
`_todo7_creation_trigger.py` 里算 ret 尺寸（该脚本只扫 `0x7775C0` 找 ret 0x10）。
本脚本把三件事分开量：

  A. `0x6930A0` 的**可达** ret 集 vs 窗口（用交付件同款 CFG 方法）
  B. `0x778030` 同上
  C. `0x7775C0` 的函数体边界（`_todo7_creation_trigger.py` 真正的缺口）

判据：只要「可达 ret 集」在某窗口 W 之后不再变化，就说明 W 是安全窗口；
若交付件用的窗口 < W，则结论**在交付件里没有被证明**。
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import capstone

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WINDOWS = (0x100, 0x200, 0x300, 0x400, 0x500, 0x800, 0xB00,
           0x1000, 0x1800, 0x2000, 0x2400, 0x3000, 0x4000, 0x6000, 0x8000)


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

    def analyse(entry, label, table_va=None):
        print()
        print("--- %s  0x%08X ---" % (label, entry))
        tbl_targets = []
        if table_va:
            raw = b[va2off(table_va):va2off(table_va) + 20 * 4]
            tbl = [struct.unpack_from("<I", raw, 4 * i)[0] for i in range(20)]
            idx = b[va2off(table_va + 0x18):va2off(table_va + 0x18) + 20]
            tbl_targets = sorted({tbl[e] for e in idx if e < 20})
            print("    分派表目标 %d 个: %s"
                  % (len(tbl_targets), ["0x%X" % t for t in tbl_targets]))

        def reach(win):
            o = va2off(entry)
            code = {i.address: i for i in md.disasm(b[o:o + win], entry)}
            seen, oow = set(), set()
            work = [entry]
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
                    elif table_va and "edx*4" in op:
                        work.extend(tbl_targets)
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
                    sizes.setdefault(int(i.op_str, 16) if i.op_str else 0, []).append(a)
            return sizes, len(seen), oow

        print("    %-8s %-6s %-5s %-30s %s"
              % ("窗口", "可达", "跳窗", "可达 ret 尺寸(个数)", "末个 ret 地址"))
        prev = None
        rows = []
        for w in WINDOWS:
            s, n, oow = reach(w)
            key = tuple(sorted(s))
            last = max((max(v) for v in s.values()), default=0)
            mark = "" if prev is None else ("  同" if key == prev else "  ★变")
            print("    0x%-6X %-6d %-5d %-30s 0x%08X%s"
                  % (w, n, len(oow),
                     ", ".join("%s×%d" % (hex(k), len(v)) for k, v in sorted(s.items())) or "∅",
                     last, mark))
            rows.append((w, key, len(oow)))
            prev = key

        tail = rows[-1][1]
        stable = next((w for w, k, oow in rows
                       if k == tail and not oow
                       and all(kk == tail and not oo for _w, kk, oo in rows
                               if _w >= w)), None)
        print("    ⇒ 收敛集合 %s；不跳窗且稳定的最小窗口 = %s"
              % (list(tail), ("0x%X" % stable) if stable else "无"))
        return tail, stable

    print("=" * 96)
    print("H-4 归属核查：谁的 ret 结论依赖窗口")
    print("=" * 96)

    a_tail, a_stable = analyse(0x6930A0, "A. §398 引用的 0x6930A0")
    bb_tail, b_stable = analyse(0x778030, "B. §398 引用的 0x778030")

    print()
    print("--- C. `_todo7_creation_trigger.py` 的真缺口：0x7775C0 的函数体边界 ---")
    o = va2off(0x7775C0)
    ins = list(md.disasm(b[o:o + 0x4C0], 0x7775C0))
    rets = [(i.address, i.op_str or "0", i.size) for i in ins if i.mnemonic == "ret"]
    last_a, last_s, last_sz = rets[-1]
    end = last_a + last_sz
    pad = b[va2off(end):va2off(0x777A80)]
    print("    线性解码 0x7775C0 + 0x4C0：%d 条指令，ret %d 个" % (len(ins), len(rets)))
    print("    末 ret 0x%08X (ret %s) 止于 0x%08X，其后 %d 字节填充 %s，"
          "紧接跳转表 0x777A80" % (last_a, last_s, end, len(pad), pad.hex()))
    print("    全部 ret 尺寸集合 = %s" % sorted({s for _a, s, _z in rets}))
    print("    交付件 STEP 2 用的窗口 = 0x400，只覆盖到 0x%08X"
          % (0x7775C0 + 0x400))
    inwin = [a for a, _s, _z in rets if a < 0x7775C0 + 0x400]
    print("    ⇒ 0x400 窗口内 %d/%d 个 ret，漏掉 %d 个（0x%X 之后的）"
          % (len(inwin), len(rets), len(rets) - len(inwin), 0x7775C0 + 0x400))

    print()
    print("=" * 96)
    print("结论")
    print("=" * 96)
    print("  0x6930A0 收敛集合 %s，稳定窗口 %s" % (list(a_tail), a_stable))
    print("  0x778030 收敛集合 %s，稳定窗口 %s" % (list(bb_tail), b_stable))
    print("  ⇒ §398 §五 说「0x6930A0 放到 0x694000 就有三种尺寸」")
    print("    实测用 CFG 方法：在 0x%X 窗口就已稳定为 %s"
          % (a_stable or 0, list(a_tail)))
    print("  ⇒ 若仍然线性扫全窗口（不跟 CFG），才会捡到别的函数的 ret。")
    print("  ⇒ `_todo7_creation_trigger.py` 的缺口与上面两个函数**不同**：")
    print("    它是窗口 0x400 **截断**了 0x7775C0 的函数体（11 个 ret 只看 8 个）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
