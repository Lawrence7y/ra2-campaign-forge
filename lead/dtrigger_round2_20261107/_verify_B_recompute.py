# -*- coding: utf-8 -*-
"""
_verify_B_recompute.py — 复核员·B 独立复算（不 import 调查员任何实现）

只依赖：原始语料 (t,f)、manifest、STALL_EVENTS.json、以及我本轮亲自读过的
权威定义件 _dtrigger_metrics.py:162-187,217,223-227 / _dtrigger_probe.py:202-239 /
CRITERIA_COMPARE.md:218-223,242-252,395,420-422 / CRITERIA_METRICS.json。
不 import 既有 _dtrigger_*.py / _check_*.py / _dB_*.py / _dC_*.py / _dD_*.py 的代码，
只读它们的落盘数据作交叉比对。

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_B_recompute.py
"""
import hashlib
import json
import re
import statistics
import os
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
METRICS_JSON = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json").resolve()
PROBE_OUT = (ROOT / "lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt").resolve()
SUPP_OUT = (ROOT / "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt").resolve()
COMPARE_MD = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md").resolve()
DB_OUT = (ROOT / "lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt").resolve()
DB_JSON = (ROOT / "lead/dtrigger_round2_20261107/_dB_anchor_recompute_data.json").resolve()
WD = (ROOT / "lead/dtrigger_round2_20261107").resolve()
REPORT = WD / "_verify_B_out.txt"

LOG = []
def say(s=""):
    LOG.append(str(s)); print(s)

def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

def pctl(a, p):
    return a[int(p * (len(a) - 1))] if a else None

# ---------------------------------------------------------------- 1 语料（自建）
corpus = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    key = (pr.parent.name if pr.parent != BASE else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    t = d["samples"]["t"]; f = d["samples"]["f"]
    assert len(t) == len(f)
    corpus[key] = (t, f)
n_files = len(corpus)
n_samples = sum(len(v[0]) for v in corpus.values())
say(f"[语料] measure_w*.json n={n_files}  采样点 n={n_samples}")

wins = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d+)\s+([0-9.]+)", ln.strip())
    if m and (m.group(1), m.group(2)) in corpus:
        t, f = corpus[(m.group(1), m.group(2))]
        if len(t) >= 2 and any(a != b for a, b in zip(f, f[1:])):
            wins.add((m.group(1), m.group(2)))
wins = sorted(wins)
say(f"[manifest] 推进窗 n={len(wins)}")

events = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
start0 = sorted((e["trip"], e["window"], e["startTick"], e["endTick"])
                for e in real if e["startTick"] == 0)
say(f"[事件] 全量 n={len(events)}  isRealMatch=true n={len(real)}  real_keys n={len(real_keys)}  startTick=0 n={len(start0)}")

# ---------------------------------------------------------------- 2 自建游程/历史
# change[a] = 1..a 内帧号变化次数；hist = 依次完成的帧间隔 (ms)
# he(i) = change[i-1] = 游程起点 i 之前已完成的帧间隔条数；og = t[i]-t[i-1]
W = {}
RUNS = []
for key in wins:
    t, f = corpus[key]
    n = len(f)
    change = [0] * n
    hist = []
    le = 0
    for a in range(1, n):
        if f[a] != f[a - 1]:
            hist.append((t[a] - t[le]) * 1000.0)
            le = a
            change[a] = change[a - 1] + 1
        else:
            change[a] = change[a - 1]
    W[key] = (t, f, hist, change)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        he = change[i - 1] if i > 0 else 0
        og = (t[i] - t[i - 1]) * 1000.0 if i > 0 else None
        RUNS.append({
            "key": key, "i": i, "j": j,
            "he": he, "og": og,
            "dfin": (t[j] - t[i]) * 1000.0,
            "k": (key[0], key[1], i, j),
        })
        i = j + 1
say(f"[游程] n={len(RUNS)}  real 与游程对齐 n={sum(1 for r in RUNS if r['k'] in real_keys)}/{len(real_keys)}")

ogs = [r["og"] for r in RUNS if r["og"] is not None]
e_full = statistics.median(ogs)
e_round = 2.511
say(f"[e] median(og|i>0) = {e_full:.9f} ms  n={len(ogs)}  (3位={e_full:.3f})")

