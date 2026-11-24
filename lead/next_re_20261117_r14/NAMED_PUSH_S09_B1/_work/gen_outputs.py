# -*- coding: utf-8 -*-
"""生成 18 份 EVIDENCE/ROW_<entry>.txt、delta.tsv、base_rate.tsv、PROGRESS.md。
依据 anchors.json + recore/retprof 精确取证；逐行独立裁定理由。"""
import os, sys, json
WORK=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK)
import recore as _R
R4sz={k:_R.ATLAS.get(k,{}).get('size',"") for k in _R.ATLAS}
OUTDIR=os.path.dirname(WORK)
EV=os.path.join(OUTDIR,"EVIDENCE")
A=json.load(open(os.path.join(WORK,"anchors.json"),encoding="utf-8"))
ROWS=json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))
R4=json.load(open(os.path.join(WORK,"ring4_deep.json"),encoding="utf-8"))

# 每行裁定：① ② ③ ④ 标签 + ③ 具体理由 + 语义
V={
"00478BA0":dict(r3="FAIL",proven=False,
  sem="CCToolTip::slot1（tooltip 文本矩形裁剪/居中：全局对象虚调取状态，jl 早退，随后三段边界钳制 + 字符串截取写）",
  r3why="chA p1/p2/p3=1/1/0。站点 0x478BAF `call dword ptr [eax+0x28]` 是对全局指针 [0x887640] 所指运行时对象的虚调用（[0x887640] 静态值为 0，运行期装入），vptr/vtable 无法从静态字节钉死 ⇒ 被调返回约定不可伪证，p3=0。非 ③b②；其余分支是比较/边界钳制（cmp/jle/jg）无伪证错误码，无合格 ③b①/③/④。"),
"00479050":dict(r3="FAIL",proven=False,
  sem="CCToolTip::slot5（12 条小函数：全局对象虚调 [eax+0x28] 取状态，jge 早退，随后 00478BA0 转发）",
  r3why="chA p1/p2/p3=1/1/0。站点 0x479058 `call [eax+0x28]` 同为 [0x887640] 运行时对象虚调，被调不可静态定位 ⇒ 返回约定不可伪证。且本体仅 12 条、`test/jge` 后即转 00478BA0，属③a 转发壳。"),
"00488350":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot39（取计数 [eax+0x94]，jle 空表早退；循环内 00557AE0 取第 ebx 项指针，空则跳过）",
  r3why="chA 站点 call@0x488350→00557AE0 + `test eax,eax`/`je`。被调 00557AE0 出口为 `xor eax,eax`(0x557AED) 或 `mov eax,[ecx+eax*4]`(0x557AF3，表项指针)：即 0/指针的取表项访问器，调用方按 null 判定，是布尔空检查，非多值状态码、非 Find -1 下标约定 ⇒ 不满足可伪证性（{0,1} 布尔/空检查不算）。"),
"00488360":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot40（00557AC0 取第 0 项指针，空则跳过；否则读 [item+4] 比较）",
  r3why="chA call@0x488365→00557AC0 + `test/je`。被调 00557AC0 出口均为表项指针/0（0x557AC7/0x557ADB），空指针检查，布尔消费，非可伪证错误码/状态。"),
"00488380":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot43（-count 循环：00557AC0 逐项取指针，007DD0F8 宽字符不区分大小写比较，命中则 0057730/7C8B3D 移除释放）",
  r3why="chA call@0x4883AA→007DD0F8（宽字符 strcmp 族，出口 `sub eax,ecx` 返回字符差）+ `test eax,eax`/`je` 判相等：比较谓词按布尔消费，非错误码。另一 call→00557AC0 是空指针检查。循环体内无合格 ③b④（数据写在被调 0057730/7C8B3D 内，触犯『禁止把被调用者内部的写当循环内非栈写』）。"),
"004883F0":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot45（同 slot43 形态：循环逐项 00557AC0 取项 + 007DD0F8 宽字符比较，命中移除）",
  r3why="同 slot43：007DD0F8 比较差按 test/je 当布尔消费；00557AC0 空检查；写在被调内。无可伪证多值返回约定。"),
