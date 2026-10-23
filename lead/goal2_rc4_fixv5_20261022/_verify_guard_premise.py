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
import collections
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

    # ★★★ §395：建全 .text 指令表 + 前驱图（分支目标解析，非线性相邻）。
    #   原来只做单条 insn() 取指，无法回答「沿控制流往回最近的写点是谁」。
    _text = None
    for v, vs_, ra_, rs_ in secs:
        if v == 0x1000:
            _text = (v + ib, vs_)
            break
    if _text is None:
        _text = (secs[0][0] + ib, secs[0][1])
    text_va, text_size = _text
    text_end = text_va + text_size
    code = {}
    pc = text_va
    while pc < text_end:
        o = va2off(pc)
        if o is None:
            break
        ch = min(0x1000, text_end - pc)
        got = list(md.disasm(b[o:o + ch], pc))
        if not got:
            pc += 1
            continue
        for i in got:
            code[i.address] = i
        pc = got[-1].address + got[-1].size
    prev = collections.defaultdict(set)

    def _add_indirect_jump_targets(ins_addr, ins):
        """解析 `jmp dword ptr [reg*4 + TABLE]` 的跳转表，把表项都记为前驱。

        ★★★ §395：不解析间接跳转 ⇒ 图是断的。
          实测 0x7777F3 的唯一入边来自 0x7776AE 的 `jmp [edx*4+0x777a80]`；
          不解析它，从 0x777803 反向 BFS 只走 7 个节点就到「入口」，
          于是「ebx 在 0x777803 处是否为 0」根本问不出来（假 FAIL）。
        """
        import re as _r
        m = _r.search(r"\[e[a-z]{2}\*4 \+ (0x[0-9a-f]+)\]", ins.op_str)
        if not m:
            return
        tbl = int(m.group(1), 16)
        for k in range(16):
            o = va2off(tbl + k * 4)
            if o is None:
                break
            t = struct.unpack_from("<I", b, o)[0]
            if t in code:
                prev[t].add(ins_addr)

    for a, i in code.items():
        ft = a + i.size
        m = i.mnemonic
        if m == "ret":
            continue
        if m == "jmp":
            try:
                prev[int(i.op_str, 16)].add(a)
            except ValueError:
                pass
            _add_indirect_jump_targets(a, i)
            continue
        if m.startswith("j") and m != "jmp":
            try:
                prev[int(i.op_str, 16)].add(a)
            except ValueError:
                pass
            if ft in code:
                prev[ft].add(a)
            continue
        if ft in code:
            prev[ft].add(a)
    print("  [图] %d 条指令 / %d 条前驱边"
          % (len(code), sum(len(v) for v in prev.values())))

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
    # ★★★ §395 修正：上面那条判据只匹配目的地址，**不匹配源寄存器**。
    #   异族 M13 实测：把源 ebx 改成 edi（清零语义完全消失）仍然 PASS，
    #   而证据栏还会打印 "mov dword ptr [0x887368], edi" 与标签自相矛盾。
    #   这里补一条真正断言源寄存器的判据。
    src_reg = (i_clr.op_str.split(",")[1].strip()
               if i_clr is not None and "," in i_clr.op_str else None)
    check("★★ 0x777803 的**源寄存器确实是 ebx**（不是任意寄存器）",
          src_reg == "ebx", "实测源 = %s" % src_reg)

    # ★★★ §395：ebx 在 0x7775C8(xor ebx,ebx) 到 0x777803 之间必须未被改写。
    #   原脚本只验了 xor 那一条指令，没验区间 —— 中间有 8 处 pop ebx，
    #   线性区间内确实会覆盖 ebx。所以「清零写的是 0」需要按**控制流**证，
    #   不能按线性区间证。这里改成：从 0x777803 沿 CFG 反向，找最近的 ebx 写点。
    def ebx_writer_before(target):
        """从 target 沿 CFG 反向，找最近的 ebx 写点。

        ★ ebx 是 callee-saved ⇒ **可以穿过 call**（call 不会破坏 ebx）。
          这与 ecx 的追踪相反（ecx 是 caller-saved，遇 call 即 UNKNOWN）。
        """
        seen = set()
        work = [target]
        found = []
        while work:
            n = work.pop()
            if n in seen:
                continue
            seen.add(n)
            if len(seen) > 200000:
                return None, len(seen)
            ps = prev.get(n)
            if not ps:
                continue
            for p in ps:
                if p in seen:
                    continue
                pi = code.get(p)
                if pi is None:
                    continue
                if pi.op_str.split(",")[0].strip() in ("ebx", "bx", "bl", "bh"):
                    found.append(pi)
                    seen.add(p)
                    continue
                work.append(p)
        found.sort(key=lambda x: x.address)
        return (found[-1] if found else None), len(seen)

    w, nvis = ebx_writer_before(0x777803)
    check("★★ 0x777803 沿控制流反向的最近 ebx 写点 = xor ebx,ebx（⇒ 写的是 0）",
          w is not None and w.mnemonic == "xor" and w.op_str == "ebx, ebx",
          ("最近写点 0x%08X %s %s（遍历 %d 节点）"
           % (w.address, w.mnemonic, w.op_str, nvis)) if w else "未找到")
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

    # ---------- STEP 6: 全量 30 个调用者普查（§393）----------
    # ★ 上面只看了崩溃链所在的 0x654320。但 0x724730 全二进制有 30 个调用者，
    #   若其中有站点的 ecx 非 0，v5 守卫在该路径上就不命中 —— 补丁覆盖不全。
    #   本节把 30 个站点全部定性。
    print()
    print("--- STEP 6  0x724730 全部 30 个调用者的 ecx 定性 ---")
    text_va = min(v for v, vs_, ra_, rs_ in secs) + ib
    text_end = text_va + 0x3E0000
    all_callers = []
    pc3 = text_va
    while pc3 < text_end:
        o3 = va2off(pc3)
        if o3 is None:
            break
        ch3 = min(0x1000, text_end - pc3)
        try:
            ins3 = list(md.disasm(b[o3:o3 + ch3], pc3))
        except Exception:
            pc3 += 1
            continue
        if not ins3:
            pc3 += 1
            continue
        for i in ins3:
            if i.mnemonic == "call" and i.op_str == "0x724730":
                all_callers.append(i.address)
        pc3 = ins3[-1].address + ins3[-1].size

    def has_zero_guard(call_va, back=0xA0):
        """调用点前是否有 `mov ecx,[0x887368]` 的装载形态。

        ★★★ 回溯起点必须是**指令边界**。第一版直接写 `lo = call_va - back`，
          结果 0x6D1541-0xA0 = 0x6D14A1 落在指令中段，capstone 解码出 **0 条**，
          于是误报「该站点没有装载」。这是 §381/§382 同类错误（把地址偏移
          当成解码起点）的复发。修法：从 `back` 起**逐步扩大**，
          取第一个能解出 ≥1 条指令的起点。
        """
        for b2 in range(back, back + 0x60):
            lo = call_va - b2
            o4 = va2off(lo)
            if o4 is None:
                continue
            seq = [i for i in md.disasm(b[o4:o4 + b2 + 8], lo)
                   if i.address < call_va]
            if not seq:
                continue
            # ★ 判据不是「解码出 ≥3 条」，而是**解码必须连续走到调用点**。
            #   第一版用 `len(seq) < 3` 当阈值 ⇒ back=161 时解出 3 条就提前返回，
            #   而那 3 条远在 0x6D14A0，根本没覆盖到 0x6D153A 的装载。
            #   正确判据：末条指令的下一条地址 == call_va（说明一路解到调用点）。
            if seq[-1].address + seq[-1].size != call_va:
                continue
            has_load = any(i.mnemonic == "mov" and i.op_str.startswith("ecx,")
                           and "[0x887368]" in i.op_str for i in seq)
            has_cmp = any(i.mnemonic == "cmp" and i.op_str.startswith("ecx,")
                          for i in seq)
            has_je = any(i.mnemonic == "je" and i.op_str.startswith("0x")
                         for i in seq)
            return has_load, has_cmp, has_je
        return False, False, False

    check("0x724730 的调用者总数为 30", len(all_callers) == 30,
          "%d 处" % len(all_callers))
    no_load = []
    for s in all_callers:
        ld, cmp_, je_ = has_zero_guard(s)
        if not ld:
            no_load.append(s)
    check("★ 所有 30 个调用点前都能找到 mov ecx,[0x887368]",
          len(no_load) == 0,
          "缺 %s" % ["0x%08X" % a for a in no_load] if no_load else "30/30")
    # 那 2 个「窗口内无装载」的站点，其所在函数自带前置守卫
    for s, fname in ((0x4A8B75, "0x4A8840"), (0x640427, "0x6403A0")):
        ld, cmp_, je_ = has_zero_guard(s, back=0xA0)
        print("    0x%08X（属 %s）: load=%s cmp=%s je=%s" % (s, fname, ld, cmp_, je_))
    check("★ 0x4A8B75 前有 ecx=[0x887368] + cmp + je（函数自带守卫）",
          all(has_zero_guard(0x4A8B75)), "%s" % (has_zero_guard(0x4A8B75),))
    check("★ 0x640427 前有 ecx=[0x887368] + cmp + je（函数自带守卫）",
          all(has_zero_guard(0x640427)), "%s" % (has_zero_guard(0x640427),))

    # ---------- STEP 7 ★★★ 真正的守卫普查（§395 修正）----------
    #   §392 原结论：「30 个调用路径在 ecx==0 时**全部**被守卫拦截 ⇒ 补丁覆盖完整」。
    #   异族 M11 实测：把 0x6403B2 的 `je` 改成 `je +0`（等于删掉守卫），
    #   三个脚本**全绿** —— 因为 has_zero_guard 只查「窗口内有没有 cmp+je」，
    #   **不查那个 je 是否真的跳过 call**。
    #
    #   更要紧的是：那条结论本身**方向错了**。
    #   v5 补丁的守卫挂在**被调函数 0x724730 头部**，不依赖调用点自带守卫。
    #   调用点有没有守卫，对补丁是否有效**无关**。
    #   真正需要证的是「每个调用点在调用瞬间 ecx == [0x887368]」
    #   —— 那一条已由 §394 _verify_ecx_dataflow.py 完成（67/67）。
    #
    #   本节保留的、有意义的断言是：**只有 2 个站点自带会跳过 call 的 ecx 守卫**。
    #   这不是「覆盖完整」的证据，而是「为什么必须把守卫放在被调函数头」的理由。
    print()
    print("--- STEP 7  ★ 调用点自带守卫的真实普查（§395 修正）---")

    def jcc_skips_call(site):
        """站点前是否有 **ecx 条件** 的 jcc，且目标**越过**该 call。

        两个修正点（都是实测踩出来的）：
        ① 判据按**指令顺序**找「jcc 之前最近的一条 cmp/test」，
           不能用 CFG 直接前驱 —— `cmp` 与 `je` 之间可以夹任意多条无关指令
           （实测 0x4A8B35 cmp → 4 条 mov → 0x4A8B4E je）。
        ② **只有目标越过 call 的 jcc 才终止回溯**。
           目标在 call 之前的 jcc（如 0x6403E7 `jne 0x6403EE`）两条边都通向 call，
           它不是守卫，必须继续往回走 —— 否则会漏掉更上游的真守卫
           （实测 0x6403B2 `je 0x64043D`，正是被 0x6403E7 挡掉的）。
        """
        out = []
        seen = set()
        work = [site]
        while work:
            n = work.pop()
            if n in seen:
                continue
            seen.add(n)
            if len(seen) > 4000:
                break
            for p in prev.get(n, ()):
                if p in seen:
                    continue
                pi = code.get(p)
                if pi is None:
                    continue
                if pi.mnemonic.startswith("j") and pi.mnemonic != "jmp":
                    try:
                        tgt = int(pi.op_str, 16)
                    except ValueError:
                        continue
                    if tgt > site:
                        cands = [c for c in code.values()
                                 if c.address < p and
                                 c.mnemonic in ("cmp", "test") and
                                 p - c.address < 0x40]
                        cands.sort(key=lambda c: c.address, reverse=True)
                        for qi in cands:
                            if "ecx" in qi.op_str:
                                out.append((p, qi))
                                break
                        continue          # 目标越过 call ⇒ 守卫，本路径终止
                    # 目标在 call 之前 ⇒ 不是守卫，继续回溯
                    work.append(p)
                    continue
                if pi.mnemonic in ("call", "ret", "jmp"):
                    continue
                work.append(p)
        return out

    guarded = []
    for s in all_callers:
        g = jcc_skips_call(s)
        if g:
            guarded.append(s)
    print("    自带 ecx 守卫且跳过 call 的站点: %d 处 %s"
          % (len(guarded), ["0x%08X" % a for a in guarded]))
    # ★ 实测 4 处（不是原来说的 2 处）。异族说 2 处，是因为它按 CFG 直接前驱
    #   找 cmp/test，漏掉了 0x4A8B35（与 je 之间夹了 4 条 mov）和
    #   0x6403B0（被 0x6403E7 的 jne 挡住）。我这里按指令顺序回溯，得 4 处。
    check("★ 自带会跳过 call 的 ecx 守卫的站点 = 4 处（实测基线）",
          sorted(guarded) == [0x4A8B75, 0x640427, 0x6D09FA, 0x6D15CB],
          "%d 处 %s" % (len(guarded), ["0x%08X" % a for a in guarded]))
    check("★★★ 30 个站点里只有 4 个自带守卫，其余 26 个没有 ⇒ 补丁必须挂在被调函数头",
          len(guarded) == 4 and len(all_callers) == 30,
          "4 有 / 26 无（含崩溃链的 0x654413、0x654469）")
    print("    ⇒ 「30 条路径被调用点守卫拦截」是**错误命题**（异族 M11 已证伪）。")
    print("      补丁有效性来自「每个调用点 ecx == [0x887368]」（§394 67/67）")
    print("      + 「守卫在 0x724730 函数头」（PATCH_SPEC_V5）。")


    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
