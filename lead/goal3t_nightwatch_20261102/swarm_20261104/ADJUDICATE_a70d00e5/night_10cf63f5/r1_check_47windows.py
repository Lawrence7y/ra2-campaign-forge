# -*- coding: utf-8 -*-
# 复核 R1 混杂控制表：3 行定点抽查 + 47 窗全量一致性核对
# 抽查行（含 1 持续低速 + 2 对照）：
#   S1 l3_20261031hb/measure_w1.json  (持续低速, 候选件称 harness=dd5459fe0cf3461c/harness8.py)
#   C1 archive_T41/measure_w0.json    (对照, 候选件称 harness 缺/缺)
#   C2 l3_1101v4d/measure_w0.json     (对照, 候选件称 harness=38244d2907e7f7fa/harness8_v4.py)
# 全量核对：47 窗 map_sha256 趟内一致 / _launch_result.json harness_sha16 缺格数=25 /
#          frame_edges 首末帧号与 samples.f 一致 / gate.ok+verdict+units0+settle_s 非空
import json, hashlib
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
SPOT = [
    ("S1", "l3_20261031hb/measure_w1.json", dict(map_sha256="f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36",
        harness_sha16="dd5459fe0cf3461c", harness="D:\\Project\\ra2-campaign-forge\\lead\\goal1_harness8_20261031\\qc151_trip.harness8.py",
        frames=(607, 725), gate_ok=True, verdict="ok", units0=1347, settle_s=0.0)),
    ("C1", "archive_T41/measure_w0.json", dict(map_sha256="9a2495268be03f17f9599c9467c477f9529bb1f59f27f7e39e65562f95b57723",
        harness_sha16=None, harness=None, frames=(132, 860), gate_ok=True, verdict="ok", units0=242, settle_s=4.0)),
    ("C2", "l3_1101v4d/measure_w0.json", dict(map_sha256="f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36",
        harness_sha16="38244d2907e7f7fa", harness="D:\\Project\\ra2-campaign-forge\\lead\\goal1_harness8_20261031\\qc151_trip.harness8_v4.py",
        frames=(920, 1699), gate_ok=True, verdict="ok", units0=1225, settle_s=4.0)),
]
# 候选件 4.3 声明 harness 缺的趟（4.2/4.1 表中 缺/缺 的 trip 目录）
CLAIM_MISSING = ["archive_T38", "archive_T39", "archive_T40", "archive_T41", "archive_T42",
                 "archive_T44", "archive_T45", "l1a_20261020", "l1c_20261021", "l1d_20261021",
                 "l1e_20261021", "l3_20261021", "t55k_20261020"]
# 候选件声明有 harness_sha16 的（trip → 声明值）
CLAIM_HAS = {"l3_1101v3a": "37a7c9cdf2ca97e3", "l3_1101v3b": "37a7c9cdf2ca97e3",
             "l3_1101v4c": "38244d2907e7f7fa", "l3_1101v4d": "38244d2907e7f7fa",
             "l3_1101v4e": "38244d2907e7f7fa", "l3_20261031hb": "dd5459fe0cf3461c",
             "l1_20261023e4": "d019e8beecfb5fd8", "l3_20261023q": "d019e8beecfb5fd8",
             "l3_20261023r": "d019e8beecfb5fd8"}
# 47 窗 = 22 steady + 25 control（基线复算的分类，来自我自己的 recount 脚本判据）
def classify():
    adv25 = []
    for p in sorted(ROOT.glob("*/measure_w*.json")):
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        fe = d.get("frame_edges") if isinstance(d.get("frame_edges"), list) else []
        df = fe[-1][0] - fe[0][0] if len(fe) >= 2 else None
        st = d.get("stats") or {}
        if df is not None and df > 0 and d.get("span_s") == 25.0 and st.get("fps_avg") is not None:
            cls = "control" if st["fps_avg"] >= 28 else ("steady" if st.get("fps_p50") is not None and st["fps_p50"] < 28 else "stalled")
            if cls in ("control", "steady"):
                adv25.append((p, cls, d))
    return adv25

rows = classify()
print("47-window rebuild: n=%d (control=%d steady=%d)" % (
    len(rows), sum(1 for _, c, _ in rows if c == "control"), sum(1 for _, c, _ in rows if c == "steady")))

