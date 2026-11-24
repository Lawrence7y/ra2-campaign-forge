# -*- coding: utf-8 -*-
"""V2 时代效应核验：全量普查 measure_w*.json + 趟级元信息（harness/map/时刻）。

只读真机数据。零真机、零母本改动。输出 CSV 到本目录。
所有指标一律自己从 samples/frame_edges 重算，不抄 stats。
"""
import glob
import hashlib
import json
import os
import sys
import csv

ROOT = r"D:\Project\ra2-campaign-forge"
TRIPS = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
LEAD_TRIPS = ROOT + r"\lead\qc161_u0400_trip"
OUT = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S544_7255362d\V2"


def sha16_of_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return None


def trip_time_from_fields(fields_path):
    """qc151_fields.json 里第一个带 ts 的记录 -> 人类时间戳（本地 +08:00）。"""
    try:
        d = json.load(open(fields_path, encoding="utf-8"))
    except Exception:
        return None, None
    first = last = None
    for x in d if isinstance(d, list) else []:
        ts = x.get("ts")
        if isinstance(ts, str) and ts:
            if first is None:
                first = ts
            last = ts
    return first, last


def launch_meta(dirpath):
    p = os.path.join(dirpath, "_launch_result.json")
    rec = {"launch_result": os.path.exists(p), "harness_sha16": None,
           "harness_path": None, "argv_harness": None, "trip_id_launch": None,
           "duration_s": None, "rc": None}
    if not rec["launch_result"]:
        return rec
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        rec["harness_path"] = "READ_FAIL:" + repr(e)
        return rec
    rec["harness_sha16"] = d.get("harness_sha16")
    rec["harness_path"] = d.get("harness")
    argv = d.get("argv") or []
    rec["argv_harness"] = argv[0] if argv else None
    rec["trip_id_launch"] = d.get("trip_id")
    rec["duration_s"] = d.get("duration_s")
    rec["rc"] = d.get("rc")
    return rec


def carrier_count(dirpath):
    """载体件数：carrier_creation_receipt.json / carrier_manifest_pre_delete.json 条目数。"""
    out = {}
    for name, key in (("carrier_creation_receipt.json", "created"),
                      ("carrier_manifest_pre_delete.json", "manifest")):
        p = os.path.join(dirpath, name)
        if not os.path.exists(p):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            out[key] = "READ_FAIL"
            continue
        if isinstance(d, dict):
            for k2 in ("files", "entries", "items", "created", "carriers", "rows"):
                if isinstance(d.get(k2), list):
                    out[key] = len(d[k2])
                    break
            else:
                out[key] = "dict:" + ",".join(sorted(d.keys())[:6])
        elif isinstance(d, list):
            out[key] = len(d)
    return out


def measure_rows(path, base):
    d = json.load(open(path, encoding="utf-8"))
    edges = d.get("frame_edges") or []
    s = d.get("samples") or {}
    t = s.get("t") or []
    f = s.get("f") or []
    gate = d.get("gate") or {}
    stats = d.get("stats") or {}
    span = d.get("span_s") or 0.0

    live = None
    live_from_t = None
    if len(edges) >= 2:
        f0, t0 = edges[0][0], edges[0][1]
        f1, t1 = edges[-1][0], edges[-1][1]
        if t1 > t0:
            live = (f1 - f0) / (t1 - t0)
        # 末沿 -> 采样末 的停摆尾段
        if t:
            live_from_t = (f1 - f0) / (t[-1] - t0) if t[-1] > t0 else None

    gap = 0.0
    gap_n = 0
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        if dt > 0.010:
            gap_n += 1
            gap += dt

    rel = os.path.relpath(path, base).replace("\\", "/")
    return {
        "file": rel,
        "base": os.path.basename(base),
        "trip_id": d.get("trip_id"),
        "window": d.get("window"),
        "schema": d.get("schema"),
        "verdict": d.get("verdict"),
        "map_sha256": d.get("map_sha256"),
        "gamemd_sha256": d.get("gamemd_sha256"),
        "hz": d.get("hz"),
        "t_clock": d.get("t_clock"),
        "t_abs0": d.get("t_abs0"),
        "span_s": span,
        "settle_s": d.get("settle_s"),
        "units0": gate.get("units0"),
        "pre_fps15": gate.get("pre_fps15"),
        "gate_ok": gate.get("gate_ok", gate.get("ok")),
        "gate_span_s": gate.get("gate_span_s"),
        "fps_avg_json": stats.get("fps_avg"),
        "fps_p50_json": stats.get("fps_p50"),
        "logic_frames_json": stats.get("logic_frames"),
        "max_stall_json": stats.get("max_stall_s"),
        "n_edges": len(edges),
        "f0": edges[0][0] if edges else None,
        "f1": edges[-1][0] if edges else None,
        "df": (edges[-1][0] - edges[0][0]) if len(edges) >= 2 else None,
        "t_first_edge": edges[0][1] if edges else None,
        "t_last_edge": edges[-1][1] if edges else None,
        "t_last_sample": t[-1] if t else None,
        "n_samples": len(t),
        "live_fps": live,
        "live_fps_to_sample_end": live_from_t,
        "gap_s": gap,
        "gap_n": gap_n,
        "f_first_sample": f[0] if f else None,
        "f_last_sample": f[-1] if f else None,
    }


