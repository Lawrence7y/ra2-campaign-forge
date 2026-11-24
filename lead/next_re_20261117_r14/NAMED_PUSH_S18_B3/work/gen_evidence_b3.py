# -*- coding: utf-8 -*-
"""生成 B3 的 18 份逐行 EVIDENCE：每环用该行自身地址与字节；③ 理由逐行不同。
裁定：②18/18 PASS（RTTI 钉死）、④18/18 PASS（活虚表派发）、③18/18 FAIL（瓶颈）=> 四环齐全 0 行。"""
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

# 逐行裁定：③ 理由逐行独立，均引用本行自身地址/被调。
D = {
 "00774CD0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 个 ③b② 站点：call@0x00774DF4/0x00774E92(->0x007CAF30, consts=['0x0'], origins=[unknown,imm0]) 与 call@0x00774EF3(->0x007C8DF0, nrets=1, origins=[unknown])，均 TEST_EAX->je(0x00774D5F/0x00774EB3/0x00774F0D)。被调 0x7CAF30 为 strchr 类字符串扫描(返回 0 或未知指针)、0x7C8DF0 无 imm 错误码常量——都是 NULL/布尔探测，非可伪证错误码(D-46(A))。循环 0x00774EB7..0x00774EC2 为剥 CR/LF 的紧循环，循环体内只有 inc esi(jmp 回边)，无写；0x00774E3B 的 mov byte ptr[ecx+ebp-1],0 在循环外，属一次性置终止符，不构成 ③b④。③不成立。"),
 "00774F50": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="③b② 机械预筛 p3=0(p1=3,p2=2 但 P3 灭)：全函数无 call->test/cmp->jcc 可伪证站点；无跳转表(chB=0)、无内存形状断言、无完整循环非栈写(NO_BACKWARD_JUMP)。仅 WinModemClass 事件处理空壳，③不成立。"),
 "00775110": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="2 站点 call@0x0077532D/0x00775347(->0x007CA4B0, consts=['0x0'], origins=[unknown,imm0]) TEST_EAX->jne(0x00775473/0x0077543A)。T 路经 path_sig 仅返回小整数 1/2(rets=[2]/[1])、F 路调 0x007CA4A0 普通处理——被调 0x7CA4B0 返回 0 或未知值，属 bool/小整数探测，0 是零值而非域内可伪证错误码(D-46(A))。循环 0x007751C8..0x00775423 体内无非栈写。③不成立。"),
 "007A3100": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="7 站点均调 CRT/未知函数：call@0x007A3909(->0x7C8D20,unknown)、0x007A3996(->0x007ADA70,consts=[],origins=[unknown,call],CMP_IMM imm=1)、0x007A3A4F/0x007A3A5D(->0x00775940,null)、0x007A3ADF/0x007A3AE4/0x007A3AEE(origins=[call]/[unknown])。全为 NULL/布尔探测，无可伪证 imm 错误码；且 0x007A3A4F 与 0x007A3A5D 两路调用集合高度重合(含 0x65D000/0x77B300)。循环 0x007A31D5/0x007A32DF/0x007A3391 体内 mov dword ptr[edx+eax*4],0 为数组清零(③a 模板假句，禁作 ③b④)。③不成立。"),
 "007A3D90": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="2 站点 call@0x007A4017(->0x005E2CD0, consts=['0x0'], origins=[imm0,call]) 与 call@0x007A4021(->0x00775940, origins=[unknown,imm0])，均 TEST_EAX->je@0x007A4047；T 路 ret0、F 路多调 0x00777000。被调返回 0 或未知(NULL/布尔)，非域内可伪证错误码；两站紧邻(0x007A4017/0x007A4021)同汇一处 je，属多路同一分支。NO_BACKWARD_JUMP 无 ③b④。③不成立。"),
 "007A4070": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x007A40A2(->0x00775940, consts=['0x0'], origins=[unknown,imm0]) TEST_EAX->je@0x007A40C8。被调返回 0/unknown，为 NULL/布尔探测(0 是零值非错误码，D-46(A))；无 imm 失败哨兵、无 signed 错误码分支。121 字节小函数、NO_BACKWARD_JUMP。③不成立。"),
 "007A41C0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="14 站点中 10 个调 0x007C9CC2(nrets=1, origins=[unknown]) TEST_EAX->je(如 0x007A4646/0x007A467B/0x007A4732/0x007A4767/0x007A4832/0x007A4867/0x007A4914/0x007A4949/0x007A4A12/0x007A4A57)，均 NULL 探测无 imm 错误码，且多路共用 call 0x007C9CC2(仅参数不同，细则#1)。site11 call@0x007A4B72(->0x004068E0 空 thunk ret) CMP_IMM imm=1 jle 为布尔比较。site12 call@0x007A4BBB(->0x00734E60) 的 0x84583c 哨兵与后续 TEST_EAX@0x007A4BCC 不同源——中间隔了 call@0x007A4BC7(0x775940)，被测试的是 0x775940 返回值(NULL 探测)。循环 0x007A4AD8..0x007A4B60 体内无非栈写。③不成立。"),
 "007A4C10": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="2 站点：call@0x007A4C54(->0x00775940, origins=[unknown,imm0]) TEST_EAX->je@0x007A4C77 = NULL 探测；call@0x007A4CB7(->0x005E2CD0, consts=['0x0']) CMP_IMM imm=7 je@0x007A4E9E = 枚举/类型等值判断(非错误码)。二者 T/F 路均普通分支、无 imm 失败哨兵。NO_BACKWARD_JUMP 无 ③b④。③不成立。"),
 "007A5290": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="本行是唯一含跳转表者：cmp eax,0x10/ja@0x007A52C0 边界检查 + mov cl,byte[eax+0x7A55DC] 映射 + jmp dword[ecx*4+0x7A55C8]@0x007A52CE(5 路: 0x007A52D5/0x007A530E/0x007A5346/0x007A535C/0x007A5401)。输入 eax=[esp+8] 为 HRESULT(0x80040075/76/77/78)，函数按错误码选错误串消息(0x1669..0x1693)——语义成立但 ③b① 不成立：各路压入不同消息号/ecx 后全部汇入同一批 call 0x00734E60(GetErrorString)、0x007CA489、[0x7E1234]，仅参数不同(细则#1『多路同一 call』不计)，且真正的写发生在被调 0x00734E60 内部(禁把被调内写当本函数写)；本函数体无写指令。func 自身 xor eax,eax;ret 0xC 恒返回 0，无可伪证返回约定(③b② 亦 FAIL，chA site0 call@0x007A53EF 间接 callee=None、site1 call@0x007A54C4->0x7C9CC2 NULL 探测)。③不成立。"),
 "007A55F0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x007A561F(->0x007C9CC2, nrets=1, origins=[unknown]) TEST_EAX->je@0x007A565C。被调无 imm 错误码、单 ret origins=unknown，T 路 ret0、F 路多调 0x007C9CC2/0x007A5710——NULL 探测非可伪证返回约定。145 字节小函数、NO_BACKWARD_JUMP。③不成立。"),
 "007A5690": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点：call@0x007A56DA/0x007A583B(->0x00775940, origins=[unknown,imm0]) 与 call@0x007A57F1(->0x004068E0 空 thunk, origins=[unknown]) TEST_EAX->je(0x007A56FD/0x007A5836/0x007A5861)。被调返回 0/unknown，NULL/布尔探测；无 imm 错误码、无 signed 错误码分支。NO_BACKWARD_JUMP 无 ③b④。③不成立。"),
 "007A5890": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="7 站点多为 CRT/NULL 探测：0x007A5CAE(->0x5E2CD0)、0x007A5D63/0x007A5E2E/0x007A6A7A(->0x7C8D20 或 0x775940, origins=[unknown]) 等 TEST_EAX/je。0x007A6A74(->0x7B5440, consts=['0x889f64']) 的哨兵与 TEST_EAX@0x007A6A82 不同源——中间隔 call@0x007A6A7A(0x7C8D20)，测的是 CRT 返回值；0x889f64 是 GetAt 类函数在内部指针为 NULL 时的回退值，非经调用方错误码分支消费。循环 0x007A6645..0x007A6669 体内 mov dword ptr[esi],0 为数组清零(③a 模板)。③不成立。"),
 "007A7110": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="9 站点含间接调用(site0 call@0x007A71C6、site4 call@0x007A781A, callee=None 无 profile)、CRT(site2/3/5 ->0x7C8D20)与 site1 call@0x007A75AD(->0x7B5440, consts=['0x889f64'])——后者哨兵与 TEST_EAX@0x007A75BB 不同源(隔 call@0x007A75B3->0x7C8D20)，测的是 CRT 返回。全为 NULL/布尔探测，无 imm 错误码+signed 分支。循环 0x007A7595..0x007A75CE、0x007A783F..0x007A7885 体内无非栈写。③不成立。"),
 "007A7EA0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="唯一站点 call@0x007A7F62(->0x007C8D20, nrets=1, origins=[unknown]) TEST_EAX->je@0x007A8218，被调无 imm 错误码常量、T 路 ret0/F 路普通分配处理——NULL 探测非可伪证错误码。其余 9 个 P1 候选被 P2(两路动作相同)灭。循环 0x007A7FAE 附近体内无非栈写。③不成立。"),
 "007A8260": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点：call@0x007A8410(->0x7B5400, consts=['0x889f64'])、0x007A8416(->0x7C8D20)、0x007A85D6(->0x7C9CC2) TEST_EAX->je(0x007A8457/0x007A85FF)。0x889f64 哨兵与 TEST_EAX@0x007A841E 不同源(隔 call@0x007A8416->0x7C8D20)，实为 CRT NULL 探测；多路紧邻同汇 0x007A8457(细则#1)。循环 0x007A82D6..0x007A8435 等体内无非栈写。③不成立。"),
 "007A8DA0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点均调 0x00775940(NULL 探测, origins=[unknown,imm0])：call@0x007A8E17/0x007A8E29 TEST_EAX->je@0x007A8E24/0x007A8E36，call@0x007A8E94(->0x7C8D20,unknown) TEST_EAX->je@0x007A8EB9。被调返回 0/unknown，T/F 路均普通分支、无 imm 错误码。NO_BACKWARD_JUMP 无 ③b④。③不成立。"),
 "007A8ED0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点：call@0x007A8F0E/0x007A8F1C(->0x00775940, consts=['0x0'], origins=[unknown,imm0]) TEST_EAX->jne@0x007A8F54；call@0x007A8F8A(->0x7C8D20,unknown) TEST_EAX->je@0x007A8FAF。全为 NULL/布尔探测，无 imm 错误码与 signed 分支；0x007A8F0E/0x007A8F1C 两路紧邻同汇 0x007A8F54(细则#1)。NO_BACKWARD_JUMP。③不成立。"),
 "007A8FC0": dict(r2="PASS", r3="FAIL", r4="PASS",
  why3="3 站点与 007A8DA0 同族但本行地址不同：call@0x007A9050/0x007A9062(->0x00775940, origins=[unknown,imm0]) TEST_EAX->je@0x007A905D/0x007A906F，call@0x007A90CD(->0x7C8D20,unknown) TEST_EAX->je@0x007A90F2。被调返回 0/unknown = NULL 探测，无可伪证错误码；两路紧邻同汇。NO_BACKWARD_JUMP。③不成立。"),
}

