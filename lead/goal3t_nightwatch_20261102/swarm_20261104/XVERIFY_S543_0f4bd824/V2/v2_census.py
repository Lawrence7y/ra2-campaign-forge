# -*- coding: utf-8 -*-
"""V2 独立复算：MEASURE_V1 窗分类 + fps 分档 + 冻结窗反证检查（纯 JSON，零图像）。

只读。写域仅 XVERIFY_S543_0f4bd824/V2/。零真机。
判据全部自己算，不引用 _leader_*.py 的结果。
"""
import glob
import json
import os
import sys

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2"

# 两种 glob：Leader 用的是 BASE/*/*.json（根目录 3 份被漏）
P_SUB = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
P_ROOT = sorted(glob.glob(os.path.join(BASE, "measure_w*.json")))


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        return {"__load_error__": repr(exc), "__path__": path}


def trace_stats(j):
    """从 500Hz 原样 samples 自己算，不信 stats 字段。"""
    s = j.get("samples") or {}
    ts, fs = s.get("t") or [], s.get("f") or []
    d = dict(n_samp_t=len(ts), n_samp_f=len(fs))
    if not fs:
        return d
    d["f_first"] = fs[0]
    d["f_last"] = fs[-1]
    d["f_distinct"] = len(set(fs))
    d["f_min"] = min(fs)
    d["f_max"] = max(fs)
    ups = downs = 0
    up_sum = down_sum = 0
    for i in range(1, len(fs)):
        delta = fs[i] - fs[i - 1]
        if delta > 0:
            ups += 1
            up_sum += delta
        elif delta < 0:
            downs += 1
            down_sum += -delta
    d["n_up_events"] = ups
    d["n_down_events"] = downs
    d["sum_up"] = up_sum
    d["sum_down"] = down_sum
    d["monotonic_nondecreasing"] = (downs == 0)
    # 自己算最长「帧号不变」时间跨度
    worst = 0.0
    run_start = ts[0] if ts else 0.0
    for i in range(1, len(fs)):
        if fs[i] == fs[i - 1]:
            if ts:
                worst = max(worst, ts[i] - run_start)
        else:
            run_start = ts[i] if ts else run_start
    d["max_stall_self"] = round(worst, 3)
    d["dur_self"] = round((ts[-1] - ts[0]), 3) if len(ts) > 1 else 0.0
    return d


def counters_check(j):
    c = j.get("counters") or []
    out = dict(n_c=len(c))
    if not c:
        return out
    for key in ("units", "infantry", "aircraft", "g", "b", "techno", "g_items", "b_items", "ws_kb", "pf_kb"):
        vals = [x.get(key) for x in c if isinstance(x, dict)]
        uniq = sorted({v for v in vals if v is not None})
        out[key + "_uniq"] = uniq if len(uniq) <= 3 else [uniq[0], "...", uniq[-1], len(uniq)]
        out[key + "_n_uniq"] = len(uniq)
    return out


rows = []
skipped = []
for path in P_SUB + P_ROOT:
    j = load(path)
    trip_dir = os.path.basename(os.path.dirname(path)) or "(ROOT)"
    if "__load_error__" in j:
        skipped.append((path, j["__load_error__"]))
        continue
    if os.path.dirname(path) == BASE:
        trip_dir = "(ROOT-LEVEL)"
    ed = j.get("frame_edges") or []
    rec = dict(
        path=path, dir=trip_dir, schema=j.get("schema"), trip_id=j.get("trip_id"),
        window=j.get("window"), span_s=j.get("span_s"), settle_s=j.get("settle_s"),
        t_abs0=j.get("t_abs0"), hz=j.get("hz"), verdict=j.get("verdict"), error=j.get("error"),
        n_edges=len(ed),
        edge_f0=(ed[0][0] if ed else None), edge_f1=(ed[-1][0] if ed else None),
        gate=j.get("gate"), map_sha=(j.get("map_sha256") or "")[:8],
        gamemd_sha=(j.get("gamemd_sha256") or "")[:8],
        stats=j.get("stats") or {},
    )
    rec.update(trace_stats(j))
    rec.update(counters_check(j))
    if not ed:
        skipped.append((path, "no frame_edges (samples.f len=%s)" % rec.get("n_samp_f")))
        continue
    rec["df_edge"] = rec["edge_f1"] - rec["edge_f0"]
    rec["df_sample"] = rec["f_last"] - rec["f_first"]
    rows.append(rec)


