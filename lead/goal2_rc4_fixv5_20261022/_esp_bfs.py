#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""沿**真实控制流**模拟 esp，逐步断言，回答 `0x777687` 处 esp 到底是多少。

背景：§382/§383/§384/§385 我连续四轮手推 `0x777687` 的 esp 都产出矛盾结论。
根因是手推容易漏掉 push/pop 或走错分支。本工具改成：

  - 用 **BFS 遍历基本块**，不线性扫描（避免把"字节相邻"当"控制流相邻"）
  - 每个基本块入口记录 esp，块内顺序执行
  - 遇到 jcc 分叉到两个后继，各自带 esp
  - 遇到 jmp 只跟一个后继
  - 遇到 ret 终止该路径
  - **同一个块被不同 esp 到达时，报告冲突**（这是分支分歧的机器判定）

只走到 `0x777687` 与 `0x7779B9` 两个目标，报告到达时的 esp 集合。
"""
import struct
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
FN = 0x7775C0
TARGETS = (0x777687, 0x7779B9)
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-58s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def main():
    import capstone
    b = EXE.read_bytes()
    IB = 0x400000

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

    def va2off(va):
        rva = va - ib
        for v, vs_, ra_, rs_ in secs:
            if v <= rva < v + max(vs_, rs_):
                return ra_ + (rva - v)
        return None

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    _ret_cache = {}

    def ret_size(va):
        if va in _ret_cache:
            return _ret_cache[va]
        off = va2off(va)
        if off is None:
            _ret_cache[va] = None
            return None
        for i in md.disasm(b[off:off + 0x800], va):
            if i.mnemonic == "ret":
                rs = int(i.op_str, 16) if i.op_str else 0
                _ret_cache[va] = rs
                return rs
        _ret_cache[va] = None
        return None

    # ---- 基本块 BFS ----
    # state: (va, esp) -> 已访问
    seen = set()
    reached = {t: set() for t in TARGETS}
    conflicts = []
    indirect_calls = set()
    q = deque([(FN, 0)])
    max_visits = 20000
    n_visits = 0

    while q and n_visits < max_visits:
        va, esp = q.popleft()
        if (va, esp) in seen:
            continue
        seen.add((va, esp))
        n_visits += 1
        if va in reached:
            reached[va].add(esp)

        off = va2off(va)
        if off is None:
            continue

        cur = esp
        # ★ 顺序执行直到遇到控制流指令。
        #   关键修正：不能只解码固定窗口（0x40）—— 窗口耗尽会被误当成
        #   "块结束"而顺序落入下一地址，把字节相邻当成控制流相邻（§382 同源错误）。
        #   改为：每次取一条指令，边解码边推进，直到 jcc/jmp/ret 为止。
        pc = va
        taken_next = None
        while True:
            off2 = va2off(pc)
            if off2 is None:
                break
            try:
                i = next(md.disasm(b[off2:off2 + 16], pc))
            except StopIteration:
                break
            m, ops = i.mnemonic, i.op_str
            if m == "push":
                cur -= 4
            elif m == "pop":
                cur += 4
            elif m == "call":
                cur -= 4
                if ops.startswith("0x"):
                    rs = ret_size(int(ops, 16))
                    cur += 4 + (rs if rs is not None else 0)
                else:
                    # ★★ 间接调用 `call [reg+disp]` / `call [mem]`：
                    #   目标未知，ret 尺寸**静态不可知**。此前一律按 ret 0
                    #   （只弹返回地址）处理，导致 `call [eax+0x38]` 之后 esp 少 4 字节，
                    #   进而 0x777687 出现 3 种 esp 的假象。
                    #   这里不再猜：标记为"不确定"，并让该路径不参与 esp 断言。
                    cur += 4
                    indirect_calls.add((i.address, cur))
                    cur = None
                    break
            elif m == "add" and ops.startswith("esp,"):
                cur += int(ops.split(",")[1].strip(), 16)
            elif m == "sub" and ops.startswith("esp,"):
                cur -= int(ops.split(",")[1].strip(), 16)

            nxt = i.address + i.size
            if cur is None:
                # 间接调用后 esp 不可知 ⇒ 该路径终止（不猜）
                taken_next = None
                break
            if m == "ret":
                taken_next = None          # ★ ret 之后没有后继
                break
            if m == "jmp":
                if ops.startswith("0x"):
                    q.append((int(ops, 16), cur))
                taken_next = None
                break
            if m.startswith("j") and ops.startswith("0x"):
                q.append((nxt, cur))       # fallthrough
                q.append((int(ops, 16), cur))   # taken
                taken_next = None
                break
            pc = nxt
            taken_next = (nxt, cur)
        if taken_next is not None:
            q.append(taken_next)

    print("=" * 96)
    print("沿真实控制流模拟 esp（BFS 遍历基本块，不线性扫描）")
    print("=" * 96)
    print("  访问状态数: %d" % n_visits)
    print()
    for t in TARGETS:
        s = reached[t]
        print("  目标 0x%08X 到达时的 esp 集合: %s"
              % (t, sorted(s) if s else "（未到达）"))
        for e in sorted(s):
            off_e = e + 0x18
            print("      esp=%+4d => [esp+0x18] = 入口 E%+d" % (e, off_e))

    print()
    print("  --- 断言 ---")
    for t in TARGETS:
        s = reached[t]
        check("0x%08X 可达" % t, bool(s), "%d 种 esp" % len(s))
        if s:
            single = len(s) == 1
            check("0x%08X 的 esp 唯一（无分支分歧）" % t, single,
                  "%s" % sorted(s))

    # ---- 解读 ----
    print()
    print("  --- 解读 ---")
    for t in TARGETS:
        for e in sorted(reached[t]):
            eo = e + 0x18
            nm = {0: "retaddr", 4: "hwnd", 8: "msg",
                  12: "wParam", 16: "lParam"}.get(eo, "E%+d" % eo)
            print("    0x%08X esp=%+d => [esp+0x18] = %s" % (t, e, nm))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