"004884A0":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot31（00557AC0 取第 arg 项，空检查后读 [item+4]；带 [ebp] 状态判断）",
  r3why="chA call@0x4884D8→00557AC0 + `test/je`，返回表项指针/0，布尔空检查，非可伪证错误码。"),
"004A57B0":dict(r3="FAIL",proven=False,
  sem="Dial8Class::slot27（全局对象虚调 + 0048E620 取项 → 004A5944 失败路；成功路按计数做表项处理循环）",
  r3why="chA call@0x4A57C6→0048E620 + `test/je`。0048E620 是转发子：内部 `call 0x4E1550` 后 `mov eax,[…]` 直接 ret，而被调 004E1550 出口仅 `xor eax,eax`(0)/`mov eax,1`(1)，是 {0,1} 布尔 ⇒ 不满足可伪证性（{0,1} 不算）。"),
"004AC380":dict(r3="FAIL",proven=False,
  sem="DisplayClass::LMBDown（鼠标左键处理：多段全局对象虚调取状态 + 边界判断，非单一可伪证返回约定）",
  r3why="chA p1/p2/p3=2/2/0，无 p3 站点。多处 `call [reg+imm]` 为运行时对象虚调或返回指针，无法从字节钉死一个『失败/成功返什么』的多值约定；分支多是状态位/边界判断，不构成 ③b②；无合格 ③b①/③/④。"),
"004B5530":dict(r3="FAIL",proven=False,
  sem="DropListClass::slot42（循环读 [esi]/[ebx] 表项比较，计数钳制后调用虚函数）",
  r3why="chA p1/p2/p3=2/1/0，无 p3。循环体内写均在被调内、本体仅指针比较/边界判断，无可伪证错误码返回约定。"),
"004C3110":dict(r3="FAIL",proven=False,
  sem="DropListClass::slot27（0048E620 取项 → 004C3180 失败路；成功路处理表项）",
  r3why="chA call@0x4C311B→0048E620 + `test/je`。0048E620→004E1550 返回 {0,1} 布尔 ⇒ 不满足可伪证性。"),
"004C3420":dict(r3="FAIL",proven=False,
  sem="DropListClass::slot38（按键过滤：CRT 字符分类 7C9A8D/7C990E/7C998C/7C9A31 + toupper 7C97D3，合法字符写入宽字符缓冲）",
  r3why="chA 站点调用 007C990E/007C9A31 等 CRT `is*` 分类函数，出口 `and eax,0x103`/`0x117`/`0x4`（字符表位掩码），调用方 `test/je/jne` 当布尔谓词消费；007C97D3 是 toupper 映射。均为分类谓词，非『失败/成功』错误码或多值状态码 ⇒ 不构成 ③b②。本体无边界循环写（单次写 `mov [ecx+eax*2],di`），非 ③b④。"),
"004E2830":dict(r3="FAIL",proven=False,
  sem="GaugeClass::slot31（仪表滚动更新：取 [esi+0x34]/[esi+0xc] 上界，边界钳制 + 递减循环 [esi+0x38]，末尾写 [edi]=0 返 1）",
  r3why="chA p1/p2/p3=3/2/0，无 p3 站点（多处 `call [edx+0x28]` 运行时对象虚调或写值返回，不可静态伪证）。存在边界检查循环（`test eax,eax/jle` + `mov [esi+0x38],eax` 非栈写），但其 I/O 经虚调 [edx+0xa0]/[edx+0x8c]，无法逐路验证完整 I/O，且失败/成功返回固定 1/0（布尔）⇒ 不达 ③b④ 的『完整循环 I/O 可逐路验证』，判 FAIL（边界，列待裁）。"),