def cls(r):
    if r["df_edge"] > 0:
        return "ADV"
    if r["df_edge"] == 0:
        return "LOAD" if r["edge_f0"] == 0 else "FRZ"
    return "BACK"


for r in rows:
    r["class"] = cls(r)

print("=== 0. 文件盘点 ===")
print("glob BASE/*/measure_w*.json : %d 份（Leader 的口径）" % len(P_SUB))
print("glob BASE/measure_w*.json   : %d 份（根目录，Leader 的 glob 漏掉）" % len(P_ROOT))
print("参与分类的窗               : %d" % len(rows))
print("被排除                     : %d" % len(skipped))
for p, why in skipped:
    print("   SKIP %s  <- %s" % (p.replace(BASE + os.sep, ""), why))
print("趟数(按目录) = %d ; 趟数(按 json 内 trip_id) = %d"
      % (len({r["dir"] for r in rows}), len({r["trip_id"] for r in rows})))
print("schema 取值:", sorted({str(r["schema"]) for r in rows}))
print()

print("=== 1. 窗分类（我自己算）===")
for k in ("ADV", "FRZ", "LOAD", "BACK"):
    n = sum(1 for r in rows if r["class"] == k)
    print("  %-5s : %3d   %s" % (k, n, {"ADV": "df>0 有推进", "FRZ": "df==0 且 f0!=0",
                                        "LOAD": "df==0 且 f0==0 加载段", "BACK": "df<0 回退"}[k]))
print("  合计 : %d 窗" % len(rows))
print("  交叉校验：edge 口径 df 与 samples 口径 df 不一致的窗：" )
bad = [r for r in rows if r["df_edge"] != r["df_sample"]]
print("     %d 个" % len(bad))
for r in bad:
    print("     %s w%s edge df=%s samples df=%s f_distinct=%s" %
          (r["dir"], r["window"], r["df_edge"], r["df_sample"], r.get("f_distinct")))
nz = [r for r in rows if r.get("f_distinct", 1) > 1 and r["df_edge"] == 0]
print("  df==0 但窗内帧号其实变过（有升或有降）的窗：%d 个" % len(nz))
for r in nz:
    print("     %s w%s f_distinct=%s up=%s down=%s" % (r["dir"], r["window"], r["f_distinct"],
                                                       r.get("n_up_events"), r.get("n_down_events")))
print()

print("=== 2. 有推进窗（ADV）按 stats.fps_avg 分档 ===")
adv = [r for r in rows if r["class"] == "ADV"]
noavg = [r for r in adv if r["stats"].get("fps_avg") is None]
hi = [r for r in adv if (r["stats"].get("fps_avg") or 0) >= 28]
lo = [r for r in adv if r["stats"].get("fps_avg") is not None and r["stats"]["fps_avg"] < 28]
print("  ADV 总数=%d ; fps_avg>=28 : %d ; <28 : %d ; fps_avg 为 null : %d"
      % (len(adv), len(hi), len(lo), len(noavg)))
print("  [自算 df/span 口径] >=28 : %d ; <28 : %d" % (
    sum(1 for r in adv if r["span_s"] and (r["df_edge"] / r["span_s"]) >= 28),
    sum(1 for r in adv if r["span_s"] and (r["df_edge"] / r["span_s"]) < 28)))
