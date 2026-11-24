#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q4 · 由 ctor 单元体推出对象字段布局（绝对写偏移集合）。

口径：
  写形态：c7 05 <disp32> <imm32>（10B，写 4 字节）、c6 05 <disp32> <imm8>（7B，写 1 字节）、
          a3 <disp32>（5B，mov [disp32],eax，写 4 字节）。
  统计范围：q3 给出的 ctor 单元体 [unit_start, unit_next_start)。
  目标窗口：[obj, obj+0x100)。
  字段上界 = max(offset + width)，即对象尺寸下界估计。

正控：字段集合应包含偏移 0（vptr）。
反控：窗口 0x100 -> 0x100000（同 ctor 单元体内）记录差异；
      另给出「不限定 ctor 单元（全 .text）」的对照，用来显示 0x100 窗口会混入
      落在同一窗口内的邻居全局对象字段（例如 +0x6c / +0x99 / +0xa0 的写入）。

用法：timeout 300 python3 q4.py
"""

import bisect
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_r123 as C

OUT = os.path.join(C.OUTDIR, "q4.json")


def q3_rows():
    p = os.path.join(C.OUTDIR, "q3.json")
    if not os.path.exists(p):
        raise SystemExit("先跑 q3.py")
    with open(p) as f:
        d = json.load(f)
    return d["objects"]


def whole_text_writes(ins, objs, win):
    """全 .text 范围内对 [obj, obj+win) 的绝对写（不限定单元）。"""
    d = C.load()
    out = {}
    oset = sorted(objs)
    for k in range(ins.n):
        a = int(ins.a[k])
        sz = int(ins.s[k])
        off = 0x1000 + (a - C.TEXT_VA)
        b = d[off:off + sz]
        if sz == 10 and b[0] == 0xC7 and b[1] == 0x05:
            t = struct.unpack_from("<I", b, 2)[0]
        elif sz == 7 and b[0] == 0xC6 and b[1] == 0x05:
            t = struct.unpack_from("<I", b, 2)[0]
        elif sz == 5 and b[0] == 0xA3:
            t = struct.unpack_from("<I", b, 1)[0]
        else:
            continue
        for o in oset:
            if o <= t < o + win:
                out.setdefault(o, []).append((a, t - o))
    return out


def main():
    ck = C.Checks()
    C.preflight(ck)
    ins = C.Insns()
    starts = C.unit_starts(ins)
    rows3 = q3_rows()
    objs = [int(r["obj"], 16) for r in rows3]

    rows = []
    for r in rows3:
        obj = int(r["obj"], 16)
        u = int(r["ctor_unit"], 16)
        w100 = C.abs_writes_in_unit(ins, starts, u, obj, 0x100)
        wbig = C.abs_writes_in_unit(ins, starts, u, obj, 0x100000)
        offs = sorted(w100)
        mx = 0
        for o, lst in w100.items():
            for _kind, w, _site in lst:
                mx = max(mx, o + w)
        detail = {("+0x%02x" % o): [{"kind": k, "width": w, "site": "0x%08x" % s}
                                    for k, w, s in sorted(w100[o])] for o in offs}
        rows.append({
            "obj": "0x%08x" % obj,
            "ctor_unit": "0x%08x" % u,
            "ctor_len": r["ctor_len"],
            "field_offsets": ["+0x%02x" % o for o in offs],
            "field_count": len(offs),
            "size_from_upper_bound": mx,
            "size_hex": "0x%02x" % mx,
            "offsets_at_1MB_window": ["+0x%x" % o for o in sorted(wbig)],
            "window_extra_offsets": ["+0x%x" % o for o in sorted(set(wbig) - set(w100))],
            "writes": detail,
        })

    set_hist = {}
    for r in rows:
        k = ",".join(r["field_offsets"])
        set_hist[k] = set_hist.get(k, 0) + 1
    ck.add("35 个对象的字段偏移集合完全一致", len(set_hist) == 1, "distinct_sets=%d %s"
           % (len(set_hist), set_hist))
    ck.add("正控：字段集合包含偏移 0（vptr）",
           all(0 in [int(f, 16) for f in r["field_offsets"]] for r in rows),
           "ok=%d/35" % sum(1 for r in rows if 0 in [int(f, 16) for f in r["field_offsets"]]))
    ck.add("字段偏移全部 4 字节对齐", all(int(f, 16) % 4 == 0 for r in rows for f in r["field_offsets"]),
           "nonaligned=%d" % sum(1 for r in rows for f in r["field_offsets"] if int(f, 16) % 4))
    ck.add("字段偏移集合 = {0,4,8,0xc,0x10,0x14}",
           set(set_hist) == {"+0x00,+0x04,+0x08,+0x0c,+0x10,+0x14"}, "sets=%s" % list(set_hist))
    ck.add("由字段上界推出的对象尺寸全为 0x18",
           {r["size_from_upper_bound"] for r in rows} == {0x18},
           "sizes=%s" % sorted({r["size_hex"] for r in rows}))
    ck.add("字段集合里含 4 字节 imm 写（c7 05）与 1 字节 imm 写（c6 05）",
           all(any(w["width"] == 4 for lst in r["writes"].values() for w in lst) and
               any(w["width"] == 1 for lst in r["writes"].values() for w in lst) for r in rows),
           "c6_05_count=%d" % sum(1 for r in rows for lst in r["writes"].values()
                                  for w in lst if w["kind"] == "c6 05"))
    ck.add("单元体内含 a3 形态写（mov [disp32],eax）",
           all(any(w["kind"] == "a3" for lst in r["writes"].values() for w in lst) for r in rows),
           "a3_count=%d" % sum(1 for r in rows for lst in r["writes"].values()
                               if any(w["kind"] == "a3" for w in lst)))

    # ---- 反控 1（卡面口径）：窗口 0x100 -> 0x100000，限定本 ctor 单元体
    extra_objs = [r["obj"] for r in rows if r["window_extra_offsets"]]
    n_extra = sum(len(r["window_extra_offsets"]) for r in rows)
    ck.add("反控 1：ctor 单元体内把窗口放大到 0x100000，新增偏移数（如实记录）", True,
           "objs_with_extra=%d total_extra=%d ; 原因：单元体只长 %s 字节，绝对写目标全在 +0x14 以内"
           % (len(extra_objs), n_extra, sorted({r["ctor_len"] for r in rows})))

    # ---- 反控 2：不限定单元（全 .text）、窗口 0x100 -> 0x100000
    wt100 = whole_text_writes(ins, objs, 0x100)
    wtbig = whole_text_writes(ins, objs, 0x100000)
    per100 = {o: sorted({off for _s, off in v}) for o, v in wt100.items()}
    perbig = {o: sorted({off for _s, off in v}) for o, v in wtbig.items()}
    contaminated = sum(1 for o in objs if set(per100.get(o, [])) - {0, 4, 8, 12, 16, 20})
    ck.add("反控 2：不限定单元时，0x100 窗口会混入非 ctor 字段（邻居全局对象）",
           contaminated >= 1,
           "objs_with_foreign=%d/35 ; 例：0xa83e30 -> %s"
           % (contaminated, ["+0x%x" % x for x in per100.get(0xA83E30, [])][:10]))
    grows = sum(1 for o in objs if len(perbig.get(o, [])) > len(per100.get(o, [])))
    ck.add("反控 2b：不限定单元时窗口 0x100000 的偏移集合严格多于 0x100", grows >= 1,
           "objs_grown=%d/35 ; 例：0xa83e30 %d -> %d 个偏移"
           % (grows, len(per100.get(0xA83E30, [])), len(perbig.get(0xA83E30, []))))

    res = {
        "q": "Q4",
        "binary": C.EXE,
        "sha256": C.sha256(),
        "scope": "q3 的 ctor 单元体内，对 [obj, obj+0x100) 的绝对写（c7 05 / c6 05 / a3）",
        "n_objects": len(rows),
        "field_set_hist": set_hist,
        "size_hist": {r["size_hex"]: sum(1 for x in rows if x["size_hex"] == r["size_hex"])
                      for r in rows},
        "poscontrol_has_offset0": sum(1 for r in rows if 0 in [int(f, 16) for f in r["field_offsets"]]),
        "negcontrol_same_unit_1MB": {"objs_with_extra": len(extra_objs),
                                     "total_extra_offsets": n_extra},
        "negcontrol_whole_text_100": {
            "objs_with_foreign_offsets": contaminated,
            "per_obj_offsets_sample": {"0xa83e30": ["+0x%x" % x for x in per100.get(0xA83E30, [])],
                                       "0x887388": ["+0x%x" % x for x in per100.get(0x887388, [])],
                                       "0x887568": ["+0x%x" % x for x in per100.get(0x887568, [])]},
        },
        "negcontrol_whole_text_1MB": {
            "objs_grown_vs_100": grows,
            "per_obj_offsets_sample": {"0xa83e30": ["+0x%x" % x for x in perbig.get(0xA83E30, [])][:16]},
        },
        "objects": rows,
        "checks": ck.rows,
        "selftest": ck.summary(),
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_objects", "field_set_hist", "size_hist",
                                          "poscontrol_has_offset0", "negcontrol_same_unit_1MB",
                                          "selftest")}, ensure_ascii=False))
    return 0 if res["selftest"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
