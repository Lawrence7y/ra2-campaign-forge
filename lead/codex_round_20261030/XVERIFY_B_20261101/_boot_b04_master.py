# -*- coding: utf-8 -*-
"""XVERIFY_B_20261101 · p04 总分析：E12 锚表 / v3c·v4 墙钟 / 墙钟-uptime 自洽 /
一致性核验 / 双份目录比对。python -I -B -X utf8。只读（写仅 OUTD）。
"""
import json, os, time, hashlib

ROOT = os.path.realpath(r"D:\Project\ra2-campaign-forge")
MIR  = os.path.realpath(os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip"))
MQC  = os.path.realpath(os.path.join(ROOT, "lead", "qc161_u0400_trip"))
LEAD = os.path.realpath(os.path.join(ROOT, "lead"))
OUTD = os.path.realpath(os.path.join(ROOT, "lead", "codex_round_20261030", "XVERIFY_B_20261101"))

def _gr(p):
    rp = os.path.realpath(p)
    if ".." in p:
        raise PermissionError(p)
    if not (rp == ROOT or rp.startswith(ROOT + os.sep)):
        raise PermissionError(p)
    return rp

def _gw(p):
    rp = os.path.realpath(p)
    if ".." in p:
        raise PermissionError(p)
    if not rp.startswith(OUTD + os.sep):
        raise PermissionError(p)
    return rp

def jload(p):
    with open(_gr(p), encoding="utf-8", errors="replace") as f:
        return json.load(f)

def sha256(p):
    h = hashlib.sha256()
    with open(_gr(p), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fmt(ep):
    if ep is None:
        return "-"
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ep)) + f".{int(round(ep % 1 * 1000)):03d}"

def parse_iso(s):
    if not s:
        return None
    try:
        return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None

TRIP_DIRS = {}
for n in ["l1a_20261020","l1c_20261021","l1d_20261021","l1e_20261021","l3_20261021","l1_20261023e4",
          "l3_20261023q","l3_20261023r","l3_20261031ha","l3_20261031hb","l3_1101v3a","l3_1101v3b",
          "l3_1101v3c","l3_1101v4a","l3_1101v4b"] + [f"archive_T{k}" for k in list(range(32,46))+[47]]:
    TRIP_DIRS[n] = os.path.join(MIR, n)
TRIP_DIRS["t55k_20261020"] = os.path.join(LEAD, "t55k_20261020")
TRIP_DIRS["archive_T49"] = os.path.join(MIR, "archive_T49_u0800")

DERIVED_BOOT = {}

def w_data(d):
    out = {}
    for w in ("w0","w1","w2"):
        p = os.path.join(d, f"measure_{w}.json")
        if not os.path.exists(p):
            continue
        j = jload(p)
        smp = j.get("samples") or {}
        t = smp.get("t") if isinstance(smp, dict) else None
        e = {"t_abs0": j.get("t_abs0"), "hz": j.get("hz"),
             "map_sha256": j.get("map_sha256"), "gamemd_sha256": j.get("gamemd_sha256"),
             "verdict": j.get("verdict"), "error": str(j.get("error") or "")[:60]}
        g = j.get("gate") or {}
        e["units0"] = g.get("units0"); e["pre_fps15"] = g.get("pre_fps15"); e["gate_ok"] = g.get("ok")
        st = j.get("stats") or {}
        e["fps_avg"] = st.get("fps_avg"); e["stall"] = st.get("max_stall_s")
        cnt = j.get("counters")
        rows = None
        if isinstance(cnt, dict):
            rows = cnt.get("rows") or cnt.get("samples")
        elif isinstance(cnt, list):
            rows = cnt
        if rows and isinstance(rows[0], dict):
            e["units_first"] = rows[0].get("units"); e["units_last"] = rows[-1].get("units")
            e["cnt_n"] = len(rows)
        if isinstance(t, list) and t and e["t_abs0"] is not None:
            e["t0"] = t[0]; e["boot"] = e["t_abs0"] - t[0]
        out[w] = e
    return out

