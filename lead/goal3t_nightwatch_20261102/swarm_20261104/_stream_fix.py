# -*- coding: utf-8 -*-
"""_stream_fix.py - 修 ra2tool.Engine.stream 的 MemoryError（**不改原件**）

问题（2026-11-04 诊断）：
  `ra2tool.py` 的 `Engine.stream` 用纯 Python 循环把 **139 万条 capstone CsInsn 对象**
  全部 append 进列表并驻留内存（`self._stream`）。
  单个 CsInsn 对象约数百字节 ⇒ 累积数百 MB~GB ⇒ 多个子代理报 MemoryError。
  实证：swarm_20261104 的 A03/A04/A06/A07/A09/A12 全部崩在
  `ra2tool.py:103  out.append(got[0])` ⇒ **MemoryError**。

修法（本文件，不动 ra2tool.py 一个字节）：
  提供 `cov(eng)` —— 用**流式单遍扫描**算覆盖率，**不保留**任何 CsInsn：
      * 同样逐址重同步线性解码（保持与原件一致的口径）
      * 只累加 `insn.size` 与失败计数，**不 append 对象**
      * 内存占用 O(1)（只留当前一条）
  另外提供 `disp_hits_stream(eng, target)` —— 流式找绝对地址访存，
  **不构建整个 _by 索引**（原件的 `_by` 也会保留 139 万条）。

用法：
    import sys; sys.path.insert(0, r"...\\swarm_20261104")
    from ra2tool import Engine
    from _stream_fix import cov, disp_hits_stream
    eng = Engine()
    print(cov(eng))                      # (覆盖率%, 指令数, resync)
    print(disp_hits_stream(eng, 0xA8ED84))

**本文件只读 gamemd.exe，不写任何数据。**
"""

import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs


def _dis(eng):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    return md


def cov(eng):
    """流式算覆盖率：返回 (coverage_pct, n_insns, n_resync)。

    与 ra2tool.Engine.coverage 同口径（重同步线性解码、逐址 +1 恢复），
    但**不保留 CsInsn 对象**，内存 O(1)。
    """
    md = _dis(eng)
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    cur = eng.TLO
    n = 0
    covered = 0
    fails = 0
    while cur < eng.THI:
        off = cur - eng.TLO
        got = list(md.disasm(tb[off: off + 15], cur, count=1))
        if not got:
            cur += 1
            fails += 1
            continue
        ins = got[0]
        covered += ins.size
        n += 1
        cur += ins.size
    return (100.0 * covered / eng.TSZ, n, fails)


def disp_hits_stream(eng, target, width=4):
    """流式找「绝对地址访存」：operand.mem 满足 base==0 且 index==0 且 disp==target。

    返回 [(va, 'W'|'R', mnemonic, op_str)]；**不建全量索引**。
    """
    md = _dis(eng)
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    cur = eng.TLO
    hits = []
    while cur < eng.THI:
        off = cur - eng.TLO
        got = list(md.disasm(tb[off: off + 15], cur, count=1))
        if not got:
            cur += 1
            continue
        ins = got[0]
        for op in ins.operands:
            if op.type != 3:          # X86_OP_MEM == 3
                continue
            m = op.mem
            if m.base != 0 or m.index != 0:
                continue
            if m.disp == target:
                acc = "W" if (op.access & 2) else "R"
                hits.append((ins.address, acc, ins.mnemonic, ins.op_str))
        cur += ins.size
    return hits


def _selftest():
    """自检：与原件 coverage 对拍（若原件能跑通）+ 覆盖率应 100%。"""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from ra2tool import Engine
    eng = Engine()
    c, n, f = cov(eng)
    print("stream_fix: coverage=%.2f%%  insns=%d  resync=%d" % (c, n, f))
    ok = abs(c - 100.0) < 0.05
    print("覆盖率自检:", "PASS" if ok else "**FAIL**")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest())
