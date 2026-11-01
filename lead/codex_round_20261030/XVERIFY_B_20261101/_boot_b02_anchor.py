# -*- coding: utf-8 -*-
"""XVERIFY_B_20261101 · p02：boot_epoch 精算 + 跨趟聚类 + E12/boot_fp 交叉锚。
python -I -B -X utf8。只读（写仅 OUTD）。
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

TRIP_DIRS = {}
for _n, _sub in [("l1a_20261020", "l1a_20261020"),
                 ("l1c_20261021", "l1c_20261021"),
                 ("l1d_20261021", "l1d_20261021"),
                 ("l1e_20261021", "l1e_20261021"),
                 ("l3_20261021", "l3_20261021"),
                 ("l1_20261023e4", "l1_20261023e4"),
                 ("l3_20261023q", "l3_20261023q"),
                 ("l3_20261023r", "l3_20261023r"),
                 ("l3_20261031ha", "l3_20261031ha"),
                 ("l3_20261031hb", "l3_20261031hb"),
                 ("l3_1101v3a", "l3_1101v3a"),
                 ("l3_1101v3b", "l3_1101v3b"),
                 ("l3_1101v3c", "l3_1101v3c"),
                 ("l3_1101v4a", "l3_1101v4a"),
                 ("l3_1101v4b", "l3_1101v4b")]:
    TRIP_DIRS[_n] = os.path.join(MIR, _sub)
TRIP_DIRS["t55k_20261020"] = os.path.join(ROOT, "lead", "t55k_20261020")
for _n in [f"archive_T{n}" for n in list(range(32, 46)) + [47]]:
    TRIP_DIRS[_n] = os.path.join(MIR, _n)
TRIP_DIRS["archive_T49"] = os.path.join(MIR, "archive_T49_u0800")

def boot_of(d):
    res = {}
    for w in ("w0", "w1", "w2"):
        p = os.path.join(d, f"measure_{w}.json")
        if not os.path.exists(p):
            continue
        j = jload(p)
        ta = j.get("t_abs0") if isinstance(j, dict) else None
        smp = j.get("samples") if isinstance(j, dict) else None
        t = smp.get("t") if isinstance(smp, dict) else None
        if ta is not None and isinstance(t, list) and t:
            res[w] = (ta - t[0], t[0], ta, j.get("t_clock"))
    return res

print("== A. 逐趟 boot_epoch（每窗，t_clock 口径披露）==")
allb = {}
for name, d in TRIP_DIRS.items():
    if not os.path.isdir(d):
        print(f"{name:16s} DIR-MISSING {os.path.basename(d)}")
        continue
    b = boot_of(d)
    allb[name] = b
    if not b:
        mw0 = os.path.join(d, "measure_w0.json")
        if os.path.exists(mw0):
            j = jload(mw0)
            if isinstance(j, dict):
                print(f"{name:16s} measure_w0 KEYS={list(j.keys())}")
                for k in ("t_abs0", "t_clock", "hz", "window", "span_s", "verdict", "error"):
                    if k in j:
                        print(f"                   {k} = {str(j.get(k))[:80]}")
                smp = j.get("samples")
                th = str(smp.get("t")[:2])[:60] if isinstance(smp, dict) and isinstance(smp.get("t"), list) else "-"
                print(f"                   samples type={type(smp).__name__} t_head={th}")
        else:
            print(f"{name:16s} no measure_w0 (其他 measure: "
                  f"{[f for f in os.listdir(d) if f.startswith('measure_') and f.endswith('.json')]})")
        continue
    parts = []
    for w in ("w0", "w1", "w2"):
        if w in b:
            be, t0, ta, tc = b[w]
            parts.append(f"{w}: {fmt(be)} t0={t0:.3f} t_clock={tc}")
    eps = [v[0] for v in b.values()]
    spread = (max(eps) - min(eps)) * 1000 if len(eps) > 1 else None
    print(f"{name:16s} " + (" | ".join(f"{w}: {fmt(v[0])}" for w, v in sorted(b.items())))
          + (f"  intra_spread={spread:.1f}ms" if spread is not None else ""))

print("\n== B. 跨趟聚类（相邻 epoch 差 <3 s 并簇）==")
flat = []
for name, b in allb.items():
    if not b:
        continue
    eps = [v[0] for v in b.values()]
    flat.append((name, min(eps), max(eps)))
flat.sort(key=lambda x: x[1])
clusters = []
for name, lo, hi in flat:
    if clusters and lo - clusters[-1]["hi"] < 3.0:
        c = clusters[-1]
        c["members"].append(name)
        c["hi"] = max(c["hi"], hi)
    else:
        clusters.append({"lo": lo, "hi": hi, "members": [name]})
for i, c in enumerate(clusters):
    span = (c["hi"] - c["lo"]) * 1000
    print(f"BOOT#{i}: {fmt(c['lo'])} .. {fmt(c['hi'])}  离散 {span:.0f} ms  成员: {', '.join(c['members'])}")

print("\n== C. 交叉锚：E12 驱动 _rec.json 的 boot_wallclock_ms_at_start ==")
rec_files = []
for base in [os.path.join(MIR, "c2ab_x"), os.path.join(MIR, "d09a_c2_candidate"), os.path.join(MIR, "d09b")]:
    if os.path.isdir(base):
        for dn in sorted(os.listdir(base)):
            p = os.path.join(base, dn, "_rec.json")
            if os.path.isfile(p):
                rec_files.append(p)
seen = {}
for p in rec_files:
    try:
        j = jload(p)
        bw = j.get("boot_wallclock_ms_at_start")
        trip = j.get("trip_id") or os.path.basename(os.path.dirname(p))
        if bw:
            seen.setdefault(round(bw / 1000.0, 3), []).append(trip)
    except Exception as e:
        print("  read err", os.path.basename(p), e)
for be_s, trips in sorted(seen.items()):
    print(f"  boot_epoch={be_s:.3f} -> {fmt(be_s)}  trips={trips}")

print("\n== D. boot_fp_20261023 锚 ==")
bfp = os.path.join(MIR, "boot_fp_20261023")
if os.path.isdir(bfp):
    for fn in sorted(os.listdir(bfp)):
        if fn.endswith(".json") and fn.startswith("boot_fingerprint"):
            j = jload(os.path.join(bfp, fn))
            sysj = j.get("system") or {}
            print(f"  {fn}: boot_key={sysj.get('boot_key')} boot_local={sysj.get('boot_time_local_from_tick')} "
                  f"captured={j.get('captured_at_local')} uptime_ms={sysj.get('uptime_ms_tick')}")
else:
    print("  no boot_fp dir")

print("\n(stdout only)")
