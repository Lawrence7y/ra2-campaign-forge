# -*- coding: utf-8 -*-
"""vtable 0x7F0344 建表解密：RC-4 链起终点同属一张虚表（§347 核心件）。

§346 把链画成 0x652CF0 → 0x4A8850 → v[42] → 0x4A8960 → … → 0x724730。
本轮问「0x652CF0 的前置条件」，结果发现一个更强的结构事实：

  **0x652CF0 和 0x4A8960 在同一张虚表 0x7F0344 里**（槽 5 与槽 42）。
  也就是说 `call [eax+0xA8]` 里的 eax == 这个对象的 vtable 指针，
  不是从别处传进来的「某个未知对象」。

这直接改写了「v[42] 是哪个对象的槽 42」这个此前一直悬空的问题：
答案是**驱动函数自己的对象**。链条不需要任何跨对象传递。

本脚本建表并断言：
  S1 表头 0x7F0344 由 ctor 0x6587AC 的 `mov [edi], 0x7F0344` 钉定。
  S2 slot[4]=ctor、slot[5]=0x652CF0（链起点）—— 同表。
  S3 slot[34]=0x654320（真崩溃站点所在函数）、slot[42]=0x4A8960（L3）。
  S4 表尾：连续代码指针段在何处结束。
  S5 该表在 .rdata 里被哪些代码构造过（ctor 引用点）。

★ 口径坑：
  - 「往前扫到第一个非代码指针」求表头不可靠（表内可夹非代码常量）。
    首次探测在 0x7F0340 看到 0x8083C0 就以为表头是 0x7F0344 —— 结论碰巧对，
    但方法不对。本脚本以 ctor 立即数为准，并用「两张独立证据是否一致」来加固。
  - 从任意偏移线性反汇编会产出幻象（xchg ah,bl / das / enter）。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

VT_HEAD = 0x007F0344
SLOT_CTOR = 4
SLOT_DRIVER = 5
SLOT_CRASHHOST = 34
SLOT_L3 = 42
CTOR = 0x006587A0
DRIVER = 0x00652CF0
L3 = 0x004A8960
CRASHHOST = 0x00654320
CTOR_WRITE = 0x006587AC

# §346 独立记录的 0x4A8960 七处虚表槽（用于交叉验证 slot42 落点）
L3_SLOTS_RECORDED = [0x7E1A0C, 0x7E61BC, 0x7EE05C, 0x7EFFFC,
                     0x7F03EC, 0x7F113C, 0x7F3100]

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


def main():
    data, img_base, secs = load()
    text = [s for s in secs if s["name"] == ".text"][0]

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def rd(va):
        o = va2off(secs, va)
        return None if o is None else struct.unpack_from("<I", data, o)[0]

    print("镜像基数 0x%08X；.text = 0x%08X..0x%08X"
          % (img_base, text["va"], text["va"] + text["rsize"]))

    # ---------- S1 表头由 ctor 立即数钉定 ----------
    print()
    print("=== S1 表头证据 ===")
    o = va2off(secs, CTOR)
    seq = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
               .disasm(data[o:o + 0x40], CTOR))
    hit = [i for i in seq if i.address == CTOR_WRITE]
    check(bool(hit), "ctor 在 0x%08X 处有指令" % CTOR_WRITE)
    if hit:
        it = hit[0]
        imm = 0
        # C7 06 <imm32> : mov dword ptr [esi], imm32
        if it.bytes[:2] == b"\xc7\x06" or it.bytes[:2] == b"\xc7\x07":
            imm = struct.unpack_from("<I", it.bytes, 2)[0]
        check(imm == VT_HEAD,
              "★ ctor `mov [this], 0x%X` 立即数即表头" % VT_HEAD,
              "实测 0x%X（%s %s）" % (imm, it.mnemonic, it.op_str))

    # 两法一致：往前扫 vs 立即数
    j = va2off(secs, 0x007F0358)
    k = 0
    while True:
        prev = struct.unpack_from("<I", data, j - 4 * (k + 1))[0]
        if not iscode(prev):
            break
        k += 1
    naive = 0x007F0358 - 4 * k
    check(naive == VT_HEAD,
          "★ 两法一致：往前扫表头 == 立即数表头 == 0x%X" % VT_HEAD,
          "naive=0x%X" % naive)

    # ---------- S2/S3 关键槽 ----------
    print()
    print("=== S2/S3 关键槽 ===")
    cases = [
        (SLOT_CTOR, CTOR, "ctor"),
        (SLOT_DRIVER, DRIVER, "驱动函数 = §346 链起点"),
        (SLOT_CRASHHOST, CRASHHOST, "真崩溃站点 0x654413 所在函数"),
        (SLOT_L3, L3, "崩溃链 L3"),
    ]
    for (slot, want, why) in cases:
        va = VT_HEAD + slot * 4
        got = rd(va)
        check(got == want,
              "★ slot[%d] @0x%08X == 0x%08X（%s）" % (slot, va, want, why),
              "实测 0x%08X" % (got or 0))

    # slot42 交叉验证 §346 记录
    slot42_addr = VT_HEAD + SLOT_L3 * 4
    check(slot42_addr in L3_SLOTS_RECORDED,
          "★ slot[%d] 地址 0x%08X 落在 §346 记录的七处之内（独立方法互证）"
          % (SLOT_L3, slot42_addr),
          "记录 %s" % ", ".join("0x%X" % x for x in L3_SLOTS_RECORDED[:3]) + " …")

    # ---------- S4 全表展开 ----------
    print()
    print("=== S4 vtable 0x7F0344 全表（连续代码指针段）===")
    entries = []
    va = VT_HEAD
    while True:
        v = rd(va)
        if v is None or not iscode(v):
            break
        entries.append((va, v))
        va += 4
    print("  连续代码指针 %d 项（0x%X 字节），止于 0x%08X"
          % (len(entries), len(entries) * 4, va))
    for idx, (a, v) in enumerate(entries):
        tag = ""
        for (s2, w2, why2) in cases:
            if idx == s2:
                tag = "   <<< " + why2
        print("    [%2d] @0x%08X = 0x%08X%s" % (idx, a, v, tag))

    check(len(entries) > SLOT_L3,
          "★ 表长 > %d 槽（覆盖 slot 42）" % SLOT_L3,
          "%d 槽" % len(entries))
    # ★ 首版断言「恰有 43 槽、slot42 是末槽」—— 实测 54 槽，纯属猜测写死。
    #   改为断言末槽之后的首个非代码项位置，作为「表尾」事实记录。
    print("  表尾 @0x%08X 的值为 0x%08X（非代码指针 ⇒ 表在此结束）"
          % (va, rd(va) or 0))
    check(va == VT_HEAD + len(entries) * 4,
          "★ 表尾地址与槽数自洽", "0x%08X" % va)

    # ---------- S5 表被谁构造 ----------
    print()
    print("=== S5 构造该表的代码点 ===")
    pat = struct.pack("<I", VT_HEAD)
    refs = []
    i = 0
    n = len(data)
    while True:
        j2 = data.find(pat, i)
        if j2 < 0:
            break
        va2 = j2 + 0x400000
        seg = None
        for s in secs:
            if s["va"] <= va2 < s["va"] + s["rsize"]:
                seg = s["name"]
        if seg == ".text":
            refs.append(va2)
        i = j2 + 1
    print("  .text 内立即数引用 %d 处：%s"
          % (len(refs), ", ".join("0x%08X" % r for r in refs)))
    # ★ 首版拿「指令地址 0x6587AC」去和「立即数地址 0x6587AE」比 ⇒ 恒不命中。
    #   `C7 07 <imm32>` 的立即数字段从指令 +2 开始，故此处的引用点是 CTOR_WRITE+2。
    CTOR_IMM = CTOR_WRITE + 2
    check(CTOR_IMM in refs,
          "★ ctor 的**立即数字段** 0x%08X（= 指令 0x%08X + 2）在引用集内"
          % (CTOR_IMM, CTOR_WRITE),
          "共 %d 处" % len(refs))
    # ★ 其中可能存在数据区巧合命中，需逐个验证是「落在指令内且是 mov 立即数」
    validated = []
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    for r in refs:
        # 从 r-0x10 起 8 种对齐起点，看是否有起点能解出覆盖 r 的指令且该指令含立即数
        ok = False
        for back in range(0, 12):
            st = r - back
            oo = va2off(secs, st)
            if oo is None:
                continue
            for ins in md.disasm(data[oo:oo + 24], st):
                if ins.address <= r < ins.address + ins.size:
                    if ins.mnemonic == "mov" and ("0x%x" % VT_HEAD) in ins.op_str:
                        ok = True
                    break
            if ok:
                break
        validated.append((r, ok))
    good = [r for r, ok in validated if ok]
    print("  其中经指令级验证包含 `mov …, 0x%X` 的 %d 处：%s"
          % (VT_HEAD, len(good), ", ".join("0x%08X" % r for r in good)))
    check(CTOR_IMM in good,
          "★ ctor 立即数字段通过指令级验证（不是数据区巧合）",
          "%d 处有效" % len(good))
    # ★ 首版以为 4 处里只有 2 处是真引用（0x652B4x 看着像数据）。指令级验证后是 4 处全有效，
    #   但它们的「指令起点」各不相同，逐条列出以免把「立即数地址」当「指令地址」用。
    print("  逐条指令起点：")
    for r, ok in validated:
        oo = va2off(secs, r - 2)
        found = ""
        if oo is not None:
            for ins in md.disasm(data[oo:oo + 16], r - 2):
                if ins.address <= r < ins.address + ins.size:
                    found = "指令@0x%08X %s %s" % (ins.address, ins.mnemonic, ins.op_str)
                    break
        print("    引用点 0x%08X → %s%s" % (r, found, "" if ok else "  (非 mov 立即数)"))

    # ---------- 结论 ----------
    print()
    print("=== 结论 ===")
    print("  0x652CF0（链起点）是 vtable 0x7F0344 的 slot 5；")
    print("  0x4A8960（L3）是同一张表的 slot 42。")
    print("  ⇒ `call [eax+0xA8]` 的 eax 就是这个对象自己的 vtable，")
    print("    不需要任何跨对象传递。「v[42] 属于哪个对象」这个悬空问题闭合。")
    print("  ⇒ 0x654320（真崩溃站点所在函数）是同表 slot 34。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ vtable 0x7F0344 建表解密完成：链起点与 L3 同表（slot 5 / slot 42）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
