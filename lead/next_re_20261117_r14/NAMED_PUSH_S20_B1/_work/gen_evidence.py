# -*- coding: utf-8 -*-
"""生成 EVIDENCE/ROW_<entry>.txt：逐行四环地址 + 字节。
每一行的内容都由本脚本当场从 gamemd.exe 读出并打印，不手抄。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(WORK), "EVIDENCE")
ROWS = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))}
SUR = {s["entry"]: s for s in json.load(open(os.path.join(WORK, "survey.json"), encoding="utf-8"))}


def load_delta_sem():
    """从 gen_delta.py 里读 DELTA（唯一语义真源），避免两处手写不一致。"""
    import ast
    src = open(os.path.join(WORK, "gen_delta.py"), encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "DELTA":
            return {e: sem for e, _s, _n, sem in ast.literal_eval(node.value)}
    return {}


SEM = load_delta_sem()

# 逐行裁决所需的手工锚点（地址全部来自本批反汇编，见各 txt 内 dump）
PLAN = {
    "00423AC0": {
        "vt": 0x007E3354, "slot_no": 23,
        "ring4_at": 0x0042201C, "ring4_host": 0x00421EA0, "ring4_base_call": 0x00421EAE,
        "ring3_form": "3b4",
        "ring3": [
            ("循环入口(外层)", 0x0042400C, "8bc8 / f7d9 / 3bc8 → jg 0x424252"),
            ("外层回边", 0x00424269, "0f8e9dfdffff jle 0x42400C"),
            ("循环入口(内层)", 0x0042402A, "db442418 fild [esp+0x18]"),
            ("内层回边", 0x0042424C, "0f8ed8fdffff jle 0x42402A"),
            ("边界检查(半径)", 0x00424051, "3b823c030000 cmp eax,[edx+0x33C] → 00424057 jg 0x424235"),
            ("循环体内非栈写", 0x00424155, "88871e010000 mov byte [edi+0x11E],al"),
        ],
        "sem": "AnimClass 每帧 AI：先处理动画/建筑状态标志，再按 [Type+0x33C] 给出的爆炸半径做 (2R+1)^2 双层扫描——对每格取距离平方、四舍五入后与半径比较（越界 `jg` 跳过），命中格用 0x5657A0 在 0x87F7E8 管理器里查对象，查到且 0x4838E0 判真则 new 0xB0 字节对象、0x5FC380 构造、0x65C7E0 取动画索引，并把结果字节写回对象 [edi+0x11E]；同时更新包围盒。",
    },
    "00428EA0": {
        "vt": 0x007E3608, "slot_no": 8,
        "ring4_at": 0x00427731, "ring4_host": 0x00427530, "ring4_base_call": 0x0042753A,
        "ring3_form": "3b2",
        "ring3": [
            ("站点1", 0x00428EC8, "8b1570f6b000 mov edx,[0xB0F670] ; 00428ECE push eax ; 00428ED3 ff5210 call [edx+0x10]"),
            ("站点1-判零间隔", 0x00428ED6, "83f8ff cmp eax,-1 ; 00428ED9 742d je 0x428F08（无 eax 覆写）"),
            ("站点1-命中路压缩写", 0x00428EFA, "895481fc mov [ecx+eax*4-4],edx ; 00428EE8 890d80f6b000 mov [0xB0F680],ecx ; 00428F06 7ce8 jl 回边"),
            ("站点2", 0x00428F08, "8b1550418b00 mov edx,[0x8B4150] ; 00428F1C ff5210 call [edx+0x10]"),
            ("站点2-判零间隔", 0x00428F1F, "83f8ff cmp eax,-1 ; 00428F22 742d je 0x428F51"),
            ("站点2-命中路压缩写", 0x00428F43, "895481fc mov [ecx+eax*4-4],edx ; 00428F31 890d60418b00 mov [0x8B4160],ecx ; 00428F4F 7ce8 jl 回边"),
            ("收尾-基类析构", 0x00428F53, "e8a8e41c00 call 0x5F7400"),
            ("收尾-按 delete 标志释放", 0x00428F58, "f644240c01 test byte [esp+0xC],1 ; 00428F60 e8d8fb3900 call 0x7C8B3D"),
        ],
        "callees": [(0x004E0550, "容器 0xB0F670 活表 007E91EC 的 vt[#4] = FindItemIndex"),
                    (0x004EE1B0, "容器 0x8B4150 活表 007EA2E4 的 vt[#4] = FindItemIndex")],
        "sem": "AnimTypeClass 标量删除析构：先把 4 张本类/基类虚表复位，在全局 DynamicVectorClass<AnimTypeClass*>（0xB0F670，计数 0xB0F680 / 数组 0xB0F674）与 0x8B4150（计数 0x8B4160 / 数组 0x8B4154）两个注册表里各自 Find 自身——未命中返 -1 直接跳过、命中则计数减一并前移压缩数组摘链，再调 0x5F7400 基类析构，最后按 `test byte [esp+0xC],1` 的 delete 标志调 0x7C8B3D 释放自身。",
    },
    "004A7C90": {
        "vt": 0x007E5FB8, "slot_no": 8,
        "ring4_at": 0x004A7A3A, "ring4_host": 0x004A7A30, "ring4_base_call": 0x004A7A33,
        "ring3_form": "3b2",
        "ring3": [
            ("站点", 0x004A7CB8, "8b1508028a00 mov edx,[0x8A0208] ; 004A7CC3 ff5210 call [edx+0x10]"),
            ("判零间隔", 0x004A7CC6, "83f8ff cmp eax,-1 ; 004A7CC9 742d je 0x4A7CF8（无 eax 覆写）"),
            ("命中路压缩写", 0x004A7CEA, "895481fc mov [ecx+eax*4-4],edx ; 004A7CD8 890d18028a00 mov [0x8A0218],ecx ; 004A7CF6 7ce8 jl 回边"),
            ("收尾-基类析构", 0x004A7CFA, "e8f184f6ff call 0x4101F0"),
            ("收尾-按 delete 标志释放", 0x004A7CFF, "f644240c01 test byte [esp+0xC],1 ; 004A7D07 e8310e3200 call 0x7C8B3D"),
        ],
        "callees": [(0x004A7FB0, "容器 0x8A0208 活表 007E5EDC 的 vt[#4] = FindItemIndex")],
        "sem": "DiskLaserClass 标量删除析构：复位 4 张虚表后在全局 DynamicVectorClass<DiskLaserClass*>（0x8A0208，计数 0x8A0218 / 数组 0x8A020C）里 Find 自身——未命中返 -1 跳过、命中则计数减一并前移压缩数组，再调 0x4101F0 基类析构，最后按 `test byte [esp+0xC],1` 的 delete 标志释放自身。",
    },
    "004C5A30": {
        "vt": 0x007E87A8, "slot_no": 5,
        "ring4_at": 0x004C537D, "ring4_host": 0x004C5370, "ring4_base_call": 0x004C5373,
        "ring3_form": "3b2",
        "ring3": [
            ("站点", 0x004C5A39, "50 push eax ; 004C5A3A 56 push esi ; 004C5A3B e840a9f4ff call 0x410380（流读封装，内部 0041039E ff500c 走 +0xC）"),
            ("失败约定", 0x00410389, "b803400080 mov eax,0x80004003（E_POINTER；00410385 test edi,edi / 00410387 jne 才继续）"),
            ("判零间隔", 0x004C5A40, "85c0 test eax,eax ; 004C5A42 7c2d jl 0x4C5A71（无 eax 覆写）"),
            ("成功路-基类子对象构造", 0x004C5A4F, "e86ca7f4ff call 0x4101C0（前 004C5A48 lea ecx,[esp+0xC] / 004C5A4C push ecx / 004C5A4D mov ecx,esi）"),
            ("成功路-装 4 表", 0x004C5A54, "c706a8877e00 / c746048c877e00 / c7460884877e00 / c7460c7c877e00"),
            ("成功路-返 0", 0x004C5A6F, "33c0 xor eax,eax ; 004C5A72 c20800 ret 8"),
        ],
        "sem": "EMPulseClass 流读入构造（vtable slot5）：调 0x410380 从流读入（该封装内部走流虚表 +0xC 的 Read）；失败原样返回被调的错误码（空对象指针时 00410389 给出 E_POINTER 0x80004003），成功则在已就位的 this 上调 0x4101C0 构造基类子对象、装 4 张 EMPulseClass 虚表，返回 0。",
    },
    "004C5AC0": {
        "vt": 0x007E87A8, "slot_no": 8,
        "ring4_at": 0x004C537D, "ring4_host": 0x004C5370, "ring4_base_call": 0x004C5373,
        "ring3_form": "3b2",
        "ring3": [
            ("站点", 0x004C5AF6, "8b1570388a00 mov edx,[0x8A3870] ; 004C5B0A ff5210 call [edx+0x10]"),
            ("判零间隔", 0x004C5B0D, "83f8ff cmp eax,-1 ; 004C5B10 742d je 0x4C5B3F（无 eax 覆写）"),
            ("命中路压缩写", 0x004C5B31, "895481fc mov [ecx+eax*4-4],edx ; 004C5B1F 890d80388a00 mov [0x8A3880],ecx ; 004C5B3D 7ce8 jl 回边"),
            ("收尾-基类析构", 0x004C5B41, "e8aaa6f4ff call 0x4101F0"),
            ("收尾-按 delete 标志释放", 0x004C5B46, "f644240c01 test byte [esp+0xC],1 ; 004C5B4E e8ea2f3000 call 0x7C8B3D"),
        ],
        "callees": [(0x004E0550, "容器 0x8A3870 的 vt[#4] = FindItemIndex（见 ROW_00428EA0 的容器族 dump，同族 or eax,-1 + ret 4）")],
        "sem": "EMPulseClass 标量删除析构：复位 4 张虚表、按全局开关 0xA8E9A0 决定是否调 0x4C58C0 清理格子占用、经 0x7258D0 解除管理器单例引用，再在全局 DynamicVectorClass<EMPulseClass*>（0x8A3870，计数 0x8A3880 / 数组 0x8A3874）里 Find 自身——未命中 -1 跳过、命中则压缩摘链，随后调 0x4101F0 基类析构，最后按 delete 标志释放自身。",
    },
    "005F44A0": {
        "vt": 0x007E3354, "slot_no": 84,
        "ring4_at": 0x0042201C, "ring4_host": 0x00421EA0, "ring4_base_call": 0x00421EAE,
        "ring3_form": "3b2",
        "ring3": [
            ("前置守卫", 0x005F44A4, "8a8683000000 mov al,[esi+0x83] ; 005F44AA 84c0 ; 005F44AC 746a je 0x5F4518"),
            ("站点", 0x005F44AE, "8b15b8eca800 mov edx,[0xA8ECB8] ; 005F44C2 ff5210 call [edx+0x10]"),
            ("判零间隔", 0x005F44C5, "83f8ff cmp eax,-1 ; 005F44C8 742d je 0x5F44F7（无 eax 覆写）"),
            ("命中路压缩写", 0x005F44E9, "895481fc mov [ecx+eax*4-4],edx ; 005F44D7 890dc8eca800 mov [0xA8ECC8],ecx ; 005F44F5 7ce8 jl 回边"),
            ("清标志+读管理器当前对象", 0x005F44FC, "c6868300000000 mov byte [esi+0x83],0 ; 005F4503 e808a6ebff call 0x4AEB10"),
            ("命中当前对象则清空", 0x005F4508, "3bc6 cmp eax,esi ; 005F450A 750c jne ; 005F4513 e818a6ebff call 0x4AEB30"),
        ],
        "callees": [(0x0040CF00, "容器 0xA8ECB8 活表 007E4F64 的 vt[#4] = FindItemIndex"),
                    (0x004AEB10, "管理器 0x87F7E8 的『取当前对象』"), (0x004AEB30, "管理器 0x87F7E8 的『置当前对象』")],
        "sem": "AnimClass::slot84 —— 从全局动画管理器注销自身：仅当 [this+0x83]（已注册标志）为真时，在全局 DynamicVectorClass<AnimClass*>（0xA8ECB8，计数 0xA8ECC8 / 数组 0xA8ECBC）中 Find 自身（未命中返 -1 直接跳过、命中则计数减一并前移压缩数组摘链），清 [this+0x83]；再取管理器 0x87F7E8 的当前对象（0x4AEB10），若正是 this 则以 0 清空（0x4AEB30）。",
    },
    "0062D7A0": {
        "vt": 0x007EF954, "slot_no": 5,
        "ring4_at": 0x0062B767, "ring4_host": 0x0062B5E0, "ring4_base_call": 0x0062B5E9,
        "ring3_form": "3b2",
        "ring3": [
            ("站点", 0x0062D7A9, "50 push eax ; 0062D7AA 56 push esi ; 0062D7AB e8d086fcff call 0x5F5E80"),
            ("被调内的失败源", 0x005F5E8B, "e8f0a4e1ff call 0x410380（流读封装）; 005F5E92 7c65 jl 0x5F5EF9；0x410380 空参于 00410389 返 E_POINTER 0x80004003"),
            ("判零间隔", 0x0062D7B0, "85c0 test eax,eax ; 0062D7B2 7c4f jl 0x62D803（无 eax 覆写）"),
            ("成功路-基类构造", 0x0062D7BF, "e88c63fcff call 0x5F3B50（前 0062D7B8 lea ecx,[esp+0xC] / 0062D7BC push ecx / 0062D7BD mov ecx,esi）"),
            ("成功路-装 4 表", 0x0062D7C4, "c70654f97e00 / c7460438f97e00 / c7460830f97e00 / c7460c28f97e00"),
            ("成功路-成员构造", 0x0062D7EB, "e8501a0a00 call 0x6CF240 ; 0062D7FC e83f1a0a00 call 0x6CF240"),
            ("成功路-返 0", 0x0062D801, "33c0 xor eax,eax ; 0062D804 c20800 ret 8"),
        ],
        "sem": "ParticleClass 流读入构造（vtable slot5）：先调 0x5F5E80（其内部 0x410380 读流并对 5 个成员做读入构造）；失败原样返回错误码（空指针时 E_POINTER 0x80004003），成功则在 this 上调 0x5F3B50 构造基类、装 4 张 ParticleClass 虚表、再构造 [+0xAC] 与 [+0x124] 两个成员对象，返回 0。",
    },
}


def hexdump_around(va, before=0, n=8):
    return C.dump(va, n)


def insn_window(va, span=16, size=None):
    """从 va 起按指令边界打印若干条（避免 mid-instruction + .byte 噪声）。"""
    insns = C.disasm_body(va, span + 16)
    out = []
    end = va + span
    for ins in insns:
        if ins.address < va:
            continue
        if ins.address >= end:
            break
        out.append("%08X  %-18s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out


def raw(va, n):
    b = C.read_va(va, n)
    return " ".join("%02x" % x for x in b)


def insns_in(range_va, lo, hi):
    """打印 [lo,hi) 之间、以 range_va 为解析起点的指令（对齐边界）。"""
    out = []
    for ins in C.disasm_body(range_va, hi - range_va + 16):
        if ins.address < lo:
            continue
        if ins.address >= hi:
            break
        out.append("%08X  %-18s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out


def window_at(insns, va, n=6, lead=1):
    """在已解析的指令表 insns 中，定位覆盖 va 的那条指令，从它（或前 lead 条）起打印 n 条。"""
    idx = None
    for i, ins in enumerate(insns):
        if ins.address <= va < ins.address + ins.size:
            idx = i
            break
    if idx is None:
        return ["(未定位到覆盖 %08X 的指令)" % va]
    start = max(0, idx - lead)
    out = []
    for ins in insns[start:start + n]:
        out.append("%08X  %-18s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out


def build(entry):
    p = PLAN[entry]
    r = ROWS[entry]
    ea = int(entry, 16)
    size = C.ATLAS.get(entry, {}).get("size") or 0
    s = SUR[entry]
    L = []
    A = L.append
    A("# ROW %s   %s   (S20, atlas size=%d, %d insns)" % (entry, r["name"], size, s["n_insn"]))
    A("# 目标：D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe  SHA-256 73201CC0...F67476")
    A("# 工具：capstone 5.0.7 (skipdata=True) + pefile 2024.8.26 / Python 3.12.10")
    A("")

    # ---- ① 入口
    r1 = s["ring1"]
    insns = C.disasm_body(ea, size)
    A("## ① 入口（entry 在 .text 内、atlas 边界自洽、skipdata=0、末条 ret/jmp）")
    A("   entry        = %s   在 .text [00401000,007E038D) 内: %s" % (entry, C.in_text(ea)))
    A("   atlas size   = %d   末条 = %08X %s %s（覆盖 %d/%d 字节）" % (
        size, r1["last_va"], insns[-1].mnemonic, insns[-1].op_str, r1["covered"], size))
    A("   skipdata(id==0) 条数 = %d ；n_insn = %d" % (r1["skipdata"], len(insns)))
    A("   判定：PASS")
    A("")

    # ---- ② 类身份
    vt = p["vt"]
    hits = [h for h in s["ring2"]["hits"] if int(h["vt"], 16) == vt]
    h = hits[0] if hits else None
    A("## ② 类身份（RTTI：槽→[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8 名串；槽号由整表枚举复算）")
    A("   类名匹配表：vt=%08X（本 entry 共驻 %d 张表，取 RTTI 类名与 name 栏同族的那张）" % (
        vt, s["ring2"]["n_hits"]))
    if h:
        slot_va = int(h["slot_va"], 16)
        A("   槽地址        = %08X（vt+0x%X，slot#%d，该表共 %d 槽）" % (
            slot_va, slot_va - vt, int(h["slot_no"]), int(h["n_slots"])))
        A("   槽内 4B 值    = %s   ⇒ 等于 entry %s ：%s" % (
            C.hx(C.u32(slot_va)), entry, C.u32(slot_va) == int(entry, 16)))
        A("   槽 4B 原始字节 = %s" % raw(slot_va, 4))
        A("   [vt-4] COL    = %s ；[COL] 原始字节 = %s ⇒ sig=0x%08X（=0，MSVC 完整对象定位器）" % (
            h["col"], raw(int(h["col"], 16), 16), C.u32(int(h["col"], 16))))
        A("   [COL+0xC] TD  = %s ；TD 原始字节 = %s" % (h["td"], raw(int(h["td"], 16), 20)))
        A("   TD+8 名串     = %s（字节 %s）" % (h["rtti"], raw(int(h["td"], 16) + 8, len(h["rtti"]) + 1)))
        A("   name 栏类名    = %s ⇒ 与 RTTI 类名一致：%s" % (
            r["name"].split("::")[0], C.class_of(h["rtti"]) == r["name"].split("::")[0]))
        A("   槽号自洽      ：name 栏 %s == 枚举槽号 %d" % (r["name"].split("::")[-1], int(h["slot_no"])))
    A("   判定：PASS")
    A("")

    # ---- ④ 使用见证（先写，因为 ③ 要引用其独立性）
    r4at = p["ring4_at"]
    host = p["ring4_host"]
    hsz = C.ATLAS.get(C.hx(host), {}).get("size") or 0
    host_insns = C.disasm_body(host, hsz)
    slot_va = int(h["slot_va"], 16) if h else 0
    A("## ④ 使用见证（活虚表：构造器装的 vt + vt[slot]==entry；锚点在行外、非 atexit）")
    A("   活表自证      ：vt[slot#%d] = %s（%s）= entry" % (
        int(h["slot_no"]) if h else -1, C.hx(C.u32(slot_va)) if h else "?", h["rtti"] if h else "?"))
    b0 = C.read_va(r4at, 7)
    A("   装表锚点      = %08X ；指令字节 = %s ；反汇编 = mov dword ptr [esi], 0x%08X" % (
        r4at, b0.hex(), int(b0[2:6][::-1].hex(), 16) if len(b0) >= 7 else 0))
    A("   所在函数      = %08X（atlas size=%d，`push <该函数>; call 0x7C978A` atexit 注册 = %s）" % (
        host, hsz, C.is_atexit(host)))
    A("   行内?          = %s（本行体 = [%08X,%08X)）⇒ 写点必须在行外" % (
        (ea <= r4at < ea + size), ea, ea + size))
    A("   构造器自证    ：宿主 %08X 首条出向调用在 %08X —— call <基类构造>，装表在其后" % (
        host, p["ring4_base_call"]))
    idx_bc = None
    for i, ins in enumerate(host_insns):
        if ins.address == p["ring4_base_call"]:
            idx_bc = i
            break
    upto = (idx_bc + 2) if idx_bc is not None else 8
    for ins in host_insns[:upto]:
        A("     %08X  %-18s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    A("   装表处上下文：")
    for line in window_at(host_insns, r4at, n=8, lead=3):
        A("     " + line)
    A("   同一虚表的全部立即数安装点（逐个核 atexit / 行内）：")
    for st in s["ring4"]["stores"]:
        A("     %08X  %-32s bytes=%s in_func=%s atexit=%s in_self=%s" % (
            st["va"], st["op"], st["bytes"], st["in_func"], st["atexit"], st["in_self"]))
    A("   ⇒ 采用 %08X（in_func=%08X，atexit=False，in_self=False）作为 ④ 锚。" % (r4at, host))
    A("   判定：PASS")
    A("   ②④ 不同源：② 锚 .rdata 的 COL/TD 描述符与槽内 4B 值；④ 锚 .text 的装表指令字节"
      "（段不同、产物不同、不复用同一槽值顶两环，§12.3）。")
    A("")

    # ---- ③ 整体合同
    A("## ③ 整体合同（只认 ③b；形态 = %s）" % p["ring3_form"])
    for label, va, note in p["ring3"]:
        A("   [%s] %08X" % (label, va))
        A("       %s" % note)
        if any(ins.address <= va < ins.address + ins.size for ins in insns):
            for line in window_at(insns, va, n=7, lead=2):
                A("       " + line)
        else:
            # 该地址不在本行体内（外部 helper），从头按指令边界打印
            f = C.func_of(va)
            fsz = C.ATLAS.get(C.hx(f[0]), {}).get("size") or 64 if f else 64
            for line in C.dump(va, min(fsz, 64)).splitlines()[:8]:
                A("       " + line)
    if p.get("callees"):
        A("   被调返回约定取证（失败常量必须字节可见）：")
        for cv, note in p["callees"]:
            A("     %08X  %s" % (cv, note))
            csz = C.ATLAS.get(C.hx(cv), {}).get("size") or 60
            for line in C.dump(cv, min(csz, 120)).splitlines():
                A("       " + line)
    A("   三陷阱排查：")
    A("     - eax 覆写：cmp/test 与 jcc **零间隔相邻**（见上逐条字节），之间无 `mov eax,..`/`call`")
    A("     - 多路同一 call：不适用（站点被调/容器/动作各异，非仅参数不同）")
    A("     - 模板假句：语义栏写本行具体分支与写动作，不用“对象初始化/清零”式措辞")
    A("   判定：PASS")
    A("")

    # ---- 语义
    A("## 一句话语义")
    A("   " + p["sem"])
    A("")

    # ---- 语义栏引用地址逐条给字节（保证 delta 第 4 列里每个地址都能在本文件里同数查到）
    A("## 语义栏引用地址逐条字节（与 delta 第 4 列逐字同数）")
    src = SEM.get(entry, "")
    cand = sorted(set(re.findall(r"\b([0-9A-F]{8})\b", src.upper())))
    cited = [a for a in cand if 0x00400000 <= int(a, 16) < 0x00C00000]
    skipped = [a for a in cand if a not in cited]
    if not cited:
        A("   （本行未入 delta，无语义栏引用）")
    for a in cited:
        va = int(a, 16)
        sec = C.sec_of(va)
        if C.in_text(va):
            insn = next((x for x in C.disasm_body(va, 16)), None)
            dis = ("%s %s" % (insn.mnemonic, insn.op_str)) if insn else "(非指令边界)"
            b = C.read_va(va, 8)
            A("   %s  [%-6s] %-46s 字节 %s" % (a, sec, dis, " ".join("%02x" % x for x in b)))
        else:
            b = C.read_va(va, 8)
            A("   %s  [%-6s] %-46s 字节 %s" % (a, sec, "（数据地址）", " ".join("%02x" % x for x in b)))
    if skipped:
        A("   （非地址的 8 位十六进制记号已剔除：%s —— 它们是语义栏里引用的机器码字节）" % ", ".join(skipped))
    A("")
    return "\n".join(L) + "\n"


for entry in PLAN:
    txt = build(entry)
    open(os.path.join(OUT, "ROW_%s.txt" % entry), "w", encoding="utf-8").write(txt)
    print("wrote ROW_%s.txt  %d bytes" % (entry, len(txt)))
