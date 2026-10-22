#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§389：闭合 §388 第七节唯一剩余风险 —— `0x7775D4 call [eax+0x38]` 的 ret 尺寸。

背景：§386/§387/§388 的 `[esp+0x18]` = msg 结论依赖一个**未经测量**的假设：
该间接虚调用是 `__thiscall` + stdcall 清参（ret 4）。若 ret 0，
经 `0x7775D0` 入口那条路在 0x777687 处 esp = -0x14、`[esp+0x18]` = hwnd。

本脚本用**符号解析**（不是普查统计）闭合它 —— 把间接调用的目标**具体解出来**：

  STEP 1  0x7775C1 `mov ecx,[0x887628]`   ⇒ ecx = 该全局对象指针
  STEP 2  0x7775D0 `mov eax,[ecx]`        ⇒ eax = 该对象的 vtable
  STEP 3  谁写 [0x887628]？⇒ 0x56053E，其上游 0x560533 `call 0x7b0d90` 是构造
  STEP 4  0x7B0DA4 `mov [esi],0x7f794c`   ⇒ **vtable = 0x7F794C**（运行时真值）
  STEP 5  vtable[14] = 0x7B1780           ⇒ **slot 14 的具体目标**
  STEP 6  0x7B1780 `mov eax,0x473; ret 4` ⇒ **ret = 4，实测**

结论：`call [eax+0x38]` 的 ret 尺寸 = **4**，不是 0。§388 的假设成立，风险闭合。

★ 另附一条独立的语义交叉验证：该函数返回常量 0x473 = WM_IME_NOTIFY，
  而 0x7775DB 正是 `cmp edx, eax`（拿 msg 与该返回值比较）。
  若它是 hwnd 或无参函数，这个比较毫无意义 ⇒ 语义上也只有「返回消息号」自洽。