def slot_block(r):
    lines=[]
    for s in r["slots"]:
        if s.get("rtti_name"):
            lines.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d (slot %d)，槽值=entry(已复核)" % (
                s.get("slot_va"), s.get("section"), s.get("vtable_base"),
                int(s.get("slot_off")), int(s.get("slot_off"))//4))
            lines.append("- RTTI: COL=%s -> TD=%s -> name=%s" % (s.get("col"), s.get("td"), s.get("rtti_name")))
    gw=[]
    for s in r["slots"]:
        if s.get("rtti_name"):
            gw += [g.get("write_va") for g in s.get("global_writes",[]) if g.get("write_va")]
    if gw:
        lines.append("- 构造期 vtable 安装点(.text): %s" % ", ".join(dict.fromkeys(gw))[:200])
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
    L.append("- entry=%s (大写十六进制无 0x；delta entry 列原样写此串)" % e)
    L.append("- atlas size=%d B，反汇编 n_instr=%d，skipdata=%d，in_text=%s" % (
        size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"]))
    L.append("- 函数体 [0x%s, 0x%s)；入口 16B: %s" % (e, hx(int(e,16)+size), " ".join("%02X"%x for x in b)))
    for x in first: L.append("    %s" % x)
    L.append("")
    L.append("## 环② 类身份（RTTI 描述符->类名字串；slotN 的 Class 仅作线索）")
    if d["r2"]=="PASS":
        L += slot_block(r)
        L.append("- 名字线索=%s；RTTI 名与线索类名一致、slot offset/4=线索槽号、槽值=entry，② **钉住**（RTTI 数据链，与④ .text 构造安装/派发链不同源）。" % r["hint_name"])
    else:
        L.append("- find_dword_refs(entry)=[]，② 取不到。")
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % d["r3"])
    if r["chA_sites"]:
        for s in r["chA_sites"][:4]:
            L.append("- 站点: call=%s callee=%s %s imm=%s jcc=%s->%s" % (
                hx(va(s["call_addr"])), hx(va(s["callee"])) if s.get("callee") else "None(indirect)",
                s["test_kind"], s["test_imm"], s["jcc_mnemonic"],
                hx(va(s["jcc_target"])) if s.get("jcc_target") else "N/A"))
    else:
        L.append("- 无 ③b② 机械站点（p3=0）。")
    if r["chB"]:
        for t in r["chB"]:
            L.append("- 跳表: jmp@%s %s bound=%s ncase=%d" % (
                t["jmp_addr"], t["op_str"], t["bound"], t["ncase"]))
    L.append("- eax 覆写陷阱: %d 处站点在 test 与 jcc 之间覆写 eax" % sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"]))
    L.append("- 判定: " + d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者 / 活虚表派发；与 ② 不同源；本行裁定 %s）" % d["r4"])
    dc = r["direct_callers"]
    L.append("- direct callers(%d): %s%s" % (len(dc), ",".join(dc[:10]), " ..." if len(dc)>10 else ""))
    sl = next((s for s in r["slots"] if s.get("rtti_name")), None)
    if sl and d["r4"]=="PASS":
        gw = [g.get("write_va") for g in sl.get("global_writes",[]) if g.get("write_va")]
        L.append("- 活虚表派发: vt %s 槽 %s (=entry) 由 .text 构造安装点 %s 写入活对象；dispatch_sites=%d 条 [reg+%d] 派发可达本 entry；该链在 .text，与 ② 的 .data RTTI 链独立。" % (
            sl.get("vtable_base"), sl.get("slot_va"), ", ".join(gw[:6]) or "见②", len(sl.get("dispatch_sites",[])), int(sl.get("slot_off"))))
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

# delta.tsv：仅四环齐全行（本批 0 行）
rows = [r for r in data if D[r["entry"]]["r2"]=="PASS" and D[r["entry"]]["r3"]=="PASS" and D[r["entry"]]["r4"]=="PASS"]
with open(os.path.join(OUT, "delta.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for r in rows:
        e=r["entry"]
        f.write("%s\tS18\t%s\t%s\t[已证]\tEVIDENCE/ROW_%s.txt\n" % (e, r["hint_name"], "", e))
print("delta rows:", len(rows), [r["entry"] for r in rows])
print("DONE")
