# -*- coding: utf-8 -*-
"""生成 B5 的 delta.tsv（9 行四环齐全）/ base_rate.tsv。"""
import os, sys, json
WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(WORK, "..")
rows = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
meta = {r["entry"]: r for r in json.load(open(os.path.join(WORK,"b5_rows.json"), encoding="utf-8"))["selected"]}
by_entry = {r["entry"]: r for r in rows}

# 9 行四环齐全行的 one_line_semantics（③b② 可伪证返回约定 + ②④ 锚点 + 陷阱排查）
SEM = {
"007B13D0": "IPXInterfaceClass::slot16（③b② 可伪证返回约定整体合同：本体 sendto/recvfrom 后 cmp eax,-1→jne 分支 SOCKET_ERROR。call 0x7c89b0=sendto@0x007B14C6→cmp eax,-1@0x007B14CB(83 F8 FF)→jne@0x007B14CE，失败路 WSAGetLastError+cmp 0x2733+日志 0x84dea4、成功路继续缓冲队列摘除；call 0x7c89aa=recvfrom@0x007B1586→cmp eax,-1@0x007B158B→mov[esp+0x10],eax(不写 eax)→jne@0x007B1592，失败路 WSAGetLastError+日志+ret、成功路 test eax,eax 组包。失败返 SOCKET_ERROR=-1、成功返字节数/0，调用方真拿 -1 分支，属 Find 返-1/多值状态码可伪证类；无 eax 覆写陷阱；② vt 007F794C slot+0x40 槽 007F798C 驻本 entry、RTTI COL=0080EA60→TD=0084D8F8→.?AVIPXInterfaceClass@@、主虚表非小成员表；④ 活 vt 构造安装点 007B0DA4 mov[esi],0x7f794c(in_func 007B0D90,非 atexit/析构)、call[reg+0x40] dispatch=233(如 0040A728/00414CBB)，与②的 .rdata RTTI 链不同源）",
"007B1BC0": "IPXInterfaceClass::slot7（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c89bc=WSAAsyncSelect@0x007B1BDB→cmp eax,-1@0x007B1BE0→jne@0x007B1BE3，失败路 WSAGetLastError+日志 0x84dea4+xor al,al ret、成功路继续端口判定与第二次 WSAAsyncSelect；call WSAAsyncSelect@0x007B1C1F→cmp eax,-1@0x007B1C24→jne@0x007B1C27，成功路 mov al,1 ret、失败路日志 0x84de68+xor al,al ret。失败返 -1 成功返 0，两路返回值不同、调用方真拿 -1 分支，可伪证；无 eax 覆写陷阱；② vt 007F794C slot+0x1C 槽 007F7968 驻 entry、RTTI→.?AVIPXInterfaceClass@@(另 007F79D8→.?AVWinsockInterfaceClass@@)；④ 构造安装 007B0DA4(非 atexit)、dispatch=142，另有 direct caller 007B3895，与②不同源）",
"007B2630": "IPXInterfaceClass::slot10（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c89a4=setsockopt@0x007B2652→cmp eax,-1@0x007B2657→jne@0x007B265A，失败路 WSAGetLastError+日志 0x84e0d8+重试 setsockopt、成功路继续；call setsockopt@0x007B2690→cmp eax,-1@0x007B2695→pop esi(不写 eax)→jne@0x007B2699，两路日志串不同(0x84e060/0x84e080)、动作真不同。失败返 -1 成功返 0，可伪证；无 eax 覆写陷阱；② vt 007F794C slot+0x28 槽 007F7974 驻 entry、RTTI→.?AVIPXInterfaceClass@@(另 Winsock/UDP 同槽)；④ 构造安装 007B0DA4(非 atexit)、dispatch=138 + direct callers=4(007B13AB/007B31BC/007B32EA/007B36A1)，与②不同源）",
"007B26D0": "IPXInterfaceClass::slot17（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c89ce=gethostname@0x007B26DB→cmp eax,-1@0x007B26E0(83 F8 FF)→jne@0x007B26E3(gap=0)，失败路 WSAGetLastError+日志 0x84e134+xor al,al ret、成功路日志 0x84e110+mov al,1 ret。失败返 -1 成功返 0，两路返回值不同(1 vs 0)、调用方真拿 -1 分支，可伪证；无 eax 覆写陷阱；② vt 007F794C slot+0x44 槽 007F7990 驻 entry、RTTI→.?AVIPXInterfaceClass@@(另 Winsock/UDP 同槽)；④ 构造安装 007B0DA4(非 atexit)、dispatch=133，与②不同源）",
"007B30B0": "UDPInterfaceClass::slot23（③b② 可伪证 INVALID_SOCKET/SOCKET_ERROR=-1：call 0x7c899e=socket@0x007B30E4→cmp eax,-1@0x007B30E9→mov[esi+0x3f06c],eax(不写 eax)→jne@0x007B30F2，失败路 xor al,al ret、成功路继续 sockaddr 组包；call 0x7c8998=bind@0x007B315F→cmp eax,-1@0x007B3164→pop edi(不写 eax)→jne@0x007B3168，成功路 setsockopt+call 0x7B2630+入列、失败路 WSAGetLastError+日志 0x84e204+xor al,al ret。失败返 -1 成功返 0/句柄，可伪证；无 eax 覆写陷阱；② vt 007F7A6C slot+0x5C 槽 007F7AC8 驻 entry、RTTI COL=0080EBE0→TD=0084E1C0→.?AVUDPInterfaceClass@@；④ 构造安装 007B2E2D/007B2E56/007B4176(均非 atexit)、dispatch=166，与②不同源）",
"007B31E0": "UDPInterfaceClass::slot26（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c8998=bind@0x007B3295→cmp eax,-1@0x007B329A(83 F8 FF)→jne@0x007B329D(gap=0)，成功路写 [ebx+0x3f320]/[ebx+0x3f300] 入组播地址表+call 0x7B2630+mov al,1、失败路 call 0x7c8992=closesocket+日志 0x84e294+xor al,al ret。失败返 -1 成功返 0，两路动作/返回值真不同、调用方真拿 -1 分支，可伪证；无 eax 覆写陷阱；② vt 007F7A6C slot+0x68 槽 007F7AD4 驻 entry、RTTI→.?AVUDPInterfaceClass@@；④ 构造安装 007B2E2D/2E56/4176(非 atexit)、dispatch=51，与②不同源）",
"007B3450": "UDPInterfaceClass::slot15（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c899e=socket@0x007B35F8→cmp eax,-1@0x007B35FD→mov[edi+0x3f070],eax(不写 eax)→jne@0x007B3606，失败路 ret、成功路 htons/htonl+组地址+继续；call 0x7c8998=bind@0x007B3653→cmp eax,-1@0x007B3658→jne@0x007B365B，成功路 setsockopt+call 0x7B2630、失败路 call[vtable]+xor al,al ret。失败返 -1 成功返 0/句柄，可伪证。另有 call 0x4068E0(WWDebug 空 stub,eax 未定义)@0x007B34E0→test→je 属布尔不计，不参与③裁定；无 eax 覆写陷阱；② vt 007F7A6C slot+0x3C 槽 007F7AA8 驻 entry、RTTI→.?AVUDPInterfaceClass@@；④ 构造安装 007B2E2D/2E56/4176(非 atexit)、dispatch=119，与②不同源）",
"007B3890": "UDPInterfaceClass::slot7（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c89bc=WSAAsyncSelect@0x007B38C6→cmp eax,-1@0x007B38CB(83 F8 FF)→je@0x007B38CE(gap=0, je 表 eax==-1 进失败路)，失败路日志 0x84e3d0+xor al,al ret、成功路遍历地址表 [esi+0x3f330]+inc ebx/add edi,4+循环末 call 0x5D4D50+mov al,1 ret。失败返 -1 成功返 0，两路动作/返回值真不同、调用方真拿 -1 分支，可伪证；无 eax 覆写陷阱；② vt 007F7A6C slot+0x1C 槽 007F7A88 驻 entry、RTTI→.?AVUDPInterfaceClass@@；④ 构造安装 007B2E2D/2E56/4176(非 atexit)、dispatch=142，与②不同源）",
"007B3AA0": "UDPInterfaceClass::slot16（③b② 可伪证 SOCKET_ERROR=-1：call 0x7c89b0=sendto@0x007B3D75→cmp eax,-1@0x007B3D7A(83 F8 FF)→jne@0x007B3D7D(gap=0)，成功路继续 [esp+0x13] 标志与 [ebp+0x48] 缓冲队列摘除、失败路 WSAGetLastError+cmp 0x2733+日志 0x84e4b4+清理 ret。失败返 -1 成功返字节数/继续处理，调用方真拿 -1 分支，可伪证；无 eax 覆写陷阱；② vt 007F7A6C slot+0x40 槽 007F7AAC 驻 entry、RTTI→.?AVUDPInterfaceClass@@；④ 构造安装 007B2E2D/2E56/4176(非 atexit)、dispatch=233，与②不同源）",
}

PASS = list(SEM.keys())
with open(os.path.join(OUT,"delta.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for e in PASS:
        nm = meta[e]["name"]
        f.write("%s\tS18\t%s\t%s\t[已证]\tEVIDENCE/ROW_%s.txt\n" % (e, nm, SEM[e], e))
print("delta rows:", len(PASS))

n=len(rows); r2=10; r3=9; r4=10; all4=9
with open(os.path.join(OUT,"base_rate.tsv"),"w",encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("NAMED_PUSH_S18_B5\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (n,r2,r3,r4,all4,all4/n))
print("base_rate: %d/%d/%d/%d/%d rate=%.4f"%(n,r2,r3,r4,all4,all4/n))
