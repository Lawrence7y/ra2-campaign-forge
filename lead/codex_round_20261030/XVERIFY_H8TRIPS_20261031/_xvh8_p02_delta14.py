#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p02：Δ 轴 n=14（13+本趟 2C）族内重算 + 闩→退 9 行族全量 + 量化律 n=14 a/post 带重算。

口径（族内，与上两轮对账一致）：
 - Δ = 首个 hwnd==0 行 t − close_rows[0].t（_xv481_q01/p02 口径；本趟 close_rows[0].t==close_delivery.t 已亲验）；
 - 闩族 = ∃ exitstate==1（盘上原始行）；闩→退 = rows[末行].t − rows[首个 exitstate==1].t
   （末行=wait==WAIT_OBJECT_0 行，含 read_fail-DICT 字段——§477 R-1 与 _xv_s01/s07 族内先例口径；
   并列打印「数值末行」口径以显式暴露两者之差）；
 - 量化律 closed = a + ceil(hold) + post，a = hold_tl[0].t − t0(反推)，post = closed − a − ceil(hold)
   （_xv481_p15 口径，:30）；hold_tl_n == ceil(hold) 同检；
 - 清单 = XVERIFY_481/_xv481_p02_delta13.py 的 PREV(11)+NEW(2) + 本批 2C 1 趟 = 14。