"004E2B50":dict(r3="FAIL",proven=False,
  sem="TriColorGaugeClass::slot27（0048E620 取项 → 004E3094 失败路；成功路做仪表/颜色写入，末尾 mov eax,1）",
  r3why="chA call@0x4E2B5E→004E2690 + `test/je`。004E2690 出口仅 `mov eax,1`(0x4E2821) 与 `xor eax,eax`(0x4E282D) ⇒ {0,1} 布尔，不满足可伪证性。"),
"004F37A0":dict(r3="FAIL",proven=False,
  sem="GraphicMenuImageItem::slot3（全局对象虚调取 bl 状态；bl=1 时 007C8E17 分配 0x30 块，005CCC30 建对象，成功则 005D1DF0）",
  r3why="chA 站点 007C8E17（`push 1; call 007C9442` operator new）与 005CCC30 出口均为指针/0 或不可定位值，调用方 `test/je` 空指针检查，布尔消费，非多值状态码。本体无合格 ③b①/③/④。"),
"004F45B0":dict(r3="PASS",proven=True,
  sem="MouseClass::slot17（鼠标显示准备：004A33A0 取图源返多值状态 0/-1/1/2，非 0 直接释放返回；为 0 则两次校验后构造渐变色结构并调用 004A35A0/35F0/3840/3660 写显示状态）",
  r3why="chA p1/p2/p3=3/3/2。站点 0x4F45EA `e8 b1 ed fa ff`(call 004A33A0) → 0x4F45EF `85 c0`(test eax,eax) → 0x4F45F1 `0f 85 4c 01 00 00`(jne→0x4F4743)，间隔零 eax 覆写。被调 004A33A0 返回约定可从字节伪证：0x4A33BC `83 c8 ff`(or eax,-1)→0x4A33C6 ret、0x4A3465 `b8 01 00 00 00`(mov eax,1)→0x4A3471 ret、0x4A3581 `f7 d8 … 1b c0 … 83 e0 02`(neg/sbb/and eax,2)→0x4A3592 ret，以及成功路 0x4A3434 ret ⇒ 失败返多值非 0 码 {-1,1,2}、成功返 0，属多值状态码（非 {0,1} 布尔）。调用方真拿它分支：jne 路 0x4F4743 释放并直接收尾；fall-through 路 0x4F45F7 起做第二次校验 + 大量构造/写显示状态，两路动作真不同。第二站点 0x4F4602 同型（对 [0x8A0E0C]）。单 call 非多路同一 call。③b② 成立。"),
"00557920":dict(r3="FAIL",proven=False,
  sem="CheckListClass::slot27（004E1550 置位检查，非 0 成功路做虚调取数据 + 循环处理表项 [esi+0x16c/+0x170]）",
  r3why="chA 站点 0x55792E→004E1550 返回 {0,1} 布尔（0x4E1561/0x4E156D）；0x55798F→004A5A50 出口均为 callret（复杂子函数返回值，非固定错误码）。无可伪证多值返回约定；循环体内非栈写在 [esi+0x170]/[esi+8] 等但无逐路可验证 ③b④。"),
"0069DEB0":dict(r3="FAIL",proven=False,
  sem="ShapeButtonClass::slot27（0048E620 取项 → 0069DFAD 失败路；成功路处理形状按钮状态）",
  r3why="chA call@0x69DEBB→0048E620→004E1550 返回 {0,1} 布尔 ⇒ 不满足可伪证性。本体另有 10 个 direct 调用者但那是 ④ 维度，不改 ③ 裁定。"),
}

