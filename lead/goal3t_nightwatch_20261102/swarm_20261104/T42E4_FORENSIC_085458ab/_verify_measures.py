import json, os, datetime

P = {
 "T42w0": r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\measure_w0.json",
 "T42w1": r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\measure_w1.json",
 "T42w2": r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\measure_w2.json",
 "E4w0":  r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e4\measure_w0.json",
 "E4w1":  r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e4\measure_w1.json",
 "E4w2":  r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e4\measure_w2.json",
}
for k, v in P.items():
    rp = os.path.realpath(v)
    if not rp.startswith(r"D:\Project\ra2-campaign-forge\out\re_work"):
        raise SystemExit("bad path: " + rp)

def wall(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def median(xs):
    xs = sorted(xs); n = len(xs)
    return xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2

for key in ("T42w0", "T42w1", "T42w2", "E4w0", "E4w1", "E4w2"):
    with open(P[key], "r", encoding="utf-8") as fh:
        j = json.load(fh)
    name = key[:3]; w = key[3:]
    t = j["samples"]["t"]; f = j["samples"]["f"]
    st = j["stats"]; gt = j["gate"]
    span = t[-1] - t[0]
    print("--- %s: trip=%s window=%s verdict=%s error=%r" % (key, j["trip_id"], j["window"], j["verdict"], j["error"]))
    print("    t_abs0=%r wall=%s  t_clock=%s hz=%s span_s=%s settle_s=%s" % (j["t_abs0"], wall(j["t_abs0"]), j["t_clock"], j["hz"], j["span_s"], j["settle_s"]))
    print("    n_samples(f/t)=%d/%d stats.samples=%s" % (len(f), len(t), st["samples"]))
    print("    perf t[%r .. %r] span=%.6fs   f[%d .. %d] df=%d" % (t[0], t[-1], span, f[0], f[-1], f[-1]-f[0]))
    edges = j["frame_edges"]
    print("    frame_edges n=%d first=%s last=%s" % (len(edges), edges[0], edges[-1]))
    print("    stats: fps_avg=%r fps_p50=%r logic_frames=%s max_stall_s=%s n_edges=%s n_multi_advance=%s note=%r tick_miss=%s frame_ms_p50=%r frame_ms_max=%r" % (
        st["fps_avg"], st["fps_p50"], st["logic_frames"], st["max_stall_s"], st["n_edges"], st["n_multi_advance"], st["note"], st["tick_miss"], st["frame_ms_p50"], st["frame_ms_max"]))
    print("    gate=%s" % (gt,))
    if j.get("w1"):
        print("    w1(nested)=%s" % (j["w1"],))
    df = f[-1] - f[0]
    if key == "E4w1":
        zeroidx = next(i for i, v in enumerate(f) if v == 0)
        print("    [RESET] first zero-sample idx=%d t=%r ; prev f=%d at t=%r" % (zeroidx, t[zeroidx], f[zeroidx-1], t[zeroidx-1]))
        pre = [v for v in f if v != 0]
        print("    [RESET] f before reset: %d..%d (n=%d) ; all f==0 after: %s" % (pre[0], pre[-1], len(pre), all(v == 0 for v in f[zeroidx:])))
        off = edges[-1][1] - t[0]
        print("    [RESET] reset edge wall ~= %s (offset %.6fs from first sample)" % (wall(j["t_abs0"] + off), off))
    if key == "E4w2":
        steps = [b - a for a, b in zip(t, t[1:])]
        gaps10 = sum(1 for s in steps if s > 0.010)
        med = median(steps)
        print("    [E4w2] my median step=%.3fms  gaps>10ms=%d  max step=%.3fms  all_f_zero=%s" % (med*1000, gaps10, max(steps)*1000, all(v == 0 for v in f)))
        lastwall = j["t_abs0"] + (t[-1] - t[0])
        print("    [E4w2] last valid sample wall ~= %s ; nominal end ~= %s ; silent tail = %.3fs" % (wall(lastwall), wall(j["t_abs0"] + j["span_s"]), (j["t_abs0"]+j["span_s"])-lastwall))
    if len(edges) > 2:
        dts = [b[1] - a[1] for a, b in zip(edges, edges[1:])]
        print("    [recompute] fps_avg=(df/span)=%.4f  fps_p50=1/median(dt)=%.4f  max_edge_gap=%.3fs" % (df/span, 1/median(dts), max(dts)))
    if key in ("T42w0", "T42w1", "E4w0", "E4w1"):
        nxt_key = {"T42w0": "T42w1", "T42w1": "T42w2", "E4w0": "E4w1", "E4w1": "E4w2"}[key]
        with open(P[nxt_key], "r", encoding="utf-8") as fh:
            nj = json.load(fh)
        nt = nj["samples"]["t"]
        print("    [continuity] this last perf=%r -> %s first perf=%r delta=%.1fms ; t_abs0 delta=%.6fs" % (t[-1], nxt_key, nt[0], (nt[0]-t[-1])*1000, nj["t_abs0"]-j["t_abs0"]))
    print()
