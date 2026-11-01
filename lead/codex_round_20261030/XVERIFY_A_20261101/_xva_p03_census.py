#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XVERIFY_A_20261101 探针 p03：与 §502 普查 tee 逐窗对照 + 停滞时长偏差界 + §500 切换点验证。
只读，零写盘（stdout）。census tee 解析失败时逐行报错，不静默。
"""
import json, io, sys, os, re, statistics, math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
CENSUS = os.path.join(ROOT, "lead", "codex_round_20261030", "LEADER_battle",
                      "stall_census_20261101.txt")
T_STALL = 0.1

TRIPS = [
    ("l3_1101v3a", [0, 1, 2]), ("l3_1101v3b", [0, 1, 2]),
    ("l3_20261031ha", [0]), ("l3_20261031hb", [0, 1, 2]),
    ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
    ("l1c_20261021", [0, 1, 2]), ("l1a_20261020", [0, 1, 2]),
    ("t55k_20261020", [0, 1, 2]), ("l1_20261023e4", [0, 1, 2]),
]

# ---- 解析 census tee ----
census = {}
pat = re.compile(r"^(\S+)\s+w(\d+)\s+(.*)$")
for ln in open(CENSUS, encoding="utf-8"):
    ln = ln.rstrip("\n")
    m = pat.match(ln)
    if not m:
        continue
    trip, w, rest = m.group(1), int(m.group(2)), m.group(3)
    if trip not in [t for t, _ in TRIPS]:
        continue
    mu = re.search(r"units0=(\d+)", rest)
    ms = re.search(r"停滞段=(\d+)", rest)
    mo = re.search(r"占比=\s*([\d.]+)%", rest)
    if mu and ms and mo:
        census[(trip, w)] = {"units0": int(mu.group(1)), "segs": int(ms.group(1)),
                             "occ": float(mo.group(1))}
    else:
        census[(trip, w)] = {"raw": rest}

print("== A. 与 §502 census 逐窗对照（segs=interior 停滞段数; occ_i=普查口径; occ_a=全覆盖口径）")
print("   %-16s %s | %-14s | %s" % ("窗", "census(段/占比%)", "复算(段/occ_i%)", "occ_a% / Δocc_a-census"))
n_match = 0
n_minor = 0
n_subst = []
for trip, wins in TRIPS:
    for w in wins:
        p = os.path.join(BASE, trip, "measure_w%d.json" % w)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        ts = d["samples"]["t"]; fs = d["samples"]["f"]
        n = len(ts)
        trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
        gaps = [(a, b, fa) for (fa, a), (fb, b) in zip(trans, trans[1:]) if b - a > T_STALL]
        head = trans[0][1] - ts[0] if trans else ts[-1] - ts[0]
        tail = ts[-1] - trans[-1][1] if trans else 0.0
        n_int = len(gaps)
        sum_i = sum(b - a for a, b, fa in gaps)
        sum_all = sum_i + (head if head > T_STALL else 0.0) + (tail if tail > T_STALL else 0.0)
        es = trans[-1][1] - trans[0][1] if len(trans) >= 2 else 0.0
        occ_i = 100.0 * sum_i / es if es > 0 else None
        occ_a = 100.0 * sum_all / (ts[-1] - ts[0])
        c = census.get((trip, w), {})
        cs = c.get("segs"); co = c.get("occ")
        d_occ = (occ_a - co) if (occ_a is not None and co is not None) else None
        verdict = ""
        if cs is not None and occ_i is not None:
            if d_occ is not None and abs(d_occ) > 5.0:
                verdict = "实质分歧(口径外冻结)"
                n_subst.append((trip, w, cs, co, n_int, occ_i, occ_a))
            elif cs == n_int and abs(co - occ_i) <= 0.15:
                verdict = "一致"
                n_match += 1
            elif abs((occ_i or 0) - co) <= 1.0 and cs == n_int:
                verdict = "小数级差"
                n_minor += 1
            else:
                verdict = "实质分歧"
                n_subst.append((trip, w, cs, co, n_int, occ_i, occ_a))
        else:
            verdict = "census无数字(帧沿不足类) -> 复算: %d段 occ_a=%.1f%%" % (n_int, occ_a)
            n_subst.append((trip, w, cs, co, n_int, occ_i, occ_a))
        print("   %-16s w%-2d %s | int=%d occ_i=%s | occ_a=%.2f Δ=%s  %s" % (
            trip, w, ("%d/%.1f%%" % (cs, co)) if cs is not None else repr(c.get("raw", ""))[:28],
            n_int, ("%.2f" % occ_i) if occ_i is not None else "None",
            occ_a, ("%.2f" % d_occ) if d_occ is not None else "?", verdict))
print("   一致=%d 小数级差=%d 实质分歧/无数字=%d" % (n_match, n_minor, len(n_subst)))
print("   实质分歧明细: %s" % ([(t, "w%d" % w) for t, w, *_ in n_subst],))

print()
print("== B. 停滞时长偏差界：>10ms 且洞内含帧推进的洞，且该洞落在 >0.1s 停滞间隙内（停滞时长上界偏差）")
for trip, wins in TRIPS:
    for w in wins:
        p = os.path.join(BASE, trip, "measure_w%d.json" % w)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        ts = d["samples"]["t"]; fs = d["samples"]["f"]
        n = len(ts)
        trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
        gaps = [(a, b) for (fa, a), (fb, b) in zip(trans, trans[1:]) if b - a > T_STALL]
        adv_hole = 0.0
        adv_n = 0
        for i in range(n - 1):
            if ts[i + 1] - ts[i] > 0.010 and fs[i + 1] > fs[i]:
                for a, b in gaps:
                    if a <= ts[i] and ts[i + 1] <= b:
                        adv_n += 1
                        adv_hole += ts[i + 1] - ts[i]
                        break
        if adv_n:
            print("   %s w%d: 停滞间隙内洞推进=%d 洞长合计=%.3fs" % (
                trip, w, adv_n, adv_hole))

print()
print("== C. §500 切换点验证（首个持续>=50%秒 + 持续滞态退出秒 -> 帧号）")
def frame_at(ts, fs, t):
    # t 为窗内相对秒；返回该时刻的 f（最后 seen 值）
    lo, hi = 0, len(ts) - 1
    if t <= ts[0] - ts[0]:
        return fs[0]
    tt = ts[0] + t
    if tt >= ts[-1]:
        return fs[-1]
    import bisect
    i = bisect.bisect_right(ts, tt) - 1
    return fs[i]

def switch_pts(trip, w):
    p = os.path.join(BASE, trip, "measure_w%d.json" % w)
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    ts = d["samples"]["t"]; fs = d["samples"]["f"]
    n = len(ts)
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    segs = []
    if len(trans) >= 2:
        for (fa, a), (fb, b) in zip(trans, trans[1:]):
            if b - a > T_STALL:
                segs.append((a, b))
    nb = int(math.ceil(ts[-1] - ts[0] - 1e-9))
    frozen = [0.0] * nb
    t0 = ts[0]
    for a, b in segs:
        for k in range(int(a - t0), min(int(b - t0), nb - 1) + 1):
            lo = max(a, t0 + k); hi = min(b, t0 + k + 1)
            if hi > lo:
                frozen[k] += hi - lo
    pct = [100.0 * frozen[k] / min(1.0, ts[-1] - t0 - k) for k in range(nb)]
    first_high = None
    for k in range(nb):
        if pct[k] >= 50 and all(x >= 50 for x in pct[k:k + 3]):
            first_high = k
            break
    exit_sec = None
    if first_high is not None:
        run = False
        for k in range(first_high, nb):
            if pct[k] < 50:
                if all(x < 50 for x in pct[k:k + 2]):
                    exit_sec = k
                    break
    tsw = frame_at(ts, fs, float(first_high)) if first_high is not None else None
    tex = frame_at(ts, fs, float(exit_sec)) if exit_sec is not None else None
    # 切换秒内的首个停滞段（帧定位）
    first_stall = None
    if first_high is not None:
        for a, b, fa in gaps:
            if a - ts[0] >= first_high and a - ts[0] < first_high + 1:
                first_stall = (fa, round(a - ts[0], 3))
                break
    print("   %s w%d: 首个持续滞态秒=%s (该秒末帧≈%s 切换秒内首停滞段=%s) 退出秒=%s (帧≈%s)" % (
        trip, w, first_high, tsw, first_stall, exit_sec, tex))
    print("      逐秒=%s" % " ".join(str(int(x)) for x in pct))

switch_pts("l3_1101v3b", 1)   # §500: 切换@frame≈940-990
switch_pts("l3_1101v3b", 2)   # §500: 混合振荡
switch_pts("l3_20261031hb", 2)  # §500: 退出@frame≈840-870
switch_pts("l3_1101v3a", 1)   # §500: 末秒 35%