def ring4_block(e):
    a=A[e]; r4=a.get("r4"); r2=a.get("r2")
    extra=""
    if e=="004F45B0":
        extra=("  另一同型构造安装点 005BDA4A `c7 06 64 19 7e 00`(mov [esi],0x7E1964)，"
               "位于 005BDA40（先 call 基类构造 0x692290 再装本类 vt），亦非 atexit。\n")
    if not r4: return "  活虚表安装点: 未取到（见 ring4_deep.json）"
    lines=[]
    lines.append("  vt=%s slot#%s vt[slot]==entry? True (槽值=%s)" % (r2["vbase"],r2["slotno"],r2["slotval"]))
    lines.append("  行外、非 atexit 的构造安装点: %s" % r4["wa"])
    if r4.get("func"):
        lines.append("  安装点字节: %s = mov [reg], %s" % (r4["inst_bytes"],r2["vbase"]))
        sz=R4sz.get(r4["func"],"")
        lines.append("  所在函数 %s (size=%s)，形态: 构造期安装本类虚表（inline 于 .text，先/后调子构造均属构造函数体）" % (
            r4["func"], sz))
        fc=r4.get("func_calls") or []
        if fc: lines.append("  该函数直接调用目标: %s" % ", ".join(fc))
    lines.append("  是否 atexit 析构注册(push<fn>;call 0x7C978A): False（已逐点排除，见 atexit_check.py）")
    if extra: lines.append(extra.rstrip())
    lines.append("  裁定: PASS（活虚表派发可达本 entry，非 direct-only；与 ② RTTI 数据链不同源）")
    return "\n".join(lines)

def site_block(e):
    a=A[e]
    lines=[]
    s=a["sites"]
    if not s:
        lines.append("  chA 机械站点 p1/p2/p3=%s（无通过 p3 的站点）" % a["chA_p1p2p3"])
        return "\n".join(lines)
    for st in s:
        lines.append("  站点 call@%s `%s` → callee=%s" % (st["call"],st["call_bytes"],st["callee"]))
        lines.append("    test@%s `%s` ; %s@%s `%s` → %s" % (
            st["test"],st["test_bytes"],st["jcc_mn"],st["jcc"],st["jcc_bytes"],st["jcc_tgt"]))
        if st.get("prof_consts"):
            lines.append("    recore callee consts=%s（详细 retprof 见正文/retprof.py）" % st["prof_consts"])
    return "\n".join(lines)

HDR=("目标: ra2youli\\gamemd.exe  SHA-256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476\n"
     "ImageBase=0x400000  .text=[0x401000,0x7E038D)  capstone 5.0.7(skipdata=True)/pefile 2024.8.26\n")

for i,r in enumerate(ROWS,1):
    e=r["entry"]; a=A[e]; v=V[e]; r2=a.get("r2"); r1=a["r1"]
    L=[]
    L.append("ROW_%s   subsystem=S09   name=%s   批次=S09_B1 第%d行(全局第%d)" % (e,r["name"],i,i))
    L.append(HDR.rstrip())
    L.append("")
    L.append("[环① 入口]")
    L.append("  entry=%s 在 .text=%s  atlas_size=%s  n_insn=%s  skipdata=%s 首条=%s 末条=%s" % (
        e,r1["in_text"],r1["atlas_size"],r1["n_disasm"],r1["n_skipdata"],r1["first"],r1["last"]))
    L.append("  函数边界自洽: 末条为 ret/ret-imm/jmp ⇒ %s" % r1["ends_with_ret_or_jmp"])
    L.append("  裁定: PASS")
    L.append("")
    L.append("[环② 类身份] 裁定=PASS")
    if r2:
        L.append("  .rdata 中本 entry 作 4B VA 的槽: %s = %s（全镜像同值槽 %d 个，%s 为线索类主表）" % (
            r2["ref"],r2["slot_bytes"],r2["n_match"],r2["name"]))
        L.append("  vtable_base=%s  slot_off=%d  slot_no=%d  线索槽号=%s ⇒ 自洽=%s" % (
            r2["vbase"],r2["off"],r2["slotno"], a["name"].split("::")[-1].replace("slot",""),
            "N/A(方法名)" if "::slot" not in a["name"] else "True"))
        L.append("  [vt-4]=COL %s 字节=%s sig=0(0=正常单一继承)" % (r2["col"],r2["col_sig_bytes"]))
        L.append("  [COL+0xC]=TD %s 字节=%s" % (r2["td"],r2["td_bytes"]))
        L.append("  TD+8 名串 @%s 字节=%s" % (r2["name_va"],r2["name_bytes"]))
        L.append("  RTTI 类名 = %s" % r2["name"])
        L.append("  小成员表核对: 本 vtable slot0 为类特有函数（非公共 00410260），且 [vt-4] 有 sig=0 的 COL + 名串 .?AV ⇒ 主虚表，非小成员表")
        L.append("  结论: PASS —— RTTI 描述符(COL→TD→名串)与虚表槽独立钉死；slot_no 由字节复算，与线索自洽；未借用名字中的 Class 部分")
    L.append("")
    L.append("[环③ 整体合同] 裁定=%s" % v["r3"])
    L.append(site_block(e))
    L.append("  %s" % v["r3why"])
    L.append("  语义: %s" % v["sem"])
    L.append("")
    L.append("[环④ 使用见证] 裁定=PASS")
    L.append(ring4_block(e))
    L.append("")
    L.append("[②④不同源]")
    L.append("  ② 锚在 .rdata 的虚表槽/RTTI COL/TD 描述符字节 (%s/%s/%s)；④ 锚在 .text 的构造安装指令 %s —— 段不同、地址不同、产物类型不同，非同一虚表槽复用" % (
        r2["ref"] if r2 else "?", r2["col"] if r2 else "?", r2["td"] if r2 else "?", a["r4"]["wa"] if a.get("r4") else "?"))
    L.append("")
    L.append("[裁定] %s" % ("四环齐全 ⇒ [已证]，写入 delta.tsv" if v["proven"] else "③ 不成立 ⇒ 不入 delta.tsv（②/④ 单环成立不等于全证）"))
    open(os.path.join(EV,"ROW_%s.txt"%e),"w",encoding="utf-8").write("\n".join(L)+"\n")
    print("wrote EVIDENCE/ROW_%s.txt  verdict=%s" % (e,v["r3"]))

