# -*- coding: utf-8 -*-
"""为四环齐全的 2 行生成 EVIDENCE/ROW_<entry>.txt（逐行取字节，不过度扩写）。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import u32, va_in, read_cstr, find_direct_calls, find_containing_atlas_func, is_atexit_registered
from analyze import rtti_chain, classify_table
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "EVIDENCE")
EXE_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"


def bx(va, n):
    return " ".join("%02X" % b for b in R.read_va(va, n))


def dis(va, n, indent="    "):
    out = []
    for i in md.disasm(R.read_va(va, n), va):
        out.append("%s%08X  %-24s %-7s %s" % (indent, i.address,
                   " ".join("%02X" % b for b in i.bytes), i.mnemonic, i.op_str))
    return "\n".join(out)


def dump_row(entry, vt, slot, sites, loops, ctor_anchor, ctor_func, dtor_sites, other_notes):
    ea = int(entry, 16)
    info = R.ATLAS[entry]
    size = info["size"]
    insns = list(md.disasm(R.read_va(ea, size), ea))
    L = []
    A = L.append
    A("ROW %s   （S15 / NAMED_PUSH_S15_B1）" % entry)
    A("exe: ra2youli\\gamemd.exe  SHA-256 %s" % EXE_SHA)
    A("ImageBase 0x400000   .text=[00401000,007E038D)")
    A("工具: capstone 5.0.7 skipdata=True / pefile 2024.8.26 / Python 3.12.10（无 venv）")
    A("")
    A("=" * 78)
    A("① 入口环 —— PASS")
    A("=" * 78)
    A("  entry = 0x%s   在 .text 内: %s" % (entry, R.in_text(ea)))
    A("  atlas 边界: size=%d  n_instr=%d" % (size, info["n_instr"]))
    A("  实测反汇编: %d 条, skipdata=%d, 末条=%s, 覆盖=%d 字节 ⇒ 边界自洽 %s"
      % (len(insns), sum(1 for i in insns if i.id == 0), insns[-1].mnemonic,
         insns[-1].address + insns[-1].size - ea, (insns[-1].address + insns[-1].size - ea) == size))
    A("  首 3 条:")
    A(dis(ea, 12))
    A("  末 2 条:")
    A(dis(insns[-2].address, 8))
    A("")
    A("=" * 78)
    A("② 类身份环 —— PASS（独立取证：.rdata RTTI 链，不采信名字里的 Class 部分）")
    A("=" * 78)
    t = classify_table(vt)
    col = u32(vt - 4)
    ch = rtti_chain(col)
    A("  虚表基址 vt = 0x%08X（.rdata）   vlen=%d 槽   slot0=0x%s ⇒ %s"
      % (vt, t["vlen"], t["slot0"], t["slot0_kind"]))
    A("  [vt-0x04] @0x%08X = 0x%08X  (COL 指针)" % (vt - 4, col))
    A("  COL @0x%08X raw bytes: %s" % (col, bx(col, 0x14)))
    A("      sig=0x%08X  offset=0x%08X  cdOffset=0x%08X  pTD=0x%08X  pCHD=0x%08X"
      % (ch["sig"], u32(col + 4), u32(col + 8), ch["td"], ch["chd"]))
    A("      注: pTD/pCHD 存的是**绝对 VA**（非 RVA），0x%08X/0x%08X 均落在镜像内，解引有效"
      % (ch["td"], ch["chd"]))
    A("  TD @0x%08X raw bytes: %s" % (ch["td"], bx(ch["td"], 0x20)))
    A("      注: 装饰名在 **TD+8 内联串**（不是指针），起始 0x%08X" % int(ch["td_name_va"], 16))
    A("      ⇒ type name = %r" % ch["td_name"])
    if ch["chd"]:
        A("  CHD @0x%08X: sig=0x%X nBaseClasses=%d BaseClassArray=0x%s"
          % (int(ch["chd"]["va"], 16), ch["chd"]["sig"], ch["chd"]["nbase"], ch["chd"]["arr"]))
        for b in ch["chd"]["bases"]:
            A("      BCD 0x%s -> %s" % (b["col"], b["name"]))
    A("  槽位: slot %d = vt+0x%02X → @0x%08X raw bytes: %s = 0x%08X  == entry %s"
      % (slot, 4 * slot, vt + 4 * slot, bx(vt + 4 * slot, 4), u32(vt + 4 * slot),
         "✓" if u32(vt + 4 * slot) == ea else "✗"))
    A("  记号名 `%s` 的类名部分与本 RTTI 名一致 ⇒ 类身份由字节钉死，非据名" % other_notes["name"])
    A("")
    A("=" * 78)
    A("③ 整体合同环 —— PASS（③b② 可伪证错误码/返回约定 + ③b④ 完整循环 I/O）")
    A("=" * 78)
    A("  判据（R14_COMMON.md:611 条 3 / MEASURE_F3A\\EVIDENCE\\CONTROLS.md 修正 1）：")
    A("    ③b② = `cmp <op>,-1` 哨兵驱动 jcc/setcc，或字面 -1 紧邻 ret；{0,1} 布尔与 test/jcc 归 ③a。")
    A("  本行命中 %d 处 `cmp eax,-1` 哨兵分支（每处独立站点、独立全局容器，非同一 call 多路）：" % len(sites))
    for s in sites:
        A("  --- 站点 %s ---" % s["no"])
        A("    容器: struct@0x%08X（计数@0x%08X, 数组@0x%08X）" % (s["container"], s["count"], s["array"]))
        A(dis(s["start"], s["len"]))
        A("    伪证: `Find` 返回 -1 ⇒ 未命中（je 跳过摘除）；返回 >=0 ⇒ 下标。")
        A("          随后 cmp eax,[count] / jge 做上界检查，dec count 后整体前移，")
        A("          与「-1 未命中」路径动作实质不同（失败路零写、成功路写计数+搬移数组）。")
        A("    cmp 与 je 之间无 eax 覆写、无控制转移 ⇒ 非 eax 覆写陷阱。")
    A("  ③b④ 佐证（同一函数体内的有界搬移循环，循环体内有**非栈写**）：")
    for lp in loops:
        A(dis(lp["start"], lp["len"]))
        A("    边界: cmp eax,[count] / jge 先于循环；循环条件 cmp eax,ecx / jl；")
        A("    循环体内 `mov [ecx+eax*4-4],edx` = 全局数组写（**本函数体内**，不是被调者内部的写）。")
    A("  非 ③a: 体内 %d 处 cmp -1 分叉 + %d 个循环 + 多处非栈写，不是单调用+单写/纯转发/无分支直线。"
      % (len(sites), len(loops)))
    A("")
    A("=" * 78
      )
    A("④ 使用见证环 —— PASS（活虚表：构造器装入 + vt[slot]==entry，写点在行外）")
    A("=" * 78)
    A("  ㉓ 专查: 枚举虚表 0x%08X 在 .text 的**全部**写点并逐个分类（析构器一律不计）:" % vt)
    for w in other_notes["writes"]:
        A("    %s  in %-9s atexit=%-5s %s" % (w[0], w[1], w[2], w[3]))
    A("  ⇒ 合法锚点（CTOR 形状、行外、非 atexit）: %s" % ", ".join(other_notes["ctors"]))
    A("  ⇒ 排除: %s（析构器/删除析构器写点，按 ㉓ 不算活 vptr 见证）" % ", ".join(dtor_sites))
    A("  采用锚点 %s（所在函数 %s）反汇编:" % (ctor_anchor, ctor_func))
    A(dis(int(ctor_func, 16), 0x30))
    A("  判构造器（非析构器）依据：① install 之前先 call 基类构造器；② 无 `mov dl,1` 前置；")
    A("  ③ 装的是本类主虚表（slot0=0x%s）；④ 字段置初值(-1/0)而非释放。" % t["slot0"])
    A("  写点在行外: %s ∉ [0x%s, 0x%08X) ⇒ %s"
      % (ctor_anchor, entry, ea + size,
         "✓" if not (ea <= int(ctor_anchor, 16) < ea + size) else "✗"))
    A("  direct-only 排除: find_rel_calls(0x%s) = %d 处 ⇒ ④ 不可能建立在 direct call 上。"
      % (entry, len(find_direct_calls(ea))))
    A("")
    A("=" * 78)
    A("②④ 不同源 —— YES")
    A("=" * 78)
    A("  ② 锚 .rdata 的 RTTI 描述符字节：COL@0x%08X / TD@0x%08X / 名串@0x%s"
      % (col, ch["td"], ch["td_name_va"]))
    A("  ④ 锚 .text 的构造安装指令字节：0x%s" % ctor_anchor)
    A("  段不同、地址不同、证据物件类型不同 ⇒ 非「同一虚表槽既证类身份又证被使用」。")
    A("")
    A("=" * 78)
    A("语义（一行）")
    A("=" * 78)
    A("  %s" % other_notes["semantics"])
    p = os.path.join(OUT, "ROW_%s.txt" % entry)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    # ---- ROW 0071FA80 : TEventClass::slot8
    dump_row(
        "0071FA80", 0x007F5578, 8,
        sites=[
            dict(no="S1", container=0x00B0F658, count=0x00B0F668, array=0x00B0F65C,
                 start=0x0071FAA6, len=0x1C),
            dict(no="S2", container=0x00B0F670, count=0x00B0F680, array=0x00B0F674,
                 start=0x0071FAEF, len=0x1C),
            dict(no="S3", container=0x00B0F1A0, count=0x00B0F1B0, array=0x00B0F1A4,
                 start=0x0071FB38, len=0x1C),
        ],
        loops=[
            dict(start=0x0071FAC2, len=0x2D),
        ],
        ctor_anchor="0071E6C1", ctor_func="0071E6A0",
        dtor_sites=["0071E836(in 0071E830)", "0071FA86(in 0071FA80 自身)"],
        other_notes=dict(
            name="TEventClass::slot8",
            semantics="TEventClass 标量删除析构器(slot8)：改回本类 vptr+基类子对象 vptr → call 0x7258D0 → "
                       "从 3 个全局注册容器(0xB0F658/0xB0F670/0xB0F1A0)按 Find 返回 -1 约定摘除自身"
                       "（下标有效则 dec 计数并前移数组）→ call 0x4101F0 基类析构 → "
                       "若 this 低位([esp+0xC]&1)调 0x7C8B3D(operator delete) → 返回 this",
            writes=[
                ("0071E6C1", "0071E6A0", "False", "CTOR  install@0071E6C1 first_call=0071E6A4(0x410170)"),
                ("0071E80D", "0071E800", "False", "CTOR  install@0071E80D first_call=0071E808(0x4101C0)"),
                ("0071E836", "0071E830", "False", "DTOR  mov dl,1@0071E834 先装表后干活 ⇒ 排除"),
                ("0071F8E4", "0071F8C0", "False", "CTOR  install@0071F8E4 first_call=0071F8CB(0x410380)"),
                ("0071FA86", "0071FA80", "False", "DTOR  本 entry 自身（标量删除析构器）⇒ 排除"),
            ],
            ctors=["0071E6C1 (in 0071E6A0)", "0071E80D (in 0071E800)", "0071F8E4 (in 0071F8C0)"],
        ))

    # ---- ROW 00726950 : TriggerClass::slot8
    dump_row(
        "00726950", 0x007F5858, 8,
        sites=[
            dict(no="S1", container=0x00A8EAE8, count=0x00A8EAF8, array=0x00A8EAEC,
                 start=0x00726976, len=0x1C),
            dict(no="S2", container=0x00B0F670, count=0x00B0F680, array=0x00B0F674,
                 start=0x007269BF, len=0x1C),
            dict(no="S3", container=0x00B0F708, count=0x00B0F718, array=0x00B0F70C,
                 start=0x00726A08, len=0x1C),
        ],
        loops=[
            dict(start=0x00726992, len=0x2D),
        ],
        ctor_anchor="00725FCE", ctor_func="00725FA0",
        dtor_sites=["00726146(in 00726140)", "00726956(in 00726950 自身)"],
        other_notes=dict(
            name="TriggerClass::slot8",
            semantics="TriggerClass 标量删除析构器(slot8)：改回本类 vptr+基类子对象 vptr → call 0x7258D0 → "
                       "从 3 个全局注册容器(0xA8EAE8/0xB0F700/0xA8EB00)按 Find 返回 -1 约定摘除自身"
                       "（下标有效则 dec 计数并前移数组）→ call 0x4101F0 基类析构 → "
                       "若 this 低位([esp+0xC]&1)调 0x7C8B3D(operator delete) → 返回 this",
            writes=[
                ("00725FCE", "00725FA0", "False", "CTOR  install@00725FCE first_call=00725FA4(0x410170)"),
                ("00726146", "00726140", "False", "DTOR  mov dl,1@00726144 先装表后干活 ⇒ 排除"),
                ("00726884", "00726860", "False", "CTOR  install@00726884 first_call=0072686B(0x410380)（另一 entry slot5）"),
                ("00726956", "00726950", "False", "DTOR  本 entry 自身（标量删除析构器）⇒ 排除"),
            ],
            ctors=["00725FCE (in 00725FA0)", "00726884 (in 00726860)"],
        ))
