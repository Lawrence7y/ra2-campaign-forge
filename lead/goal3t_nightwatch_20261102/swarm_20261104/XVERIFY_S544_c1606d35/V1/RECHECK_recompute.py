"""RECHECK independent recomputation — written from scratch for the V1 recheck.

Inputs (read-only): all measure_w*.json under the trip tree, harness v4 source,
launch-result / fields JSON, end-screen PNGs. No live process is touched.
All formulas are re-derived from the source lines read in this session:
  :4757-4759  span = t[-1]-t[0]; logic = f[-1]-f[0]
  :4791       fps_avg = logic/span (logic<=0 => null, :4784-4787)
  :4794-4813  frame_ms = (tb-ta)*1000 only for df==1; p50 linear interp; fps_p50=1000/p50
  :5322       JSON span_s = constant MEASURE_WINDOW_S (25.0)
Output: stdout only (redirected to RECHECK_out.txt by the caller).
"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
TRIP = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
V1 = ROOT / "lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V1"
HARNESS = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py"


def pctl(sorted_vals, q):
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    idx = (n - 1) * q
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def analyze(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    s = d.get("samples") or {}
    t = [float(x) for x in s.get("t", [])]
    f = [int(x) for x in s.get("f", [])]
    st = d.get("stats") or {}
    gate = d.get("gate") or {}
    r = {
        "path": path.relative_to(TRIP).as_posix(),
        "trip_id": d.get("trip_id"),
        "window": d.get("window"),
        "schema": d.get("schema"),
        "hz": d.get("hz"),
        "span_s_field": d.get("span_s"),
        "map_sha": (d.get("map_sha256") or "")[:16],
        "gamemd_sha": (d.get("gamemd_sha256") or "")[:16],
        "pre_fps15": gate.get("pre_fps15"),
        "units0": gate.get("units0"),
        "verdict": d.get("verdict"),
        "n_samples": len(t),
        "len_t": len(t), "len_f": len(f),
    }
    if len(t) != len(f) or len(t) < 2:
        r["ok"] = False
        return r
    r["ok"] = True
    span = t[-1] - t[0]
    logic = f[-1] - f[0]
    r["measured_span"] = span
    r["logic_frames"] = logic
    r["fps_avg"] = (logic / span) if (span > 0 and logic > 0) else None
    r["fps_avg_if_hardcoded_25"] = (logic / 25.0) if logic > 0 else None

    # rebuild edge table from raw samples (first observation of each f change)
    edges = []
    prev = None
    for tv, fv in zip(t, f):
        if prev is None or fv != prev:
            edges.append((fv, tv))
            prev = fv
    stored = [[int(e[0]), float(e[1])] for e in (d.get("frame_edges") or [])]
    r["n_edges"] = len(edges)
    r["edges_match_stored"] = (stored == [[a, b] for a, b in edges])

    # frame_ms: df==1 only; df>1 discarded and counted
    frame_ms = []
    n_multi = 0
    for (fa, ta), (fb, tb) in zip(edges, edges[1:]):
        df = fb - fa
        if df == 1:
            frame_ms.append((tb - ta) * 1000.0)
        elif df > 1:
            n_multi += 1
    frame_ms.sort()
    p50 = pctl(frame_ms, 0.50)
    r["frame_ms_p50"] = p50
    r["fps_p50"] = (1000.0 / p50) if (p50 is not None and p50 > 0) else None
    r["n_multi_advance"] = n_multi
    r["n_frame_ms_samples"] = len(frame_ms)

    # live_fps from first/last edges (this V1 ask's formula)
    r["edge_df"] = (edges[-1][0] - edges[0][0]) if len(edges) >= 2 else None
    r["edge_dt"] = (edges[-1][1] - edges[0][1]) if len(edges) >= 2 else None
    r["live_fps"] = (
        r["edge_df"] / r["edge_dt"]
        if len(edges) >= 2 and r["edge_dt"] > 0 and r["edge_df"] > 0
        else None
    )

    # longest constant-frame run (same estimator as _measure_stats :4773-4783)
    run_t0, run_f = t[0], f[0]
    best = 0.0
    for tv, fv in zip(t[1:], f[1:]):
        if fv != run_f:
            best = max(best, tv - run_t0)
            run_t0, run_f = tv, fv
    best = max(best, t[-1] - run_t0)
    r["max_stall_s"] = best

    # sampling gaps
    dts = [t[i + 1] - t[i] for i in range(len(t) - 1)]
    r["dt_min"] = min(dts)
    r["dt_max"] = max(dts)
    r["dt_sum"] = sum(dts)
    r["gap_gt_10ms_count"] = sum(1 for x in dts if x > 0.010)
    r["gap_gt_10ms_sum"] = sum(x for x in dts if x > 0.010)
    r["gap_gt_5ms_count"] = sum(1 for x in dts if x > 0.005)

    # stored stats comparison
    r["stored_fps_avg"] = st.get("fps_avg")
    r["stored_fps_p50"] = st.get("fps_p50")
    r["stored_logic_frames"] = st.get("logic_frames")
    r["stored_n_edges"] = st.get("n_edges")
    r["stored_max_stall_s"] = st.get("max_stall_s")
    r["stored_n_multi"] = st.get("n_multi_advance")
    r["stored_note"] = st.get("note")
    return r


def num(v, k=6):
    return "NA" if v is None else f"{v:.{k}f}"


def main():
    files = sorted(TRIP.rglob("measure_w*.json"))
    rows = [analyze(p) for p in files]
    print(f"TRIP={TRIP.as_posix()}")
    print(f"TOTAL_FILES={len(files)}")
    print(f"ROOT_LEVEL_FILES={sum(1 for r in rows if '/' not in r['path'])}")
    print(f"SUBDIR_FILES={sum(1 for r in rows if '/' in r['path'])}")
    print(f"BAD_TF_LENGTH={sum(1 for r in rows if r['len_t'] != r['len_f'])}")
    print(f"EDGE_TABLE_MISMATCH={sum(1 for r in rows if r.get('ok') and not r['edges_match_stored'])}")

    # classify all 103
    computable = [r for r in rows if r.get("live_fps") is not None]
    noncomp = [r for r in rows if r.get("live_fps") is None]
    print(f"COMPUTABLE_LIVE_FPS={len(computable)}  NONCOMPUTABLE={len(noncomp)}")
    reason = Counter()
    for r in noncomp:
        if not r.get("ok"):
            reason["short_or_mismatched_samples"] += 1
        elif r["logic_frames"] <= 0:
            reason["logic_frames<=0"] += 1
        elif r["n_edges"] < 2:
            reason["edges<2"] += 1
        elif r["edge_df"] <= 0 or r["edge_dt"] <= 0:
            reason["nonpositive_edge_df_or_dt"] += 1
        else:
            reason["other"] += 1
    print(f"NONCOMPUTABLE_REASONS={dict(reason)}")
    print("NONCOMPUTABLE_LIST:")
    for r in noncomp:
        print(f"  {r['path']} samples={r['n_samples']} logic={r.get('logic_frames')} "
              f"edges={r.get('n_edges')} verdict={r['verdict']} note={r.get('stored_note')!r}")

    # categories of every window
    print(f"LOGIC_LE_0_ALL={sum(1 for r in rows if r.get('logic_frames') is not None and r['logic_frames'] <= 0)}")
    print(f"STORED_FPS_AVG_NULL_WHEN_LOGIC_LE_0="
          f"{sum(1 for r in rows if r.get('logic_frames') is not None and r['logic_frames'] <= 0 and r['stored_fps_avg'] is None)}")
    print(f"NOMINAL_SPAN_DISTRIBUTION={dict(Counter(repr(r['span_s_field']) for r in rows))}")
    print(f"N_MULTI_ADVANCE_NONZERO_ALL={sum(1 for r in rows if (r.get('n_multi_advance') or 0) > 0)}")
    print(f"STORED_N_MULTI_NONZERO={sum(1 for r in rows if (r.get('stored_n_multi') or 0) > 0)}")

    # stored vs recomputed agreement
    bad_avg = [(r["path"], r["fps_avg"], r["stored_fps_avg"])
               for r in computable
               if r["stored_fps_avg"] is None
               or abs(r["fps_avg"] - r["stored_fps_avg"]) > 1e-5]
    bad_p50 = [(r["path"], r["fps_p50"], r["stored_fps_p50"])
               for r in computable
               if r["stored_fps_p50"] is None
               or abs(r["fps_p50"] - r["stored_fps_p50"]) > 0.01]
    print(f"STORED_VS_RECOMPUTED_FPS_AVG_MISMATCH_GT_1E-5={len(bad_avg)} {bad_avg[:6]}")
    print(f"STORED_VS_RECOMPUTED_FPS_P50_MISMATCH_GT_0.01={len(bad_p50)} {bad_p50[:6]}")

    # spans: measured vs hardcoded 25.0
    spans = [r["measured_span"] for r in computable]
    print(f"MEASURED_SPAN_MIN_MAX_ALL_COMPUTABLE=({min(spans):.9f}, {max(spans):.9f})")
    n25 = [r for r in computable if r["span_s_field"] == 25.0]
    s25 = [r["measured_span"] for r in n25]
    print(f"NOMINAL_25S_COMPUTABLE_COUNT={len(n25)} "
          f"SPAN_MIN_MAX=({min(s25):.9f}, {max(s25):.9f})")
    exact25 = sum(1 for x in s25 if abs(x - 25.0) < 1e-9)
    print(f"NOMINAL_25S_SPAN_EXACTLY_25.0_COUNT={exact25}")
    # hardest evidence: the window with the largest deviation from 25.0
    dev = max(n25, key=lambda r: abs(25.0 - r["measured_span"]))
    print(f"MAX_DEVIATION_WINDOW={dev['path']} measured_span={dev['measured_span']:.9f} "
          f"logic={dev['logic_frames']} recomputed_fps_avg={dev['fps_avg']:.9f} "
          f"stored_fps_avg={dev['stored_fps_avg']!r} logic/25={dev['fps_avg_if_hardcoded_25']:.9f}")

    # threshold counts
    avg_low = [r for r in computable if r["fps_avg"] is not None and r["fps_avg"] < 28]
    mixed = [r for r in computable
             if r["fps_avg"] is not None and r["fps_avg"] < 28
             and r["fps_p50"] is not None and r["fps_p50"] >= 28]
    live_low = [r for r in computable if r["live_fps"] < 28]
    p50_low = [r for r in computable if r["fps_p50"] is not None and r["fps_p50"] < 28]
    p50_none = [r for r in computable if r["fps_p50"] is None]
    print()
    print(f"THRESHOLD=28 DENOMINATOR_COMPUTABLE={len(computable)}")
    print(f"FPS_AVG_LT_28={len(avg_low)}")
    print(f"FPS_AVG_LT_28_AND_FPS_P50_GE_28={len(mixed)}")
    print(f"LIVE_FPS_LT_28={len(live_low)}")
    print(f"FPS_P50_LT_28={len(p50_low)}")
    print(f"FPS_P50_NONE_IN_COMPUTABLE={len(p50_none)}")
    print(f"FPS_P50_NONE_ALL_103={sum(1 for r in rows if r.get('stored_fps_p50') is None)}")
    print("MIXED_14 (recomputed from raw samples):")
    for r in mixed:
        print(f"  {r['path']}\tavg={num(r['fps_avg'])}\tlive={num(r['live_fps'])}\t"
              f"p50={num(r['fps_p50'])}\tmax_stall={num(r['max_stall_s'])}\t"
              f"edge_dt={num(r['edge_dt'])}\tlogic={r['logic_frames']}\t"
              f"span={num(r['measured_span'])}\tn_multi={r['n_multi_advance']}\t"
              f"gap10={num(r['gap_gt_10ms_sum'], 9)}")
    print(f"MIXED_WITH_LIVE_GE_28={sum(1 for r in mixed if r['live_fps'] >= 28)}")
    print(f"MIXED_WITH_LIVE_LT_28={sum(1 for r in mixed if r['live_fps'] < 28)}")
    print(f"MIXED_MAX_STALL_MIN_MAX=({min(r['max_stall_s'] for r in mixed):.6f}, "
          f"{max(r['max_stall_s'] for r in mixed):.6f})")
    print(f"MIXED_GAP_GT10MS_TOTAL={sum(r['gap_gt_10ms_sum'] for r in mixed):.9f}")
    print(f"LIVE_FPS_LT_FPS_AVG_COUNT={sum(1 for r in computable if r['live_fps'] < r['fps_avg'])}")

    # T34 special
    t34 = next(r for r in rows if r["path"] == "archive_T34/measure_w0.json")
    print()
    print("ARCHIVE_T34_W0_SPECIAL")
    for k in ("trip_id", "schema", "hz", "span_s_field", "n_samples", "logic_frames",
              "measured_span", "dt_sum", "fps_avg", "stored_fps_avg", "fps_p50",
              "stored_fps_p50", "frame_ms_p50", "n_frame_ms_samples", "n_edges",
              "edge_df", "edge_dt", "live_fps", "max_stall_s", "stored_max_stall_s",
              "dt_min", "dt_max", "gap_gt_10ms_count", "gap_gt_10ms_sum",
              "gap_gt_5ms_count", "n_multi_advance", "verdict"):
        print(f"  {k}={t34[k]!r}")
    p34 = TRIP / "archive_T34/measure_w0.json"
    d34 = json.loads(p34.read_text(encoding="utf-8"))
    t = [float(x) for x in d34["samples"]["t"]]
    f = [int(x) for x in d34["samples"]["f"]]
    runs = []
    start = 0
    for i in range(1, len(f) + 1):
        if i == len(f) or f[i] != f[start]:
            runs.append((f[start], start, i - 1, t[start], t[i - 1], t[i - 1] - t[start]))
            start = i
    print(f"  n_constant_runs={len(runs)}")
    for fr, a, b, ta, tb, dur in runs:
        print(f"  run f={fr} idx={a}..{b} dur_s={dur:.6f}")
    print(f"  f_start={f[0]} f_end={f[-1]} sum_run_durations={sum(x[5] for x in runs):.9f}")
    print(f"  T34_W1_W2_FILES={sorted(p.name for p in (TRIP/'archive_T34').glob('measure_w*.json'))}")

    # correlations and independence structure
    trips = defaultdict(list)
    for r in rows:
        trips[r["trip_id"]].append(r)
    print()
    print(f"N_TRIP_IDS={len(trips)}")
    print(f"TRIPS_WITH_3_WINDOWS={sum(1 for k, v in trips.items() if len(v) == 3)}")
    print(f"DISTINCT_TRIPS_AMONG_COMPUTABLE={len({r['trip_id'] for r in computable})}")
    pairs_all = [(r["pre_fps15"], r["live_fps"], r["units0"], r)
                 for r in computable
                 if r["pre_fps15"] is not None and r["units0"] is not None]
    print(f"PAIRS_PRE_AND_UNITS_NONNULL={len(pairs_all)}")
    print(f"RHO_PRE_LIVE_ALL={pearson([p[0] for p in pairs_all], [p[1] for p in pairs_all])!r}")
    print(f"RHO_UNITS_LIVE_ALL={pearson([float(p[2]) for p in pairs_all], [p[1] for p in pairs_all])!r}")
    gt0 = [p for p in pairs_all if p[2] > 0]
    eq0 = [p for p in pairs_all if p[2] == 0]
    print(f"PAIRS_UNITS_GT_0={len(gt0)} RHO_PRE_LIVE={pearson([p[0] for p in gt0], [p[1] for p in gt0])!r}")
    print(f"PAIRS_UNITS_EQ_0={len(eq0)} RHO_PRE_LIVE={pearson([p[0] for p in eq0], [p[1] for p in eq0])!r}")
    print("  UNITS_EQ_0_WINDOWS:")
    for p in eq0:
        print(f"    {p[3]['path']} pre={p[0]} live={num(p[1])} units0={p[2]}")
    only25 = [p for p in pairs_all if p[3]["span_s_field"] == 25.0]
    print(f"PAIRS_NOMINAL_25S={len(only25)} RHO_PRE_LIVE={pearson([p[0] for p in only25], [p[1] for p in only25])!r}")
    # trip-level dedup: mean of live_fps per trip; pre_fps15 shared
    by_trip = defaultdict(list)
    for p in pairs_all:
        by_trip[p[3]["trip_id"]].append(p)
    tx = [sum(q[0] for q in v) / len(v) for v in by_trip.values()]
    ty = [sum(q[1] for q in v) / len(v) for v in by_trip.values()]
    tu = [sum(q[2] for q in v) / len(v) for v in by_trip.values()]
    print(f"TRIP_LEVEL_N={len(by_trip)} RHO_PRE_LIVE={pearson(tx, ty)!r} RHO_UNITS_LIVE={pearson(tu, ty)!r}")
    shared = sum(1 for v in by_trip.values()
                 if len(v) >= 2 and len({q[0] for q in v}) == 1)
    print(f"TRIPS_WITH_>=2_PAIRS_AND_IDENTICAL_PRE={shared} "
          f"OF_MULTI_WINDOW_TRIPS={sum(1 for v in by_trip.values() if len(v) >= 2)}")

    # confounding: the two headline trips
    print()
    print("HEADLINE_TRIP_COMPARISON (from raw JSON):")
    for r in computable:
        if r["path"].startswith(("l1c_20261021/", "l3_1101v4d/")):
            print(f"  {r['path']} trip={r['trip_id']} units0={r['units0']} pre={r['pre_fps15']} "
                  f"avg={num(r['fps_avg'])} live={num(r['live_fps'])} map={r['map_sha']} "
                  f"gamemd={r['gamemd_sha']} hz={r['hz']} schema={r['schema']}")
    for r in computable:
        if r["path"].startswith(("l1c_20261021/", "l3_1101v4d/")):
            pass
    print(f"DISTINCT_MAP_SHA16_ALL_103={len({r['map_sha'] for r in rows})}")
    print(f"DISTINCT_GAMEMD_SHA16_ALL_103={len({r['gamemd_sha'] for r in rows})} {sorted({r['gamemd_sha'] for r in rows})}")
    print(f"DISTINCT_HZ_ALL_103={sorted({r['hz'] for r in rows})}")
    print(f"DISTINCT_SCHEMA_ALL_103={sorted({r['schema'] for r in rows})}")

    # launch harness versions, read from raw launch-result json
    print()
    print("LAUNCH_RESULT_HARNESS_PATHS:")
    for name in ("l1c_20261021", "l3_1101v4d"):
        d = TRIP / name
        cands = sorted(d.glob("*launch*result*.json")) + sorted(d.glob("qc151_fields.json"))
        for c in cands:
            try:
                obj = json.loads(c.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  {c.name}: unreadable {e!r}")
                continue
            hits = []

            def walk(o, prefix=""):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if isinstance(v, (dict, list)):
                            walk(v, prefix + k + ".")
                        elif isinstance(v, str) and ("harness" in k.lower() or "harness" in v.lower()):
                            hits.append((prefix + k, v[:200]))
                elif isinstance(o, list):
                    for i, v in enumerate(o[:20]):
                        if isinstance(v, (dict, list)):
                            walk(v, prefix + f"[{i}].")
                        elif isinstance(v, str) and "harness" in v.lower():
                            hits.append((prefix + f"[{i}]", v[:200]))
            walk(obj)
            print(f"  {name}/{c.name} root_type={type(obj).__name__} "
                  f"keys={list(obj.keys())[:25] if isinstance(obj, dict) else 'LIST len=' + str(len(obj))}")
            for k, v in hits[:12]:
                print(f"    {k} = {v}")

    # PNG evidence: file names, sha256, byte equality
    print()
    print("ARCHIVE_T34_PNG_EVIDENCE:")
    pngs = sorted((TRIP / "archive_T34").rglob("*.png"))
    print(f"  n_pngs={len(pngs)}")
    for p in pngs:
        print(f"  {p.relative_to(TRIP).as_posix()} bytes={p.stat().st_size} "
              f"sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")
    w1 = list((TRIP / "archive_T34").rglob("measure_w1_end_x.png"))
    w2 = list((TRIP / "archive_T34").rglob("measure_w2_end_x.png"))
    if w1 and w2:
        b1, b2 = w1[0].read_bytes(), w2[0].read_bytes()
        print(f"  w1_w2_byte_identical={b1 == b2} sha_equal="
              f"{hashlib.sha256(b1).hexdigest() == hashlib.sha256(b2).hexdigest()}")

    # qc151_fields.json T34 w1/w2 lines of interest
    fp = TRIP / "archive_T34/qc151_fields.json"
    if fp.is_file():
        obj = json.loads(fp.read_text(encoding="utf-8"))
        print(f"  qc151_fields.json root_type={type(obj).__name__} len={len(obj)}")
        seq = obj if isinstance(obj, list) else [obj]
        for i, item in enumerate(seq):
            if isinstance(item, dict) and ("current_frame" in item or "empty_window" in item):
                print(f"    rec[{i}] current_frame={item.get('current_frame')} "
                      f"empty_window={item.get('empty_window')} "
                      f"keys={list(item.keys())[:12]}")
    # pixel-level comparison of the two end-screen PNGs (no OCR: decode only)
    # PNGs are decoded via zlib + struct in pure stdlib; report dimensions and
    # exact per-pixel difference ratio (or state that a library was unavailable).
    try:
        import zlib
        import struct

        def decode_png(p):
            raw = p.read_bytes()
            assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not PNG"
            off, idat, w, h, bd, ct = 8, b"", None, None, None, None
            while off < len(raw):
                ln = struct.unpack(">I", raw[off:off + 4])[0]
                typ = raw[off + 4:off + 8]
                data = raw[off + 8:off + 8 + ln]
                if typ == b"IHDR":
                    w, h, bd, ct = struct.unpack(">IIBB", data[:10])
                elif typ == b"IDAT":
                    idat += data
                elif typ == b"IEND":
                    break
                off += 12 + ln
            ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ct)
            if bd != 8 or ch is None:
                return None, None, None, f"unsupported bd={bd} ct={ct}"
            dec = zlib.decompress(idat)
            stride = w * ch
            rows, prev, pos = [], bytearray(stride), 0
            for _y in range(h):
                ft = dec[pos]; pos += 1
                cur = bytearray(dec[pos:pos + stride]); pos += stride
                if ft == 1:
                    for x in range(ch, stride):
                        cur[x] = (cur[x] + cur[x - ch]) & 255
                elif ft == 2:
                    for x in range(stride):
                        cur[x] = (cur[x] + prev[x]) & 255
                elif ft == 3:
                    for x in range(stride):
                        a = cur[x - ch] if x >= ch else 0
                        cur[x] = (cur[x] + ((a + prev[x]) >> 1)) & 255
                elif ft == 4:
                    for x in range(stride):
                        a = cur[x - ch] if x >= ch else 0
                        b = prev[x]
                        c = prev[x - ch] if x >= ch else 0
                        pp = a + b - c
                        pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                        pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                        cur[x] = (cur[x] + pr) & 255
                elif ft != 0:
                    return None, None, None, f"unsupported filter {ft}"
                rows.append(bytes(cur))
                prev = cur
            return w, h, ch, rows

        p1 = (TRIP / "archive_T34/measure_w1_end_x.png")
        p2 = (TRIP / "archive_T34/measure_w2_end_x.png")
        w1_, h1_, c1_, r1 = decode_png(p1)
        w2_, h2_, c2_, r2 = decode_png(p2)
        print(f"  DECODED w1={w1_}x{h1_}ch={c1_} w2={w2_}x{h2_}ch={c2_}")
        if isinstance(r1, list) and isinstance(r2, list) and (w1_, h1_, c1_) == (w2_, h2_, c2_):
            diff_bytes = sum(sum(1 for a, b in zip(x, y) if a != b)
                             for x, y in zip(r1, r2))
            total = w1_ * h1_ * c1_
            diff_px = sum(sum(1 for i in range(0, w1_ * c1_, c1_)
                              if x[i:i + c1_] != y[i:i + c1_])
                          for x, y in zip(r1, r2))
            print(f"  PIXEL_BYTE_DIFF={diff_bytes}/{total} ({diff_bytes / total:.9f}) "
                  f"DIFF_PIXELS={diff_px}/{w1_ * h1_} ({diff_px / (w1_ * h1_):.9f})")
            # largest bounding box of differing pixels
            xs, ys = [], []
            for yy, (x, y) in enumerate(zip(r1, r2)):
                for i in range(0, w1_ * c1_, c1_):
                    if x[i:i + c1_] != y[i:i + c1_]:
                        xs.append(i // c1_); ys.append(yy)
            if xs:
                print(f"  DIFF_BBOX=(x {min(xs)}..{max(xs)}, y {min(ys)}..{max(ys)})")
        else:
            print(f"  DECODE_FAILED_OR_DIM_MISMATCH {r1!r} {r2!r}")
    except Exception as e:
        print(f"  PNG_DECODE_EXCEPTION={e!r}")
    print("DONE")


if __name__ == "__main__":
    main()
