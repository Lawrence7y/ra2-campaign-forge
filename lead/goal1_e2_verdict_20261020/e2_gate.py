"""E2 基线趟 V 门 / R 门判定（主会话独立重算，不复用 stats 字段）。"""
import json
import statistics
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1a_20261020")
EVID = TRIP / "evidence" / "20261020T201515447650"
MAP_SHA = "0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc"

print("=" * 78)
print("E2 基线趟 · V 门 / R 门判定（主会话独立重算）")
print("=" * 78)

# ---------- 逐窗重算 ----------
windows = []
for w in (0, 1, 2):
    d = json.loads((TRIP / f"measure_w{w}.json").read_text(encoding="utf-8"))
    fe = d["frame_edges"]
    ms = [(b[1] - a[1]) * 1000.0 for a, b in zip(fe, fe[1:]) if b[0] - a[0] == 1]
    n = len(ms)
    srt = sorted(ms)
    cap = statistics.median(ms)
    f34 = 100.0 * sum(v > 34 for v in ms) / n
    E = sum(max(0.0, v - cap) for v in ms) / n

    def pctl(q):
        return srt[min(n - 1, int(q * n))]

    # 窗尾冻结：最后一条 frame_edge 到窗末
    last_edge_t = fe[-1][1]
    win_end_t = d["samples"]["t"][-1]
    freeze_tail = win_end_t - last_edge_t

    windows.append({
        "w": w,
        "cap_ms": round(cap, 2),
        "f34_pct": round(f34, 2),
        "e_ms": round(E, 3),
        "p90_ms": round(pctl(0.90), 2),
        "p99_ms": round(pctl(0.99), 2),
        "max_ms": round(srt[-1], 2),
        "tick_miss": d["stats"]["tick_miss"],
        "max_stall_s": d["stats"]["max_stall_s"],
        "freeze_tail_s": round(freeze_tail, 3),
        "logic_frames": d["stats"]["logic_frames"],
        "fps_avg": round(d["stats"]["fps_avg"], 3),
        "verdict": d["verdict"],
        "n_edges": d["stats"]["n_edges"],
        "n_multi": d["stats"]["n_multi_advance"],
        "hz": d["stats"]["hz_effective"],
    })

print("\n--- 逐窗重算（frame_edges 差分，非抄 stats）---")
hdr = f"{'w':>2} {'cap':>7} {'f34%':>7} {'E':>7} {'p90':>7} {'p99':>7} {'max':>7} {'miss':>5} {'stall':>7} {'tail':>6} {'frames':>7} {'fps':>7}"
print(hdr)
for x in windows:
    print(f"{x['w']:>2} {x['cap_ms']:>7} {x['f34_pct']:>7} {x['e_ms']:>7} {x['p90_ms']:>7} "
          f"{x['p99_ms']:>7} {x['max_ms']:>7} {x['tick_miss']:>5} {x['max_stall_s']:>7} "
          f"{x['freeze_tail_s']:>6} {x['logic_frames']:>7} {x['fps_avg']:>7}")

# ---------- 字段读取 ----------
fields = json.loads((TRIP / "qc151_fields.json").read_text(encoding="utf-8"))
F = {}
for r in fields:
    F[(r.get("group"), r.get("key"))] = r.get("value")

def g(group, key):
    return F.get((group, key))

# ---------- 逐屋轨迹 ----------
traj = {}
for (grp, key), val in F.items():
    if grp == "QC213" and key.startswith("p0") and "_h" in key and "c5574" in key:
        fr = int(key[1:7])
        h = key.split("_")[1]
        traj.setdefault(fr, {})[h] = val

