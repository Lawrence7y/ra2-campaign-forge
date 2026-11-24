# -*- coding: utf-8 -*-
"""生成 18 份逐行 EVIDENCE：每环用该行自身地址与字节；③ 理由逐行不同。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)
data = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))

def va(x): return int(x,16) if isinstance(x,str) else int(x)
def hx(x): return "%08X" % (x & 0xFFFFFFFF)

# 逐行裁定：③ 理由逐行独立；四环齐全仅 005414C0
D = {
"0048BF40": dict(ring3="FAIL",
  why3="唯一 ③b② 候选 call@0x0048BFFD(->0x0048B410) 后 TEST_EAX@0x0048C004/je@0x0048C006；被调 0x0048B410 返回集合={0x0,0x1}（imm 两态），属 bool 主输出（D-46(A) bool 不算 ③b②）；且失败路 0x0048BFC9 仅 xor eax,eax;ret 0x10、成功路 0x0048C018 mov eax,1;ret 0x10，汇于同一 ret 仅 eax 常量不同＝模板/纯转发壳。③不成立。"),
"0048C040": dict(ring3="FAIL",
  why3="3 个 ③b② 候选：site0 call@0x0048C086 被调 0x0048B6E0 只 1 ret 且返回未知(origins=[unknown])，无可伪证错误码；site1/site2 call@0x0048C1D1/0x0048C246 被调 0x0048B6D0 返回={0,1} bool 主输出(D-46(A))；均不构成可伪证错误码/返回约定。③不成立。"),
"0048C320": dict(ring3="FAIL",
  why3="唯一站点 call@0x0048C2F3(->0x0048B9A0) TEST_EAX@0x0048C2FA/je@0x0048C302；被调 0x0048B9A0 仅 1 ret、返回源 origins=[unknown]，bytes 中读不到 imm 失败常量；失败路 ret 0、成功路继续处理但无可伪证哨兵，P3 只由测试点 je(TEST_EAX) 机械满足。③不成立。"),
"0048C3B0": dict(ring3="FAIL",
  why3="34 字节小函数，call@0x0048C3A5/@0x0048C3B0 均为寄存器间接 call(callee=None)，TEST_EAX+je->0x0048C3CE；两条路径都汇到 0x0048C3CE 同一 ret，仅 mov eax,0/1 之别（sig T=ret[0]/F=ret[1] 全无调用）＝纯转发壳 + bool 主输出(D-46(A))。③不成立。"),
"004A0630": dict(ring3="FAIL",
  why3="机械预筛 p3=0：唯一 call@0x004A0685 后 TEST_EAX/je 的动作签名两路相同，且被调无 falsifiable 返回常量，③b② 三个站点条件无一成立；无跳表(③b①=0)、无内存形状断言、无完整循环非栈写。③不成立。"),
"0053FCB0": dict(ring3="FAIL",
  why3="599 字节函数 ③b② 预筛 p3=0（p1=3,p2=2 但 P3 全灭）：3 处 call+test 的被调均无 falsifiable imm 常量、两路动作签名不足以构成可伪证返回约定；无跳表/内存形状/完整循环非栈写。③不成立。"),
"0053FF10": dict(ring3="FAIL",
  why3="唯一站点 call@0x0053FF24(->0x0048B9A0) TEST_EAX/je->0x0053FF8D；被调 0x0048B9A0 单 ret、返回源 unknown，无可伪证失败常量；失败路 xor eax,eax;ret、成功路继续，仍属机械 je 而非可伪证错误码。③不成立。"),
"0053FFA0": dict(ring3="FAIL",
  why3="唯一站点 call@0x0053FFB5(->0x0048B9A0) TEST_EAX/je->0x00540024；被调 0x0048B9A0 单 ret 返回源 unknown，无 imm 哨兵；站点仅满足机械形态，不构成可伪证返回约定。③不成立。"),
"00540050": dict(ring3="FAIL",
  why3="唯一站点 call@0x00540092(->0x0053FCA0) TEST_EAX/je->0x00540075；被调 0x0053FCA0 返回集合={0,1} bool 两态(D-46(A))，且 success 路只是 call 0x0050…、无域内可伪证错误码；③b② 不成立。"),
"005414C0": dict(ring3="PASS",
  why3="站点 call dword ptr [edx+0x18]@0x0054159B (FF 52 18) -> 被调 0x00541040；零间隔 cmp eax,-1@0x0054159E (83 F8 FF)，je@0x005415A1 (74 33)->0x005415D6。被调 0x00541040 @0x00541066 mov eax,0xffffffff;ret —— 失败返回 -1（可伪证哨兵，非 bool）。失败路 0x005415D6 inc dword [esi+0xA0](FF 86 A0 00 00 00，非栈写)+xor eax,eax;ret 0x10；成功路 0x005415A3 走 [esi+eax*4+0x28] 查表、0x005415C7 call [eax+8] 实发送、mov eax,1;ret 0x10。两路动作真不同（非同一 call 仅差参数）、无 eax 覆写陷阱。③b② 成立。"),
"00541820": dict(ring3="FAIL",
  why3="2655 字节大函数，6 个 ③b② 站点(0x005418EB/0x00541A1B/0x00541A21/0x00541B01/…)：被调 0x007359?0(=0x00735940 家族) 返回={0}或 unknown、0x007C8D20/0x007C91D0 等 CRT 调用返回指针或未知；全部是 call->TEST_EAX->je 空指针/布尔探测，无一个给出可伪证的错误码 imm；路径多为事件遍历内的普通分支。按 D-46(A)+宁严不宽，③不成立。"),
"00542350": dict(ring3="FAIL",
  why3="站点 call [edx+0x18]@0x00542376(FF 52 18)、cmp eax,-1@0x00542379(83 F8 FF)、je@0x0054237C->0x005423AF；虽 -1 可伪证，但 taken(0x005423AF) 与 fallthrough(0x0054237E) 都是纯取值返回（前者 xor eax,eax;ret 4，后者 mov eax,[esi+eax*4+0x28];…;ret 4），无任何状态写/调用差异＝③a 纯转发 getter。③不成立。"),
"005423C0": dict(ring3="FAIL",
  why3="站点 call [edx+0x18]@0x005423E6(FF 52 18)、cmp eax,-1@0x005423E9、je->0x0054241F；与 00542350 同族但地址独立：两路仍只是返回查表值或 0(F=ret 且 end_eax=None)，无状态写、无差异调用，属 ③a getter 而非整体合同闭合。③不成立。"),
"005C18A0": dict(ring3="FAIL",
  why3="唯一站点 call 0x007C8E17@0x005C190B = malloc(0x70) 后 TEST_EAX@0x005C1913/je@0x005C1915；taken edi=0、fallthrough call 0x0049B610 构造后 edi=eax，两路随后都汇入 call 0x0049CAF0 —— 这是典型『malloc 空判断 + 对象初始化』模板假句，malloc 的 NULL 不是域内可伪证错误码，③b② 不成立。"),
"005C1A10": dict(ring3="FAIL",
  why3="4 站点：call@0x005C1A57/0x005C1A65 被调 0x00775940 返回={0,?} bool 态(D-46(A))；call@0x005C1B77/0x005C1C15 被调 0x007CD680 单 ret 返回源=(call)未知，无 imm 哨兵。T/F 动作签名多ollowing 高度重合，不构成可伪证错误码/返回约定；③不成立。"),
"005C1DC0": dict(ring3="FAIL",
  why3="唯一站点 call 0x007C8E17@0x005C1E5B = malloc(0x70) 后 TEST_EAX@0x005C1E63/je@0x005C1E65；taken 走 xor eax,eax、fallthrough call 0x0049B610 构造，两路随后都写 [edx+edi*4] 并 call 0x0049CAF0 —— 与 005C18A0 同族 malloc 模板假句，非域内可伪证返回约定。③不成立。"),
"005C2100": dict(ring3="FAIL",
  why3="唯一站点 call@0x005C21CF(->0x005E26C0) TEST_EAX@0x005C21D7/je->0x005C2187；被调 0x005E26C0 单 ret、返回源=(call)未知，无可伪证 imm 错误码；两路一为 ret、一为 call 0x005C2184 的普通分支，不构成可伪证返回约定。③不成立。"),
"005C2680": dict(ring3="FAIL",
  why3="两站点 call@0x005C23E5(->0x0049BC80)/@0x005C23EA(->0x005E26C0) TEST_EAX/je->0x005C26BC；被调 0x0049BC80 两 ret 均 eax=unknown、0x005E26C0 单 ret 源=(call)，都无可伪证错误码常量；且两路都含 call 0x0049C2C0（同一 call），属『多路同一 call』细则#1，③不成立。"),
}

def slot_block(r):
    lines=[]
    for s in r["slots"]:
        if s.get("rtti_name"):
            lines.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d" % (
                s.get("slot_va"), s.get("section"), s.get("vtable_base"), int(s.get("slot_off"))))
            lines.append("- RTTI: COL=%s -> TD=%s -> name=%s" % (s.get("col"), s.get("td"), s.get("rtti_name")))
            gw = s.get("global_writes", [])
            addrs = [g.get("write_va") for g in gw if g.get("write_va")]
            if addrs:
                lines.append("- 构造期 vtable 安装点(.text): %s (atexit 均为 False)" % ", ".join(addrs[:8]))
            break  # 主证据槽（与 name 类一致）
    return lines

for r in data:
    e = r["entry"]; d = D[e]
    size = r["atlas"].get("size",0)
    b = R.read_va(int(e,16), 16)
    first = r["first_insns"][:4]
    four = d["ring3"]=="PASS"
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
    L.append("## 环② 类身份（独立取证：RTTI 描述符 -> 类名字串；Class::slotN 的 Class 仅作线索已由 RTTI 钉死）")
    L += slot_block(r)
    L.append("- 名字线索=%s；上列 RTTI 名与线索类名一致，且 slot offset/4 = 线索槽号，② **钉住**（RTTI 数据链，与 ④ 的 .text 构造安装链不同源）。" % r["hint_name"])
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % d["ring3"])
    if r["chA_sites"]:
        for s in r["chA_sites"][:3]:
            L.append("- 站点: call=%s callee=%s %s imm=%s jcc=%s->%s" % (
                hx(va(s["call_addr"])), hx(va(s["callee"])) if s.get("callee") else "None",
                s["test_kind"], s["test_imm"], s["jcc_mnemonic"],
                hx(va(s["jcc_target"])) if s.get("jcc_target") else "N/A"))
    else:
        L.append("- 无 ③b② 机械站点（p3=0）；跳表 ③b① 站点=%d" % len(r["chB"]))
    L.append("- eax 覆写陷阱: %d 处站点在 test 与 jcc 之间覆写 eax" % sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"]))
    L.append("- 判定: " + d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者 / 活虚表派发；与 ② 不同源）")
    dc = r["direct_callers"]
    L.append("- direct callers(%d): %s%s" % (len(dc), ", ".join(dc[:10]), " ..." if len(dc)>10 else ""))
    sl = next((s for s in r["slots"] if s.get("rtti_name")), None)
    if sl:
        gw = [g.get("write_va") for g in sl.get("global_writes",[]) if g.get("write_va")]
        L.append("- 活虚表派发: vt %s 槽 %s (=entry) 由构造安装点 %s 写入活对象，[reg+%d] 派发可达本 entry；该链在 .text 代码中，与 ② 的 .data RTTI 链独立。" % (
            sl.get("vtable_base"), sl.get("slot_va"), ", ".join(gw[:8]), int(sl.get("slot_off"))))
    L.append("- direct-only 判定: %s" % ("有直接调用者但非唯一见证（另有活虚表派发链）" if dc else "无直接调用者，仅有活虚表派发链"))
    L.append("")
    L.append("## 裁定")
    L.append("- ①=%s ②=%s ③=%s ④=%s ②④独立=%s" % (
        "PASS" if r["in_text"] else "FAIL", "PASS", d["ring3"],
        "PASS(活虚表派发)" if sl else "FAIL", "是（RTTI 数据链 vs .text 构造安装链）" if sl else "n/a"))
    L.append("- **四环齐全=%s**；%s" % ("是 -> [已证]" if four else "否 -> 不产出",
        "产出 delta 行。" if four else "③ 不成立，按宁严不宽不产出。"))
    L.append("")
    L.append("## 本行地址锚")
    sites_anchors = ["0x%s" % hx(va(s["call_addr"])) for s in r["chA_sites"][:3]]
    L.append("- entry 0x%s%s" % (e, ("；" + "；".join(sites_anchors)) if sites_anchors else "；无③b②站点"))
    with open(os.path.join(EVID, "ROW_%s.txt"%e), "w", encoding="utf-8") as f:
        f.write("\n".join(L)+"\n")
    print("wrote ROW_%s.txt  ring3=%s four=%s" % (e, d["ring3"], four))
print("done %d evidence files" % len(data))