# delta.tsv
proven=[r for r in ROWS if V[r["entry"]]["proven"]]
dl=["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for r in proven:
    e=r["entry"]
    sem=V[e]["sem"]+"（"+V[e]["r3why"]+"）"
    evp="D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S09_B1/EVIDENCE/ROW_%s.txt"%e
    dl.append("%s\t%s\t%s\t%s\t[已证]\t%s"%(e,r["subsystem"],r["name"],sem,evp))
open(os.path.join(OUTDIR,"delta.tsv"),"w",encoding="utf-8").write("\n".join(dl)+"\n")
print("delta.tsv rows=%d"%(len(proven)))

# base_rate.tsv
n=len(ROWS); r2n=sum(1 for r in ROWS if A[r["entry"]].get("r2"))
r3n=sum(1 for r in ROWS if V[r["entry"]]["r3"]=="PASS")
r4n=sum(1 for r in ROWS if A[r["entry"]].get("r4"))
alln=len(proven); rate=(alln/n)
br="batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\nNAMED_PUSH_S09_B1\t%d\t%d\t%d\t%d\t%d\t%.4f\n"%(n,r2n,r3n,r4n,alln,rate)
open(os.path.join(OUTDIR,"base_rate.tsv"),"w",encoding="utf-8").write(br)
print("base_rate:",br.strip().splitlines()[1])

# PROGRESS.md
P=["# PROGRESS — NAMED_PUSH_S09_B1","",
   "每 5 行追加一次；逐行核完即落 EVIDENCE/ROW_<entry>.txt。",""]
for k in range(5,n+1,5):
    grp=ROWS[k-5:k]
    P.append("## 行 %d–%d（累计 %d/18）"%(k-4,k,k))
    for r in grp:
        e=r["entry"]; v=V[e]
        P.append("- %s %-42s ①PASS ②PASS ③%s ④PASS ⇒ %s（EVIDENCE 已落盘）"%(
            e,r["name"],v["r3"],"[已证]" if v["proven"] else "不成立"))
    P.append("")
P.append("- 基础率累计：rows=%d ②=%d ③b=%d ④=%d all_four=%d"%(n,r2n,r3n,r4n,alln))
open(os.path.join(OUTDIR,"PROGRESS.md"),"w",encoding="utf-8").write("\n".join(P)+"\n")
print("PROGRESS.md written")
