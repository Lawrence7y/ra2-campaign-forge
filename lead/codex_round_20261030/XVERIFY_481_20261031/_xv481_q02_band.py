#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）第二任对账员独立探针 q02：
   (a) §481「5 个不闩趟跨 3 会话聚集 20.587~21.651」——5 点归零绝对 + 会话可证性全部由本探针从盘上重算；
   (b) §481「close 分布 16.09~17.17（跨 1.1s）而归零聚在 ~1.1s 窄带」两句的集合口径核对（p03 发现的复核）；
   (c) 闩族 latch_abs 带（p12 增量）独立抽验。
   只读；stdout 落 _raw/q02_stdout.txt。
"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
NOLATCH = [("E5h15", "20261030T072353_9001_P3e_E12_T1"), ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
           ("hold15", "20261030T212233_9001_P3e_E12_T1"), ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"),
           ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]
LATCH = [("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold14", "20261030T212148_9001_P3e_E12_T1"),
         ("E5h10", "20261030T072242_9001_P3e_E12_T1"), ("1029T2228", "20261029T222811_9001_P3e_E12_T1"),
         ("1029T2316", "20261029T231621_9001_P3e_E12_T1"), ("204123", "20261028T204123_9001_P3e_EARLY_MENU"),
         ("204921", "20261028T204921_9001_P3e_EARLY_MENU"), ("205108", "20261028T205108_9001_P3e_EARLY_MENU")]

print("== (a) 不闩族 5 点：归零绝对（自启动）+ 会话可证性 ==")
rows_out = []
for tag, d in NOLATCH:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hzi = next(i for i, x in enumerate(rows) if x.get("hwnd") == 0)
    dl = round(rows[hzi]["t"] - rows[0]["t"], 3)
    absz = round(r["closed_at_s"] + dl, 3)
    rows_out.append((tag, r["closed_at_s"], dl, absz, r.get("boot_wallclock_ms_at_start")))
    print(f"  {tag:<9} close={r['closed_at_s']:<8} Δ={dl:<7} 归零绝对={absz:<8} boot_wall={r.get('boot_wallclock_ms_at_start')}")
sess = sorted({x[4] for x in rows_out if x[4]})
absz_all = [x[3] for x in rows_out]
print(f"  归零绝对全距 = [{min(absz_all)}, {max(absz_all)}] 跨度 {round(max(absz_all)-min(absz_all),3)} s  (§481 称 20.587~21.651)")
print(f"  boot_wall 非空趟数={sum(1 for x in rows_out if x[4])}/5  不同会话数={len(sess)}  (§481 称跨 3 会话)")

print("\n== (b) §481 两句的集合口径 ==")
c4 = [x[1] for x in rows_out if x[0] != "E5h20"]
print(f"  『close 分布 16.09~17.17（跨 1.1s）』: 4 点（不含 E5h20，其 close=21.249）= {sorted(c4)} "
      f"跨度 {round(max(c4)-min(c4),3)} s")
print(f"  『归零聚在 ~1.1s 窄带』: 全 5 点归零跨度 = {round(max(absz_all)-min(absz_all),3)} s；"
      f"同 4 点口径 = {round(max(x[3] for x in rows_out if x[0]!='E5h20') - min(x[3] for x in rows_out if x[0]!='E5h20'),3)} s")
print(f"  ⇒ §481 该句 close 用 4 点集合、归零用 5 点集合（口径混合，数值本身都对，须改述为同集合口径）")

print("\n== (c) 闩族 latch_abs 带（p12 增量的独立抽验） ==")
latch_abs = []
for tag, d in LATCH:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    li = r.get("latch_row_index")
    if li is None:  # 旧 schema：闩行=首个 exitstate==1 行（§479 教训口径）
        li = next((i for i, x in enumerate(rows) if x.get("exitstate") == 1), None)
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    lab = round(rows[li]["t"] - t0, 3) if li is not None else None
    latch_abs.append((tag, lab))
    print(f"  {tag:<9} latch 行绝对(自启动)={lab}")
vals = [v for _t, v in latch_abs if v is not None]
print(f"  闩族 latch_abs 全距 = [{min(vals)}, {max(vals)}] n={len(vals)}  (p12 称 [20.145, 22.552])")
union = sorted(absz_all + vals)
print(f"  合成 ~21s 带（不闩 hz_abs ∪ 闩 latch_abs）= [{min(union)}, {max(union)}] 跨度 {round(max(union)-min(union),3)} s n={len(union)}")
