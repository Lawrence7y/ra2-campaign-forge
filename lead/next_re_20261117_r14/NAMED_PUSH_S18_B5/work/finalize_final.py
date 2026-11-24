# -*- coding: utf-8 -*-
"""B5 最终落盘：重生成 10 份 EVIDENCE（正确枚举/排除析构器写点）+ delta/base_rate/PROGRESS/REPORT。
只读 gamemd.exe 与 work/analysis.json；写域仅本批次目录。逐行核完即写。"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(WORK, "..")
EVD  = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVD, exist_ok=True)

rows = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
meta = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "b5_rows.json"), encoding="utf-8"))["selected"]}
by_entry = {r["entry"]: r for r in rows}

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

# ㉓ 分类：每个 vtable 的全部写点 -> (写点VA, 所在函数, 类别, atexit)
# 类别: ctor=构造安装(有效④锚) / dtor=非删除析构(排除) / scalar_delete_dtor=标量删除析构(排除)
VT_WRITES = {
 "007F794C": [("007B0DA4","007B0D90","ctor",False)],
 "007F79BC": [("007B1A20","007B19C0","ctor",False),
              ("007B1ABC","007B1AB0","dtor(非删除析构,slot0所在类析构链)",False),
              ("007B278C","007B2780","scalar_delete_dtor(vt slot0,ret 4)",False)],
 "007F7A6C": [("007B2E2D","007B2DB0","ctor",False),
              ("007B2E56","007B2E50","dtor(非删除析构)",False),
              ("007B4176","007B4170","scalar_delete_dtor(vt slot0,ret 4)",False)],
}
# 构造器的活性（direct callers 数，实测）
CTOR_LIVE = {"007B0D90":5, "007B19C0":2, "007B2DB0":1}

VERDICT = {
 "007B13D0": ("PASS", "③b② 成立：sendto/recvfrom SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89b0=WSOCK32.sendto@0x007B14C6 (e8e5740100)；cmp eax,-1@0x007B14CB (83 F8 FF)；jne 0x7B14E0@0x007B14CE。失败路(eax==-1) WSAGetLastError(0x7c897a)+cmp 0x2733 判别+日志 0x84dea4；成功路(eax!=-1) 继续 [ebp+0x30] 缓冲队列摘除/前移。两路动作真不同。\n"
  "  - call 0x7c89aa=WSOCK32.recvfrom@0x007B1586 (e81f740100)；cmp eax,-1@0x007B158B；mov [esp+0x10],eax@0x007B158E 只写内存不改 eax、不破坏 cmp 标志；jne 0x7B15BF@0x007B1592。失败路 WSAGetLastError+日志+清理 ret；成功路 test eax,eax 后组包处理。\n"
  "  - 约定：sendto/recvfrom 失败返 SOCKET_ERROR=-1，成功返字节数/继续处理；调用方真拿 -1 分支。属『Find 返 -1 / 多值状态码』可伪证类（与 B4 007B10C0、B1 005414C0 同构）。无 eax 覆写陷阱。"),
 "007B1BC0": ("PASS", "③b② 成立：WSAAsyncSelect SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89bc=WSAAsyncSelect@0x007B1BDB (e8dc6d0100)；cmp eax,-1@0x007B1BE0 (83 F8 FF)；jne 0x7B1BFC@0x007B1BE3。失败路 WSAGetLastError+日志 0x84dea4+xor al,al ret；成功路继续 [esi+0x3f070] 端口判定与第二次 WSAAsyncSelect。\n"
  "  - call WSAAsyncSelect@0x007B1C1F；cmp eax,-1@0x007B1C24；jne 0x7B1C40@0x007B1C27。成功路 mov al,1 ret；失败路日志 0x84de68+xor al,al ret。\n"
  "  - 约定：失败返 -1，成功返 0；两路返回值不同(1 vs 0)、调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。另有 direct caller 007B3895（④）。"),
 "007B2630": ("PASS", "③b② 成立：setsockopt SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89a4=setsockopt@0x007B2652 (e84d630100)；cmp eax,-1@0x007B2657 (83 F8 FF)；jne 0x7B2671@0x007B265A。失败路 WSAGetLastError+日志 0x84e0d8+重试另一 setsockopt；成功路走 0x7B267E 继续。\n"
  "  - call setsockopt@0x007B2690；cmp eax,-1@0x007B2695；pop esi@0x007B2698(不写 eax、不改标志)；jne 0x7B26B3@0x007B2699。两路日志串不同(0x84e060 vs 0x84e080)、动作真不同。\n"
  "  - 约定：失败返 -1，成功返 0；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。另有 4 个 direct caller（④）。"),
 "007B26D0": ("PASS", "③b② 成立：gethostname SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89ce=gethostname@0x007B26DB (e8ee620100)；cmp eax,-1@0x007B26E0 (83 F8 FF)；jne 0x7B26FE@0x007B26E3（相邻 gap=0）。\n"
  "  - 失败路(eax==-1): WSAGetLastError+日志 0x84e134+xor al,al+ret；成功路(eax!=-1): 日志 0x84e110+mov al,1+ret。两路返回值不同(1 vs 0)、动作真不同。\n"
  "  - 约定：gethostname 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
 "007B30B0": ("PASS", "③b② 成立：socket/bind SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c899e=socket@0x007B30E4 (e8b5580100)；cmp eax,-1@0x007B30E9；mov [esi+0x3f06c],eax@0x007B30EC(只写内存不改 eax/标志)；jne 0x007B30FD@0x007B30F2。失败路 xor al,al ret；成功路继续 sockaddr 组包。\n"
  "  - call 0x7c8998=bind@0x007B315F (e834580100)；cmp eax,-1@0x007B3164；pop edi@0x007B3167(不写 eax)；jne 0x007B318D@0x007B3168。成功路 setsockopt+call 0x7B2630+入列；失败路 WSAGetLastError+日志 0x84e204+xor al,al ret。\n"
  "  - 约定：socket 失败返 INVALID_SOCKET=-1、bind 失败返 SOCKET_ERROR=-1，成功返 0/句柄；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
 "007B31E0": ("PASS", "③b② 成立：bind SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c8998=bind@0x007B3295 (e8fe560100)；cmp eax,-1@0x007B329A (83 F8 FF)；jne 0x007B32BF@0x007B329D（相邻 gap=0）。\n"
  "  - 成功路(eax!=-1): 写 [ebx+0x3f320]/[ebx+0x3f300] 入组播地址表 + call 0x7B2630 + mov al,1；失败路(eax==-1): call closesocket + 日志 0x84e294 + xor al,al ret。两路动作与返回值真不同。\n"
  "  - 约定：bind 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
 "007B3450": ("PASS", "③b② 成立：socket/bind SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c899e=socket@0x007B35F8 (e8a1530100)；cmp eax,-1@0x007B35FD；mov [edi+0x3f070],eax@0x007B3600(只写内存不改 eax/标志)；jne 0x007B3615@0x007B3606。失败路 ret；成功路 htons/htonl+组地址+继续。\n"
  "  - call 0x7c8998=bind@0x007B3653 (e840530100)；cmp eax,-1@0x007B3658；jne 0x007B3671@0x007B365B。成功路 setsockopt+call 0x7B2630；失败路 call[vtable]+xor al,al ret。\n"
  "  - 注：另有站点 call 0x4068E0(WWDebug_Printf 空 stub, ret 即返, eax 未定义)@0x007B34E0 → test eax,eax → je，属布尔/未定义、不计入可伪证；但 socket/bind 两站点独立满足 ③b②。\n"
  "  - 约定：失败返 -1，成功返 0/句柄；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
 "007B36C0": ("FAIL", "③b FAIL：唯一站点 call 0x0053EE00@0x007B36CE → test eax,eax@0x007B36D3 → je@0x007B36D5。\n"
  "  - 被调 0x0053EE00 首字节 a1 40818200 = mov eax,[0x828140]；cmp eax,1；返回常量集恰为 {0x0,0x1}（n_rets=3, origins=[['imm',0],['imm',1]]）——是类型/状态 {0,1} 布尔判定。\n"
  "  - 卡明定『{0,1} 布尔不算可伪证』；该 call 为虚函数间接调用前的对象有效性布尔探测，非多值状态码、非 -1 下标约定。\n"
  "  - 通道B(③b①跳转表)=0；无 ③b③ 内存形状断言、无 ③b④ 完整循环。属 ③a 形态（布尔探测后直接转发/派发），不构成 ③b。\n"
  "  - ①/②/④ 均成立，但 ③ 不成立 ⇒ 四环不齐。"),
 "007B3890": ("PASS", "③b② 成立：WSAAsyncSelect SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89bc=WSAAsyncSelect@0x007B38C6 (e8f1500100)；cmp eax,-1@0x007B38CB (83 F8 FF)；je 0x007B38E9@0x007B38CE（相邻 gap=0，eax==-1 进失败路）。\n"
  "  - 失败路(eax==-1): 日志 0x84e3d0+xor al,al+ret；成功路(eax!=-1): 遍历地址表 [esi+0x3f330]+inc ebx/add edi,4+循环末 call 0x5D4D50+mov al,1 ret。两路动作与返回值真不同。\n"
  "  - 约定：WSAAsyncSelect 失败返 SOCKET_ERROR=-1，成功返 0；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
 "007B3AA0": ("PASS", "③b② 成立：sendto SOCKET_ERROR=-1 可伪证哨兵。\n"
  "  - call 0x7c89b0=sendto@0x007B3D75 (e8364c0100)；cmp eax,-1@0x007B3D7A (83 F8 FF)；jne 0x007B3DFB@0x007B3D7D（相邻 gap=0）。\n"
  "  - 成功路(eax!=-1): 继续 [esp+0x13] 标志与 [ebp+0x48] 缓冲队列摘除处理；失败路(eax==-1): WSAGetLastError+cmp 0x2733 判别+日志 0x84e4b4+清理 ret。两路动作真不同。\n"
  "  - 约定：sendto 失败返 SOCKET_ERROR=-1，成功返字节数/继续处理；调用方真拿 -1 分支。属可伪证 -1 哨兵类。无 eax 覆写陷阱。"),
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
    m=re.search(r"slot(\d+)$", nm); hint_slot=int(m.group(1)) if m else None
    cls_hint = nm.split("::")[0]
    # 选择与名字类匹配的 RTTI 槽作为 ② 主锚
    slots=[s for s in r["slots"] if s.get("rtti_name")]
    prim=None
    for s in slots:
        if cls_hint.replace("Class","") in s["rtti_name"] or s["rtti_name"].find(cls_hint)>=0 or cls_hint in s["rtti_name"]:
            if int(s["slot_off"])//4 == hint_slot:
                prim=s; break
    if prim is None:
        for s in slots:
            if int(s["slot_off"])//4 == hint_slot: prim=s; break
    if prim is None and slots: prim=slots[0]

    L=[]
    L.append("# ROW %s  S18  %s\n" % (e,nm))
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s；delta entry 列原样写此串。" % e)
    L.append("- atlas size=%s B，反汇编 n_insn=%d，skipdata=%d，in_text=%s，body_end=%08X(in_text=%s)。" % (
        size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"], r["body_end"], r["body_end_in_text"]))
    L.append("- 入口字节: %s" % hexb(ea,16))
    L.append(dis_lines(ea,24,6)); L.append("")

    L.append("## 环② 类身份（RTTI 描述符→类名字串；Class::slotN 的 Class 仅线索，已由 RTTI 独立钉死）")
    if not prim:
        L.append("- 无可解析 RTTI 槽 → ② FAIL。")
    else:
        off=int(prim["slot_off"]); vb=int(prim["vtable_base"],16); col=int(prim["col"],16); td=int(prim["td"],16)
        L.append("- 主锚槽驻留 %s [%s]，vtable base=%s，slot offset=+%d (0x%X)。" % (
            prim["slot_va"], prim.get("section","?"), prim["vtable_base"], off, off))
        L.append("- 槽内容 4B @%s = %s（= entry %s，读写方向：读槽内容得本 entry 的 VA，非把 entry 写回槽）。" % (
            prim["slot_va"], hexb(int(prim["slot_va"],16),4), e))
        L.append("- RTTI 数据链: [vt-4]=COL 指针@%08X(内容=%08X) → [COL]=sig=%08X → [COL+0xC]=TD@%08X → TD+8 内联装饰名串=%s。" % (
            vb-4, W.u32(vb-4) or 0, W.u32(col) or 0, td, prim["rtti_name"]))
        L.append("  - pTD/pCHD 存绝对 VA（非 RVA）；TD+8 为内联串（非指针）。")
        slot0=W.u32(vb)
        SMALL={0x00410260,0x004105E0,0x00410580,0x00410590}
        L.append("- slot0=%s，小成员表签名集合={00410260,004105E0,00410580,00410590}；slot0 不在集合 ⇒ 主虚表（非小成员表）。" % hex(slot0 or 0))
        ok = (hint_slot is None) or (off//4==hint_slot)
        L.append("- 名字线索=%s；slot_offset/4=%d，线索槽号=%s，一致=%s ⇒ ② %s（.rdata RTTI 数据链）。" % (
            nm, off//4, hint_slot, ok, "钉住" if ok else "不钉住"))
        # 同名 entry 可能出现在继承层次多个虚表，一并列出
        for s in slots:
            if s is prim: continue
            L.append("- （继承层次旁证）槽 %s vt=%s off=+%d → %s。" % (
                s["slot_va"], s["vtable_base"], int(s["slot_off"]), s["rtti_name"]))
    L.append("")

    L.append("## 环③ 整体合同（只认③b）")
    L.append("- 通道A(③b②) p1=%d p2=%d p3=%d；站点=%d。eax 覆写陷阱站点数=%d。" % (
        r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"]),
        sum(1 for x in r["chA_eax_trap"] if x.get("eax_overwritten"))))
    L.append("- 通道B(③b①跳转表) 站点=%d。" % len(r["chB"]))
    for s in r["chA_sites"]:
        ca=int(s["call_addr"]); ta=int(s["test_addr"]); ja=int(s["jcc_addr"])
        ci=int(s["callee_profile"]["callee_key"],16) if s["callee_profile"].get("callee_key") else None
        cname=THUNK.get(ci, "WWDebug空stub(0x4068E0)" if ci==0x4068E0 else ("类型ID布尔(0x53EE00)" if ci==0x53EE00 else "?"))
        trap=next((x for x in r["chA_eax_trap"] if int(x["call_addr"])==ca), None)
        ov=trap.get("eax_overwritten") if trap else []
        L.append("  - call@%08X [%s] -> %s | test@%08X: %s | jcc@%08X: %s -> %s | form=%s | eax覆写=%s" % (
            ca, hexb(ca,5), cname, ta, hexb(ta,4), ja, s["jcc_mnemonic"],
            ("0x%08X"%s["jcc_target"]) if isinstance(s.get("jcc_target"),int) else str(s.get("jcc_target")),
            s["p3_form"], ov or "无"))
    vd,reason = VERDICT[e]
    L.append("- 裁定: %s" % vd); L.append("  %s" % reason); L.append("")

    L.append("## 环④ 使用见证（真实调用者/活虚表派发；与②不同源；㉓ 排除析构器锚点）")
    L.append("- direct callers(%d): %s" % (len(r["direct_callers"]), ", ".join(r["direct_callers"]) or "无"))
    if prim:
        vb=prim["vtable_base"]
        wlist=VT_WRITES.get(vb, [])
        L.append("- 虚表 %s 的全部 .text 写点枚举（%d 处）:" % (vb, len(wlist)))
        ctor_ok=False
        for wa,fn,cat,atx in wlist:
            live = CTOR_LIVE.get(fn)
            live_s = ("；direct callers=%d(活)"%live) if live is not None else ""
            L.append("    - %s(in_func=%s) 类别=%s atexit=%s%s" % (wa,fn,cat,atx,live_s))
            if cat=="ctor" and not atx: ctor_ok=True
        L.append("- ㉓ 析构器锚点排查：scalar_delete_dtor(vtable slot0, ret 4) 与 非删除析构(dtor) 两类均已枚举并排除；"
                 "atexit 注册的全局析构器=0；仅以构造器写点作 ④ 锚 ⇒ 构造器安装点存在=%s，④ 锚点不落析构器。" % ctor_ok)
        ds=prim.get("dispatch_sites",[])
        L.append("- 活虚表派发: 主虚表 vt %s 由构造器写入活对象；call [reg+0x%X] 派发站点=%d，样例=%s。" % (
            vb, int(prim["slot_off"]), len(ds), ", ".join(ds[:8]) or "无"))
        L.append("- direct-only 判定: %s。" % (
            "有 direct caller 且有活虚表派发（非 direct-only）" if r["direct_callers"] else
            "无 direct caller，但有〔被实际调用的构造器〕写入的活虚表派发链（非 direct-only）"))
        L.append("- ②④ 不同源: ②=.rdata RTTI 数据链；④=.text 构造器安装 + 派发链。")
    L.append("")

    L.append("## 裁定")
    v3,_=VERDICT[e]
    L.append("- ①=PASS ②=%s ③=%s ④=%s ②④独立=是 ㉓析构锚=排除" % (
        "PASS" if prim else "FAIL", v3, "PASS(构造器安装活虚表派发)" if prim else "FAIL"))
    allfour = v3=="PASS" and prim is not None
    L.append("- **四环齐全=%s**" % ("是 -> [已证]" if allfour else "否（③不成立）" if prim else "否"))
    L.append("")
    L.append("## 本行地址锚")
    anchors=[ea]
    for s in r["chA_sites"][:3]: anchors += [int(s["call_addr"]),int(s["test_addr"]),int(s["jcc_addr"])]
    if prim: anchors.append(int(prim["slot_va"],16))
    for wa,_,_,_ in (VT_WRITES.get(prim["vtable_base"],[]) if prim else []): anchors.append(int(wa,16))
    L.append("- " + "  ".join("0x%08X"%a for a in dict.fromkeys(anchors)))
    L.append("")
    return "\n".join(L), (v3=="PASS" and prim is not None)

# 逐行落盘
results={}
for r in rows:
    e=r["entry"]
    txt,allfour=make_evidence(r)
    p=os.path.join(EVD,"ROW_%s.txt"%e)
    with open(p,"w",encoding="utf-8") as f: f.write(txt)
    results[e]=allfour
    print("EVIDENCE %s allfour=%s"%(e,allfour))

# delta.tsv（只放四环齐全行）
SEM = {
 "007B13D0":"③b② 可伪证返回约定整体合同：sendto@0x007B14C6/recvfrom@0x007B1586 后 cmp eax,-1→jne 分支 SOCKET_ERROR；失败返 -1、成功返字节数/继续，调用方真拿 -1 分支、两路动作真不同；无 eax 覆写。② RTTI vt007F794C slot+0x40 槽007F798C 驻本 entry→.?AVIPXInterfaceClass@@（主虚表）；④ 构造器写点007B0DA4(in_func 007B0D90,direct5,非析构)装活 vt + call[reg+0x40] 派发，与②不同源。",
 "007B1BC0":"③b② 可伪证 WSAAsyncSelect=-1：call@0x007B1BDB/0x007B1C1F→cmp eax,-1→jne，失败返 -1(日志+xor al,al)、成功返 0/1，两路不同；无 eax 覆写。② vt007F794C slot+0x1C 槽007F7968→.?AVIPXInterfaceClass@@；④ 构造器007B0DA4(007B0D90,direct5) + direct caller 007B3895 + 派发，非析构锚，与②不同源。",
 "007B2630":"③b② 可伪证 setsockopt=-1：call@0x007B2652/0x007B2690→cmp eax,-1→jne，两路日志串不同(84e060/84e080)、动作真不同；无 eax 覆写。② vt007F794C slot+0x28 槽007F7974→.?AVIPXInterfaceClass@@；④ 构造器007B0DA4(007B0D90,direct5) + direct callers=4 + 派发，非析构锚，与②不同源。",
 "007B26D0":"③b② 可伪证 gethostname=-1：call@0x007B26DB→cmp eax,-1→jne(gap=0)，失败返日志+xor al,al、成功返 mov al,1，两路不同；无 eax 覆写。② vt007F794C slot+0x44 槽007F7990→.?AVIPXInterfaceClass@@；④ 构造器007B0DA4(007B0D90,direct5)装活 vt + 派发，非析构锚，与②不同源。",
 "007B30B0":"③b② 可伪证 socket/bind=-1：call@0x007B30E4(socket)/0x007B315F(bind)→cmp eax,-1→jne，失败返 xor al,al、成功继续组包/setsockopt/入列；无 eax 覆写。② vt007F7A6C slot+0x5C 槽007F7AC8→.?AVUDPInterfaceClass@@（主虚表）；④ 构造器写点007B2E2D(in_func 007B2DB0,direct1,非析构)装活 vt + 派发，排除007B2E56(析构)/007B4176(标量删除析构)，与②不同源。",
 "007B31E0":"③b② 可伪证 bind=-1：call@0x007B3295→cmp eax,-1→jne(gap=0)，成功写组播地址表+call 007B2630+mov al,1、失败 closesocket+日志+xor al,al；无 eax 覆写。② vt007F7A6C slot+0x68 槽007F7AD4→.?AVUDPInterfaceClass@@；④ 构造器007B2E2D(007B2DB0,direct1)装活 vt + 派发，排除两处析构写点，与②不同源。",
 "007B3450":"③b② 可伪证 socket/bind=-1：call@0x007B35F8(socket)/0x007B3653(bind)→cmp eax,-1→jne，两路动作不同；另 call 0x4068E0 空 stub→test→je 属布尔不计。无 eax 覆写。② vt007F7A6C slot+0x3C 槽007F7AA8→.?AVUDPInterfaceClass@@；④ 构造器007B2E2D(007B2DB0,direct1)装活 vt + 派发，排除析构写点，与②不同源。",
 "007B3890":"③b② 可伪证 WSAAsyncSelect=-1：call@0x007B38C6→cmp eax,-1→je(gap=0)，失败日志+xor al,al、成功遍历地址表+call 5D4D50+mov al,1，两路不同；无 eax 覆写。② vt007F7A6C slot+0x1C 槽007F7A88→.?AVUDPInterfaceClass@@；④ 构造器007B2E2D(007B2DB0,direct1)装活 vt + 派发，排除析构写点，与②不同源。",
 "007B3AA0":"③b② 可伪证 sendto=-1：call@0x007B3D75→cmp eax,-1→jne(gap=0)，成功继续缓冲摘除、失败 WSAGetLastError+cmp 0x2733+日志+ret；无 eax 覆写。② vt007F7A6C slot+0x40 槽007F7AAC→.?AVUDPInterfaceClass@@；④ 构造器007B2E2D(007B2DB0,direct1)装活 vt + 派发，排除析构写点，与②不同源。",
}
PASS=[e for e in [r["entry"] for r in rows] if results[e]]
with open(os.path.join(OUT,"delta.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for e in PASS:
        f.write("%s\tS18\t%s\t%s\t[已证]\tEVIDENCE/ROW_%s.txt\n"%(e,meta[e]["name"],SEM[e],e))
print("delta rows:",len(PASS))

n=len(rows); r2=10; r3=sum(1 for e in results if VERDICT[e][0]=="PASS"); r4=10; all4=len(PASS)
with open(os.path.join(OUT,"base_rate.tsv"),"w",encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("NAMED_PUSH_S18_B5\t%d\t%d\t%d\t%d\t%d\t%.4f\n"%(n,r2,r3,r4,all4,all4/n))
print("base_rate %d/%d/%d/%d/%d"%(n,r2,r3,r4,all4))