只读。
"""
import json, io, sys, os, math
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
TRIPS = [
    ("hold13",        "20261030T211741_9001_P3e_E12_T1",     0.101, "§481"),
    ("hold14",        "20261030T212148_9001_P3e_E12_T1",     0.101, "§481"),
    ("hold15",        "20261030T212233_9001_P3e_E12_T1",     4.822, "§481"),
    ("E5h10",         "20261030T072242_9001_P3e_E12_T1",     0.101, "§481"),
    ("E5h15",         "20261030T072353_9001_P3e_E12_T1",     5.023, "§481"),
    ("E5h20",         "20261030T072630_9001_P3e_E12_T1",     0.402, "§481"),
    ("E12-1029T2228", "20261029T222811_9001_P3e_E12_T1",     0.122, "§481"),
    ("E12-1029T2316", "20261029T231621_9001_P3e_E12_T1",     0.101, "§481"),
    ("P3e-204123",    "20261028T204123_9001_P3e_EARLY_MENU", 0.102, "§481"),
    ("P3e-204921",    "20261028T204921_9001_P3e_EARLY_MENU", 0.102, "§481"),
    ("P3e-205108",    "20261028T205108_9001_P3e_EARLY_MENU", 0.100, "§481"),
    ("b2-h15.3",      "20261031T083340_9001_P3e_E12_T1",     3.718, "§481"),
    ("b2-h15.8",      "20261031T083611_9001_P3e_E12_T1",     3.414, "§481"),
    ("2C-h14.0",      "20261031T154139_9001_P3e_E12_T1",     None,  "§485"),
]

hdr = "{:<15}{:>8}{:>7}{:>7}{:>5}{:>5}{:>9}{:>9}{:>7}{:>6}{:>5}{:>12}"
print(hdr.format("trip", "close_s", "Δ本算", "Δ台账", "n(1)", "闩?", "wait末行", "闩→退末行", "hold", "ceil", "n读", "a/post"))
pts = []
for tag, d, prevd, src in TRIPS:
    base = f"{CB}/{d}"
    rec = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{base}/timeline.json", encoding="utf-8"))
    rows, ht = tl["close_rows"], tl["hold_tl"]
    t0 = rows[0]["t"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    sg = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    dg = round(rows[hz[0]]["t"] - t0, 3) if hz else None
    hold = rec.get("e2_params", {}).get("hold_after_window_s")
    if hold is None:
        ho = rec.get("hold_override") or {}
        hold = ho.get("effective_s")
    ceilh = math.ceil(hold) if isinstance(hold, (int, float)) else None
    a = round(ht[0]["t"] - (rec["close_delivery"]["t"] - rec["closed_at_s"]), 3) if (ht and ceilh is not None) else None
    post = round(rec["closed_at_s"] - a - ceilh, 3) if (a is not None and ceilh is not None) else None
    # 闩→退：末行 − 首个 exitstate==1 行；对照数值末行
    if ones:
        l2e_last = round(rows[-1]["t"] - rows[ones[0]]["t"], 3)
        num = [i for i, x in enumerate(rows) if isinstance(x.get("exitstate"), int)]
        l2e_num = round(rows[num[-1]]["t"] - rows[ones[0]]["t"], 3)
    else:
        l2e_last = l2e_num = None
    latch = len(ones) > 0
    cs = rec["closed_at_s"]
    _fmt = lambda v: ("%.3f" % v) if isinstance(v, float) else str(v)
    print(hdr.format(tag, _fmt(cs), _fmt(dg), _fmt(prevd), len(ones), "Y" if latch else "N",
                     rows[-1]["wait"], _fmt(l2e_last), _fmt(hold), _fmt(ceilh), len(ht),
                     f"{a}/{post}" if a is not None else "-"))
    pts.append(dict(tag=tag, close=rec["closed_at_s"], d=dg, n1=len(ones), latch=latch,
                    l2e_last=l2e_last, l2e_num=l2e_num, hold=hold, ceil=ceilh, nread=len(ht),
                    a=a, post=post, hz0=hz[0] if hz else None, sg0=sg[0] if sg else None,
                    src=src, exited=rec.get("exited"), wait_last=rows[-1]["wait"]))

print("\n== (A) Δ 二分轴 n=14 族内零例外检验 ==")
valid = [p for p in pts if p["d"] is not None]
lat = [p for p in valid if p["latch"]]
nol = [p for p in valid if not p["latch"]]
print(f"  n={len(valid)}  闩族={len(lat)}  不闩族={len(nol)}")
print("  闩族 Δ:", [(p["tag"], p["d"]) for p in lat])
print("  不闩族 Δ:", [(p["tag"], p["d"]) for p in nol])
lmax = max(p["d"] for p in lat); nmin = min(p["d"] for p in nol)
gray = [p["tag"] for p in valid if 0.15 <= p["d"] <= 0.35]
print(f"  闩侧 max Δ={lmax:.3f}  不闩侧 min Δ={nmin:.3f}  ⇒ 判据 Δ<0.15⇒闩 ∧ Δ>0.35⇒不闩 零例外? "
      f"{lmax < 0.15 and nmin > 0.35}   灰区点数={len(gray)} {gray}")
bad = [(p["tag"], p["n1"], json.load(open(f"{CB}/{d}/_rec.json", encoding='utf-8')).get("latch_detected", "<no-key>"))
       for p, (tag, d, _pd, _s) in zip(pts, TRIPS)]
mis = [(t, n1, ld) for (t, n1, ld) in bad if ld != "<no-key>" and bool(n1) != bool(ld)]
nokey = [(t, n1, ld) for (t, n1, ld) in bad if ld == "<no-key>"]
print(f"  原始行 exitstate==1 计数 vs latch_detected 字段 不符趟: {mis if mis else '无'}")
print(f"  旧 schema 无 latch_detected 键趟: {nokey if nokey else '无'}")
same = [(p["tag"], p["hz0"], p["sg0"]) for p in valid if p["hz0"] != p["sg0"]]
print(f"  hwnd/singleton 同行归零 不符趟: {same if same else '无（14/14 同行）'}")

print("\n== (B) 闩→退（末行口径，族内先例 _xv_s01:97）全量带 ==")
for p in lat:
    print(f"  {p['tag']:<15} rows[-1].wait={p['wait_last']} exited={p['exited']} "
          f"闩→退(末行)={p['l2e_last']}  闩→退(数值末行)={p['l2e_num']}")
vals = [p["l2e_last"] for p in lat if p["l2e_last"] is not None]
print(f"  带 = [{min(vals):.3f}, {max(vals):.3f}]  n={len(vals)}（§485 主张 2.003 新下沿；既往带 2.004~2.108）")

print("\n== (C) 量化律 n=14：closed = a + ceil(hold) + post ==")
lawok = [p for p in pts if p["a"] is not None]
print(f"  n读==ceil(hold) 趟数: {sum(1 for p in lawok if p['nread']==p['ceil'])}/{len(lawok)}")
for p in lawok:
    resid = round(p["close"] - (p["a"] + p["ceil"] + p["post"]), 3)
    assert resid == 0.0, (p["tag"], resid)
aa = [p["a"] for p in lawok if p["a"] is not None]
pp = [p["post"] for p in lawok]
print(f"  a ∈ [{min(aa):.3f}, {max(aa):.3f}]   post ∈ [{min(pp):.3f}, {max(pp):.3f}]   (n=14 全带)")
old_aa = [p["a"] for p in lawok if p["src"] == "§481"]
old_pp = [p["post"] for p in lawok if p["src"] == "§481"]
print(f"  n=13 旧带: a ∈ [{min(old_aa):.3f}, {max(old_aa):.3f}]  post ∈ [{min(old_pp):.3f}, {max(old_pp):.3f}]")
p2c = next(p for p in pts if p["tag"] == "2C-h14.0")
print(f"  本趟 2C: a={p2c['a']} post={p2c['post']}  a+post={round(p2c['a']+p2c['post'],3)} "
      f"∈ [0.996,1.289]? {0.996 <= p2c['a']+p2c['post'] <= 1.289}")
print(f"  注：§485 写 post∈[0.373,0.644]——核对 n=13 旧带与 n=14 新带是否一致（若 2C post 在带内则为旧带转录）")

print("\n== (D) 边界收窄重算：闩族 max closed vs 不闩族 min closed ==")
lc = max(p["close"] for p in lat if isinstance(p["close"], (int, float)))
nc = min(p["close"] for p in nol if isinstance(p["close"], (int, float)))
print(f"  闩族 max closed={lc}（{[p['tag'] for p in lat if p['close']==lc]}）  不闩族 min closed={nc}"
      f"（{[p['tag'] for p in nol if p['close']==nc]}）  ← 注意：不闩族含 closed=7.558/7.164 等早窗小 hold 趟，")
print("   故该 min 非 §485 边界下界来源；§485 边界是 hold≈15 档族内比较（见下行限定）")
sub = [p for p in nol if isinstance(p['close'],(int,float)) and p['close'] > 14]
print(f"  不闩族中 closed>14 的点: {[(p['tag'],p['close']) for p in sub]} ⇒ min={min(p['close'] for p in sub)}")
subl = [p for p in lat if isinstance(p['close'],(int,float)) and p['close']>14]
print(f"  闩族中 closed>14 的点: {[(p['tag'],p['close']) for p in subl]} ⇒ max={max(p['close'] for p in subl)}")
print(f"  ⇒ 边界（closed 轴）∈ ({lc}, {nc}]；§485 主张 (15.194,16.272]")
