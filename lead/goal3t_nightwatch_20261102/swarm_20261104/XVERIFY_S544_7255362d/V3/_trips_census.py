import json, os, glob, collections

BASE = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/"
V3 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/"
dirs = sorted([d for d in os.listdir(BASE) if os.path.isdir(BASE + d)])
out = []
for d in dirs:
    lr = BASE + d + "/_launch_result.json"
    if not os.path.exists(lr):
        continue
    try:
        L = json.load(open(lr, encoding="utf-8"))
    except Exception:
        continue
    argv = L.get("argv") or []

    def val(flag):
        return argv[argv.index(flag) + 1] if flag in argv else None

    m0 = BASE + d + "/measure_w0.json"
    v = u0 = pf = fs = None
    if os.path.exists(m0):
        try:
            j = json.load(open(m0, encoding="utf-8"))
            v = j.get("verdict")
            g = j.get("gate") or {}
            u0 = g.get("units0")
            pf = g.get("pre_fps15")
            f = (j.get("samples") or {}).get("f")
            fs = (min(f), max(f), len(f)) if f else None
        except Exception as e:
            v = "READERR:" + str(e)[:40]
    known = {"--target-map", "--target-sha256", "--carrier", "--carrier-create-from",
             "--carrier-create-files", "--trip-id", "--out-dir", "--measure",
             "--fullscreen", "--evid-diff", "--probe-frames", "--h7-measure-start-frame",
             "--h8-wait-trace", "--h8-wait-hz"}
    out.append({
        "dir": d, "trip_id": L.get("trip_id"),
        "harness": os.path.basename(L.get("harness") or ""), "h_sha16": L.get("harness_sha16"),
        "dur_s": L.get("duration_s"), "h7frame": val("--h7-measure-start-frame"),
        "waittrace": "--h8-wait-trace" in argv, "waithz": val("--h8-wait-hz"),
        "measure": val("--measure"), "fullscreen": "--fullscreen" in argv,
        "nwin": len(glob.glob(BASE + d + "/measure_w*.json")),
        "verdict": v, "units0": u0, "pre_fps15": pf, "fsamples": fs,
        "map": (L.get("argv") or [None, None])[2],
        "extra_flags": [a for a in argv if a.startswith("--") and a not in known],
    })

hdr = ("%-22s %-32s %-24s %-8s %-8s %-8s %-5s %-4s %-18s %-7s %-9s %s" % (
    "dir", "trip_id", "harness", "h7frame", "trace", "dur_s", "nwin", "", "verdict", "units0", "pre_fps", "f(min,max,n)"))
print(hdr)
for r in out:
    print("%-22s %-32s %-24s %-8s %-8s %-8s %-5s %-4s %-18s %-7s %-9s %s" % (
        r["dir"], r["trip_id"], r["harness"], r["h7frame"], r["waittrace"], r["dur_s"],
        r["nwin"], "", r["verdict"], r["units0"], r["pre_fps15"], r["fsamples"]))

print("\n### (harness, h7frame, verdict) counts")
c = collections.Counter((r["harness"], r["h7frame"], str(r["verdict"])) for r in out)
for k, n in sorted(c.items(), key=lambda x: str(x[0])):
    print("   ", k, n)
print("\n### distinct target maps")
for k, n in collections.Counter(os.path.basename(str(r["map"])) for r in out).items():
    print("   ", k, n)
json.dump(out, open(V3 + "_trips_census.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
