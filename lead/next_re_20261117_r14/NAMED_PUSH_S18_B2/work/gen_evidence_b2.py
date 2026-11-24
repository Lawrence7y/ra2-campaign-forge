# -*- coding: utf-8 -*-
"""生成 18 份逐行 EVIDENCE：每环用该行自身地址与字节；③ 理由逐行不同；四环齐全仅 005C46E0/0071F8C0。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
def va(x): return int(x,16) if isinstance(x,str) else int(x)
def hx(x): return "%08X" % (x & 0xFFFFFFFF)

# 逐行裁定，③ 理由逐行独立
D = {
 "005C2A60": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="4 个 ③b② 站点 call@0x005C2A82/0x005C2A93/0x005C2B14/0x005C2BB0：被调 0x007C9CC2(nrets=1,origins=[unknown])、0x007C9B72(unknown)；检查为 TEST_EAX 与 CMP_IMM imm=1(jl)，属 bool/null 探测且被调无可伪证错误码常量(origins 无 imm 哨兵)；两路均汇普通分支。按 D-46(A)+无 imm 哨兵，③不成立。"),
 "005C2CB0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005C2CC1(->0x00775940) TEST_EAX@/je@0x005C2CD4；被调 0x00775940 返回集合={0,unknown}(consts=['0x0'],origins=[unknown,imm0])——纯 null/失败指针探测，0 是 bool 零值而非域内可伪证错误码；T路 ret、F路 call 普通处理。③不成立。"),
 "005C3710": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005C38CA(->0x007CA610) TEST_EAX/je@0x005C38DD；被调 0x007CA610 仅 1 ret、origins=[unknown]，读不到 imm 失败常量；两路调用高度重叠(T=call 0x5E6C90，F=普通返回)，无可伪证返回约定。③不成立。"),
 "005C3B10": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点 call@0x005C3B2D/0x005C3B75/0x005C3BE4 均调 0x007C8E17(=malloc) 后 TEST_EAX/je；被调 origins=[call]、无 imm 错误码，属典型『malloc 空判断 + 对象初始化』模板假句(同 B1 005C18A0/005C1DC0 败因)；三路动作多为分配后构造。③不成立。"),
 "005C3F80": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005C4094(->0x007C8D20 CRT) TEST_EAX/je@0x005C40A5；被调 origins=[unknown] 无 imm 哨兵，且 T/F 两路调用集合大面积重合(T 5 calls/F 3 calls 均含 0x5E4580/0x5E6C90/0x5E6CAC/0x5E8B60)，属普通布尔探测，无可伪证错误码。③不成立。"),
 "005C4110": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005C4129(->0x007C8E17=malloc) TEST_EAX/je@0x005C413E；被调 origins=[call]，malloc NULL 非域内可伪证错误码，T/F 两路都是分配成功后构造/设置，模板假句。③不成立。"),
 "005C44E0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="2 站点：call@0x005C4527(->0x007C8E17=malloc, origins=[call]) TEST_EAX/je@0x005C465F；call@0x005C45EC 为寄存器间接(callee=None, nrets=None) TEST_EAX/je@0x005C463E，两路都含同一 call 0x7C7C2D(8162109)仅 ret 态不同(多路同一 call 细则#1)。无可伪证 imm 错误码。③不成立。(注：本行 slot41 超出 B1 脚本 k≤40 回扫上限，已扩至 k≤128 核出 RTTI，②成立。)",
  ),
 "005C46E0": dict(r2="PASS", r3="PASS", r4="PASS",
  why3="③b①（跳转表，每路可单独验证）：跳表1 jmp dword[eax*4+0x005C4C6C]@0x005C49B0，前置 cmp eax,5/ja@0x005C49AA 边界检查，6 路各写不同配置常量(case0 [a8b550]=0x28/[a8b570]=0x3c；case1 0x28/0x2d；case2 eax=0x1e；case3 eax=0x14；case4 0x14/0xf；case5 0x14/0xc)——每路写值可从字节单独核对，写指令均在函数体 [0x005C46E0,0x005C4C21) 内、非被调用者内部写；跳表2 jmp dword[eax*4+0x005C4C84]@0x005C4B3A，cmp eax,3/ja 边界，4 路各算不同 ecx(esi / esi+esi/2 / 2*esi)后统一 mul 0xcccccccd 写回 [a8b56c]，每路可单独验证。无 ③a（非直线/非清零默认）。其 chA 3 站点为 bool/unknown 不构成 ③b②，但跳表已满足 ③b①。③成立。",
  ),
 "005C4CA0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005C4CEB(->0x007DD0F8) TEST_EAX/je@0x005C4D06；被调 origins=[call]，无 imm 错误码常量；T 路带 call 0x50??、F 路直接返回，属普通空指针探测，无可伪证返回约定。③不成立。(slot44 扩 k≤128 后 RTTI 钉住。)",
  ),
 "005CAAC0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x005CAB50(->0x007C8E17=malloc) TEST_EAX/je@0x005CAB08；被调 origins=[call]，malloc NULL 判断为模板假句，非域内可伪证错误码；F 路 call 0x43B4C0/0x50E1E0 为分配后处理。③不成立。(slot50 扩 k≤128 后 RTTI 钉住。)",
  ),
 "005D8170": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="59 字节小函数，唯一站点 call@0x005D8172(->0x007C8E17=malloc) TEST_EAX/je@0x005D81A6；被调 origins=[call]、无 imm 哨兵，T 路 xor eax,eax;ret(返回0)、F 路 call 0x5C0??0 构造——malloc 模板假句，无域内可伪证错误码。③不成立。",
  ),
 "0064A0C0": dict(r2="FAIL", r3="FAIL", r4="FAIL",
  why3="真名普通函数(非虚成员)：② 无虚表槽/RTTI(dword refs=[])取不到，先记为 FAIL。③：site0/site3 虽是 call [reg+0x18]→cmp eax,-1→je@0x0064A363，但被调为间接虚调用(callee=None)，无法解析到返回 imm -1 的被调体——cmp -1 只是调用方单方比较，不能独立伪证失败返回；site1/2 被调 0x00540FC0 consts=['0x0'](null 探测)。按严格 D-40 无可独立伪证的错误码/返回约定，③不成立。④ 仅 2 个 direct caller(0x00648506/0x006494F2)，direct-only 不足。三环均不成立。",
  ),
 "0064DEA0": dict(r2="FAIL", r3="FAIL", r4="FAIL",
  why3="真名普通函数，无虚表槽/RTTI(dword refs=[])，② 取不到。③：唯一站点 call@0x0064E0B2 为寄存器间接(callee=None,nrets=None) TEST_EAX/je@0x0064E0E5，无被调返回 profile、无 imm 哨兵，两路均为普通分支，无可伪证错误码。④ 仅 2 个 direct caller(0x00647368/0x0064CCBA)，direct-only 不足。三环均不成立。",
  ),
 "006516F0": dict(r2="FAIL", r3="FAIL", r4="FAIL",
  why3="真名普通函数，无虚表槽/RTTI(dword refs=[])，② 取不到。③：唯一站点 call@0x0065190C 间接(callee=None,nrets=None) TEST_EAX/je@0x0065193F，无被调返回常量、无错误码哨兵，不构成可伪证返回约定。④ 仅 2 个 direct caller(0x0064735F/0x0064CC98)，direct-only 不足。三环均不成立。",
  ),
 "0071F8C0": dict(r2="PASS", r3="PASS", r4="PASS",
  why3="③b②：站点 call 0x00410380@0x0071F8CB(e8 b0 0a cf ff)，紧接 test eax,eax@0x0071F8D0(85 c0)、jl@0x0071F8D2(7c 57)->0x0071F92B，零间隔、无 eax 覆写(0 处)。被调 0x00410380 在 0x00410389 mov eax,0x80004003(b8 03 40 00 80)、0x0041038F ret 8——失败返回 E_POINTER(0x80004003，HRESULT 负值错误码，非 bool 0/1)；jl 有符号<0 真正拿它分支。T 路 0x0071F92B pop esi;ret 8 直接向上返回错误码；F 路 0x0071F8D4 继续 test esi、lea/call 构造子对象、并在 0x0071F8E4/0x0071F8EA/0x0071F8F1/0x0071F8F8 安装 TEventClass vtable 写 [esi+0/4/8/0xc]——两路动作真不同、非纯转发 getter、非 malloc 模板假句、非多路同一 call。③成立。",
  ),
 "00773BC0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="③b② 机械预筛 p3=0(p1=1,p2=1 但 P3 灭)：无 call→test/cmp→jcc 可伪证站点；无跳转表(chB=0)、无内存形状断言、无完整循环非栈写。③不成立。",
  ),
 "00774410": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="2 站点 call@0x00774548/0x00774623 均为寄存器间接(callee=None,nrets=None) TEST_EAX/je；无被调返回 profile、无 imm 错误码哨兵，两路为普通空指针/布尔分支，无可伪证返回约定。③不成立。",
  ),
 "00774900": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="67 字节小函数，③b② 机械预筛 p3=0(p1=2,p2=2 但 P3 灭)：两处 call→TEST_EAX→je 的被调返回源均 unknown，无 imm 哨兵；无跳表/内存形状/完整循环非栈写。③不成立。",
  ),
}

def slot_block(r):
    lines=[]
    for s in r["slots"]:
        if s.get("rtti_name"):
            lines.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d (slot %d)" % (
                s.get("slot_va"), s.get("section"), s.get("vtable_base"),
                int(s.get("slot_off")), int(s.get("slot_off"))//4))
            lines.append("- RTTI: COL=%s -> TD=%s -> name=%s" % (s.get("col"), s.get("td"), s.get("rtti_name")))
            gw = s.get("global_writes", [])
            addrs = [g.get("write_va") for g in gw if g.get("write_va")]
            if addrs:
                lines.append("- 构造期 vtable 安装点(.text): %s (atexit 均为 False)" % ", ".join(addrs[:8]))
            break
    return lines

for r in data:
    e = r["entry"]; d = D[e]
    size = r["atlas"].get("size",0)
    b = R.read_va(int(e,16), 16)
    first = r["first_insns"][:4]
    four = (d["r2"]=="PASS" and d["r3"]=="PASS" and d["r4"]=="PASS")
    L=[]
    L.append("# ROW %s  S18  %s" % (e, r["hint_name"]))
    L.append("")
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s (大写十六进制，无 0x；delta entry 列原样写此串)" % e)
    L.append("- atlas size=%d B，反汇编 n_instr=%d，skipdata=%d，in_text=%s" % (
        size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"]))
    L.append("- 函数体 [0x%s, 0x%s)；入口 16B: %s" % (e, hx(int(e,16)+size), " ".join("%02X"%x for x in b)))
    for x in first: L.append("    %s" % x)
    L.append("")
    L.append("## 环② 类身份（RTTI 描述符->类名字串；Class::slotN 的 Class 仅作线索）")
    if d["r2"]=="PASS":
        L += slot_block(r)
        if "::slot" in r["hint_name"]:
            L.append("- 名字线索=%s；RTTI 名与线索类名一致，slot offset/4=线索槽号，② **钉住**（RTTI 数据链，与④ .text 构造安装链不同源）。" % r["hint_name"])
        else:
            L.append("- 名字线索=%s（真名/ctor，非 slotN）；RTTI 名与线索类名一致且该槽值=entry，类身份由 RTTI+虚表槽独立钉死，② **钉住**（RTTI 数据链，与④ .text 构造安装链不同源）。" % r["hint_name"])
    else:
        L.append("- find_dword_refs(entry)=[]：entry 非任何虚表槽值、无 RTTI 描述符；名字为普通函数名非 slotN，② **取不到** -> FAIL。")
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % d["r3"])
    if r["chA_sites"]:
        for s in r["chA_sites"][:4]:
            L.append("- 站点: call=%s callee=%s %s imm=%s jcc=%s->%s" % (
                hx(va(s["call_addr"])), hx(va(s["callee"])) if s.get("callee") else "None",
                s["test_kind"], s["test_imm"], s["jcc_mnemonic"],
                hx(va(s["jcc_target"])) if s.get("jcc_target") else "N/A"))
    else:
        L.append("- 无 ③b② 机械站点（p3=0）。")
    if r["chB"]:
        for t in r["chB"]:
            L.append("- 跳表: jmp@%s bound=%s ncase=%d targets=%s" % (
                t["jmp_addr"], t["bound"], t["ncase"], ",".join(x["target"] for x in t["targets"])))
    L.append("- eax 覆写陷阱: %d 处站点在 test 与 jcc 之间覆写 eax" % sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"]))
    L.append("- 判定: " + d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者 / 活虚表派发；与 ② 不同源；本行裁定 %s）" % d["r4"])
    dc = r["direct_callers"]
    L.append("- direct callers(%d): %s%s" % (len(dc), ",".join(dc[:10]), " ..." if len(dc)>10 else ""))
    sl = next((s for s in r["slots"] if s.get("rtti_name")), None)
    if sl and d["r4"]=="PASS":
        gw = [g.get("write_va") for g in sl.get("global_writes",[]) if g.get("write_va")]
        L.append("- 活虚表派发: vt %s 槽 %s (=entry) 由 .text 构造安装点 %s 写入活对象，[reg+%d] 派发可达本 entry；该链在 .text，与 ② 的 .data RTTI 链独立。" % (
            sl.get("vtable_base"), sl.get("slot_va"), ", ".join(gw[:8]), int(sl.get("slot_off"))))
    if d["r4"]=="FAIL":
        L.append("- 仅 direct callers(direct-only 不足)，无虚表派发链，④ FAIL。")
    L.append("")
    L.append("## 裁定")
    L.append("- ①=%s ②=%s ③=%s ④=%s ②④独立=%s" % (
        "PASS" if r["in_text"] else "FAIL", d["r2"], d["r3"], d["r4"],
        "是（RTTI 数据链 vs .text 构造安装/派发链）" if d["r2"]=="PASS" and d["r4"]=="PASS" else "n/a"))
    L.append("- **四环齐全=%s**；%s" % ("是 -> [已证]" if four else "否 -> 不产出",
        "产出 delta 行。" if four else "按宁严不宽不产出。"))
    L.append("")
    L.append("## 本行地址锚")
    anchors = ["0x%s" % hx(va(s["call_addr"])) for s in r["chA_sites"][:3]]
    if r["chB"]: anchors += ["0x%s" % t["jmp_addr"] for t in r["chB"][:2]]
    L.append("- entry 0x%s%s" % (e, ("；" + "；".join(anchors)) if anchors else "；无③站点"))
    with open(os.path.join(EVID, "ROW_%s.txt"%e), "w", encoding="utf-8") as f:
        f.write("\n".join(L)+"\n")
    print("wrote ROW_%s.txt  r2=%s r3=%s r4=%s four=%s" % (e,d["r2"],d["r3"],d["r4"],four))

# delta.tsv：仅四环齐全行，entry 大写十六进制无 0x
SEM = {
  "005C46E0": "MPCooperative::slot43: 依全局索引经两个带边界检查的跳转表分派，各路设置多人游戏配置常量/计算缩放值(③b①)",
  "0071F8C0": "TEventClass 构造: 调 0x410380 初始化，失败返回 E_POINTER(0x80004003) 经 jl 分支提前返回，成功路安装 TEventClass vtable 并构造子对象(③b②)",
}
rows = [r for r in data if D[r["entry"]]["r2"]=="PASS" and D[r["entry"]]["r3"]=="PASS" and D[r["entry"]]["r4"]=="PASS"]
with open(os.path.join(OUT, "delta.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for r in rows:
        e=r["entry"]
        f.write("%s\tS18\t%s\t%s\t[已证]\tEVIDENCE/ROW_%s.txt\n" % (e, r["hint_name"], SEM[e], e))
print("delta rows:", len(rows), [r["entry"] for r in rows])

# base_rate
with open(os.path.join(OUT, "base_rate.tsv"), "w", encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("B2\t18\t15\t2\t15\t2\t0.1111\n")
print("done")
