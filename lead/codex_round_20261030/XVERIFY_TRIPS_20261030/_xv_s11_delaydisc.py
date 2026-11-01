#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s11：跨 9 趟菜单早窗自算「关窗→hwnd 归零延迟 Δ」与闩态的二分关系
   （台账未表述的候选判别式，用于检验「关窗时引擎阶段」中介说）。只读原始 timeline。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
D = [("hold13(本批)", "20261030T211741_9001_P3e_E12_T1"),
     ("hold14(本批)", "20261030T212148_9001_P3e_E12_T1"),
     ("hold15(本批)", "20261030T212233_9001_P3e_E12_T1"),
     ("E5h10", "20261030T072242_9001_P3e_E12_T1"),
     ("E5h15", "20261030T072353_9001_P3e_E12_T1"),
     ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
     ("E12 1029T2228", "20261029T222811_9001_P3e_E12_T1"),
     ("E12 1029T2316", "20261029T231621_9001_P3e_E12_T1"),
     ("P3e 204123(挂死)", "20261028T204123_9001_P3e_EARLY_MENU"),
     ("P3e 204921", "20261028T204921_9001_P3e_EARLY_MENU"),
     ("P3e 205108", "20261028T205108_9001_P3e_EARLY_MENU")]
hdr = "{:<19} {:>8} {:>9} {:>9} {:>9} {:>9} {:>8}"
print(hdr.format("trip", "close_s", "hwnd0_ab", "d(h-z)", "latch_ab", "n(1)", "exited"))
lat, nol = [], []
for tag, d in D:
    if not os.path.isfile(f"{CB}/{d}/_rec.json"):
        print(f"  {tag}: 缺"); continue
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    li = r.get("latch_row_index")
    lab = round(rows[li]["t"] - t0, 3) if li is not None else None
    hzabs = round(rows[hz[0]]["t"] - t0, 3) if hz else None
    dd = round(hzabs - r["closed_at_s"], 3) if hzabs else None
    print(hdr.format(tag, "%.3f" % r["closed_at_s"], str(hzabs), ("%.3f" % dd) if dd is not None else "-",
                      str(lab), str(len(ones)), str(r.get("exited"))))
    if dd is not None:
        (lat if ones else nol).append((tag, dd, len(ones), hzabs, r["closed_at_s"]))
print("\n闩态趟 Δ(hwnd归零-close):", [(t, d) for t, d, *_ in lat])
print("无闩趟 Δ:", [(t, d) for t, d, *_ in nol])
print("二分成立(闩侧 Δ 全部 <0.15 且 无闩侧 Δ 全部 >0.35)?",
      bool(lat) and bool(nol) and max(d for _, d, *_ in lat) < 0.15 < min(d for _, d, *_ in nol))
print("闩侧 Δ max=%.3f min=%.3f ; 无闩侧 Δ min=%.3f max=%.3f" % (
    max(d for _, d, *_ in lat), min(d for _, d, *_ in lat),
    min(d for _, d, *_ in nol), max(d for _, d, *_ in nol)))
print("无闩趟的 hwnd 归零绝对时刻（是否落 21s 带）:", [(t, h) for t, d, n, h, c in nol])
print("闩趟的 hwnd 归零绝对时刻:", [(t, h) for t, d, n, h, c in lat])
