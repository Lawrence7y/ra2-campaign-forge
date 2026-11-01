#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p12：P3e 族 13 趟的三时刻对（close / hwnd 归零绝对 / 闩绝对）与 ~21s 带的合成口径。
   闩绝对时刻 = timeline.close_rows[latch_row_index].t − t0（t0 = close_delivery.t − closed_at_s；自启动起算），
   无 latch_row_index 键的 10-28 三趟改用首个 exitstate==1 行自推（口径与上轮 §6-4 schema 披露一致）。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
ALL = [("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold14", "20261030T212148_9001_P3e_E12_T1"),
       ("hold15", "20261030T212233_9001_P3e_E12_T1"), ("E5h10", "20261030T072242_9001_P3e_E12_T1"),
       ("E5h15", "20261030T072353_9001_P3e_E12_T1"), ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
       ("E12-2228", "20261029T222811_9001_P3e_E12_T1"), ("E12-2316", "20261029T231621_9001_P3e_E12_T1"),
       ("P3e-204123", "20261028T204123_9001_P3e_EARLY_MENU"), ("P3e-204921", "20261028T204921_9001_P3e_EARLY_MENU"),
       ("P3e-205108", "20261028T205108_9001_P3e_EARLY_MENU"),
       ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]
print("{:<12} {:>8} {:>9} {:>9} {:>9} {:>9} {:>10} {:>7}".format(
      "trip", "close", "hz_abs", "Δ", "latch_abs", "退_abs", "latch−hz", "族"))
hz_all, lat_all = [], []
for tag, d in ALL:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    hz = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    li = r.get("latch_row_index")
    if li is None and ones:
        li = ones[0]
    hzab = round(rows[hz]["t"] - t0, 3) if hz is not None else None
    lab = round(rows[li]["t"] - t0, 3) if li is not None else None
    eab = None
    if ones:
        last = ones[-1]
        if last + 1 < len(rows) and rows[last + 1].get("wait") == 0:
            eab = round(rows[last + 1]["t"] - t0, 3)
    fam = "闩" if ones else "不闩"
    print("{:<12} {:>8.3f} {:>9} {:>9} {:>9} {:>9} {:>10} {:>7}".format(
        tag, r["closed_at_s"], str(hzab), round(hzab - r["closed_at_s"], 3) if hzab else "-",
        str(lab), str(eab), round(lab - hzab, 3) if (lab and hzab) else "-", fam))
    if hzab:
        hz_all.append((tag, hzab, fam))
    if lab:
        lat_all.append((tag, lab))
print(f"\n闩族 latch_abs 区间 = [{min(v for _, v in lat_all):.3f}, {max(v for _, v in lat_all):.3f}]  n={len(lat_all)}")
print("  " + ", ".join(f"{t}={v:.3f}" for t, v in lat_all))
nl = [(t, v) for t, v, f in hz_all if f == "不闩"]
lt = [(t, v) for t, v, f in hz_all if f == "闩"]
print(f"不闩族 hz_abs 区间 = [{min(v for _, v in nl):.3f}, {max(v for _, v in nl):.3f}] n={len(nl)}")
print(f"闩族   hz_abs 区间 = [{min(v for _, v in lt):.3f}, {max(v for _, v in lt):.3f}] n={len(lt)}")
comb = sorted([v for _, v in nl] + [v for _, v in lat_all])
print(f"\n合成 ~21s 带（不闩 hz_abs ∪ 闩 latch_abs）= [{min(comb):.3f}, {max(comb):.3f}] 跨度 {max(comb)-min(comb):.3f}s n={len(comb)}")
print("  注：本批 2 点把带的下沿从 21.094 拉低到 20.587 ⇒ 带跨度由 0.557s（上轮 3 点）扩为 "
      f"{max(nl)[1]-min(v for _,v in nl):.3f}s（5 点）")
print("\n闩族内 Δ(hz−close) 与 latch−hz 的关系（闩发生在 hwnd 归零之后多久）:")
for t, v, f in hz_all:
    if f == "闩":
        lab = dict(lat_all).get(t)
        print(f"  {t:<12} hz_abs={v}  latch_abs={lab}  latch−hz={round(lab - v, 3)}")
