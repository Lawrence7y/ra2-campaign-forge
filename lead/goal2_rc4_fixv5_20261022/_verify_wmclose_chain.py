#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§379 全链门禁：WM_CLOSE 经 DefWindowProcA 必然清零单例 [0x887368]。

这条链推翻了 §370「从未置值」与 §374 §二「WM_CLOSE 不改变单例态」。
本脚本把 Lead 的独立复证固化成可复算断言，每一环都从**已验证的指令边界**
用 capstone 解码，不依赖散文。

链路（5 环）：
  1. 派发表把 WM_CLOSE 送到 0x7779B9，且 0x7779CB `call 0x54F790`
  2. 0x54F790 对 msg=0x10 走 `add eax,0xffffff00 / cmp eax,5 / ja 0x54FB3D`
  3. 0x54FB3D 是 `xor eax,eax` + `ret 0x10` ⇒ 返回 0
  4. 0x7779D2 `je` 继续，0x7779E6 `jne 0x777A64`（msg≠0x286）
  5. 0x777A70 `call [0x7E1394]` = USER32!DefWindowProcA
     ⇒ DestroyWindow ⇒ 同步 WM_DESTROY ⇒ 0x777803 `mov [0x887368], ebx(=0)`

★ 反汇编起点全部是已验证的指令边界（铁律）。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"

RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-56s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def main():
    import capstone
    b = EXE.read_bytes()
    IB = 0x400000

    def rd(va, n):
        return b[va - IB:va - IB + n]

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    def insn_at(va, n=1):
        out = []
        for i in md.disasm(rd(va, 32), va):
            out.append(i)
            if len(out) >= n:
                break
        return out

    print("=" * 96)
    print("§379 全链门禁：WM_CLOSE ⇒ DefWindowProcA ⇒ WM_DESTROY ⇒ 清零 [0x887368]")
    print("=" * 96)

    # ---- 环节 1：0x7779CB call 0x54F790 ----
    print()
    print("--- 环节 1：派发到 0x54F790 ---")
    ins = insn_at(0x7779CB, 3)
    ok = (ins and ins[0].mnemonic == "call"
          and ins[0].op_str == "0x54f790")
    check("0x7779CB 是 call 0x54F790", ok,
          "%s %s" % (ins[0].mnemonic, ins[0].op_str) if ins else "解码失败")
    check("0x7779D2 是 je（返回 0 才继续）",
          insn_at(0x7779D2, 1)[0].mnemonic == "je",
          insn_at(0x7779D2, 1)[0].op_str)

    # ---- 环节 2：0x54F80F add eax,0xffffff00 / cmp 5 / ja ----
    print()
    print("--- 环节 2：0x54F790 对 msg 的分支 ---")
    i1 = insn_at(0x54F80F, 3)
    check("0x54F80F 是 add eax, 0xffffff00",
          i1[0].mnemonic == "add" and "0xffffff00" in i1[0].op_str,
          "%s %s" % (i1[0].mnemonic, i1[0].op_str))
    check("0x54F814 是 cmp eax, 5",
          i1[1].mnemonic == "cmp" and i1[1].op_str == "eax, 5",
          "%s %s" % (i1[1].mnemonic, i1[1].op_str))
    check("0x54F817 是 ja 0x54fb3d",
          i1[2].mnemonic == "ja" and i1[2].op_str == "0x54fb3d",
          "%s %s" % (i1[2].mnemonic, i1[2].op_str))

    # 算术：WM_CLOSE = 0x10
    eax = (0x10 + 0xFFFFFF00) & 0xFFFFFFFF
    check("算术：WM_CLOSE(0x10)-0x100 = 0xFFFFFF10 > 5 ⇒ 跳 0x54FB3D",
          eax > 5, "eax=0x%X" % eax)

    # ---- 环节 3：0x54FB3D 返回 0 ----
    print()
    print("--- 环节 3：0x54FB3D 返回 0 ---")
    # ★ 从 0x54FB3D 起解码，按 mnemonic 找，不假设固定下标
    seq3 = insn_at(0x54FB3D, 8)
    xor_i = next((x for x in seq3 if x.mnemonic == "xor" and x.op_str == "eax, eax"), None)
    ret_i = next((x for x in seq3 if x.mnemonic == "ret"), None)
    check("0x54FB3D 段内有 xor eax, eax（返回 0）",
          xor_i is not None,
          ("0x%X %s %s" % (xor_i.address, xor_i.mnemonic, xor_i.op_str)) if xor_i else "未找到")
    check("该段以 ret 0x10 结束",
          ret_i is not None and "0x10" in ret_i.op_str,
          ("0x%X %s %s" % (ret_i.address, ret_i.mnemonic, ret_i.op_str)) if ret_i else "未找到")

    # ---- 环节 4：0x7779E1 cmp 0x286 / jne 0x777A64 ----
    print()
    print("--- 环节 4：msg≠0x286 走默认处理 ---")
    i4 = insn_at(0x7779E1, 2)
    check("0x7779E1 是 cmp eax, 0x286",
          i4[0].mnemonic == "cmp" and "0x286" in i4[0].op_str,
          "%s %s" % (i4[0].mnemonic, i4[0].op_str))
    check("0x7779E6 是 jne 0x777a64",
          i4[1].mnemonic == "jne" and i4[1].op_str == "0x777a64",
          "%s %s" % (i4[1].mnemonic, i4[1].op_str))
    check("WM_CLOSE(0x10) ≠ 0x286 ⇒ jne 成立", 0x10 != 0x286, "")

    # ---- 环节 5：0x777A70 call [0x7E1394] = DefWindowProcA ----
    print()
    print("--- 环节 5：0x777A70 调 USER32!DefWindowProcA ---")
    i5 = insn_at(0x777A70, 1)
    check("0x777A70 是 call dword ptr [0x7e1394]",
          i5[0].mnemonic == "call" and "0x7e1394" in i5[0].op_str,
          "%s %s" % (i5[0].mnemonic, i5[0].op_str))

    # IAT 解析（遍历节表 + 导入表）
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
        for va_, vs_, ra_, rs_ in secs:
            if va_ <= rva < va_ + max(vs_, rs_):
                return ra_ + (rva - va_)
        return None

    imp_rva, _ = struct.unpack_from("<II", b, opt + 96 + 8)
    target = 0x7E1394 - ib
    off = va2off(ib + imp_rva)
    found = None
    n = 0
    while True:
        o = off + n * 20
        oft, ts, fc, name_rva, ft = struct.unpack_from("<IIIII", b, o)
        if name_rva == 0:
            break
        dll = b[va2off(ib + name_rva):va2off(ib + name_rva) + 32].split(b"\0")[0].decode()
        thunk = oft or ft
        to = va2off(ib + thunk)
        k = 0
        while True:
            val = struct.unpack_from("<I", b, to + k * 4)[0]
            if val == 0:
                break
            if ft + k * 4 == target:
                if val & 0x80000000:
                    found = (dll, "ORD#%d" % (val & 0xFFFF))
                else:
                    no = va2off(ib + val)
                    found = (dll, b[no + 2:no + 64].split(b"\0")[0].decode())
                break
            k += 1
        if found:
            break
        n += 1
    check("IAT 0x7E1394 解析为 USER32!DefWindowProcA",
          found == ("USER32.dll", "DefWindowProcA"), str(found))

    # ---- 环节 6：销毁分支清零，且有守卫 ----
    print()
    print("--- 环节 6：0x777803 清零（有守卫）---")
    # ★ 从 0x7777F9 起解码 5 条，按 mnemonic/op_str 找，不假设固定下标
    seq6 = insn_at(0x7777F9, 7)
    cmp_i = next((x for x in seq6 if x.mnemonic == "cmp" and x.op_str == "ecx, ebx"), None)
    je_i = next((x for x in seq6 if x.mnemonic == "je"), None)
    mov_i = next((x for x in seq6
                  if x.mnemonic == "mov" and "0x887368" in x.op_str), None)
    check("0x7777F9 段内有 cmp ecx, ebx",
          cmp_i is not None,
          ("0x%X %s %s" % (cmp_i.address, cmp_i.mnemonic, cmp_i.op_str)) if cmp_i else "未找到")
    check("该段内有 je（槽为 0 时跳过写）",
          je_i is not None,
          ("0x%X %s %s" % (je_i.address, je_i.mnemonic, je_i.op_str)) if je_i else "未找到")
    check("该段内有 mov [0x887368], ebx（清零）",
          mov_i is not None and "ebx" in mov_i.op_str,
          ("0x%X %s %s" % (mov_i.address, mov_i.mnemonic, mov_i.op_str)) if mov_i else "未找到")
    check("清零指令地址确为 0x777803",
          mov_i is not None and mov_i.address == 0x777803,
          "0x%X" % mov_i.address if mov_i else "未找到")
    # 同块相隔 11 字节清零 hwnd（既有记忆 [RC-4 尾窗三锚点]）
    i7 = insn_at(0x77780E, 1)
    check("0x77780E 是 mov [0xb73550], ebx（hwnd 同块清零）",
          i7[0].mnemonic == "mov" and "0xb73550" in i7[0].op_str,
          "%s %s" % (i7[0].mnemonic, i7[0].op_str))

    # ---- 负控：C1 的起点错位必须被检出 ----
    print()
    print("--- 负控：0x7775F0 不是指令边界 ---")
    # 从 0x7775EB 正确解码，看它跨过 0x7775F0
    i8 = insn_at(0x7775EB, 1)[0]
    spans = i8.address < 0x7775F0 < i8.address + i8.size
    check("负控 0x7775F0 落在 0x7775EB 指令内部（起点错位）",
          spans, "0x%X size=%d ⇒ 覆盖 [0x%X,0x%X)"
          % (i8.address, i8.size, i8.address, i8.address + i8.size))
    check("负控 真函数头是 0x7775C0（前有 90 填充）",
          b[0x7775C0 - IB] == 0x51 and b[0x7775BC - IB] == 0x90,
          "0x7775C0=%02X 0x7775BC=%02X"
          % (b[0x7775C0 - IB], b[0x7775BC - IB]))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    if npass != len(RESULTS):
        for t, c, e in RESULTS:
            if not c:
                print("  - %s  %s" % (t, e))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
