# -*- coding: utf-8 -*-
"""D-21 裁 A 第 5 条：五读负担复算（同一 87 窗、同一基线、两套沿数口径）。

只读既有 measure_w*.json。零真机。
同时纠正两处算式：
  - 6→5 减少的是原六读的 1/6（16.67%），不是 20%（20% 是「六比五多」的分母）
  - 五读整体增幅 = 5×沿数/基线，不是 D-21 条目里我写的 +12.6%
"""
import glob
import io
import json

GLOB = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json'

files = sorted(glob.glob(GLOB))
print("files:", len(files))

rows = []
for p in files:
    d = json.load(io.open(p, encoding="utf-8"))
    st = d.get("stats") or {}
    if d.get("span_s") != 25.0 or (st.get("samples") or 0) == 0:
        continue
    rows.append(dict(
        trip=d.get("trip_id"), w=d.get("window"),
        samples=st.get("samples"), n_edges=st.get("n_edges"),
    ))

print("25s windows:", len(rows))
S = sum(r["samples"] for r in rows)
E = sum(r["n_edges"] for r in rows)
T = sum(max(0, r["n_edges"] - 1) for r in rows)   # 跳变口径（首样不触发）
print("Σsamples(基线) = %d" % S)
print("Σn_edges(沿表) = %d ; Σ跳变 = %d" % (E, T))

worst = max(rows, key=lambda r: r["n_edges"])
print("最坏窗: %s w%s edges=%d samples=%d"
      % (worst["trip"], worst["w"], worst["n_edges"], worst["samples"]))

print("\n" + "=" * 74)
print("三种读次口径 × 两套沿数口径")
print("=" * 74)
print("%-22s %-16s %-16s" % ("口径", "沿表", "跳变"))
for n, lbl in ((4, "4读(A2 原稿)"), (5, "5读(D-21 裁A)"), (6, "6读(W5 旧版)")):
    a = 100.0 * n * E / S
    b = 100.0 * n * T / S
    print("%-22s +%-14.3f%% +%-14.3f%%" % (lbl, a, b))

print("\n最坏单窗（edges=%d / samples=%d）：" % (worst["n_edges"], worst["samples"]))
for n in (4, 5, 6):
    a = 100.0 * n * worst["n_edges"] / worst["samples"]
    b = 100.0 * n * max(0, worst["n_edges"] - 1) / worst["samples"]
    print("  %d读  沿表 +%.4f%%   跳变 +%.4f%%" % (n, a, b))

print("\n" + "=" * 74)
print("★ 两处算式纠正")
print("=" * 74)
print("  (1) 6→5 的减少比例：")
print("      减少量 = 1 读；分母取【原六读】⇒ 1/6 = %.4f%%" % (100.0 / 6))
print("      20%% 是「六比五多」的分母（1/5），**不能**说「减少 20%%」")
print("  (2) 五读整体增幅（沿表）= 5×%d / %d = %.4f%%" % (E, S, 100.0 * 5 * E / S))
print("      D-21 条目里我写的 +12.6%% **错**，裁决书给的 ~13.09%% **对**")

print("\n" + "=" * 74)
print("字节口径（每读 4 B）")
print("=" * 74)
for n, lbl in ((5, "5读"), (6, "6读")):
    print("  %s：每沿 %d B；87 窗合计 %d B；最坏窗 %d B；最坏窗字节率 %.1f B/s"
          % (lbl, 4 * n, 4 * n * E, 4 * n * worst["n_edges"],
             4 * n * worst["n_edges"] / 25.0))

print("\n★ 全部为「名义操作数」，不是耗时/CPU/扰动实测（RULING_D19.md:69）")
print("\nDONE")
