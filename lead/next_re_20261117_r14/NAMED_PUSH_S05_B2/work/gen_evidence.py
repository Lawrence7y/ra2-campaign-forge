# -*- coding: utf-8 -*-
"""NAMED-PUSH S05 B2 逐行证据生成：每行四环自有地址与字节，③ 理由逐行独立。
只读 gamemd.exe；写域仅本批 EVIDENCE / delta / base_rate / PROGRESS。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)
rows = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))
ana = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
rtti = json.load(open(os.path.join(WORK, "rtti_map.json"), encoding="utf-8"))

def va(x): return int(x, 16) if isinstance(x, str) else int(x)
def hx(x): return R.hx(va(x))

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
def dispatch_count(off):
    n = 0
    for ins in MD.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == off and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
                n += 1
    return n

# 每行独立 ②/③/④ 裁定与理由（地址自证）
D = {
"00459900": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="4 个 channel A 站点 0x004561D3/0x00456363/0x00456533/0x00456637 均为 call 0x007C8E17(malloc) 后 TEST_EAX@+1 -> je；被调常量集为空（分配器 NULL 探测），属『malloc 空判断 + 对象初始化』模板假句（D-40 禁 ③a），非域内可伪证错误码，两路签名差异仅来自后续构造，不构成 ③b②；无跳表/内存形状断言/完整循环非栈写。③不成立。",
  why4="vt 007E3EBC 槽 007E4324(=entry,slot#282) 由该虚表构造安装点写入活对象，[reg+0x468] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00459C20": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="127B 函数，channel A p1=p2=p3=0、无跳表：无任何 call->test/cmp->jcc 可伪证返回约定站点；无 ③b①/③b③/③b④ 形态。③不成立。",
  why4="vt 007E3EBC 槽 007E4228(=entry,slot#219) 由构造安装点写入活对象，[reg+0x36C] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00523B10": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="43B 小函数，唯一站点 call 0x007C8E17(malloc)@0x00523B18 -> TEST_EAX@0x00523B1A -> je@0x00523B1C->0x00523B35(taken: xor eax,eax;ret)；被调为分配器 NULL 探测无 falsifiable 常量，fallthrough 0x00523B24 call 0x00517A50 构造。典型 malloc 空判断+对象初始化模板假句（D-40 禁 ③a）。③不成立。",
  why4="vt 007EB610 槽 007EB69C(=entry,slot#35) 由构造安装点写入活对象，[reg+0x8c] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00523B40": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="唯一站点 call 0x007C8E17(malloc)@0x00523B4B -> TEST_EAX->je@0x00523C17(taken: xor al,al;ret)；NULL 探测模板假句；fallthrough 0x00523B5B 继续 call 0x00517A50 构造后再 test esi,esi/je，全为分配/状态布尔探测，无用域内可伪证错误码分支。③不成立。",
  why4="vt 007EB610 槽 007EB690(=entry,slot#32) 由构造安装点写入活对象，[reg+0x80] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"005240A0": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="1725B 大函数，9 个 channel A 站点：被调 0x00528A10/0x00428B80/0x007C9CC2 返回常量集均只有 {0}（或空），TEST_EAX->je 全为 NULL/布尔探测（如 0x00524125->0x00524139、0x00524227->0x00524268），无 falsifiable 域内错误码；多路均为字符串/字段初始化与资源获取（mov [esi+0xe04],eax 等非栈写属对象初始化模板假句），非 ③b④ 完整循环；无跳表。③不成立。",
  why4="vt 007EB610 槽 007EB674(=entry,slot#25) 由构造安装点写入活对象，[reg+0x64] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00524D70": dict(ring2="PASS", ring3="PASS", ring4="PASS",
  why3="站点 call dword ptr [edx+0x10]@0x00524DAA (FF 52 10；edx=[0xA8E348] 运行时全局列表对象) -> 零间隔 cmp eax,-1@0x00524DAD (83 F8 FF) -> je@0x00524DB0 (74 2D) -> 0x00524DDF。-1 为 falsifiable 哨兵（未找到索引）。je 成立路 0x00524DDF 起为字段释放路径（call 0x7C8B3D 释放 [esi+0xe3c]、逐字段清零，jmp 收尾）；不成立路 0x00524DB2 起 mov ecx,[0xA8E358]/cmp eax,ecx/jge 边界检查、0x00524DBF mov [0xA8E358],ecx（非栈写）、0x00524DC7 起 inc eax / mov edx,[ecx+eax*4] / mov [ecx+eax*4-4],edx (89 54 81 FC) 数组前移循环（循环体非栈写 + 边界检查，jl 回边 0x00524DDD）。两路动作真不同（-1 跳过摘链 vs 找到则摘链），cmp 与 je 间无 eax 覆写，非 bool、非纯转发、非 malloc 模板、非多路同一 call。与 B1 已收 00410C30/0041CFE0 同构。③b② 成立。",
  why4="vt 007EB610 槽 007EB630(=entry,slot#8) 由构造安装点 005237E8/005239A8（所在函数非 atexit 注册）写入活对象，[reg+0x20] 派发链位于 .text（dispatch 358 处），与 ② 的 .rdata RTTI 数据链不同源。"),
"005F7900": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="唯一站点 call 0x004F7870@0x005F79A3 -> TEST_EAX@0x005F79A8 -> jle@0x005F79AB；被调 0x004F7870 返回常量集 {0,1}（bool 布尔态，D-46(A) 不算 ③b②），jle 只是对布尔/小值的符号分支；taken@0x005F7A57 为循环计数收尾、fallthrough 继续对象链遍历，属状态机循环而非可伪证错误码约定。③不成立。",
  why4="vt 007E2868 槽 007E28FC(=entry,slot#37) 由构造安装点写入活对象，[reg+0x94] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"005F9950": dict(ring2="PASS", ring3="PASS", ring4="PASS",
  why3="站点 call 0x00410320@0x005F995F (E8 BC 69 E1 FF) -> 零间隔 test eax,eax@0x005F9964 (85 C0) -> jl@0x005F9966 (7C 02) -> 0x005F996A(ret 0xc)。被调 0x00410320 是有符号比较 helper：0x00410325 test esi,esi / 0x0041032A mov eax,0x80004003(E_POINTER)/ret（NULL 入参返回可伪证 HRESULT 错误码），非 NULL 路 call [eax+0x10] 后 test/jl 传播负值，返回常量集含 0x80004003（falsifiable）。jl 成立路保留负值错误码原样 ret 0xc；不成立路 0x005F9968 xor eax,eax 归一为 0 后 ret。两路返回确定且可逐条证伪（负→原值/非负→0），test 与 jl 间无 eax 覆写，非 bool、非纯转发、非 malloc 模板。与 KPROVED4 已收同型。③b② 成立。",
  why4="vt 007EF2D8 槽 007EF2F0(=entry,slot#6) 由构造安装点 005F73D9/005F740B（所在函数非 atexit 注册）写入活对象，[reg+0x18] 派发链位于 .text（dispatch 367 处），与 ② 的 .rdata RTTI 数据链不同源。"),
"006F3F40": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="953B 大函数，4 个 channel A 站点：0x006F3F69 间接 call 后 TEST_EAX->je@0x006F42F7(仅 pop;ret)，被调返回源 unknown、无 falsifiable 码；0x006F4136/0x006F4185/0x006F41D6 均 call 0x007C8E17(malloc) 后 TEST_EAX->je，属分配 NULL 模板假句。其余为状态字段遍历与 [reg+off] 虚调用取属性，无 ③b① 跳表、无完整循环非栈写（写入均为对象初始化）。③不成立。",
  why4="vt 007E8C94 槽 007E8CB8(=entry,slot#9) 由构造安装点写入活对象，[reg+0x24] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00703860": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="686B 函数，channel A p1=2/p2=2 但 p3=0：两站点 0x007038D5 CMP_IMM imm=6(je)、0x00703A8F CMP_IMM imm=100(jge)，imm=6/100 均非 falsifiable（非 0/1/-1 且不在 HRESULT 0x80000xxx/0xC0000xxx 区间），被调 0x007C5F00 返回常量集为空。函数体确有多处 mov eax,<码> 计算距离档位，但那是函数自身返回值而非被调可伪证返回约定、也没有调用方 test/cmp+跳转消费统一错误码；不构成严格 D-40 ③b②。无跳表/完整循环非栈写。③不成立。",
  why4="vt 007F4960 槽 007F49C8(=entry,slot#26) 由构造安装点写入活对象，[reg+0x68] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00704350": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="3 个 channel A 站点：0x0070439E 间接 call 后 CMP_IMM imm=1->jne（imm=1 布尔态，D-46(A)）；0x007043F5 间接 call 后 TEST_EAX->je（被调源 unknown）；0x007043FD call 0x0047C520 返回常量集 {0} 后 TEST_EAX->je（NULL/布尔探测）。三路均落入 0x00704421 同一汇合点做状态判定，无 falsifiable 域内错误码、无每路可单独验证的跳表。③不成立。",
  why4="vt 007F4960 槽 007F4C4C(=entry,slot#187) 由构造安装点写入活对象，[reg+0x2ec] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00712040": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="135B 函数，channel A p1=p2=p3=0、无跳表：无任何 call->test/cmp->jcc 可伪证返回约定站点，无 ③b①/③b③/③b④ 形态。③不成立。",
  why4="vt 007E2868 槽 007E2900(=entry,slot#38) 由构造安装点写入活对象，[reg+0x98] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"007120D0": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="74B 小函数，唯一站点 call 0x007C5F00@0x00712107 -> CMP_IMM imm=1@0x0071210B -> jg@0x0071210D；imm=1 为布尔态（D-46(A)），被调 0x007C5F00 返回常量集空、无 falsifiable 错误码。taken 0x00712118 仅 pop;ret、fallthrough 0x00712113 mov eax,1 后同 ret，两路只是返回 0/1 布尔，属 getter 布尔态非整体合同。③不成立。",
  why4="vt 007E2868 槽 007E2918(=entry,slot#44) 由构造安装点写入活对象，[reg+0xb0] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"007170A0": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="255B 函数，channel A p1=p2=p3=0、无跳表：无任何 call->test/cmp->jcc 可伪证返回约定站点，无 ③b①/③b③/③b④ 形态。③不成立。",
  why4="vt 007E2868 槽 007E2884(=entry,slot#7) 由构造安装点写入活对象，[reg+0x1c] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"007474B0": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="唯一站点 call 0x007C8E17(malloc)@0x007474BB -> TEST_EAX->je@0x00747554(taken: xor al,al;ret)；NULL 探测模板假句。fallthrough 0x007474CB call 0x007353C0 后再 test esi,esi/je，全为分配/状态布尔探测，无 falsifiable 域内错误码。③不成立。",
  why4="vt 007F6218 槽 007F6298(=entry,slot#32) 由构造安装点写入活对象，[reg+0x80] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00747560": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="43B 小函数，唯一站点 call 0x007C8E17(malloc)@0x00747568 -> TEST_EAX->je@0x00747585(taken: xor eax,eax;ret)；NULL 探测模板假句。fallthrough 0x00747574 call 0x007353C0 构造后 ret，无 falsifiable 错误码。③不成立。",
  why4="vt 007F6218 槽 007F62A4(=entry,slot#35) 由构造安装点写入活对象，[reg+0x8c] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"00748010": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="2 站点 0x0074805A call 0x005F8110（返回常量集仅 {0}）/0x00748061 call 0x005F9070（常量集空），均 TEST_EAX->je@0x0074809E(taken: xor eax,eax;ret)，为 NULL/布尔探测，无 falsifiable 域内错误码；fallthrough 0x00748070 为字段读取+0x7C9FF0 调用的对象初始化模板。③不成立。",
  why4="vt 007F6218 槽 007F622C(=entry,slot#5) 由构造安装点写入活对象，[reg+0x14] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
"007480B0": dict(ring2="PASS", ring3="FAIL", ring4="PASS",
  why3="29B 极小函数，channel A p1=p2=p3=0、无跳表：无任何 call->test/cmp->jcc 可伪证返回约定站点，无 ③b①/③b③/③b④ 形态。③不成立。",
  why4="vt 007F6218 槽 007F6230(=entry,slot#6) 由构造安装点写入活对象，[reg+0x18] 派发链位于 .text，与 ② 的 .rdata RTTI 数据链不同源。"),
}

def rtti_block(e):
    rm = rtti.get(e)
    if not rm: return ["- ② 无虚表槽/RTTI"]
    slotva = hx(rm["slot_va"]); vt = hx(rm["vtable_base"]); off = rm["slot_off"]
    slotno = rm["slotno"]; col = hx(rm["col"]); td = hx(rm["td"]); name = rm["rtti_name"]
    return [
      "- 槽驻留 %s [.rdata]，vtable base=%s，slot offset=+%d (=slot#%d)" % (slotva, hx(vt), off, slotno),
      "- RTTI 扩展回扫(kmax=600): COL=%s(sig=0) -> TD=%s -> name=%s" % (col, td, name),
      "- [vt-4]=COL、VT[slot#%d]=%s(=entry)，slot offset/4=%d=名字线索槽号；类名与 %s 逐字一致；② 独立钉死（非仅凭 slotN 类名）" % (slotno, slotva, slotno, name),
    ]

cnt = 0
for row in rows:
    e = row["entry"]; nm = row["name"]
    d = D[e]; r = ana[e]
    size = r["atlas"].get("size", 0)
    b = R.read_va(int(e, 16), 16)
    first = r["first_insns"][:4]
    four = (d["ring2"] == "PASS" and d["ring3"] == "PASS" and d["ring4"] == "PASS")
    rm = rtti.get(e)
    off = rm["slot_off"] if rm else 0
    dcnt = dispatch_count(off)
    L = []
    L.append("# ROW %s  S05  %s" % (e, nm))
    L.append("")
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s（大写十六进制、无 0x；delta entry 列原样写此串）" % e)
    L.append("- atlas size=%d B，反汇编 n_instr=%d，skipdata=%d，in_text=%s" % (size, r["n_insn_disasm"], r["n_skipdata"], r["in_text"]))
    L.append("- 函数体 [0x%s,0x%s)；入口 16B: %s" % (e, hx(int(e,16)+size), " ".join("%02X" % x for x in b)))
    for x in first: L.append("    %s" % x)
    L.append("")
    L.append("## 环② 类身份（独立取证；Class::slotN 的 Class 仅作线索，已由 RTTI/虚表钉死）")
    L += rtti_block(e)
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % d["ring3"])
    if r["chA_sites"]:
        for s in r["chA_sites"][:4]:
            L.append("- 站点: call=%s callee=%s %s imm=%s jcc=%s" % (hx(s["call_addr"]), hx(s["callee"]) if s.get("callee") else "None(间接)", s["test_kind"], s["test_imm"], s["jcc_mnemonic"]))
    else:
        L.append("- 无 ③b② 机械站点（channel A p3=0）；channel B 跳表站点=%d" % len(r["chB"]))
    L.append("- eax 覆写陷阱: %d 处站点在 test/cmp 与 jcc 之间覆写 eax" % sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"]))
    L.append("- 判定: " + d["why3"])
    L.append("")
    L.append("## 环④ 使用见证（真实调用者 / 活虚表派发；与 ② 不同源）")
    L.append("- " + d["why4"].replace("[reg+", "[reg+"))
    L.append("- 本行 [reg+0x%X] 派发站点计数=%d；2 和 4 分属 .rdata RTTI 数据链 与 .text 构造安装/派发链 -> 不同源" % (off, dcnt))
    dc = r["direct_callers"]
    L.append("- direct callers(%d): %s" % (len(dc), ", ".join(dc[:8]) if dc else "无"))
    L.append("")
    L.append("## 裁定")
    L.append("- ①=%s ②=%s ③=%s ④=%s ②④独立=%s" % (
        "PASS" if r["in_text"] else "FAIL", d["ring2"], d["ring3"], d["ring4"],
        "是（.rdata RTTI 数据链 vs .text 构造安装/派发链）" if d["ring2"] == "PASS" else "n/a"))
    L.append("- **四环齐全=%s**；%s" % ("是 -> [已证]" if four else "否 -> 不产出", "产出 delta 行。" if four else "按宁严不宽不产出。"))
    L.append("")
    with open(os.path.join(EVID, "ROW_%s.txt" % e), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    cnt += 1
    print("wrote ROW_%s.txt ring2=%s ring3=%s ring4=%s four=%s" % (e, d["ring2"], d["ring3"], d["ring4"], four), flush=True)

print("done %d evidence files" % cnt)