# ---------------------------------------------------------------- 3 我自己的谓词实现
# 权威锚：_dtrigger_metrics.py:217,223-227（我本轮亲读）
# C2-abs-P95x2 / C3-r4 / C3-r8 / C3-r12 = lastEdge；两个 -clean = runStart
def first_x(r, w, theta_or_base, mult, anchor, is_p95):
    t = w[0]
    he, og = r["he"], r["og"]
    if he < 64:
        return None
    if anchor == "lastEdge" and og is None:
        return None
    if anchor == "runStart" and og is None:
        pass  # runStart 谓词不需要 og（metrics:183 off=0.0）
    hist = w[2]
    window = sorted(hist[he - 64:he])
    if is_p95:
        theta = pctl(window, 0.95) * 2.0
        if anchor == "lastEdge":
            cmp = lambda wait: wait + og > theta
        else:
            cmp = lambda wait: wait > theta
    else:
        base = statistics.median(window)
        if base <= 0:
            return None
        off = og if anchor == "lastEdge" else 0.0
        cmp = lambda wait: wait + off > mult * base
    i, j = r["i"], r["j"]
    for x in range(i, j + 1):
        wait = (t[x] - t[i]) * 1000.0
        if cmp(wait):
            return x, wait
    return None

IDS = [
    ("C2-abs-P95x2", "lastEdge", True,  0.0),
    ("C3-r4",        "lastEdge", False, 4.0),
    ("C3-r4-clean",  "runStart", False, 4.0),
    ("C3-r8",        "lastEdge", False, 8.0),
    ("C3-r8-clean",  "runStart", False, 8.0),
    ("C3-r12",       "lastEdge", False, 12.0),
]
RES = {}
for cid, anchor, is_p95, mult in IDS:
    rows = []
    for r in RUNS:
        got = first_x(r, W[r["key"]], None, mult, anchor, is_p95)
        if got is None:
            continue
        x, wait = got
        rows.append({"k": r["k"], "i": r["i"], "j": r["j"], "idx": x,
                     "wait": wait, "og": r["og"], "he": r["he"],
                     "dfin": r["dfin"], "isReal": r["k"] in real_keys})
    waits = sorted(z["wait"] for z in rows)
    real_waits = sorted(z["wait"] for z in rows if z["isReal"])
    RES[cid] = {
        "rows": rows,
        "nTrig": len(waits),
        "nGe100": sum(1 for v in waits if v >= 100.0),
        "nGt50PlusE": sum(1 for v in waits if v + e_full > 50.0),
        "nGt50PlusE_round": sum(1 for v in waits if v + e_round > 50.0),
        "nGt50": sum(1 for v in waits if v > 50.0),
        "wmin": waits[0], "wmed": statistics.median(waits), "wmax": waits[-1],
        "realHits": len(real_waits),
        "latP50_real": statistics.median(real_waits) if real_waits else None,
        "waits": waits,
    }

say("")
say("[主表·我独立复算]  id | nTrig | >=100 | +e>50(全精度) | +e>50(e=2.511) | >50 | min/med/max | realHits")
for cid, anchor, _, _ in IDS:
    c = RES[cid]
    say(f"  {cid:<16} {c['nTrig']:>5} {c['nGe100']:>7} {c['nGt50PlusE']:>16} "
        f"{c['nGt50PlusE_round']:>17} {c['nGt50']:>5} "
        f"{c['wmin']:.3f}/{c['wmed']:.3f}/{c['wmax']:.3f}  {c['realHits']:>5}")

# ---------------------------------------------------------------- 4 结构量
n_i0 = sum(1 for r in RUNS if r["i"] == 0)
n_og_none_ge64 = sum(1 for r in RUNS if r["og"] is None and r["he"] >= 64)
n_he_lt64 = sum(1 for r in RUNS if r["he"] < 64)
say("")
say(f"[结构] i==0 n={n_i0}  og=None 且 he>=64 n={n_og_none_ge64}  he<64 n={n_he_lt64}")
s0 = []
for k in start0:
    hit = [r for r in RUNS if r["k"] == k]
    s0.append((k, len(hit), hit[0]["he"], hit[0]["og"]))
    in_all = [cid for cid, _, _, _ in IDS
              if any(z["k"] == k for z in RES[cid]["rows"])]
    say(f"  start0 {k} 游程数={len(hit)} he={hit[0]['he']} og={hit[0]['og']} "
        f"进入触发集的 id={in_all}")
say(f"[结构] 各 id 触发行中 og=None 的条数："
    + str({cid: sum(1 for z in RES[cid]['rows'] if z['og'] is None) for cid, _, _, _ in IDS}))