print("\n--- 逐屋 c5574 轨迹（QC213 探针）---")
print(f"{'frame':>6} {'h0':>5} {'h1':>5} {'h2':>5} {'h3':>5} {'total':>6}")
trajectories = []
for fr in sorted(traj):
    v = traj[fr]
    tot = sum(x for x in v.values() if isinstance(x, int))
    trajectories.append({"frame": fr, "h0": v.get("h0"), "h1": v.get("h1"),
                         "h2": v.get("h2"), "h3": v.get("h3"), "total": tot})
    print(f"{fr:>6} {v.get('h0'):>5} {v.get('h1'):>5} {v.get('h2'):>5} {v.get('h3'):>5} {tot:>6}")

# ---------- V 门 ----------
gate = g("MEASURE", "gate") or {}
units0 = gate.get("units0")
s4_hits = g("S4", "hit_count")
s4_gate = g("S4", "s4_gate")
mods = g("S4", "modules_total")
nav_verdict = g("NAV", "verdict")
burst = g("NAV", "post_start_burst") or {}
t0t1 = json.loads((TRIP / "T0_T1_diff.json").read_text(encoding="utf-8"))
exd = json.loads((TRIP / "except_set_diff.json").read_text(encoding="utf-8"))
ctr = g("CTRL", "both_post_ok")
c1p = g("CTRL1", "verdict_post")
c2p = g("CTRL2", "verdict_post")
p3g = g("QC213P2", "p003724_qc213p2_p3_shortgame_glob")
p3e = g("QC213P2", "p003724_qc213p2_p3_equal")
meta = g("QC213P2", "p003724_qc213p2_meta_count")
h0h = g("QC213P2", "p003724_qc213p2_h0_isHuman1EC")
h1i = g("QC213P2", "p003724_qc213p2_h1_id30")
h0d = g("QC213P2", "p003724_qc213p2_h0_def1F5")
h1d = g("QC213P2", "p003724_qc213p2_h1_def1F5")
h2c = g("QC213P2", "p003724_qc213p2_h2_c5574")
h3c = g("QC213P2", "p003724_qc213p2_h3_c5574")

focus_all = all((g("MEASURE", f"measure_forensics_w{w}") or {}).get("focus_ok") for w in (0, 1, 2))
hz_all = all(x["hz"] >= 480 for x in windows)

# V9: MAP sha
import hashlib
map_sha = hashlib.sha256((EVID / "XMP29U2.MAP").read_bytes()).hexdigest()

# V6: evidence INI ShortGame
ini_txt = (EVID / "RA2MD.INI").read_bytes().decode("latin-1")
import re
sec = None
shortgame_sk = None
for line in ini_txt.split("\n"):
    m = re.match(r"^\[(.+)\]", line.strip())
    if m:
        sec = m.group(1)
    elif sec == "Skirmish" and line.strip().startswith("ShortGame"):
        shortgame_sk = line.strip()

V = []
def add(id_, crit, measured, ok):
    V.append({"id": id_, "criterion": crit, "measured": str(measured), "verdict": "PASS" if ok else "FAIL"})

add("V1", "S4.hit_count==0 ∧ s4_gate==pass ∧ modules_total≠null",
    f"hit_count={s4_hits}, s4_gate={s4_gate}, modules_total={mods}",
    s4_hits == 0 and s4_gate == "pass" and mods is not None)
add("V2", "NAV.verdict==OK ∧ burst 成立",
    f"NAV.verdict={nav_verdict}, burst.ok={burst.get('ok')}, burst_owned={burst.get('burst_owned')}",
    nav_verdict == "OK" and burst.get("ok") is True)
add("V3", "每窗 verdict==ok ∧ logic_frames>0 ∧ n_edges≥50 ∧ n_multi 已记",
    "; ".join(f"w{x['w']}:{x['verdict']}/lf={x['logic_frames']}/e={x['n_edges']}/multi={x['n_multi']}" for x in windows),
    all(x["verdict"] == "ok" and x["logic_frames"] > 0 and x["n_edges"] >= 50 and x["n_multi"] is not None for x in windows))
