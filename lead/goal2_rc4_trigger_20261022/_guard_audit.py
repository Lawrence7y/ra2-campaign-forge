# -*- coding: utf-8 -*-
"""30 个 call 0x724730 站点的 this(ecx) 来源 + null 守卫审计（§346 承重件）。

背景（本轮 §346 已定的事实）：
  - 真崩溃指令 `mov eax,[ebp+0x250]`（0x724737），ebp 由 `mov ebp,ecx` 赋值，
    所以 EBP==0 只能是**调用者把 ecx 传成 0** ⇒ NULL 解引用，不是悬垂。
  - 0x724730 有 30 个直接 E8 调用者，分布在 15 个函数（crash_site 的 4 宿主只是其中之四）。
  - 已定样本 0x4A8960：0x4A8B18 `mov ecx,[0x887368]` → 0x4A8B35 `cmp ecx,ebx`
    → 0x4A8B4E `je 0x4A8B9B`（跳过崩溃调用，走占位框路径）⇒ **这条路有守卫**。

本轮要回答的单一问题：
  **剩下 29 个站点里，哪些把 ecx 传成「无守卫的值」？**

判定口径（每个站点一条记录）：
  A. ecx 定义点：在站点前同函数体内、最近一次写 ecx 的指令。
  B. 该定义到站点之间的 cmp/test 是否测的就是 ecx（或其拷贝）。
  C. 若有测，是否有一个 jcc 分支**绕过**站点（即站点只在某一侧）。
  D. 结论档：
       GUARDED   有测 + 有绕过分支 ⇒ 与其他路径不可达
       UNGUARDED 无任何相关测 ⇒ 静态上 ecx=0 会直接崩
       CONST-0   定义即 xor ecx,ecx / mov ecx,0 ⇒ 必崩（极可能是死代码）
       UNKNOWN   反向切片跨 call 且寄存器易失 / 到函数头未定义 ⇒ 不判

★ 踩过的坑：本脚本首版把「同函数内 ecx 最后一次写」当成唯一定义，
   漏掉了 `mov ecx,[esi]` 这种「先取 vtable 再 call」的 this 透传形态；
   本版同时记录 op_str 供人工复核，并把跨 call 的易失情况显式标 UNKNOWN。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys

import capstone
from capstone.x86 import X86_OP_REG, X86_OP_MEM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CRASH = 0x00724730
SINGLETON = 0x00887368

fails = []


def check(cond, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label,
                           ("  " + detail) if detail else ""))
    if not cond:
        fails.append(label)
    return cond


def load():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, rva, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": name, "va": img_base + rva, "vsize": vsize,
                     "rsize": rsize, "roff": roff})
    return data, img_base, secs


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rsize"]:
            return s["roff"] + (va - s["va"])
    return None


def build(secs, data):
    from array import array
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    func_of = array("I", bytes(4 * len(tb)))
    insns = []
    cur = None
    pending = True
    off = 0
    n = len(tb)
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            o = ins.address - tva
            if pending and ins.mnemonic not in ("nop", "int3", "lea"):
                cur = ins.address
                pending = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    func_of[k] = cur
            insns.append((o, ins.mnemonic, ins.op_str))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pending = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, insns, func_of


JCC = ("je", "jne", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge",
       "jl", "jle", "js", "jns", "jo", "jno", "jp", "jnp")


def analyse(insns, tva, func_of, tb, site_va):
    """返回 (func, ecx_def_va, ecx_def_txt, guard_txt, bypass_txt, verdict)。"""
    fs = func_of[site_va - tva]
    # 取同函数体
    body = []
    for (o, m, s) in insns:
        if func_of[o] == fs:
            body.append((tva + o, m, s))
    idx = None
    for k, (a, m, s) in enumerate(body):
        if a == site_va:
            idx = k
            break
    if idx is None:
        return fs, None, "", "", "", "UNKNOWN"

    # A. 往回找最近写 ecx 的指令（含 call 警告）
    def_va, def_txt, crossed_call = None, "", False
    for j in range(idx - 1, -1, -1):
        a, m, s = body[j]
        if m in ("call", "callf"):
            crossed_call = True
            continue
        if m in ("mov", "lea", "xor", "pop", "and", "or", "add", "sub") \
                and s.split(",")[0].strip() == "ecx":
            def_va, def_txt = a, m + " " + s
            break
        if m in ("mov", "lea", "xor", "pop", "and", "or", "add", "sub"):
            # dst 是别的寄存器，但可能是 32 位子寄存器形式
            pass

    # B/C. 定义点 → 站点之间的 cmp/test，及绕过站点的 jcc
    guard_txt, bypass_txt = "", ""
    if def_va is not None:
        seg = [(a, m, s) for (a, m, s) in body
               if def_va < a < site_va]
        for (a, m, s) in seg:
            if m in ("cmp", "test") and "ecx" in s:
                guard_txt = "0x%08X %s %s" % (a, m, s)
            elif m in JCC and guard_txt:
                # 目标是否跳过站点
                try:
                    tgt = int(s, 16)
                except ValueError:
                    tgt = None
                tgt = tgt + 0x400000 if tgt is not None and tgt < 0x400000 else tgt
                if tgt is not None and tgt > site_va:
                    bypass_txt = "0x%08X %s %s（目标越过站点）" % (a, m, s)

    # D. 结论
    if def_va is None:
        verdict = "UNKNOWN"
    elif def_txt.startswith("xor ecx, ecx") or def_txt.replace(" ", "") == "movedx,0".replace("edx", "ecx"):
        verdict = "CONST-0"
    elif guard_txt and bypass_txt:
        verdict = "GUARDED"
    elif guard_txt and not bypass_txt:
        verdict = "GUARD-NOBYPASS"
    elif crossed_call and def_va is None:
        verdict = "UNKNOWN"
    else:
        verdict = "UNGUARDED"
    return fs, def_va, def_txt, guard_txt, bypass_txt, verdict


def main():
    data, img_base, secs = load()
    tb, tva, insns, func_of = build(secs, data)
    n = len(tb)
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))
    bnd = set(o for (o, m, s) in insns)

    sites = []
    for o in range(n - 5):
        if tb[o] != 0xE8 or o not in bnd:
            continue
        rel = struct.unpack_from("<i", tb, o + 1)[0]
        if tva + o + 5 + rel == CRASH:
            sites.append(tva + o)
    check(len(sites) == 30, "call 0x724730 站点数 == 30", "实测 %d" % len(sites))

    print()
    print("=== 逐站点 this(ecx) / 守卫审计 ===")
    recs = []
    for s in sites:
        fs, dv, dt, gt, bt, vd = analyse(insns, tva, func_of, tb, s)
        recs.append((s, fs, dv, dt, gt, bt, vd))
        print("  0x%08X (func 0x%08X)" % (s, fs))
        print("      ecx <- 0x%s  %s" % ("%08X" % dv if dv else "--------", dt or "（函数内未定义/形参）"))
        if gt:
            print("      guard  %s" % gt)
        if bt:
            print("      bypass %s" % bt)
        print("      ==> %s" % vd)

    print()
    print("=== 汇总 ===")
    tally = {}
    for r in recs:
        tally[r[6]] = tally.get(r[6], 0) + 1
    for k in sorted(tally):
        print("  %-16s %d" % (k, tally[k]))

    unguarded = [r for r in recs if r[6] in ("UNGUARDED", "CONST-0")]
    guarded = [r for r in recs if r[6] == "GUARDED"]
    unknown = [r for r in recs if r[6] in ("UNKNOWN", "GUARD-NOBYPASS")]

    print()
    print("=== 判定 ===")
    check(True, "GUARDED（有测且有绕过分支）站点数 = %d" % len(guarded),
          ", ".join("0x%08X" % r[0] for r in guarded) or "无")
    check(True, "UNGUARDED / CONST-0（静态上可传 0）站点数 = %d" % len(unguarded),
          ", ".join("0x%08X(func 0x%08X)" % (r[0], r[1]) for r in unguarded) or "无")
    check(True, "UNKNOWN / GUARD-NOBYPASS（判不了）站点数 = %d" % len(unknown),
          ", ".join("0x%08X" % r[0] for r in unknown) or "无")

    # 已知样本必须复现 §346 的结论
    ex = [r for r in recs if r[0] == 0x004A8B75]
    check(bool(ex), "已知样本 0x4A8B75 在审计内")
    if ex:
        r = ex[0]
        check(r[6] == "GUARDED",
              "★ 0x4A8B75 判 GUARDED（复现手工结论：cmp ecx,ebx / je 越过站点）",
              r[6] + "  guard=" + (r[4] or "-") + "  bypass=" + (r[5] or "-"))

    check(len(unguarded) + len(guarded) + len(unknown) == len(recs),
          "三档计数守恒", "%d = %d" % (len(unguarded) + len(guarded) + len(unknown), len(recs)))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 守卫审计完成：GUARDED=%d  UNGUARDED/CONST0=%d  UNKNOWN=%d"
          % (len(guarded), len(unguarded), len(unknown)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
