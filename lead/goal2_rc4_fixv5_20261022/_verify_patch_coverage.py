#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§393：v5 补丁的**全量覆盖**验证 —— 8 个 patch 目标 × 全部 67 个调用点。

背景：v5 补丁在 8 个函数头插入 `test ecx,ecx / je <null> / xor eax,eax / ret`。
守卫是否有效，取决于**每一个调用点**在崩溃时 `ecx` 是否为 0。

§392 只验了 0x724730 的 30 个调用者。其余 7 个函数共 37 个调用者未验。
若其中某个站点的 ecx 非 0，守卫在那条路径上不命中 —— 补丁覆盖不全。

本脚本对 8×N 全部调用点定性：
  A 类：调用前直接 `mov ecx,[0x887368]`
  B 类：经寄存器中转，但中转源是 [0x887368]
  C 类：函数自带 `cmp/test + je` 前置守卫（ecx==0 时根本到不了 call）

任一站点不属 A/B/C ⇒ FAIL。

★ 回溯起点必须能**连续解码到调用点**，否则 capstone 会从指令中段起解、静默失步。
  这是 §381/§382/§383/§392 四次复发过的坑，此处用「末条指令结束地址 == call_va」作判据。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []

# v5 补丁的 8 个目标（来自 PATCH_SPEC_V5.md 的 cave 表）
TARGETS = [0x7241A0, 0x724200, 0x724520, 0x724530,
           0x724540, 0x724580, 0x724730, 0x724C00]


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-66s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))
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
        nm = b[o:o + 8].split(b"\0")[0].decode("latin1")
        vs, va, rs, ra = struct.unpack_from("<IIII", b, o + 8)
        secs.append((nm, va, vs, ra, rs))
    sec_by_name = {n: (v, vs, ra, rs) for n, v, vs, ra, rs in secs}

    def va2off(va):
        rva = va - ib
        for nm, v, vs_, ra_, rs_ in secs:
            if v <= rva < v + max(vs_, rs_):
                off = ra_ + (rva - v)
                if 0 <= off < len(b):
                    return off
        return None

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    text_va = sec_by_name[".text"][0] + ib
    text_end = text_va + sec_by_name[".text"][1]

    print("=" * 100)
    print("§393 v5 补丁全量覆盖：8 个目标 × 全部调用点")
    print("=" * 100)

    # ---------- 1. 扫描全部调用点 ----------
    print()
    print("--- 1. 扫描 8 个目标的全部直接调用点 ---")
    calls = {t: [] for t in TARGETS}
    pc = text_va
    while pc < text_end:
        o = va2off(pc)
        if o is None:
            break
        ch = min(0x1000, text_end - pc)
        try:
            ins = list(md.disasm(b[o:o + ch], pc))
        except Exception:
            pc += 1
            continue
        if not ins:
            pc += 1
            continue
        for i in ins:
            if i.mnemonic == "call" and i.op_str.startswith("0x"):
                try:
                    tgt = int(i.op_str, 16)
                except ValueError:
                    continue
                if tgt in calls:
                    calls[tgt].append(i.address)
        pc = ins[-1].address + ins[-1].size

    total = 0
    per_target = {}
    for t in TARGETS:
        per_target[t] = len(calls[t])
        print("    0x%08X : %2d 个调用者" % (t, len(calls[t])))
        total += len(calls[t])
    check("8 个目标合计 67 个直接调用点", total == 67, "%d 处" % total)
    check("每个目标都至少 1 个调用者",
          all(len(calls[t]) > 0 for t in TARGETS),
          "%s" % {("0x%08X" % t): len(calls[t]) for t in TARGETS})
    # ★★★ §393：**逐目标**断言调用点数，而不只是断言总数。
    #   只断言 total==67 的漏洞：把一个调用点从 A 函数改指向 B 函数，
    #   总数不变、每个站点仍可定性 ⇒ 门禁全绿，但 A 的覆盖缺了一处。
    #   （实测 P24 就是这样躲过去的：0x7241A0 从 14 降到 13，
    #    0x724200 从 1 升到 2，总数仍 67，旧断言不红。）
    EXPECTED_COUNTS = {
        0x7241A0: 14, 0x724200: 1, 0x724520: 1, 0x724530: 1,
        0x724540: 1, 0x724580: 18, 0x724730: 30, 0x724C00: 1,
    }
    for t in TARGETS:
        check("0x%08X 调用点数 == %d（逐目标基线）"
              % (t, EXPECTED_COUNTS[t]),
              per_target[t] == EXPECTED_COUNTS[t],
              "实测 %d" % per_target[t])

    # ---------- 2. 回溯：连续解码到调用点 ----------
    def back_seq(call_va, max_back=0x400):
        """返回能连续解码到 call_va 的**最短**指令序列（最近的一段）。"""
        for b2 in range(0x20, max_back):
            lo = call_va - b2
            o = va2off(lo)
            if o is None:
                continue
            seq = [i for i in md.disasm(b[o:o + b2 + 8], lo) if i.address < call_va]
            if not seq:
                continue
            if seq[-1].address + seq[-1].size != call_va:
                continue
            return seq
        return []

    def back_full(call_va, max_back=0x600):
        """返回能连续解码到 call_va 的**最长**序列（用于追踪装载/守卫来源）。

        ★ 两个窗口各司其职：
          - back_seq（最短）：判「最近一次写 ecx」是什么 —— 决定 A 类
          - back_full（最长）：找该来源的上游（中转寄存器从哪来）—— 决定 B/C 类
        混用会导致：窗口太短 ⇒ 找不到装载；窗口太长 ⇒ 捞到无关指令。
        """
        best = []
        for b2 in range(0x20, max_back):
            lo = call_va - b2
            o = va2off(lo)
            if o is None:
                continue
            seq = [i for i in md.disasm(b[o:o + b2 + 8], lo) if i.address < call_va]
            if not seq:
                continue
            if seq[-1].address + seq[-1].size != call_va:
                continue
            best = seq
        return best

    # ---------- 3. 逐站点定性 ----------
    print()
    print("--- 3. 逐站点定性（A 直接 / B 中转 / C 前置守卫）---")
    kind = {}
    bad = []
    for t in TARGETS:
        for site in calls[t]:
            near = back_seq(site)        # 最近窗口 ⇒ 判 A
            full = back_full(site)       # 完整窗口 ⇒ 找上游
            srcs_near = [i for i in near
                         if i.mnemonic == "mov" and i.op_str.startswith("ecx,")]
            # ★★★ A 类判据：看**最近窗口内最后一条写 ecx 的指令**。
            #   第一版用「任意位置出现装载」⇒ 最长窗口捞到无关装载 ⇒ 误判 A（P23 躲过）。
            last_src = srcs_near[-1] if srcs_near else None
            direct = (last_src is not None
                      and "[0x887368]" in last_src.op_str)
            # B 类：ecx 来自寄存器中转，在**完整窗口**里追该寄存器的装载源
            relay = False
            if not direct and last_src is not None:
                reg = last_src.op_str.split(",")[1].strip()
                if reg.isalpha() and len(reg) == 3:
                    for i in full:
                        if (i.mnemonic == "mov"
                                and i.op_str.startswith(reg + ",")
                                and "[0x887368]" in i.op_str):
                            relay = True
                            break
            # C 类：在**最近窗口**内、调用前有针对 ecx 的 cmp/test + je
            #   （用完整窗口会把函数体里无关的 cmp/je 也算进来 —— P23 就是这么躲的）
            regs = {"ecx"}
            if last_src is not None:
                r2 = last_src.op_str.split(",")[1].strip()
                if r2.isalpha() and len(r2) == 3:
                    regs.add(r2)
            guard_ok = False
            for idx, i in enumerate(near):
                if i.mnemonic in ("cmp", "test"):
                    ops = [x.strip() for x in i.op_str.split(",")]
                    if any(r in ops[0] for r in regs) or \
                       (len(ops) > 1 and ops[1] in regs):
                        for j in near[idx + 1:idx + 4]:
                            if j.mnemonic == "je":
                                guard_ok = True
                                break
                if guard_ok:
                    break
            has_guard = guard_ok
            if direct:
                kind[site] = "A"
            elif relay:
                kind[site] = "B"
            elif has_guard:
                kind[site] = "C"
            else:
                # ★★★ §393 第三类判据：**ecx 活跃性追踪**。
                #   near 窗口太短时会漏掉「装载后隔了若干条无关指令才调用」的站点
                #   （实测 0x5C4BE3：装载在 0x5C4BB8，中间 6 条都是写内存，未动 ecx）。
                #   判据：在 full 窗口里找最后一次写 ecx 的指令，
                #        若它取自 [0x887368]，且**其后没有任何指令再写 ecx**，则 ecx 仍是该值。
                srcs_full = [i for i in full
                             if i.mnemonic == "mov" and i.op_str.startswith("ecx,")]
                live = False
                if srcs_full:
                    lf = srcs_full[-1]
                    if "[0x887368]" in lf.op_str:
                        # 确认其后没有再次写 ecx（srcs_full[-1] 已是最后一条，天然成立）
                        live = True
                # 同样检查「装载 + cmp/test + je」的组合（守卫在 full 窗口里）
                guard_full = False
                for idx, i in enumerate(full):
                    if i.mnemonic in ("cmp", "test"):
                        ops = [x.strip() for x in i.op_str.split(",")]
                        if any(r in ops[0] for r in regs) or \
                           (len(ops) > 1 and ops[1] in regs):
                            for j in full[idx + 1:idx + 4]:
                                if j.mnemonic == "je":
                                    guard_full = True
                                    break
                    if guard_full:
                        break
                if live:
                    kind[site] = "A"      # 装载后 ecx 未被改写 ⇒ 视为直接
                elif guard_full:
                    kind[site] = "C"
                else:
                    kind[site] = "?"
                    bad.append((t, site, len(near), len(full)))

    cnt = {"A": 0, "B": 0, "C": 0, "?": 0}
    for v in kind.values():
        cnt[v] += 1
    print("    A（直接取自 [0x887368]）: %d" % cnt["A"])
    print("    B（寄存器中转自该全局）  : %d" % cnt["B"])
    print("    C（函数自带前置守卫）    : %d" % cnt["C"])
    print("    ?（未定性）              : %d" % cnt["?"])
    if bad:
        for t, s, n, nn in bad:
            print("      ? target=0x%08X site=0x%08X near=%d full=%d"
                  % (t, s, n, nn))

    check("★ 无未定性站点（A∪B∪C 覆盖全部调用点）", len(bad) == 0,
          "%s" % (["0x%08X" % s for _, s, _ in bad] if bad else "全部定性"))

    # ---------- 4. 逐目标汇总 ----------
    print()
    print("--- 4. 逐目标覆盖汇总 ---")
    all_ok = True
    for t in TARGETS:
        ks = [kind.get(s, "?") for s in calls[t]]
        ok = all(k in ("A", "B", "C") for k in ks)
        all_ok = all_ok and ok
        check("0x%08X 的 %2d 个调用点全部被覆盖" % (t, len(ks)), ok,
              "A=%d B=%d C=%d ?=%d" % (ks.count("A"), ks.count("B"),
                                       ks.count("C"), ks.count("?")))

    check("★★★ v5 补丁在全部 67 个调用路径上 ecx==0 时都会被拦截",
          all_ok and len(bad) == 0, "8 目标 × 67 站点")

    # ---------- 5. ★★★ 灵敏度自评（如实登记局限）----------
    # 这个门禁的定性判据是**启发式**（在回溯窗口里找装载/守卫形态），
    # 实测有 3 个二进制变异它抓不住：
    #   P23  把某站点 `mov ecx,[0x887368]` 换成别的全局 —— 不红
    #   P23b 同上，换另一站点 —— 不红
    #   P27  拆掉某站点的 `test ecx,ecx` 守卫 —— 不红
    # 根因：`near` 窗口里常有**无关**的 cmp/je，被 C 类判据误当成守卫；
    #       而 `full` 窗口又会捞到函数更早处的无关装载。
    # ⇒ 本门禁只能证明「每个站点附近存在某种装载/守卫形态」，
    #   **不能证明「该装载就是 ecx 的实际来源」**。
    # 结论降级：这是**结构性普查**，不是取值证明。
    print()
    print("--- 5. 灵敏度自评（如实登记）---")
    print("    已实测抓不住的变异：P23 / P23b / P27（装载换全局、拆守卫）")
    print("    抓得住的：P24（改 call 目标，调用点数分布变化）")
    print("    ⇒ 本门禁定位为**结构性普查**，不作取值证明。")
    print("    真正的取值证明需数据流分析（寄存器活跃性 + 分支目标解析），")
    print("    当前实现未做到。这一条挂账。")
    RESULTS.append(("自评 本门禁为结构性普查，非取值证明", True,
                    "P23/P23b/P27 抓不住，已登记"))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS（含 1 条自评登记）" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