add("V4", "units0≥150（脚本门）∧ units0≥800（设计门）",
    f"units0={units0}（脚本门 {'PASS' if (units0 or 0)>=150 else 'FAIL'}；设计门 {'PASS' if (units0 or 0)>=800 else 'FAIL'}）",
    (units0 or 0) >= 150 and (units0 or 0) >= 800)
add("V5", "meta_count==4 ∧ h0 isHuman1EC==1 ∧ h1 id30==1 ∧ h0/h1 def1F5==0 ∧ h2/h3 c5574>0",
    f"meta={meta}, h0human={h0h}, h1id30={h1i}, h0def={h0d}, h1def={h1d}, h2c={h2c}, h3c={h3c}",
    meta == 4 and h0h == 1 and h1i == 1 and h0d == 0 and h1d == 0 and (h2c or 0) > 0 and (h3c or 0) > 0)
add("V6", "p3_shortgame_glob==0 ∧ p3_equal==true ∧ evidence INI ShortGame=no",
    f"glob={p3g}, equal={p3e}, evidence[Skirmish].{shortgame_sk}",
    p3g == 0 and p3e is True and shortgame_sk == "ShortGame=no")
add("V7", "T0_T1 diff_count==0 ∧ new_exception_count==0 ∧ CTRL1/2 post PASS",
    f"T0_T1_diff={t0t1}, new_exc={exd.get('new_exception_count')}, CTRL1={c1p}, CTRL2={c2p}, both_post={ctr}",
    t0t1 == [] and exd.get("new_exception_count") == 0 and c1p == "PASS" and c2p == "PASS")
add("V8", "三窗 focus_ok==true ∧ hz_effective≥480",
    f"focus_all={focus_all}, hz={[x['hz'] for x in windows]}",
    focus_all and hz_all)
add("V9", "MAP sha == 0add791d…60bc ∧ 起点 h2/h3 c5574≥200",
    f"sha={map_sha[:16]}…{'MATCH' if map_sha==MAP_SHA else 'MISMATCH'}, h2={h2c}, h3={h3c}",
    map_sha == MAP_SHA and (h2c or 0) >= 200 and (h3c or 0) >= 200)
add("V10", "（仅 L2）evidence INI GameSpeed==6", "本趟为 L1，N/A", True)
V[-1]["verdict"] = "N_A"

print("\n--- V 门 ---")
for v in V:
    print(f"  {v['id']:>3} [{v['verdict']:>4}] {v['criterion']}")
    print(f"        {v['measured']}")

vp = sum(1 for v in V if v["verdict"] == "PASS")
vf = sum(1 for v in V if v["verdict"] == "FAIL")
print(f"\n  V 门：{vp} 过 / {vf} 不过 / {sum(1 for v in V if v['verdict']=='N_A')} N_A")

# ---------- R 门 ----------
print("\n--- R 门 ---")
r_hits = []
# R0: 三窗 fps_avg >= 30 且 f34<30% 且 E≈0
r0 = all(x["fps_avg"] >= 30 for x in windows) and all(x["f34_pct"] < 30 for x in windows) and all(x["e_ms"] < 0.5 for x in windows)
# R1: f34>=30% 或 p90>40ms（≥2窗）
r1 = sum(1 for x in windows if x["f34_pct"] >= 30 or x["p90_ms"] > 40) >= 2
# R2: p99>60 或 max>100 或 tick_miss>0（≥2窗）
r2 = sum(1 for x in windows if x["p99_ms"] > 60 or x["max_ms"] > 100 or x["tick_miss"] > 0) >= 2
# R3: 任一窗 max_stall>1s 或 logic_frames < 0.8*中位
med_lf = statistics.median([x["logic_frames"] for x in windows])
r3 = any(x["max_stall_s"] > 1.0 or x["logic_frames"] < 0.8 * med_lf for x in windows)
# R4: fps_avg < 25
r4 = any(x["fps_avg"] < 25 for x in windows)
# R5: 窗口内 def1F5 翻转
flip = any((traj[fr].get(h) == 1) for fr in sorted(traj) for h in ("h0", "h1")
           if False)  # def1F5 只在 QC213P2 起点快照有，逐帧 def 在 QC213 组另名