def main():
    rows = []
    bases = [("mirror", TRIPS), ("lead", LEAD_TRIPS)]
    seen_dirs = {}
    for tag, base in bases:
        if not os.path.isdir(base):
            print("MISSING BASE", base)
            continue
        files = sorted(glob.glob(os.path.join(base, "*", "measure_w*.json")))
        files += sorted(glob.glob(os.path.join(base, "measure_w*.json")))
        print("BASE %s : %d measure files (%d subdirs+root)" % (tag, len(files), 0))
        dirs = sorted(set(os.path.dirname(p) for p in files))
        meta = {}
        for dp in dirs:
            lm = launch_meta(dp)
            first, last = trip_time_from_fields(os.path.join(dp, "qc151_fields.json"))
            cc = carrier_count(dp)
            mtime = max((os.path.getmtime(p) for p in files if os.path.dirname(p) == dp),
                        default=None)
            meta[dp] = dict(lm, fields_ts_first=first, fields_ts_last=last,
                            carrier=cc, mtime=mtime)
            seen_dirs.setdefault((tag, dp), True)
        for p in files:
            dp = os.path.dirname(p)
            try:
                r = measure_rows(p, base)
            except Exception as e:
                print("READ_FAIL", p, repr(e))
                continue
            m = meta.get(dp, {})
            r["dir"] = os.path.relpath(dp, base).replace("\\", "/")
            r["harness_sha16"] = m.get("harness_sha16")
            r["harness_path"] = m.get("harness_path")
            r["argv_harness"] = m.get("argv_harness")
            r["launch_trip_id"] = m.get("trip_id_launch")
            r["fields_ts_first"] = m.get("fields_ts_first")
            r["fields_ts_last"] = m.get("fields_ts_last")
            r["dir_mtime"] = m.get("mtime")
            r["carrier"] = json.dumps(m.get("carrier"), ensure_ascii=False)
            r["base_tag"] = tag
            rows.append(r)

    out_csv = os.path.join(OUT, "census.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("WROTE %s rows=%d" % (out_csv, len(rows)))

    # 汇总
    from collections import Counter
    print("\n=== 目录数（有 measure 文件）===")
    for tag in ("mirror", "lead"):
        ds = sorted(set(r["dir"] for r in rows if r["base_tag"] == tag))
        print(" %s: %d dirs" % (tag, len(ds)))
    print("\n=== trip_id 集合大小 ===", len(set(r["trip_id"] for r in rows)))
    print("\n=== harness_sha16 分布（目录级）===")
    c = Counter()
    for (tag, dp) in seen_dirs:
        ds = sorted(set(r["dir"] for r in rows if r["base_tag"] == tag))
    dirs_info = {}
    for r in rows:
        dirs_info.setdefault((r["base_tag"], r["dir"]),
                             (r["harness_sha16"], r["argv_harness"], r["fields_ts_first"]))
    for k, v in sorted(dirs_info.items(), key=lambda x: (x[1][2] or "")):
        c[v[0]] += 1
        print("  %-28s %-18s %-30s %s" % (k[0] + "/" + k[1], v[0], (v[1] or "")[-46:], v[2]))
    print("\n=== harness 计数 ===", dict(c))


if __name__ == "__main__":
    main()
