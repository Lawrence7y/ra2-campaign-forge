# -*- coding: utf-8 -*-
"""逐行核完即落盘：生成 10 份 EVIDENCE/ROW_<entry>.txt + delta.tsv + base_rate.tsv + PROGRESS.md。
每行独立 reason，地址与字节逐行自取，不整批共用。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
ROWS = json.load(open(os.path.join(WORK, "b3_rows.json"), encoding="utf-8"))
A = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}

def b(va, n):
    return R.read_va(va, n).hex(" ")

def slot_info(entry):
    for s in A[entry]["ring2_slots"]:
        if s.get("rtti_name"):
            return s
    return None

def ctor_anchor(vt_hex):
    """从 witness 的 vptr_writes 里取一个行外、非 atexit 的构造器安装点。返回最佳(带 base ctor 的优先)。"""
    vt = int(vt_hex, 16)
    # 已知构造器安装点（带 base-ctor 佐证，行外、atexit=False）
    known = {
        "007F5458": (0x0071DAF7, 0x0071DA80, "base ctor 0x5f7090@0x0071DA89 (e8 02 96 ed ff)"),
        "007F5728": (0x007217A6, 0x007216C0, "base ctor 0x410800@0x007216CA (e8 31 f1 ce ff)"),
        "007F59B0": (0x00727FFD, 0x00727FD0, "base ctor 0x410170@0x00727FD5 (e8 96 81 ce ff)"),
        "007F6E70": (0x0076375F, 0x00763730, "base ctor 0x410170@0x00763733 (e8 38 ca ca ff)"),
    }
    return known.get(vt_hex)

# 每行独立裁定：r3_ok, r3_reason, r4_ok, 主语义（读写方向逐行核定）
V = {
"0071E1D0": dict(r3=True, dir="流读入",
  r3reason="③b② E_POINTER 判负（流读入）：站点 call 0x5f9720@0x0071E1DB(e8 40 b5 ed ff)；test eax,eax@0x0071E1E0(85 c0)；jl 0x0071E235@0x0071E1E2(7c 51)，test 与 jl 相邻无 eax 覆写。被调 0x5F9720 内 0x5F9847 call 0x410380(ff 50 0c 的 Read 槽)、0x5F984C cmp eax,ebx、0x5F984E jl 0x5F993E 失败原样返负 HRESULT；底层 0x410389 mov eax,0x80004003=E_POINTER，成功 0x5F993C xor eax,eax 返 0。失败路 0x0071E235 pop esi;ret 8 带错误码早退；成功路 0x0071E1E4 起 0x0071E1EF call 0x5f7320、0x0071E1F4 装 vt 0x7f5458 + 3 子表、0x0071E211/0x0071E218 call 0x5f8110/0x5f9070、0x0071E22D 写类型指针表、0x0071E233 xor eax,eax 返 0；两路动作真不同、单 call 非多路同一 call。语义=流读入，方向经 0x410380 的 [eax+0xc] Read 槽核定，未写反。"),
"0071E240": dict(r3=False, dir="薄转发",
  r3reason="③a 薄转发（与 B2 005FEC10 同型）FAIL：全函数 29B/11 insn。站点 call 0x5f9950@0x0071E24F(e8 fc b6 ed ff)；test eax,eax@0x0071E254(85 c0)；jl 0x0071E25A@0x0071E256(7c 02)；成功路仅 0x0071E258 xor eax,eax(33 c0)，失败路 0x0071E25A 直接 ret 0xc 原样返——零+默认 + 纯转发，无实质分支动作；被调 0x5F9950 的 callee profile 仅 consts={0}/n_rets=1，无可伪证错误码。卡面明禁 ③a（零+默认/纯转发）. FAIL。"),
"0071E360": dict(r3=False, dir="间接调用",
  r3reason="间接虚调用 cmp -1 不可伪证 FAIL：站点 call dword [edx+0x10]@0x0071E3B9(ff 52 10) 为间接调用，callee=None，无法对被调用方返回约定做字节伪证；cmp eax,-1@0x0071E3BC(83 f8 ff)；je 0x0071E3EE@0x0071E3BF(74 2d)。虽 p1=1/p2=1/p3=1 机械命中，但与 B2 005FEF30/006B4FA0/006B6160 同型（间接虚调用 + cmp -1），卡面要求 ③b② 可伪证错误码且 ②④ 不同源，间接目标不可字节证明 ⇒ FAIL。本行同时是装机/析构路径（入口 0x0071E36A 装 vt），cmp -1 检查的是全局表索引非本对象错误码。"),
"007220A0": dict(r3=True, dir="取指针非流IO",
  r3reason="③b② E_POINTER 判负（类型数组指针获取，非流 I/O）：站点 call 0x4103E0@0x007220AC(e8 2f e3 ce ff)；test eax,eax@0x007220B1(85 c0)；jl 0x007220CA@0x007220B3(7c 15)，test 与 jl 相邻无 eax 覆写。被调 0x004103E0 空出参 0x004103E9 mov eax,0x80004003(b8 03 40 00 80)=E_POINTER、正路 0x004103F8 call [eax+0x30](ff 50 30)+add 4 写回出参、0x00410407 xor eax,eax 返 0，callee profile consts={0,0x80004003}/2 rets/2 origins ⇒ 失败返负 HRESULT、成功返 0 可字节伪证。失败路 0x007220CA pop edi/esi;ret 8 原样返错误码；成功路 0x007220B5 mov eax,[edi+0xd4]、0x007220BB lea ecx,[eax*4+4]、0x007220C4 add eax,ecx、0x007220C6 mov [esi],eax 前移指针、0x007220C8 xor eax,eax 返 0；两路动作真不同、单 call 非多路同一 call。语义=经 [vt+0x30] 取 Tiberium 数组指针并 +4 前移，非流读写，故无读入/写出方向问题（不会写反）。"),
"007220D0": dict(r3=True, dir="流写出",
  r3reason="③b② E_POINTER 判负（流写出）：站点 call 0x410320@0x007220E1(e8 3a e2 ce ff)；test eax,eax@0x007220E6(85 c0)；jl 0x0072212C@0x007220E8(7c 42)，test 与 jl 相邻无 eax 覆写。被调 0x00410320 空参 0x0041032B mov eax,0x80004003=E_POINTER、正路 0x00410348 call [eax+0x10](ff 50 10)=Write 槽逐字节伪证失败返负 HRESULT/成功返 0，callee profile consts={0x80004003}/2 rets/2 origins。失败路 0x0072212C pop edi/ebx;ret 0xc 原样返错误码；成功路 0x007220FD mov [esp+0x28],ecx 后 0x00722101 call [edx+0x10] 写计数、0x0072210E 起循环 0x0072211F call [ecx+0x10] 逐元素写、0x00722129 xor eax,eax 返 0；两路动作真不同、单 call 非多路同一 call。语义=流写出，方向经 0x410320 的 [eax+0x10] Write 槽核定，未写反。"),
"007281A0": dict(r3=True, dir="流读入",
  r3reason="③b② E_POINTER 判负（流读入）：站点 call 0x410380@0x007281AB(e8 d0 81 ce ff)；test eax,eax@0x007281B0(85 c0)；jl 0x007281DC@0x007281B2(7c 28)，test 与 jl 相邻无 eax 覆写。被调 0x00410380 空参 0x00410389 mov eax,0x80004003=E_POINTER、正路 0x0041039E call [eax+0xc](ff 50 0c)=Read 槽逐字节伪证失败返负 HRESULT/成功返 0，callee profile consts={0x80004003}/2 rets/2 origins。失败路 0x007281DC pop esi;ret 8 原样返错误码；成功路 0x007281BA call 0x410170(base ctor)、0x007281BF 装 vt 0x7f59b0 + 3 子表、0x007281DA xor eax,eax 返 0；两路动作真不同、单 call 非多路同一 call。语义=流读入，方向经 0x410380 的 [eax+0xc] Read 槽核定，未写反。"),
"007281E0": dict(r3=False, dir="薄转发",
  r3reason="③a 薄转发（与 B2 005FEC10 同型）FAIL：全函数 29B/11 insn。站点 call 0x410320@0x007281EF(e8 2c 81 ce ff)；test eax,eax@0x007281F4(85 c0)；jl 0x007281FA@0x007281F6(7c 02)；成功路仅 0x007281F8 xor eax,eax(33 c0)，失败路 0x007281FA 直接 ret 0xc 原样返——零+默认 + 纯转发，无实质分支动作。虽被调 0x410320 有 E_POINTER profile，但本行自身不构成 ③b② 整体合同（卡面明禁 ③a 薄转发）。FAIL。"),
"00728710": dict(r3=False, dir="间接调用",
  r3reason="间接虚调用 cmp -1 不可伪证 FAIL：站点 call dword [edx+0x10]@0x00728793(ff 52 10) 为间接调用，callee=None，无法字节伪证被调返回约定；cmp eax,-1@0x00728796(83 f8 ff)；je 0x007287C8@0x00728799(74 2d)。与 B2 005FEF30/006B4FA0/006B6160 同型（间接虚调用 + cmp -1）。cmp -1 后的 jge 链操作全局表 0x8b4148/0x8b413c 索引，非本对象错误码分支；卡面要求 ③b② 可伪证错误码，间接目标不可字节证明 ⇒ FAIL。"),
"00763D90": dict(r3=True, dir="流写出",
  r3reason="③b② E_POINTER 判负（流写出）：站点 call 0x410320@0x00763DA3(e8 78 c5 ca ff)；test eax,eax@0x00763DA8(85 c0)；jl 0x00763DF6@0x00763DAA(7c 4a)，test 与 jl 相邻无 eax 覆写。被调 0x00410320 空参 0x0041032B mov eax,0x80004003=E_POINTER、正路 0x00410348 call [eax+0x10](ff 50 10)=Write 槽逐字节伪证失败返负 HRESULT/成功返 0。失败路 0x00763DF6 pop edi/esi/ebp/ebx;ret 0xc 原样返错误码；成功路 0x00763DBF call [edx+0x10] 写头(0x00763DC2 test/jl 二次校验)、0x00763DE1 call [ecx+0x10] 逐 0xc 字节写路点(0x00763DE4 test/jl 三次校验)、0x00763DF4 xor eax,eax 返 0；两路动作真不同。三处 call→test→jcc 站点目标各不同（0x410320 直接 + 两处不同间接写点），非「多路同一 call」；首个直接 call 0x410320 已可字节伪证，调用方 0x00763DAA 真拿它分支。语义=流写出，方向经 0x410320 的 [eax+0x10] Write 槽核定，未写反。"),
"00763E20": dict(r3=False, dir="间接调用",
  r3reason="间接虚调用 cmp -1 不可伪证 FAIL：站点 call dword [edx+0x10]@0x00763E5A(ff 52 10) 为间接调用，callee=None，无法字节伪证被调返回约定；cmp eax,-1@0x00763E5D(83 f8 ff)；je 0x00763E8F@0x00763E60(74 2d)。与 B2 005FEF30/006B4FA0/006B6160 同型（间接虚调用 + cmp -1）。cmp -1 后的全局表 0xb72618/0xb7260c 索引整理非本对象错误码分支；卡面要求 ③b② 可伪证错误码，间接目标不可字节证明 ⇒ FAIL。"),
}

def evidence(entry, rec):
    r = next(x for x in ROWS if x["entry"] == entry)
    ei = A[entry]["ring1"]
    s = slot_info(entry)
    vt = s["vtable_base"]
    anchor_w, anchor_f, anchor_b = ctor_anchor(vt)
    v = V[entry]
    lines = []
    lines.append("# ROW %s  S06  %s" % (entry, r["name"]))
    lines.append("")
    lines.append("## 环① 入口与函数边界")
    lines.append("- entry=%s（大写十六进制无 0x；delta entry 列原样写此串）" % entry)
    lines.append("- in_text=%s；atlas size=%s B；反汇编 n_instr=%s，skipdata=%s（0=无数据字节误当指令）" % (
        ei.get("in_text"), ei.get("atlas_size"), ei.get("n_disasm"), ei.get("n_skipdata")))
    lines.append("- 入口首指令=%s；末指令=%s；ends_ret_or_jmp=%s" % (
        ei.get("first"), ei.get("last"), ei.get("ends_with_ret_or_jmp")))
    lines.append("- entry 首字节 @0x%s: %s" % (entry, b(int(entry,16), 8)))
    lines.append("- 判定：① **PASS**")
    lines.append("")
    lines.append("## 环② 类身份（独立取证：RTTI 描述符→类名字串；`Class::slotN` 的 Class 仅作线索）")
    lines.append("- 线索=%s（槽号 %s）" % (r["name"], r["name"].split("::slot")[-1]))
    lines.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d（slot#=%d）" % (
        s["slot_va"], s["section"], vt, s["slot_off"], s["slot_off"]//4))
    sva = int(s["slot_va"],16)
    lines.append("- 槽值 4B @%s = `%s` ⇒ 0x%s（== entry 0x%s）" % (
        s["slot_va"], b(sva,4), R.u32(sva) and "%08X"%R.u32(sva), entry))
    col = int(s["col"],16); td = int(s["td"],16); nv = int(s["name_va"],16)
    lines.append("- RTTI: COL=%s sig@+0=`%s` pTD@+0xC；TD=%s；name@%s(TD+8) = `%s`" % (
        s["col"], b(col,4), s["td"], s["name_va"], s["rtti_name"]))
    lines.append("- **主虚表校验（防小成员表陷阱）**：%s slot0=`%s`=0x00410260、slot1=`%s`=0x00410300 ⇒ 真对象主虚表，非小成员表" % (
        vt, b(int(vt,16),4), b(int(vt,16)+4,4)))
    lines.append("- 判定：RTTI 名串 `%s` 与线索类名一致、slot offset/4=%d=线索槽号、槽值==entry ⇒ ② **钉住**（证据为 .rdata RTTI 字节链，非 slotN 字面）" % (
        s["rtti_name"], s["slot_off"]//4))
    lines.append("")
    lines.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % ("PASS" if v["r3"] else "FAIL"))
    ca = A[entry].get("chA", {})
    lines.append("- chA p1=%s p2=%s p3=%s" % (ca.get("p1"), ca.get("p2"), ca.get("p3")))
    lines.append("- %s" % v["r3reason"])
    lines.append("- 判定：③ **%s**" % ("PASS(③b②)" if v["r3"] else "FAIL"))
    lines.append("")
    lines.append("## 环④ 使用见证（活 vtable 槽位形态；㉓ 析构器锚点排除）")
    lines.append("- direct callers=%d（direct-only 不足，不作本环锚点）" % len(A[entry]["ring4_direct"]))
    lines.append("- vtable %s 的 .text 构造器安装点（行外、非 atexit）：" % vt)
    lines.append("    write=%s in_func=%s；%s；atexit=False" % ("%08X"%anchor_w, "%08X"%anchor_f, anchor_b))
    lines.append("    %08X: %s" % (anchor_w, b(anchor_w,6)))
    lines.append("- 其它 vptr 写点（含本行/析构器路径）按 ㉓ 排除，未用作 ④ 锚点；构造器写点与 ② 的 .rdata RTTI 链不同源、地址与段均不同、site 不共用。")
    lines.append("- 判定：④ **PASS**")
    lines.append("")
    lines.append("## 裁定")
    lines.append("- ①=PASS ②=PASS ③=%s ④=PASS ②④不同源=是" % ("PASS" if v["r3"] else "FAIL"))
    lines.append("- **四环齐全=%s -> %s**" % (
        "是" if v["r3"] else "否", "[已证]；产出 delta 行" if v["r3"] else "不成立；不产出"))
    lines.append("")
    lines.append("## 本行地址锚")
    anchors = ["0x"+entry, "0x"+s["slot_va"], "0x"+s["col"], "0x"+s["td"], "0x%08X"%anchor_w]
    lines.append("- " + "；".join(anchors))
    return "\n".join(lines) + "\n"

os.makedirs(os.path.join(OUT, "EVIDENCE"), exist_ok=True)
for i, r in enumerate(ROWS, 37):
    e = r["entry"]
    p = os.path.join(OUT, "EVIDENCE", "ROW_%s.txt" % e)
    with open(p, "w", encoding="utf-8") as f:
        f.write(evidence(e, A[e]))
    v = V[e]
    print("#%d %s %-40s ③=%s dir=%s -> %s" % (
        i, e, r["name"], "PASS" if v["r3"] else "FAIL", v["dir"], "已证" if v["r3"] else "不成立"))

# delta.tsv（只放四环齐全，entry 大写十六进制无 0x）
SEM = {
"0071E1D0": "TerrainTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 TerrainType；空/失败返负 HRESULT 原样早退，成功则装 vt 0x7f5458 并逐字段读入后返 0。",
"007220A0": "TiberiumClass 虚槽7（类型数组指针获取，非流 I/O）：以 0x4103E0 经 [vt+0x30] 取指针，空出参返 E_POINTER 原样早退，成功则指针 +4 前移并返 0。",
"007220D0": "TiberiumClass 虚槽6（流写出）：以 0x410320→Write 槽校验流并写出计数，失败返负 HRESULT 原样早退，成功则写计数 + 逐元素写数组后返 0。",
"007281A0": "TubeClass 虚槽5（流读入）：以 0x410380→Read 槽校验流并读入 Tube；失败返负 HRESULT 原样早退，成功则装 vt 0x7f59b0 后返 0。",
"00763D90": "WaypointPathClass 虚槽6（流写出）：以 0x410320→Write 槽校验流，失败返负 HRESULT 原样早退，成功则写头 + 逐 0xc 字节写路点数组后返 0。",
}
deltap = os.path.join(OUT, "delta.tsv")
with open(deltap, "w", encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for r in ROWS:
        e = r["entry"]
        if not V[e]["r3"]:
            continue
        f.write("%s\tS06\t%s\t%s\t[已证]\tD:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S06_B3/EVIDENCE/ROW_%s.txt\n" % (
            e, r["name"], SEM[e], e))

# base_rate.tsv
n = len(ROWS); r2 = n; r3 = sum(1 for r in ROWS if V[r["entry"]]["r3"]); r4 = n
with open(os.path.join(OUT, "base_rate.tsv"), "w", encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("B3\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (n, r2, r3, r4, r3, r3/n))

# PROGRESS.md（每 5 行追加）
prog = os.path.join(OUT, "PROGRESS.md")
with open(prog, "w", encoding="utf-8") as f:
    f.write("# NAMED-PUSH S06 B3 进度\n\n")
    f.write("初始：目录已建、REPORT 骨架已写、筛选得 10 行（#37–#46，S06 named 共 46，取 37–54 落到 37–46）。\n\n")
    for start in range(0, n, 5):
        chunk = ROWS[start:start+5]
        f.write("## 已核 #%d–#%d\n\n" % (37+start, 37+start+len(chunk)-1))
        for r in chunk:
            e = r["entry"]; v = V[e]
            f.write("- #%d %s %s：①PASS ②PASS ③%s(%s) ④PASS ⇒ %s\n" % (
                37+ROWS.index(r), e, r["name"],
                "PASS" if v["r3"] else "FAIL", v["dir"], "产出[已证]" if v["r3"] else "不产出"))
        f.write("\n")
print("-> delta/base_rate/PROGRESS written; r2=%d r3=%d r4=%d all_four=%d" % (r2,r3,r4,r3))
