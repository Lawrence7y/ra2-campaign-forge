# -*- coding: utf-8 -*-
"""XVERIFY_B_20261101 · BOOT 证据员 p01：逐趟证据盘点 + boot_epoch 亲算。
只读全仓（除本写域）。python -I -B -X utf8。
证据锚：measure_w*.json 内 t_abs0（墙钟 epoch 秒）与 samples.t[0]（time.perf_counter，
开机起秒）为同一时刻 ⇒ boot_epoch = t_abs0 - t[0]。跨趟一致即同 BOOT。
路径纪律：全部路径经 realpath 规范化；读限 ROOT 内；写限 OUTD 内；禁 ..。
"""
import json, os, sys, time

ROOT = os.path.realpath(r"D:\Project\ra2-campaign-forge")
MIR  = os.path.realpath(os.path.join(ROOT, "out", "re_work", "work_chain", "continue_x", "unused"))  # placeholder, fixed below
MIR  = os.path.realpath(os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip"))
MQC  = os.path.realpath(os.path.join(ROOT, "lead", "qc161_u0400_trip"))
LEAD = os.path.realpath(os.path.join(ROOT, "lead"))
OUTD = os.path.realpath(os.path.join(ROOT, "lead", "codex_round_20261030", "XVERIFY_B_20261101"))

def _guard_read(p):
    rp = os.path.realpath(p)
    if ".." in p or not (rp == ROOT or rp.startswith(ROOT + os.sep)):
        raise PermissionError(f"read outside ROOT: {p}")
    return rp

def _guard_write(p):
    rp = os.path.realpath(p)
    if ".." in p or not rp.startswith(OUTD + os.sep):
        raise PermissionError(f"write outside OUTD: {p}")
    return rp

def jload(p):
    try:
        with open(_guard_read(p), encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception as e:
        return {"__err__": repr(e)}

def mt(p):
    try: return os.path.getmtime(_guard_read(p))
    except Exception: return None

def fmt_ts(ep):
    if ep is None: return None
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ep)) + "+08:00"

HASH_KEYS = ["ra2render.ini","ra2md.ini","ddraw.ini","XMP29U2.MAP","gamemd.exe","game.exe","ra2md.exe","ra2render.dll"]

TRIPS = [
    ("l1a_20261020",  [os.path.join(MIR,"l1a_20261020"), os.path.join(LEAD,"l1a_20261020")]),
    ("t55k_20261020", [os.path.join(LEAD,"t55k_20261020"), os.path.join(MIR,"t55k_20261020")]),
    ("l1c_20261021",  [os.path.join(MQC,"l1c_20261021"), os.path.join(MIR,"l1c_20261021")]),
    ("l1d_20261021",  [os.path.join(MQC,"l1d_20261021"), os.path.join(MIR,"l1d_20261021")]),
    ("l1e_20261021",  [os.path.join(MQC,"l1e_20261021"), os.path.join(MIR,"l1e_20261021")]),
    ("l3_20261021",   [os.path.join(MQC,"l3_20261021"), os.path.join(MIR,"l3_20261021")]),
    ("l1_20261023e4", [os.path.join(MIR,"l1_20261023e4")]),
    ("l3_20261023q",  [os.path.join(MIR,"l3_20261023q")]),
    ("l3_20261023r",  [os.path.join(MIR,"l3_20261023r")]),
    ("l3_20261031ha", [os.path.join(MIR,"l3_20261031ha")]),
    ("l3_20261031hb", [os.path.join(MIR,"l3_20261031hb")]),
    ("l3_1101v3a",    [os.path.join(MIR,"l3_1101v3a")]),
    ("l3_1101v3b",    [os.path.join(MIR,"l3_1101v3b")]),
    ("l3_1101v3c",    [os.path.join(MIR,"l3_1101v3c")]),
    ("l3_1101v4a",    [os.path.join(MIR,"l3_1101v4a")]),
    ("l3_1101v4b",    [os.path.join(MIR,"l3_1101v4b")]),
] + [(f"archive_T{n}", [os.path.join(MIR,f"archive_T{n}")]) for n in list(range(32,46))+[47,49]]

