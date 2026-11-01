#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XVERIFY_A_20261101 探针 p01：停滞判据独立复算。
只读趟目录；本探针零写盘，输出走 stdout（落盘由 shell 重定向完成）。
判据：T_STALL=0.1s；帧冻结段=相邻帧沿(f值变化点)间隔>0.1s，方向不论。
三类冻结段：head(窗首样本→首个帧沿) / interior(相邻帧沿间) / tail(末帧沿→窗末样本)。
双占比口径：
  occ_interior = interior合计 / (末帧沿t-首帧沿t)   ← §502 普查复算口径
  occ_all      = (head+interior+tail)合计 / (末样本t-首样本t) ← 全覆盖口径
分类规则（互斥按序）：R0 读失败主导(err含ReadProcessMemory失败 或 覆盖率<80%)
  R1 无推进(上行帧沿=0) / R2 加载期(覆盖段max(f)<10) /
  R3 终局期(units_final<=max(100,0.15*units0)) / R4 活动战斗期(其余，
  按occ_all细分 快态<2% 混合2-25% 滞态>=25%)；修饰标记：采样缺口主导(>10ms缺口合计>50%span)。
"""
import json, io, sys, os, math, statistics
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
T_STALL = 0.1

TRIPS = [
    ("l3_1101v3a", [0, 1, 2]), ("l3_1101v3b", [0, 1, 2]),
    ("l3_20261031ha", [0]), ("l3_20261031hb", [0, 1, 2]),
    ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
    ("l1c_20261021", [0, 1, 2]), ("l1a_20261020", [0, 1, 2]),
    ("t55k_20261020", [0, 1, 2]), ("l1_20261023e4", [0, 1, 2]),
]

def pctl(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    i = q * (len(s) - 1)
    lo = math.floor(i)
    hi = math.ceil(i)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (i - lo)

def units_at(counters, t_rel):
    pts = []
    for c in counters:
        if c.get("units") is not None and c.get("t_rel") is not None:
            pts.append((c["t_rel"], c["units"]))
    if not pts:
        return None
    if t_rel <= pts[0][0]:
        return pts[0][1]
    if t_rel >= pts[-1][0]:
        return pts[-1][1]
    for (t0, u0), (t1, u1) in zip(pts, pts[1:]):
        if t0 <= t_rel <= t1:
            if t1 == t0:
                return u0
            return u0 + (u1 - u0) * (t_rel - t0) / (t1 - t0)
    return pts[-1][1]

def classify(read_fail, coverage, n_adv_up, f_max_cov, u0, uN, occ_all_pct, gap10_pct):
    if read_fail or (coverage is not None and coverage < 0.80):
        cat = "读失败主导"
    elif n_adv_up == 0:
        cat = "无推进"
    elif f_max_cov < 10:
        cat = "加载期"
    elif uN is not None and u0 and uN <= max(100, 0.15 * u0):
        cat = "终局期"
    else:
        cat = "活动战斗期"
    sub = ""
    if cat == "活动战斗期":
        if occ_all_pct < 2:
            sub = "快态"
        elif occ_all_pct < 25:
            sub = "混合"
        else:
            sub = "滞态"
    tag = cat
    if gap10_pct is not None and gap10_pct > 50:
        tag = tag + "+采样缺口主导"
    return tag, sub

def run(mode):
    results = []
    txt = []
    for trip, wins in TRIPS:
        for w in wins:
            path = os.path.join(BASE, trip, "measure_w%d.json" % w)
            if not os.path.isfile(path):
                txt.append("!! 缺文件 %s w%d" % (trip, w))
                results.append({"trip": trip, "w": w, "missing": True})
                continue
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            ts = d["samples"]["t"]
            fs = d["samples"]["f"]
            n = len(ts)
            span_s = d.get("span_s")
            hz = d.get("hz")
            t_abs0 = d.get("t_abs0")
            err_text = d.get("error") or ""
            read_fail = "ReadProcessMemory" in err_text
            stats = d.get("stats") or {}
            span = ts[-1] - ts[0]
            nominal = None
            if span_s and hz:
                nominal = int(round(span_s * hz))
            coverage = None
            if nominal:
                coverage = n / nominal

            dts = []
            for i in range(n - 1):
                dts.append(ts[i + 1] - ts[i])
            g_norm = sum(g for g in dts if g <= 0.003)
            g_3_5 = sum(g for g in dts if 0.003 < g <= 0.005)
            g_5_10 = sum(g for g in dts if 0.005 < g <= 0.010)
            g_10_50 = sum(g for g in dts if 0.010 < g <= 0.050)
            g_50 = sum(g for g in dts if g > 0.050)
            n10 = 0
            for g in dts:
                if g > 0.010:
                    n10 += 1
            gap10_sum_pct = None
            if span:
                gap10_sum_pct = 100.0 * (g_10_50 + g_50) / span

            trans = []
            for i in range(1, n):
                if fs[i] != fs[i - 1]:
                    trans.append((fs[i], ts[i]))
            n_adv_up = 0
            n_adv_down = 0
            n_multi = 0
            for i in range(1, n):
                df = fs[i] - fs[i - 1]
                if df > 0:
                    n_adv_up += 1
                elif df < 0:
                    n_adv_down += 1
                if df > 1:
                    n_multi += 1
            fe = d.get("frame_edges") or []
            fe_ok = False
            if fe and trans:
                fe_ok = (len(fe) == len(trans) + 1 and fe[0][0] == fs[0]
                         and abs(fe[0][1] - ts[0]) < 1e-6
                         and fe[-1][0] == trans[-1][0]
                         and abs(fe[-1][1] - trans[-1][1]) < 1e-6)
            elif not fe and not trans:
                fe_ok = True

            segs = []
            if trans:
                head = trans[0][1] - ts[0]
                if head > T_STALL:
                    segs.append({"kind": "head", "t0": ts[0], "t1": trans[0][1],
                                 "dur": head, "frame": fs[0],
                                 "f_delta": trans[0][0] - fs[0]})
                for (fa, ta), (fb, tb) in zip(trans, trans[1:]):
                    if tb - ta > T_STALL:
                        segs.append({"kind": "interior", "t0": ta, "t1": tb,
                                     "dur": tb - ta, "frame": fa,
                                     "f_delta": fb - fa})
                tail = ts[-1] - trans[-1][1]
                if tail > T_STALL:
                    segs.append({"kind": "tail", "t0": trans[-1][1], "t1": ts[-1],
                                 "dur": tail, "frame": trans[-1][0],
                                 "f_delta": None})
            else:
                if span > T_STALL:
                    segs.append({"kind": "head", "t0": ts[0], "t1": ts[-1],
                                 "dur": span, "frame": fs[0], "f_delta": 0})
            segs_all = sorted(segs, key=lambda s: s["t0"])
            interior = []
            for s in segs_all:
                if s["kind"] == "interior":
                    interior.append(s)
            sum_interior = 0.0
            for s in interior:
                sum_interior += s["dur"]
            sum_all = 0.0
            for s in segs_all:
                sum_all += s["dur"]
            edges_span = 0.0
            if len(trans) >= 2:
                edges_span = trans[-1][1] - trans[0][1]
            occ_interior_pct = None
            if edges_span > 0:
                occ_interior_pct = 100.0 * sum_interior / edges_span
            occ_all_pct = None
            if span:
                occ_all_pct = 100.0 * sum_all / span
            f_max_cov = max(fs)
            f_min_cov = min(fs)

            starts = []
            for s in interior:
                starts.append(s["t0"])
            ivs = []
            for a, b in zip(starts, starts[1:]):
                ivs.append(b - a)
            iv_med = None; iv_q1 = None; iv_q3 = None; iv_cv = None
            if ivs:
                iv_med = statistics.median(ivs)
                iv_q1 = pctl(ivs, 0.25)
                iv_q3 = pctl(ivs, 0.75)
                m = statistics.mean(ivs)
                if m > 0:
                    iv_cv = statistics.pstdev(ivs) / m

            buckets = []
            if span > 0:
                nb = int(math.ceil(span - 1e-9))
                frozen = [0.0] * nb
                for s in segs_all:
                    i0 = int((s["t0"] - ts[0]) // 1)
                    i1 = int((s["t1"] - ts[0]) // 1)
                    for k in range(max(i0, 0), min(i1, nb - 1) + 1):
                        lo = max(s["t0"], ts[0] + k)
                        hi = min(s["t1"], ts[0] + k + 1)
                        if hi > lo:
                            frozen[k] += hi - lo
                for k in range(nb):
                    buckets.append(100.0 * frozen[k] / min(1.0, span - k))

            counters = d.get("counters") or []
            u0 = None
            uN = None
            if counters:
                u0 = counters[0].get("units")
                for c in reversed(counters):
                    if c.get("units") is not None:
                        uN = c["units"]
                        break
            gate = d.get("gate") or {}

            top_rows = []
            for s in sorted(segs_all, key=lambda s: -s["dur"])[:4]:
                top_rows.append({"dur": round(s["dur"], 3), "frame": s["frame"],
                                 "units": units_at(counters, s["t0"] - ts[0]),
                                 "kind": s["kind"],
                                 "t_rel": round(s["t0"] - ts[0], 3)})

            occ_for_class = occ_all_pct
            if occ_for_class is None:
                occ_for_class = 0.0
            gap_for_class = gap10_sum_pct
            if gap_for_class is None:
                gap_for_class = 0.0
            cov_for_class = coverage
            if cov_for_class is None:
                cov_for_class = 1.0
            tag, sub = classify(read_fail, cov_for_class, n_adv_up, f_max_cov,
                                u0, uN, occ_for_class, gap_for_class)
            wall0 = "?"
            if t_abs0:
                wall0 = datetime.fromtimestamp(t_abs0 + ts[0]).strftime("%H:%M:%S.%f")[:-3]

            res = {
                "trip": trip, "w": w,
                "verdict": d.get("verdict"), "error": err_text,
                "span_s_meta": span_s, "hz_meta": hz, "t_abs0": t_abs0,
                "wall_start": wall0,
                "n_samples": n, "nominal_beats": nominal, "coverage": None,
                "read_fail": read_fail,
                "span": round(span, 4),
                "hz_eff": round((n - 1) / span, 1) if span else None,
                "beat_med_ms": round(statistics.median(dts) * 1000, 3) if dts else None,
                "beat_max_ms": round(max(dts) * 1000, 2) if dts else None,
                "n_beat_gt10ms": n10,
                "gap10_sum_pct": round(gap10_sum_pct, 2) if gap10_sum_pct is not None else None,
                "beat_class_pct": {
                    "le3": round(100 * g_norm / span, 2) if span else None,
                    "3_5": round(100 * g_3_5 / span, 2) if span else None,
                    "5_10": round(100 * g_5_10 / span, 2) if span else None,
                    "10_50": round(100 * g_10_50 / span, 2) if span else None,
                    "gt50": round(100 * g_50 / span, 2) if span else None},
                "f0": fs[0], "fN": fs[-1],
                "f_min_cov": f_min_cov, "f_max_cov": f_max_cov,
                "n_trans": len(trans),
                "n_adv_up": n_adv_up, "n_adv_down": n_adv_down, "n_multi": n_multi,
                "frame_edges_stored_n": len(fe), "frame_edges_match": bool(fe_ok),
                "n_stall_interior": len(interior),
                "n_stall_head": len([s for s in segs_all if s["kind"] == "head"]),
                "n_stall_tail": len([s for s in segs_all if s["kind"] == "tail"]),
                "sum_interior_s": round(sum_interior, 3),
                "sum_all_s": round(sum_all, 3),
                "edges_span": round(edges_span, 3),
                "occ_interior_pct": round(occ_interior_pct, 2) if occ_interior_pct is not None else None,
                "occ_all_pct": round(occ_all_pct, 2) if occ_all_pct is not None else None,
                "head_frozen_s": round(trans[0][1] - ts[0], 4) if trans else round(span, 4),
                "tail_frozen_s": round(ts[-1] - trans[-1][1], 4) if trans else 0.0,
                "stall_iv": {"n": len(ivs),
                             "med": round(iv_med, 4) if iv_med is not None else None,
                             "q1": round(iv_q1, 4) if iv_q1 is not None else None,
                             "q3": round(iv_q3, 4) if iv_q3 is not None else None,
                             "cv": round(iv_cv, 3) if iv_cv is not None else None,
                             "min": round(min(ivs), 4) if ivs else None,
                             "max": round(max(ivs), 4) if ivs else None},
                "per_sec_pct": [round(b) for b in buckets],
                "units0": u0, "units_final": uN, "gate": gate,
                "stats_cross": {"fps_avg": stats.get("fps_avg"),
                                "n_edges": stats.get("n_edges"),
                                "max_stall_s": stats.get("max_stall_s"),
                                "note": stats.get("note")},
                "top_stalls": top_rows,
                "class": tag, "sub": sub,
            }
            results.append(res)

            if mode == "txt":
                txt.append("== %s w%d [%s%s] verdict=%s 窗起=%s span_meta=%ss" % (
                    trip, w, tag, ("/" + sub) if sub else "", res["verdict"], wall0, span_s))
                txt.append("   样本 %d/%s 覆盖=%s 到拍: 中位=%sms 最大=%sms >10ms拍=%d 缺口/span=%s%%" % (
                    n, nominal, res["coverage"] if res["coverage"] is not None else
                    (round(cov_for_class, 4) if nominal else "?"),
                    res["beat_med_ms"], res["beat_max_ms"], n10,
                    res["gap10_sum_pct"]))
                txt.append("   f: %s->%s (min%d max%d) 帧沿: 变化=%d 上行=%d 下行=%d 多帧=%d 存储edges=%d 吻合=%s" % (
                    fs[0], fs[-1], f_min_cov, f_max_cov, len(trans), n_adv_up,
                    n_adv_down, n_multi, len(fe), fe_ok))
                txt.append("   冻结段: int=%d head=%d tail=%d 合计int=%.3fs 合计all=%.3fs" % (
                    len(interior), res["n_stall_head"], res["n_stall_tail"],
                    sum_interior, sum_all))
                txt.append("   占比: 普查口径=%s%% (int合计/边沿跨%.3fs) | 全覆盖=%s%% (all合计/样本跨%.3fs)" % (
                    res["occ_interior_pct"], edges_span, res["occ_all_pct"], span))
                txt.append("   head_frozen=%ss tail_frozen=%ss units %s->%s gate.pre_fps15=%s ok=%s" % (
                    res["head_frozen_s"], res["tail_frozen_s"], u0, uN,
                    gate.get("pre_fps15"), gate.get("ok")))
                if ivs:
                    txt.append("   起始间隔(n=%d): 中位=%.3f Q1=%.3f Q3=%.3f CV=%.2f min=%.3f max=%.3f" % (
                        len(ivs), iv_med, iv_q1, iv_q3, iv_cv, min(ivs), max(ivs)))
                if top_rows:
                    parts = []
                    for r in top_rows:
                        parts.append("%.3fs@f%s u%s(%s)" % (r["dur"], r["frame"], r["units"], r["kind"]))
                    txt.append("   top冻结: " + " | ".join(parts))
                txt.append("   逐秒%%: %s" % " ".join(str(x) for x in res["per_sec_pct"]))
                txt.append("   stats交叉: fps_avg=%s n_edges=%s max_stall=%s note=%r err=%r" % (
                    res["stats_cross"]["fps_avg"], res["stats_cross"]["n_edges"],
                    res["stats_cross"]["max_stall_s"], res["stats_cross"]["note"], err_text))
                txt.append("")

    if mode == "json":
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        for line in txt:
            print(line)
        print("[窗数=%d]" % len(results))

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "txt")