print("== A. E12 驱动 _rec.json 锚表（主仓 lead/qc161_u0400_trip）==")
recs = []
for base in ["c2ab_x","c2ab","ab24"]:
    b = os.path.join(MQC, base)
    if not os.path.isdir(b):
        continue
    for dp, dns, fns in os.walk(b):
        if "_rec.json" in fns:
            recs.append(os.path.join(dp, "_rec.json"))
        dns[:] = [x for x in dns if x not in ("ct","evidence","_carrier_bak","__pycache__")]
seen = {}
for p in sorted(recs):
    try:
        j = jload(p)
        bw = j.get("boot_wallclock_ms_at_start")
        if bw:
            rel = os.path.relpath(os.path.dirname(p), MQC)
            seen.setdefault(round(bw/1000.0, 3), []).append(rel)
    except Exception:
        pass
print(f"  ({len(recs)} 个 _rec.json, {len(seen)} 个不同 boot)")
for be_s, trips in sorted(seen.items()):
    print(f"  boot={be_s:.3f} -> {fmt(be_s)}  n={len(trips)}")
    for t in trips[:6]:
        print(f"      {t}")
    if len(trips) > 6:
        print(f"      (+{len(trips)-6} more)")

print("\n== B. 无 t0 趟（v3c/v4b）与无 measure 趟（v4a）墙钟锚 ==")
for n in ["l3_1101v3c","l3_1101v4a","l3_1101v4b"]:
    d = TRIP_DIRS[n]
    print(f"-- {n}")
    mw = os.path.join(d, "measure_w0.json")
    if os.path.exists(mw):
        j = jload(mw)
        ta = j.get("t_abs0")
        print(f"   measure_w0.t_abs0={ta} -> {fmt(ta)}  verdict={j.get('verdict')}")
        print(f"   err={str(j.get('error') or '')[:70]}")
    p = os.path.join(d, "qc151_fields.json")
    if os.path.exists(p):
        j = jload(p)
        meta = {}
        for e in j:
            if e.get("group") == "META":
                meta[e.get("key")] = e.get("value")
        tss = [e.get("ts") for e in j if e.get("ts")]
        print(f"   qc151 META.started={meta.get('started')} trip_id={meta.get('trip_id')} ts_last={tss[-1] if tss else None}")
    lr = os.path.join(d, "_launch_result.json")
    if os.path.exists(lr):
        j = jload(lr)
        print(f"   launch rc={j.get('rc')} dur={j.get('duration_s')}s harness_sha16={j.get('harness_sha16')}")
    top = []
    for fn in os.listdir(d):
        fp = os.path.join(d, fn)
        if os.path.isfile(fp):
            top.append((os.path.getmtime(fp), fn))
    top.sort()
    print(f"   mtime {fmt(top[0][0])} ({top[0][1]}) | {fmt(top[-1][0])} ({top[-1][1]})")

print("\n== C. 逐趟 墙钟-uptime 自洽（有推导 boot 的趟）==")
print(f"  {'trip':16s} {'boot(derived)':32s} {'META.started':21s} {'meta-boot(h)':>12s} {'w_abs0-meta(s)':>14s} {'wn':>3s} 判")
rows_c = {}
for n, d in TRIP_DIRS.items():
    ws = w_data(d)
    b0 = ws.get("w0", {}).get("boot")
    if b0 is None:
        continue
    DERIVED_BOOT[n] = b0
    meta_start = None
    p = os.path.join(d, "qc151_fields.json")
    if os.path.exists(p):
        j = jload(p)
        for e in j:
            if e.get("group") == "META" and e.get("key") == "started":
                meta_start = e.get("value")
    me = parse_iso(meta_start)
    ta = ws["w0"]["t_abs0"]
    mb = (me - b0) / 3600 if me else None
    am = (ta - me) if me else None
    okflag = "OK" if (me and am is not None and 0 < am < 3600 and 0 < mb < 60) else ("CHECK" if me else "no-meta")
    rows_c[n] = (b0, meta_start, mb, am)
    mbs = f"{mb:12.2f}" if mb is not None else f"{'-':>12s}"
    ams = f"{am:14.1f}" if am is not None else f"{'-':>14s}"
    print(f"  {n:16s} {fmt(b0):32s} {str(meta_start)[:19]:21s} {mbs} {ams} {len(ws):3d} {okflag}")