def probe_dir(d):
    d = _guard_read(d)
    r = {"dir": d, "exists": os.path.isdir(d)}
    if not r["exists"]:
        return r
    r["measures"] = {}
    for w in ("w0","w1","w2"):
        p = os.path.join(d, f"measure_{w}.json")
        if not os.path.exists(p): continue
        j = jload(p)
        if not isinstance(j, dict) or "__err__" in j:
            r["measures"][w] = {"__err__": str(j.get("__err__")) if isinstance(j, dict) else "not-dict"}
            continue
        e = {}
        e["t_abs0"] = j.get("t_abs0"); e["t_clock"] = j.get("t_clock"); e["hz"] = j.get("hz")
        e["map_sha256"] = j.get("map_sha256"); e["gamemd_sha256"] = j.get("gamemd_sha256")
        e["window"] = j.get("window"); e["span_s"] = j.get("span_s")
        g = j.get("gate") or {}
        e["gate_units0"] = g.get("units0"); e["gate_pre_fps15"] = g.get("pre_fps15"); e["gate_ok"] = g.get("ok")
        e["verdict"] = j.get("verdict"); e["error"] = j.get("error")
        st = j.get("stats") or {}
        e["fps_avg"] = st.get("fps_avg"); e["max_stall_s"] = st.get("max_stall_s")
        e["frame_ms_p50"] = st.get("frame_ms_p50"); e["frame_ms_max"] = st.get("frame_ms_max")
        cnt = j.get("counters")
        if isinstance(cnt, dict):
            e["counters_type"] = "dict"
            rows = cnt.get("rows") or cnt.get("samples") or []
            e["counters_rows_n"] = len(rows) if hasattr(rows, "__len__") else None
            if rows and isinstance(rows[0], dict):
                e["units_first"] = rows[0].get("units"); e["units_last"] = rows[-1].get("units")
        elif isinstance(cnt, list):
            e["counters_type"] = "list"; e["counters_rows_n"] = len(cnt)
            if cnt and isinstance(cnt[0], dict):
                e["units_first"] = cnt[0].get("units"); e["units_last"] = cnt[-1].get("units")
        smp = j.get("samples")
        if isinstance(smp, dict) and isinstance(smp.get("t"), list) and smp["t"]:
            t0 = smp["t"][0]
            e["t0_perf"] = t0
            if e["t_abs0"] is not None:
                e["boot_epoch"] = e["t_abs0"] - t0
                e["boot_local"] = fmt_ts(e["boot_epoch"])
        r["measures"][w] = e
    p = os.path.join(d, "qc151_fields.json")
    if os.path.exists(p):
        j = jload(p)
        if isinstance(j, list):
            meta = {}; ts_all = []; boot_keys = []
            for ent in j:
                ts = ent.get("ts")
                if ts: ts_all.append(ts)
                if ent.get("group") == "META": meta[ent.get("key")] = ent.get("value")
                k = (ent.get("key","") + " " + ent.get("note","")).lower()
                if "boot" in k or "uptime" in k:
                    boot_keys.append((ent.get("group"), ent.get("key"), str(ent.get("value"))[:80]))
            r["qc151"] = {
                "n_entries": len(j),
                "META_started": meta.get("started"),
                "trip_id": meta.get("trip_id"),
                "fullscreen": meta.get("fullscreen"),
                "measure_start_frame": meta.get("h7_measure_start_frame", meta.get("measure_start_frame")),
                "ts_first": ts_all[0] if ts_all else None,
                "ts_last": ts_all[-1] if ts_all else None,
                "boot_uptime_keys": boot_keys[:10],
            }
        else:
            r["qc151"] = {"__err__": "not-list"}
    p = os.path.join(d, "_launch_result.json")
    if os.path.exists(p):
        j = jload(p)
        argv = j.get("argv") or []
        flags = {}
        for fl in ["--measure","--fullscreen","--evid-diff","--probe-frames","--h7-measure-start-frame",
                   "--h8-wait-trace","--h7-keep-rect-wait","--allow-loader","--trip-id","--target-map","--target-sha256"]:
            if fl in argv:
                i = argv.index(fl)
                flags[fl] = argv[i+1] if (i+1 < len(argv) and not str(argv[i+1]).startswith("--")) else True
        r["launch"] = {
            "rc": j.get("rc"), "duration_s": j.get("duration_s"), "trip_id": j.get("trip_id"),
            "harness": j.get("harness"), "harness_sha16": j.get("harness_sha16"),
            "carriers_deleted": j.get(" carriers_deleted") if False else j.get("carriers_deleted"),
            "leftover_procs": j.get("leftover_procs"), "argv_n": len(argv), "flags": flags,
        }
    p = os.path.join(d, "carrier_manifest_pre_delete.json")
    if os.path.exists(p):
        j = jload(p)
        files = j.get("files") or {}
        hs = {}
        if isinstance(files, dict):
            for k in HASH_KEYS:
                if k in files and isinstance(files[k], dict):
                    hs[k] = files[k].get("sha256")
        r["carrier"] = {"file_count": j.get("file_count"), "manifest_ok": j.get("manifest_ok"),
                        "created_at": j.get("created_at"), "sha": hs}
    r["has_rec_json"] = os.path.exists(os.path.join(d, "_rec.json"))
    r["has_fs_boot_probe_png"] = os.path.exists(os.path.join(d, "fs_boot_probe.png"))
    tops = []
    try:
        for fn in os.listdir(d):
            fp = os.path.join(d, fn)
            if os.path.isfile(fp):
                tops.append((mt(fp), fn))
    except Exception:
        pass
    if tops:
        tops = [t for t in tops if t[0] is not None]
        tops.sort()
        r["mtime_min"] = {"ts": fmt_ts(tops[0][0]), "file": tops[0][1]}
        r["mtime_max"] = {"ts": fmt_ts(tops[-1][0]), "file": tops[-1][1]}
    return r

def main():
    out = {}
    for name, cands in TRIPS:
        cands = [c for c in cands if c]
        entry = {"candidates": []}
        chosen = None
        for cd in cands:
            pr = probe_dir(cd)
            entry["candidates"].append(pr)
            if pr["exists"] and chosen is None:
                chosen = pr
        entry["primary"] = chosen
        out[name] = entry
    op = _guard_write(os.path.join(OUTD, "_raw", "p01_collect.json"))
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print(f"{'trip':16s} {'boot_w0':32s} {'boot_w1':32s} {'boot_w2':32s} units0  pre     flags")
    for name, _ in TRIPS:
        pr = out[name]["primary"]
        if not pr or not pr.get("exists"):
            print(f"{name:16s} DIR-MISSING")
            continue
        ms = pr.get("measures", {})
        def bs(w):
            e = ms.get(w) or {}
            bl = e.get("boot_local") or "-"
            return bl if e.get("boot_epoch") is not None else ("(no t_abs0)" if e else "-")
        gu = ms.get("w0", {}).get("gate_units0")
        gp = ms.get("w0", {}).get("gate_pre_fps15")
        fl = list((pr.get("launch") or {}).get("flags", {}).keys()) if pr.get("launch") else []
        print(f"{name:16s} {bs('w0'):32s} {bs('w1'):32s} {bs('w2'):32s} {str(gu):7s} {str(gp):7s} {','.join(fl)}")
    print("\nwrite:", op)

if __name__ == "__main__":
    main()
