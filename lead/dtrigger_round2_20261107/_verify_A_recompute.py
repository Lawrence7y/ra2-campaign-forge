# -*- coding: utf-8 -*-
"""Independent read-only verification of dimension-A claims.

No process introspection, no game execution, no sampling code. This script reads
existing corpus and result files, recomputes the deterministic claims, and writes
only _verify_A_out.txt within lead/dtrigger_round2_20261107/.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
QUOTA_JSON = (ROOT / "lead/dtrigger_compare_20261107/_cost_quota_data.json").resolve()
METRICS_JSON = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json").resolve()
WD = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT_TXT = WD / "_dA_out.txt"
OUT_JSON = WD / "_dA_data.json"
CHECK_TXT = WD / "_dA_check.txt"
DESIGN_MD = WD / "_dA_design.md"
RUN_PY = WD / "_dA_run.py"
PROBE_PY = WD / "_dA_probe.py"
RESULT = WD / "_verify_A_out.txt"

REPORT: list[str] = []


def say(s: str = "") -> None:
    REPORT.append(s)
    print(s)


def check(name: str, ok: bool, detail: str = "") -> None:
    say(f"{'PASS' if ok else 'FAIL'} {name}{(' :: ' + detail) if detail else ''}")


def sha256_file(p: Path) -> tuple[str, int]:
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def pctl(sorted_values: list[float], p: float) -> float | None:
    return sorted_values[int(p * (len(sorted_values) - 1))] if sorted_values else None


def bucket(g: float) -> str:
    # Independent algebraic form; same five boundaries as the claim.
    if g < 0.05:
        return "S"
    if g < 0.5:
        return "M"
    if g < 2.0:
        return "L"
    if g < 5.0:
        return "X"
    return "G"


def elapsed(T: list[float], i: int, x: int) -> float:
    return (T[x] - T[i]) * 1000.0


def gap(T: list[float], x: int) -> float:
    return (T[x] - T[x - 1]) * 1000.0


# ------------------------------------------------------------------ hashes / given fingerprints
GIVEN_FP = {
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md": ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json": ("7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b", 17926),
    "lead/dtrigger_compare_20261107/_cost_quota_data.json": ("e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac", 111044),
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt": ("f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66", 5088),
    "lead/d30_ruling_20261106/RULING_D30.md": ("d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f", 13197),
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md": ("ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001", 27271),
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md": ("1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29", 20133),
}
say("=== 1. HASHES / GIVEN UPSTREAM FINGERPRINTS ===")
for rel, expected in GIVEN_FP.items():
    actual = sha256_file(ROOT / rel)
    check(f"given fingerprint {rel}", actual == expected, f"sha={actual[0]} bytes={actual[1]}")
for p in sorted(WD.glob("_dA_*")):
    if p.is_file():
        h, n = sha256_file(p)
        say(f"HASH {p.name} sha256={h} bytes={n}")
main_hash, main_bytes = sha256_file(DESIGN_MD)
say(f"被核对象 SHA256 = {main_hash}，字节数 = {main_bytes} [lead/dtrigger_round2_20261107/_dA_design.md]")

# ------------------------------------------------------------------ corpus reconstruction
say("\n=== 2. CORPUS / EVENTS / RUNS (INDEPENDENT RECONSTRUCTION) ===")
cache: dict[tuple[str, str], dict] = {}
corpus_files = sorted(BASE.rglob("measure_w*.json"))
for p in corpus_files:
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus path escapes base")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    if len(d["samples"]["t"]) != len(d["samples"]["f"]):
        raise ValueError("sample length mismatch")
    cache[key] = d
n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
hz = sorted({v.get("hz") for v in cache.values()})
check("corpus files/samples/hz", (len(cache), n_samples, hz) == (104, 1125992, [500]),
      f"files={len(cache)} samples={n_samples} hz={hz}")

manifest_keys: set[tuple[str, str]] = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            manifest_keys.add((m[1], m[2]))
manifest_keys = sorted(manifest_keys)
check("moving windows", len(manifest_keys) == 64, f"n={len(manifest_keys)} trips={len(set(k[0] for k in manifest_keys))}")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real_events = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real_events}
dur_of = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e["durationMs"] for e in real_events}
check("events", (len(events_all), len(real_events), len(real_keys)) == (1737, 1681, 1681),
      f"all={len(events_all)} real={len(real_events)} unique={len(real_keys)}")

# Each record deliberately carries only causal inputs and post-hoc labels.
records: list[dict] = []
nonmono = 0
for trip, win in manifest_keys:
    T, F = cache[(trip, win)]["samples"]["t"], cache[(trip, win)]["samples"]["f"]
    n = len(F)
    if any(T[x + 1] <= T[x] for x in range(n - 1)):
        nonmono += 1
    hist: list[float] = []
    hlen = [0] * n
    le = 0
    for a in range(1, n):
        if F[a] != F[a - 1]:
            hist.append((T[a] - T[le]) * 1000.0)
            le = a
        hlen[a] = len(hist)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and F[j + 1] == F[i]:
            j += 1
        he = hlen[i - 1] if i > 0 else 0
        e = (T[i] - T[i - 1]) * 1000.0 if i > 0 else None
        prev_gaps: list[float] = []
        if i > 0:
            q = i - 1
            fq = F[q]
            while q > 0 and F[q - 1] == fq:
                q -= 1
            prev_gaps = [(T[k] - T[k - 1]) * 1000.0 for k in range(q + 1, i + 1)]
        records.append({
            "trip": trip, "win": win, "i": i, "j": j, "npts": j - i + 1,
            "T": T, "F": F, "dfin": (T[j] - T[i]) * 1000.0, "e": e,
            "key": (trip, win, i, j), "is_real": (trip, win, i, j) in real_keys,
            "hist": hist, "he": he,
            "D": hist[he - 1] if he >= 1 else None,
            "prev_min": min(prev_gaps) if prev_gaps else None,
            "prev_max": max(prev_gaps) if prev_gaps else None,
            "prev_len": len(prev_gaps) if prev_gaps else None,
        })
        i = j + 1
check("frame-number runs / t monotonicity", (len(records), nonmono) == (28381, 0),
      f"runs={len(records)} nonmono_windows={nonmono}")
aligned = sum(1 for r in records if r["is_real"])
check("real events aligned to runs", aligned == 1681, f"aligned={aligned}")
es = sorted(r["e"] for r in records if r["e"] is not None)
check("e valid / unknown count", len(es) == 28317 and len(records) - len(es) == 64,
      f"valid={len(es)} unknown={len(records)-len(es)}")
e_stats = (round(es[0], 3), round(statistics.median(es), 3), round(pctl(es, .99), 3), round(es[-1], 3))
check("e min/med/P99/max ms", e_stats == (0.008, 2.511, 4.145, 488.616), str(e_stats))
diffs = [abs(r["dfin"] - dur_of[r["key"]]) for r in records if r["is_real"]]
check("real dfin vs durationMs", round(max(diffs), 6) == 0.005 and round(sum(diffs)/len(diffs), 6) == 0.002473,
      f"max={max(diffs):.6f} mean={sum(diffs)/len(diffs):.6f}")

win_counts = Counter(k[:2] for k in real_keys)
trip_counts = Counter(k[0] for k in real_keys)
ideal_w = {N: sum(min(N, c) for c in win_counts.values()) for N in (1, 3, 5)}
ideal_t = {N: sum(min(N, c) for c in trip_counts.values()) for N in (1, 3, 5)}
check("quota hard bounds W/T", (ideal_w, ideal_t) == ({1: 26, 3: 73, 5: 117}, {1: 12, 3: 31, 5: 47}),
      f"W={ideal_w} T={ideal_t} nonempty_windows={len(win_counts)} nonempty_trips={len(trip_counts)}")

# ------------------------------------------------------------------ independent predicate definitions
# Trigger functions receive only T, F, run boundaries, and already-completed history.
def cal_k(r: dict, k: int) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    return i + k - 1 if j - i + 1 >= k else None

def cal_abs(r: dict, theta: float) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    if j - i + 1 < 3:
        return None
    for x in range(i + 2, j + 1):
        if elapsed(T, i, x) > theta:
            return x
    return None

def cal_hybrid(r: dict, k: int, theta: float) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    if j - i + 1 < k:
        return None
    for x in range(i + k - 1, j + 1):
        if elapsed(T, i, x) > theta:
            return x
    return None

def word_match(r: dict, target: str) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    w = ""
    for x in range(i + 1, j + 1):
        w += bucket(gap(T, x))
        if len(w) >= max(len(target), 3) and w.endswith(target):
            return x
    return None

def run_letter(r: dict, letter: str, length: int) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    streak = 0
    for x in range(i + 1, j + 1):
        if bucket(gap(T, x)) == letter:
            streak += 1
            if streak >= length:
                return x
        else:
            streak = 0
    return None

def d3_min_gt_prev(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    pm = r["prev_min"]
    if pm is None or pm <= 0:
        return None
    for x in range(i + 1, j + 1):
        if min(gap(T, k) for k in range(i + 1, x + 1)) > pm and x - i >= 3:
            return x
    return None

def d3_flip(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    if r["prev_len"] is None or r["prev_len"] < 2 or i + 2 > j:
        return None
    prev_first = bucket(gap(T, i - r["prev_len"] + 1))
    curr_first = bucket(gap(T, i + 1))
    if curr_first == prev_first or curr_first not in ("L", "X", "G"):
        return None
    return i + 2

def d4_rising(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    g: list[float] = []
    for x in range(i + 1, j + 1):
        g.append(gap(T, x))
        if len(g) >= 3 and g[-3] < g[-2] < g[-1]:
            return x
    return None

def d4_burst(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    prev = None
    for x in range(i + 1, j + 1):
        g = gap(T, x)
        if prev is not None and prev < 0.5 and g >= 2.0:
            return x
        prev = g
    return None

def d5_phase(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    D = r["D"]
    if D is None or D <= 0:
        return None
    prev_phase, prev_bkt = 0, None
    for x in range(i + 1, j + 1):
        ph = int(elapsed(T, i, x) / D)
        cb = bucket(gap(T, x))
        if ph > prev_phase and cb != prev_bkt and x - i >= 3:
            return x
        prev_phase, prev_bkt = ph, cb
    return None

def d5_ordinal(r: dict) -> int | None:
    T, i, j = r["T"], r["i"], r["j"]
    if r["prev_len"] is None or r["prev_len"] < 2:
        return None
    pstart = i - r["prev_len"]
    pscore = sum(1 for k in range(pstart + 1, i + 1) if bucket(gap(T, k)) in ("L", "X", "G"))
    cscore = 0
    for x in range(i + 1, j + 1):
        if bucket(gap(T, x)) in ("L", "X", "G"):
            cscore += 1
        if cscore > pscore and x - i >= 3:
            return x
    return None

CRITERIA: list[tuple[str, object]] = [
    ("CAL-C1-k10", lambda r: cal_k(r, 10)),
    ("CAL-C1-k25", lambda r: cal_k(r, 25)),
    ("CAL-C4-t40", lambda r: cal_abs(r, 40.0)),
    ("CAL-C5-k10t30", lambda r: cal_hybrid(r, 10, 30.0)),
    ("D1-word-MMM", lambda r: word_match(r, "MMM")),
    ("D1-word-LLL", lambda r: word_match(r, "LLL")),
    ("D1-word-G", lambda r: word_match(r, "G")),
    ("D2-run-S4", lambda r: run_letter(r, "S", 4)),
    ("D2-run-M6", lambda r: run_letter(r, "M", 6)),
    ("D3-min>prev", d3_min_gt_prev),
    ("D3-flip", d3_flip),
    ("D4-rising", d4_rising),
    ("D4-burst", d4_burst),
    ("D5-phase", d5_phase),
    ("D5-ordinal", d5_ordinal),
]

def trigger_list(fn) -> list[tuple]:
    out = []
    for r in records:
        idx = fn(r)
        if idx is None:
            continue
        w = elapsed(r["T"], r["i"], idx)
        e = r["e"]
        out.append((r["T"][idx], idx, r["trip"], r["win"], r["key"], r["is_real"],
                    r["dfin"], w, e, e is not None and w + e <= 50.0))
    return out

def simulate(trig: list[tuple], scope: str, N: int) -> dict:
    groups: dict[tuple, list[tuple]] = defaultdict(list)
    for t in trig:
        groups[(t[2], t[3]) if scope == "window" else t[2]].append(t)
    captured: set[tuple] = set()
    strict: set[tuple] = set()
    eaten = 0
    used = 0
    for arr in groups.values():
        arr.sort(key=lambda x: (x[0], x[3], x[1]))
        for t in arr[:N]:
            used += 1
            if not t[5]:
                eaten += 1
            else:
                captured.add(t[4])
                if t[9]:
                    strict.add(t[4])
    return {"captured": len(captured), "captured_strict50": len(strict),
            "quotaEatenByFalse": eaten, "quotaUsed": used}

say("\n=== 3. ALL 15 CRITERIA / 6 QUOTA CELLS EACH / 3D METRICS ===")
computed: dict[str, dict] = {}
trigs: dict[str, list[tuple]] = {}
for cid, fn in CRITERIA:
    lst = trigger_list(fn)
    trigs[cid] = lst
    real_lats = sorted(t[7] for t in lst if t[5])
    row = {
        "triggers": len(lst),
        "realHits": len({t[4] for t in lst if t[5]}),
        "falseTriggers": sum(1 for t in lst if t[6] < 100),
        "falseRate": (sum(1 for t in lst if t[6] < 100) / len(lst)) if lst else None,
        "latP50": statistics.median(real_lats) if real_lats else None,
        "latP95": pctl(real_lats, .95),
        "latMax": max(real_lats) if real_lats else None,
        "in50_strict_hits": len({t[4] for t in lst if t[5] and t[9]}),
        "in50_strict_rate": len({t[4] for t in lst if t[5] and t[9]}) / 1681,
        "W": {}, "T": {},
    }
    for N in (1, 3, 5):
        row["W"][str(N)] = simulate(lst, "window", N)
        row["T"][str(N)] = simulate(lst, "trip", N)
    computed[cid] = row
    say(f"{cid:<16} trig={row['triggers']:>6} hits={row['realHits']:>4} "
        f"false={row['falseTriggers']:>5} fRate={(row['falseRate'] or 0)*100:>8.3f}% "
        f"latP50={(row['latP50'] or 0):>10.6f} in50={row['in50_strict_hits']:>4} "
        f"W={[row['W'][str(N)]['captured'] for N in (1,3,5)]} "
        f"T={[row['T'][str(N)]['captured'] for N in (1,3,5)]} "
        f"QfalseW5={row['W']['5']['quotaEatenByFalse']}")

data = json.loads(OUT_JSON.read_text(encoding="utf-8-sig"))
def close(a, b) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-9)
    return a == b

def compare_obj(label: str, got, expected) -> bool:
    if isinstance(expected, dict):
        if not isinstance(got, dict):
            return False
        return all(k in got and compare_obj(label + "." + k, got[k], v) for k, v in expected.items())
    same = close(got, expected)
    if not same:
        say(f"  DIFF {label}: computed={got!r} expected={expected!r}")
    return same

all_equal = True
for cid, row in computed.items():
    got = data["criteria"].get(cid)
    if got is None:
        all_equal = False
        say(f"  MISSING {cid}")
        continue
    for key in ("triggers", "realHits", "falseTriggers", "falseRate", "latP50", "latP95", "latMax",
                "in50_strict_hits", "in50_strict_rate", "W", "T"):
        same = compare_obj(cid + "." + key, row[key], got[key])
        all_equal &= same
check("all 15 criteria, 3D fields, W/T quota objects equal _dA_data.json", all_equal)

# Parse the master table from _dA_out.txt and compare all visible cells.
out_lines = OUT_TXT.read_text(encoding="utf-8-sig").splitlines()
table_rows = {}
for ln in out_lines[50:65]:
    parts = [x.strip() for x in ln.split("|")]
    if len(parts) >= 10:
        table_rows[parts[0]] = parts
table_equal = True
for cid, row in computed.items():
    p = table_rows.get(cid)
    if not p:
        table_equal = False
        say(f"  MISSING table row {cid}")
        continue
    def num(s: str) -> float:
        return float(s)
    vals = [row["triggers"], row["realHits"], row["falseTriggers"], row["falseRate"] * 100 if row["falseRate"] is not None else None,
            row["latP50"], row["latP95"], row["in50_strict_hits"]]
    expected_str = [p[1], p[2], p[3], None if p[4] == "N/A" else p[4],
                    None if p[5] == "N/A" else p[5], None if p[6] == "N/A" else p[6], p[7]]
    for k, (a, b) in enumerate(zip(vals, expected_str)):
        same = (a is None and b is None) or (b is not None and math.isclose(float(a), float(b), abs_tol=5e-4))
        table_equal &= same
        if not same:
            say(f"  TABLE DIFF {cid} field{k}: {a} vs {b}")
    for idx, N in enumerate((1, 3, 5)):
        table_equal &= int(p[8].split()[idx]) == row["W"][str(N)]["captured"]
        table_equal &= int(p[9].split()[idx]) == row["T"][str(N)]["captured"]
    table_equal &= int(p[10]) == row["W"]["5"]["quotaEatenByFalse"]
check("all 15 table rows in _dA_out.txt:49-65 equal recomputation", table_equal)

# Four independent calibration baselines vs upstream references.
mref = json.loads(METRICS_JSON.read_text(encoding="utf-8-sig"))
qref = json.loads(QUOTA_JSON.read_text(encoding="utf-8-sig"))
cal_map = {"CAL-C1-k10": "C1-k10", "CAL-C1-k25": "C1-k25",
           "CAL-C4-t40": "C4-t40", "CAL-C5-k10t30": "C5-k10t30"}
cal_ok = True
for cal_id, ref_id in cal_map.items():
    row = computed[cal_id]
    ok = (row["triggers"] == mref[ref_id]["triggers"] and row["realHits"] == mref[ref_id]["realHits"])
    for N in (1, 3, 5):
        ok &= row["W"][str(N)]["captured"] == qref["results"][ref_id][f"window{N}"]["captured"]
        ok &= row["T"][str(N)]["captured"] == qref["results"][ref_id][f"trip{N}"]["captured"]
    cal_ok &= ok
    check(f"calibration {ref_id} vs upstream JSON", ok)
check("calibration PASS=4 FAIL=0", cal_ok)

# Independent counterparts of the 12 assertions listed in _dA_check.txt.
c1_map = {t[4]: t[1] for t in trigs["CAL-C1-k10"]}
diff_detail: dict[str, tuple[str, int, int, float]] = {}
for cid, _ in CRITERIA:
    if not cid.startswith("D"):
        continue
    mine = {t[4]: t[1] for t in trigs[cid]}
    common = set(mine) & set(c1_map)
    n_diff = sum(1 for k in common if mine[k] != c1_map[k])
    rate = (n_diff / len(common) * 100) if common else 0.0
    status = "DEGENERATE" if not mine else ("DISTINCT" if n_diff else "SAME_AS_C1")
    diff_detail[cid] = (status, len(common), n_diff, rate)
    say(f"DIFF_VS_C1 {cid:<16} common={len(common):>6} different={n_diff:>6} rate={rate:>6.2f}% {status}")
# Compare printed rates with _dA_out.txt:261-271.
diff_table_ok = True
for ln in out_lines[260:271]:
    m = re.search(r"(D[1-5][^ ]*)\s+与 C1-k10 共同触发游程=\s*(\d+) 其中触发拍不同=\s*(\d+) \(\s*([0-9.]+)%\)", ln)
    if m:
        cid, common, n_diff, rate = m.group(1), int(m.group(2)), int(m.group(3)), float(m.group(4))
        got = diff_detail.get(cid)
        diff_table_ok &= got is not None and got[1] == common and got[2] == n_diff and math.isclose(got[3], rate, abs_tol=0.005)
check("11 difference-rate rows in _dA_out.txt:261-271 equal recomputation", diff_table_ok)
# ------------------------------------------------------------------ formal bound recomputations
say("\n=== 4. BOUND TABLES / E AND S PITFALLS ===")
TAUS = (10, 18, 25, 30, 40, 45, 50, 60, 70, 80, 90, 99, 100)
base_rate_rows = {}
for tau in TAUS:
    alive = [r for r in records if r["dfin"] > tau]
    a_real = sum(1 for r in alive if r["is_real"])
    a_fb = sum(1 for r in alive if r["dfin"] < 100 and not r["is_real"])
    br = a_real / len(alive) if alive else None
    base_rate_rows[tau] = [len(alive), a_real, a_fb, br]
    say(f"base_rate τ={tau:>3}: A={len(alive):>5} real={a_real:>4} falseB={a_fb:>5} br={br*100:>9.4f}%")
br_ok = True
for tau, vals in data["bound_baserate"].items():
    br_ok &= compare_obj(f"bound_baserate[{tau}]", base_rate_rows[int(tau)], vals)
check("13 base-rate rows equal _dA_data.json", br_ok)
check("13 base rates monotone nondecreasing",
      all(base_rate_rows[a][3] <= base_rate_rows[b][3] for a, b in zip(TAUS, TAUS[1:])))
check("τ=50 precision surrogate <= 33.2279%", math.isclose(base_rate_rows[50][3] * 100, 33.2279, abs_tol=5e-5),
      f"{base_rate_rows[50][3]*100:.6f}%")

# Signature stream: deliberately recompute coarse and exact forms independently.
def signature_set(r: dict, tau: float, coarse: bool) -> set[tuple]:
    T, i, j = r["T"], r["i"], r["j"]
    D = r["D"]
    if coarse:
        dsig = bucket(D) if D is not None else "NONE"
    else:
        dsig = round(D, 3) if D is not None else None
    P = r["prev_len"]
    psig = ("P0" if P is None else "P1" if P <= 3 else "P2" if P <= 8 else "P3") if coarse else P
    word_c, word_e, S = "", [], set()
    x = i + 1
    while x <= j and elapsed(T, i, x) <= tau:
        g = gap(T, x)
        if coarse:
            word_c += bucket(g)
            S.add((x - i, word_c, dsig, psig))
        else:
            word_e.append(round(g, 3))
            S.add((x - i, tuple(word_e), dsig, psig))
        x += 1
    return S

# Pair each causal prefix point with its exact signature. This allows construction
# of a concrete deterministic lookup-table predicate phi(signature)->{0,1}.
def signature_pairs(r: dict, tau: float, coarse: bool) -> list[tuple[int, tuple]]:
    T, i, j = r["T"], r["i"], r["j"]
    D = r["D"]
    if coarse:
        dsig = bucket(D) if D is not None else "NONE"
    else:
        dsig = round(D, 3) if D is not None else None
    P = r["prev_len"]
    psig = ("P0" if P is None else "P1" if P <= 3 else "P2" if P <= 8 else "P3") if coarse else P
    word_c, word_e, pairs = "", [], []
    x = i + 1
    while x <= j and elapsed(T, i, x) <= tau:
        g = gap(T, x)
        if coarse:
            word_c += bucket(g)
            pairs.append((x, (x - i, word_c, dsig, psig)))
        else:
            word_e.append(round(g, 3))
            pairs.append((x, (x - i, tuple(word_e), dsig, psig)))
        x += 1
    return pairs

prefix_rows = {}
for tau in (18, 25, 30, 40, 45, 50):
    counts: Counter = Counter()
    real_sets: list[set] = []
    false_sets: list[set] = []
    U: set = set()
    empty_real = 0
    for r in records:
        S = signature_set(r, tau, True)
        if r["is_real"]:
            if S:
                real_sets.append(S)
                U |= S
            else:
                empty_real += 1
        elif r["dfin"] < 100:
            false_sets.append(S)
            counts.update(S)
    lb1 = max(min(counts[s] for s in S) for S in real_sets) if real_sets else 0
    ub_naive = sum(1 for S in false_sets if S & U)
    n_cov = len(real_sets)
    prec = n_cov / (n_cov + lb1) if n_cov + lb1 else None
    prefix_rows[tau] = [n_cov, empty_real, lb1, ub_naive, prec]
    say(f"prefix τ={tau:>2}: n_cov={n_cov} empty_real={empty_real} LB1={lb1} UB_naive={ub_naive} precision<={prec*100:.4f}%")
prefix_ok = True
for tau, vals in data["bound_prefix"].items():
    prefix_ok &= compare_obj(f"bound_prefix[{tau}]", prefix_rows[int(tau)], vals)
check("6 coarse-signature prefix rows equal _dA_data.json", prefix_ok)
check("claimed LB1 / precision / empty-prefix values",
      prefix_rows[18][:5] == [1672, 9, 4056, 26617, 1672/(1672+4056)] and
      prefix_rows[50][:3] == [1678, 3, 1638] and
      math.isclose(prefix_rows[50][4]*100, 50.6031, abs_tol=5e-5),
      f"τ18={prefix_rows[18]} τ50={prefix_rows[50]}")
check("all 12 self-check counterparts from independently recomputed values",
      len(records) == 28381 and aligned == 1681 and cal_ok and
      all(row[s][str(N)]["captured"] <= row["realHits"] for row in computed.values() for s in ("W", "T") for N in (1, 3, 5)) and
      all(row["W"][str(N)]["captured"] <= ideal_w[N] and row["T"][str(N)]["captured"] <= ideal_t[N]
          for row in computed.values() for N in (1, 3, 5)) and
      all(row[s][str(N)]["captured_strict50"] <= row[s][str(N)]["captured"]
          for row in computed.values() for s in ("W", "T") for N in (1, 3, 5)) and
      all(not any(tok in data["criteria"][cid]["note"] or tok in cid for tok in ("P95", "P99", "CAP", "percentile"))
          for cid, _ in CRITERIA if cid.startswith("D")) and
      base_rate_rows[50][3] <= 0.35 and prefix_rows[50][2] > 0 and prefix_rows[18][1] > 0 and
      all(row["in50_strict_hits"] <= 1621 for row in computed.values()) and
      all(v[0] in ("DISTINCT", "DEGENERATE") for v in diff_detail.values()))

# Exact signature: check why universal information-theoretic impossibility is not established.
for tau in (18, 50):
    counts, real_sets, false_sets, U = Counter(), [], [], set()
    for r in records:
        if not r["is_real"] and r["dfin"] >= 100:
            continue
        S = signature_set(r, tau, False)
        if r["is_real"]:
            if S:
                real_sets.append(S)
                U |= S
        else:
            false_sets.append(S)
            counts.update(S)
    lb1_exact = max(min(counts[s] for s in S) for S in real_sets) if real_sets else 0
    ub_exact = sum(1 for S in false_sets if S & U)
    check(f"exact-signature LB1=0 / UB_naive=1 at τ={tau}", (lb1_exact, ub_exact) == (0, 1),
          f"LB1={lb1_exact} UB_naive={ub_exact}")

real_e_gt50 = sum(1 for r in records if r["is_real"] and r["e"] is not None and r["e"] > 50)
real_e_none = sum(1 for r in records if r["is_real"] and r["e"] is None)
check("real e>50 / e unknown / e<=50 counts", (real_e_gt50, real_e_none, 1681-real_e_gt50-real_e_none) == (56, 4, 1621),
      f"gt50={real_e_gt50} none={real_e_none} le50={1681-real_e_gt50-real_e_none}")
check("1621/1681 numeric", math.isclose(1621/1681*100, 96.4307, abs_tol=5e-5), f"{1621/1681*100:.6f}%")

# Critical semantic test: w+e<=50 is sufficient under the corpus bracket S_hat-S in [0,e],
# but is not a measured physical-S latency. The predicate can pass while physical latency
# remains unknown; no code path measures S or action completion C.
s_latency_measured = any("physicalS" in ln or "saveComplete" in ln for ln in RUN_PY.read_text(encoding="utf-8-sig").splitlines())
check("runner does not identify a measured physical S/save-completion C", not s_latency_measured)

# ------------------------------------------------------------------ claims, wording, checks, scope
say("\n=== 5. CLAIM WORDING / FORBIDDEN TERMS / SCOPE ===")
out_text = OUT_TXT.read_text(encoding="utf-8-sig")
design_text = DESIGN_MD.read_text(encoding="utf-8-sig")
check("D5-phase latP50=105.151 and in50=18 from recomputation",
      math.isclose(computed["D5-phase"]["latP50"], 105.151, abs_tol=5e-4) and computed["D5-phase"]["in50_strict_hits"] == 18,
      f"latP50={computed['D5-phase']['latP50']:.6f} in50={computed['D5-phase']['in50_strict_hits']}")
check("D5-phase W5=66 / D4-burst in50=1569 / fRate=93.990%",
      computed["D5-phase"]["W"]["5"]["captured"] == 66 and
      computed["D4-burst"]["in50_strict_hits"] == 1569 and
      math.isclose(computed["D4-burst"]["falseRate"]*100, 93.990, abs_tol=5e-4))
check("D1-MMM falseRate=0 but quota artifact Qfalse@W5=1",
      computed["D1-word-MMM"]["falseTriggers"] == 0 and computed["D1-word-MMM"]["W"]["5"]["quotaEatenByFalse"] == 1)
check("D1-LLL falseRate=0 but quota artifact Qfalse@W5=1",
      computed["D1-word-LLL"]["falseTriggers"] == 0 and computed["D1-word-LLL"]["W"]["5"]["quotaEatenByFalse"] == 1)
check("output explicitly labels latP50 / in50 strict as S_hat lower-bound / strict e accounting",
      "latP50 仅真实命中子集" in out_text and "S_hat 锚下界" in out_text and
      "触发等待 + 逐游程 e <= 50ms" in out_text and "waitAfterS_hat 是下界" in out_text)
check("U1-U8 are present as unverified", all(f"U{i}." in out_text for i in range(1, 9)) and "未验项" in out_text)
check("U5 explicitly withholds arbitrary-real-valued-predicate info-theoretic claim",
      "信息论级不可判定性未验" in out_text and "不作「任意谓词皆不可能」" in out_text)
check("design explicitly distinguishes S_hat lower bound from physical S",
      "所有 `waitAfterS_hat` / `latP50` 都是下界" in design_text and
      "物理起点 S 的微秒点估计语料不可得" in design_text)
check("design does not claim scheme feasibility from low false rate",
      "方案可行" not in design_text and "工程可行" not in design_text)
check("design states evidence 3 is restricted to feature class",
      "证据③的 `LB1` 限定于" in design_text and "不作" in design_text)
# Contradictory universal wording is evidence of a claim-scope defect, not a passing check.
universal_out = [f"{i+1}:{ln.strip()}" for i, ln in enumerate(out_text.splitlines())
                 if ("任意" in ln or "任何" in ln) and ("前缀谓词" in ln or "(t,f)" in ln)]
say("UNIVERSAL_WORDING_CANDIDATES=" + json.dumps(universal_out, ensure_ascii=False))
# Record the claim-scope defect: evidence 4 is labeled universal, while U5 and
# S_OBSERVABILITY.md say the observational e limitation is not an online-system proof.
e_universal_claim = "是**任何 (t,f) 前缀判据的上确界**" in out_text
e_scope_limited = "S 不可精确观测不构成 :177 无法满足的证明" in (ROOT / "lead/dstart_observable_20261107/S_OBSERVABILITY.md").read_text(encoding="utf-8-sig")
check("e hard bound is only an offline verifiability bound, NOT an online physical upper bound",
      not (e_universal_claim and e_scope_limited),
      f"universal_wording={e_universal_claim} upstream_scope_limit={e_scope_limited}; see _dA_out.txt:253 and S_OBSERVABILITY.md:173-179")
# Concrete logical counterexample to the universal reading: let physical S be at the
# lower end of the interval for all 60 events, and let the online detector act at
# S+0. The offline strict test still rejects them because external e>50 or e unknown;
# an online predicate with an independent clock is not subject to the external gap.
offline_strict_possible = 1621
online_counterexample_possible = 1681
check("counterexample: external e cannot cap online physical-S compliance",
      offline_strict_possible < online_counterexample_possible,
      f"offline verifiable={offline_strict_possible}, conceptual online possible={online_counterexample_possible}; no online execution performed")

BANNED_PAT = re.compile(r"ctypes|OpenProcess|ReadProcessMemory|WriteProcessMemory|VirtualAllocEx|CreateRemoteThread|SetWindowsHookEx|TerminateProcess|MiniDump|SuspendThread|StackWalk|gamemd|ra2loader|YURI\.exe|taskkill", re.I)
script_texts = {p.name: p.read_text(encoding="utf-8-sig") for p in (RUN_PY, PROBE_PY)}
check("no forbidden process/sampling identifiers in _dA_run.py/_dA_probe.py",
      all(not BANNED_PAT.search(t) for t in script_texts.values()))
check("_dA_check.txt PASS=12 FAIL=0 and self-hash line differs from final file",
      "合计 PASS=12 FAIL=0" in CHECK_TXT.read_text(encoding="utf-8-sig") and
      hashlib.sha256(CHECK_TXT.read_bytes()).hexdigest() == "434e358b82ae7e795a2c3c6952ebccf128095e5a1523e250e7aa01e3a1563d1c" and
      "404c07a5ee662430bb801cfcad8e6e83c5867a7b428345137b3b78319e19a4ba" in CHECK_TXT.read_text(encoding="utf-8-sig"))
check("upstream CRITERIA_COMPARE.md warning: strict S+50 proof unavailable",
      ":177 的严格 S+50ms 核算需物理 S，本次语料不可得" in (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md").read_text(encoding="utf-8-sig"))
check("S_OBSERVABILITY.md warning: S unobservability is not proof of online impossibility",
      "S 不可精确观测不构成 :177 无法满足的证明" in (ROOT / "lead/dstart_observable_20261107/S_OBSERVABILITY.md").read_text(encoding="utf-8-sig"))
check("RULING_D30.md forbids extrapolating low false rate / coverage to feasibility",
      "不得把误报率高外推为栈采样不可行，也不得把99.76%覆盖率外推为方案可行" in (ROOT / "lead/d30_ruling_20261106/RULING_D30.md").read_text(encoding="utf-8-sig"))

# The coarse signature used by LB1 is (x-i, cumulative bucket word, bucket(D),
# bucket(prev_len)). Several implemented D predicates do not receive that signature:
# they use prev_min numeric value, first gap only, a three-gap rising window, or an
# L/X/G count. Verify this mismatch against the actual trigger function definitions.
run_src = RUN_PY.read_text(encoding="utf-8-sig").splitlines()
predicate_span = "\n".join(run_src[245:362])
sig_span = "\n".join(run_src[569:581])
outside_summary = all(tok in predicate_span for tok in
                      ("r[\"prev_min\"]", "cfirst = bkt", "gs[-3] < gs[-2] < gs[-1]", "pscore = sum"))
check("feature-class mismatch: implemented predicates use summaries absent from LB1 signature",
      outside_summary and "word" in sig_span and "prev_len" in sig_span,
      "_dA_run.py:281-360 vs _dA_run.py:569-581; LB1 is for sig_stream, not all D1-D5 predicates")

# Concrete deterministic lookup predicate on exact causal signatures at tau=50:
# accept signatures observed among real runs; at most one first triggering point
# per run. Since U_R and the falseB signature sets are disjoint (probe's
# UB_naive=1 counts one false run with an empty prefix), this predicate has
# 1678 real triggers and zero false triggers by construction.
TAU_EXACT = 50.0
real_exact_sigs: set[tuple] = set()
def exact_lookup_trigger(r: dict) -> int | None:
    for idx, sig in signature_pairs(r, TAU_EXACT, False):
        if sig in real_exact_sigs:
            return idx
    return None

for r in records:
    if r["is_real"]:
        real_exact_sigs.update(sig for _, sig in signature_pairs(r, TAU_EXACT, False))
lookup_trig = trigger_list(exact_lookup_trigger)
lookup_real = sum(1 for t in lookup_trig if t[5])
lookup_false = sum(1 for t in lookup_trig if t[6] < 100)
lookup_precision = lookup_real / (lookup_real + lookup_false) if lookup_trig else None
lookup_strict = len({t[4] for t in lookup_trig if t[5] and t[9]})
look_w = {N: simulate(lookup_trig, "window", N)["captured"] for N in (1, 3, 5)}
check("exact-signature lookup predicate refutes universal 33.2279% precision bound",
      lookup_precision > base_rate_rows[50][3] and (lookup_real, lookup_false) == (1678, 1),
      f"trig={len(lookup_trig)} real={lookup_real} false={lookup_false} precision={lookup_precision:.6f} "
      f"(bound={base_rate_rows[50][3]:.6f})")
say(f"EXACT_LOOKUP in50_strict={lookup_strict}/1681 W1/W3/W5={look_w} "
    "(still not an engineering feasibility claim: physical S/C/Q5 unverified)")

# A deliberately constructed richer predicate exposes the base-rate argument's logical gap:
# a mixture's precision can exceed max baseline rate when it fires at different rates
# across distinguishable groups. The bound itself is recomputed correctly, but its
# stated universal interpretation is invalid.
n_real, n_false = 1681, 3355
rate_real, rate_false = 1.0, 0.01
mixture_precision = n_real * rate_real / (n_real * rate_real + n_false * rate_false)
check("counterexample: differential firing beats max single-τ base-rate bound",
      mixture_precision > base_rate_rows[50][3],
      f"precision={mixture_precision:.6f} > max_base_rate={base_rate_rows[50][3]:.6f}")

# Timing-model counterexample: external sampler gap e is an observational artifact;
# an online detector with independent clock could act before S_hat. This is conceptual
# from S_OBSERVABILITY.md:173-179 and is not an executed online measurement.
say("S_ONLINE_NOTE=S_OBSERVABILITY.md:173-179 says offline U does not bound online probe; no online measurement was run in this review.")

# Print a compact final verdict field for the workflow.
passes = sum(1 for ln in REPORT if ln.startswith("PASS "))
fails = sum(1 for ln in REPORT if ln.startswith("FAIL "))
say(f"\nSUMMARY PASS={passes} FAIL={fails}")
RESULT.write_text("\n".join(REPORT) + "\n", encoding="utf-8")
print(f"[written] {RESULT}")
