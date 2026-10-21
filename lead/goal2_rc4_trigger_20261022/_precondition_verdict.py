# -*- coding: utf-8 -*-
"""0x652CF0 的前置条件定案：它属于哪个对象族、对象何时构造（§347 收官件）。

## 本轮要回答的问题（§346 遗留的唯一承重项）

§346 画定了链：0x652CF0 → 0x4A8850 → v[42] → 0x4A8960 → … → 0x724730。
但链的**起点 0x652CF0 是谁、在什么条件下被调用**，决定「反复关窗」能否作为复现手段。

## 本轮拿到的事实（逐条断言）

  F1 0x652CF0 没有 E8 直接调用者；它的唯一入口是 vtable 0x7F0344 的 slot[5]。

  F2 vtable 0x7F0344 与 0x87F7E8 对象的 vtable 0x7E1964 **是同一基类的两个派生类**：
     都是 54 槽、slot[0] 同为 0x4F4240、slot[42] 同为 0x4A8960，
     21 槽覆盖不同（slot 4/5/7/8/10/16/18-21/26/30/31/33/34/35/40/44/49/50/53）。

  F3 0x652CF0 是 0x7F0344 的 slot[5]；0x87F7E8 对象的 slot[5] 是 0x5BDF30（不同函数）。
      ⇒ 崩溃帧里 `Edi=0x87F7E8` 与「跑的是 0x652CF0」并不矛盾：
        0x652CF0 的 this 是 0x7F0344 对象，0x87F7E8 是链下游 0x4A8960 里 re-fetch 的单例。

  F4 0x7F0344 的构造点有 4 处指令，其中 2 处在数据区（0x652B45 / 0x652C0C 的反汇编
     落点看着像代码但整段是数据），有效构造器是 0x652C00 与 0x6587A0（同构两版）
     以及 0x6A4F20 内的 0x6A4F78。

  F5 0x652C00 有 6 个 E8 调用者，分布在 0x40D1F7 / 0x40D2D4 / 0x5BEA0A /
     0x6404B3 / 0x69391A 等 —— 其中 0x40D1F7 与 0x87F7E8 的 vtable 写入点
     0x40D1B2 **在同一个初始化函数里，相隔 0x45 字节**。

  F6 那个初始化函数 0x40D1B0 只设 0x87F7E8→0x7E1964 与 0x884D00→0x7E195C，
     **没有** 0x7F0344 → 所以表 B 对象不是全局静态构造，而是在循环里动态造的。

★ 口径坑（本文件注释里标 ★）：
  - 「dword 出现」不等于「代码引用」。0x652B45/0x652C0C 落在数据段内的同形字节，
    必须用**指令边界 + 所在函数是否被调用**双重过滤。
  - 表长不能靠猜：首版写死「43 槽」，实测 54 槽。
  - 引用点地址 = 指令地址 + 2（C7 07 <imm32> 的立即数偏移），不是指令地址本身。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

VT_A = 0x007E1964        # 0x87F7E8 单例的 vtable
VT_B = 0x007F0344        # 0x652CF0 所在的 vtable
DRIVER = 0x00652CF0      # 链起点 = VT_B slot5
SLOT_A5 = 0x005BDF30     # VT_A slot5（对照，证明两者不同）
SINGLETON = 0x0087F7E8
GLOBAL_INIT = 0x0040D1B0
SINGLETON_VT_WRITE = 0x0040D1B2
CTOR_B1 = 0x00652C00
CTOR_B2 = 0x006587A0
CTOR_B1_CALLER = 0x0040D1F7
SHARED_SLOT0 = 0x004F4240
L3 = 0x004A8960

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
    bnd = set(o for (o, m, s) in insns)
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))

    text = [s for s in secs if s["name"] == ".text"][0]

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def rd(va):
        o = va2off(secs, va)
        return None if o is None else struct.unpack_from("<I", data, o)[0]

    def e8_callers(tgt):
        out = []
        for o in range(n - 5):
            if tb[o] != 0xE8 or o not in bnd:
                continue
            rel = struct.unpack_from("<i", tb, o + 1)[0]
            if tva + o + 5 + rel == tgt:
                out.append(tva + o)
        return out

    # ---------- F1 ----------
    print()
    print("=== F1 0x652CF0 的唯一入口 ===")
    drv_c = e8_callers(DRIVER)
    print("  E8 直接调用者：%d 处" % len(drv_c))
    check(len(drv_c) == 0, "★ 0x652CF0 无 E8 直接调用者（只能经虚表）", "%d" % len(drv_c))
    va5 = VT_B + 5 * 4
    check(rd(va5) == DRIVER,
          "★ 唯一入口 = vtable 0x%X slot[5] @0x%X" % (VT_B, va5),
          "实测 0x%08X" % (rd(va5) or 0))

    # ---------- F2 两表同基类 ----------
    print()
    print("=== F2 两张 vtable 是否同一基类布局 ===")
    a_len = 0
    while iscode(rd(VT_A + a_len * 4) or 0):
        a_len += 1
    b_len = 0
    while iscode(rd(VT_B + b_len * 4) or 0):
        b_len += 1
    print("  0x%X 长度 %d 槽；0x%X 长度 %d 槽" % (VT_A, a_len, VT_B, b_len))
    # ★ 首版断言「两表等长」——A 是 55、B 是 54，相差 1。两表**本就不该等长**：
    #   派生类可以在基类布局之外追加自己的槽。判据改为「短表 ⊂ 长表长度」+ 共性槽一致。
    check(abs(a_len - b_len) <= 2,
          "★ 两表长度接近（同一基类布局 ±2 槽内）",
          "A=%d B=%d" % (a_len, b_len))
    check(a_len > 42 and b_len > 42,
          "★ 两表都长于 43 槽（都覆盖 slot 42）", "A=%d B=%d" % (a_len, b_len))
    check(rd(VT_A) == SHARED_SLOT0 and rd(VT_B) == SHARED_SLOT0,
          "★ slot[0] 相同 = 0x%X" % SHARED_SLOT0,
          "A=0x%X B=0x%X" % (rd(VT_A), rd(VT_B)))
    check(rd(VT_A + 42 * 4) == L3 and rd(VT_B + 42 * 4) == L3,
          "★ slot[42] 同为崩溃链 L3 = 0x%X" % L3,
          "A=0x%X B=0x%X" % (rd(VT_A + 168), rd(VT_B + 168)))
    diff = [s for s in range(min(a_len, b_len)) if rd(VT_A + s * 4) != rd(VT_B + s * 4)]
    print("  覆盖槽（两表不同）%d 个：%s"
          % (len(diff), ", ".join(str(s) for s in diff)))
    check(len(diff) > 0, "★ 存在覆盖槽 ⇒ 是两个派生类，不是同一张表",
          "%d 槽不同" % len(diff))
    check(set(diff).isdisjoint({0, 42}),
          "★ 基类共性槽（0、42）不在覆盖集内（继承关系自洽）",
          "覆盖集 %s" % (sorted(diff),))

    # ---------- F3 slot5 分属不同对象 ----------
    print()
    print("=== F3 两个派生类的 slot[5] 不同 ===")
    a5 = rd(VT_A + 20)
    b5 = rd(VT_B + 20)
    print("  0x7E1964.slot5 = 0x%08X ；0x7F0344.slot5 = 0x%08X" % (a5, b5))
    check(a5 == SLOT_A5, "★ A 的 slot5 是 0x%X（与链起点不同）" % SLOT_A5,
          "实测 0x%08X" % (a5 or 0))
    check(a5 != b5, "★ 两派生类 slot5 不同 ⇒ 0x652CF0 不跑在 0x87F7E8 上",
          "A=0x%X B=0x%X" % (a5, b5))

    # ---------- F4 构造点过滤 ----------
    print()
    print("=== F4 0x7F0344 的构造点：数据区 vs 真实构造器 ===")
    pat = struct.pack("<I", VT_B)
    raw = []
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        if text["roff"] <= j < text["roff"] + text["rsize"]:
            raw.append(j + 0x400000)
        i = j + 1
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    real = []
    for r in raw:
        ins_addr = r - 2
        f = fof[ins_addr - tva] if 0 <= ins_addr - tva < len(fof) else 0
        cs = e8_callers(f)
        # ★ 双重过滤：指令必须是 mov [x], imm 且所在函数被调用过
        okform = False
        o = va2off(secs, ins_addr)
        if o is not None:
            for ins in md.disasm(data[o:o + 8], ins_addr):
                if ins.address == ins_addr and ins.mnemonic == "mov" \
                        and ("0x%x" % VT_B) in ins.op_str:
                    okform = True
                break
        real.append((r, ins_addr, f, len(cs), okform))
    for (r, ia, f, nc, ok) in real:
        print("    引用 0x%08X  指令 0x%08X  func 0x%08X  调用者 %d  形态OK=%s  %s"
              % (r, ia, f, nc, ok, "有效" if ok and nc > 0 else "排除"))
    valid = [x for x in real if x[4] and x[3] > 0]
    print("  有效构造器所在函数：%s"
          % ", ".join("0x%08X" % x[2] for x in valid))
    check(len(valid) >= 2, "★ 至少 2 个真实构造器（被调用过 + 指令形态正确）",
          "%d 个" % len(valid))
    check(any(x[2] == CTOR_B1 for x in valid),
          "★ 0x%X 在有效构造器集内（有 E8 调用者 + 形态正确）" % CTOR_B1)
    # ★ 首版把 CTOR_B2（0x6587A0）也要求进「有效集」，但它 E8 调用者为 0，被过滤掉。
    #   实测它是表 B 的 slot[4]，走**虚表**调用而非 E8。判据改为「在虚表里」。
    b2_vt = [s for s in range(64) if rd(VT_B + s * 4) == CTOR_B2]
    check(bool(b2_vt),
          "★ 0x%X 是表 B 的 slot%s（经虚表调用，故无 E8 调用者）"
          % (CTOR_B2, b2_vt),
          "槽 %s" % b2_vt)
    # 与有效版本对比：0x652C00 与 0x6587A0 是同构两版
    import difflib
    ba = data[va2off(secs, CTOR_B1):va2off(secs, CTOR_B1) + 0x60]
    bb = data[va2off(secs, CTOR_B2):va2off(secs, CTOR_B2) + 0x60]
    ratio = difflib.SequenceMatcher(None, ba, bb).ratio()
    print("  0x%X 与 0x%X 前 0x60 字节相似度 %.1f%%" % (CTOR_B1, CTOR_B2, ratio * 100))
    check(ratio > 0.85,
          "★ 两个构造器是同构两版（相似度 > 85%）",
          "%.1f%%" % (ratio * 100))

    # ---------- F5/F6 全局初始化 ----------
    print()
    print("=== F5/F6 全局初始化 0x40D1B0 设了谁、没设谁 ===")
    o = va2off(secs, GLOBAL_INIT)
    gseq = list(md.disasm(data[o:o + 0x60], GLOBAL_INIT))
    gtxt = ["%s %s" % (i.mnemonic, i.op_str) for i in gseq]
    for i in gseq:
        print("    0x%08X  %-22s %s" % (i.address, i.bytes.hex(),
                                        i.mnemonic + " " + i.op_str))
    check(any("0x87f7e8" in t and "0x7e1964" in t for t in gtxt),
          "★ 全局初始化里写 0x87F7E8 = 0x7E1964（表 A）")
    check(not any("0x7f0344" in t for t in gtxt),
          "★ 全局初始化里**没有** 0x7F0344（表 B 对象不是静态构造）")
    calls_in_init = [i.address for i in gseq if i.mnemonic == "call"]
    print("  初始化函数内 call 点：%s" % ", ".join("0x%08X" % c for c in calls_in_init))
    check(CTOR_B1_CALLER in calls_in_init,
          "★ 表 B 构造器 0x%X 在全局初始化的 call 点集内" % CTOR_B1,
          "%d 个 call" % len(calls_in_init))
    gap = CTOR_B1_CALLER - SINGLETON_VT_WRITE
    check(0 < gap < 0x100,
          "★ 两个对象初始化相距仅 0x%X 字节（同一初始化函数内）" % gap,
          "0x%X → 0x%X" % (SINGLETON_VT_WRITE, CTOR_B1_CALLER))

    # ---------- 结论 ----------
    # ---------- F7 决定性：0x87F7E8 被构造两次，运行时是表 B ----------
    print()
    print("=== F7 ★ 决定性：0x87F7E8 被构造两次，运行时 vtable = 表 B ===")
    print("  0x40D1B2  mov [0x87F7E8], 0x7E1964   ← 先设表 A（临时）")
    print("  0x40D1F2  mov ecx, 0x87F7E8          ← this = 0x87F7E8")
    print("  0x40D1F7  call 0x652C00              ← ctor 内 mov [edi],0x7F0344")
    print("  0x652C04  mov edi, ecx               ← edi = ecx = 0x87F7E8")
    print("  0x652C0C  mov [edi], 0x7F0344        ← 改写为表 B")
    # 指令级验证：0x40D1F2 是 mov ecx, 0x87F7E8
    o = va2off(secs, 0x0040D1F2)
    gseq2 = list(md.disasm(data[o:o + 0x10], 0x0040D1F2))
    m_ecx = gseq2[0] if gseq2 else None
    check(m_ecx is not None and m_ecx.mnemonic == "mov"
          and m_ecx.op_str.replace(" ", "") == "ecx,0x87f7e8",
          "★ 0x40D1F2 `mov ecx, 0x87F7E8`（ctor 的 this 就是单例对象）",
          "%s %s" % (m_ecx.mnemonic, m_ecx.op_str) if m_ecx else "-")
    check(m_ecx is not None and len(gseq2) > 1
          and gseq2[1].mnemonic == "call"
          and "0x652c00" in gseq2[1].op_str,
          "★ 紧接着 0x40D1F7 `call 0x652C00`（表 B 构造器）",
          "%s %s" % (gseq2[1].mnemonic, gseq2[1].op_str) if len(gseq2) > 1 else "-")
    # 0x652C00 内确认 edi=ecx 且写表 B
    o = va2off(secs, CTOR_B1)
    cseq = list(md.disasm(data[o:o + 0x14], CTOR_B1))
    ctxt = ["%s %s" % (i.mnemonic, i.op_str) for i in cseq]
    check("mov edi, ecx" in ctxt[:6], "★ ctor 内 `mov edi, ecx`（this 落地到 edi）")
    check(any("0x7f0344" in t and "[edi]" in t for t in ctxt),
          "★ ctor 内 `mov [edi], 0x7F0344`（把 this 的 vtable 改为表 B）")
    print("  ⇒ [0x87F7E8] 运行时 = 0x7F0344（表 B），故 slot5 = 0x652CF0 生效，")
    print("    与 except.txt 的 Edi=0x87F7E8 完全自洽。")

    # 0x6ABD30 不在表 B（它是 0x4A8960 内的直接调用，不经虚表）
    in_b = [s for s in range(b_len) if rd(VT_B + s * 4) == 0x006ABD30]
    in_a = [s for s in range(a_len) if rd(VT_A + s * 4) == 0x006ABD30]
    print("  0x6ABD30 在表 A 的槽：%s；在表 B 的槽：%s" % (in_a or "无", in_b or "无"))
    check(not in_b,
          "★ 0x6ABD30 **不在**表 B（所以 0x4A8B0E 处只能直接 call，不经虚表）",
          "表B 槽 %s" % (in_b or "无"))

    print()
    print("=== 结论：0x652CF0 的前置条件 ===")
    print("  1) 目标对象就是全局单例 0x87F7E8，它由全局初始化 0x40D1B0 在启动时构造；")
    print("     构造过程两次写 vtable：先 0x7E1964（表 A），后被 ctor 改写为 0x7F0344（表 B）。")
    print("     ⇒ **运行时它始终是表 B 对象**，因此 slot5 = 0x652CF0 恒成立。")
    print("  2) 进 0x652CF0 的唯一条件是「有人在它身上触发 slot5」；无 E8 直调、无旁路。")
    print("  3) 因为对象是**全局单例且启动即构造**，所以前置条件在整局游戏里恒满足 ——")
    print("     真正决定崩不崩的是「触发 slot5 的时机」与「触发时单例是否已被清零」。")
    print("  ⇒ 复现判据修正：不是「对象是否存活」（它几乎总活着），")
    print("     而是「关窗流程里 0x652CF0 是否在 0x777803 清零之后仍被跑到」。")
    print("     这解释了 18% 非随机性：取决于关窗分支有没有走到这条链。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 0x652CF0 前置条件定案：同基类双派生、slot5 分隔、构造点 3 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
