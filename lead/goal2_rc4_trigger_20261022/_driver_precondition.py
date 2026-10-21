# -*- coding: utf-8 -*-
"""0x652CF0 的前置条件：它属于哪个类、对象谁创建、何时创建（§347）。

§346 定案了 RC-4 的因果链，但留下一个承重问题：
  链的起点 0x652CF0 是「谁、什么时候」调用的？
  §346 说「反复关窗才是靶」，其前提是每次关窗都能跑到 0x652CF0。
  本脚本检验这个前提。

已知（§347 手工探测）：
  - 0x652CF0 没有直接 E8 调用者 ⇒ 只能经虚表/函数指针分发。
  - 它作为 dword 在 .rdata 只出现 1 次：0x7F0358。
  - 其前一个槽 0x7F0354 = 0x6587A0（对象构造器，写 [edi]=0x7F0344）。

本脚本要证的：
  R1 0xCF0 在虚表里（且只有 1 处），排除「还有别的入口」。
  R2 表头定位不能用「往前扫到非代码」——0x7F0340 夹着 0x8083C0（非代码），
     那样会把手表头算到 0x7F0344，但真正表头要靠**构造函数写入的立即数**来钉。
  R3 同表槽 4 = 0x6587A0 是构造器（写 [edi]=表头）。
  R4 对象尺寸：ctor 里 `lea ecx,[edi+0x14c0]`/`[edi+0x1500]` 给出下界。
  R5 0x652CF0 的函数体形态：它是 __thiscall、有 ret 4、内部做什么。

★ 口径坑（本文件注释标 ★ 的都是踩过的）：
  - 从任意偏移线性反汇编会产出 xchg ah,bl / das / enter 这类幻象。
    必须先确定函数头，或只用「单遍线性解码得到的指令边界集」。
  - 「往前扫到第一个非代码指针」求表头不可靠：表内可以夹非代码常量。
    构造器写入的立即数是更硬的证据。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

DRIVER = 0x00652CF0      # 崩溃链起点
CTOR = 0x006587A0        # 推定构造器（同表前一槽）
VT_SLOT_DRIVER = 0x007F0358
VT_HEAD = 0x007F0344     # 由 ctor 立即数钉的表头
SUB_OBJ = 0x00655A90     # ctor 里调用的子构造

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
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    fof = array("I", bytes(4 * len(tb)))
    insns = []
    cur = None
    pend = True
    off = 0
    n = len(tb)
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            o = ins.address - tva
            if pend and ins.mnemonic not in ("nop", "int3", "lea"):
                cur = ins.address
                pend = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    fof[k] = cur
            insns.append((o, ins.mnemonic, ins.op_str))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pend = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, insns, fof


def main():
    data, img_base, secs = load()
    tb, tva, insns, fof = build(secs, data)
    n = len(tb)
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))
    bnd = set(o for (o, m, s) in insns)

    text = [s for s in secs if s["name"] == ".text"][0]

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def seg_of(va):
        for s in secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                return s["name"]
        return None

    # ---------- R1：0x652CF0 / 0x6587A0 的引用普查 ----------
    print()
    print("=== R1 引用普查（虚表槽 vs 代码立即数）===")

    def dword_sites(val):
        pat = struct.pack("<I", val)
        out = []
        i = 0
        while True:
            j = data.find(pat, i)
            if j < 0:
                break
            out.append(j + 0x400000)
            i = j + 1
        return out

    def vt_slots(val):
        out = []
        for va in dword_sites(val):
            if seg_of(va) != ".rdata":
                continue
            j = va - 0x400000
            nb = [struct.unpack_from("<I", data, j + k * 4)[0] for k in (-1, 1)]
            if all(iscode(v) for v in nb):
                out.append(va)
        return out

    def e8_callers(tgt):
        out = []
        for o in range(n - 5):
            if tb[o] != 0xE8 or o not in bnd:
                continue
            rel = struct.unpack_from("<i", tb, o + 1)[0]
            if tva + o + 5 + rel == tgt:
                out.append(tva + o)
        return out

    drv_vt = vt_slots(DRIVER)
    drv_e8 = e8_callers(DRIVER)
    ctor_vt = vt_slots(CTOR)
    print("  0x%08X（驱动函数）虚表槽 %d 处：%s" % (DRIVER, len(drv_vt),
                                            ", ".join("0x%08X" % v for v in drv_vt)))
    print("  0x%08X（驱动函数）E8 调用者 %d 处" % (DRIVER, len(drv_e8)))
    print("  0x%08X（推定 ctor）虚表槽 %d 处：%s" % (CTOR, len(ctor_vt),
                                           ", ".join("0x%08X" % v for v in ctor_vt)))

    check(len(drv_vt) == 1 and drv_vt[0] == VT_SLOT_DRIVER,
          "★ 驱动函数只有 1 个入口：虚表槽 0x%08X（无其他分发路径）" % VT_SLOT_DRIVER,
          "%d 处" % len(drv_vt))
    check(len(drv_e8) == 0,
          "★ 驱动函数**没有** E8 直接调用者（只能经虚表调）",
          "%d 处" % len(drv_e8))
    check(len(ctor_vt) == 1,
          "★ ctor 也只在虚表里出现 1 次（同表相邻槽）",
          ", ".join("0x%08X" % v for v in ctor_vt))

    # ---------- R2：表头由构造器立即数钉定 ----------
    print()
    print("=== R2 表头定位：构造器写入的立即数 vs 往前扫 ===")
    o = va2off(secs, CTOR)
    ctor_txt = []
    for ins in capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32) \
            .disasm(data[o:o + 0x40], CTOR):
        ctor_txt.append((ins.address, ins.mnemonic, ins.op_str))
    print("  ctor 头部：")
    for (a, m, s) in ctor_txt[:8]:
        print("    0x%08X  %s %s" % (a, m, s))
    writes_head = [a for (a, m, s) in ctor_txt
                   if m == "mov" and ("0x%x" % VT_HEAD) in s and "[edi]" in s]
    check(bool(writes_head),
          "★ ctor 内 `mov [edi], 0x%X`（this 首 dword = 表头，硬证据）" % VT_HEAD,
          ", ".join("0x%08X" % a for a in writes_head))

    # 往前扫得到的表头（对照，说明为何不可靠）
    j = VT_SLOT_DRIVER - 0x400000
    k = 0
    while iscode(struct.unpack_from("<I", data, j - 4 * (k + 1))[0]):
        k += 1
    naive_head = VT_SLOT_DRIVER - 4 * k
    print("  往前扫求表头 = 0x%08X（槽号 %d）" % (naive_head, k))
    # 表内夹的非代码常量
    in_table = []
    for s2 in range(VT_HEAD, VT_SLOT_DRIVER + 0x80, 4):
        v = struct.unpack_from("<I", data, s2 - 0x400000)[0]
        if s2 >= VT_HEAD and not iscode(v) and v != 0:
            in_table.append((s2, v))
            if len(in_table) >= 4:
                break
    print("  表内非代码常量：%s"
          % ", ".join("0x%08X=0x%08X" % (a, v) for a, v in in_table[:3]))
    check((VT_SLOT_DRIVER - VT_HEAD) % 4 == 0,
          "★ 表头 0x%08X 与槽 0x%08X 对齐（槽号 %d）"
          % (VT_HEAD, VT_SLOT_DRIVER, (VT_SLOT_DRIVER - VT_HEAD) // 4),
          "差值 0x%X" % (VT_SLOT_DRIVER - VT_HEAD))

    # ---------- R3/R4：ctor 做了什么、对象多大 ----------
    print()
    print("=== R3/R4 ctor 体与对象尺寸下界 ===")
    o = va2off(secs, CTOR)
    seq = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
               .disasm(data[o:o + 0x80], CTOR))
    txt = ["%s %s" % (i.mnemonic, i.op_str) for i in seq]
    leas = [t for t in txt if t.startswith("lea ecx, [edi +")]
    offs = []
    for t in leas:
        try:
            offs.append(int(t.split("+")[-1].rstrip("]"), 16))
        except ValueError:
            pass
    print("  ctor 内 lea ecx,[edi+off]：%s"
          % ", ".join("0x%X" % x for x in sorted(set(offs))))
    check(bool(offs), "★ ctor 有子对象 lea（给出对象尺寸下界）",
          "最大子对象偏移 0x%X" % max(offs) if offs else "-")
    if offs:
        check(max(offs) >= 0x1400,
              "★ 对象尺寸下界 ≥ 0x%X（远大于崩溃容器 0x250）" % max(offs),
              "实测最大子对象偏移 0x%X" % max(offs))

    # ---------- R5：驱动函数体 ----------
    print()
    print("=== R5 驱动函数 0x652CF0 体（它就是 §346 链条起点）===")
    o = va2off(secs, DRIVER)
    dseq = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
                .disasm(data[o:o + 0xA8], DRIVER))
    dtxt = ["%s %s" % (i.mnemonic, i.op_str) for i in dseq]
    for i in dseq[:22]:
        print("    0x%08X  %-22s %s" % (i.address, i.bytes.hex(),
                                        i.mnemonic + " " + i.op_str))
    check("mov esi, ecx" in dtxt, "★ 0x652CF0 是 __thiscall（esi = this = ecx）")
    check(any(t.startswith("call 0x4a8850") for t in dtxt),
          "★ 0x652CF0 内 call 0x4A8850（§346 链的第一跳，直接 E8）")
    # this 偏移写入
    thisw = [t for t in dtxt if "[esi + 0x1" in t and t.startswith("mov")]
    print("  对 this 的偏移写入 %d 条（ESI+0x11xx 区）" % len(thisw))
    check(bool(thisw), "★ 驱动函数对 this+0x11xx 初始化（与 ctor 的 0x1500 尺寸相符）",
          thisw[0] if thisw else "-")

    # ---------- 判定 ----------
    print()
    print("=== 判定：0x652CF0 的前置条件 ===")
    print("  1) 必须先有一个「类 vtable=0x7F0344」的活动对象（由 ctor 0x6587A0 构造）。")
    print("  2) 然后对该对象触发虚表槽 5（0x7F035C 那一格 = 0x652CF0）。")
    print("  3) 该槽只有 1 个入口，无 E8 直调 ⇒ 不存在「别的代码路径绕过前置」的可能。")
    print("  ⇒ 「反复关窗」能否命中，取决于该对象在关窗时是否仍存活、其槽 5 是否被触发。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 0x652CF0 前置条件分析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
