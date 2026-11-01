#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p02：Δ 二分轴全量复核 n=13 + boot 会话一致性 + hold→closed 开销重算。
   Δ 算法**独立重写**：t0 = close_rows[0].t（上轮 _xv_s11 用 close_delivery.t − closed_at_s 反推 t0），
   两口径并列打印以显式暴露差异。既有 11 点清单取自上轮对账书 §6-1（XVERIFY_TRIPS_20261030.md:354-357）
   + _xv_s11_delaydisc.py:9-19 的目录列表，全部由本探针重跑重算（不引用上轮 stdout）。
   闩/不闩族归属一律由盘上原始行 exitstate==1 计数判定（不采信 _rec 的 latch_detected 单一字段）。
"""
import json, io, sys, os
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
CST = timezone(timedelta(hours=8))

PREV = [  # 上轮 11 点（tag, 目录, 上轮记录 Δ, 上轮族判定）
    ("hold13", "20261030T211741_9001_P3e_E12_T1", 0.101, "闩"),
    ("hold14", "20261030T212148_9001_P3e_E12_T1", 0.101, "闩"),
    ("hold15", "20261030T212233_9001_P3e_E12_T1", 4.822, "不闩"),
    ("E5h10", "20261030T072242_9001_P3e_E12_T1", 0.101, "闩"),
    ("E5h15", "20261030T072353_9001_P3e_E12_T1", 5.023, "不闩"),
    ("E5h20", "20261030T072630_9001_P3e_E12_T1", 0.402, "不闩"),
    ("E12-1029T2228", "20261029T222811_9001_P3e_E12_T1", 0.122, "闩"),
    ("E12-1029T2316", "20261029T231621_9001_P3e_E12_T1", 0.101, "闩"),
    ("P3e-204123(挂死)", "20261028T204123_9001_P3e_EARLY_MENU", 0.102, "闩"),
    ("P3e-204921", "20261028T204921_9001_P3e_EARLY_MENU", 0.102, "闩"),
    ("P3e-205108", "20261028T205108_9001_P3e_EARLY_MENU", 0.100, "闩"),
]
NEW = [("b2-hold15.3", "20261031T083340_9001_P3e_E12_T1", 3.718, "不闩"),
       ("b2-hold15.8", "20261031T083611_9001_P3e_E12_T1", 3.414, "不闩")]


def load(d):
    base = f"{CB}/{d}"
    ok = os.path.isfile(f"{base}/_rec.json") and os.path.isfile(f"{base}/timeline.json")
    if not ok:
        return None, None
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{base}/timeline.json", encoding="utf-8"))["close_rows"]
    return r, rows


def ep(ms):
    return (datetime.fromtimestamp(ms / 1000, CST).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+08") if ms else "None"


hdr = ("{:<19} {:>8} {:>8} {:>8} {:>8} {:>9} {:>5} {:>5} {:>5} {:>6} {:>6} {:>7} {:>16}")
print(hdr.format("trip", "close_s", "Δ本算", "Δ上轮", "Δ反推", "hz0绝对", "idx", "sg0", "n(1)",
                 "latchfld", "exited", "hold", "boot_wallclock"))
pts = []
missing = []
for tag, d, prevd, _fam in PREV + NEW:
    src = "new" if any(a == tag for a, _, _, _ in NEW) else "prev"
    r, rows = load(d)
    if r is None:
        missing.append(tag); print(f"  {tag}: 缺件 {d} → UNVERIFIED"); continue
    t0 = rows[0]["t"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    sg = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    dO = round(rows[hz[0]]["t"] - t0, 3) if hz else None
    dR = round(rows[hz[0]]["t"] - (r["close_delivery"]["t"] - r["closed_at_s"]), 3) if hz else None
    ab = round(r["closed_at_s"] + dO, 3) if dO is not None else None
    hold = r.get("e2_params", {}).get("hold_after_window_s")
    print(hdr.format(tag, "%.3f" % r["closed_at_s"], str(dO), "%.3f" % prevd, str(dR), str(ab),
                     hz[0] if hz else "-", sg[0] if sg else "-", len(ones),
                     str(r.get("latch_detected", "no-key")), str(r.get("exited")),
                     str(hold), str(r.get("boot_wallclock_ms_at_start"))))
    pts.append(dict(tag=tag, src=src, close=r["closed_at_s"], dOwn=dO, dPrev=prevd, dRev=dR, absz=ab,
                    hz=hz[0] if hz else None, sg=sg[0] if sg else None, n1=len(ones),
                    latch=r.get("latch_detected"), hold=hold, bootw=r.get("boot_wallclock_ms_at_start"),
                    bootms=r.get("boot_ms_at_start"), wall=r.get("wallclock_ms_at_start"),
                    n=len(rows), same=(hz and sg and hz[0] == sg[0])))

print(f"\n缺件趟: {missing if missing else '无'}")
print("\n== Δ 与上轮记录差（本算 vs 上轮 §6-1 记载）==")
for p in pts:
    dd = None if p["dOwn"] is None else round(p["dOwn"] - p["dPrev"], 3)
    print(f"  {p['tag']:<19} 本算={p['dOwn']} 上轮={p['dPrev']} 差={dd}")

print("\n== Δ 二分轴 n=13 重算 ==")
valid = [p for p in pts if p["dOwn"] is not None]
lat = [p for p in valid if p["n1"] > 0]
nol = [p for p in valid if p["n1"] == 0]
print(f"  n={len(valid)}  闩族(∃ exitstate==1)={len(lat)}  不闩族(0 行)={len(nol)}")
print("  闩族 Δ:", [(p["tag"], p["dOwn"]) for p in lat])
print("  不闩族 Δ:", [(p["tag"], p["dOwn"]) for p in nol])
lmax = max(p["dOwn"] for p in lat); nmin = min(p["dOwn"] for p in nol)
print(f"  闩侧 max Δ={lmax:.3f} (min={min(p['dOwn'] for p in lat):.3f}) ; 不闩侧 min Δ={nmin:.3f} (max={max(p['dOwn'] for p in nol):.3f})")
print(f"  判据 Δ<0.15⇒闩 ∧ Δ>0.35⇒不闩 于 n={len(valid)} 零例外? {lmax < 0.15 and nmin > 0.35}")
print(f"  灰区 [0.15,0.35] 内点数 = {sum(1 for p in valid if 0.15 <= p['dOwn'] <= 0.35)}")
print("  族归属 vs _rec.latch_detected 一致性:")
for p in valid:
    if p["latch"] is None or isinstance(p["latch"], bool):
        print(f"    {p['tag']:<19} n(1)={p['n1']:<5} latch_detected={p['latch']} 一致={bool(p['n1']) == bool(p['latch'])}")
    else:
        print(f"    {p['tag']:<19} n(1)={p['n1']:<5} latch_detected=<无此键(旧schema)>")

print("\n== ~21s 绝对带（不闩族 hwnd 归零绝对时刻 / close 分布）==")
for p in nol:
    print(f"  {p['tag']:<19} close={p['close']:.3f}  Δ={p['dOwn']}  归零绝对={p['absz']}  [会话 boot_wall={p['bootw']}]")
band = [p["absz"] for p in nol]
print(f"  不闩族归零绝对跨度 {min(band):.3f} ~ {max(band):.3f} s (n={len(band)})  close 跨度 "
      f"{min(p['close'] for p in nol):.3f} ~ {max(p['close'] for p in nol):.3f} s")
print(f"  闩族归零绝对: " + ", ".join(f"{p['tag']}={p['absz']}" for p in lat))

print("\n== (4) boot 会话一致性 ==")
for p in pts:
    print(f"  {p['tag']:<19} boot_wall={p['bootw']} ({ep(p['bootw'])})  boot_ms={p['bootms']}  "
          f"wall={p['wall']} ({ep(p['wall'])})  自洽(wall−boot==wallboot)={None if not p['wall'] or not p['bootms'] or not p['bootw'] else (p['wall'] - p['bootms'] == p['bootw'])}")
nb = [p["bootw"] for p in pts if p["src"] == "new" and p["bootw"]]
print(f"  本批 2 趟极差 = {max(nb) - min(nb)} ms ; 会话起点 = {ep(min(nb))}")
prev_b = [p["bootw"] for p in pts if p["src"] == "prev" and p["bootw"]]
print(f"  §474 批(10-30) 可证 boot_wall = 1793337038119/…113 → {ep(1793337038119)}")
print(f"  本批 − §474 会话 = {min(nb) - 1793337038119} ms ≈ {(min(nb) - 1793337038119)/1000/3600:.2f} h ⇒ 不同会话? {min(nb) != 1793337038119}")

print("\n== (5) hold→closed 投递开销重算 ==")
for p in pts:
    if p["hold"] is None:
        print(f"  {p['tag']:<19} hold 键缺失 → 开销不可算 (closed={p['close']})"); continue
    print(f"  {p['tag']:<19} hold={p['hold']} closed={p['close']} 开销={round(p['close'] - p['hold'], 3)} "
          f"会话boot={p['bootw']}")
