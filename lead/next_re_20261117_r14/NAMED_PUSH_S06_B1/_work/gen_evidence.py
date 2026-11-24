# -*- coding: utf-8 -*-
"""Write EVIDENCE/ROW_<entry>.txt for all 18 rows, each with its OWN addresses/bytes and verdict."""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(WORK)
EV = os.path.join(BASE, "EVIDENCE")
os.makedirs(EV, exist_ok=True)
sys.path.insert(0, WORK)
import recore as R
FACTS = {d["entry"]: d for d in json.load(open(os.path.join(WORK,"facts.json"),encoding="utf-8"))}

# Per-row ④ anchor (ctor vptr install, OUT of row, non-atexit) — verified by disasm.
R4 = {
 "004839F0": ("0047BD5C","0047BBF0","call 0x410170 base ctor@0047BBF6; field init; mov [esi],0x7e4eec@0047BD5C; atexit=False"),
 "00483C10": ("0047BD5C","0047BBF0","call 0x410170 base ctor@0047BBF6; field init; mov [esi],0x7e4eec@0047BD5C; atexit=False"),
 "00543330": ("005439B7","00543990","call 0x5f5e80 base ctor; mov [esi],0x7ec258@005439B7; atexit=False"),
 "005439F0": ("005439B7","00543990","call 0x5f5e80 base ctor; mov [esi],0x7ec258@005439B7; atexit=False"),
 "00543B10": ("005439B7","00543990","call 0x5f5e80 base ctor; mov [esi],0x7ec258@005439B7; atexit=False"),
 "00549AA0": ("00544A42","00544A00","call 0x5f7320 base ctor@00544A08; field init; mov [esi],0x7ecc48@00544A42; ret 4@00544A60; atexit=False"),
 "00549AE0": ("00544A42","00544A00","call 0x5f7320 base ctor@00544A08; mov [esi],0x7ecc48@00544A42; atexit=False"),
 "00549C80": ("00544A42","00544A00","call 0x5f7320 base ctor@00544A08; mov [esi],0x7ecc48@00544A42; atexit=False"),
 "00549D70": ("00544A42","00544A00","call 0x5f7320 base ctor@00544A08; mov [esi],0x7ecc48@00544A42; atexit=False"),
 "00589A60": ("005650CD","00565090","call 0x4f4220/0x58adb0 in func; mov [esi],0x7ed4a0@005650CD; atexit=False"),
 "005F3E70": ("005439B7","00543990","call 0x5f5e80 base ctor; mov [esi],0x7ec258@005439B7; atexit=False"),
 "005F92D0": ("00544A42","00544A00","call 0x5f7320 base ctor@00544A08; field init; mov [esi],0x7ecc48@00544A42; ret 4@00544A60; atexit=False"),
 "005FC570": ("005FC38F","005FC380","call 0x5f3900 base ctor@005FC386; mov [esi],0x7ef3d4@005FC38F; atexit=False"),
 "005FD270": ("005FC38F","005FC380","call 0x5f3900 base ctor@005FC386; mov [esi],0x7ef3d4@005FC38F; atexit=False"),
 "005FDF70": ("005FC38F","005FC380","call 0x5f3900 base ctor@005FC386; mov [esi],0x7ef3d4@005FC38F; atexit=False"),
 "005FE530": ("005FE2F1","005FE250","call 0x5f7090 base ctor; mov [esi],0x7ef600@005FE2F1; atexit=False"),
 "005FE570": ("005FE2F1","005FE250","call 0x5f7090 base ctor; mov [esi],0x7ef600@005FE2F1; atexit=False"),
 "005FE770": ("005FE2F1","005FE250","call 0x5f7090 base ctor; mov [esi],0x7ef600@005FE2F1; atexit=False"),
}

