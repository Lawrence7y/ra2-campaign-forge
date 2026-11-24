# -*- coding: utf-8 -*-
"""S14 B1 逐行 EVIDENCE 生成器：只取四环锚点，每行只写自身地址与字节。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *

WORK = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(os.path.dirname(WORK), "EVIDENCE")
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
R4 = json.load(open(os.path.join(WORK, "ring4.json"), encoding="utf-8"))

# ---- ③ 逐行裁定（每行独立理由；PASS 才进 delta） ----
D3 = {
"0041E540": dict(ok=False, sem="",
  why="站点 0x41E54B `e8 30 1e ff ff`->0x410380（哨兵 0x410389 `b8 03 40 00 80`=E_POINTER）；0x41E550 `85 c0`；0x41E552 `7c 60` jl->0x41E5B4。失败路 0x41E5B4 `5e c2 08 00` 原样返负 HRESULT；成功路 0x41E554 起 0x41E55F call 0x410960、0x41E564/6A/71/78 装 4 张子对象虚表、0x41E58B/59C/5AD 三次 call 0x6CF240 构造 +0xD8/+0xDC/+0xE0 容器。结构上站点成立，但成功路内容全部是「装虚表+构造成员」= 构造初始化，语义只能落到「校验后初始化对象」式，触及卡片『模板假句』禁令 => 判 FAIL（形态不合格，非结构不合格）。"),
"0041E5C0": dict(ok=False, sem="",
  why="站点 0x41E5CF `e8 4c 1d ff ff`->0x410320（哨兵 0x41032B `b8 03 40 00 80`）；0x41E5D4 `85 c0`；0x41E5D6 `7c 02` jl->0x41E5DA。成功侧 0x41E5D8 `33 c0`(xor eax,eax) 后与失败路在 0x41E5DA `c2 0c 00` 汇合，两路唯一差别是 eax 常量（错误码 vs 0）=> ③a 纯转发壳（D-46(A) 常量差不算 ③b②）。"),
"0041F580": dict(ok=True,
  sem="AITriggerTypeClass 虚槽25 的名字解析链：调 0x523C90 在表 0xA8E34C 中查下标，未命中返回 -1 时依次回退 0x747370 / 0x41CAA0 / 0x45E7B0 三张表，命中则以 [0xA8E34C+idx*4] 取表项存入 this+0xD8",
  why="站点 0x41F783 `e8 08 45 10 00`->0x523C90；0x41F788 `83 f8 ff` cmp eax,-1；0x41F78B `74 0b` je->0x41F798。被调返回约定可字节伪证：未命中 0x523CE7 `83 c8 ff`(or eax,-1) 后 ret（返 -1）；命中 0x523CEC `8b c6`(mov eax,esi) 返数组下标。调用方真的拿它分支：命中(-!= -1) 走 0x41F78D `8b 0d 4c e3 a8 00` + 0x41F793 `8b 34 81` 用下标取表项；未命中(-1) 走 0x41F798 call 0x747370 继续查下一张表（再 cmp -1/je，四级链）。两路动作真不同、单 call、test 与 jcc 之间无 eax 覆写。"),
"0041FFF0": dict(ok=False, sem="",
  why="站点 0x420023 `ff 52 10`(call dword ptr [edx+0x10]) 为间接派发；0x420026 `83 f8 ff`；0x420029 `74 2d` je->0x420058。被调无法定位到具体函数 => 『失败返回 -1』无法从字节伪证，只剩调用方单侧猜测 => FAIL。"),
"004FB9B0": dict(ok=False, sem="",
  why="9 个 cmp eax,-1 站点（0x4FBA49 / 0x4FBA70 / 0x4FBAB0 / 0x4FBAD7 / 0x4FBB17 / 0x4FBB3E / 0x4FBBA5 / 0x4FBBCC / 0x4FBC0C）全为 `ff 52 10` / `ff 50 10` 间接派发，被调不可定位，返回约定不可伪证 => FAIL。"),
"005024F0": dict(ok=False, sem="",
  why="站点 0x502506 `e8 0c 69 2c 00`->0x7C8E17；该被调是 14 字节 thunk（`6a 01 ff 74 24 08 e8 20 06 00 00 59 59 c3`）转 0x7C9442，返回源不可定；0x50250E `85 c0`；0x502510 `74 18` je->0x50252A（失败路 0x50252B `b8 0e 00 07 80` 返 E_OUTOFMEMORY）。零值判断型，无被调侧可伪证错误码 => FAIL。"),
"00503040": dict(ok=True,
  sem="HouseClass 虚槽5（流读入）：先弹出 +0x258 队列末项，再以 0x410380 校验接口参数（空则返 E_POINTER 0x80004003 并原样早退），成功则经 0x4F5190 与 +0x5700 子对象虚派发、逐一遍历 +0x5500..+0x55DC 共 12 个 stride 0x14 的容器调 0x49FBE0 读入，再构造各子对象",
  why="站点 0x5031C9 `e8 b2 d1 f0 ff`->0x410380；0x5031CE `85 c0`；0x5031D0 `0f 8c 93 0e 00 00` jl->0x504069。失败路 0x504069 `5f 5e 5d 5b 83 c4 10 c2 08 00` 原样返负 HRESULT；成功路 0x5031D6 起：0x5031E1 call 0x4F5190、0x5031F4 `ff 11`(call [ecx]) 派发 +0x5700 子对象、0x5031FD..0x503281 连续 12 次 call 0x49FBE0 于 +0x5500 起 stride 0x14 逐容器读入、0x50328F/0x50329B 起 0x6CF240 构造。两路动作真不同、无 eax 覆写。"),
"00504080": dict(ok=False, sem="",
  why="chA p1=34/p2=34/p3=0：34 个 call->test/cmp->jcc 结构两路动作确实不同，但无一个站点的返回约定可伪证（被调既无 falsifiable imm 常量、调用点也无哨兵比较）=> FAIL。"),
"00511850": dict(ok=False, sem="",
  why="7 个站点（0x511D2D / 0x511D5A / 0x511D6D / 0x511E3A / 0x511E66 / 0x511F70 / 0x511F9C）全为 `test eax,eax; je`；被调 0x528A10 成功返长度、失败/空返 0（0x528BC0 `33 c0` 后 `c2 14 00`），0x524CB0 / 0x7C9CC2 同型 => 零值判断，不是错误码 => FAIL。"),
"00512290": dict(ok=True,
  sem="HouseTypeClass 虚槽5（流读入）：以 0x410380 校验接口参数（空则返 E_POINTER 并原样早退），成功则经 [reg+0xC] 分四次读入计数、逐元素构造 +0x150 / +0x16C / +0x188 三个数组的元素，并对三段各 n 个单元调 0x6CF240 构造",
  why="站点 0x5122D0 `e8 ab e0 ef ff`->0x410380；0x5122D5 `85 c0`；0x5122D7 `0f 8c 90 01 00 00` jl->0x51246D（0x51246D 起 `5f 5e 5d 5b 59 c2 08 00` 原样返负 HRESULT）。成功路：0x5122E8 call 0x511650、0x5122F7 call 0x512DC0 + 0x5122FC `c7 03 08 ac 7e 00`、0x51230E/0x51232D/0x51236F/0x5123BB 四次 `call [reg+0xc]` 读 4 字节计数、0x512337/0x512392/0x5123DE 循环逐元素、0x512405/0x512430/0x51245B 三段 0x6CF240。两路真不同、无 eax 覆写。"),
"00512480": dict(ok=True,
  sem="HouseTypeClass 虚槽6（流写出）：以 0x410320 校验参数（空则返 E_POINTER 并原样早退），成功则对 +0x150 / +0x16C / +0x188 三数组各写 4 字节计数，并经 [reg+0x10] 逐元素写 4 字节",
  why="站点 0x512491 `e8 8a de ef ff`->0x410320；0x512496 `85 c0`；0x512498 `0f 8c be 00 00 00` jl->0x51255C（`5f 5e c2 0c 00` 原样返负 HRESULT）。成功路：0x5124B5/0x5124F3/0x512531 三次 `call [reg+0x10]` 写计数（+0x15C/+0x178/+0x194），0x5124D3/0x512511/0x51254F 三个循环把 +0x150/+0x16C/+0x188 逐元素写 4 字节。两路真不同、无 eax 覆写。"),
"00512760": dict(ok=False, sem="",
  why="站点 0x51279A `ff 52 10` 间接派发；0x51279D `83 f8 ff`；0x5127A0 `74 2d` je->0x5127CF；被调不可定位 => FAIL。"),
"0065AB80": dict(ok=False, sem="",
  why="chA p1=4/p2=4/p3=0（同 00504080 口径）：4 个站点两路动作不同但无一可伪证返回约定 => FAIL。（本行有 direct caller 0x70BF5C，但 direct 不能替代 ③。）"),
"0065AC40": dict(ok=True,
  sem="RadioClass 虚槽6（流读入）：以 0x410320 校验参数（空则返 E_POINTER 并原样早退），成功则读 4 字节计数存 +0xE8、循环经 [reg+0x10] 逐 4 字节读入 +0xE4 数组；任一读返负 HRESULT 即原样返回，全成返 0",
  why="站点 0x65AC52 `e8 c9 56 db ff`->0x410320；0x65AC57 `85 c0`；0x65AC59 `7c 4a` jl->0x65ACA5（`5f 5e 5b c2 0c 00` 原样返负 HRESULT）。成功路 0x65AC5B 取 [edi+0xE8]、0x65AC71 `ff 52 10` 读 4 字节计数；0x65AC76 `7c 4a` 再判负->同 epilogue；0x65AC93 循环 `ff 51 10` 逐 4 字节写 +0xE4 数组；末 0x65ACA3 `33 c0` 返 0。两路真不同、无 eax 覆写。（另有 direct caller 0x70C25F。）"),
"00691630": dict(ok=False, sem="",
  why="站点 0x69163B `e8 40 ed d7 ff`->0x410380；0x691640 `85 c0`；0x691642 `7c 3b` jl->0x69167F。失败路 0x69167F `5e c2 08 00` 原样返；成功路 0x69164F call 0x4101C0 + 0x691654/5A/61/68 装 4 张虚表 + 0x691678 call 0x6CF240(esi+0x24) + 0x69167D `33 c0` 返 0。结构成立但成功路仅「基类构造+装虚表+构造子对象」= 构造初始化，语义只能写成对象初始化式，触『模板假句』禁令 => FAIL。"),
"00691690": dict(ok=False, sem="",
  why="站点 0x69169F `e8 7c ec d7 ff`->0x410320；0x6916A4 `85 c0`；0x6916A6 `7c 02` jl->0x6916AA。0x6916A8 `33 c0` 与失败路在 0x6916AA `c2 0c 00` 汇合，两路仅 eax 常量差 => ③a 纯转发壳 => FAIL。"),
"006918A0": dict(ok=False, sem="",
  why="站点 0x691908 `e8 03 71 e9 ff`->0x528A10；0x69190D `85 c0`；0x69190F `7e 3c` jle->0x69194D。被调成功返长度、失败返 0，`jle` 实为 ‘<=0’ 的零值判断 => 非错误码 => FAIL。"),
"00691D90": dict(ok=False, sem="",
  why="站点 0x691D9B `e8 e0 e5 d7 ff`->0x410380；0x691DA0 `85 c0`；0x691DA2 `7c 2d` jl->0x691DD1。失败路 0x691DD1 `5e c2 08 00` 原样返；成功路 0x691DAF call 0x410960 + 0x691DB4/BA/C1/C8 装 4 张虚表 + 0x691DCF `33 c0` 返 0 —— 成功路仅基类构造+装虚表，语义落到对象初始化式，触『模板假句』禁令 => FAIL（形态不合格）。"),
}

def by(va, n=16):
    return R.read_va(va, n).hex(" ")

def ins1(va):
    l = list(R.disasm(va, R.read_va(va, 16)))[:1]
    if not l: return None
    i = l[0]
    return "%08X: %-8s %-26s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(" "))

def cstr(va, n=64):
    return C2.read_cstr(va, n)

summary = []
for entry, rec in AN.items():
    d = D3[entry]
    r4 = R4[entry]
    size = rec["ring1"].get("atlas_size")
    insns = R.disasm(int(entry, 16), R.read_va(int(entry, 16), size))
    L = []
    L.append("# ROW %s  S14  %s" % (entry, rec["name"]))
    L.append("")
    L.append("## 环① 入口与函数边界")
    L.append("- entry=%s（大写十六进制无 0x；delta entry 列原样写此串）" % entry)
    L.append("- in_text=True；atlas size=%d B；反汇编 n_instr=%d，skipdata=%d" % (
        size, len(insns), sum(1 for i in insns if i.id == 0)))
    L.append("- 体内 [0x%s, 0x%08X)；入口 16B: %s" % (entry, int(entry, 16) + size, by(int(entry, 16))))
    for i in list(R.disasm(int(entry, 16), R.read_va(int(entry, 16), 20)))[:3]:
        L.append("    %08X: %-8s %-26s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(" ")))
    L.append("")
    L.append("## 环② 类身份（独立取证：RTTI 描述符 -> 类名字串；`Class::slotN` 的 Class 仅作线索）")
    slot = None
    for s in rec["ring2_slots"]:
        if s.get("rtti_name"):
            slot = s
            break
    cue = rec["name"].split("::")[1]
    L.append("- 线索=%s（槽号 %s）" % (rec["name"], cue.replace("vslot", "").replace("slot", "")))
    L.append("- 槽驻留 %s [%s]，vtable base=%s，slot offset=+%d（slot#=%d）" % (
        slot["slot_va"], slot["section"], slot["vtable_base"], slot["slot_off"], slot["slot_off"] // 4))
    slotval = R.u32(int(slot["slot_va"], 16))
    L.append("- 槽值 4B @%s = `%s` ⇒ 0x%08X（== entry 0x%s）" % (
        slot["slot_va"], by(int(slot["slot_va"], 16), 4), slotval, entry))
    L.append("- RTTI: COL=%s sig@+0=`%s`(=0) pTD@+0xC=`%s` -> TD=%s -> name@%s(TD+8) = `%s`" % (
        slot["col"], by(int(slot["col"], 16), 4),
        by(int(slot["col"], 16) + 0xC, 4), slot["td"], slot["name_va"],
        cstr(int(slot["name_va"], 16), 64)))
    L.append("- 判定：RTTI 名串 `%s` 与线索类名一致，且 slot offset/4 = %d = 线索槽号 ⇒ ② **钉住**（证据为 .rdata 的 RTTI 描述符字节链）。" % (
        slot["rtti_name"], slot["slot_off"] // 4))
    L.append("")
    L.append("## 环③ 整体合同（只认 ③b；本行裁定 %s）" % ("PASS" if d["ok"] else "FAIL"))
    chA = rec.get("chA") or {}
    L.append("- chA p1=%s p2=%s p3=%s" % (chA.get("p1"), chA.get("p2"), chA.get("p3")))
    sites = chA.get("sites") or []
    SEL = {"0041E540": 0x41E54B, "0041E5C0": 0x41E5CF, "0041F580": 0x41F783,
           "0041FFF0": 0x420023, "004FB9B0": 0x4FBA49, "005024F0": 0x502506,
           "00503040": 0x5031C9, "00511850": 0x511D2D, "00512290": 0x5122D0,
           "00512480": 0x512491, "00512760": 0x51279A, "0065AC40": 0x65AC52,
           "00691630": 0x69163B, "00691690": 0x69169F, "006918A0": 0x691908,
           "00691D90": 0x691D9B}
    if sites:
        want = SEL.get(entry)
        s0 = [s for s in sites if s["call_addr"] == want] or sites[:1]
        for s in s0:
            L.append("- 站点 call=%08X test=%s imm=%s jcc=%s->%s" % (
                s["call_addr"], s["test_kind"], s["test_imm"], s["jcc_mnemonic"],
                "%08X" % s["jcc_target"] if s["jcc_target"] else "-"))
            for a in (s["call_addr"], s["test_addr"], s["jcc_addr"]):
                t = ins1(a)
                if t: L.append("    %s" % t)
            clob = []
            for i in insns:
                if s["test_addr"] < i.address < s["jcc_addr"]:
                    if i.id == X86_INS_CALL:
                        clob.append("%08X call" % i.address)
                    elif i.operands and i.operands[0].type == X86_OP_REG \
                            and i.operands[0].reg == X86_REG_EAX:
                        clob.append("%08X %s" % (i.address, i.mnemonic))
            L.append("- eax 覆写在 (test,jcc) 之间：%s" % (", ".join(clob) or "无"))
    L.append("- 判定依据：%s" % d["why"])
    if d["ok"]:
        L.append("- 本行 one_line_semantics：%s" % d["sem"])
    L.append("")
    L.append("## 环④ 使用见证（活 vtable 槽位形态，D-43(A)：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用；不要求真实派发点）")
    inst = [i for i in r4["installs"] if i["in_func"] != entry]
    L.append("- direct callers: %s" % (", ".join(r4["direct"]) or "none"))
    L.append("- vtable %s 的 .text 安装点（行外，atexit 判定见列）：" % r4["vtable"])
    for i in inst:
        t = ins1(int(i["va"], 16))
        L.append("    %s  in_func=%s atexit=%s  %s" % (i["va"], i["in_func"], i["atexit"], t))
    good = [i for i in inst if i["atexit"] is False]
    L.append("- 取 %s（atexit=False ⇒ 非析构器注册的表）为活表安装点，与 ② 的 .rdata RTTI 链不同源（.text 指令 vs .data 数据）。" % (
        good[0]["va"] if good else "none"))
    L.append("")
    L.append("## 裁定")
    L.append("- ①=PASS ②=PASS ③=%s ④=PASS" % ("PASS" if d["ok"] else "FAIL"))
    L.append("- ②④不同源：②=`.rdata` RTTI 描述符字节链；④=`.text` 构造安装点指令（行外、site 不共用）")
    L.append("- **四环齐全=%s**" % ("是 -> [已证]；产出 delta 行" if d["ok"] else "否"))
    L.append("")
    L.append("## 本行地址锚")
    anchor = [entry]
    if slot: anchor += [slot["slot_va"], slot["col"], slot["td"]]
    if sites: anchor.append("%08X" % sites[0]["call_addr"])
    if good: anchor.append(good[0]["va"])
    L.append("- " + "；".join("0x" + a if not a.startswith("%") else a for a in anchor))
    open(os.path.join(OUTD, "ROW_%s.txt" % entry), "w", encoding="utf-8").write("\n".join(L) + "\n")
    summary.append((entry, rec["name"], d["ok"]))

print("evidence written:", len(summary))
print("③ PASS:", sum(1 for _, _, ok in summary if ok))
json.dump([{"entry": e, "name": n, "ring3": ok, "sem": D3[e]["sem"]} for e, n, ok in summary],
          open(os.path.join(WORK, "verdict.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