print("== SPOT CHECKS (candidate claim -> my reading) ==")
for tag, rel, claim in SPOT:
    p = ROOT / rel
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    fe = d["frame_edges"]
    g = d.get("gate") or {}
    mine = dict(map_sha256=d.get("map_sha256"), frames=(fe[0][0], fe[-1][0]),
                gate_ok=g.get("ok"), verdict=d.get("verdict"), units0=g.get("units0"),
                settle_s=d.get("settle_s"))
    lr = p.parent / "_launch_result.json"
    if lr.exists():
        L = json.loads(lr.read_text(encoding="utf-8-sig"))
        mine["harness_sha16"] = L.get("harness_sha16")
        mine["harness"] = L.get("harness")
        mine["launch_keys"] = sorted(L.keys())
    else:
        mine["harness_sha16"] = None
        mine["harness"] = None
        mine["launch_keys"] = "FILE_ABSENT"
    diffs = {k: (claim.get(k), mine.get(k)) for k in claim if claim.get(k) != mine.get(k)}
    print("[%s] %s" % (tag, rel))
    print("   mine:", json.dumps(mine, ensure_ascii=False))
    print("   claim-vs-mine mismatches:", json.dumps(diffs, ensure_ascii=False) if diffs else "NONE")
    # harness sha16 vs 实际 harness 文件 sha256 前 16 位（若文件在）
    hp = mine.get("harness")
    if hp and Path(hp).exists():
        h = hashlib.sha256(Path(hp).read_bytes()).hexdigest()[:16]
        print("   recomputed sha256[:16] of harness file = %s ; launch_result says %s ; candidate says %s -> file==launch:%s file==cand:%s" % (
            h, mine.get("harness_sha16"), claim.get("harness_sha16"), h == mine.get("harness_sha16"), h == claim.get("harness_sha16")))

print("== FULL 47 CHECKS ==")
by_trip = {}
for p, cls, d in rows:
    by_trip.setdefault(p.parent.name, []).append(p)
bad_map, miss_harness, bad_frames = [], [], []
for trip, files in sorted(by_trip.items()):
    maps = set()
    for p in files:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        fe = d.get("frame_edges") if isinstance(d.get("frame_edges"), list) else []
        f = (d.get("samples") or {}).get("f") or []
        maps.add(d.get("map_sha256"))
        if not fe or fe[0][0] != f[0] or fe[-1][0] != f[-1]:
            bad_frames.append(p.name)
        lr = p.parent / "_launch_result.json"
        has = False
        if lr.exists():
            L = json.loads(lr.read_text(encoding="utf-8-sig"))
            has = L.get("harness_sha16") is not None
        if not has:
            miss_harness.append("%s/%s" % (trip, p.name))
        if trip in CLAIM_HAS and has:
            L = json.loads(lr.read_text(encoding="utf-8-sig"))
            if L.get("harness_sha16") != CLAIM_HAS[trip]:
                print("   HARNESS MISMATCH %s: launch=%s candidate=%s" % (trip, L.get("harness_sha16"), CLAIM_HAS[trip]))
    if len(maps) != 1 or None in maps:
        bad_map.append((trip, [str(m)[:12] for m in maps]))
print("trips=%d ; trips with inconsistent/absent map_sha256=%d %s" % (len(by_trip), len(bad_map), bad_map))
distinct_maps = {}
for trip, files in by_trip.items():
    d = json.loads(files[0].read_text(encoding="utf-8-sig"))
    distinct_maps.setdefault(d.get("map_sha256"), []).append(trip)
print("distinct map_sha256 across 47 windows: %d" % len(distinct_maps))
for m, ts in sorted(distinct_maps.items()):
    print("   %s... -> %s" % (m[:16], ts))
print("harness_sha16 missing count = %d / 47 (candidate claims 25)" % len(miss_harness))
print("missing-harness trips:", sorted({t.split("/")[0] for t in miss_harness}))
claim_missing_ok = set(CLAIM_MISSING) == {t.split("/")[0] for t in miss_harness}
print("candidate-missing-list == my-missing-list:", claim_missing_ok)
print("frame_edges endpoints == samples.f endpoints violations: %d" % len(bad_frames))