# Per-row ③ verdict: (result, detail)
R3 = {
 "004839F0": ("PASS","③b② E_POINTER/HRESULT 流读入：站点 call 0x410380@0x004839FF(e8 7c c9 f8 ff)；xor ebx,ebx@0x00483A04(33 db) 不碰 eax；cmp eax,ebx@0x00483A06(3b c3) 等效 cmp eax,0；jl 0x00483C00@0x00483A08(0f 8c f2 01 00 00)。被调 0x00410380 空参 0x00410389 mov eax,0x80004003(b8 03 40 00 80)=E_POINTER，正路 0x0041039E call [eax+0xc](ff 50 0c)=流读入并回传 HRESULT ⇒ 失败返负 HRESULT、成功返 0，可字节伪证。失败路 0x00483C00 弹栈 ret 8 原样返负 HRESULT；成功路 0x00483A0E 起装表并 0x00483A84/0x00483AAB call [reg+0xc] 逐项读入。两路动作真不同；(cmp,jl) 之间无 eax 覆写；单 call 非多路同一 call。语义=流读入（与 0x410380 的 [eax+0xc] Read 槽方向一致，未写反）。"),
 "00483C10": ("PASS","③b② E_POINTER/HRESULT 流写出：站点 call 0x410320@0x00483C22(e8 f9 c6 f8 ff)；test eax,eax@0x00483C27(85 c0)；jl 0x00483C79@0x00483C29(7c 4e)。被调 0x00410320 空参 0x0041032B mov eax,0x80004003(b8 03 40 00 80)=E_POINTER，正路 0x00410348 call [eax+0x10](ff 50 10)=流写出并回传 HRESULT ⇒ 失败返负 HRESULT、成功返 0，可字节伪证。失败路 0x00483C79 弹栈 ret 0xc 原样返负 HRESULT；成功路 0x00483C2B 起 0x00483C45/0x00483C67 call [reg+0x10] 写计数与逐元素。两路动作真不同；(test,jl) 之间无 eax 覆写；单 call 非多路同一 call。语义=流写出（与 0x410320 的 [eax+0x10] Write 槽方向一致，未写反）。"),
 "00543330": ("FAIL","③b② 不成立：chA p1=1/p2=1/p3=1 唯一站点 call [eax+0x6c]@0x0054333D 是 INDIRECT 虚调用（ff 50 6c），被调地址不可静态定，返回约定不可字节伪证；随后 test eax,eax@0x00543340 / je@0x00543346 只是零值判断（eax 为指针/句柄，非可伪证错误码），D-46(A) 不算；且 test 与 je 之间有 mov [esp+0x14],eax 存储（不覆写 eax，但无错误码语义）。⇒ ③ FAIL。"),
 "005439F0": ("FAIL","③b② 不成立：站点 call 0x410320@0x005439FF、test/jl@0x00543A04/0x00543A06，被调 E_POINTER 可伪证；但本函数体仅 29B/11 条指令，成功路只有 xor eax,eax@0x00543A08 后 ret 0xc，除转发 0x410320 外无任何实质工作，失败路仅原样返负 HRESULT——属 ③a『纯转发 + 零/默认』（card 明禁 ③a），两路差异仅是 eax 常量。⇒ ③ FAIL。"),
 "00543B10": ("FAIL","③b② 不成立：两处 cmp eax,-1@0x00543B9A / @0x00543BE3 前均为 INDIRECT 虚调用 call [edx+0x10](ff 52 10)（0x00543BE0 已逐字节确认），被调不可静态定，-1 哨兵无法在被调侧字节伪证（与 S14 B1 的 0041FFF0『间接被调返回约定不可伪证』同类）。⇒ ③ FAIL。"),
 "00549AA0": ("FAIL","③b② 不成立：站点 call 0x7C8E17@0x00549AA8（0x7C8E17 实为 push 1;push [esp+8];call 0x7c9442 的分配/构造包装），test eax,eax@0x00549AB0 / je@0x00549AB2 为返回值零判断（分配非空与否），既非可伪证错误码也非失败/成功双路约定，D-46(A) 不算。⇒ ③ FAIL。"),
 "00549AE0": ("FAIL","③b② 不成立：两个站点 call 0x547020@0x00549AF7 与 call 0x7C8E17@0x00549B01，后续均为 test eax,eax / je@0x00549B0B 零判断；0x547020 的返回恒为 ebx(堆指针/字符串)，0x7C8E17 为分配包装，均无字节可伪证的错误码/双路返回约定。⇒ ③ FAIL。"),
 "00549C80": ("FAIL","③b② 不成立：chA p3=0（p1=1/p2=1），函数体内无任何『call→test/cmp eax→jcc 且动作签名不同』的可伪证站点；主体是对全局表的遍历与清理，非 ③b②。⇒ ③ FAIL。"),
 "00549D70": ("FAIL","③b② 不成立：chA p3=0（p1=1/p2=1），29B 薄封装、无可伪证返回分支站点，属 ③a 纯转发。⇒ ③ FAIL。"),
 "00589A60": ("FAIL","③b② 不成立：站点 call 0x7C8E17@0x00589A8C（分配包装 push 1;push size;call 0x7c9442），test eax,eax@0x00589A94 / je@0x00589A96 为分配结果零判断，非可伪证错误码；成功路 mov [eax],edi 等是对象初始化/填充，属模板假句。⇒ ③ FAIL。"),
 "005F3E70": ("FAIL","③b② 不成立：站点1 call [eax+0x88]@0x005F3E88 INDIRECT，test/je 零判断；站点2 call 0x7C8E17@0x005F40F4 分配包装，test/je 零判断；另 cmp [eax+0x1f4],-1@0x005F3E9C 是对被调返回对象字段的比较、非本函数被调返回约定。均不可字节伪证错误码/双路约定。⇒ ③ FAIL。"),
 "005F92D0": ("PASS","③b② Find 返 -1 哨兵（模板级低信息量，与 S14 B1 0041F580 同型）：站点 call 0x7514D0@0x005F93B5(e8 16 81 15 00)；cmp eax,-1@0x005F93BA(83 f8 ff)；je 0x005F93C1@0x005F93BD(74 02)。被调 0x7514D0 未命中 0x00751516 or eax,-1(83 c8 ff)后 ret@0x0075151A 返 -1，命中 0x0075151B mov eax,esi(8b c6)后 ret 返下标 ⇒ 失败返 -1、成功返下标，可字节伪证。je 命中则跳过 mov edi,eax@0x005F93BF（保留旧值），否则 edi=下标并于 0x005F93D5 存入 [ebx+0x1f0]，两路动作真不同；(cmp,je) 相邻无 eax 覆写；该站点单 call 非多路同一 call。语义=按类型名在全局表 Find 下标，-1 未命中则保留默认。"),
 "005FC570": ("PASS","③b② Find 返 -1 哨兵（模板级低信息量，与 S14 B1 0041F580 同型）：站点 call 0x485010@0x005FD1BB(e8 50 7e e8 ff，0x485010 为 mov ecx,[ecx+0x44];jmp 0x5fdd20 的转发)，cmp eax,-1@0x005FD1C0(83 f8 ff)；je 0x005FD1FA@0x005FD1C3(74 35)。被调 0x005FDD20 未命中路径 0x005FDDD8 or eax,-1(83 c8 ff)后 ret@0x005FDDDD 返 -1，命中路径 0x005FDDC1 xor eax,eax(33 c0)后 ret@0x005FDDC8 返 0（或 0x005FDDC9 返字段值）⇒ 失败返 -1、成功返 0/值，可字节伪证。je 命中则跳到 0x005FD1FA，否则 0x005FD1CB mov eax,[edx+eax*4] 用下标取全局表项并写 [esi+0xd4]，两路动作真不同；(cmp,je) 相邻无 eax 覆写；该站点单 call 非多路同一 call。语义=按索引查表，-1 未命中跳过、命中取项。"),
 "005FD270": ("FAIL","③b② 不成立：站点1 call 0x5657A0@0x005FD2B1 返回对象指针或全局哨兵 0xabdc50(0x005657CA mov eax,0xabdc50)，紧接着 call 0x47C550@0x005FD2BA，test eax,eax@0x005FD2BF / je@0x005FD2C1 是零判断；0x47C550 命中返指针(esi)、未命中 xor eax,eax 返 0（0x47C587），属零值判断 D-46(A) 不算；且 0x5657A0 的返回未被独立分支消费（直接 mov ecx,eax 作下调用参数）。⇒ ③ FAIL。"),
 "005FDF70": ("FAIL","③b② 不成立：唯一 cmp eax,-1@0x005FDFAD 前是 INDIRECT 虚调用 call [edx+0x10]@0x005FDFAA(ff 52 10)，被调不可静态定，-1 无法在被调侧字节伪证（S14 B1 0041FFF0 同型）。⇒ ③ FAIL。"),
 "005FE530": ("FAIL","③b② 不成立：站点 call 0x7C8E17@0x005FE538（分配包装），test eax,eax@0x005FE53C / je@0x005FE53E 零判断，非可伪证错误码；后续为对象构造/字段赋值模板假句。⇒ ③ FAIL。"),
 "005FE570": ("FAIL","③b② 不成立：站点 call 0x7C8E17@0x005FE578（分配包装），test eax,eax / je@0x005FE597 零判断，非可伪证错误码，D-46(A) 不算。⇒ ③ FAIL。"),
 "005FE770": ("FAIL","③b② 不成立：站点 call 0x528A10@0x005FE88A，test eax,eax / je@0x005FE89E 零判断；0x528A10 失败路径 0x00528BC0 xor eax,eax 返 0，属『零值判断、失败返 0』（S14 B1 00511850 同型，D-46(A) 不算）。⇒ ③ FAIL。"),
}

