import json, os

BASE = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/"
V3 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/"
# gate predicate as implemented in qc151_trip.harness8_v4.py:5183-5199
GATE_FPS15_MIN = 3.0
GATE_SPAN_S = 1.5
SETTLE_S = 4.0

DIRS = ["l1_20261023e1", "l1_20261023hb", "l1_20261023k", "l3_1101v4f", "l3_1101v4g",
        "l3_1101v4c", "l3_1101v4d", "l3_1101v4e", "l3_1101v3a", "l3_1101v3b",
        "l1_20261023e4", "l3_20261023q", "l3_20261023r", "l3_20261031hb"]

print("%-16s %-9s %-6s %-9s %-6s %-6s %-9s %-9s %s" % (
    "dir", "verdict", "h7flag", "pre_fps", "units0", "f0", "firstUnits>0_s", "firstF>0_s", "gate_replay"))
for d in DIRS:
    p = BASE + d + "/measure_w0.json"
    if not os.path.exists(p):
        print(d, "no measure_w0")
        continue
    j = json.load(open(p, encoding="utf-8"))
    g = j["gate"]
    f = j["samples"]["f"]
    t = j["samples"]["t"]
    t0 = t[0]
    # independent recompute of pre_fps15 over last 1.5s of the settle
    cut = t0 + SETTLE_S - GATE_SPAN_S
    pts = [(x - t0, y) for x, y in zip(t, f) if x >= cut]
    recompute = (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0]) if len(pts) >= 2 and pts[-1][0] > pts[0][0] else None
    ctr = j["counters"]
    units0_from_first_row = next((r["units"] for r in ctr if r.get("units") is not None), None)
    fu = next((round(r["t_rel"], 3) for r in ctr if (r.get("units") or 0) > 0), None)
    ff = next((round(x - t0, 3) for x, y in zip(t, f) if y > 0), None)
    lr = json.load(open(BASE + d + "/_launch_result.json", encoding="utf-8"))
    h7 = "--h7-measure-start-frame" in lr["argv"]
    gate_replay = bool(recompute is not None and recompute >= GATE_FPS15_MIN and units0_from_first_row is not None and units0_from_first_row > 0)
    print("%-16s %-9s %-6s %-9s %-6s %-6s %-9s %-9s %s" % (
        d, j["verdict"], h7, round(recompute, 3) if recompute is not None else None,
        units0_from_first_row, f[0], fu, ff, "PASS" if gate_replay else "FAIL(units0=0)" if units0_from_first_row == 0 else ("FAIL(fps)" if not gate_replay else "PASS")))
    if j["verdict"] == "no_advance":
        # for no_advance the saved w0 JSON *is* the settle payload => reproducible
        assert g["units0"] == units0_from_first_row, (d, g["units0"], units0_from_first_row)
        assert abs(round(recompute, 3) - g["pre_fps15"]) < 1e-3, (d, recompute, g["pre_fps15"])
print("\n(for every no_advance trip above the w0 payload IS the settle span: recomputed pre_fps15 and units0 match gate exactly)")
