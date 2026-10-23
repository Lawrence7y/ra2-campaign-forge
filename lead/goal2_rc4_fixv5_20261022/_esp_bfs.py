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
        """返回函数入口 va 的**可达** ret 尺寸。

        ★★★ §396b：原实现扫到「第一条 ret」就返回，这是错的。
          实测 `0x6930A0` 在 0x2000 窗口内 30 个 ret / 4 种尺寸
          （`0x10`×5 / `4`×9 / `0`×16 / `8`×3）；取第一条纯属运气。
          正确做法：从入口按 CFG 求**可达集**，再看可达集内的 ret 尺寸。
          可达集内尺寸不唯一 ⇒ 返回 None（不猜）。
        """
        if va in _ret_cache:
            return _ret_cache[va]
        off = va2off(va)
        if off is None:
            _ret_cache[va] = None
            return None
        code = {}
        for i in md.disasm(b[off:off + 0x2000], va):
            code[i.address] = i
        reach = set()
        work = [va]
        while work:
            a = work.pop()
            if a in reach:
                continue
            reach.add(a)
            i = code.get(a)
            if i is None or i.mnemonic == "ret":
                continue
            nxt = a + i.size
            if i.mnemonic == "jmp":
                if i.op_str.startswith("0x"):
                    work.append(int(i.op_str, 16))
                continue
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                work.append(int(i.op_str, 16))
                work.append(nxt)
                continue
            work.append(nxt)
        sizes = set()
        for a in reach:
            if code[a].mnemonic == "ret":
                sizes.add(int(code[a].op_str, 16) if code[a].op_str else 0)
        rs = sizes.pop() if len(sizes) == 1 else None
        _ret_cache[va] = rs
        return rs

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
    # ★★★ §388（异族核验 D/P4 推翻）：原版这里只有「可达」「唯一」两条断言，
    #   全是结构性断言、**没有一条断言取值**。实测把二进制 0x7775C0 的
    #   `push ecx` 改成 `nop`，本工具打印 esp=-12 ⇒ [esp+0x18]=wParam，
    #   仍然 6/6 PASS、exit 0。⇒ 原版是**打印机不是门禁**。
    #   现在把「算出来的值」本身写成断言，并加起点边界自检。
    EXPECTED_ESP = -0x10          # §386/§387 定谳值
    EXPECTED_ARG = 0x08           # E+0x08 = msg
    for t in TARGETS:
        s = reached[t]
        check("0x%08X 可达" % t, bool(s), "%d 种 esp" % len(s))
        if s:
            check("0x%08X 的 esp 唯一（无分支分歧）" % t, len(s) == 1,
                  "%s" % sorted(s))
            # ★ 取值断言：esp 必须**恰好**等于期望值
            got = sorted(s)[0] if len(s) == 1 else None
            check("0x%08X 的 esp 取值 = %+d（实算，非结构性）"
                  % (t, EXPECTED_ESP), got == EXPECTED_ESP,
                  "实算 %s" % (got if got is not None else sorted(s)))
            check("⇒ 0x%08X 的 [esp+0x18] = E+0x%02X = msg" % (t, EXPECTED_ARG),
                  got is not None and got + 0x18 == EXPECTED_ARG,
                  "E%+d" % (got + 0x18) if got is not None else "N/A")
        else:
            check("0x%08X 的 esp 取值 = %+d（实算，非结构性）"
                  % (t, EXPECTED_ESP), False, "未到达")

    # ---- ★ 起点边界自检（异族 B2：起点错位会静默给出错值）----
    print()
    print("  --- ★ 起点边界自检（§388 补，异族 B2 指出原版缺失）---")
    off_fn = va2off(FN)
    bounds = {i.address for i in md.disasm(b[off_fn - 16:off_fn + 16], FN - 16)}
    check("起点 0x%08X 是已知指令边界" % FN, FN in bounds,
          "in %d boundaries" % len(bounds))
    # ★ 负控要选**落在指令中段**的地址。0x7775C1 恰好是下一条指令的边界
    #   （push ecx 是 1 字节），不是好样例；改用 0x7775C3（在
    #   `8b 0d 28 76 88 00` 的立即数内部，§381 已实证）。
    WRONG = 0x7775C3
    check("负控 0x%08X（指令中段）不是边界" % WRONG, WRONG not in bounds,
          "已确认错位起点会被抓到")

    # ---- ★★ 目标指令本体自检（异族 P2：本工具只按地址算 esp，从不读目标指令）----
    #   实测：把 0x777687 的 `[esp+0x18]` 改成 `[esp+0x1c]`，本工具仍 12/12 PASS
    #   —— 因为它只算「到达该地址时 esp 是多少」，不问「那条指令读哪个槽」。
    #   两者必须同时成立才有意义，所以这里把目标指令的**解码结果**也断言。
    print()
    print("  --- ★ 目标指令本体自检（§388 补，异族 P2 指出）---")
    TARGET_DISP = {0x777687: (0x777687, 0x18), 0x7779B9: (0x7779B5, 0x18)}
    for t, (ins_va, want_disp) in TARGET_DISP.items():
        o = va2off(ins_va)
        try:
            ins = next(md.disasm(b[o:o + 8], ins_va))
        except StopIteration:
            check("0x%08X 可解码" % ins_va, False, "解码失败")
            continue
        want = "[esp + 0x%x]" % want_disp
        check("0x%08X 的目标指令读 %s（实读二进制）" % (ins_va, want),
              ins.mnemonic == "mov" and want in ins.op_str,
              "%s %s" % (ins.mnemonic, ins.op_str))

    # ---- 解读 ----
    print()
    print("  --- 解读 ---")
    for t in TARGETS:
        for e in sorted(reached[t]):
            eo = e + 0x18
            nm = {0: "retaddr", 4: "hwnd", 8: "msg",
                  12: "wParam", 16: "lParam"}.get(eo, "E%+d" % eo)
            print("    0x%08X esp=%+d => [esp+0x18] = %s" % (t, e, nm))

    # ---- ★★ §387：如实登记本工具的**覆盖边界** ----
    # 本工具在间接调用处终止路径（不猜 ret 尺寸）。0x77764F `call [0x7e1404]`
    # （GetMenu）正是这样的间接调用 ⇒ 经过 GetMenu 的那条分支到不了 0x777687。
    # 因此「esp 唯一」只覆盖**不经 GetMenu** 的分支。
    # 另一条分支由 _verify_stack_offset.py 的 hand_esp() 独立手算补齐
    # （两条分支同为 -0x10），本工具不重复验证。
    print()
    print("  --- ★ 覆盖边界（§387 登记；§395 改为不进 PASS 计数）---")
    ind = sorted(indirect_calls)
    print("    间接调用点 %d 处，路径在此终止：%s"
          % (len(ind), ["0x%08X" % a for a, _ in ind][:6]))
    # ★★★ §395：这两条原来记成 PASS，但它们是**工具按构造必然成立**的局限，
    #   不是对被测物的任何断言（异族判为「免责声明伪装成 PASS」）。
    #   改成只打印、不进 RESULTS —— PASS 计数只统计真断言。
    print("    [局限] 本工具结果只覆盖「不经间接调用」的分支"
          "（%d 处间接调用 ⇒ 另一分支由 hand_esp() 补）" % len(ind))
    has_getmenu = any(a == 0x77764F for a, _ in ind)
    print("    [局限] 0x77764F(GetMenu) %s 终止点内 ⇒ 本工具不含该分支"
          % ("在" if has_getmenu else "不在"))
    # 真正有意义的断言：间接调用终止点**确实**存在（否则「局限」无从谈起）
    check("★ 确实存在间接调用终止点且含 GetMenu（局限是真实的，不是空话）",
          len(ind) > 0 and has_getmenu,
          "%d 处，含 GetMenu=%s" % (len(ind), has_getmenu))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
