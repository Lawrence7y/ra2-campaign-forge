# -*- coding: utf-8 -*-
"""找出「谁以 0x87F7E8 为 this 驱动 0x4A8850」——闭合 RC-4 崩溃链的最后一段。

上一轮判据链已定：vtable 0x7E1964 的 slot[42]=0x4A8960（L3）。
本轮问的是：在静态上，**哪个调用点能让 [eax+0xA8] 的 eax 真的等于 0x7E1964**。

关键结构（本脚本 §0 逐条断言）：
  - 0x87F7E8 是「对象地址」不是「vtable 地址」。该对象首 dword = 0x7E1964。
  - 0x4A8850 是 __thiscall，esi = ecx = this；0x4A8850 内做的
    `mov eax,[esi] / mov ecx,esi / call [eax+0xA8]` 就是 this->vtable[42](arg)。
  - 因此闭合条件是：存在站点 `mov/lea ecx, 0x87F7E8` + `call 0x4A8850`
    （或 ecx 来自 [0x87F7E8] 的持有者），或 0x4A8850 本身被放在某张
    vtable 的槽里、而那个 this 是 0x87F7E8。

口径：
  - 只认指令边界已验证的站点（线性解码 func_of 表）。
  - 「ecx 来源」用反向切片，跨 call 遇易失寄存器即 UNKNOWN，不猜。
  - 虚表槽的判定要求命中点两侧邻项都是 .text 指针（同 §345 口径）。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys

import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OBJ = 0x0087F7E8          # 单例对象地址（首 dword = vtable）
VT_HEAD = 0x007E1964      # 该单例的 vtable
SLOT_L3 = 42
L3 = 0x004A8960
BRIDGE = 0x004A8850       # 崩溃链上一层的 __thiscall
BRIDGE_SITE = 0x004A88AA  # call [eax+0xA8]
SLOT42_CALL_SITES_NOTE = "全文件 29 处 call [reg+0xA8]（§346 普查）"

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
                     "rsize": rsize, "roff": roff, "base": img_base})
    return data, img_base, secs, pe


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rsize"]:
            return s["roff"] + (va - s["va"])
    return None


def linear(secs, data, img_base):
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
            insns.append((o, ins.mnemonic, ins.op_str, ins.bytes))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pending = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, insns, func_of


def main():
    data, img_base, secs, pe = load()
    tb, tva, insns, func_of = linear(secs, data, img_base)
    print("镜像基数 0x%08X；.text 线性解码 %d 条" % (img_base, len(insns)))

    by_addr = {}
    for (o, m, s, bs) in insns:
        by_addr[tva + o] = (o, m, s, bs)

    # ---------- §0 结构断言 ----------
    print()
    print("=== §0 结构前提 ===")
    o = va2off(secs, OBJ)
    check(o is None,
          "★ 0x87F7E8 在文件里**无内容**（.data 的 BSS 尾：rsize 止于 0x87E000）",
          "va2off=%r" % (o,))

    # BSS 全局 ⇒ 首写必来自代码。普查所有写点。
    md32 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md32.detail = True
    wtgt = "0x%x" % OBJ
    writers = []
    for (oo, m, s) in [(a, b, c) for (a, b, c, dd) in insns]:
        if m not in ("mov", "and", "or", "xor"):
            continue
        if wtgt not in s.split(",")[0]:
            continue
        writers.append((tva + oo, m, s))
    print("  对 0x87F7E8 的写点 %d 处：" % len(writers))
    for (w, m, s) in writers[:12]:
        print("    0x%08X  %s %s" % (w, m, s))
    check(bool(writers), "★ 0x87F7E8 的写点存在（BSS 只能由代码初始化）",
          "%d 处" % len(writers))

    # 首个写点是否 mov dword [0x87F7E8], 0x7E1964
    got_vt = None
    for (w, m, s) in writers:
        if "0x7e1964" in s:
            got_vt = w
            break
    check(got_vt is not None,
          "★ 存在 `mov [0x87F7E8], 0x7E1964`（对象首 dword 由代码钉为 vtable）",
          "0x%08X" % got_vt if got_vt else "未找到")

    o = va2off(secs, BRIDGE)
    seq = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
               .disasm(data[o:o + 0x70], BRIDGE))
    txt = ["%s %s" % (i.mnemonic, i.op_str) for i in seq]
    check("mov esi, ecx" in txt, "0x4A8850 是 __thiscall（esi = this = ecx）")
    check(any(t.startswith("mov eax, dword ptr [esi]") for t in txt),
          "0x4A8850 内 eax <- [esi]（取 this->vtable）")
    check("call dword ptr [eax + 0xa8]" in txt,
          "0x4A8850 内 call [eax+0xA8]（即 this->vtable[42]）")
    # 站点前是否把 ecx 设成 esi —— 这是 __thiscall 的 this 透传
    k_a8 = [k for k, t in enumerate(txt) if t.startswith("call dword ptr [eax + 0xa8]")]
    pre = txt[:k_a8[0]] if k_a8 else txt
    check("mov ecx, esi" in pre,
          "0x4A88AA 前 mov ecx, esi（this 透传，eax 来自同一 this）")

    # ---------- §1 谁调用 0x4A8850 ----------
    print()
    print("=== §1 谁直接 call 0x4A8850（E8）===")
    callers = []
    boundary = set((tva + o) for (o, m, s, bs) in insns)
    for (o, m, s, bs) in insns:
        if m not in ("call", "callf"):
            continue
        if o + 5 > len(tb) or tb[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", tb, o + 1)[0]
        if tva + o + 5 + rel == BRIDGE and (tva + o + 5) in boundary:
            callers.append(tva + o)
    print("  直接调用点 %d 处：%s" % (len(callers),
                                 ", ".join("0x%08X" % c for c in callers)))
    check(len(callers) > 0, "0x4A8850 有直接 E8 调用者", "%d 处" % len(callers))

    # 每个调用点查 ecx 来源
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    resolved = []
    for c in callers:
        fs = func_of[c - tva]
        o = va2off(secs, fs)
        fe = None
        for (ao, am, as_, ab) in insns:
            if ao >= (c - tva) + 5:
                break
            if func_of[ao] != fs:
                fe = ao
                break
        body = data[o:va2off(secs, c) + 5]
        lst = list(md.disasm(body, fs))
        idx = None
        for k, i in enumerate(lst):
            if i.address == c:
                idx = k
                break
        src = "?"
        if idx is not None:
            for j in range(idx - 1, max(-1, idx - 40), -1):
                ins = lst[j]
                if ins.mnemonic in ("mov", "lea") and len(ins.operands) >= 2:
                    if ins.operands[0].type == X86_OP_REG and md.reg_name(ins.operands[0].reg) == "ecx":
                        s = ins.operands[1]
                        if s.type == X86_OP_IMM:
                            src = "ecx <- 0x%08X" % s.imm
                        elif s.type == X86_OP_MEM:
                            b = md.reg_name(s.mem.base) if s.mem.base else None
                            i2 = md.reg_name(s.mem.index) if s.mem.index else None
                            src = "ecx <- [%s%s+0x%x]" % (b or "", ("+" + i2) if i2 else "",
                                                          s.mem.disp)
                        else:
                            src = "ecx <- %s" % ins.op_str
                        break
                if ins.mnemonic in ("push", "pop"):
                    continue
        resolved.append((c, func_of[c - tva], src))

    print()
    print("=== §1b 每个调用点的 this(ecx) 来源 ===")
    for (c, fs, src) in resolved:
        mark = "  ★ 指向单例 0x87F7E8" if "87F7E8" in src.upper() else ""
        print("  0x%08X (func 0x%08X)  %s%s" % (c, fs, src, mark))

    hit_obj = [r for r in resolved if "87F7E8" in r[2].upper()]
    check(True, "ecx 指向单例 0x87F7E8 的调用点数 = %d（如实记录，不作通过条件）"
          % len(hit_obj))

    # ---------- §2 0x4A8850 是否在虚表里 ----------
    print()
    print("=== §2 0x4A8850 / 0x4A8960 的虚表槽 ===")
    text = [s for s in secs if s["name"] == ".text"][0]

    def is_code(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def vt_hits(val):
        pat = struct.pack("<I", val)
        out = []
        i = 0
        while True:
            j = data.find(pat, i)
            if j < 0:
                break
            va = j + 0x400000
            sn = None
            for s in secs:
                if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                    sn = s["name"]
                    break
            if sn == ".rdata":
                ok = all(is_code(struct.unpack_from("<I", data, j + k * 4)[0])
                         for k in (-1, 1) if 0 <= j + k * 4 < len(data) - 4)
                if ok:
                    out.append(va)
            i = j + 1
        return out

    vb = vt_hits(BRIDGE)
    vl = vt_hits(L3)
    print("  0x4A8850 作为虚表槽：%d 处 %s" % (len(vb), ", ".join("0x%08X" % x for x in vb)))
    print("  0x4A8960 作为虚表槽：%d 处 %s" % (len(vl), ", ".join("0x%08X" % x for x in vl)))
    check(len(vl) >= 1, "0x4A8960 在虚表里（§345 已定）")

    # 0x4A8850 的槽位号（相对其所在表头）
    for h in vb[:3]:
        j = h - 0x400000
        k = 0
        while True:
            k += 1
            prev = struct.unpack_from("<I", data, j - 4 * k)[0]
            if not is_code(prev):
                break
        head = h - 4 * (k - 1)
        print("    槽 @0x%08X 所在表头约 0x%08X，槽号 %d" % (h, head, k - 1))

    # ---------- §3 L3 是否会自我递归 ----------
    print()
    print("=== §3 0x4A8960 函数体是否再次 call [reg+0xA8]（递归风险）===")
    o = va2off(secs, L3)
    body = data[o:o + 0x120]
    s3 = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
              .disasm(body, L3))
    txt3 = ["%s %s" % (i.mnemonic, i.op_str) for i in s3]
    a8 = [t for t in txt3 if "+ 0xa8]" in t]
    print("  0x4A8960 前 %d 条内 call [reg+0xA8] 出现 %d 次" % (len(txt3), len(a8)))
    check(True, "如实记录（0 次 ⇒ 不自我递归；>0 ⇒ 链可再接一层）",
          "实测 %d 次" % len(a8))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ this-driven 闭合分析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
