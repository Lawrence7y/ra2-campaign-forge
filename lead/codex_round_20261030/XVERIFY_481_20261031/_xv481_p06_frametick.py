#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p06：frame/tick 字段族内基线 + hold_tl 旁证 + exitstate 严格值域逐位复核。
   目的：核实「本批两趟 frame 恒 0 / tick 恒 1」是本协议常态还是本批特有（决定它是否构成新线索）。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
ALL = [("hold13", "20261030T211741_9001_P3e_E12_T1", "闩"), ("hold14", "20261030T212148_9001_P3e_E12_T1", "闩"),
       ("hold15", "20261030T212233_9001_P3e_E12_T1", "不闩"), ("E5h10", "20261030T072242_9001_P3e_E12_T1", "闩"),
       ("E5h15", "20261030T072353_9001_P3e_E12_T1", "不闩"), ("E5h20", "20261030T072630_9001_P3e_E12_T1", "不闩"),
       ("E12-1029T2228", "20261029T222811_9001_P3e_E12_T1", "闩"), ("E12-1029T2316", "20261029T231621_9001_P3e_E12_T1", "闩"),
       ("P3e-204123", "20261028T204123_9001_P3e_EARLY_MENU", "闩(挂死)"),
       ("P3e-204921", "20261028T204921_9001_P3e_EARLY_MENU", "闩"), ("P3e-205108", "20261028T205108_9001_P3e_EARLY_MENU", "闩"),
       ("b2-hold15.3", "20261031T083340_9001_P3e_E12_T1", "不闩-新"), ("b2-hold15.8", "20261031T083611_9001_P3e_E12_T1", "不闩-新")]

print("{:<16} {:>10} {:>7} {:>14} {:>14} {:>10} {:>12} {:>14}".format(
      "trip", "族", "n_rows", "frame 值域", "tick 值域", "wait值域", "hold_tl_n", "exitstate 值域"))
for tag, d, fam in ALL:
    base = f"{CB}/{d}"
    if not os.path.isfile(f"{base}/timeline.json"):
        print(f"  {tag}: 缺 timeline → UNVERIFIED"); continue
    tl = json.load(open(f"{base}/timeline.json", encoding="utf-8"))
    rows = tl["close_rows"]
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    fv = sorted({str(x.get("frame")) for x in rows}, key=lambda s: (len(s), s))
    tv = sorted({str(x.get("tick")) for x in rows}, key=lambda s: (len(s), s))
    wv = sorted({str(x.get("wait")) for x in rows})
    ev = sorted({str(x.get("exitstate")) for x in rows})
    ht = tl.get("hold_tl")
    print("{:<16} {:>10} {:>7} {:>14.14} {:>14.14} {:>10} {:>12} {:>14.14}".format(
        tag, fam, len(rows), ",".join(fv)[:14], ",".join(tv)[:14], ",".join(wv)[:10],
        str(r.get("hold_tl_n")) + "/" + str(len(ht) if isinstance(ht, list) else "-"), ",".join(ev)[:14]))
    if tag.startswith("b2"):
        mx = max((x.get("frame") or 0) for x in rows)
        print(f"      {tag}: frame max={mx}  非零行数={sum(1 for x in rows if x.get('frame'))}  "
              f"rows[0] t={rows[0]['t']}  rows[-1] t={rows[-1]['t']}")
        print(f"      _rec.hold_tl_n={r.get('hold_tl_n')} 与 len(timeline['hold_tl'])={len(ht)} 一致={r.get('hold_tl_n') == len(ht)}")
        # hold_tl 内 frame/tick 是否推进
        f2 = sorted({str(x.get("frame")) for x in ht}) if isinstance(ht, list) else "?"
        t2 = sorted({str(x.get("tick")) for x in ht}) if isinstance(ht, list) else "?"
        print(f"      hold_tl frame 值域={f2}  tick 值域={t2}  ws_kb 跨度="
              f"{(max(x['ws_kb'] for x in ht) - min(x['ws_kb'] for x in ht)) if isinstance(ht, list) and ht and 'ws_kb' in ht[0] else '?'} KB")
print("\n注：frame/tick 语义无定义来源（Y-7/§479 开放项①同族）——本表仅报读数形态，不作因果结论。")
