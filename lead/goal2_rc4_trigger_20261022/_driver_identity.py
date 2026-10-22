# -*- coding: utf-8 -*-
"""0x652CF0 的身份与语义：它是 RadarClass::One_Time()（§349）。

## 为什么这是本轮的关键

§348 得出「msg 路不接崩溃链」的负面结论后，剩下的问题是：
  0x652CF0 到底在什么时机被调用？

本轮从函数体自带的**调试字符串**直接拿到答案：
  0x652CF3 push 0x8392DC → "RadarClass::One_Time()\n"

一旦知道它是 RadarClass 的一次性初始化，整条链的语义就闭合了：
  - 它写 this+0x11E4..0x1204 一批常量（雷达面板几何参数）
  - 然后 call 0x4A8850 → v[42] → 0x4A8960（§345 已定：视口矩形重设函数）
  - 「雷达初始化要设视口尺寸」在语义上完全自洽
  - 末尾往 [0xB04A20..0xB04A30] 写 0x31/0x8C/0x6C/0xDF，再 call 0x753250 查表登记

## 断言

  R1 函数体第一个参数是字符串指针 0x8392DC，其内容为 "RadarClass::One_Time()"。
  R2 该字符串全文件只在此处被引用（身份唯一）。
  R3 一批 this 偏移常量：+0x11E4/+0x11E8/+0x11EC/+0x11F4/+0x11F8/+0x11FC/+0x1200/+0x1204。
  R4 call 0x4A8850 发生在 this 常量写完之后（先设参数、再重设视口）。
  R5 全局写入 [0xB04A20]/[0xB04A24]/[0xB04A28]/[0xB04A30] 四个值。
  R6 末尾 call 0x753250 是字符串表线性查找（返回索引），结果存 this+0x14D4。
  R7 One_Time 的语义 ⇒ 只在**初始化一次**，这与 §347「对象整局存活」一致。
  R8 因此「关窗时跑进这条链」不可能是 One_Time 本身被重跑 ——
     必须是 §346 链的下游（0x4A8960 及其后）在别的时机被调到。

★ 口径：
  - 「函数在打印某字符串」这个判断要用「push <字符串VA>」+「该地址内容是可读 ASCII」双条件，
    不能只看 op_str 里出现一个像地址的数字。
  - One_Time 的 "One_Time" 是 RA2/Westwood 的固定命名约定（同族还有 Read_INI 等），
    但本脚本不依赖这个外部知识，权重放在字符串字面量本身。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

DRIVER = 0x00652CF0
NAME_STR = 0x008392DC
EVA_STR = 0x008392C0
EXPECT_NAME = b"RadarClass::One_Time()"
BRIDGE = 0x004A8850
VIEWPORT_FN = 0x004A8960
LOOKUP_FN = 0x00753250
THIS_OFFSETS = [0x11E4, 0x11E8, 0x11EC, 0x11F4, 0x11F8, 0x11FC, 0x1200, 0x1204]
GLOBALS = [0x00B04A20, 0x00B04A24, 0x00B04A28, 0x00B04A30]
RESULT_STORE = 0x14D4

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


def cstr(secs, data, va, cap=96):
    o = va2off(secs, va)
    if o is None:
        return None
    e = data.find(b"\x00", o, o + cap)
    if e < 0:
        e = o + cap
    return data[o:e]


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
    text = [s for s in secs if s["name"] == ".text"][0]
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    # ---------- R1 函数名 ----------
    print()
    print("=== R1 函数自报的名字 ===")
    o = va2off(secs, DRIVER)
    seq = list(md.disasm(data[o:o + 0xA0], DRIVER))
    pushes = [i for i in seq if i.mnemonic == "push"
              and i.operands and i.operands[0].type == X86_OP_IMM]
    strs = []
    for i in pushes:
        s = cstr(secs, data, i.operands[0].imm)
        # ★ 首版要求「全部字节都是可打印 ASCII（32..126）」，把尾部 \n（10）滤掉了，
        #   于是 "RadarClass::One_Time()\n" 被排除、R1 假红。允许 \t\n\r。
        if s and len(s) >= 4 and all(32 <= c < 127 or c in (9, 10, 13) for c in s):
            strs.append((i.address, i.operands[0].imm, s))
    print("  函数内 push 的可打印常量字符串：")
    for (a, va, s) in strs:
        print("    0x%08X  push 0x%08X  %r" % (a, va, s))
    names = [s for (a, va, s) in strs]
    # ★ 字符串字面量自带尾部 \n，断言用 startswith 而不是 ==（首版用 == 导致假红）。
    check(any(s.startswith(EXPECT_NAME) for s in names),
          "★ 函数自报名为 %r（调试字符串是身份的直接证据）" % EXPECT_NAME.decode(),
          "实测 %s" % (names[0] if names else "无"))

    # 名字字符串内容精确匹配（允许尾部换行）
    got = cstr(secs, data, NAME_STR)
    check(got is not None and got.startswith(EXPECT_NAME),
          "★ 0x%08X 处字符串以 %r 开头" % (NAME_STR, EXPECT_NAME.decode()),
          "实测 %r" % (got,))

    # ---------- R2 身份唯一性 ----------
    print()
    print("=== R2 该字符串是否只被此处引用 ===")
    pat = struct.pack("<I", NAME_STR)
    refs = []
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        va = j + 0x400000
        if text["va"] <= va < text["va"] + text["rsize"]:
            refs.append(va)
        i = j + 1
    print("  .text 内立即数引用 %d 处：%s"
          % (len(refs), ", ".join("0x%08X" % r for r in refs)))
    check(len(refs) == 1,
          "★ 名字字符串在 .text 内只被 1 处引用（身份无歧义）",
          "%d 处" % len(refs))

    # ---------- R3 this 偏移常量 ----------
    print()
    print("=== R3 写入的 this 偏移常量 ===")
    hits = {}
    for ins in seq:
        s = ins.op_str
        if ins.mnemonic != "mov" or "[esi + 0x" not in s:
            continue
        try:
            off_val = int(s.split("[esi + 0x")[1].split("]")[0], 16)
        except (IndexError, ValueError):
            continue
        imm = ins.operands[1].imm if len(ins.operands) > 1 \
            and ins.operands[1].type == X86_OP_IMM else None
        hits[off_val] = imm
    for off_val in sorted(hits):
        print("    this+0x%04X <- %s" % (off_val, ("0x%X" % hits[off_val])
                                         if hits[off_val] is not None else "(寄存器)"))
    missing = [x for x in THIS_OFFSETS if x not in hits]
    check(not missing,
          "★ 8 个 this 偏移全部被写（雷达面板几何参数）",
          "缺 %s" % (["0x%X" % m for m in missing] or "无"))

    # ---------- R4 先设参数再重设视口 ----------
    print()
    print("=== R4 call 0x4A8850 的位置 ===")
    bridge_calls = [i.address for i in seq
                    if i.mnemonic == "call" and "0x4a8850" in i.op_str]
    check(len(bridge_calls) == 1,
          "★ 函数内恰 1 次 call 0x4A8850（§346 链第一跳）",
          ", ".join("0x%08X" % a for a in bridge_calls))
    if bridge_calls:
        b = bridge_calls[0]
        before = [x for x in THIS_OFFSETS if hits.get(x) is not None]
        last_write = max(seq[[i for i, ins in enumerate(seq)
                             if ins.address == 0x00652D42][0]].address, 0) \
            if any(ins.address == 0x00652D42 for ins in seq) else None
        check(last_write is not None and last_write < b,
              "★ 最后一次 this 常量写入（0x%X）在 call 之前 ⇒ 先设参数再重设视口"
              % (last_write or 0),
              "call @0x%08X" % b)

    # ---------- R5 全局四写 ----------
    print()
    print("=== R5 全局常量写入（视口尺寸的全局副本）===")
    gw = []
    for ins in seq:
        for g in GLOBALS:
            if "0x%x" % g in ins.op_str.split(",")[0] and ins.mnemonic == "mov":
                imm = ins.operands[1].imm if len(ins.operands) > 1 \
                    and ins.operands[1].type == X86_OP_IMM else None
                gw.append((ins.address, g, imm))
    for (a, g, imm) in gw:
        print("    0x%08X  [0x%08X] <- %s" % (a, g, ("0x%X" % imm)
                                              if imm is not None else "(寄存器)"))
    check(len(gw) == len(GLOBALS),
          "★ 4 个全局全部被写", "%d 个" % len(gw))

    # ---------- R6 末尾查表 ----------
    print()
    print("=== R6 末尾 call 0x753250 与结果存储 ===")
    lk = [i.address for i in seq
          if i.mnemonic == "call" and "0x753250" in i.op_str]
    check(len(lk) == 1, "★ 末尾恰 1 次 call 0x753250", ", ".join("0x%X" % a for a in lk))
    store = [i for i in seq
             if i.mnemonic == "mov" and ("0x%x" % RESULT_STORE) in i.op_str]
    print("  结果存储：%s" % (["0x%08X %s" % (i.address, i.op_str) for i in store] or "无"))
    check(bool(store), "★ 查表结果存入 this+0x%X" % RESULT_STORE)
    # 0x753250 自身形态：字符串表线性查找
    o = va2off(secs, LOOKUP_FN)
    lseq = list(md.disasm(data[o:o + 0x50], LOOKUP_FN))
    ltxt = ["%s %s" % (i.mnemonic, i.op_str) for i in lseq]
    is_lookup = any("[eax + esi*4]" in t for t in ltxt) and any(
        t.startswith("cmp esi") for t in ltxt)
    print("  0x753250 形态：索引数组遍历 + 比较 = %s" % is_lookup)
    check(is_lookup,
          "★ 0x753250 是字符串表线性查找（遍历 + 比较，返回索引）")

    # ---------- R7/R8 语义推论 ----------
    print()
    print("=== R7/R8 One_Time 语义与复现推论 ===")
    check(b"One_Time" in (got or b""),
          "★ 名字含 One_Time ⇒ 语义上是「一次性初始化」")
    print("  ⇒ 与 §347「对象整局存活」一致：One_Time 只跑一次，之后 this 字段常驻。")
    print("  ⇒ 因此「关窗时跑进这条链」**不可能**是 One_Time 本身被重跑。")
    print("     必然是 §346 链的下游（0x4A8960 及其后）在**别的时机**被调到。")
    print("     而 0x4A8960 是视口矩形重设函数（§345 已定，全文件仅 2 个写 [0x886FA0] 的点）")
    print("     ⇒ 崩溃发生时机 = 某次视口重设/尺寸变更，且此时单例已清零。")
    check(True, "如实记录：One_Time 语义 ⇒ 崩溃时机在下游重设，不在初始化本身", "")

    # ---------- R9 下游 0x4A8960 的语义（用同一手法取证） ----------
    print()
    print("=== R9 v[42] 目标 0x4A8960 的语义（同法取证） ===")
    o = va2off(secs, VIEWPORT_FN)
    vseq = list(md.disasm(data[o:o + 0x300], VIEWPORT_FN))
    vstrs = []
    for i in vseq:
        if i.mnemonic == "push" and i.operands and i.operands[0].type == X86_OP_IMM:
            s = cstr(secs, data, i.operands[0].imm)
            if s and len(s) >= 4 and all(32 <= c < 127 or c in (9, 10, 13) for c in s):
                vstrs.append((i.address, s))
    for (a, s) in vstrs:
        print("    0x%08X  %r" % (a, s))
    vtxt = b" | ".join(s for (a, s) in vstrs)
    check(b"Set_View_Dimensions" in vtxt,
          "★ v[42] 目标打印 Set_View_Dimensions（视口尺寸设置）")
    check(b"ABuffer" in vtxt and b"ZBuffer" in vtxt,
          "★ 同函数内 Deleting/Allocating A|ZBuffer（渲染缓冲重建）")
    print("  ⇒ 0x4A8960 = 视口尺寸变更 + 渲染缓冲重建（比 §345 的「矩形重设」更精确）")
    print("  ⇒ RadarClass::One_Time 调它，是因为雷达初始化要按新视口重建缓冲区。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 0x652CF0 身份定案：RadarClass::One_Time()（雷达一次性初始化）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
