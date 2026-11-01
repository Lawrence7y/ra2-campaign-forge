# -*- coding: utf-8 -*-
"""XVERIFY_B_20261101 · p03：簇内分裂消解（uptime 单调性）+ E12 _rec 定位 + 特例盘查。
python -I -B -X utf8。只读（写仅 OUTD）。
判据：同 BOOT 内 uptime（perf_counter 秒）必随墙钟单调增。若按 t_abs0 排序后 t0 严格单调
⇒ 同 BOOT（墙钟步进解释 epoch 分裂）；若后跑趟 t0 反而更小 ⇒ 中途真重启 ⇒ 异 BOOT。
"""
import json, os, time

ROOT = os.path.realpath(r"D:\Project\ra2-campaign-forge")
MIR  = os.path.realpath(os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip"))
OUTD = os.path.realpath(os.path.join(ROOT, "lead", "codex_round_20261030", "XVERIFY_B_20261101"))

def _gr(p):
    rp = os.path.realpath(p)
    if ".." in p or not rp.startswith(ROOT + os.sep):
        raise PermissionError(p)
    return rp

def jload(p):
    with open(_gr(p), encoding="utf-8", errors="replace") as f:
        return json.load(f)

def fmt(ep):
    if ep is None: return "-"
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ep)) + f".{int(round(ep % 1 * 1000)):03d}"

CLUSTERS = {
    "BOOT#0(10-16)": ["archive_T32","archive_T33","archive_T34","archive_T36","archive_T38","archive_T39",
                      "archive_T40","archive_T41","archive_T42","archive_T43","archive_T44",
                      "archive_T45","archive_T47","archive_T49"],
    "BOOT#1(10-19)": ["l1a_20261020","t55k_20261020"],
    "BOOT#4(10-30)": ["l3_20261023q","l3_20261023r"],
    "BOOT#5(10-31)": ["l3_20261031ha","l3_20261031hb","l3_1101v3a","l3_1101v3b"],
}
DIRS = {n: (os.path.join(MIR, n) if not n.startswith("t55k") else os.path.join(ROOT, "lead", n))
        for n in [f"archive_T{n}" for n in list(range(32, 46)) + [47]]}
DIRS["archive_T49"] = os.path.join(MIR, "archive_T49_u0800")
for n in ["l1a_20261020","l1c_20261021","l1d_20261021","l1e_20261021","l3_20261021","l1_20261023e4",
          "l3_20261023q","l3_20261023r","l3_20261031ha","l3_20261031hb","l3_1101v3a","l3_1101v3b",
          "l3_1101v3c","l3_1101v4a","l3_1101v4b"]:
    DIRS[n] = os.path.join(MIR, n)
DIRS["t55k_20261020"] = os.path.join(ROOT, "lead", "t55k_20261020")

def w0_of(d):
    p = os.path.join(d, "measure_w0.json")
    if not os.path.exists(p):
        return None
    j = jload(p)
    smp = j.get("samples") or {}
    t = smp.get("t") if isinstance(smp, dict) else None
    if isinstance(t, list) and t and j.get("t_abs0") is not None:
        return {"t0": t[0], "t_abs0": j["t_abs0"], "boot": j["t_abs0"] - t[0]}
    return None

print("== A. 簇内 uptime 单调性检验（同 BOOT 判定）==")
for cname, members in CLUSTERS.items():
    rows = []
    for m in members:
        w = w0_of(DIRS[m])
        if w:
            rows.append((m, w["t_abs0"], w["t0"], w["boot"]))
    rows.sort(key=lambda x: x[1])
    mono = all(rows[i+1][2] > rows[i][2] for i in range(len(rows)-1)) if len(rows) > 1 else None
    print(f"\n-- {cname} (按 t_abs0 升序) monotonic_t0={mono}")
    prev = None
    for m, ta, t0, be in rows:
        dt_t0 = f"+{t0-prev[2]:.3f}s" if prev else "   -    "
        dt_wall = f"+{ta-prev[1]:.3f}s" if prev else "   -    "
        step = f"  boot_epoch_delta_vs_prev={be-prev[3]:+.3f}s" if prev else ""
        print(f"   {m:16s} t_abs0={fmt(ta)} t0(uptime)={t0:12.3f}s  Δt0={dt_t0} Δwall={dt_wall} boot={fmt(be)}{step}")
        prev = (m, ta, t0, be)

