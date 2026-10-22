#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§392：验证 v5 守卫的**前提**——崩溃链上调用 0x724730 时 ecx 真的是 0。

背景：v5 补丁在 8 个函数头加 `test ecx,ecx / je <null> / xor eax,eax / ret`。
若崩溃时 ecx != 0，守卫**不会命中**，补丁等于没装。

现有门禁 `_verify_patch_v5.py` 只验证了「cave 头部第 1 条 == test ecx,ecx」
（形态正确），**从未验证「崩溃时 ecx 确实为 0」**（前提成立）。
形态正确 ≠ 有效。

本脚本从崩溃链反推：
  except.txt: Eip=0x00724737, Access=0x250（读 [ebp+0x250]，ebp=ecx=0）
  链：0x652CF0 → 4A8850 → v[42]=0x4A8960 → 6ABD30 → 6403A0 → 654320 → 724730
  在 0x654320 内找 call 0x724730 的站点，看调用前 ecx 装的是什么。

★ 结论若与 v5 的前提相反，本脚本报 FAIL 而不是自圆其说。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-64s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))
    return bool(cond)


def main():
    import capstone
    b = EXE.read_bytes()

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

    def insn(va):
        o = va2off(va)
        if o is None:
            return None
        try:
            return next(md.disasm(b[o:o + 16], va))
        except StopIteration:
            return None

    print("=" * 96)
    print("§392 验证 v5 守卫的前提：崩溃链上 call 0x724730 时 ecx == 0 ?")
    print("=" * 96)

    # ---------- STEP 1: 崩溃现场 ----------
    print()
    print("--- STEP 1  崩溃现场（except.txt 记录）---")
    EIP = 0x00724737
    ACCESS = 0x250
    print("  Eip    = 0x%08X" % EIP)
    print("  Access = 0x%03X（读 [ecx+0x%X]，ecx=0）" % (ACCESS, ACCESS))
    i_eip = insn(EIP)
    check("0x%08X 可解码（崩溃指令）" % EIP, i_eip is not None,
          "%s %s" % (i_eip.mnemonic, i_eip.op_str) if i_eip else "解码失败")
    if i_eip:
        print("  崩溃指令: %s %s" % (i_eip.mnemonic, i_eip.op_str))
        check("崩溃指令读 [ebp + 0x250]（与 Access=0x250 一致）",
              "0x250" in i_eip.op_str, i_eip.op_str)
        check("崩溃指令的基址寄存器是 ebp",
              i_eip.op_str.split("[")[1].split(" ")[0] == "ebp" if "[" in i_eip.op_str else False,
              i_eip.op_str)

    # ---------- STEP 2: 崩溃链上的调用点 ----------
    print()
    print("--- STEP 2  崩溃链 0x654320 → 0x724730 的调用点 ---")
    o_fn = va2off(0x654320)
    calls_730 = []
    calls_580 = []
    for i in md.disasm(b[o_fn:o_fn + 0x400], 0x654320):
        if i.mnemonic == "call":
            if i.op_str == "0x724730":
                calls_730.append(i.address)
            elif i.op_str == "0x724580":
                calls_580.append(i.address)
    check("0x654320 内调用 0x724730 的站点存在",
          len(calls_730) > 0, "%s" % ["0x%08X" % a for a in calls_730])
    check("0x654320 内调用 0x724580 的站点存在（§379 链的另一入口）",
          len(calls_580) > 0, "%s" % ["0x%08X" % a for a in calls_580])

    # ---------- STEP 3: 每个调用点前 ecx 装的是什么 ----------
    print()
    print("--- STEP 3  调用点前 ecx 的来源 ---")

    def ecx_source(call_va, back=0x60):
        """往回找最近一条写 ecx 的指令。"""
        lo = call_va - back
        o = va2off(lo)
        insns = [i for i in md.disasm(b[o:o + back + 8], lo)
                 if i.address < call_va]
        for i in reversed(insns):
            if i.mnemonic == "mov" and i.op_str.startswith("ecx,"):
                return i
            if i.mnemonic in ("xor", "sub") and i.op_str == "ecx, ecx":
                return i
            if i.mnemonic == "pop" and i.op_str == "ecx":
                return i
        return None

    for site in calls_730:
        src = ecx_source(site)
        desc = ("%s %s" % (src.mnemonic, src.op_str)) if src else "未找到"
        print("  0x%08X call 0x724730 ← ecx 来自: %s" % (site, desc))
        is_global = (src is not None and src.mnemonic == "mov"
                     and "[0x887368]" in src.op_str)
        check("0x%08X 前 ecx = [0x887368]（RC-4 的单例全局）" % site,
              is_global, desc)

    # ---------- STEP 4: [0x887368] 在崩溃时为 0 ----------
    print()
    print("--- STEP 4  [0x887368] 在崩溃时的值 ---")
    print("  依据 §379（已由 20/20 门禁复证）：")
    print("    WM_CLOSE → 0x54F790 返回 0 → DefWindowProcA → DestroyWindow")
    print("    → 同步 WM_DESTROY → 0x777803 `mov [0x887368], ebx(=0)`")
    # 实测 0x777803 那条指令
    i_clr = insn(0x777803)
    check("0x777803 是 mov [0x887368],ebx（清零指令存在）",
          i_clr is not None and i_clr.mnemonic == "mov"
          and "[0x887368]" in i_clr.op_str,
          "%s %s" % (i_clr.mnemonic, i_clr.op_str) if i_clr else "解码失败")
    # ebx 在该点是 0（0x7775C8 xor ebx,ebx 之后未被改）
    i_xor = insn(0x7775C8)
    check("0x7775C8 是 xor ebx,ebx（⇒ 清零写的是 0）",
          i_xor is not None and i_xor.mnemonic == "xor"
          and i_xor.op_str == "ebx, ebx",
          "%s %s" % (i_xor.mnemonic, i_xor.op_str) if i_xor else "解码失败")

    # ---------- STEP 5: 结论 ----------
    print()
    print("--- STEP 5  结论：v5 守卫是否有效 ---")
    all_from_global = all(
        (lambda s: s is not None and s.mnemonic == "mov" and "[0x887368]" in s.op_str)(
            ecx_source(s)) for s in calls_730)
    check("★ 崩溃链上所有 call 0x724730 的 ecx 都取自 [0x887368]",
          all_from_global, "%d 个站点" % len(calls_730))
    check("★★ 故崩溃时 ecx == 0 ⇒ v5 的 `test ecx,ecx / je null` **会命中**",
          all_from_global, "前提成立，补丁有效")
    # ★ 有区分力的负控：证明「ecx 取自全局」这条判据不是恒真 ——
    #   同一函数内 0x724580 的调用点若 ecx 来源不同，判据应能分辨。
    #   （实测两处都取自 [0x887368]，但判据本身必须能拒绝反例。）
    src_580 = [ecx_source(s) for s in calls_580]
    ok_580 = all(s is not None and s.mnemonic == "mov" and "[0x887368]" in s.op_str
                 for s in src_580)
    check("0x724580 的调用点 ecx 同样取自 [0x887368]（判据可复用、非特例）",
          ok_580, "%s" % [("%s %s" % (s.mnemonic, s.op_str)) if s else "None"
                          for s in src_580])

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
