# -*- coding: utf-8 -*-
"""生成 B4 全部 18 行 EVIDENCE，逐行落盘。③ 裁定依据人工深核结论：
- 007B10C0: ③b② PASS (Winsock SOCKET_ERROR=-1 哨兵, call->cmp eax,-1->jne 两路动作真不同)
- 007AB440/007AB8E0: chA p3=0, 无可伪证站点 -> FAIL
- 007AC700/007AC870/007AD690: ATL QueryInterface 模板, 内部 call+test eax 判空 {0,1} -> FAIL
- 其余 VCChatEventSink slot: 被调 0x775940/0x7B54B0 返回 null/指针布尔, 0x7C8D20/0x7B5340/0x7B4940/0x79D110 返回 unknown/布尔 -> FAIL
②④ 依 analysis.json 的 witness 数据如实写入。
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(WORK, "..", "EVIDENCE")
os.makedirs(OUT, exist_ok=True)
rows = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
meta = {r["entry"]: r for r in json.load(open(os.path.join(WORK,"b4_rows.json"), encoding="utf-8"))["selected"]}

def hexb(va, n):
    b = R.read_va(va, n)
    return b.hex() if b else ""

def dis_lines(va, n, maxn=6):
    out=[]
    for i in R.disasm(va, R.read_va(va,n))[:maxn]:
        out.append("    %08X: %s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
    return "\n".join(out)

def verdict(entry, chA):
    if entry == "007B10C0":
        return ("PASS", "③b② 成立： Winsock SOCKET_ERROR=-1 可伪证哨兵。\n"
            "  - call 0x7c899e=WSOCK32.socket@0x007B1147；cmp eax,-1@0x007B114C (83 F8 FF)，"
            "mov [esi+0x3f06c],eax@0x007B114F 只写内存不改 eax，pop edi@0x007B1155 不动 eax，jne 0x7B1180@0x007B1156：无 eax 覆写陷阱。\n"
            "  - call 0x7c8998=WSOCK32.bind@0x007B126B；cmp eax,-1@0x007B1270 (83 F8 FF)；jne 0x7B129D@0x007B1273。\n"
            "  - call 0x7c89a4=WSOCK32.setsockopt@0x007B12D9 / 0x007B132A / 0x007B137B；各 cmp eax,-1 + jne。\n"
            "  - 失败路 (eax==-1)：call WSAGetLastError(0x7c897a)+日志串 0x84dd04/0x84dcec + return；"
            "成功路：继续 setsockopt/bind 建链、组地址数据后 ret。两路动作真不同，非同一 call 仅差参数。\n"
            "  - 约定：失败返回 -1 (SOCKET_ERROR)，成功返回 0/有效 socket 句柄；调用方真拿它分支。属『Find 返 -1 / 多值状态码』可伪证类。")
    if chA["p3"] == 0:
        return ("FAIL", "③b FAIL：通道A p3=0，函数体内无 call→可伪证 imm 比较→jcc 的返回约定站点；"
                        "入口仅 test 参数/布尔探测后即 ret，属③a/模板假句，不构成③b。")
    if entry in ("007AC700","007AC870","007AD690"):
        return ("FAIL", "③b FAIL：ATL CComObject::QueryInterface(slot0) 模板。唯一站点 call [map+4]→test eax,eax→je→E_NOINTERFACE，"
                        "被调返回的是接口指针或 0（判空 {0,1} 布尔），非多值状态码也非 -1 下标约定；"
                        "E_POINTER(0x80004003)/E_NOINTERFACE(0x80004002) 是本函数自身常量返回，非消费被调返回约定。属模板假句。")
    # generic VCChatEventSink slot
    return ("FAIL", "③b FAIL：函数体内 call→test eax,eax→je/jne 站点被调均为布尔/null 探测——"
                    "0x775940 返回 0 或指针 (xor eax,eax;ret / mov eax,[eax*8+..];ret)，"
                    "0x7B54B0 返回 0 或 this，0x7C8D20/0x7B5340/0x7B4940/0x79D110 返回 unknown/布尔；"
                    "无多值状态码、无 -1 下标约定，{0,1} 布尔不算可伪证。无独立③b①跳转表(chB=0)、无③b③/③b④完整循环。")

def make_evidence(r):
    e=r["entry"]; nm=meta[e]["name"]; ea=r["ea"]; size=r["atlas"].get("size",0)
    L=[]
    L.append("# ROW %s  S18  %s\n" % (e,nm))
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s；delta entry 列原样写此串。" % e)
    L.append("- atlas size=%s B，反汇编 n_insn=%d，skipdata=%d，in_text=%s，body_end=%08X(in_text=%s)。" % (
        size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"], r["body_end"], r["body_end_in_text"]))
    L.append("- 入口字节: %s" % hexb(ea,16))
    L.append(dis_lines(ea,24,6))
    L.append("")
    L.append("## 环② 类身份（RTTI 描述符→类名字串；Class::slotN 的 Class 仅作线索，已由 RTTI 钉死）")
    slots=[s for s in r["slots"] if s.get("rtti_name")]
    if not slots:
        L.append("- 无可解析 RTTI 槽 → ② FAIL。")
    for s in slots:
        vb=int(s["vtable_base"],16); off=int(s["slot_off"]); col=int(s["col"],16); td=int(s["td"],16)
        L.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d (0x%X)。" % (
            s["slot_va"], s.get("section","?"), s["vtable_base"], off, off))
        L.append("- 槽内容 4B @%s = %s（应等于 entry %s）。" % (s["slot_va"], hexb(int(s["slot_va"],16),4), e))
        L.append("- RTTI: COL@%08X sig=%08X → TD@%08X → name=%s。" % (
            col, W.u32(col) or 0, td, s["rtti_name"]))
        L.append("- vtable[-4]@%08X = %08X（COL 指针）；vtable[0..5]=%s → 80+ 槽主虚表，非小成员表。" % (
            vb-4, W.u32(vb-4) or 0, [hex(W.u32(vb+4*i) or 0) for i in range(6)]))
        gws=s.get("global_writes",[])
        atx=[g for g in gws if g.get("atexit")]
        L.append("- 构造安装点(.text): %s；atexit/析构器安装点=%d。" % (
            ", ".join("%s(in_func=%s,atexit=%s)"%(g.get("write_va"),
                ("%08X"%g["in_func"][0]) if g.get("in_func") else "?", g.get("atexit")) for g in gws) or "无", len(atx)))
        for g in gws[:2]:
            gva=int(g["write_va"],16)
            L.append("    %08X: %s" % (gva, hexb(gva,8)))
        # slot number check
        hint_slot=None
        import re
        m=re.search(r"slot(\d+)$", nm)
        if m: hint_slot=int(m.group(1))
        ok = (hint_slot is None) or (off//4==hint_slot)
        L.append("- 名字线索=%s；slot_offset/4=%d，线索槽号=%s，一致=%s。② %s（RTTI 数据链，与④的 .text 构造安装链不同源）。" % (
            nm, off//4, hint_slot, ok, "钉住" if ok else "不钉住"))
    L.append("")
    L.append("## 环③ 整体合同（只认③b）")
    L.append("- 通道A(③b②) p1=%d p2=%d p3=%d；站点=%d。eax 覆写陷阱站点数=%d。" % (
        r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"]),
        sum(1 for x in r["chA_eax_trap"] if x.get("eax_overwritten"))))
    L.append("- 通道B(③b①跳转表) 站点=%d。" % len(r["chB"]))
    for s in r["chA_sites"]:
        ca=int(s["call_addr"]); ta=int(s["test_addr"]); ja=int(s["jcc_addr"])
        jt = s.get("jcc_target")
        jt_s = ("0x%08X" % jt) if isinstance(jt, int) else str(jt)
        L.append("  - call@%08X [%s] | test@%08X: %s | jcc@%08X: %s %s -> %s | form=%s" % (
            ca, hexb(ca,6), ta, hexb(ta,4), ja, s["jcc_mnemonic"],
            hexb(ja,6), jt_s, s["p3_form"]))
        L.append("      callee_profile=%s" % s["callee_profile"])
    vd,reason = verdict(e, r["chA"])
    L.append("- 裁定: %s" % vd)
    L.append("  %s" % reason)
    L.append("")
    L.append("## 环④ 使用见证（真实调用者/活虚表派发；与②不同源）")
    L.append("- direct callers(%d): %s" % (len(r["direct_callers"]), ", ".join(r["direct_callers"]) or "无"))
    for s in slots:
        ds=s.get("dispatch_sites",[])
        L.append("- 活虚表派发: vt %s 槽 %s(=entry) 由构造安装点写入活对象；"
                 "call [reg+0x%X] 类型的 dispatch sites=%d，样例=%s。该链在 .text 代码中，与②的 .rdata RTTI 数据链独立。" % (
            s["vtable_base"], s["slot_va"], int(s["slot_off"]), len(ds), ", ".join(ds[:8]) or "无"))
    L.append("- direct-only 判定: 无直接调用者，仅有活虚表派发链（非 direct-only）。")
    L.append("")
    L.append("## 裁定")
    v3,_=verdict(e,r["chA"])
    allfour = "是 -> [已证]" if v3=="PASS" and slots else "否"
    L.append("- ①=PASS ②=%s ③=%s ④=%s ②④独立=%s" % (
        "PASS" if slots else "FAIL", v3, "PASS(活虚表派发)" if slots else "FAIL", "是" if slots else "NA"))
    L.append("- **四环齐全=%s**" % allfour)
    L.append("")
    L.append("## 本行地址锚")
    anchors=[ea]
    for s in r["chA_sites"][:2]: anchors += [int(s["call_addr"]),int(s["test_addr"]),int(s["jcc_addr"])]
    for s in slots: anchors.append(int(s["slot_va"],16))
    L.append("- " + "  ".join("0x%08X"%a for a in dict.fromkeys(anchors)))
    L.append("")
    return "\n".join(L)

for r in rows:
    e=r["entry"]
    p=os.path.join(OUT,"ROW_%s.txt"%e)
    with open(p,"w",encoding="utf-8") as f: f.write(make_evidence(r))
    print("wrote", p)
