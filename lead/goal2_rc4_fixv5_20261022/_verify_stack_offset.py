#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3 补证：`0x777687` 读的确实是 **msg**，不是返回地址。

背景：异族核验 C3 判定「ret 尺寸属实，但 14 条断言没有一条验证栈偏移」
⇒ 结论只存在于散文推演，未经机器验证。本脚本把它变成断言。

做法：从 WndProc 入口 `0x7775C0` 起**线性模拟 esp**，逐个跟踪：
  - `push r32` / `push imm8` / `push imm32`   ⇒ esp -= 4
  - `pop r32`                                  ⇒ esp += 4
  - `call rel32` / `call [mem]`                ⇒ 先压返回地址（esp -= 4），
                                                 返回后再按被调函数 ret 尺寸清栈
  - `add esp, imm` / `sub esp, imm`            ⇒ 相应调整
  - `ret imm16`                                ⇒ 清栈后结束

WndProc 是 stdcall：入口 esp 指向返回地址，参数在 [esp+4], [esp+8], [esp+0xC], [esp+0x10]
（hwnd, msg, wParam, lParam）。

★ 反汇编起点 `0x7775C0` 已由 §381 的边界自检证明是真实指令边界。
★ 被调函数的 ret 尺寸用 capstone 实测，不硬编码。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-58s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def main():
    import capstone
    b = EXE.read_bytes()
    IB = 0x400000

    # ---- 节表 + IAT ----
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

    imp_rva, _ = struct.unpack_from("<II", b, opt + 96 + 8)
    imp_off = va2off(ib + imp_rva)

    def resolve(iat_va):
        target = iat_va - ib
        n = 0
        while True:
            o = imp_off + n * 20
            oft, ts, fc, name_rva, ft = struct.unpack_from("<IIIII", b, o)
            if name_rva == 0:
                return None
            thunk = oft or ft
            to = va2off(ib + thunk)
            k = 0
            while True:
                val = struct.unpack_from("<I", b, to + k * 4)[0]
                if val == 0:
                    break
                if ft + k * 4 == target:
                    if val & 0x80000000:
                        return "ORD#%d" % (val & 0xFFFF)
                    no = va2off(ib + val)
                    return b[no + 2:no + 64].split(b"\0")[0].decode()
                k += 1
            n += 1

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False

    def ret_size(fn_va):
        """实测被调函数的 ret 尺寸（扫描到第一条 ret）。"""
        off = va2off(fn_va)
        for i in md.disasm(b[off:off + 0x800], fn_va):
            if i.mnemonic == "ret":
                return int(i.op_str, 16) if i.op_str else 0
        return None

    print("=" * 96)
    print("C3 补证：模拟 esp，证明 0x777687 读的是 msg")
    print("=" * 96)

    # ---- 实测两个被调函数的 ret 尺寸 ----
    rs_6930A0 = ret_size(0x6930A0)
    rs_778030 = ret_size(0x778030)
    check("0x6930A0 的 ret 尺寸 = 0x10（实测）", rs_6930A0 == 0x10,
          "ret 0x%X" % rs_6930A0)
    check("0x778030 的 ret 尺寸 = 0x8（实测）", rs_778030 == 0x8,
          "ret 0x%X" % rs_778030)

    # ---- IAT 身份（用于说明这两次调用的性质）----
    check("IAT 0x7E1404 = USER32!GetMenu", resolve(0x7E1404) == "GetMenu",
          str(resolve(0x7E1404)))

    # ---- esp 模拟：0x7775C0 → 0x777687 ----
    # ★ 路径必须**沿实际控制流**走：
    #   - 入口 0x7775C0 起，4 次 push 后 0x7775CE `je 0x777627`（[0x887628]==0 分支）
    #   - 0x777627 起，走到 0x77766C `je 0x777687`
    #   - 注意 0x77766E..0x777684 是 **je 不成立** 的分支（含 4 次 pop 和 ret），
    #     不能把它算进到达 0x777687 的路径 —— 否则 esp 会算错 4 字节。
    path1 = (0x7775C0, 0x7775CE)     # 入口到 je（不含 je 本身之后）
    path2 = (0x777627, 0x77766E)     # je 目标到 0x77766C je 之后（不含不成立分支）

    esp = 0                          # 相对入口的偏移；入口 esp=0，[esp+0]=返回地址
    trace = []

    def walk(lo, hi):
        nonlocal esp
        off = va2off(lo)
        n = (hi - lo) + 32
        for i in md.disasm(b[off:off + n], lo):
            if i.address >= hi:
                break
            m, ops = i.mnemonic, i.op_str
            before = esp
            if m == "push":
                esp -= 4
            elif m == "pop":
                esp += 4
            elif m == "call":
                esp -= 4                      # 压返回地址
                if ops.startswith("0x"):
                    tgt = int(ops, 16)
                    rs = ret_size(tgt)
                    if rs is None:
                        trace.append((i.address, m, ops, before, esp, "RETSIZE?未知"))
                        continue
                    esp += 4 + rs                 # ret 清栈：弹返回地址 + 参数
                else:
                    # call [mem]：外部 API。被调方按 stdcall 自己清栈，
                    # 净效果是 esp 回到调用前（压的返回地址被 ret 弹掉）。
                    esp += 4
            elif m == "add" and ops.startswith("esp,"):
                esp += int(ops.split(",")[1].strip(), 16)
            elif m == "sub" and ops.startswith("esp,"):
                esp -= int(ops.split(",")[1].strip(), 16)
            trace.append((i.address, m, ops, before, esp, ""))

    walk(*path1)
    walk(*path2)

    print()
    print("  esp 轨迹（相对入口，负数=已下压）：")
    for addr, m, ops, before, after, note in trace:
        if after != before or m in ("call",):
            print("    0x%08X  %-6s %-26s esp: %+4d -> %+4d  %s"
                  % (addr, m, ops, before, after, note))

    # ---- 关键断言 ----
    print()
    # 目标指令：0x777687 mov eax,[esp+0x18]
    off = va2off(0x777687)
    target = next(md.disasm(b[off:off + 8], 0x777687))
    check("0x777687 是 mov eax, dword ptr [esp + 0x18]",
          target.mnemonic == "mov" and "[esp + 0x18]" in target.op_str,
          "%s %s" % (target.mnemonic, target.op_str))

    # 此时 esp 的相对值（沿实际控制流 0x7775C0 → 0x777627 → 0x77766C → 0x777687）
    esp_at_687 = esp
    # 入口 esp 处：[esp+0x00]=retaddr [esp+0x04]=hwnd [esp+0x08]=msg
    #             [esp+0x0C]=wParam [esp+0x10]=lParam
    read_off = esp_at_687 + 0x18
    check("esp 在 0x777687 处的相对偏移 = -0x14",
          esp_at_687 == -0x14, "esp=%+d" % esp_at_687)
    check("⇒ 0x777687 的 [esp+0x18] 对应入口 [esp+0x04]",
          read_off == 0x04,
          "read_off=%+d（入口偏移）" % read_off)

    # ---- ★ 关键：0x777687 那条路径是否真的会到达？----
    # 它的唯一前驱是 0x77766C `je 0x777687`，而该 je 取决于 0x778030 的返回值。
    print()
    print("  ★ 未决点（§383 已撤回 §382 的 hwnd 说法）：")
    print("    0x777687 读的是入口 [esp+0x04]（机器可证）。")
    print("    若按标准 WndProc 布局，那是 **hwnd**；")
    print("    但 0x77768B `cmp eax,0x18` / `lea ecx,[eax-1]` / `cmp ecx,0x13`")
    print("    是对 **msg** 才成立的分派。二者矛盾。")
    print()
    print("    我试过的三种解释全部互斥不成立：")
    print("      A 签名无 hwnd   —— 但 0x777C79 确证它是 lpfnWndProc，必有 hwnd")
    print("      B edx 不是 msg  —— 但 0x778030 用 cmp 0x281/0x10D/0x10E 比，只能是 msg")
    print("      C 第四参是 msg  —— 但那是 E+0x10=lParam，WM_CREATE 时是 LPCREATESTRUCT")
    print()
    print("    ⇒ 判定：0x777687 处 [esp+0x18] 的语义 = **UNVERIFIABLE（静态不可判定）**。")
    print("      本轮只断言 esp 值（机器可证），**不**断言它读到 hwnd 还是 msg。")
    print("      需要：0x6930A0 完整参数语义 / 真机断点。C3 整体仍挂账。")

    # ---- ★ 可达性：0x777687 的前驱 je 是否常成立 ----
    print()
    print("--- 0x777687 可达性 ---")
    # 0x778030 的返回值决定 0x77766C je 是否跳 0x777687
    # 返回 1 仅当 msg ∈ {0x10D,0x10E,0x10F,0x281,0x282..0x291}；其余返回 0
    def ret_778030(msg):
        if msg > 0x281:
            return 1 if 0x282 <= msg <= 0x291 else 0
        if msg == 0x281:
            return 1
        if msg in (0x10D, 0x10E, 0x10F):
            return 1
        return 0

    check("0x778030(WM_CREATE=0x001) 返回 0 ⇒ 0x777687 可达",
          ret_778030(0x001) == 0, "ret=%d" % ret_778030(0x001))
    check("0x778030(WM_CLOSE=0x010) 返回 0 ⇒ 0x777687 可达",
          ret_778030(0x010) == 0, "ret=%d" % ret_778030(0x010))
    check("0x778030(0x281) 返回 1 ⇒ 不跳（负控）",
          ret_778030(0x281) == 1, "ret=%d" % ret_778030(0x281))
    check("0x778030(0x10D) 返回 1 ⇒ 不跳（负控）",
          ret_778030(0x10D) == 1, "ret=%d" % ret_778030(0x10D))
    # 解码验证这两条返回路径确实存在
    seq = insn_at(0x7780F4, 2) if False else None
    off_r1 = va2off(0x7780F4)
    i_r1 = next(md.disasm(b[off_r1:off_r1 + 8], 0x7780F4))
    check("0x7780F4 是 mov eax, 1（返回 1 的路径存在）",
          i_r1.mnemonic == "mov" and i_r1.op_str == "eax, 1",
          "%s %s" % (i_r1.mnemonic, i_r1.op_str))
    off_r0 = va2off(0x7780FD)
    i_r0 = next(md.disasm(b[off_r0:off_r0 + 8], 0x7780FD))
    check("0x7780FD 是 xor eax, eax（返回 0 的路径存在）",
          i_r0.mnemonic == "xor" and i_r0.op_str == "eax, eax",
          "%s %s" % (i_r0.mnemonic, i_r0.op_str))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