print("  stats.fps_avg 与 df/span_s 最大偏差：%.3f" %
      max([abs((r["stats"].get("fps_avg") or 0) - (r["df_edge"] / (r["span_s"] or 1))) for r in adv]))
print()
print("  --- fps_avg<28 的窗（「目标①可用样本」候选）---")
print("  %-20s %3s %8s %8s %10s %10s %10s" % ("dir", "w", "fps_avg", "df", "span_s", "max_stall", "df/span"))
for r in sorted(lo, key=lambda x: x["stats"]["fps_avg"]):
    print("  %-20s %3s %8.3f %8d %10.3f %10.3f %10.3f" %
          (r["dir"], r["window"], r["stats"]["fps_avg"], r["df_edge"], r["span_s"] or 0,
           r["stats"].get("max_stall_s") or 0, r["df_edge"] / (r["span_s"] or 1)))
print()
print("  --- ADV 中 max_stall_s 很大（>=10s）的窗：名义「有推进」但整窗大部分时间停 ---")
for r in sorted(adv, key=lambda x: -(x["stats"].get("max_stall_s") or 0)):
    ms = r["stats"].get("max_stall_s") or 0
    if ms >= 10:
        print("     %-20s w%s fps_avg=%8.3f df=%5d max_stall=%7.3f span=%6.3f  stall/span=%.3f" %
              (r["dir"], r["window"], r["stats"].get("fps_avg") or -1, r["df_edge"], ms,
               r["span_s"] or 0, ms / (r["span_s"] or 1)))
print()

print("=== 3. 冻结窗（FRZ）全表 + 反证检查 ===")
frz = [r for r in rows if r["class"] == "FRZ"]
print("  %-20s %3s %6s %8s %9s %7s %8s %8s %9s %7s %s" %
      ("dir", "w", "f0", "pre_fps", "gate_ok", "logic", "maxstall", "span", "samp_n", "n_edges", "counters_const(units/g/b)"))
for r in sorted(frz, key=lambda x: (x["dir"], x["window"])):
    g = r["gate"] or {}
    st = r["stats"]
    cc = ("units=%s g=%s b=%s" %
          (r["units_n_uniq"], r.get("g_n_uniq"), r.get("b_n_uniq")))
    print("  %-20s %3s %6s %8.3f %9s %7s %8.3f %8.3f %9s %7s %s" %
          (r["dir"], r["window"], r["edge_f0"], g.get("pre_fps15") or -1, g.get("ok"),
           st.get("logic_frames"), st.get("max_stall_s") or 0, r["span_s"] or 0,
           r["n_samp_f"], r["n_edges"], cc))
print()
print("  --- 反证条件逐条统计 ---")
c1 = [r for r in frz if (r["gate"] or {}).get("pre_fps15", 0) >= 28 and r["stats"].get("logic_frames") == 0]
c1bad = [r for r in frz if r not in c1]
print("  A) pre_fps15>=28 且 logic_frames==0 : %d/%d 窗满足" % (len(c1), len(frz)))
for r in c1bad:
    print("     反例: %-20s w%s pre_fps15=%s ok=%s logic_frames=%s" %
          (r["dir"], r["window"], (r["gate"] or {}).get("pre_fps15"), (r["gate"] or {}).get("ok"),
           r["stats"].get("logic_frames")))
c2 = []
for r in frz:
    if r.get("units_n_uniq") == 1 and r.get("g_n_uniq") == 1 and r.get("b_n_uniq") == 1:
        c2.append(r)
print("  B) 冻结窗内 units/g/b 三者完全不变   : %d/%d 窗满足" % (len(c2), len(frz)))
for r in frz:
    if r not in c2:
        print("     反例: %-20s w%s units=%s g=%s b=%s techno=%s infantry=%s" %
              (r["dir"], r["window"], r.get("units_uniq"), r.get("g_uniq"), r.get("b_uniq"),
               r.get("techno_uniq"), r.get("infantry_uniq")))
