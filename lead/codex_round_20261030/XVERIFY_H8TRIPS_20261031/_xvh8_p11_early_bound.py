#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p11：早相整体域（0..991）可行性界 + units 反推自洽（同一 spawn 假设）+ hb 全段实测。

(1) hb/ha：从 nav_end 到末窗末沿的墙钟与帧程 = 本批早相整体平均 fps 实测；
(2) q/r：把帧域 0..991（本批 hb 的全部早相）设为 x fps，余下帧按族内上限 V = 解 x 下界；
(3) units 反推：用各趟自身 delta_u/delta_f 线性外推到 frame 0，检验 q/r 与 ha/hb 是否同一 spawn 满员态。
只读。
"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def win(trip, w):
    return json.load(open(ROOT + "/" + trip + "/measure_w" + str(w) + ".json", encoding="utf-8"))

def edges_of(m):
    return [(int(f), t) for f, t in (m.get("frame_edges") or [])]

def t2f(E, t):
    if t <= E[0][1]:
        return E[0][0]
    for (fa, ta), (fb, tb) in zip(E, E[1:]):
        if ta <= t <= tb:
            return fb if tb == ta else fa + (fb - fa) * (t - ta) / (tb - ta)
    return E[-1][0]

def fields(trip):
    return json.load(open(ROOT + "/" + trip + "/qc151_fields.json", encoding="utf-8"))

def gv(f, g, k):
    v = [e["value"] for e in f if e.get("group") == g and e.get("key") == k]
    return v[-1] if v else None

print("=" * 78)
print("(1) 本批早相整体实测（nav_end 到末窗末沿，同一 perf_counter 轴）")
print("=" * 78)
hb = fields("l3_20261031hb")
net_hb = gv(hb, "NAV", "h7_nav_end_t")
last_t = f_last = None
for w in (0, 1, 2):
    E = edges_of(win("l3_20261031hb", w))
    last_t, f_last = E[-1][1], E[-1][0]
    print("  hb w%d: 末沿 frame=%s t=%.3f" % (w, f_last, last_t))
W_hb = round(last_t - net_hb, 3)
hb_avg = f_last / W_hb
print("  => hb 早相 0..%d 帧用墙钟 %.3f s => 平均 %.2f fps（其中 H8 等待段 0..400 用 94.676 s = %.2f fps）"
      % (f_last, W_hb, hb_avg, 400 / 94.676))
Ea = edges_of(win("l3_20261031ha", 0))
net_ha = gv(fields("l3_20261031ha"), "NAV", "h7_nav_end_t")
print("  ha: nav_end=%.3f w0 末沿 frame=%d t=%.3f => 0..%d 用 %.3f s = %.2f fps"
      % (net_ha, Ea[-1][0], Ea[-1][1], Ea[-1][0], Ea[-1][1] - net_ha, Ea[-1][0] / (Ea[-1][1] - net_ha)))

print("\n" + "=" * 78)
print("(2) q/r：帧域 0..991 以 x fps，余下按族内上限 V => x 下界")
print("=" * 78)
SEG = 991
for d in ("l3_20261023q", "l3_20261023r"):
    m = win(d, 0)
    net = gv(fields(d), "NAV", "h7_nav_end_t")
    F0, T0 = m["samples"]["f"][0], m["samples"]["t"][0]
    W = round(T0 - net, 3)
    rest = F0 - SEG
    print("\n  %s: W(battle->w0)=%.3f s, f0=%d, 余下 %d 帧（%d..%d）按 V：" % (d, W, F0, rest, SEG, F0))
    for V in (31.4, 32.0, 40.0):
        rem_t = W - rest / V
        x = SEG / rem_t if rem_t > 0 else float("inf")
        print("      V=%-5.1f => 早相 0..%d 可用 %7.2f s => x >= %5.2f fps"
              "（本批 hb 同域实测 %.2f fps => 需快 %.1f 倍）" % (V, SEG, rem_t, x, hb_avg, x / hb_avg))

print("\n" + "=" * 78)
print("(3) units 线性反推到 frame 0（同一 spawn 满员态检验）")
print("=" * 78)
for d, ws in (("l3_20261023q", (0, 1)), ("l3_20261023r", (0, 1)),
              ("l3_20261031hb", (0, 1, 2)), ("l3_20261021", (0, 1, 2))):
    pts = []
    for w in ws:
        m = win(d, w)
        E = edges_of(m)
        base = E[0][1]
        for c in m["counters"]:
            if c.get("units") is not None:
                pts.append((t2f(E, base + c["t_rel"]), c["units"]))
    (fa, ua), (fb, ub) = pts[0], pts[-1]
    rate = (ub - ua) / (fb - fa)
    print("  %s: 观测域 frame %d..%d units %d..%d 速率 %+.4f u/帧 => 线性反推 frame0 ~= %.1f"
          % (d, round(fa), round(fb), ua, ub, rate, ua - rate * fa))
print("  参照：hb P2 frozen_final@frame0 houses=[480,480,240,240] 和=1440（p05 §(D)）；"
      "counters.units 首行 ha/hb=1342/1341。速率非严格线性（早期衰减 => 反推为下界估计）。")
