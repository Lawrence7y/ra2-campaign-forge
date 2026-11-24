#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q3 · 求 35 个对象的 ctor 单元 / dtor 单元起点与字节长度。

代码单元切分规则（卡面指定）：
  capstone 线性扫描（skipdata=True，否则扫描会中途停），
  ret 之后的第一个非填充指令（0x90 / 0xcc 单字节填充不算）为新单元起点。
  首个单元起点固定为 .text 起始 0x401000。
  ctor 单元 = 该对象「低地址写入站点」所在单元；
  dtor 单元 = 该对象「高地址写入站点」所在单元。
  单元长度 = 下一单元起点 - 本单元起点（末单元到 .text 尾）。

正控：0x40ee5d 所在单元起点 == 0x40ee40；0x40ee88 所在单元起点 == 0x40ee80。
反控：不开 skipdata 再扫，必须提前中断（记录中断地址）。

用法：timeout 300 python3 q3.py
"""

import bisect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_r123 as C

OUT = os.path.join(C.OUTDIR, "q3.json")


def q1_rows():
    p = os.path.join(C.OUTDIR, "q1.json")
    if not os.path.exists(p):
        raise SystemExit("先跑 q1.py")
    with open(p) as f:
        d = json.load(f)
    return [(int(r["obj"], 16),
             sorted([(int(w["site"], 16), int(w["imm"], 16)) for w in r["writes"]]))
            for r in d["objects"]]


def main():
    ck = C.Checks()
    C.preflight(ck)
    ins = C.Insns()
    ck.add("skipdata=True 线性扫描覆盖整个 .text", ins.why is None and ins.last_end == C.TEXT_END,
           "n_insn=%d last_end=0x%08x why=%s" % (ins.n, ins.last_end, ins.why))

    starts = C.unit_starts(ins)
    ck.add("单元数在合理量级（1e4..1e5）", 10000 <= len(starts) <= 100000, "units=%d" % len(starts))
    ck.add("首个单元起点 = .text 起点", int(starts[0]) == C.TEXT_VA, "0x%08x" % int(starts[0]))

    # 正控
    u_ee5d = C.unit_of(starts, 0x40EE5D)
    u_ee88 = C.unit_of(starts, 0x40EE88)
    ck.add("正控：0x40ee5d 所在单元起点 == 0x40ee40", u_ee5d == 0x40EE40, "0x%08x" % (u_ee5d or 0))
    ck.add("正控：0x40ee88 所在单元起点 == 0x40ee80", u_ee88 == 0x40EE80, "0x%08x" % (u_ee88 or 0))

    rows = []
    for obj, ws in sorted(q1_rows()):
        s1, s2 = ws[0][0], ws[1][0]
        u1 = C.unit_of(starts, s1)
        u2 = C.unit_of(starts, s2)
        k1 = C.unit_index(starts, u1)
        k2 = C.unit_index(starts, u2)
        a1, b1 = C.unit_range(starts, k1)
        a2, b2 = C.unit_range(starts, k2)
        rows.append({
            "obj": "0x%08x" % obj,
            "site_ctor": "0x%08x" % s1,
            "site_dtor": "0x%08x" % s2,
            "ctor_unit": "0x%08x" % u1,
            "dtor_unit": "0x%08x" % u2,
            "ctor_len": b1 - a1,
            "dtor_len": b2 - a2,
            "ctor_unit_end": "0x%08x" % b1,
            "dtor_unit_end": "0x%08x" % b2,
        })

    ck.add("每对象的 ctor/dtor 均为独立单元（35+35 个不同单元）",
           len({r["ctor_unit"] for r in rows}) == 35 and len({r["dtor_unit"] for r in rows}) == 35,
           "ctor_units=%d dtor_units=%d" % (len({r["ctor_unit"] for r in rows}),
                                            len({r["dtor_unit"] for r in rows})))
    ck.add("ctor 单元全部落在 dtor 单元之前（同一对象）",
           all(int(r["ctor_unit"], 16) < int(r["dtor_unit"], 16) for r in rows),
           "violations=%d" % sum(1 for r in rows
                                 if int(r["ctor_unit"], 16) >= int(r["dtor_unit"], 16)))
    len_hist = {}
    for r in rows:
        key = "%d/%d" % (r["ctor_len"], r["dtor_len"])
        len_hist[key] = len_hist.get(key, 0) + 1
    ck.add("ctor 单元长度全为正且 <= 0x400", all(0 < r["ctor_len"] <= 0x400 for r in rows),
           "hist=%s" % len_hist)

    # 反控：不开 skipdata
    ins2 = C.Insns(skipdata=False)
    ck.add("反控：不写 skipdata 时扫描提前中断", ins2.why is not None and ins2.last_end < C.TEXT_END,
           "n_insn=%d last_end=0x%08x why=%s" % (ins2.n, ins2.last_end, ins2.why))
    ck.add("反控：中断点在 .text 内部（不是段首即停）", C.TEXT_VA < ins2.last_end < C.TEXT_END,
           "0x%08x" % ins2.last_end)
    ck.add("反控：不 skipdata 的指令数显著少于 skipdata（数据字节被当指令吃）",
           ins2.n < ins.n, "no_skip=%d vs skip=%d" % (ins2.n, ins.n))
    starts2 = C.unit_starts(ins2)
    ck.add("反控：不 skipdata 时 0x40ee5d 单元划分与 skipdata 一致或不可达（记录）",
           True, "units=%d ; unit(0x40ee5d)=0x%08x"
           % (len(starts2), C.unit_of(starts2, 0x40EE5D) or 0))

    res = {
        "q": "Q3",
        "binary": C.EXE,
        "sha256": C.sha256(),
        "rule": "skipdata=True 线性扫描；ret 后第一个非 0x90/0xcc 单字节填充的指令为新单元起点",
        "n_insn": ins.n,
        "n_units": len(starts),
        "text_last_end": "0x%08x" % ins.last_end,
        "poscontrol": {"0x40ee5d": "0x%08x" % (u_ee5d or 0), "0x40ee88": "0x%08x" % (u_ee88 or 0)},
        "negcontrol_no_skipdata": {
            "n_insn": ins2.n, "last_end": "0x%08x" % ins2.last_end, "why": ins2.why,
            "n_units": len(starts2),
        },
        "ctor_len_dtor_len_hist": len_hist,
        "objects": rows,
        "checks": ck.rows,
        "selftest": ck.summary(),
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_insn", "n_units", "poscontrol",
                                          "negcontrol_no_skipdata", "ctor_len_dtor_len_hist",
                                          "selftest")}, ensure_ascii=False))
    return 0 if res["selftest"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
