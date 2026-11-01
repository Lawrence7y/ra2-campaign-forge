#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p15：
   (A) 由 p10 分解导出协议常量律 closed ≈ a + ceil(hold) + post，检验 8 趟是否全落在该律内；
   (B) 据此评估 §481「用 hold≈14.6~14.9 补偿」这一操作建议的可行性（hold 旋钮是否连续）；
   (C) 不闩族 Δ 与 close 的 Spearman 秩相关 + 隐含边界（close+Δ）的会话内散差（检验「窄带」锐度）。
"""
import json, io, sys, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
D = [("E5h10", "20261030T072242_9001_P3e_E12_T1", "A"), ("E5h15", "20261030T072353_9001_P3e_E12_T1", "A"),
     ("E5h20", "20261030T072630_9001_P3e_E12_T1", "A"), ("hold13", "20261030T211741_9001_P3e_E12_T1", "B"),
     ("hold14", "20261030T212148_9001_P3e_E12_T1", "B"), ("hold15", "20261030T212233_9001_P3e_E12_T1", "B"),
     ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1", "C"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1", "C")]
tab = []
for tag, d, s in D:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))
    ht, hold = tl["hold_tl"], r["e2_params"]["hold_after_window_s"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    a = ht[0]["t"] - t0
    closed = r["closed_at_s"]
    post = closed - a - math.ceil(hold)
    tab.append(dict(tag=tag, s=s, hold=hold, n=len(ht), ceil=math.ceil(hold), a=a, post=post,
                   closed=closed, oh=closed - hold))
print("== (A) 律：closed = a(启动→hold 首读) + ceil(hold)(1Hz 量化) + post(循环退出→取 closed_at) ==")
print("{:<9} {:>3} {:>6} {:>5} {:>5} {:>7} {:>7} {:>8} {:>11}".format(
      "trip", "会话", "hold", "n读", "ceil", "a", "post", "closed", "a+ceil+post"))
for x in tab:
    print("{:<9} {:>3} {:>6} {:>5} {:>5} {:>7.3f} {:>7.3f} {:>8.3f} {:>11.3f}".format(
        x["tag"], x["s"], x["hold"], x["n"], x["ceil"], x["a"], x["post"], x["closed"],
        x["a"] + x["ceil"] + x["post"]))
amin, amax = min(x["a"] for x in tab), max(x["a"] for x in tab)
pmin, pmax = min(x["post"] for x in tab), max(x["post"] for x in tab)
print(f"  ⇒ n读 == ceil(hold) 于 {sum(1 for x in tab if x['n'] == x['ceil'])}/{len(tab)} 趟成立（1 Hz 量化直接物证）")
print(f"  a ∈ [{amin:.3f}, {amax:.3f}]  post ∈ [{pmin:.3f}, {pmax:.3f}]")
print(f"  会话 C post = {[round(x['post'],3) for x in tab if x['s']=='C']} ; 会话 A/B post = "
      f"{[round(x['post'],3) for x in tab if x['s'] in ('A','B')]}")
print(f"  量化项 ceil(hold)−hold：C 批 {[round(x['ceil']-x['hold'],3) for x in tab if x['s']=='C']} ; "
      f"A/B 批 {[round(x['ceil']-x['hold'],3) for x in tab if x['s'] in ('A','B')]}")
newC = [x for x in tab if x["s"] == "C"]
oldAB = [x for x in tab if x["s"] in ("A", "B")]
resid = [round(x["oh"] - (x["ceil"] - x["hold"]), 3) for x in newC]
ores = [round(x["oh"], 3) for x in oldAB]
print(f"  扣除量化项后的 C 批残差 = {resid}  vs A/B 批残差区间 [{min(ores):.3f}, {max(ores):.3f}] ⇒ 残差落入旧区间? "
      f"{min(ores) <= min(resid) and max(resid) <= max(ores)}")

print("\n== (B) §481 建议复算：『用 hold≈14.6~14.9 补偿』 ==")
for h in (13.5, 14.0, 14.1, 14.6, 14.9, 15.0, 15.3, 15.8):
    c = math.ceil(h)
    lo, hi = amin + c + pmin, amax + c + pmax
    print(f"  hold={h:<5} ceil={c:<3} ⇒ 预测 closed ∈ [{lo:.3f}, {hi:.3f}]  目标 (14.997,16.272] ⇒ "
          f"{'可能落入' if lo <= 16.272 and hi > 14.997 else '区间外'}")
print(f"  ⇒ 旋钮被 ceil(hold) 量化：h∈(14,15] 全部映射到同一 closed 带 [{amin+15+pmin:.3f}, {amax+15+pmax:.3f}]，"
      f"带内调小数不产生两个不同样本点")
print(f"  h∈(14,15] 带下沿 {amin+15+pmin:.3f} 是否已 > 目标上界 16.272? {amin+15+pmin > 16.272}"
      f" ⇒ 若是，则 h=15.3/15.8 落区间外是该量化带的**必然**，与'会话'无关")
print(f"  跨 ceil 档取两点：h∈(13,14] ⇒ closed [{amin+14+pmin:.3f}, {amax+14+pmax:.3f}]；"
      f"h∈(14,15] ⇒ [{amin+15+pmin:.3f}, {amax+15+pmax:.3f}]")


print("\n== (C) 不闩族：Δ 与 close 的秩相关；隐含边界（= closed+Δ）散差 ==")
NOL = [("E5h15", "20261030T072353_9001_P3e_E12_T1", "A"), ("E5h20", "20261030T072630_9001_P3e_E12_T1", "A"),
       ("hold15", "20261030T212233_9001_P3e_E12_T1", "B"), ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1", "C"),
       ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1", "C")]
pts = []
for tag, d, s in NOL:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    hz = next(i for i, x in enumerate(rows) if x.get("hwnd") == 0)
    absz = round(rows[hz]["t"] - t0, 3)          # hwnd 归零（自启动）
    dl = round(rows[hz]["t"] - r["close_delivery"]["t"], 3)   # Δ = 归零行时刻 − 关窗投递时刻
    dl_alt = round(absz - r["closed_at_s"], 3)                 # 交叉口径：归零绝对 − closed_at_s(舍入值)
    assert abs(dl - dl_alt) <= 0.001, (tag, dl, dl_alt)
    pts.append((tag, s, round(r["closed_at_s"], 3), dl, absz))
print("{:<10} {:>3} {:>9} {:>8} {:>10}".format("trip", "会话", "close", "Δ", "归零绝对(=隐含边界)"))
for t, s, c, dl, b in pts:
    print("{:<10} {:>3} {:>9.3f} {:>8.3f} {:>10.3f}".format(t, s, c, dl, b))
def ranks(vals, reverse=False):
    order = sorted(range(len(vals)), key=lambda i: -vals[i] if reverse else vals[i])
    rk = [0] * len(vals)
    for rank, i in enumerate(order):
        rk[i] = rank + 1
    return rk
cl = [p[2] for p in pts]; dd = [p[3] for p in pts]
rc, rd = ranks(cl), ranks(dd)
n = len(pts); d2 = sum((a_ - b_) ** 2 for a_, b_ in zip(rc, rd))
rho = 1 - 6 * d2 / (n * (n * n - 1))
print(f"  Spearman ρ(close, Δ) = {rho:+.3f}（n={n}）⇒ {'严格单调下降（close 越大 Δ 越小）' if rho == -1 else ('严格单调上升' if rho == 1 else '非严格单调')}")
for s in ("A", "B", "C"):
    bb = [p[4] for p in pts if p[1] == s]
    if bb:
        print(f"  会话 {s} 归零绝对（隐含边界）= {[round(v,3) for v in bb]} 会话内散差 = {round(max(bb)-min(bb),3)} s")
allb = [p[4] for p in pts]
print(f"  5 点归零绝对 ∈ [{min(allb):.3f}, {max(allb):.3f}] 跨度 {round(max(allb)-min(allb),3)} s；"
      f"close 跨度 {round(max(cl)-min(cl),3)} s ⇒ §481『close 跨 1.1s / 归零跨 ~1.1s』两条数值各自复算：")
print(f"    close 全 5 点跨度 = {round(max(cl)-min(cl),3)}（含 E5h20=21.249）；"
      f"排除 E5h20 后 4 点 = {round(max(p[2] for p in pts if p[0] != 'E5h20') - min(p[2] for p in pts if p[0] != 'E5h20'),3)}")
print(f"    归零绝对 全 5 点跨度 = {round(max(allb)-min(allb),3)}；排除 E5h20 后 4 点 = "
      f"{round(max(p[4] for p in pts if p[0] != 'E5h20') - min(p[4] for p in pts if p[0] != 'E5h20'),3)}")