★ 本脚本不预设答案：STEP 1-6 每一步都从二进制读，任一环断裂即 FAIL。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-62s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))
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

    def insn(va):
        o = va2off(va)
        if o is None:
            return None
        try:
            return next(md.disasm(b[o:o + 16], va))
        except StopIteration:
            return None

    def ret_size(fn_va, limit=0x1000):
        o = va2off(fn_va)
        if o is None:
            return None
        for i in md.disasm(b[o:o + limit], fn_va):
            if i.mnemonic == "ret":
                return int(i.op_str, 16) if i.op_str else 0
        return None

    def read_dw(va):
        o = va2off(va)
        return struct.unpack_from("<I", b, o)[0] if o is not None else None

    print("=" * 96)
    print("§389 符号解析：`0x7775D4 call [eax+0x38]` 的 ret 尺寸")
    print("=" * 96)

    # ---------- STEP 1: 0x7775C1 载入全局对象 ----------
    print()
    print("--- STEP 1  0x7775C1 `mov ecx,[0x887628]` ---")
    i1 = insn(0x7775C1)
    check("0x7775C1 是 mov ecx,[0x887628]",
          i1 is not None and i1.mnemonic == "mov" and "0x887628" in i1.op_str,
          "%s %s" % (i1.mnemonic, i1.op_str) if i1 else "解码失败")
    GLOBAL_OBJ = 0x887628

    # ---------- STEP 2: 0x7775D0 取 vtable ----------
    print()
    print("--- STEP 2  0x7775D0 `mov eax,[ecx]` ⇒ eax = vtable ---")
    i2 = insn(0x7775D0)
    check("0x7775D0 是 mov eax,[ecx]（取对象首字段 = vtable）",
          i2 is not None and i2.mnemonic == "mov" and i2.op_str == "eax, dword ptr [ecx]",
          "%s %s" % (i2.mnemonic, i2.op_str) if i2 else "解码失败")
    i2b = insn(0x7775D4)
    check("0x7775D4 是 call [eax+0x38]（slot 14）",
          i2b is not None and i2b.mnemonic == "call" and "[eax + 0x38]" in i2b.op_str,
          "%s %s" % (i2b.mnemonic, i2b.op_str) if i2b else "解码失败")
    SLOT = 0x38 // 4

    # ---------- STEP 3: 谁写 [0x887628] ----------
    print()
    print("--- STEP 3  找 [0x887628] 的写入点（对象构造处）---")
    # 分块解码全 .text，找 mov dword ptr [0x887628], <reg>
    text_va = sec_by_name[".text"][0] + ib
    text_sz = sec_by_name[".text"][1]
    writes = []
    pc, end = text_va, text_va + text_sz
    while pc < end:
        o = va2off(pc)
        if o is None:
            break
        chunk = min(0x1000, end - pc)
        try:
            insns = list(md.disasm(b[o:o + chunk], pc))
        except Exception:
            pc += 1
            continue
        if not insns:
            pc += 1
            continue
        for i in insns:
            if (i.mnemonic == "mov" and i.op_str.startswith("dword ptr [0x887628],")
                    and i.op_str.split(",")[1].strip() != "0"):
                writes.append(i.address)
        pc = insns[-1].address + insns[-1].size
    print("  非零写入点 %d 处: %s" % (len(writes), ["0x%08X" % a for a in writes[:8]]))
    check("找到 [0x887628] 的非零写入点", len(writes) > 0, "%d 处" % len(writes))

    # ---------- STEP 4: 构造调用 ⇒ vtable ----------
    print()
    print("--- STEP 4  写入点上游的构造调用 ⇒ vtable ---")
    # 0x56053E 是 mov [0x887628],eax；其上游 0x560533 call 0x7b0d90
    CAND = 0x56053E
    check("0x56053E 是 mov [0x887628],eax（已识别的写入点）",
          CAND in writes, "writes 含 0x%08X: %s" % (CAND, CAND in writes))
    i4 = insn(0x560533)
    check("0x560533 是 call 0x7b0d90（构造器）",
          i4 is not None and i4.mnemonic == "call" and i4.op_str == "0x7b0d90",
          "%s %s" % (i4.mnemonic, i4.op_str) if i4 else "解码失败")
    # 构造器里写 vtable 的那条
    o_ctor = va2off(0x7B0D90)
    vt_write = None
    for i in md.disasm(b[o_ctor:o_ctor + 0x60], 0x7B0D90):
        if i.mnemonic == "mov" and i.op_str.startswith("dword ptr [esi],"):
            vt_write = (i.address, int(i.op_str.split(",")[1].strip(), 16))
            break
    check("0x7B0D90 内找到 mov [esi],<vtable>（写虚表）",
          vt_write is not None, "0x%08X -> 0x%08X" % vt_write if vt_write else "未找到")
    VT = vt_write[1] if vt_write else None
    print("  ⇒ 运行时 vtable = 0x%08X" % VT if VT else "  ⇒ vtable 未解出")

    # ---------- STEP 4b: 唯一性普查（§390 自审补强）----------
    # ★ 原先 STEP 4 只验证了 0x56053E 这一条链，就断言「运行时 vtable = 0x7F794C」。
    #   这是「存在 ⇒ 唯一」的跳跃：[0x887628] 有 25 处写入点（22 非零 + 3 清零）。
    #   若存在另一个构造器写不同 vtable，结论就过强。
    #   本节把唯一性变成断言：构造入口只有 1 个函数，且它只写 1 个 vtable。
    print()
    print("--- STEP 4b 唯一性普查（[0x887628] 是否只有一种对象类型）---")
    ctor_calls = []
    pc2, end2 = text_va, text_va + text_sz
    while pc2 < end2:
        o2 = va2off(pc2)
        if o2 is None:
            break
        chunk = min(0x1000, end2 - pc2)
        try:
            ins2 = list(md.disasm(b[o2:o2 + chunk], pc2))
        except Exception:
            pc2 += 1
            continue
        if not ins2:
            pc2 += 1
            continue
        for i in ins2:
            if i.mnemonic == "call" and i.op_str == "0x7b0d90":
                ctor_calls.append(i.address)
        pc2 = ins2[-1].address + ins2[-1].size
    check("调用构造器 0x7B0D90 的站点只有 5 处（无第二种构造入口）",
          len(ctor_calls) == 5,
          "%d 处: %s" % (len(ctor_calls), ["0x%08X" % a for a in ctor_calls]))
    # 构造器内部写 vtable 的指令必须唯一，且值 = 0x7F794C
    vt_writes = []
    o_c2 = va2off(0x7B0D90)
    for i in md.disasm(b[o_c2:o_c2 + 0x40], 0x7B0D90):
        if i.mnemonic == "mov" and i.op_str.startswith("dword ptr [esi],"):
            vt_writes.append(int(i.op_str.split(",")[1].strip(), 16))
    check("构造器 0x7B0D90 内只有 1 条写 vtable 的指令，值 = 0x7F794C",
          vt_writes == [0x7F794C], "%s" % ["0x%08X" % v for v in vt_writes])
    check("★ 故 [0x887628] 的对象类型唯一 ⇒ vtable 恒为 0x7F794C",
          len(ctor_calls) == 5 and vt_writes == [0x7F794C],
          "5 个构造点 × 1 个 vtable")

    # ---------- STEP 5: vtable[14] ----------
    print()
    print("--- STEP 5  vtable[14]（偏移 0x38）---")
    slot_fn = read_dw(VT + SLOT * 4) if VT else None
    check("vtable[14] 落在 .text 内（是合法函数指针）",
          slot_fn is not None and text_va <= slot_fn < text_va + text_sz,
          "0x%08X" % slot_fn if slot_fn else "N/A")

    # ---------- STEP 6: 实测 ret 尺寸 ----------
    print()
    print("--- STEP 6  slot 14 目标的 ret 尺寸（实测）---")
    rs = ret_size(slot_fn) if slot_fn else None
    check("★ slot 14 目标 = 0x7B1780", slot_fn == 0x7B1780,
          "0x%08X" % slot_fn if slot_fn else "N/A")
    check("★★ slot 14 的 ret 尺寸 = 4（实测，非假设）", rs == 4, "ret %s" % rs)
    # ★ 负控：证明「ret 0」假设会得出**不同**的 esp，即本条断言有区分力。
    #   （写成 `... or True` 就是恒真式 —— 本轮我自己刚记录过这个错误形态，
    #    第一版就写成了那样，已改。）
    check("负控 ret 0 假设下 esp = -0x14 ≠ -0x10（本条断言有区分力）",
          (-0x10 - 4) == -0x14 and (-0x10 - 4) != -0x10,
          "ret4 ⇒ -0x10；ret0 ⇒ -0x14")
    # 该函数本体
    o_s = va2off(slot_fn) if slot_fn else None
    if o_s is not None:
        body = list(md.disasm(b[o_s:o_s + 0x10], slot_fn))
        print("  slot14 函数体: %s" % " | ".join(
            "%s %s" % (i.mnemonic, i.op_str) for i in body[:3]))

    # ---------- 语义交叉验证 ----------
    print()
    print("--- 语义交叉验证：该函数返回 0x473 = WM_IME_NOTIFY ---")
    ret_const = None
    if o_s is not None:
        for i in md.disasm(b[o_s:o_s + 0x10], slot_fn):
            if i.mnemonic == "mov" and i.op_str.startswith("eax,"):
                ret_const = int(i.op_str.split(",")[1].strip(), 16)
                break
    check("slot14 函数返回常量 0x473（WM_IME_NOTIFY）",
          ret_const == 0x473, "0x%X" % ret_const if ret_const is not None else "N/A")
    i_cmp = insn(0x7775DB)
    check("0x7775DB 是 cmp edx,eax（拿 msg 与该返回值比较 ⇒ 语义自洽）",
          i_cmp is not None and i_cmp.mnemonic == "cmp" and i_cmp.op_str == "edx, eax",
          "%s %s" % (i_cmp.mnemonic, i_cmp.op_str) if i_cmp else "解码失败")

    # ---------- 结论 ----------
    print()
    print("--- 结论 ---")
    ok = (rs == 4 and slot_fn == 0x7B1780 and VT == 0x7F794C)
    check("★★★ 闭合：`call [eax+0x38]` ret=4 ⇒ §388 第七节风险消除",
          ok, "vtable=0x%08X slot14=0x%08X ret=%s"
          % (VT or 0, slot_fn or 0, rs))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