print("\n== B. E12 驱动 _rec.json 定位与 boot 锚 ==")
recs = []
for dirpath, dirnames, filenames in os.walk(MIR):
    if "_rec.json" in filenames:
        recs.append(os.path.join(dirpath, "_rec.json"))
    dirnames[:] = [d for d in dirnames if d not in ("ct", "evidence", "_carrier_bak", "__pycache__")]
print(f"  found {len(recs)} _rec.json")
seen = {}
for p in sorted(recs):
    try:
        j = jload(p)
        bw = j.get("boot_wallclock_ms_at_start")
        trip = j.get("trip_id") or os.path.basename(os.path.dirname(p))
        rel = os.path.relpath(os.path.dirname(p), MIR)
        if bw:
            seen.setdefault(round(bw / 1000.0, 3), []).append(f"{rel} [{trip}]")
    except Exception as e:
        print("  err", p, e)
for be_s, trips in sorted(seen.items()):
    print(f"  boot_epoch={be_s:.3f} -> {fmt(be_s)}  n={len(trips)}")
    for t in trips:
        print(f"      {t}")

print("\n== C. l1_20261023e4 特查（趟名 1023 vs 推得 BOOT 10-26）==")
d = DIRS["l1_20261023e4"]
j = jload(os.path.join(d, "qc151_fields.json"))
meta = {}
ts_all = []
for ent in j:
    if ent.get("group") == "META":
        meta[ent.get("key")] = ent.get("value")
    if ent.get("ts"): ts_all.append(ent.get("ts"))
print(f"  trip_id={meta.get('trip_id')}")
print(f"  META.started={meta.get('started')}")
print(f"  ts_first={ts_all[0]} ts_last={ts_all[-1]} n={len(ts_all)}")
lr = jload(os.path.join(d, "_launch_result.json"))
print(f"  launch.rc={lr.get('rc')} duration={lr.get('duration_s')} trip_id={lr.get('trip_id')}")
tops = []
for fn in os.listdir(d):
    fp = os.path.join(d, fn)
    if os.path.isfile(fp):
        tops.append((os.path.getmtime(fp), fn))
tops.sort()
print(f"  mtime_min={fmt(tops[0][0])} ({tops[0][1]})")
print(f"  mtime_max={fmt(tops[-1][0])} ({tops[-1][1]})")

print("\n== D. v3c / v4b 的 h8 块与 qc151_run_log（寻找第二钟对）==")
for n in ["l3_1101v3c", "l3_1101v4b"]:
    d = DIRS[n]
    print(f"-- {n}")
    mw = os.path.join(d, "measure_w0.json")
    if os.path.exists(mw):
        j = jload(mw)
        h8 = j.get("h8")
        print(f"   h8 keys={list(h8.keys()) if isinstance(h8,dict) else h8}")
        if isinstance(h8, dict):
            for k, v in h8.items():
                print(f"     {k} = {str(v)[:150]}")
    p = os.path.join(d, "qc151_run_log.json")
    if os.path.exists(p):
        j = jload(p)
        s = json.dumps(j, ensure_ascii=False)
        print(f"   qc151_run_log: {s[:400]}")

print("\n== E. v4a 全目录文件清单（无 measure 时可用证据面）==")
d = DIRS["l3_1101v4a"]
for fn in sorted(os.listdir(d)):
    fp = os.path.join(d, fn)
    if os.path.isfile(fp):
        print(f"   {fn}  mtime={fmt(os.path.getmtime(fp))} size={os.path.getsize(fp)}")
    else:
        print(f"   [dir] {fn}")

print("\n(stdout only)")
