# -*- coding: utf-8 -*-
"""生成 18 份逐行 EVIDENCE，四环各行自有地址与字节；③ 理由逐行独立，不整批共用。
只读 gamemd.exe；写域仅本批 EVIDENCE 目录。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.dirname(WORK)
EVID=os.path.join(OUT,"EVIDENCE")
os.makedirs(EVID,exist_ok=True)
rows=json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))
ana={r["entry"]:r for r in json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))}

def hx(x): return R.hx(x)
def va(x): return int(x,16) if isinstance(x,str) else int(x)

# 与名字一致的 COL/TD/RTTI 与槽偏移（来自 resolve_rtti_ext.txt，扩展 kmax=400 钉死）
# (slot_va, vt, off, slotno, col, td, rtttiname)
RTTI={
 "00410C30":("007E2020","007E2000",32,8,"007FB210","00817808",".?AVAbstractTypeClass@@"),
 "00414290":("007E22A4","007E22A4",0,0,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "00414BB0":("007E2300","007E22A4",92,23,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "004176F0":("007E2728","007E22A4",1156,289,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "00417CC0":("007E2318","007E22A4",116,29,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "004190B0":("007E2438","007E22A4",404,101,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "004196B0":("007E2450","007E22A4",428,107,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "0041A9E0":("007E2664","007E22A4",960,240,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "0041AA80":("007E2724","007E22A4",1152,288,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "0041B890":("007E2780","007E22A4",1244,311,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "0041BBD0":("007E27CC","007E22A4",1320,330,"007FB4C0","00817B90",".?AVAircraftClass@@"),
 "0041CB20":("007E28F4","007E2868",140,35,"007FB5B0","00817FB8",".?AVAircraftTypeClass@@"),
 "0041CC20":("007E28CC","007E2868",100,25,"007FB5B0","00817FB8",".?AVAircraftTypeClass@@"),
 "0041CE20":("007E287C","007E2868",20,5,"007FB5B0","00817FB8",".?AVAircraftTypeClass@@"),
 "0041CE90":("007E2880","007E2868",24,6,"007FB5B0","00817FB8",".?AVAircraftTypeClass@@"),
 "0041CFE0":("007E2888","007E2868",32,8,"007FB5B0","00817FB8",".?AVAircraftTypeClass@@"),
}

# 逐行 ③ 裁定与理由（每行独立地址与文字）
D={
"00410380":dict(ring3="FAIL", ring2="FAIL", ring4="FAIL",
  why2="该 entry 作为 4B VA 在非 .text 段全镜像 0 命中，无虚表槽、无 RTTI 描述符链可钉类身份；名字仅 AbstractClass（非 Class::slotN 形态），按 D-40 ② 无法独立取证 -> FAIL。",
  why3="body 90B/41 指令，channel A p3=0、channel B 无跳转表；该函数本身是 AbstractClass 的 QueryInterface 转发桩（0x0041038F mov eax,0x80004003;ret 失败常量），但它自己没有被测的 call->test->jcc 错误码合同，③a 直线转发，不构成 ③b。",
  why4="direct callers 42 个（如 0041D6FC/0041E54B/00420DEC），但无虚表槽、无活虚表派发链；按『direct-only 不足』且 ② 已 FAIL，④ 不作为独立升级依据。"),
"00410C30":dict(ring3="PASS", ring2="PASS", ring4="PASS",
  why3="站点 call dword ptr [edx+0x10]@0x00410C63 (FF 52 10；edx=[0xA8E968] 运行时全局对象) -> 零间隔 cmp eax,-1@0x00410C66 (83 F8 FF) -> je@0x00410C69->0x00410C98。-1 为 falsifiable 哨兵（未找到索引）。je 成立路 0x00410C98 直接 base-dtor+ret；不成立路 0x00410C6B 起 cmp eax,[0xA8E978] 边界检查、0x00410C78 mov [0xA8E978],ecx（非栈写）、0x00410C80 起 inc eax / mov edx,[ecx+eax*4] / mov [ecx+eax*4-4],edx 数组前移循环（循环体内非栈写+边界检查）。两路动作真不同（-1 跳过摘链 vs 找到则摘链），test/cmp 与 je 间无 eax 覆写，非 bool、非纯转发、非 malloc 模板、非多路同一 call。③b② 成立。",
  why4="vt 007E2000 槽 007E2020(=entry) 由构造安装点 00410975/004109CD/00410C3D 写入活对象；[reg+0x20] 派发链在 .text（dispatch 358 处），与 ② 的 .rdata RTTI 链不同源。"),
"00414290":dict(ring3="PASS", ring2="PASS", ring4="PASS",
  why3="站点 call 0x00410260@0x004142A2 (E8 B9 BF FF FF) -> zero-gap test eax,eax@0x004142A7 (85 C0) -> jge@0x004142A9 (7D 3E)。被调 0x00410260 是 QueryInterface 族：0x00410269 mov eax,0x80004003(E_POINTER)/0x004102EC mov eax,0x80004002(E_NOINTERFACE)/0x004102F5 xor eax,eax(S_OK)，返回可伪证 HRESULT（负值错误码，非 bool）。jge 对有符号 >=0 分支：eax>=0(S_OK) 走 0x004142E9 直接 ret 0xC；eax<0(错误码) 走 0x004142AB repe cmpsd 比 GUID [esi] vs 0x7E9B40、0x004142C8 mov [ebp],eax 写_OUT、0x004142CF/0x004142E4 call [ecx+4] 释放后 0x004142EC ret 0xC。两路动作真不同、无 eax 覆写陷阱、非 bool、非纯转发。③b② 成立。",
  why4="vt 007E22A4 槽 007E22A4(=entry,slot0) 由构造安装点 00413D87/0041408A/0041B4E1 写入活对象；[reg+0] 派发链在 .text（dispatch 820 处），与 ② 的 .rdata RTTI 链不同源。"),
"00414BB0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="5 个 channel A 站点：0x00414CE8/0x00414D45 为寄存器间接 call(callee=None)、0x00414E9E/0x00414F15 被调 0x007C8E17=malloc、0x00415127 被调 0x00421EA0 单 ret 源未知——全为 TEST_EAX->je 空指针/布尔探测，无一给出 falsifiable imm 错误码；malloc 空判属模板假句。另有跳表 0x00414BCD(table 0x4151B8,bound 30)仅 2 目标可达(0x414BDB/0x414BD4)，非每路可单独验证。③不成立。",
  why4="vt 007E22A4 槽 007E2300(=entry,slot23) 构造安装点 00413D87/0041408A/0041B4E1，[reg+0x5c] 派发链（dispatch 166 处），.text 代码链与 ② RTTI 链不同源。"),
"004176F0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="2 个 channel A 站点 0x004179C5(CMP_IMM imm=1,jne,callee=None 间接)/0x00417B0C(TEST_EAX,je,callee=None 间接)：imm=1 为布尔态非可伪证错误码，间接被调无法取证返回约定；跳表 0x00417749(table 0x417BAC,bound 27)仅 3 目标(0x417750/0x41775E/0x417C70)，非每路可验。③不成立。",
  why4="vt 007E22A4 槽 007E2728(=entry,slot289) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"00417CC0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="692B/243 指令大函数，channel A p1=10 但 p3=0：10 处 call->test 的被调返回均无 falsifiable 常量或两路动作签名不足以构成可伪证返回约定（多为间接虚调用的状态探测）；无跳表、无内存形状断言、无完整循环非栈写。③不成立。",
  why4="vt 007E22A4 槽 007E2318(=entry,slot29) 构造安装点 00413D87/0041408A/0041B4E1，[reg+0x74] 派发链（dispatch 131 处），.text 与 ② RTTI 链不同源。"),
"004190B0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="5 站点：0x00419224/0x00419413/0x00419428 为 CMP_IMM imm=1 布尔态（非可伪证错误码，callee=None）；0x00419281/0x004193C4 被调 0x004D8FB0 返回常量集={0xA,0x14}（枚举值 10/20，非错误码）。两跳转表 0x004190CC(table 0x41952C,bound27)/0x00419102(table 0x419550,bound25) 为大型状态机，目标分散且非每路可单独验证。③不成立。",
  why4="vt 007E22A4 槽 007E2438(=entry,slot101) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"004196B0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="261B/93 指令函数，channel A p3=0、无跳表：唯一可能的 call->test 路径两路动作签名相同或被调无可伪证返回常量，不构成 ③b②；无 ③b①/③b③/③b④。③不成立。",
  why4="vt 007E22A4 槽 007E2450(=entry,slot107) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"0041A9E0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="唯一站点 call 0x0041A9F6->0x006FC0B0 @0x0041A9F6 后 TEST_EAX@0x0041A9F8/jne->0x0041AA79；被调 0x006FC0B0 32 ret、返回常量仅 {0}（strcmp/串比较族，其余源未知），TEST_EAX jne 是『非零即不同』的比较分支而非可伪证错误码/返回约定；taken 仅 ret、fallthrough 继续状态检查，属布尔探测。③不成立。",
  why4="vt 007E22A4 槽 007E2664(=entry,slot240) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"0041AA80":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="3 站点：0x0041AB62(CMP_IMM imm=1,jne,间接)/0x0041AC81(CMP_IMM imm=1,je,间接) 为布尔态非错误码；0x0041AC2E 被调 0x0070C610 单 ret 无可伪证常量、TEST_EAX je。各路均为对象状态检查与资源获取分支，无一构成 falsifiable imm 错误码/返回约定。③不成立。",
  why4="vt 007E22A4 槽 007E2724(=entry,slot288) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"0041B890":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="103B/37 指令小函数，channel A p3=0、无跳表：2 处 call->test 的被调返回无 falsifiable 常量、两路动作签名相同，不构成可伪证返回约定；无 ③b①/③b③/③b④。③不成立。",
  why4="vt 007E22A4 槽 007E2780(=entry,slot311) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"0041BBD0":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="站点 call dword ptr [edx+0x278]@0x0041BBF4 (FF 92 78 02 00 00) -> cmp eax,1@0x0041BBFA (83 F8 01) -> je@0x0041BBFD->0x0041BC26；被调 =vt007E22A4[0x278]=0x0065AAA0 单 ret 源=(call)未知，cmp eax,1 为布尔态比较、无 falsifiable 错误码。taken(0x0041BC26) 仅 ret 缓存值、fallthrough(0x0041BBFF) mov [esi+0x6CC],0 + call 0x004DF040 重算后写回，属 getter/缓存刷新，非整体合同。③不成立。",
  why4="vt 007E22A4 槽 007E27CC(=entry,slot330) 由扩展回扫钉死；构造安装点 00413D87/0041408A/0041B4E1，[reg+slot] 派发链在 .text，与 ② RTTI 链不同源。"),
"0041CB20":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="43B 小函数，唯一站点 call 0x007C8E17@0x0041CB28 = malloc，TEST_EAX@0x0041CB2A/je->0x0041CB45；je 路 xor eax,eax;ret（分配失败）、fallthrough 0x0041CB34 call 0x00413D20 构造后 ret。典型『malloc 空判断 + 对象初始化』模板假句，malloc 的 NULL 不是域内可伪证错误码。③不成立。",
  why4="vt 007E2868 槽 007E28F4(=entry,slot35) 构造安装点 0041C900/0041CE44/0041CFE6，[reg+0x8c] 派发链（dispatch 50 处），.text 与 ② RTTI 链不同源。"),
"0041CC20":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="唯一站点 call 0x00528A10@0x0041CD19 后 TEST_EAX@0x0041CD1C/je->0x0041CD2D；被调 0x00528A10 两 ret、返回常量仅 {0}（其余源未知），TEST_EAX je 是空指针/布尔探测而非可伪证错误码；je 路与 fallthrough 0x0041CD22 call 0x00428B80 后都汇入 0x0041CD31 的对象字段初始化（mov [esi+0xE00]/[0xE04],eax 非栈写），属初始化模板假句。③不成立。",
  why4="vt 007E2868 槽 007E28CC(=entry,slot25) 构造安装点 0041C900/0041CE44/0041CFE6，[reg+0x64] 派发链（dispatch 49 处），.text 与 ② RTTI 链不同源。"),
"0041CE20":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="100B/29 指令函数，channel A p3=0、无跳表：call->test 的被调无可伪证返回常量且两路动作签名相同，不构成 ③b②；无 ③b①/③b③/③b④。③不成立。",
  why4="vt 007E2868 槽 007E287C(=entry,slot5) 构造安装点 0041C900/0041CE44/0041CFE6，[reg+0x14] 派发链（dispatch 273 处），.text 与 ② RTTI 链不同源。"),
"0041CE90":dict(ring3="FAIL", ring2="PASS", ring4="PASS",
  why3="29B/11 指令极小函数，channel A p3=0、无跳表：唯一 call->test 路径两路动作签名相同、被调返回不可伪证，③a 直线转发而非 ③b；无 ③b①/③b③/③b④。③不成立。",
  why4="vt 007E2868 槽 007E2880(=entry,slot6) 构造安装点 0041C900/0041CE44/0041CFE6，[reg+0x18] 派发链（dispatch 367 处），.text 与 ② RTTI 链不同源。"),
"0041CFE0":dict(ring3="PASS", ring2="PASS", ring4="PASS",
  why3="站点 call dword ptr [edx+0x10]@0x0041D01A (FF 52 10；edx=[0xA8B218] 运行时全局对象) -> 零间隔 cmp eax,-1@0x0041D01D (83 F8 FF) -> je@0x0041D020->0x0041D04F。-1 为 falsifiable 哨兵（未找到索引）。je 成立路 0x0041D04F 直接 base-dtor+ret；不成立路 0x0041D022 起 cmp eax,[0xA8B228] 边界检查、0x0041D02F mov [0xA8B228],ecx（非栈写）、0x0041D037 起 inc eax / mov edx,[ecx+eax*4] / mov [ecx+eax*4-4],edx 数组前移循环（循环体非栈写+边界检查）。两路动作真不同，cmp 与 je 间无 eax 覆写，非 bool/纯转发/malloc 模板/多路同一 call。③b② 成立。",
  why4="vt 007E2868 槽 007E2888(=entry,slot8) 构造安装点 0041C900/0041CE44/0041CFE6，[reg+0x20] 派发链在 .text（dispatch 358 处），与 ② 的 .rdata RTTI 链不同源。"),
"00450630":dict(ring3="FAIL", ring2="FAIL", ring4="FAIL",
  why3="915B/248 指令函数，channel A p3=0、无跳表：2 处 call->test 路径被调返回无 falsifiable imm 常量、两路动作签名不足以构成可伪证返回约定；无 ③b①/③b③/③b④。③不成立。",
  why2="该 entry 作为 4B VA 在非 .text 段全镜像 0 命中，无虚表槽、无 RTTI 链；名字 fn_00450630 为匿名形态，按 D-40 ② 无法独立取证 -> FAIL。",
  why4="direct caller 1 个（004401B6），无虚表槽、无活虚表派发链；按『direct-only 不足』且 ② 已 FAIL，④ 不成立。"),
}

# 为 16 个有 RTTI 的行补 ② / ④ 理由（每行引用自己的槽号/类名/偏移，非共用空话）
for e,dd in D.items():
    if e in RTTI:
        sv,vt,off,slotno,col,td,name=RTTI[e]
        dd.setdefault("why2",
          "虚表槽 %s 驻 .rdata，回扫 [vt-4]=COL %s(sig=0)->[COL+0xC]=TD %s->TD+8 名串 %s；"
          "vtable base=%s、slot offset=+%d(=slot#%d)，名串类与名字线索一致且 slot offset/4=%d=线索槽号，"
          "② 由 RTTI 数据链独立钉死（非仅凭 slotN 类名）。"%(sv,col,td,name,vt,off,slotno,slotno))
    if dd.get("ring4")=="PASS" and "why4" not in dd:
        dd["why4"]=(
          "vt %s 槽 %s(=entry,slot#%d) 由该虚表的构造安装点写入活对象，[reg+%d] 派发链位于 .text；"
          "派发见证与 ② 的 .rdata RTTI 数据链不同源（行自有槽地址 %s，slot offset +%d）。"
          %(vt,sv,slotno,off,sv,off))

def rtti_block(e):
    if e not in RTTI:
        return ["- ② 无虚表槽/RTTI：见 why2"]
    s=list(RTTI[e])
    slotva,vt,off,slotno,col,td,name=s
    L=[]
    L.append("- 槽驻留 %s [.rdata]，vtable base=%s，slot offset=+%d (=slot#%d)"%(slotva,vt,off,slotno))
    L.append("- RTTI 扩展回扫(kmax=400): COL=%s(sig=0) -> TD=%s -> name=%s"%(col,td,name))
    L.append("- [vt-4]=COL、VT[%d]=%s(=entry)，slot offset/4=%d=名字线索槽号；② 独立钉死"%(slotno,slotva,slotno))
    return L

count=0
for row in rows:
    e=row["entry"]; nm=row["name"]
    d=D[e]; r=ana[e]
    size=r["atlas"].get("size",0)
    b=R.read_va(int(e,16),16)
    first=r["first_insns"][:4]
    four = (d["ring2"]=="PASS" and d["ring3"]=="PASS" and d["ring4"]=="PASS")
    L=[]
    L.append("# ROW %s  S05  %s"%(e,nm))
    L.append("")
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s（大写十六进制、无 0x；delta entry 列原样写此串）"%e)
    L.append("- atlas size=%d B，反汇编 n_instr=%d，skipdata=%d，in_text=%s"%(size,r["n_insn_disasm"],r["n_skipdata"],r["in_text"]))
    L.append("- 函数体 [0x%s,0x%s)；入口 16B: %s"%(e,hx(int(e,16)+size)," ".join("%02X"%x for x in b)))
    for x in first: L.append("    %s"%x)
    L.append("")
    L.append("## 环② 类身份（独立取证；Class::slotN 的 Class 仅作线索，已由 RTTI/虚表钉死）")
    L+=rtti_block(e)
    L.append("- "+d["why2"])
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）"%d["ring3"])
    if r["chA_sites"]:
        for s in r["chA_sites"][:4]:
            L.append("- 站点: call=%s callee=%s %s imm=%s jcc=%s"%(hx(va(s["call_addr"])),
                hx(va(s["callee"])) if s.get("callee") else "None(间接)",s["test_kind"],s["test_imm"],s["jcc_mnemonic"]))
    else:
        L.append("- 无 ③b② 机械站点（channel A p3=0）；channel B 跳表站点=%d"%len(r["chB"]))
    L.append("- eax 覆写陷阱: %d 处站点在 test/cmp 与 jcc 之间覆写 eax"%sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"]))
    L.append("- 判定: "+d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者 / 活虚表派发；与 ② 不同源）")
    L.append("- "+d["why4"])
    dc=r["direct_callers"]
    L.append("- direct callers(%d): %s"%(len(dc),", ".join(dc[:8]) if dc else "无"))
    L.append("")
    L.append("## 裁定")
    L.append("- ①=%s ②=%s ③=%s ④=%s ②④独立=%s"%(
        "PASS" if r["in_text"] else "FAIL", d["ring2"], d["ring3"], d["ring4"],
        "是（.rdata RTTI 数据链 vs .text 构造安装/派发链）" if d["ring2"]=="PASS" else "n/a"))
    L.append("- **四环齐全=%s**；%s"%("是 -> [已证]" if four else "否 -> 不产出",
        "产出 delta 行。" if four else "按宁严不宽不产出。"))
    L.append("")
    L.append("## 本行地址锚")
    anchors=[e]+[hx(va(s["call_addr"])) for s in r["chA_sites"][:3]]
    L.append("- "+"；0x".join(anchors))
    with open(os.path.join(EVID,"ROW_%s.txt"%e),"w",encoding="utf-8") as f:
        f.write("\n".join(L)+"\n")
    count+=1
    print("wrote ROW_%s.txt ring2=%s ring3=%s ring4=%s four=%s"%(e,d["ring2"],d["ring3"],d["ring4"],four))
print("done %d evidence files"%count)