# C2-abs-P95x2 的 >=100 与 false(d_fin<100) 是否同一批
c2 = RES["C2-abs-P95x2"]
ge100_ks = {z["k"] for z in c2["rows"] if z["wait"] >= 100.0}
false_ks = {z["k"] for z in c2["rows"] if z["dfin"] < 100.0}
say(f"[陷阱核对] C2-abs-P95x2: >=100 的 {len(ge100_ks)} 条 d_fin 最小={min(z['dfin'] for z in c2['rows'] if z['k'] in ge100_ks):.3f}；"
    f"false(d_fin<100) n={len(false_ks)}；两集合交集 n={len(ge100_ks & false_ks)}")

# ---------------------------------------------------------------- 5 交叉校验（只读）
say("")
say("[交叉校验 A] 与 CRITERIA_METRICS.json（本轮实读）比对")
ref = json.loads(METRICS_JSON.read_text(encoding="utf-8-sig"))
A_ok = True
for cid, anchor, _, _ in IDS:
    c = RES[cid]; r = ref[cid]
    ok1 = c["nTrig"] == r["triggers"]
    ok2 = c["realHits"] == r["realHits"]
    if c["latP50_real"] is None:
        ok3 = r["latencySampleN"] == 0
    else:
        ok3 = abs(c["latP50_real"] - r["latencyP50Ms"]) < 0.002
    A_ok &= (ok1 and ok2 and ok3)
    say(f"  {cid:<16} nTrig {c['nTrig']}=={r['triggers']} {ok1} | realHits {c['realHits']}=={r['realHits']} {ok2} | "
        f"latP50(real) {c['latP50_real']} vs {r['latencyP50Ms']} {ok3}")
say(f"  A_ok = {A_ok}")

say("[交叉校验 B] 与 _dtrigger_probe_out.txt:138,149,160,171（本轮实读+正则解析）比对")
probe_lines = PROBE_OUT.read_text(encoding="utf-8-sig").splitlines()
probe_expect = {}
for ln in (138, 149, 160, 171):
    m = re.search(r"waitAfterS_hat\(ms\): min=([0-9.]+) med=([0-9.]+) P90=[0-9.]+ P99=[0-9.]+ max=([0-9.]+)",
                  probe_lines[ln - 1])
    probe_expect[ln] = tuple(float(m.group(i)) for i in (1, 2, 3))
ids4 = ["C2-abs-P95x2", "C3-r4", "C3-r8", "C3-r12"]
B_ok = True
for cid, ln in zip(ids4, (138, 149, 160, 171)):
    mn, md, mx = probe_expect[ln]
    c = RES[cid]
    ok = (c["nTrig"] > 0 and abs(c["wmin"] - mn) < 0.002
          and abs(c["wmed"] - md) < 0.002 and abs(c["wmax"] - mx) < 0.002)
    B_ok &= ok
    say(f"  :{ln} {cid:<16} probe {mn:.3f}/{md:.3f}/{mx:.3f} vs mine "
        f"{c['wmin']:.3f}/{c['wmed']:.3f}/{c['wmax']:.3f}  {'OK' if ok else 'FAIL'}")
say(f"  B_ok = {B_ok}")

say("[交叉校验 C] 与交付 _dB_anchor_recompute_data.json 比对（12 格 + 逐触发 wait 数组）")
d = json.loads(DB_JSON.read_text(encoding="utf-8-sig"))
C_ok = True
for cid, _, _, _ in IDS:
    c = RES[cid]; dj = d["cells"][cid]
    same_cells = (c["nTrig"] == dj["nTrig"] and c["nGe100"] == dj["nGe100"]
                  and c["nGt50PlusE"] == dj["nGt50PlusE"]
                  and abs(c["wmin"] - dj["waitMin"]) < 1e-6
                  and abs(c["wmed"] - dj["waitMed"]) < 1e-6
                  and abs(c["wmax"] - dj["waitMax"]) < 1e-6
                  and c["realHits"] == dj["realHits"])
    drows = d["trigger_details"][cid]
    mw = sorted(c["waits"]); dw = sorted(z["wait"] for z in drows)
    same_waits = (len(mw) == len(dw) and all(abs(a - b) < 1e-9 for a, b in zip(mw, dw)))
    same_keys = sorted(z["k"] for z in c["rows"]) == sorted(
        (z["trip"], z["win"], z["i"], z["j"]) for z in drows)
    C_ok &= (same_cells and same_waits and same_keys)
    say(f"  {cid:<16} cells={same_cells} 逐值wait={same_waits} 触发键集合={same_keys}")