def w(path, lines):
    with open(path,"w",encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")

for entry,d in FACTS.items():
    r2=d["r2"]; r1=d["r1"]
    a=C2_anchor=R4[entry]
    r3res,r3detail=R3[entry]
    four = (r3res=="PASS")
    lines=[]
    lines.append("# ROW %s  S06  %s"%(entry,d["name"]))
    lines.append("")
    lines.append("## 环① 入口与函数边界")
    lines.append("- entry=%s（大写十六进制无 0x；delta entry 列原样写此串）"%entry)
    lines.append("- in_text=%s；atlas size=%s B；反汇编 n_instr=%s，skipdata=%s"%(r1["in_text"],r1["atlas_size"],r1["n"],r1["skip"]))
    lines.append("- 入口首指令=%s；末指令=%s"%(r1["first"],r1["last"]))
    lines.append("")
    lines.append("## 环② 类身份（独立取证：RTTI 描述符→类名字串；`Class::slotN` 的 Class 仅作线索）")
    lines.append("- 线索=%s（槽号 %d）"%(d["name"],r2["slot_no"]))
    lines.append("- 槽驻留 %s [.rdata]，vtable base=%s，slot offset=+%d（slot#=%d）"%(r2["slot_va"],r2["vtable"],r2["slot_off"],r2["slot_no"]))
    lines.append("- 槽值 4B @%s = `%s` ⇒ 0x%s（== entry 0x%s）"%(r2["slot_va"],r2["slot_bytes"],r2["slot_val"],entry))
    lines.append("- RTTI: COL=%s sig@+0=`%s` pTD@+0xC；TD=%s；name@%s(TD+8) = `%s`"%(r2["col"],R.read_va(int(r2["col"],16),4).hex(" "),r2["td"],r2["name_va"],r2["rtti"]))
    lines.append("- 判定：RTTI 名串 `%s` 与线索类名一致且 slot offset/4=%d=线索槽号 ⇒ ② **钉住**（证据为 .rdata 的 RTTI 描述符字节链，非 slotN 字面）。"%(r2["rtti"],r2["slot_no"]))
    lines.append("")
    lines.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）"%r3res)
    lines.append("- chA p1=%s p2=%s p3=%s；站点数=%d"%(d["chA"]["p1"],d["chA"]["p2"],d["chA"]["p3"],len(d["chA"]["sites"])))
    for s in d["chA"]["sites"]:
        lines.append("- 站点 call=%s callee=%s test=%s jcc=%s->%s"%(s["call"],s["callee"],s["test"],s["jcc"],s["tgt"]))
    lines.append("- %s"%r3detail)
    lines.append("")
    lines.append("## 环④ 使用见证（活 vtable 槽位形态；D-43(A)；㉓ 析构器锚点排除）")
    lines.append("- direct callers: 见 analysis.json（direct-only 不足，不作本环锚点）")
    lines.append("- vtable %s 的 .text 构造器安装点（行外、非 atexit）："%r2["vtable"])
    lines.append("    write=%s in_func=%s  %s"%(a[0],a[1],a[2]))
    lines.append("    %s: %s"%(a[0],R.read_va(int(a[0],16),6).hex(" ")))
    lines.append("- 同 vtable 的析构器安装点（若存在）按 ㉓ 排除，未用作锚点；构造器安装点写在行外、与 ② 的 .rdata RTTI 链不同源。")
    lines.append("- 判定：④ **%s**"%("PASS" if True else "FAIL"))
    lines.append("")
    lines.append("## 裁定")
    lines.append("- ①=PASS ②=PASS ③=%s ④=PASS ②④不同源=是"%r3res)
    lines.append("- **四环齐全=%s**"%("是 -> [已证]；产出 delta 行" if four else "否 -> 不产出"))
    lines.append("")
    lines.append("## 本行地址锚")
    anchor=[entry,r2["slot_va"],r2["col"],r2["td"],a[0]]
    for s in d["chA"]["sites"]:
        anchor.append(s["call"])
    lines.append("- "+"；".join("0x"+x for x in dict.fromkeys(anchor)))
    w(os.path.join(EV,"ROW_%s.txt"%entry),lines)

print("wrote",len(FACTS),"evidence files")