c3 = []
for r in frz:
    ms = r["stats"].get("max_stall_s") or 0
    sp = r["span_s"] or 0
    if sp and abs(ms - sp) <= 0.05:
        c3.append(r)
print("  C) max_stall_s 与 span_s 差 <=0.05s  : %d/%d 窗满足" % (len(c3), len(frz)))
for r in frz:
    if r not in c3:
        print("     反例: %-20s w%s max_stall=%s span=%s 自算stall=%s" %
              (r["dir"], r["window"], r["stats"].get("max_stall_s"), r["span_s"], r.get("max_stall_self")))
c4 = [r for r in frz if r["n_samp_f"] >= 0.95 * 500 * (r["span_s"] or 25)]
print("  D) 采样点数 >= 95%% 的 span*500Hz（采样未提前结束）: %d/%d" % (len(c4), len(frz)))
for r in frz:
    if r not in c4:
        print("     反例: %-20s w%s samples=%s span=%s 期望≈%d error=%s verdict=%s" %
              (r["dir"], r["window"], r["n_samp_f"], r["span_s"], int(500 * (r["span_s"] or 25)),
               r["error"], r["verdict"]))
print()
print("  --- 冻结窗内 ws_kb / pf_kb 是否也在动（内存侧证）---")
for r in sorted(frz, key=lambda x: (x["dir"], x["window"])):
    print("     %-20s w%s ws_uniq=%s %s | pf_uniq=%s %s" %
          (r["dir"], r["window"], r.get("ws_kb_n_uniq"), r.get("ws_kb_uniq"),
           r.get("pf_kb_n_uniq"), r.get("pf_kb_uniq")))
print()

print("=== 4. 跨窗连续性：FRZ 的 f0 是否等于同趟前一窗的 f1 ===")
bytrip = {}
for r in rows:
    bytrip.setdefault(r["dir"], []).append(r)
for d, rs in sorted(bytrip.items()):
    rs.sort(key=lambda x: x["window"] if x["window"] is not None else -1)
    parts = []
    for r in rs:
        parts.append("w%s[%s->%s df=%s st=%s]" % (r["window"], r["edge_f0"], r["edge_f1"],
                                                  r["df_edge"], r["stats"].get("max_stall_s")))
    print("  %-20s %s" % (d, " ".join(parts)))
print()

print("=== 5. 帧号回退窗（BACK）与加载段窗（LOAD）全字段 ===")
for r in rows:
    if r["class"] in ("BACK", "LOAD"):
        print("  --- %s w%s class=%s ---" % (r["dir"], r["window"], r["class"]))
        print("      trip_id=%s map=%s gamemd=%s span=%s settle=%s hz=%s verdict=%s error=%s"
              % (r["trip_id"], r["map_sha"], r["gamemd_sha"], r["span_s"], r["settle_s"], r["hz"],
                 r["verdict"], r["error"]))
        print("      gate=%s" % json.dumps(r["gate"], ensure_ascii=False))
        print("      edge_f0=%s edge_f1=%s df_edge=%s f_first=%s f_last=%s df_sample=%s f_min=%s f_max=%s f_distinct=%s"
              % (r["edge_f0"], r["edge_f1"], r["df_edge"], r.get("f_first"), r.get("f_last"),
                 r["df_sample"], r.get("f_min"), r.get("f_max"), r.get("f_distinct")))
        print("      n_edges=%s up=%s down=%s sum_up=%s sum_down=%s monotonic=%s"
              % (r["n_edges"], r.get("n_up_events"), r.get("n_down_events"), r.get("sum_up"),
                 r.get("sum_down"), r.get("monotonic_nondecreasing")))
        print("      stats=%s" % json.dumps(r["stats"], ensure_ascii=False))
        print("      frame_edges head=%s tail=%s" % (r["path"] and "", ""))
        j = load(r["path"])
        ed = j["frame_edges"]
        print("      frame_edges[:6]=%s" % json.dumps(ed[:6]))
        print("      frame_edges[-6:]=%s" % json.dumps(ed[-6:]))
        print("      counters[:2]=%s" % json.dumps((j.get("counters") or [])[:2], ensure_ascii=False)[:400])
        print("      counters[-2:]=%s" % json.dumps((j.get("counters") or [])[-2:], ensure_ascii=False)[:400])
        print("      ws_uniq=%s units_uniq=%s g_uniq=%s b_uniq=%s" %
              (r.get("ws_kb_uniq"), r.get("units_uniq"), r.get("g_uniq"), r.get("b_uniq")))
