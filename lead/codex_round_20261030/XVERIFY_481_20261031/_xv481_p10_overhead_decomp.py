#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p10：hold→closed 开销逐段分解（8 趟有 hold_after_window_s 键）。
   检验 §481「hold→closed 投递开销随会话漂移」的**归因**，对照另一解释：
   驱动 hold 循环 = `while now()-th < hold: 读数; sleep(1.0)`（_drive_c2_x_e12.py:429-434），
   故非整数 hold 会多睡一拍 ⇒ 循环退出时刻 ≈ th + (floor(hold) + (1 if frac>0 else 0))，与"会话"无关。
   口径：t0 = close_delivery.t − closed_at_s（驱动 :441-443）；th = timeline.hold_tl[0].t；tc = close_delivery.t。
"""
import json, io, sys, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
D = [("E5h10", "20261030T072242_9001_P3e_E12_T1", "会话A(10-29 BOOT)"),
     ("E5h15", "20261030T072353_9001_P3e_E12_T1", "会话A(10-29 BOOT)"),
     ("E5h20", "20261030T072630_9001_P3e_E12_T1", "会话A(10-29 BOOT)"),
     ("hold13", "20261030T211741_9001_P3e_E12_T1", "会话B(10-30 BOOT)"),
     ("hold14", "20261030T212148_9001_P3e_E12_T1", "会话B(10-30 BOOT)"),
     ("hold15", "20261030T212233_9001_P3e_E12_T1", "会话B(10-30 BOOT)"),
     ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1", "会话C(10-31 新BOOT)"),
     ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1", "会话C(10-31 新BOOT)")]
print("{:<9} {:<20} {:>5} {:>4} {:>7} {:>7} {:>8} {:>8} {:>9} {:>10} {:>10}".format(
      "trip", "会话", "hold", "n读", "th−t0", "退出−th", "退出理论", "tc−退出", "closed−hold", "模型预测", "残差"))
tab = []
for tag, d, sess in D:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))
    ht, hold = tl["hold_tl"], r["e2_params"]["hold_after_window_s"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    th, last = ht[0]["t"], ht[-1]["t"]
    tc = r["close_delivery"]["t"]
    frac = hold - math.floor(hold)
    pred = math.floor(hold) + (1.0 if frac > 1e-9 else 0.0)   # 循环退出（相对 th）的理论时刻
    a = th - t0
    loopspan = tc - th
    post = loopspan - pred                                    # 截图 + post_close + closed_at 取时
    oh = r["closed_at_s"] - hold
    model = a + (pred - hold) + post
    print("{:<9} {:<20} {:>5} {:>4} {:>7.3f} {:>7.3f} {:>8.1f} {:>8.3f} {:>9.3f} {:>10.3f} {:>10.6f}".format(
        tag, sess, hold, len(ht), a, loopspan, pred, post, oh, model, oh - model))
    tab.append(dict(tag=tag, sess=sess, hold=hold, n=len(ht), a=a, pred=pred, post=post, oh=oh,
                    frac=frac, loopspan=loopspan, overshoot=pred - hold))

print("\n== 分量分布（a=启动→hold 开始；overshoot=1Hz 量化多睡；post=截图+投递+取时）==")
for key, fmt in (("a", "启动→hold %.3f"), ("overshoot", "量化多睡 %.3f"), ("post", "截图+投递 %.3f"), ("oh", "closed−hold %.3f")):
    vals = [(x["tag"], x[key]) for x in tab]
    print(f"  {key:<10}: " + ", ".join(f"{t.split('-')[-1]}={v:.3f}" for t, v in vals))
print("\n  会话 A/B（6 点，hold 全为整数）closed−hold 区间 = [%.3f, %.3f]" % (
    min(x["oh"] for x in tab if x["sess"].startswith(("会话A", "会话B"))),
    max(x["oh"] for x in tab if x["sess"].startswith(("会话A", "会话B")))))
print("  会话 C（2 点，hold 非整数 15.3/15.8）closed−hold = [%.3f, %.3f]" % (
    min(x["oh"] for x in tab if x["sess"].startswith("会话C")),
    max(x["oh"] for x in tab if x["sess"].startswith("会话C"))))
print("  会话 C 量化项 pred−hold = [%.3f, %.3f] ⇒ 仅量化一项即解释 A/B→C 偏移的大部" % (
    min(x["overshoot"] for x in tab if x["sess"].startswith("会话C")),
    max(x["overshoot"] for x in tab if x["sess"].startswith("会话C"))))
print("\n  反证「随会话漂移」的同会话内证据：会话C 两点 hold 差 0.5s，closed−hold 反而**减小** "
      "%.3f→%.3f（差 %.3f），而量化预测差 = %.3f（1−0.3 −(1−0.8)）⇒ 方向与幅度由 frac(hold) 决定，非会话。" % (
      tab[6]["oh"], tab[7]["oh"], tab[7]["oh"] - tab[6]["oh"], (tab[6]["pred"] - tab[6]["hold"]) - (tab[7]["pred"] - tab[7]["hold"])))
print("\n  跨会话同 hold 值对照（会话A h15 vs 会话B h15）：closed−hold = %.3f vs %.3f ⇒ 真会话间残差 ≤ %.3f s" % (
    tab[1]["oh"], tab[5]["oh"], abs(tab[1]["oh"] - tab[5]["oh"])))
print("  （同 hold=15.0、同 a≈0.6、同量化=1.0 ⇒ 差异只落在 post 项）")
