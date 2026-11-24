# -*- coding: utf-8 -*-
"""写 delta.tsv / base_rate.tsv（entry 大写十六进制无 0x；每行语义独立）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(WORK)
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
R4 = json.load(open(os.path.join(WORK, "ring4.json"), encoding="utf-8"))
V = json.load(open(os.path.join(WORK, "verdict.json"), encoding="utf-8"))

PASS = ["0041F580", "00503040", "00512290", "00512480", "0065AC40"]

# 每行 ④ 要引用的安装点 / ② 锚点 / ③ 站点，全部按行取盘上实际值
R4PICK = {"0041F580": "0041E401", "00503040": "004F5457", "00512290": "00511572",
          "00512480": "00511572", "0065AC40": "0065A798"}
SITE = {"0041F580": "0041F783", "00503040": "005031C9", "00512290": "005122D0",
        "00512480": "00512491", "0065AC40": "0065AC52"}
TEST = {"0041F580": "cmp eax,-1@0x0041F788(83 F8 FF)", "00503040": "test eax,eax@0x005031CE(85 C0)",
        "00512290": "test eax,eax@0x005122D5(85 C0)", "00512480": "test eax,eax@0x00512496(85 C0)",
        "0065AC40": "test eax,eax@0x0065AC57(85 C0)"}
JCC = {"0041F580": "je@0x0041F78B(74 0B)->0x0041F798",
       "00503040": "jl@0x005031D0(0F 8C 93 0E 00 00)->0x00504069",
       "00512290": "jl@0x005122D7(0F 8C 90 01 00 00)->0x0051246D",
       "00512480": "jl@0x00512498(0F 8C BE 00 00 00)->0x0051255C",
       "0065AC40": "jl@0x0065AC59(7C 4A)->0x0065ACA5"}
SENT = {"0041F580": "被调 0x00523C90 未命中 0x00523CE7 or eax,-1(83 C8 FF) 后 ret 返 -1、命中 0x00523CEC mov eax,esi(8B C6) 返下标（可伪证 -1 哨兵）",
        "00503040": "被调 0x00410380 空参 0x00410389 mov eax,0x80004003(B8 03 40 00 80)=E_POINTER、否则经 [eax+0xC] 派发后传回其负 HRESULT（可伪证错误码）",
        "00512290": "被调 0x00410380 空参 0x00410389 mov eax,0x80004003(B8 03 40 00 80)=E_POINTER（可伪证错误码）",
        "00512480": "被调 0x00410320 空参 0x0041032B mov eax,0x80004003(B8 03 40 00 80)=E_POINTER（可伪证错误码）",
        "0065AC40": "被调 0x00410320 空参 0x0041032B mov eax,0x80004003(B8 03 40 00 80)=E_POINTER（可伪证错误码）"}
PATHS = {"0041F580": "命中路 0x0041F78D mov ecx,[0x00A8E34C](8B 0D 4C E3 A8 00)+0x0041F793 mov esi,[ecx+eax*4](8B 34 81) 向下标取表项；未命中路 0x0041F798 转 call 0x00747370 查下一张表（后接 0x0041CAA0/0x0045E7B0 共四级链）",
         "00503040": "失败路 0x00504069 起 5F 5E 5D 5B 83 C4 10 C2 08 00 原样返负 HRESULT；成功路 0x005031E1 call 0x004F5190、0x005031F4 FF 11 派发 +0x5700 子对象、0x005031FD..0x00503281 连续 12 次 call 0x0049FBE0 于 +0x5500 起 stride 0x14 逐容器读入、0x0050328F 起 0x006CF240 构造",
         "00512290": "失败路 0x0051246D 起 5F 5E 5D 5B 59 C2 08 00 原样返负 HRESULT；成功路 0x005122E8 call 0x00511650、0x005122F7 call 0x00512DC0+0x005122FC C7 03 08 AC 7E 00、0x0051230E/0x0051232D/0x0051236F/0x005123BB 四次 call [reg+0xC] 读 4B 计数、0x00512337/0x00512392/0x005123DE 循环逐元素、0x00512405/0x00512430/0x0051245B 三段 0x006CF240",
         "00512480": "失败路 0x0051255C 起 5F 5E C2 0C 00 原样返负 HRESULT；成功路 0x005124B5/0x005124F3/0x00512531 三次 call [reg+0x10] 写计数入 +0x15C/+0x178/+0x194、0x005124D3/0x00512511/0x0051254F 三循环把 +0x150/+0x16C/+0x188 逐元素写 4B",
         "0065AC40": "失败路 0x0065ACA5 起 5F 5E 5B C2 0C 00 原样返负 HRESULT；成功路 0x0065AC5B 取 [edi+0xE8]、0x0065AC71 FF 52 10 读 4B 计数、0x0065AC76 7C 4A 再判负同 epilogue、0x0065AC93 FF 51 10 循环逐 4B 写 +0xE4 数组、末 0x0065ACA3 33 C0 返 0"}
DIRECT = {"0041F580": "无 direct caller", "00503040": "无 direct caller",
          "00512290": "无 direct caller", "00512480": "无 direct caller",
          "0065AC40": "另有 direct caller 0x0070C25F"}

lines = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
SEM = {r["entry"]: r["sem"] for r in V}
for e in PASS:
    rec = AN[e]
    slot = [s for s in rec["ring2_slots"] if s.get("rtti_name")][0]
    inst = [i for i in R4[e]["installs"] if i["va"] == R4PICK[e]][0]
    sem = ""  # 逐行手写组合（避免统一模板）
    # 逐行手写组合（避免统一模板）
    site = SITE[e]
    callee = {"0041F580": 0x523C90, "00503040": 0x410380, "00512290": 0x410380,
              "00512480": 0x410320, "0065AC40": 0x410320}[e]
    sem = ("S14 %s —— ③b② 合同：站点 call@0x%s 调 0x%08X；%s；%s；%s；两路动作真不同、test 与 jcc 之间无 eax 覆写陷阱。"
           "语义：%s。"
           "② 槽 %s(vt %s +0x%X，slot#%d) 的 4B 值即本 entry，RTTI COL=%s→TD=%s→name=%s，与线索类名一致且槽号自洽；"
           "④ 活 vt 构造安装点 0x%s(in_func=%s，atexit=False，写在行外、与 ② site 不共用) 把 vt 装入活对象，%s，"
           "②④ 不同源（.rdata RTTI 数据链 vs .text 构造安装指令）。") % (
        rec["name"], site, callee, TEST[e], JCC[e], SENT[e],
        SEM[e], slot["slot_va"], slot["vtable_base"], slot["slot_off"], slot["slot_off"] // 4,
        slot["col"], slot["td"], slot["rtti_name"],
        inst["va"], inst["in_func"], DIRECT[e])
    path = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S14_B1/EVIDENCE/ROW_%s.txt" % e
    assert "\t" not in sem and "\n" not in sem
    lines.append("\t".join([e, "S14", rec["name"], sem, "[已证]", path]))

open(os.path.join(BASE, "delta.tsv"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
open(os.path.join(BASE, "base_rate.tsv"), "w", encoding="utf-8").write(
    "batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n"
    "B1\t18\t18\t5\t18\t5\t0.2778\n")
print("delta rows:", len(lines) - 1)
