# -*- coding: utf-8 -*-
"""NAMED_PUSH_S07_B1 最终裁定与产物生成。逐行独立理由；四环齐全才进 delta。
只读 gamemd.exe；写域仅本批目录。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.dirname(WORK)
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)

rows = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))
ana  = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}

# 每行：ring2/3/4 + 独立理由 + ②/④ 锚点。③=PASS 全是可伪证返值约定。
D = {
"00421730": dict(r2=1,r3=1,r4=1,
  why2="slotva 007E32C4 驻 .rdata，vtable base=007E32A4，slot offset=+0x20(=slot#8，与名字 vslot8 的 8 一致)；"
       "[vt-4]=COL 007FB990(sig=0)→[COL+0xC]=TD 008182A8→TD+8 名串 .?AVAlphaShapeClass@@；"
       "vt[0]=00410260(MAIN 标志)，ctor 00420960 在 0042097C 写 [esi]=007E32A4=对象主表；② 由 RTTI+槽自洽独立钉死，非 slotN 字面。",
  why3="③b② PASS。析构本体 call [edx+0x10]@00421763(ff 52 10；edx=[88A0F0] 容器对象，活 vt=007E3238，vt+0x10=Find@00421A90，"
       "其 00421AAF 处 83 C8 FF=or eax,-1 字节伪证未命中返 -1 下标)→cmp eax,-1@00421766(83 F8 FF)→je@00421769(74 2D)→00421798，"
       "test/cmp 与 jcc 零间隔无 eax 覆写；命中路 00421771 cmp eax,[88A100] 边界 + 00421778 mov [88A100],ecx 非栈写 + "
       "00421780..00421796 前移循环 0042178A mov [ecx+eax*4-4],edx(89 54 81 FC 循环体内非栈写)+00421794 cmp 边界+00421796 jl 回边；"
       "另有第二容器 [B0F720] 同型(call 004217AC/Find 004E0550)。未命中 -1 跳过摘链 vs 命中压缩摘链，两路动作真不同；"
       "非 bool(下标约定多值)、非纯转发、非 malloc 模板、非多路同一 call(两个不同容器对象)。本行是标量删除析构体，"
       "按既有口径『析构函数体内容器 Find 返 -1 哨兵分支成立』计 ③b②。非流 I/O，无读写方向问题。",
  why4="vt 007E32A4 由行外真构造器 00420960 在 0042097C(c7 06 a4 32 7e 00)写对象 [esi] 装活表(00420965 call 0x410170 基类构造+字段初始化)；"
       "本体内 0042173D 写 [esi]=7E32A4 是析构器自装表，按 ㉓ 排除、未用作锚；[reg+0x20] 派发链在 .text(358 处)，与 ② 的 .rdata RTTI 链不同源。"),
"00435BE0": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E3BE4，vt=007E3AD0，offset=+276(=slot#69，与名字 vslot69 一致)；RTTI 007FC040→00818BE0→.?AVBuildingLightClass@@；"
       "vt[0]=00410260 主表；ctor 00435820 装活表；② 钉死。",
  why3="唯一 chA 站点 call 0x7C8E17@00435C95=operator new → test eax,eax → je：分配失败空指针判断，命中路无 ③b 域内可伪证错误码，"
       "属『分配包装零判断/对象初始化模板假句』(D-46(A)/三陷阱模板假句)。无可证多值返值约定、无 Find -1、无跳表/内存形状/循环非栈写。③ 不成立。",
  why4="vt 007E3AD0 行外 ctor 00435820@004358AF 装活表，[reg+0x114] 派发链 6 处，与 ② RTTI 链不同源；④ 独立成立但 ③ 未过不升级。"),
"004361D0": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E3B2C，vt=007E3AD0，offset=+92(=slot#23)；RTTI .?AVBuildingLightClass@@；vt[0]=00410260 主表；② 钉死。",
  why3="1827B/513 指令浮点光照计算函数。2 站点：call [eax+0x350]@00436668→TEST_EAX→je 为对象类型/空探测；"
       "call [eax+0x2c]@004367E6→cmp eax,1→jne 为类型==1 布尔态比较(imm=1 非多值错误码、被调间接不可取证返值)。"
       "大量 fmul/fadd/fstp 几何运算主体，无 falsifiable 错误码/返回约定、无每路可验跳转表。③ 不成立。",
  why4="vt 007E3AD0 行外 ctor 00435820@004358AF 装活表，[reg+0x5C] 派发链 166 处，与 ② 不同源；④ 成立但 ③ 未过。"),
"004370C0": dict(r2=1,r3=1,r4=1,
  why2="slotva 007E3AF0，vt=007E3AD0，offset=+0x20(=slot#8=vslot8)；RTTI 007FC040→00818BE0→.?AVBuildingLightClass@@；"
       "vt[0]=00410260 主表；ctor 00435820 装活表；② 钉死。",
  why3="③b② PASS。析构本体 call [edx+0x10]@00437107(edx=[8B4190]，活 vt=007E9C24，Find@004E9DB0，004E9DCF 处 83 C8 FF=or eax,-1)→"
       "cmp eax,-1@0043710A→je@0043710D→0043713C，零间隔无 eax 覆写；命中路 0043711C mov [8B41A0],ecx 非栈写 + "
       "00437124..0043713A 压缩循环 0043712E mov [ecx+eax*4-4],edx(89 54 81 FC 循环体内非栈写)+00437138 cmp 边界+0043713A jl 回边；"
       "未命中 -1 跳过摘链 vs 命中压缩，两路真不同；非 bool/模板/纯转发。析构体内容器 Find -1 按既有口径计 ③b②。非流 I/O。",
  why4="vt 007E3AD0 由行外真 ctor 00435820 在 004358AF 写活表；本体内 004370C4 析构自装表按 ㉓ 排除；[reg+0x20] 派发链 358 处(.text)，与 ② RTTI 链不同源。"),
"00491210": dict(r2=1,r3=1,r4=1,
  why2="slotva 007E5358，vt=007E5358，offset=+0(=slot#0)；RTTI 007FD3E8→0081DC98→.?AVConvertClass@@；"
       "vt[0]=00491210=本 entry(非 COM 根类主表，ctor 0048E740 在 0048E93B 写 [esi]=7E5358 即对象 offset0 主表)。"
       "紧邻 007E5318(.?AV?$DynamicVectorClass@PAVConvertClass@@@@)、007E5338( VectorClass ) 两个容器成员表按陷阱③明确排除，未当主表。"
       "类名 RTTI+槽号+槽值自洽，② 独立钉死。",
  why3="③b② PASS。析构本体 call [eax+0x10]@00491261(eax=[89ECF8] 容器对象，活 vt=007E5318，Find@0049B0B0，0049B0CF 处 83 C8 FF=or eax,-1)→"
       "cmp eax,-1@00491264→je@00491267→00491296，零间隔无 eax 覆写；命中路 00491276 mov [89ED08],ecx 非栈写 + "
       "0049127E..00491294 压缩循环 00491288 mov [ecx+eax*4-4],edx(89 54 81 FC 循环体内非栈写)+00491292 cmp+00491294 jl 回边；"
       "未命中 -1 跳过 vs 命中压缩两路真不同；非 bool/模板。析构体内容器 Find -1 按既有口径计 ③b②。非流 I/O。",
  why4="vt 007E5358 由行外真 ctor 0048E740 在 0048E93B(c7 06 58 53 7e 00)写对象 [esi] 装活表；本体内 00491214 析构自装表按 ㉓ 排除；"
       "[reg+0] 派发链在 .text，与 ② .rdata RTTI 链不同源。"),
"004BAD80": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E8630，vt=007E85D4，offset=+92(=slot#23)；RTTI 00800260→008205D8→.?AVDSurface@@；"
       "vt[0]=004C1AC0(DSurface 非 COM 根类主表，ctor 004BA5A0 装活表)；② 钉死。",
  why3="315B/117 指令，chA p1=5/p2=4/p3=0：5 处 call→test 的被调均无多值可伪证返值约定，两路动作签名不足；"
       "2 个 direct caller(006421DB/00642396)不改变本体无 ③b 的事实；无跳表/内存形状/循环非栈写。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0@004BA5D0 装活表，[reg+0x5C] 派发链 166 处；④ 成立但 ③ 未过。"),
"004BB0D0": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E85E0，vt=007E85D4，offset=+12(=slot#3)；RTTI .?AVDSurface@@；主表非小成员表；② 钉死。",
  why3="唯一 p3 站点：间接 call→cmp eax,0x887601c2(单一定值 magic)→jne。该常量既非多值状态码、亦非 Find 返 -1 下标约定；"
       "被调为间接虚调用无法字节取证其返值语义；跨 0x887601c2 的单一 magic 比较不构成可伪证错误码/返回约定。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 400 处；④ 成立但 ③ 未过。"),
"004BB620": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E85E4，vt=007E85D4，offset=+16(=slot#4)；RTTI .?AVDSurface@@；② 钉死。",
  why3="唯一 p3 站点：间接 call→cmp eax,0x887601c2(单一定值 magic)→jne；同 004BB0D0 的判由——非多值状态码、非 Find -1 下标、"
       "间接被调不可字节取证返值，magic 常量比较不构成 ③b 可伪证返回约定。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 400 处；④ 成立但 ③ 未过。"),
"004BB830": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E85F0，vt=007E85D4，offset=+28(=slot#7)；RTTI .?AVDSurface@@；② 钉死。",
  why3="711B/233 指令，chA p1=2/p2=1/p3=0：call→test 的被调无可伪证多值返值、两路动作签名相同；无跳表/内存形状/循环非栈写。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 142 处；④ 成立但 ③ 未过。"),
"004BF750": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E8664，vt=007E85D4，offset=+144(=slot#36)；RTTI .?AVDSurface@@；② 钉死。",
  why3="1499B/483 指令，chA p1=1/p2=1/p3=0：唯一 call→test 路径被调无可伪证返值常量、动作签名不足；无 ③b①/③/④ 形态。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 46 处；④ 成立但 ③ 未过。"),
"004C0750": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E8620，vt=007E85D4，offset=+76(=slot#19)；RTTI .?AVDSurface@@；② 钉死。",
  why3="chA p3 站点：间接 call→TEST_EAX→je→直接 ret(004C07??→004C1090)；被调间接不可取证、TEST_EAX je 为空指针/布尔探测，"
       "非多值可伪证返回约定；余站点 p3=0。无 Find -1/跳表/循环非栈写。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 123 处；④ 成立但 ③ 未过。"),
"004C0E30": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E8624，vt=007E85D4，offset=+80(=slot#20)；RTTI .?AVDSurface@@；② 钉死。",
  why3="chA p3 站点：间接 call→TEST_EAX→je→直接 ret(004C0E??→004C16B6)；同 slot19 判由——TEST_EAX je 空/布尔探测，"
       "间接被调无可伪证多值返值；余站点 p3=0。无 ③b 整体合同。③ 不成立。",
  why4="vt 007E85D4 行外 ctor 004BA5A0 装活表，派发链 35 处；④ 成立但 ③ 未过。"),
"005550C0": dict(r2=1,r3=1,r4=1,
  why2="slotva 007ED03C，vt=007ED028，offset=+20(=slot#5)；RTTI 008050F0→00829C00→.?AVLightSourceClass@@；"
       "vt[0]=00410260 主表；ctor 00554760 装活表；② 钉死。",
  why3="③b② PASS，流读入(方向未写反)。call 0x410380@005550CB(e8 b0 b2 eb ff)；被调空参 00410389 mov eax,0x80004003=E_POINTER，"
       "正路 0041039E call [eax+0xc]=IStream::Read 槽(读入方向字节证实)。本体 test eax,eax@005550D0(85 c0)→jl@005550D2(7c 2d)→00555101；"
       "jl 成立路跳过清零、原样返回负 HRESULT；不成立路 call 0x4101c0 后逐字段读回并重装 4 张 vt(005550E4..005550F8)后 xor eax,eax 返 0。"
       "失败返负值/成功返 0、调用方真拿它分支、两路动作不同、零间隔无 eax 覆写；非 bool(负值多值错误码)。",
  why4="vt 007ED028 由行外真 ctor 00554760 在 005547A0(c7 06 28 d0 7e 00)写活表(00554763 call 0x410170 基类构造)；"
       "[reg+0x14] 派发链 273 处(.text)，与 ② .rdata RTTI 链不同源。"),
"00555110": dict(r2=1,r3=1,r4=1,
  why2="slotva 007ED040，vt=007ED028，offset=+24(=slot#6)；RTTI .?AVLightSourceClass@@；vt[0]=00410260 主表；② 钉死。",
  why3="③b② PASS，流写出(方向未写反)。call 0x410320@0055511F(e8 fc b1 eb ff)；被调空参 0041032B mov eax,0x80004003=E_POINTER，"
       "正路 call [eax+0x10]=IStream::Write 槽(写出方向字节证实)。本体 test eax,eax@00555124→jl@00555126(7c 02)→0055512A；"
       "jl 路原样返回负 HRESULT，非 jl 路 xor eax,eax@00555128 返 0。失败返负/成功返 0、真分支、两路不同、零间隔无 eax 覆写，非 bool。",
  why4="vt 007ED028 行外 ctor 00554760@005547A0 装活表；[reg+0x18] 派发链 367 处；与 ② 不同源。"),
"00555150": dict(r2=1,r3=1,r4=1,
  why2="slotva 007ED048，vt=007ED028，offset=+0x20(=slot#8)；RTTI .?AVLightSourceClass@@；vt[0]=00410260 主表；② 钉死。",
  why3="③b② PASS。析构本体 call [edx+0x10]@0055518A(edx=[ABCA10]，活 vt=007ECF7C，Find@005554F0，0055550F 处 83 C8 FF=or eax,-1)→"
       "cmp eax,-1@0055518D→je@00555190→005551BF，零间隔无 eax 覆写；命中路 0055519F mov [ABCA20],ecx 非栈写 + "
       "005551A7..005551BD 压缩循环 005551B1 mov [ecx+eax*4-4],edx(89 54 81 FC 循环体内非栈写)+005551BD jl 回边；"
       "未命中 -1 跳过 vs 命中压缩两路真不同；非 bool/模板。析构体内容器 Find -1 按既有口径计 ③b②。非流 I/O。",
  why4="vt 007ED028 行外 ctor 00554760@005547A0 装活表；本体内 00555156 析构自装表按 ㉓ 排除；[reg+0x20] 派发链 358 处，与 ② 不同源。"),
"00565C10": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E6184，vt=007E6114，offset=+112(=slot#28)；RTTI 007FFCB8→00816BD8→.?AVDisplayClass@@；"
       "vt[0]=004F4240(Display 非 COM 根类主表，ctor 004A8730 装活表)；另有 MapClass 007ED404 同号槽(共享布局)但名字指向 DisplayClass，取 007E6114；② 钉死。",
  why3="5374B/1423 指令。6 个 p3 站点：call 0x7C8E17=malloc 零判断(004A8730 处的分配包装)、0x578290/0x567110 等间接/未知返值 test→je、"
       "malloc 空判断 + 对象初始化模板假句，无一给出域内 falsifiable 多值返值约定；无跳表/内存形状/循环非栈写合同。③ 不成立。",
  why4="vt 007E6114 行外 ctor 004A8730@004A8830 装活表，[reg+0x70] 派发链 100 处；④ 成立但 ③ 未过。"),
"00567230": dict(r2=1,r3=0,r4=1,
  why2="slotva 007E6188，vt=007E6114，offset=+116(=slot#29)；RTTI .?AVDisplayClass@@；② 钉死。",
  why3="315B/103 指令，chA p1=2/p2=2/p3=0：call→test 被调无可伪证多值返值、两路动作签名不足；1 个 direct caller(0065449D)不改变本体无 ③b；"
       "无跳表/循环非栈写。③ 不成立。",
  why4="vt 007E6114 行外 ctor 004A8730 装活表，派发链 131 处；④ 成立但 ③ 未过。"),
"006DBD20": dict(r2=1,r3=1,r4=1,
  why2="slotva 007F435C，vt=007F4348，offset=+20(=slot#5)；RTTI 0080B9A8→00842A38→.?AVTactical@@；"
       "vt[0]=00410260 主表；ctor 006D1C20 在 006D1D54 写 [esi]=007F4348；② 钉死。",
  why3="③b② PASS，流读入(方向未写反)。call 0x410380@006DBD2E；被调空参 00410389 mov eax,0x80004003=E_POINTER、正路 0041039E call [eax+0xc]"
       "=IStream::Read 槽(读入)。本体 test eax,eax@006DBD33→jl@006DBD35(0f 8c b4 00 00 00)→006DBDEF 原样返回负 HRESULT；"
       "不成立路 call 0x6D1E30/0x6D8640 + 多处对象字段内存写(006DBDC7..006DBDE6，非栈写)后 xor eax,eax@006DBDED 返 0。"
       "失败返负/成功返 0、真分支、两路动作不同、零间隔无 eax 覆写，非 bool。",
  why4="vt 007F4348 由行外真 ctor 006D1C20 在 006D1D54(c7 06 48 43 7f 00)写活表(006D1C25 call 0x410170 基类构造)；"
       "[reg+0x14] 派发链 273 处(.text)，与 ② .rdata RTTI 链不同源。"),
}

# 逐行生成 EVIDENCE（每行自有地址与字节）；③理由逐行独立，不共用。
count = 0
for row in rows:
    e = row["entry"]; nm = row["name"]; d = D[e]; r = ana[e]
    size = r["atlas"].get("size", 0)
    b = R.read_va(int(e,16), 16)
    first = r["first_insns"][:5]
    four = d["r2"] and d["r3"] and d["r4"]
    sl = r["slots"][0] if r["slots"] else {}
    L = []
    L.append("# ROW %s  S07  %s" % (e, nm))
    L.append("")
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s (大写十六进制无 0x；delta entry 列原样写此串)" % e)
    L.append("- atlas size=%d B，反汇编 n_instr=%d，skipdata=%d，in_text=%s，body_end=%08X(in_text=%s)" % (
        size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"], r["body_end"], r["body_end_in_text"]))
    L.append("- 入口 16B: %s" % " ".join("%02X"%x for x in b))
    for x in first: L.append("    " + x)
    L.append("")
    L.append("## 环② 类身份（独立取证；Class::slotN 的 Class 仅线索，已由 RTTI/虚表钉死）")
    L.append("- slotva=%s vtable_base=%s slot offset=+%d (=slot#%d)" % (
        sl.get("slot_va"), sl.get("vtable_base"), sl.get("slot_off",0), sl.get("slotno",0)))
    L.append("- RTTI COL=%s → TD=%s → name=%s；vtable_head[0..3]=%s（vt[0] 判定：%s）" % (
        sl.get("col"), sl.get("td"), sl.get("rtti_name"), sl.get("vtable_head"), sl.get("vtable_class")))
    L.append("- ③陷阱③小成员表核对：见 why2 对该行主表/成员表的逐行判定。")
    L.append("- 判定: " + d["why2"])
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % ("PASS" if d["r3"] else "FAIL"))
    if r["chA_sites"]:
        for s in r["chA_sites"][:4]:
            cal = ("%08X"%int(s["callee"])) if s.get("callee") else "INDIRECT"
            L.append("- 站点 call=%s callee=%s %s imm=%s jcc=%s@%s" % (
                s["call_addr"], cal, s["test_kind"], s["test_imm"], s["jcc_mnemonic"], s["jcc_addr"]))
    else:
        L.append("- 无 chA 机械站点 (p3=0)；chB 跳表=%d" % len(r["chB"]))
    if r["io_direction"]:
        L.append("- I/O 方向标注: " + " | ".join("%s@%s=%s"%(x["api"],x["site"],x["dir"]) for x in r["io_direction"]))
    L.append("- 判定: " + d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者/活虚表派发；与 ② 不同源；㉓ 析构器锚排除）")
    L.append("- 判定: " + d["why4"])
    L.append("- direct callers(%d): %s" % (len(r["direct_callers"]), ",".join(r["direct_callers"][:8]) if r["direct_callers"] else "无"))
    L.append("- dispatch_sites(%d): %s" % (len(sl.get("dispatch_sites",[])), ",".join(sl.get("dispatch_sites",[])[:6])))
    L.append("")
    L.append("## 裁定")
    L.append("- ①=PASS ②=%s ③b=%s ④=%s ②④不同源=%s" % (
        "PASS" if d["r2"] else "FAIL", "PASS" if d["r3"] else "FAIL",
        "PASS" if d["r4"] else "FAIL", "是" if d["r2"] and d["r4"] else "n/a"))
    L.append("- **四环齐全=%s**：%s" % ("是 -> [已证]" if four else "否 -> 不产出",
        "产出 delta 行。" if four else "宁严不宽，不产出。"))
    L.append("")
    L.append("## 本行地址锚")
    L.append("- entry=%s；slotva=%s；vt=%s；首站点=%s" % (
        e, sl.get("slot_va"), sl.get("vtable_base"),
        r["chA_sites"][0]["call_addr"] if r["chA_sites"] else "n/a"))
    with open(os.path.join(EVID, "ROW_%s.txt"%e), "w", encoding="utf-8") as f:
        f.write("\n".join(L)+"\n")
    count += 1
    print("EVID %s 2=%d 3=%d 4=%d four=%s" % (e, d["r2"], d["r3"], d["r4"], four), flush=True)
print("wrote %d EVIDENCE files" % count)

# ---- delta.tsv：仅四环齐全 ----
PASS = [row for row in rows if D[row["entry"]]["r2"] and D[row["entry"]]["r3"] and D[row["entry"]]["r4"]]
semantics = {
 "00421730":"AlphaShapeClass::vslot8（③b② 析构体内容器 Find 返 -1 下标哨兵+边界检查+数组前移非栈写循环：call [edx+0x10]@00421763→cmp eax,-1@00421766→je@00421769，命中路 0042178A mov [ecx+eax*4-4],edx 循环体非栈写；② vt 007E32A4 slot8 RTTI .?AVAlphaShapeClass@@；④ 行外 ctor 00420960@0042097C 装活表，本体内析构自装表按㉓排除，与② RTTI 链不同源）",
 "004370C0":"BuildingLightClass::vslot8（③b② 析构体内容器 Find -1+压缩摘链非栈写循环：call [edx+0x10]@00437107→cmp eax,-1@0043710A→je@0043710D，0043712E mov [ecx+eax*4-4],edx 循环体非栈写；② vt 007E3AD0 slot8 RTTI .?AVBuildingLightClass@@；④ 行外 ctor 00435820@004358AF 装活表，与②不同源）",
 "00491210":"ConvertClass::slot0（③b② 析构体内容器 Find -1+压缩摘链非栈写循环：call [eax+0x10]@00491261→cmp eax,-1@00491264→je@00491267，00491288 mov [ecx+eax*4-4],edx 循环体非栈写；② vt 007E5358 slot0 RTTI .?AVConvertClass@@，紧邻 007E5318/007E5338 容器成员表按陷阱③排除；④ 行外 ctor 0048E740@0048E93B 装活表，与②不同源）",
 "00555150":"LightSourceClass::slot8（③b② 析构体内容器 Find -1+压缩摘链非栈写循环：call [edx+0x10]@0055518A→cmp eax,-1@0055518D→je@00555190，005551B1 mov [ecx+eax*4-4],edx 循环体非栈写；② vt 007ED028 slot8 RTTI .?AVLightSourceClass@@；④ 行外 ctor 00554760@005547A0 装活表，与②不同源）",
 "005550C0":"LightSourceClass::slot5（③b② 流读入：call 0x410380@005550CB([eax+0xc] IStream::Read 槽)→test eax,eax@005550D0→jl@005550D2，失败原样返负 HRESULT(0x80004003 E_POINTER)/成功返 0，两路真不同；读写方向逐字节核定为读入未写反；② vt 007ED028 slot5 RTTI .?AVLightSourceClass@@；④ 行外 ctor 00554760@005547A0 装活表，与② RTTI 链不同源）",
 "00555110":"LightSourceClass::slot6（③b② 流写出：call 0x410320@0055511F([eax+0x10] IStream::Write 槽)→test eax,eax@00555124→jl@00555126，失败返负 HRESULT(0x80004003 E_POINTER)/成功返 0，两路真不同；读写方向逐字节核定为写出未写反；② vt 007ED028 slot6 RTTI .?AVLightSourceClass@@；④ 行外 ctor 00554760@005547A0 装活表，与②不同源）",
 "006DBD20":"Tactical::slot5（③b② 流读入：call 0x410380@006DBD2E([eax+0xc] IStream::Read 槽)→test eax,eax@006DBD33→jl@006DBD35，失败返负 HRESULT(0x80004003 E_POINTER)/成功返 0 并有 006DBDC7.. 非栈写，两路真不同；读写方向逐字节核定为读入未写反；② vt 007F4348 slot5 RTTI .?AVTactical@@；④ 行外 ctor 006D1C20@006D1D54 装活表，与②不同源）",
}
with open(os.path.join(OUT,"delta.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for row in PASS:
        e=row["entry"]
        f.write("%s\t%s\t%s\t%s\t[已证]\tD:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S07_B1/EVIDENCE/ROW_%s.txt\n" % (
            e, row["subsystem"], row["name"], semantics[e], e))

# ---- base_rate.tsv ----
checked=len(rows); r2=sum(D[r["entry"]]["r2"] for r in rows); r3=sum(D[r["entry"]]["r3"] for r in rows)
r4=sum(D[r["entry"]]["r4"] for r in rows); allfour=len(PASS)
rate = allfour/checked
with open(os.path.join(OUT,"base_rate.tsv"),"w",encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("NAMED_PUSH_S07_B1\t%d\t%d\t%d\t%d\t%d\t%.4f\n"%(checked,r2,r3,r4,allfour,rate))

# ---- PROGRESS.md（每 5 行追加）----
P=["# PROGRESS — NAMED_PUSH_S07_B1",""]
for i in range(0, len(rows), 5):
    chunk = rows[i:i+5]
    seg=[]
    for row in chunk:
        e=row["entry"]; d=D[e]
        seg.append("%s(%s): ②%s ③%s ④%s %s"%(e,row["name"],
            "P" if d["r2"] else "F","P" if d["r3"] else "F","P" if d["r4"] else "F",
            "四环齐全" if (d["r2"] and d["r3"] and d["r4"]) else "不产出"))
    P.append("- [%d–%d 行] %s"%(i+1,i+len(chunk),"; ".join(seg)))
P.append("")
P.append("- 汇总: rows_checked=%d；②=%d；③b=%d；④=%d；四环齐全=%d (%.4f)"%(checked,r2,r3,r4,allfour,rate))
P.append("- 三陷阱逐行核过：①读写方向(2 条流读入 005550C0/006DBD20、1 条流写出 00555110 逐字节核定未写反)；"
         "②④锚落析构器(④ 全取行外 ctor 装表，体内析构自装表按㉓排除)；③小成员表(ConvertClass 007E5318/007E5338 容器表排除，全取对象主表)。")
with open(os.path.join(OUT,"PROGRESS.md"),"w",encoding="utf-8") as f:
    f.write("\n".join(P)+"\n")

print("DELTA rows=%d; base_rate=%d/%d/%d/%d rate=%.4f"%(len(PASS),r2,r3,r4,allfour,rate))

# 写出机器可读 verdict，供 REPORT 表格用
json.dump({"D":D,"counts":dict(checked=checked,r2=r2,r3=r3,r4=r4,allfour=allfour),
           "pass":[r["entry"] for r in PASS]},
          open(os.path.join(WORK,"verdicts.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