print()

print("=== 6. T42 与 l1_20261023e4 专查 ===")
for d in ("archive_T42", "l1_20261023e4"):
    for r in rows:
        if r["dir"] != d:
            continue
        j = load(r["path"])
        print("  --- %s w%s class=%s ---" % (r["dir"], r["window"], r["class"]))
        print("     trip_id=%s span=%s settle=%s verdict=%s error=%s gate=%s" %
              (r["trip_id"], r["span_s"], r["settle_s"], r["verdict"], r["error"],
               json.dumps(r["gate"], ensure_ascii=False)))
        print("     f0=%s f1=%s df=%s f_distinct=%s n_edges=%s samples=%s" %
              (r["edge_f0"], r["edge_f1"], r["df_edge"], r.get("f_distinct"), r["n_edges"], r["n_samp_f"]))
        print("     stats=%s" % json.dumps(r["stats"], ensure_ascii=False))
        print("     counters uniq: units=%s inf=%s g=%s b=%s techno=%s g_items=%s b_items=%s ws=%s pf=%s" %
              (r.get("units_uniq"), r.get("infantry_uniq"), r.get("g_uniq"), r.get("b_uniq"),
               r.get("techno_uniq"), r.get("g_items_uniq"), r.get("b_items_uniq"),
               r.get("ws_kb_uniq"), r.get("pf_kb_uniq")))
        st = j.get("stats") or {}
        print("     隐含游戏时长: f0/31.2=%.2fs  f0/30=%.2fs" %
              ((r["edge_f0"] or 0) / 31.2, (r["edge_f0"] or 0) / 30.0))
print()

print("=== 7. 全部窗逐行 CSV（自查用）===")
print("dir,trip_id,w,class,f0,f1,df,fps_avg,df/span,logic_frames,max_stall_s,span_s,pre_fps15,gate_ok,samples,n_edges,f_distinct,units_uniq,g_uniq,b_uniq,map8,gamemd8,verdict")
for r in sorted(rows, key=lambda x: (x["dir"], x["window"])):
    g = r["gate"] or {}
    print("%s,%s,%s,%s,%s,%s,%s,%s,%.3f,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
        r["dir"], r["trip_id"], r["window"], r["class"], r["edge_f0"], r["edge_f1"], r["df_edge"],
        r["stats"].get("fps_avg"),
        (r["df_edge"] / (r["span_s"] or 1)),
        r["stats"].get("logic_frames"), r["stats"].get("max_stall_s"), r["span_s"],
        g.get("pre_fps15"), g.get("ok"), r["n_samp_f"], r["n_edges"], r.get("f_distinct"),
        r.get("units_n_uniq"), r.get("g_n_uniq"), r.get("b_n_uniq"),
        r["map_sha"], r["gamemd_sha"], r["verdict"]))

print()
print("=== 8. 同趟 pre_fps15 是否三窗同值（gate 是否被复制）===")
for d, rs in sorted(bytrip.items()):
    vals = [(r["window"], (r["gate"] or {}).get("pre_fps15"), (r["gate"] or {}).get("units0")) for r in sorted(rs, key=lambda x: x["window"] or -1)]
    uniq = {v[1] for v in vals}
    if len(uniq) == 1 and len(vals) > 1:
        print("  SAME  %-20s %s" % (d, vals))
