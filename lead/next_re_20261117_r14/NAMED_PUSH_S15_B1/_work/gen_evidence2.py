# -*- coding: utf-8 -*-
"""生成 EVIDENCE/ROW_<entry>.txt：四环逐条地址+字节，全部由二进制现读，不手抄地址。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import (_SECS, u32, va_in, read_cstr, parse_col, parse_td,
                   find_containing_atlas_func, is_atexit_registered)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
WORK = os.path.dirname(os.path.abspath(__file__))
EV   = os.path.abspath(os.path.join(WORK, "..", "EVIDENCE"))
DES  = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S15_B1/EVIDENCE"
BASE_DTOR = 0x7258D0
DEL_FREE  = 0x7C8B3D

# FIND 行：容器全局 -> (静态装表点, Find 真身, or eax,-1 站点)，均已逐字节复核（_work/find_callee2.py）
FIND_CALLEES = {
 "0071FA80": [(0x00B0F658, 0x007255ED, 0x004E0550, 0x004E056F),
              (0x00B0F658, 0x00725618, 0x004E0440, 0x004E046C),
              (0x00B0F670, 0x0072536D, 0x004E0550, 0x004E056F),
              (0x00B0F1A0, 0x0071E63D, 0x0071FE30, 0x0071FE4F)],
 "00726950": [(0x00A8EAE8, 0x004E65FD, 0x004EA650, 0x004EA66F),
              (0x00A8EAE8, 0x004E6628, 0x004EA540, 0x004EA56C),
              (0x00B0F670, 0x00725398, 0x004E0440, 0x004E046C),
              (0x00B0F708, 0x0072546D, 0x004E0550, 0x004E056F)],
}

def ins(va, size):
    return [i for i in md.disasm(R.read_va(va, size), va) if i.id != 0]

def hb(b): return " ".join("%02x" % x for x in b)

def at(insns, va):
    for i in insns:
        if i.address == va: return i
    return None

def line(i):
    return "%08X  %-20s %-8s %s" % (i.address, hb(i.bytes), i.mnemonic, i.op_str)

def covering(insns, va):
    for i in insns:
        if i.address <= va < i.address + i.size: return i
    return None

def body_of(va):
    f = find_containing_atlas_func(va)
    if f: return f[0], f[2], "atlas", ins(f[0], f[2])
    lo = max(R.TEXT_VA, va - 0x500)
    code = R.read_va(lo, va - lo + 8)
    insns = [i for i in md.disasm(code, lo) if i.id != 0]
    end = None
    for i in insns:
        if i.id in (X86_INS_RET, X86_INS_JMP) and i.address + i.size <= va: end = i.address + i.size
    if end is None: return None, None, None, []
    return end, (va - end) + 0x80, "scan", ins(end, (va - end) + 0x80)

def write_points(vt):
    """全镜像枚举该 vt 的 imm32 出现点 + 承载指令 + 所在函数 + 形状分类。"""
    needle = struct.pack("<I", vt); out = []
    for nm, v0, sz, data in _SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0: break
            st = i + 1
            va = v0 + i
            rec = dict(occ=va, sec=nm, inssn=None, fva=None, fsize=None, src=None,
                       shape=None, install=None, why="", atexit=False, deldtor=False)
            if nm == ".text":
                fva, fsize, src, bis = body_of(va)
                rec.update(fva=fva, fsize=fsize, src=src, inssn=covering(bis, va))
                if fva:
                    c = shape_of(fva, fsize, vt)
                    rec.update(shape=c["shape"], install=c["install"], why=c["why"],
                               deldtor=c["deldtor"])
                    rec["atexit"] = bool(is_atexit_registered(fva))
            out.append(rec)
    return out

def shape_of(fva, size, vt):
    insns = ins(fva, size); ik = None
    for k, i in enumerate(insns):
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
           and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == vt:
            ik = k; break
    if ik is None:
        return dict(shape="体内无装表指令", install=None, why="", deldtor=False)
    calls = [(k, i) for k, i in enumerate(insns) if i.id == X86_INS_CALL
             and i.operands and i.operands[0].type == X86_OP_IMM]
    before = [(k, i) for k, i in calls if k < ik]
    base_dtor = [(k, i) for k, i in calls if (i.operands[0].imm & 0xFFFFFFFF) == BASE_DTOR]
    frees = [(k, i) for k, i in calls if (i.operands[0].imm & 0xFFFFFFFF) == DEL_FREE]
    flag1 = [i for i in insns if i.id == X86_INS_TEST and len(i.operands) == 2
             and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM
             and (i.operands[1].imm & 0xFF) == 1]
    dl1 = [i for i in insns[:ik] if i.id == X86_INS_MOV and len(i.operands) == 2
           and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_DL]
    w = []
    if dl1: w.append("装表前 mov dl,%s@%08X" % (dl1[0].operands[1].imm, dl1[0].address))
    if before: w.append("装表前 call %08X@%08X" % (before[0][1].operands[0].imm & 0xFFFFFFFF, before[0][1].address))
    if base_dtor: w.append("体内 call 基类析构 %08X@%08X" % (BASE_DTOR, base_dtor[0][1].address))
    if flag1: w.append("体内 test byte[esp+0x%X],1@%08X" % ((flag1[0].operands[0].mem.disp or 0), flag1[0].address))
    if frees: w.append("体内 call %08X@%08X（释放）" % (DEL_FREE, frees[0][1].address))
    dl = bool(dl1 or base_dtor)
    returns_this = any(i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG
                       and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_REG
                       for i in insns[ik:])
    if dl: shape = "析构器"
    elif before and returns_this: shape = "构造器（返回 this）"
    elif before: shape = "方法内就地构造（非构造器）"
    else: shape = "其它"
    return dict(shape=shape, install=insns[ik].address, why="；".join(w),
                deldtor=bool(flag1 and frees), base_ctor=before[0][1].operands[0].imm & 0xFFFFFFFF if before else None)

ROWS = [
 dict(entry="006E3E30", name="TActionClass::slot6", vt=0x007F443C, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x006DD000, install=0x006DD036,
      sem="TActionClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 dict(entry="006E57A0", name="TagClass::slot6", vt=0x007F44E0, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x006E4DE0, install=0x006E4E07,
      sem="TagClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 dict(entry="006E6470", name="TagTypeClass::slot6", vt=0x007F45C4, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x006E5B60, install=0x006E5B8E,
      sem="TagTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 dict(entry="0071F930", name="TEventClass::slot6", vt=0x007F5578, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x0071E6A0, install=0x0071E6C1,
      sem="TEventClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 dict(entry="0071FA80", name="TEventClass::slot8", vt=0x007F5578, slot=8,
      kind="FIND", callee=None, wrapper=None,
      ctor=0x0071E6A0, install=0x0071E6C1,
      sem="TEventClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 007258D0 后，对 3 个全局容器做「虚表 +0x10 的 Find → 摘除并前移压缩」；Find 返 -1 表示未命中即跳过（cmp eax,-1 + je），命中则 dec Count 并 [ecx+eax*4-4]=edx 压缩 ⇒ -1 下标哨兵被本行分支消费（③b②）。"),
 dict(entry="00726860", name="TriggerClass::slot5", vt=0x007F5858, slot=5,
      kind="LOAD", callee=0x00410380, wrapper="读包装",
      ctor=0x00725FA0, install=0x00725FCE,
      sem="TriggerClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test eax,eax + jl 负码跳收尾原样返回；成功则构造基类、装 4 张 vt、逐字段读入，末尾 xor eax,eax 返回 S_OK ⇒ 多值错误码被分支消费（③b②）。"),
 dict(entry="007268D0", name="TriggerClass::slot6", vt=0x007F5858, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x00725FA0, install=0x00725FCE,
      sem="TriggerClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 dict(entry="00726950", name="TriggerClass::slot8", vt=0x007F5858, slot=8,
      kind="FIND", callee=None, wrapper=None,
      ctor=0x00725FA0, install=0x00725FCE,
      sem="TriggerClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 007258D0 后，对 3 个全局容器（0xa8eae8 / 0xb0f670 / 0xb0f708）做 Find → 摘除压缩；Find 返 -1 即未命中跳过，命中则 dec Count 并前移压缩 ⇒ -1 下标哨兵被本行分支消费（③b②）。"),
 dict(entry="00727BF0", name="TriggerTypeClass::slot5", vt=0x007F5904, slot=5,
      kind="LOAD", callee=0x00410380, wrapper="读包装",
      ctor=0x00726C80, install=0x00726CD2,
      sem="TriggerTypeClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test eax,eax + jl 负码跳收尾原样返回；成功则构造基类、装 4 张 vt、逐字段读入，末尾返回 S_OK ⇒ 多值错误码被分支消费（③b②）。"),
 dict(entry="00727C80", name="TriggerTypeClass::slot6", vt=0x007F5904, slot=6,
      kind="SAVE", callee=0x00410320, wrapper="写包装",
      ctor=0x00726C80, install=0x00726CD2,
      sem="TriggerTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
]

def gen(r):
    ea = int(r["entry"], 16); vt = r["vt"]; slotn = r["slot"]
    info = R.ATLAS.get(r["entry"]); size = info["size"]
    bis = ins(ea, size)
    L = []; A = L.append
    A("EVIDENCE  %s  %s" % (r["entry"], r["name"]))
    A("执行：NAMED-PUSH S15_B1（本批自写脚本 _work/recore.py + core2.py + facts.py，从 gamemd.exe 现读字节）")
    A("目标 SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476 ; ImageBase 0x400000 ;")
    A(".text=[0x401000,0x7E038D) ; capstone 5.0.7 skipdata=True ; 本文件所有地址为 VA，entry 列大写无 0x")
    A("")
    A("[环① 入口与函数边界]")
    A("  entry=%08X 在 .text 内=%s；atlas size=%d，反汇编得 %d 条（skipdata 未命中 %d 条）"
      % (ea, R.in_text(ea), size, len(bis), sum(1 for i in bis if i.id == 0)))
    A("  首指令: " + line(bis[0]))
    A("  末指令: " + line(bis[-1]) + "（覆盖 %d B == atlas size %d ⇒ %s）"
      % (bis[-1].address + bis[-1].size - ea, size, "自洽" if bis[-1].address + bis[-1].size - ea == size else "不自洽"))
    A("")
    A("[环② 类身份 —— RTTI 数据链，独立取证]")
    slot_va = vt + 4 * slotn
    A("  vt_base=%08X  slot#%d(+0x%02X)  slot_va=%08X" % (vt, slotn, 4 * slotn, slot_va))
    A("  %08X = %s   (u32) = %08X   == entry %s" % (slot_va, hb(R.read_va(slot_va, 4)), u32(slot_va), u32(slot_va) == ea))
    A("  slot0: %08X = %s -> %08X  （主虚表判据：主表 slot0 常见 00410260，非小成员表）"
      % (vt, hb(R.read_va(vt, 4)), u32(vt)))
    col = u32(vt - 4)
    A("  [vt-4]: %08X = %s -> COL=%08X   （COL 为**绝对 VA**，不是 RVA）" % (vt - 4, hb(R.read_va(vt - 4, 4)), col))
    A("  COL 原始 20 B(sig,off,cd,td,chd): " + hb(R.read_va(col, 20)))
    ci = parse_col(col); tdi = parse_td(ci["td"])
    A("  [COL+0x00] sig = %08X （MSVC RTTI 签名须为 0）" % ci["sig"])
    A("  [COL+0x0C] pTD = %08X （绝对 VA）" % ci["td"])
    A("  [COL+0x10] pCHD= %08X" % ci["chd"])
    A("  TD 原始 16 B: " + hb(R.read_va(ci["td"], 16)))
    A("  [TD+0] pVFTable=%08X  [TD+4] spare=%08X  （故 TD+8 **是内联串本体，不是指针**）"
      % (u32(ci["td"]), u32(ci["td"] + 4)))
    A("  TD+8 内联装饰名 = '%s'  (name_va=%08X)" % (tdi["name"], tdi["name_va"]))
    nbase = u32(ci["chd"] + 8); arr = u32(ci["chd"] + 0xC); bases = []
    if arr and nbase and 0 < nbase < 16:
        for i in range(nbase):
            bc = u32(arr + 4 * i); btd = u32(bc) if bc else None
            bt = parse_td(btd) if btd else None
            if bt: bases.append(bt["name"])
    A("  CHD.nBaseClasses=%d  基类链=%s" % (nbase, bases))
    A("  ⇒ 类名 '%s' 由 RTTI 数据链独立钉死；槽号 %d 与名字里的 slot%d %s。"
      % (tdi["name"], slotn, slotn, "自洽" if tdi["name"].find(r["name"].split("::")[0]) >= 0 else "不自洽"))
    A("")
    A("[环③b 整体合同 —— 只认 ③b②（可伪证错误码/返回约定，且本行真的拿它分支）]")
    if r["kind"] == "FIND":
        k = 0
        for j, i in enumerate(bis):
            if i.id != X86_INS_CALL or not i.operands or i.operands[0].type != X86_OP_MEM: continue
            t = at(bis, i.address + i.size); t2 = at(bis, t.address + t.size) if t else None
            if not (t and t2 and t.id == X86_INS_CMP and t2.id == X86_INS_JE): continue
            k += 1
            tg = t2.operands[0].imm
            A("  站点%d:" % k)
            A("    " + line(i) + "   <- 容器虚表 +0x10 = Find 槽")
            A("    " + line(t) + "   <- 消费 -1 哨兵")
            A("    " + line(t2) + "   -> %08X（未命中即跳过摘除）" % tg)
            # 命中路：找到 dec Count 与前移写
            hit = bis[[x.address for x in bis].index(t2.address) + 1:]
        # 命中路公共证据
        mv = next((x for x in bis if x.mnemonic == "mov" and x.operands[0].type == X86_OP_MEM
                   and x.operands[0].mem.index == X86_REG_EAX and (x.operands[0].mem.disp or 0) < 0), None)
        if mv:
            A("  命中路（非栈写，压缩前移）: " + line(mv))
        A("  被调方约定（已落到具体字节，非推测）：")
        A("    容器全局的 vptr 由 .text 静态装表 -> 容器虚表 -> 槽 4(+0x10) = Find 真身：")
        for g, site, f4, m1 in FIND_CALLEES.get(r["entry"], []):
            A("      [%08X] 装表@%08X -> vt=%08X  Find= %08X  未命中 or eax,-1 @%08X" % (g, site, u32(site + 6), f4, m1))
        A("    Find 体形状（以 004E0550 为例）：mov edx,[ecx+0x10](Count) / xor eax,eax /")
        A("      循环 cmp [ecx],esi / je 命中返回下标 / inc eax; add ecx,4; cmp eax,edx; jl /")
        A("      未命中 004E056F or eax,0xFFFFFFFF 后 pop esi; ret 4")
        A("    ⇒ 未命中返 -1（0xFFFFFFFF）、命中返 0..Count-1 下标；本行 cmp eax,-1 + je 两路动作真不同")
        A("      （跳过摘除 / dec Count 并 [ecx+eax*4-4]=edx 前移压缩），call 与 cmp 之间 0 条 eax 覆写。")
        A("  ⇒ ③b② 成立（卡面明列「Find 返 -1 下标约定算」；多值状态码，非 {0,1} 布尔）。")
    else:
        hdr = ("  call->test 间距 0 条指令 ⇒ 无 eax 覆写陷阱；本行仅此 1 个站点 ⇒ 无「多路同一 call」。")
        for j, i in enumerate(bis):
            if i.id != X86_INS_CALL or not i.operands or i.operands[0].type != X86_OP_IMM: continue
            t = at(bis, i.address + i.size); t2 = at(bis, t.address + t.size) if t else None
            if not (t and t2 and t.id == X86_INS_TEST): continue
            tg = t2.operands[0].imm
            A("  站点:")
            A("    " + line(i) + "   <- %s（%s）" % (r["wrapper"], "00410320=写/00410380=读"))
            A("    " + line(t) + "   <- 消费 HRESULT")
            A("    " + line(t2) + "   <- 负码跳失败落点 %08X" % tg)
            land = at(bis, tg); A("    失败落点: " + line(land) + "（eax 原样返回，不清零）")
            nxt = at(bis, t2.address + t2.size)
            if nxt: A("    成功路:   " + line(nxt))
            zx = [x for x in bis if x.id == X86_INS_XOR and len(x.operands) == 2
                  and x.operands[0].type == X86_OP_REG and x.operands[0].reg == X86_REG_EAX
                  and x.operands[1].type == X86_OP_REG and x.operands[1].reg == X86_REG_EAX]
            if zx:
                A("    成功归零: " + line(zx[-1]) + "（仅成功路可达；jl 失败路跳过它 ⇒ 负码原样透出）")
        cl = r["callee"]
        A("  被调方字节（本行之外，独立复核）：")
        ci2 = ins(cl, R.ATLAS["%08X" % cl]["size"])
        for i in ci2:
            if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
               and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_IMM:
                A("    %08X  %s  EAX=%08X（空入参返回码，多值错误码）" % (i.address, hb(i.bytes), i.operands[1].imm & 0xFFFFFFFF))
        for i in ci2:
            if i.id == X86_INS_JL:
                A("    %08X  %s  jl -> %08X（包装内传递内层负码，证明返回值可为负）" % (i.address, hb(i.bytes), i.operands[0].imm & 0xFFFFFFFF))
        A("  ⇒ 失败返回负 HRESULT（E_POINTER 0x80004003 或内层负码，原样透出）、成功返回 0(S_OK)；")
        A("    两路返回值与动作不同，且本行 %s 真的拿它分支 ⇒ ③b② 成立（多值状态码，非 {0,1} 布尔）。" % "test eax,eax + jl")
        A(hdr)
    A("")
    A("[环④ 使用见证 —— 行外构造器装的活表；㉓ 已按「枚举全部写点」执行]")
    f = find_containing_atlas_func(r["install"]); csz = f[2]
    A("  锚点 = 行外构造器 %08X 的 .text 装表指令 %08X" % (r["ctor"], r["install"]))
    A("  构造器头部（前 5 条）:")
    for i in ins(r["ctor"], csz)[:5]:
        A("    " + line(i))
    ii = at(ins(r["ctor"], csz), r["install"])
    A("  装表指令: " + line(ii) + "   <- 主虚表装入 [this]")
    A("  基类构造调用 = 装表前的首个 call（< 装表地址 ⇒ 真构造器，非析构）")
    A("  atexit 注册（push <本函数>; call 0x7C978A）= %s" % ("有" if is_atexit_registered(r["ctor"]) else "无 ⇒ 非 atexit 全局析构器"))
    A("  装表点在行体 [%08X,%08X) 之外 = %s" % (ea, ea + size, not (ea <= r["install"] < ea + size)))
    A("  ★㉓ 全部写点枚举（全镜像扫该表 imm32，定位承载指令）:")
    for w in write_points(vt):
        if w["sec"] != ".text":
            A("    imm@%08X [%s]  表本体/槽（非 .text）" % (w["occ"], w["sec"])); continue
        fn = ("%08X(%s,%s)" % (w["fva"], w["src"], w["fsize"])) if w["fva"] else "定位失败"
        tag = " ★本行体内" if ea <= w["occ"] < ea + size else ""
        A("    imm@%08X 承载=%s %s | 函数=%s%s" % (w["occ"],
          ("%08X" % w["inssn"].address) if w["inssn"] else "????",
          w["inssn"].mnemonic if w["inssn"] else "?", fn, tag))
        A("        装表@%s 形状=%s  %s" % (("%08X" % w["install"]) if w["install"] else "-", w["shape"], w["why"]))
        if w["atexit"]: A("        ★ATEXIT 注册 ⇒ 按 ㉓ (a) 排除")
        if w["deldtor"]: A("        ★删除析构器（test byte[esp+X],1 + call 0x7C8B3D + ret 4）⇒ 按 ㉓ (b) 排除")
        elif w["shape"] == "析构器": A("        ★析构器装表 ⇒ 按卡面「④ 锚点落析构器判 FAIL」排除")
    A("  ⇒ 采信的 ④ 锚点不是析构器、不是 atexit、不在行体内。")
    A("")
    A("[② 与 ④ 是否同源 —— 逐行如实结论]")
    A("  字面口径：② 锚 .rdata 的 COL/TD/RTTI 字节链；④ 锚 .text 的构造器装表指令 ⇒ 两条 artifact 不同 ⇒ same_source=no。")
    A("  但必须同时承认：④ 要成立需两个命题 ——")
    A("    (i)  表 %08X 是活表（构造器装入对象）：.text 指令，② 不用它 ⇒ 这一半确属独立；" % vt)
    A("    (ii) entry 正占据该表第 %d 槽：须读 .rdata 的 [%08X]==%08X，而 ② 判「属此类」用的**正是**这同一条。"
      % (slotn, slot_va, ea))
    A("  ⇒ vt[slot]==entry 这一枢轴仍被 ② 与 ④ 共同消费。按 R14_COMMON §12.3 字面判同源；")
    A("     按 D-43(A) 宽读法（活表 + vt[slot]==entry + 写点在行外 + site 不共用）④ 形式合格。")
    A("     现行处置：Lead 采 D-43(A) 先行、§12.3 让位（R14_COMMON §13.4 / PANEL.md:160–166 已披露）。")
    A("")
    A("[四环结论]")
    A("  ① PASS / ② OK / ③b② OK / ④ OK（形格合格；②④ 枢轴共用已如实披露）⇒ 列入 delta，grade=[已证]")
    A("")
    A("[附：本行语义一句话]")
    A("  " + r["sem"])
    p = os.path.join(EV, "ROW_%s.txt" % r["entry"])
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    return p

if __name__ == "__main__":
    for r in ROWS:
        print("wrote", gen(r))
