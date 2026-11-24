#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B3 step E: emit the final verdict.tsv from _verdict.json."""
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
V = json.load(open(os.path.join(HERE, "_verdict.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in V["rows"]}

FIELDS_BY = {}
with open(os.path.join(R14, "R16_D1_WIDE_B3", "fields.tsv"), encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        if line.strip():
            p = dict(zip(hdr, line.rstrip("\n").split("\t")))
            FIELDS_BY[p["entry"]] = p

NOTE = {
    "005B3A60": "entry 本身是 scalar deleting dtor；宿主 005B2DA0 为真 ctor（mov esi,ecx→call ObjectClass ctor 005F3900→4 个 vptr→returns this）",
    "005F4B10": "撤回：④ 字节真（007EF060 slot65=005F4B10，RTTI .?AVObjectClass@@）但行名类无 ② 链支持——② 原文归属 BuildingLightClass vt 007E3AD0 slot65 且 verdict_polarity=NEG、证据路径在 W174_dirty80；且 slot65 被 16 张表共有，类归属不可由 ④ 单独支撑",
    "0062AF70": "宿主 00629210 为真 ctor（call 0x410170 基类 ctor，4 个 vptr）",
    "0062B250": "mov_abs：目标 0xAC4910 在 .data（VirtualSize 域 0x812000..0xB79BE4）；宿主 00629190 为静态初始化器（非 ctor，mov_abs 不要求 ctor）",
    "0062B300": "同上（同 vt/同装表点，slot 4）",
    "00631CC0": "reg：宿主 007BA420 写 this@disp0 但为析构器——被 scalar-deleting 包装器 00477790 调用（test@00477798/call 0x7C8B3D@004777A0/ret 4），体内释成员后尾调基类析构 00631C80；该表无任何 ctor 写 this 的装表点",
    "0063FEA0": "宿主 0063F6B0 为真 ctor（call 0x652960 基类 ctor，returns this）",
    "00653850": "宿主 00652960（atlas 670B）为真 ctor；★执行器原取的 00652A83 是本审计初版启发式的假起点，已用 atlas+clean-decode 交叉确认 00652960",
    "0065C0D0": "mov_abs：目标 0xB04BD0 在 .data；宿主 0065B160 为静态初始化器",
    "0065C180": "同上（同 vt/同装表点，slot 4）",
    "0065CAC0": "SITE_FIX：旧点 0065CA03/宿主 0065CA00 为析构器（尾 0065CA5F mov [esi],0x7f08bc 写基类 vptr，被 00432610 删除包装器调用）→ 改取真 ctor 0065CAA8/0065CA80",
    "0065CDD0": "SITE_FIX：同 0065CAC0",
    "0065CF00": "SITE_FIX：同 0065CAC0",
    "0065D0D0": "SITE_FIX：同 0065CAC0",
    "0065D150": "SITE_FIX：旧点 004014C4 实测 mov [esp+0x20],0x7e1668 为栈临时写（宿主 004011C0 非 ctor）→ 改取真 ctor 0047AA3C/0047AA30（call 0x431B20 基类 ctor，returns this）",
    "0065D190": "SITE_FIX：同 0065D150",
    "006AC210": "宿主 006A4E60 为真 ctor（call 0x63F6B0 PowerClass ctor）",
    "006B8140": "entry 本身是 scalar deleting dtor；宿主 006B6C90（atlas 516B）为真 ctor（call 0x410170 基类 ctor）",
}

with open(os.path.join(HERE, "verdict.tsv"), "w", encoding="utf-8") as f:
    f.write("# R16-AUDIT-D1-WIDE-B3 逐行判决 — 独立复算（自写 PE/RTTI/装表点/宿主身份）\n")
    f.write("# verdict: PASS=该行 ④ 可用；WITHDRAW=应随行从宽读集合剔除并撤回 ④（Lead 已裁定）\n")
    f.write("entry\tname\tvt\tslot\tinstall_site\tfields_form\tmy_form\tfields_status\t"
            "A\tB\tC\tD\tE\tF\tverdict\tnote\n")
    for e in [r["entry"] for r in V["rows"]]:
        o = ROWS[e]
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            o["entry"], o["name"], o["vt"], o["slot"], o["site"],
            o["C"]["fields_form"], o["C"]["my_form"],
            FIELDS_BY.get(e, {}).get("status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"),
            "PASS" if o["A"]["pass"] else "FAIL",
            "PASS" if o["B"]["pass"] else "FAIL",
            "PASS" if o["C"]["pass"] else "FAIL",
            "PASS" if o["D"]["pass"] else "FAIL",
            "PASS" if o["E"]["pass_"] else "FAIL",
            "PASS" if o["F"]["pass_"] else "FAIL",
            o["verdict"], NOTE.get(e, "")))
print("wrote verdict.tsv")