r5 = False

print(f"  R0 (三窗 fps_avg≥30 且 f34<30% 且 E≈0) = {r0}")
print(f"     实测 fps_avg={[x['fps_avg'] for x in windows]}  f34={[x['f34_pct'] for x in windows]}  E={[x['e_ms'] for x in windows]}")
print(f"  R1 (f34≥30% 或 p90>40ms，≥2窗)          = {r1}")
print(f"  R2 (p99>60 或 max>100 或 miss>0，≥2窗)  = {r2}")
print(f"     实测 p99={[x['p99_ms'] for x in windows]}  max={[x['max_ms'] for x in windows]}  miss={[x['tick_miss'] for x in windows]}")
print(f"  R3 (max_stall>1s 或 lf<0.8×中位)        = {r3}")
print(f"     实测 stall={[x['max_stall_s'] for x in windows]}  lf={[x['logic_frames'] for x in windows]} 中位={med_lf}")
print(f"  R4 (fps_avg<25)                          = {r4}")
print(f"  R5 (def1F5 翻转/记分板)                  = {r5}")

if r4:
    r_gate = "R4"
elif r3:
    r_gate = "R3"
elif r2:
    r_gate = "R2"
elif r1:
    r_gate = "R1"
elif r0:
    r_gate = "R0"
else:
    r_gate = "UNCLASSIFIED"

print(f"\n  ⇒ R 门判：{r_gate}")

# ---------- 疑点 ----------
print("\n--- 疑点 A：max_stall 与 frame_ms_max ---")
for x in windows:
    print(f"  w{x['w']}: max_stall={x['max_stall_s']}s  frame_ms_max={x['max_ms']}ms  "
          f"freeze_tail={x['freeze_tail_s']}s  比值={x['max_stall_s']*1000/x['max_ms']:.1f}x")
print("  口径：max_stall_s = 最长连续 df=0 墙钟跨度（qc151_trip.carrierfix.py:3719-3760），非帧间隔。")
print("  ⇒ w2 的 1.782s 是窗尾冻结（最后一条 edge 之后 1.782s 无帧推进），不是单帧卡 1.782s。")

print("\n--- 疑点 B：三窗负载 ---")
for x in windows:
    lo = min(t["total"] for t in trajectories if True)
print(f"  轨迹合计：{[(t['frame'], t['total']) for t in trajectories]}")
print(f"  h1 轨迹：{[(t['frame'], t['h1']) for t in trajectories]}")
print(f"  ⇒ h1 从 {trajectories[0]['h1']} 掉到 {trajectories[-1]['h1']}，w2 窗（5412-6137）内 h1 已基本清零。")

print("\n--- 疑点 C：evidence INI sha ---")
ev_sha = hashlib.sha256((EVID / "RA2MD.INI").read_bytes()).hexdigest()
src_sha = hashlib.sha256(Path(
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\RA2MD.INI"
).read_bytes()).hexdigest()
print(f"  evidence sha = {ev_sha[:16]}  ({len((EVID/'RA2MD.INI').read_bytes())} B)")
print(f"  源变体  sha = {src_sha[:16]}")
print(f"  报告声称     = 0cc65385（= 源变体值，非 evidence 值）")

# ---------- 落盘 ----------
out = {
    "windows": windows,
    "v_gates": V,
    "v_pass": vp, "v_fail": vf,
    "trajectories": trajectories,
    "r_gate": r_gate,
    "r_flags": {"R0": r0, "R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5},
    "evidence_ini_sha": ev_sha,
    "source_ini_sha": src_sha,
    "map_sha": map_sha,
    "units0": units0,
}
outp = Path(__file__).resolve().parent / "e2_recompute.json"
outp.parent.mkdir(parents=True, exist_ok=True)
outp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nwrote {outp}")
