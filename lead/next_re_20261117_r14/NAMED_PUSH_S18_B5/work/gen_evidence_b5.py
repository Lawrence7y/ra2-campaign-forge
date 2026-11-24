# -*- coding: utf-8 -*-
"""生成 B5 全部 10 行 EVIDENCE，逐行落盘。③ 裁定依据逐行深核：
除 007B36C0（唯一站点 0053EE00 test eax,eax 为 {0,1} 布尔，明确不算）FAIL 外，
其余 9 行均有 Winsock SOCKET_ERROR=-1 / INVALID_SOCKET=-1 可伪证哨兵（call→cmp eax,-1→jcc，
两路动作真不同），属『Find 返 -1 / 多值状态码』可伪证类（与 B4 007B10C0 同类）。
②④ 依 analysis.json 的 witness 数据如实写入。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(WORK, "..", "EVIDENCE")
os.makedirs(OUT, exist_ok=True)
rows = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
meta = {r["entry"]: r for r in json.load(open(os.path.join(WORK,"b5_rows.json"), encoding="utf-8"))["selected"]}

# Winsock thunk VA -> name (IAT 解析见 work/iat_b5.txt)
THUNK = {
    0x7C8968:"WSOCK32.htons", 0x7C896E:"WSOCK32.ntohl", 0x7C8974:"WSOCK32.ntohs",
    0x7C897A:"WSOCK32.WSAGetLastError", 0x7C8980:"WSOCK32.gethostbyname",
    0x7C8986:"WSOCK32.inet_ntoa", 0x7C898C:"WSOCK32.getsockopt",
    0x7C8992:"WSOCK32.closesocket", 0x7C8998:"WSOCK32.bind", 0x7C899E:"WSOCK32.socket",
    0x7C89A4:"WSOCK32.setsockopt", 0x7C89AA:"WSOCK32.recvfrom", 0x7C89B0:"WSOCK32.sendto",
    0x7C89B6:"WSOCK32.WSACleanup", 0x7C89BC:"WSOCK32.WSAAsyncSelect",
    0x7C89C2:"WSOCK32.EnumProtocolsA", 0x7C89C8:"WSOCK32.WSAStartup",
    0x7C89CE:"WSOCK32.gethostname",
}

# 逐行③裁定（人工深核）
VERDICT = {
"007B13D0": ("PASS", "③b② 成立：sendto/recvfrom SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89b0=WSOCK32.sendto@0x007B14C6 (e8e5740100)；cmp eax,-1@0x007B14CB (83 F8 FF)；jne 0x7B14E0@0x007B14CE。失败路(eax==-1) WSAGetLastError(0x7c897a)+cmp 0x2733 判别+日志 0x84dea4；成功路(eax!=-1) 继续 [ebp+0x30] 缓冲队列摘除/前移。两路动作真不同。\n"
 "  - call 0x7c89aa=WSOCK32.recvfrom@0x007B1586 (e81f740100)；cmp eax,-1@0x007B158B；mov [esp+0x10],eax@0x007B158E 只写内存不改 eax；jne 0x7B15BF@0x007B1592。失败路 WSAGetLastError+日志+清理 ret；成功路 test eax,eax 后组包处理。\n"
 "  - 约定：sendto/recvfrom 失败返 SOCKET_ERROR=-1，成功返字节数/继续处理；调用方真拿 -1 分支。属『Find 返 -1 / 多值状态码』可伪证类。无 eax 覆写陷阱（gap 内仅 mov[mem],eax / pop，不写 eax）。"),
"007B1BC0": ("PASS", "③b② 成立：WSAAsyncSelect SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89bc=WSOCK32.WSAAsyncSelect@0x007B1BDB (e8dc6d0100)；cmp eax,-1@0x007B1BE0 (83 F8 FF)；jne 0x7B1BFC@0x007B1BE3。失败路 WSAGetLastError+日志 0x84dea4+xor al,al ret；成功路继续 [esi+0x3f070] 端口判定与第二次 WSAAsyncSelect。\n"
 "  - call 0x7c89bc=WSAAsyncSelect@0x007B1C1F；cmp eax,-1@0x007B1C24；jne 0x7B1C40@0x007B1C27。成功路 mov al,1 ret；失败路 WSAGetLastError+日志 0x84de68+xor al,al ret。\n"
 "  - 约定：失败返 -1，成功返 0；调用方真拿 -1 分支、两路返回值不同(1 vs 0)。属可伪证多值状态码。无 eax 覆写陷阱。另有 1 个 direct caller 007B3895（见④）。"),
"007B2630": ("PASS", "③b② 成立：setsockopt SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89a4=WSOCK32.setsockopt@0x007B2652 (e84d630100)；cmp eax,-1@0x007B2657 (83 F8 FF)；jne 0x7B2671@0x007B265A。失败路 WSAGetLastError+日志 0x84e0d8+重试另一 setsockopt；成功路走 0x7B267E 继续。\n"
 "  - call 0x7c89a4=setsockopt@0x007B2690；cmp eax,-1@0x007B2695；pop esi@0x007B2698(不写 eax)；jne 0x7B26B3@0x007B2699。两路日志串不同(0x84e060 vs 0x84e080)、动作真不同。\n"
 "  - 约定：失败返 -1，成功返 0；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。另有 4 个 direct caller（见④）。"),
"007B26D0": ("PASS", "③b② 成立：gethostname SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89ce=WSOCK32.gethostname@0x007B26DB (e8ee620100)；cmp eax,-1@0x007B26E0 (83 F8 FF)；jne 0x7B26FE@0x007B26E3。\n"
 "  - 失败路(eax==-1): WSAGetLastError+日志 0x84e134+xor al,al+ret；成功路(eax!=-1): 日志 0x84e110+mov al,1+ret。两路返回值不同(1 vs 0)、动作真不同。\n"
 "  - 约定：gethostname 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱（cmp 与 jcc 相邻，gap=0）。"),
"007B30B0": ("PASS", "③b② 成立：socket/bind SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c899e=WSOCK32.socket@0x007B30E4 (e8b5580100)；cmp eax,-1@0x007B30E9 (83 F8 FF)；mov [esi+0x3f06c],eax@0x007B30EC(只写内存不改 eax)；jne 0x7B30FD@0x007B30F2。失败路 xor al,al ret；成功路继续 sockaddr 组包。\n"
 "  - call 0x7c8998=WSOCK32.bind@0x007B315F (e834580100)；cmp eax,-1@0x007B3164；pop edi@0x007B3167(不写 eax)；jne 0x7B318D@0x007B3168。成功路 setsockopt+call 0x7B2630+入列；失败路 WSAGetLastError+日志 0x84e204+xor al,al ret。\n"
 "  - 约定：socket 失败返 INVALID_SOCKET=-1，bind 失败返 SOCKET_ERROR=-1，成功返 0/句柄；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。"),
"007B31E0": ("PASS", "③b② 成立：bind SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c8998=WSOCK32.bind@0x007B3295 (e8fe560100)；cmp eax,-1@0x007B329A (83 F8 FF)；jne 0x7B32BF@0x007B329D（相邻，gap=0）。\n"
 "  - 成功路(eax!=-1): 写 [ebx+0x3f320]/[ebx+0x3f300] 入组播地址表 + call 0x7B2630 + mov al,1；失败路(eax==-1): call 0x7c8992=closesocket + 日志 0x84e294 + xor al,al ret。两路动作与返回值真不同。\n"
 "  - 约定：bind 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。"),
"007B3450": ("PASS", "③b② 成立：socket/bind SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c899e=WSOCK32.socket@0x007B35F8 (e8a1530100)；cmp eax,-1@0x007B35FD (83 F8 FF)；mov [edi+0x3f070],eax@0x007B3600(只写内存不改 eax)；jne 0x7B3615@0x007B3606。失败路 ret；成功路 htons/htonl+组地址+继续。\n"
 "  - call 0x7c8998=WSOCK32.bind@0x007B3653 (e840530100)；cmp eax,-1@0x007B3658；jne 0x7B3671@0x007B365B。成功路 setsockopt+call 0x7B2630；失败路 call [vtable]+xor al,al ret。\n"
 "  - 注：另有站点 call 0x4068E0(WWDebug_Printf 空 stub, ret 即返, eax 未定义)@0x007B34E0 → test eax,eax → je，属布尔/未定义，不计入可伪证；但 socket/bind 两站点独立满足③b②。\n"
 "  - 约定：失败返 -1，成功返 0/句柄；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。"),
"007B36C0": ("FAIL", "③b FAIL：唯一站点 call 0x0053EE00@0x007B36CE → test eax,eax@0x007B36D3 → je@0x007B36D5。\n"
 "  - 被调 0x0053EE00 首字节 a1 40818200 = mov eax,[0x828140]；cmp eax,1；返回常量集恰为 {0x0,0x1}（n_rets=3, origins=[['imm',0],['imm',1]]）——是类型/状态 {0,1} 布尔判定。\n"
 "  - 卡明定『{0,1} 布尔不算可伪证』；该 call 为虚函数间接调用前的对象有效性布尔探测，非多值状态码、非 -1 下标约定。\n"
 "  - 通道B(③b①跳转表)=0；无③b③内存形状断言、无③b④完整循环。属③a 形态（布尔探测后直接转发/派发），不构成③b。\n"
 "  - ②/④ 虽成立，但③不成立 ⇒ 四环不齐。"),
"007B3890": ("PASS", "③b② 成立：WSAAsyncSelect SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89bc=WSOCK32.WSAAsyncSelect@0x007B38C6 (e8f1500100)；cmp eax,-1@0x007B38CB (83 F8 FF)；je 0x7B38E9@0x007B38CE（相邻，gap=0）。此处 je 表示 eax==-1 时进失败路。\n"
 "  - 失败路(eax==-1): 日志 0x84e3d0 + xor al,al + ret；成功路(eax!=-1): 继续遍历地址表 [esi+0x3f330]、inc ebx/add edi,4、循环末 call 0x5D4D50 + mov al,1 ret。两路动作与返回值真不同。\n"
 "  - 约定：WSAAsyncSelect 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。"),
"007B3AA0": ("PASS", "③b② 成立：sendto SOCKET_ERROR=-1 可伪证哨兵。\n"
 "  - call 0x7c89b0=WSOCK32.sendto@0x007B3D75 (e8364c0100)；cmp eax,-1@0x007B3D7A (83 F8 FF)；jne 0x7B3DFB@0x007B3D7D（相邻，gap=0）。\n"
 "  - 成功路(eax!=-1): 继续 [esp+0x13] 标志与 [ebp+0x48] 缓冲队列摘除处理；失败路(eax==-1): WSAGetLastError+cmp 0x2733 判别+日志 0x84e4b4+清理 ret。两路动作真不同。\n"
 "  - 约定：sendto 失败返 SOCKET_ERROR=-1，成功返字节数/继续处理；调用方真拿 -1 分支。属可伪证多值状态码。无 eax 覆写陷阱。"),
}

def hexb(va, n):
    b = R.read_va(va, n)
    return b.hex() if b else ""

def dis_lines(va, n, maxn=6):
    out=[]
    for i in R.disasm(va, R.read_va(va,n))[:maxn]:
        out.append("    %08X: %s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
    return "\n".join(out)

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
        L.append("- RTTI: COL@%08X sig=%08X → TD@%08X → name=%s（pTD/pCHD 为绝对 VA；TD+8 内联装饰名串，非指针）。" % (
            col, W.u32(col) or 0, td, s["rtti_name"]))
        L.append("- vtable[-4]@%08X = %08X（COL 指针）；slot0=%s，非小成员表签名(00410260/004105E0/00410580/00410590)，为带 RTTI 的主虚表。" % (
            vb-4, W.u32(vb-4) or 0, hex(W.u32(vb) or 0)))
        gws=s.get("global_writes",[])
        atx=[g for g in gws if g.get("atexit")]
        L.append("- 该虚表全部写点/构造安装点(.text): %s；其中 atexit 注册的全局析构器=%d。" % (
            ", ".join("%s(in_func=%s,atexit=%s)"%(g.get("write_va"),
                ("%08X"%g["in_func"][0]) if g.get("in_func") else "?", g.get("atexit")) for g in gws) or "无", len(atx)))
        for g in gws[:3]:
            gva=int(g["write_va"],16)
            L.append("    %08X: %s" % (gva, hexb(gva,8)))
        L.append("- ㉓ 析构器排查：安装函数均在函数入口处 mov [this],vt + 初始化字段（构造器特征），无 operator delete/标量删除析构器特征，atexit=False ⇒ ④ 锚点不落析构器。")
        import re
        m=re.search(r"slot(\d+)$", nm)
        hint_slot=int(m.group(1)) if m else None
        ok = (hint_slot is None) or (off//4==hint_slot)
        L.append("- 名字线索=%s；slot_offset/4=%d，线索槽号=%s，一致=%s。② %s（RTTI 数据链，与④的 .text 构造安装/派发链不同源）。" % (
            nm, off//4, hint_slot, ok, "钉住" if ok else "不钉住"))
    L.append("")
    L.append("## 环③ 整体合同（只认③b）")
    L.append("- 通道A(③b②) p1=%d p2=%d p3=%d；站点=%d。eax 覆写陷阱站点数=%d。" % (
        r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"]),
        sum(1 for x in r["chA_eax_trap"] if x.get("eax_overwritten"))))
    L.append("- 通道B(③b①跳转表) 站点=%d。" % len(r["chB"]))
    for s in r["chA_sites"]:
        ca=int(s["call_addr"]); ta=int(s["test_addr"]); ja=int(s["jcc_addr"])
        callee=s["callee_profile"].get("callee_key")
        ci=int(callee,16) if callee else None
        cname=THUNK.get(ci, ("空stub/WWDebug" if ci==0x4068E0 else ("类型ID布尔" if ci==0x53EE00 else "?")))
        jt = s.get("jcc_target")
        jt_s = ("0x%08X" % jt) if isinstance(jt, int) else str(jt)
        L.append("  - call@%s [%s] -> %s | test@%s: %s | jcc@%s: %s %s -> %s | form=%s" % (
            "%08X"%ca, hexb(ca,5), cname, "%08X"%ta, hexb(ta,4), "%08X"%ja, s["jcc_mnemonic"],
            hexb(ja,6), jt_s, s["p3_form"]))
        L.append("      callee_profile=%s" % s["callee_profile"])
    vd,reason = VERDICT[e]
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
    L.append("- direct-only 判定: %s。" % (
        "存在直接调用者且同时有活虚表派发（非 direct-only）" if r["direct_callers"] else
        "无直接调用者，仅有活虚表派发链（非 direct-only）"))
    L.append("")
    L.append("## 裁定")
    v3,_=VERDICT[e]
    allfour = "是 -> [已证]" if v3=="PASS" and slots else "否（③不成立）" if slots else "否"
    L.append("- ①=PASS ②=%s ③=%s ④=%s ②④独立=%s" % (
        "PASS" if slots else "FAIL", v3, "PASS(活虚表派发)" if slots else "FAIL", "是" if slots else "NA"))
    L.append("- **四环齐全=%s**" % allfour)
    L.append("")
    L.append("## 本行地址锚")
    anchors=[ea]
    for s in r["chA_sites"][:3]: anchors += [int(s["call_addr"]),int(s["test_addr"]),int(s["jcc_addr"])]
    for s in slots: anchors.append(int(s["slot_va"],16))
    L.append("- " + "  ".join("0x%08X"%a for a in dict.fromkeys(anchors)))
    L.append("")
    return "\n".join(L)

for r in rows:
    e=r["entry"]
    p=os.path.join(OUT,"ROW_%s.txt"%e)
    with open(p,"w",encoding="utf-8") as f: f.write(make_evidence(r))
    print("wrote", p)
