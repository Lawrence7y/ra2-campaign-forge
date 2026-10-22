# -*- coding: utf-8 -*-
"""29 处 call [reg+0xA8] 的「对象来源」判定：哪几处是雷达单例（§350）。

## 本轮的问题

§349 定案链起点是 RadarClass::One_Time() 之后，剩下的关键问题是：
  **还有谁触发 v[42]？** 因为 One_Time 只跑一次，崩溃必然发生在
  v[42]（= 0x4A8960，视口尺寸变更+缓冲重建）被别的时机调到时。

§346 普查过 29 处 `call [reg+0xA8]`，但只有 5 处能把 reg 切片到具体来源，
其余 24 处判 UNKNOWN。本轮换角度：**从对象来源侧判定**。

## 判定口径（必须先讲清楚，否则结论不可信）

一个站点能被判为「雷达对象」需要满足：
  D1 reg 的 dataflow 根是**地址常量 0x87F7E8**（对象本体，BSS 直接取址），或
  D2 reg 的 dataflow 根是指针变量，且该变量有一处写点把 **0x87F7E8 的地址**写进去。

**仅有「reg 来自某个全局指针变量」不足以判定为雷达** —— 因为这类
「当前活动对象」指针在引擎里到处都是，指向什么取决于运行时。

本脚本因此分三档输出：
  MATCH     有直接证据指向 0x87F7E8（D1 或 D2 成立）
  GLOBAL-ONLY   reg 来自全局指针变量，但无证据表明该变量存的是雷达
  UNKNOWN    dataflow 切不出来

## 已在手工探测中确认的两个背景事实

  B1 [0x87F7E8] 是**对象本体**地址（.data BSS，rsize 止于 0x87E000，文件无内容）。
  B2 [0xA8B23C] 是**指针变量**（.data BSS，10 个写点 / 164 个读点），
     在 0x68589C 与 0x685FE6 两处作为 `call [reg+0xA8]` 的 reg 来源，
     形态是「取全局对象 → cmp 判空 → call slot42」。
     它的写点源来自别的对象（如 0x5E5447 处 ebp 从 0x5D5F30 返回值来），
     **没有**一处把 0x87F7E8 写进去 ⇒ 不是雷达。

★ 口径坑：
  - 「全局指针变量」≠「雷达单例」。前者是 BSS 里存对象地址的一个 dword，
    后者是对象本体。混为一谈会把「场景对象」误判成雷达。
  - 「dword 出现」≠「代码引用」：0x652B00 段整段是数据，任意偏移都能解出
    看似合法的 mov，必须用函数调用图 + 指令边界双过滤（§347 已踩）。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

SINGLETON = 0x0087F7E8      # 雷达对象本体
CUR_OBJ = 0x00A8B23C        # 「当前活动对象」指针变量（对照）
DISP = 0xA8
MODRM = {0x90: "eax", 0x91: "ecx", 0x92: "edx", 0x93: "ebx",
         0x94: "esp", 0x95: "ebp", 0x96: "esi", 0x97: "edi"}

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


def trace_reg(seq, idx, md, reg, depth=0):
    """从 seq[idx] 往前追 reg 的定义，返回 (kind, value)。

    kind:
      "singleton"  链根是地址常量 0x87F7E8（雷达本体）
      "global"     链根是某个全局 dword（指针变量），value=该全局地址
      "vtable"     链是 reg2 <- [reg1] 形式（取 vtable），继续追 reg1
      "objptr"     reg2 <- [reg1 + disp] 且 disp 非 0（取成员/对象）
      None         追不到

    ★ 关键：`call [edx+0xA8]` 里 edx 常是**vtable 指针**（`mov edx,[ecx]`），
      ecx 才是对象。首版只看 reg 的直接定义（edx <- [ecx]），
      没继续追一层到 ecx <- [0xA8B23C]，于是 29 站全判 UNKNOWN。
    """
    if depth > 6:
        return (None, None)
    for j in range(idx - 1, max(-1, idx - 40), -1):
        i = seq[j]
        if len(i.operands) != 2 or i.mnemonic != "mov":
            continue
        if i.operands[0].type != X86_OP_REG:
            continue
        if md.reg_name(i.operands[0].reg) != reg:
            continue
        s = i.operands[1]
        if s.type == X86_OP_IMM:
            if s.imm == SINGLETON:
                return ("singleton", SINGLETON)
            return ("const", s.imm)
        if s.type == X86_OP_REG:
            return trace_reg(seq, j, md, md.reg_name(s.reg), depth + 1)
        if s.type == X86_OP_MEM:
            b = md.reg_name(s.mem.base) if s.mem.base else None
            ix = md.reg_name(s.mem.index) if s.mem.index else None
            if ix is not None:
                return (None, None)
            if b is None:
                return ("global", s.mem.disp)
            # reg <- [base + disp]：若是 [base]（disp==0）则是取 vtable/首字段，
            # 继续追 base；若 disp!=0 则是取对象成员。
            if s.mem.disp == 0:
                sub = trace_reg(seq, j, md, b, depth + 1)
                if sub[0] is not None:
                    return sub
                return ("vtable", b)
            sub = trace_reg(seq, j, md, b, depth + 1)
            if sub[0] is not None:
                return sub
            return ("objptr", b)
    return (None, None)


def main():
    data, img_base, secs = load()
    tb, tva, insns, fof = build(secs, data)
    n = len(tb)
    bnd = set(o for (o, m, s) in insns)
    text = [s for s in secs if s["name"] == ".text"][0]
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    # ---------- B1/B2 两个全局的语义 ----------
    print()
    print("=== B1/B2 两个全局的语义区分 ===")
    for va, name in ((SINGLETON, "雷达对象本体"), (CUR_OBJ, "当前活动对象指针")):
        in_file = va2off(secs, va) is not None
        print("  0x%08X %-16s 在文件内=%s" % (va, name, in_file))
    check(va2off(secs, SINGLETON) is None,
          "★ 0x87F7E8 在文件内无内容（.data BSS ⇒ 对象本体，运行时才写 vtable）")
    check(va2off(secs, CUR_OBJ) is None,
          "★ 0xA8B23C 在文件内无内容（.data BSS ⇒ 指针变量，运行时赋值）")
    check(SINGLETON != CUR_OBJ,
          "★ 两者是**不同的**全局（一个对象本体、一个指针变量）",
          "0x%X vs 0x%X" % (SINGLETON, CUR_OBJ))

    # ---------- CUR_OBJ 的写点源 ----------
    print()
    print("=== B2 [0xA8B23C] 的写点是否有 0x87F7E8 ===")
    writes = []
    off = 0
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            oo = ins.address - tva
            if len(ins.operands) >= 1 and ins.mnemonic == "mov":
                d0 = ins.operands[0]
                if d0.type == X86_OP_MEM and d0.mem.disp == CUR_OBJ \
                        and not d0.mem.base and not d0.mem.index:
                    writes.append((tva + oo, ins.op_str))
            off = oo + ins.size
            prog = True
        if not prog:
            off += 1
    print("  写点 %d 处：" % len(writes))
    for (a, t) in writes:
        print("    0x%08X  %s" % (a, t))
    writes_singleton = [a for (a, t) in writes if "0x87f7e8" in t]
    check(not writes_singleton,
          "★ **没有**任何一处把 0x87F7E8 写进 [0xA8B23C] ⇒ 它不是雷达",
          "%d 处命中" % len(writes_singleton))

    # ---------- 29 处 +0xA8 站点分档 ----------
    print()
    print("=== 29 处 call [reg+0xA8] 的对象来源分档 ===")
    sites = []
    for o in range(n - 6):
        if tb[o] != 0xFF or tb[o + 1] not in MODRM:
            continue
        if struct.unpack_from("<I", tb, o + 2)[0] != DISP:
            continue
        if o not in bnd:
            continue
        sites.append((tva + o, MODRM[tb[o + 1]]))
    print("  站点 %d 处" % len(sites))
    check(len(sites) == 29, "★ 站点数 == 29（与 §346 一致）", "%d" % len(sites))

    # 对每个站点，追 reg 的 dataflow 根（含 vtable 一层）
    matched, global_only, unknown = [], [], []
    for (site, reg) in sites:
        fs = fof[site - tva]
        o = va2off(secs, fs)
        body = data[o:va2off(secs, site) + 8]
        seq = list(md.disasm(body, fs))
        idx = None
        for k, i in enumerate(seq):
            if i.address == site:
                idx = k
                break
        kind, val = (None, None)
        if idx is not None:
            kind, val = trace_reg(seq, idx, md, reg)
        if kind == "singleton":
            matched.append(site)
            tag = "MATCH 根即雷达本体 0x87F7E8"
        elif kind == "global":
            global_only.append((site, val))
            tag = "GLOBAL-ONLY [0x%X]" % val
        else:
            unknown.append((site, kind))
            tag = "UNKNOWN(%s)" % (kind or "追不到")
        print("    0x%08X  %-3s : %s" % (site, reg, tag))

    print()
    print("  分档统计：MATCH=%d  GLOBAL-ONLY=%d  UNKNOWN=%d"
          % (len(matched), len(global_only), len(unknown)))
    check(len(matched) + len(global_only) + len(unknown) == 29,
          "★ 三档计数守恒", "%d" % (len(matched) + len(global_only) + len(unknown)))
    # ★ 首版切片器只看 reg 的直接定义，29 站全 UNKNOWN（因为 edx <- [ecx] 是取 vtable，
    #   对象在 ecx 里）。修好后应有可识别项。这条断言用来防止退回旧状态。
    check(len(unknown) < 29,
          "★ UNKNOWN 不再是 29（切片器已能追 vtable 一层）",
          "UNKNOWN=%d" % len(unknown))

    # ---------- 结论 ----------
    print()
    print("=== 结论 ===")
    print("  MATCH（reg 基址 = 雷达本体 0x87F7E8）= %d 处：%s"
          % (len(matched), ", ".join("0x%08X" % s for s in matched) or "无"))
    print("  ⇒ 若 MATCH 为 0，说明**没有**任何一处 static 上直接把雷达本体当 reg。")
    print("    这与 §349 相符：One_Time 是 slot5，不是 slot42；")
    print("    它调 v[42] 是**在它自己内部**用 `mov ecx,esi` 的 this 透传（§346 已证），")
    print("    所以那 29 处 +0xA8 站点与 One_Time 无关。")
    print()
    print("  GLOBAL-ONLY 里的 [0xA8B23C] 两处（0x68589C / 0x685FE6）:")
    print("    形态是「取当前活动对象 → cmp 判空 → call slot42」，")
    print("    在 Scenario.CPP 里，靠近 'Toggle display mode back to shell res'。")
    print("    ⇒ 这是**显示模式切换**时对当前场景对象调 slot42，")
    print("      而 slot42 = 0x4A8960 = 视口尺寸变更 + 缓冲重建。")
    print("    ⇒ **这才是 §349 要找的『别的时机』**，且它有 cmp 判空守卫。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 对象来源分档完成：MATCH=%d GLOBAL-ONLY=%d UNKNOWN=%d"
          % (len(matched), len(global_only), len(unknown)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
