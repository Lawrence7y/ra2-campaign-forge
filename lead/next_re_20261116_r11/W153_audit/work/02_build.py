# -*- coding: utf-8 -*-
"""步骤2：一次性全量提取（我自己实现的分段器）

分段口径（本卡定义，可在 03 里切换）：
  时间源 = t_perf_ns（100 ns 网格，实测最小正增量 ~0.09 ms）——**不用 t_monotonic**
  （实测 t_monotonic 量化到 15.625 ms，见 EVIDENCE/01b_schema_timing.txt）。
  窗口 k = floor((t - t_trip_first)/10 s)；段内 Δt/Δframe 取该段首末样本之差。

输出：
  EVIDENCE/segments.tsv   每行 = 一个 10 秒分段
  EVIDENCE/trips.tsv      每行 = 一趟的汇总
  EVIDENCE/df_hist.txt    相邻样本 Δframe 分布（奇偶性、量化证据）
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

SEG_HDR = ["trip", "rel", "win", "n_samp", "t_start_s", "t_end_s", "span_s",
           "first_frame", "last_frame", "dframe", "dt_ms", "ms_per_frame",
           "ms_per_frame_exact10", "a8_mean", "a8_med", "a8_max", "a8_min",
           "b0_mean", "x87_delta", "scans_per_frame", "mode_set", "step_set",
           "iv_med_ms", "iv_n", "iv_med_msperframe", "iv_adv_n"]


def main():
    files = C.all_files()
    seg_rows = []
    trip_rows = []
    df_hist_all = Counter()
    df_adv_parity = Counter()
    mspf_hist = Counter()          # 相邻帧推进区间的 ms/frame（2 位小数）
    dt_hist = Counter()
    bad = []
    for i, p in enumerate(files):
        try:
            rows, meta = C.load_series(p)
        except Exception as e:
            bad.append((C.trip_rel(p), repr(e)))
            continue
        if len(rows) < 10:
            trip_rows.append(dict(trip=meta["trip"], rel=meta["rel"], n=meta["n"],
                                  dur_s=meta.get("dur_s"), note="too_short"))
            continue
        t0 = rows[0]["t"]
        # ---- 相邻样本层：Δframe 与 per-interval ms/frame ----
        df_hist = Counter()
        for a, b in zip(rows, rows[1:]):
            dt = b["t"] - a["t"]
            df = (b["frame"] or 0) - (a["frame"] or 0)
            df_hist[df] += 1
            if df > 0:
                df_adv_parity[df % 2] += 1
                mspf_hist[round(dt * 1000.0 / df, 2)] += 1
                dt_hist[round(dt * 1000.0, 1)] += 1
        df_hist_all.update(df_hist)

        # ---- 10 秒分段 ----
        buckets = {}
        for s in rows:
            k = int((s["t"] - t0) // 10.0)
            buckets.setdefault(k, []).append(s)
        wins = []
        for k in sorted(buckets):
            seg = buckets[k]
            if len(seg) < 2:
                continue
            a, b = seg[0], seg[-1]
            span_s = b["t"] - a["t"]
            dt_ms = span_s * 1000.0
            df = (b["frame"] or 0) - (a["frame"] or 0)
            a8 = [x["A8ED50"] for x in seg if x["A8ED50"] is not None]
            b0 = [x["B0CE88"] for x in seg if x["B0CE88"] is not None]
            x87 = [x["X87E8E0"] for x in seg if x["X87E8E0"] is not None]
            modes = sorted({x["mode"] for x in seg if x["mode"] is not None})
            steps = sorted({x["step"] for x in seg if x["step"] is not None})
            ivs = []
            iv_adv = 0
            for u, v in zip(seg, seg[1:]):
                d = v["t"] - u["t"]
                f = (v["frame"] or 0) - (u["frame"] or 0)
                if d > 0:
                    ivs.append(d * 1000.0)
                if f > 0 and d > 0:
                    iv_adv += 1
            # 段内"帧推进区间"的 ms/frame 中位（另一种口径）
            adv_mspf = []
            for u, v in zip(seg, seg[1:]):
                d = v["t"] - u["t"]
                f = (v["frame"] or 0) - (u["frame"] or 0)
                if f > 0 and d > 0:
                    adv_mspf.append(d * 1000.0 / f)
            row = dict(
                trip=meta["trip"], rel=meta["rel"], win=k, n_samp=len(seg),
                t_start_s=round(a["t"] - t0, 4), t_end_s=round(b["t"] - t0, 4),
                span_s=round(span_s, 4),
                first_frame=a["frame"], last_frame=b["frame"], dframe=df,
                dt_ms=round(dt_ms, 3),
                ms_per_frame=(round(dt_ms / df, 4) if df > 0 else None),
                ms_per_frame_exact10=(round(10000.0 / df, 4) if df > 0 else None),
                a8_mean=(round(C.mean(a8), 3) if a8 else None),
                a8_med=(round(C.median(a8), 3) if a8 else None),
                a8_max=(max(a8) if a8 else None),
                a8_min=(min(a8) if a8 else None),
                b0_mean=(round(C.mean(b0), 3) if b0 else None),
                x87_delta=((x87[-1] - x87[0]) if len(x87) >= 2 else None),
                scans_per_frame=((round((x87[-1] - x87[0]) / df, 4)) if (len(x87) >= 2 and df > 0) else None),
                mode_set=";".join(str(m) for m in modes),
                step_set=";".join(str(s) for s in steps)[:40],
                iv_med_ms=(round(C.median(ivs), 3) if ivs else None),
                iv_n=len(ivs), iv_adv_n=iv_adv,
                iv_med_msperframe=(round(C.median(adv_mspf), 4) if adv_mspf else None),
            )
            wins.append(row)
            seg_rows.append(row)
        trip_rows.append(dict(trip=meta["trip"], rel=meta["rel"], n=meta["n"],
                              dur_s=round(meta["dur_s"], 3) if meta.get("dur_s") else None,
                              frame0=meta.get("frame0"), frame1=meta.get("frame1"),
                              df_total=((meta.get("frame1") or 0) - (meta.get("frame0") or 0)),
                              n_win=len(wins),
                              a8_max=(max(r["a8_max"] for r in wins) if wins else None),
                              a8_mean=(round(C.mean([r["a8_mean"] for r in wins]), 3) if wins else None),
                              df_hist=";".join("%d:%d" % kv for kv in sorted(df_hist.items())[:8]),
                              note=""))
        print("[%d/%d] %s n=%d win=%d" % (i + 1, len(files), meta["trip"], meta["n"], len(wins)), flush=True)

    # 写 segments.tsv
    p = os.path.join(C.EVID, "segments.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\t".join(SEG_HDR) + "\n")
        for r in seg_rows:
            fh.write("\t".join("" if r.get(h) is None else str(r.get(h)) for h in SEG_HDR) + "\n")
    # 写 trips.tsv
    tcols = ["trip", "rel", "n", "dur_s", "frame0", "frame1", "df_total", "n_win", "a8_max", "a8_mean", "df_hist", "note"]
    p2 = os.path.join(C.EVID, "trips.tsv")
    with open(p2, "w", encoding="utf-8") as fh:
        fh.write("\t".join(tcols) + "\n")
        for r in trip_rows:
            fh.write("\t".join("" if r.get(h) is None else str(r.get(h)) for h in tcols) + "\n")

    # Δframe 分布
    lines = ["=== 全部趟：相邻样本 Δframe 分布（总样本对 %d） ===" % sum(df_hist_all.values())]
    for k, v in sorted(df_hist_all.items()):
        lines.append("  dframe=%4d  n=%9d  (%.4f%%)" % (k, v, 100.0 * v / sum(df_hist_all.values())))
    lines.append("")
    lines.append("=== 帧推进区间(Δframe>0)的 Δframe 奇偶 ===")
    tot = sum(df_adv_parity.values())
    for k, v in sorted(df_adv_parity.items()):
        lines.append("  parity=%d n=%d (%.4f%%)" % (k, v, 100.0 * v / tot))
    lines.append("")
    lines.append("=== 帧推进区间的 ms/frame 值分布（2 位小数，前 40 个最频） ===")
    for k, v in mspf_hist.most_common(40):
        lines.append("  ms/frame=%10.2f  n=%8d (%.4f%%)" % (k, v, 100.0 * v / tot))
    lines.append("")
    lines.append("=== 帧推进区间的 dt(ms) 分布（0.1 ms 桶，前 30） ===")
    for k, v in dt_hist.most_common(30):
        lines.append("  dt=%.1f ms  n=%d" % (k, v))
    lines.append("")
    lines.append("=== 解析/读取异常 ===")
    for r in bad:
        lines.append("  %s -> %s" % r)
    txt = "\n".join(lines)
    C.write_evidence("02_df_hist.txt", txt)
    print(txt)
    print("segments=%d trips=%d" % (len(seg_rows), len(trip_rows)))


if __name__ == "__main__":
    main()