print("\n== D. 一致性核验：地图/gamemd/ini/协议/units ==")
mothers = {"L1": os.path.join(MIR, "_src_L1_sf8_20261020"), "L3": os.path.join(MIR, "_src_L3_sf10c_20261021")}
mhash = {}
for k, mp in mothers.items():
    for f in ["XMP29U2.MAP","gamemd.exe","ra2render.ini","ra2md.ini","ddraw.ini","game.exe"]:
        fp = os.path.join(mp, f)
        if os.path.exists(fp):
            mhash[f"{k}:{f}"] = sha256(fp)
print("  母本哈希（亲算）：")
for k in sorted(mhash):
    print(f"    {k:22s} {mhash[k]}")

print()
hdr = f"  {'trip':16s} {'map(w0)':9s} {'gamemd':9s} {'md5?':4s} {'ini':12s} {'hz':>4s} MFSE {'KR':>2s} {'MSF':>4s} {'u0':>5s} {'pre':>6s} {'w0 units':>12s} {'w1 units':>12s} {'w2 units':>12s} verdicts"
print(hdr)
for n, d in TRIP_DIRS.items():
    ws = w_data(d)
    if not ws:
        cm = os.path.join(d, "carrier_manifest_pre_delete.json")
        inis = "---"
        if os.path.exists(cm):
            j = jload(cm)
            fs = j.get("files") or {}
            def m3(k):
                for kk, mv in mhash.items():
                    if kk.split(":")[1] == k and fs.get(k, {}).get("sha256") == mv:
                        return kk.split(":")[0]
                return "?" if k in fs else "-"
            inis = f"{m3('ra2render.ini')}/{m3('ra2md.ini')}/{m3('ddraw.ini')}"
        av = []
        lr = os.path.join(d, "_launch_result.json")
        if os.path.exists(lr):
            av = jload(lr).get("argv") or []
        msf = "-"
        if "--h7-measure-start-frame" in av:
            msf = av[av.index("--h7-measure-start-frame") + 1]
        fl = f"M={('Y' if '--measure' in av else '-')} F={('Y' if '--fullscreen' in av else '-')} E={('Y' if '--evid-diff' in av else '-')}"
        print(f"  {n:16s} {'(no measure)':9s} {'-':9s} {'-':4s} {inis:12s} {'-':>4s} {fl} KR={('Y' if '--h7-keep-rect-wait' in av else '-')} MSF={msf}")
        continue
    w0 = ws["w0"]
    cm = os.path.join(d, "carrier_manifest_pre_delete.json")
    inis = "---"
    if os.path.exists(cm):
        j = jload(cm)
        fs = j.get("files") or {}
        def m2(k):
            for kk, mv in mhash.items():
                if kk.split(":")[1] == k and fs.get(k, {}).get("sha256") == mv:
                    return kk.split(":")[0]
            return "?" if k in fs else "-"
        inis = f"{m2('ra2render.ini')}/{m2('ra2md.ini')}/{m2('ddraw.ini')}"
    mapw = str(w0.get("map_sha256"))[:8] if w0.get("map_sha256") else "-"
    gmd = str(w0.get("gamemd_sha256)) "][:8]) if w0.get("gamemd_sha256") else "-"
    gfull = ""
    if w0.get("gamemd_sha256"):
        for kk, mv in mhash.items():
            if kk.endswith("gamemd.exe") and mv == w0["gamemd_sha256"]:
                gfull = kk.split(":")[0]
    av = []
    lr = os.path from_file
    print("placeholder")