say(f"  C_ok = {C_ok}  | data.selfcheck_all_pass = {d['selfcheck_all_pass']}")

say("[交叉校验 D] e 取 2.511 常数时 12 格不变？")
D_ok = all(RES[cid]["nGe100"] == d["cells"][cid]["nGe100"] and
           RES[cid]["nGt50PlusE"] == RES[cid]["nGt50PlusE_round"] for cid, _, _, _ in IDS)
say(f"  D_ok = {D_ok}  (>=100 与交付一致 且 全精度e与e=2.511同值) " + str({cid: (RES[cid]['nGt50PlusE'], RES[cid]['nGt50PlusE_round']) for cid, _, _, _ in IDS}))

say("[交叉校验 E] 敏感性：6 档一律 runStart 谓词（我独立复算）")
SENS = [
    ("C2-abs-P95x2/runStart", True, 0.0),
    ("C3-r4/runStart", False, 4.0),
    ("C3-r4-clean", False, 4.0),
    ("C3-r8/runStart", False, 8.0),
    ("C3-r8-clean", False, 8.0),
    ("C3-r12/runStart", False, 12.0),
]
sens = {}
for name, is_p95, mult in SENS:
    rows = []
    for r in RUNS:
        got = first_x(r, W[r["key"]], None, mult, "runStart", is_p95)
        if got is None:
            continue
        rows.append(got[1])
    waits = sorted(rows)
    sens[name] = (len(waits), sum(1 for v in waits if v >= 100.0),
                  sum(1 for v in waits if v + e_full > 50.0),
                  statistics.median(waits) if waits else None,
                  waits[-1] if waits else None)
    say(f"  {name:<24} nTrig/>=100/+e>50 = {sens[name][0]}/{sens[name][1]}/{sens[name][2]} "
        f"waitMed={sens[name][3]:.3f} waitMax={sens[name][4]:.3f}")

# ---------------------------------------------------------------- 6 指纹/铁律9 行核对
say("")
say("[指纹] 本轮实算")
for p in (DB_OUT, DB_JSON, (WD / "_dB_anchor_recompute.py"),
          (WD / "_dB_anchor_recompute_stdout.txt"), COMPARE_MD):
    h, n = sha(p)
    say(f"  {p.name:<38} {h} {n}")
out_lines = DB_OUT.read_text(encoding="utf-8-sig").splitlines()
line18 = out_lines[17]
h_cmp, n_cmp = sha(COMPARE_MD)
h_db, n_db = sha(DB_OUT)
say(f"  out.txt:18 = {line18}")
say(f"  out.txt:18 的 hash == CRITERIA_COMPARE.md ? {h_cmp in line18} ；== _dB_anchor_recompute_out.txt ? {h_db in line18}")
say(f"  我复核用的铁律9行：被核对象 SHA256 = {h_db}，字节数 = {n_db}")

say("[交叉校验 F] 回件 evidence 中的 _dB_ 指纹字符串是否与实际吻合")
ev_script_tail = "26f3fb61829756dfeecf"
ev_out_tail = "b6f95763794"
h_script, _ = sha(WD / "_dB_anchor_recompute.py")
h_data, _ = sha(DB_JSON)
say(f"  回件称脚本 hash 尾={ev_script_tail}；实算脚本 hash 含该尾? {ev_script_tail in h_script}；"
    f"该尾出现在 data.json? {ev_script_tail in h_data}")
say(f"  回件称 out.txt hash 尾={ev_out_tail}；实算 out.txt hash 含该尾? {ev_out_tail in h_db}；"
    f"该尾出现在 data.json? {ev_out_tail in h_data}")

# ---------------------------------------------------------------- 7 汇总
say("")
say(f"[汇总] A_ok={A_ok} B_ok={B_ok} C_ok={C_ok} D_ok={D_ok}")
say("[交付件内部文本核对]")
for ln in (120, 126, 148, 149, 150, 153, 155):
    say(f"  out.txt:{ln}: {out_lines[ln-1]}")
supp = SUPP_OUT.read_text(encoding="utf-8-sig").splitlines()
say(f"  supplement_out.txt:15: {supp[14]}")
say(f"  supplement_out.txt:21: {supp[20]}")
say(f"  supplement_out.txt:22: {supp[21]}")

REPORT.write_text("\n".join(LOG) + "\n", encoding="utf-8")
print(f"\n已写：{REPORT}  (仅 _verify_B_ 前缀新文件)")
