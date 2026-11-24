import json, os, collections

ROOT = "D:/Project/ra2-campaign-forge/"
rows = json.load(open(ROOT + "lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/_census_measure.json", encoding="utf-8"))

na = [r for r in rows if r.get("verdict") == "no_advance"]
print("no_advance rows:", len(na))
buckets = collections.Counter()
for r in na:
    key = (r.get("units0"), r.get("pre_fps15"))
    buckets[(r["trip_id"], r["units0"], r["pre_fps15"], r["fmin"], r["fmax"], r["nsamples"], r["span_s"])] += 1
print("%-34s %-7s %-9s %-6s %-6s %-5s %s" % ("trip_id", "units0", "pre_fps", "fmin", "fmax", "nsmp", "path-tail"))
for k in sorted(buckets, key=lambda x: str(x[0])):
    trip, u0, pf, fmin, fmax, ns, sp = k
    ps = [r["path"] for r in na if r["trip_id"] == trip]
    tail = ps[0].replace(ROOT, "")
    print("%-34s %-7s %-9s %-6s %-6s %-5s %s" % (trip, u0, pf, fmin, fmax, ns, tail.replace("/measure_w0.json", "")))

print()
print("### no_advance rows where fmax == 0 (frame never left 0):")
for r in na:
    if r.get("fmax") == 0:
        print("   ", r["trip_id"], r["path"].replace(ROOT, ""), "units0=", r["units0"], "pre_fps=", r["pre_fps15"], "nsamples=", r["nsamples"])

print()
print("### rows with error/None fields (not measurable):")
for r in rows:
    if r.get("readerr") or r.get("notdict"):
        print("   ", r["path"].replace(ROOT, ""), r)
