# -*- coding: utf-8 -*-
# _fg_recheck.py —— 升格终评独立复算（只读既有件；stdout 输出）
import json, statistics

D = r"D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107"

print("== [1] O1 括注算术（_dD_PHYSICAL_S_ALIGNMENT.md:126「合计 ≤ 50ms 的 2%」） ==")
print("1/50 = %.1f%% ; 2/50 = %.1f%% ; 2/20 = %.1f%%" % (100*1/50, 100*2/50, 100*2/20))

print()
print("== [2] 维度 B：从 _dB_anchor_recompute_data.json 独立重算 12 格 ==")
d = json.load(open(D + "/_dB_anchor_recompute_data.json", encoding="utf-8"))
print("top-level keys =", sorted(d.keys()))
print("e_med_full =", d.get("e_med_full"))
# 找逐触发明细
td_key = None
for k in d.keys():
    v = d[k]
    if isinstance(v, dict) and any("abs-P95x2" in str(kk) for kk in v.keys()):
        td_key = k
print("per-id detail key =", td_key)
E = 2.510999998776242
EXPECT = {  # _dB_anchor_recompute_out.txt:50-55 主表直读值
    "C2-abs-P95x2": (29, 5, 29, 66.334, 70.931, 321.002),
    "C3-r4":        (24, 24, 24, 125.884, 127.491, 440.389),
    "C3-r4-clean":  (24, 24, 24, 128.284, 130.237, 461.598),
    "C3-r8":        (16, 16, 16, 251.709, 256.261, 258.378),
    "C3-r8-clean":  (16, 16, 16, 254.247, 258.835, 260.904),
    "C3-r12":       (15, 15, 15, 377.385, 385.601, 387.990),
}
details = d[td_key]
allok = True
for cid, exp in EXPECT.items():
    entry = details[cid]
    waits = None
    if isinstance(entry, dict):
        for cand in ("waits", "wait_list", "waitMs", "wait_ms", "waits_ms", "triggers"):
            if cand in entry:
                waits = entry[cand]
                break
        if waits is None and "trigger_details" in entry:
            waits = [t["wait"] for t in entry["trigger_details"]]
    if isinstance(entry, list) and entry and isinstance(entry[0], dict):
        waits = [t.get("wait") for t in entry if t.get("wait") is not None]
    if waits is None:
        print(cid, "STRUCT?  keys=", list(entry.keys()) if isinstance(entry, dict) else type(entry))
        allok = False
        continue
    n = len(waits)
    ge100 = sum(1 for w in waits if w >= 100.0)
    gt50e = sum(1 for w in waits if w + E > 50.0)
    mn, md, mx = min(waits), statistics.median(waits), max(waits)
    ok = (n, ge100, gt50e) == exp[:3] and all(abs(a-b) < 0.002 for a, b in zip((mn, md, mx), exp[3:]))
    allok = allok and ok
    print("%-14s n=%2d >=100=%2d +e>50=%2d min/med/max=%.3f/%.3f/%.3f  vs exp %s  %s"
          % (cid, n, ge100, gt50e, mn, md, mx, exp, "MATCH" if ok else "MISMATCH"))
print("B_RECHECK_ALL_OK =", allok)

print()
print("== [3] 维度 C：从 _dC_cells.txt 独立重算 156 格不变式 ==")
rows = []
with open(D + "/_dC_cells.txt", encoding="utf-8", errors="replace") as f:
    for ln in f:
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 12 and parts[0] and parts[0][0] in "Cc" and parts[1] and parts[1][0] in "wt":
            try:
                cap, nf, up, ideal = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                dnf, dnc, dc = int(parts[6]), int(parts[7]), int(parts[8])
                dec, hits, grp = parts[9], int(parts[10]), parts[11]
            except ValueError:
                continue
            rows.append(dict(c=parts[0], s=parts[1], cap=cap, nf=nf, up=up, ideal=ideal,
                             dnf=dnf, dnc=dnc, dc=dc, dec=dec, hits=hits, grp=grp))
print("data rows =", len(rows))
decomp_bad = [r for r in rows if r["dc"] != r["dnf"] + r["dnc"]]
nonneg_bad = [r for r in rows if r["dnf"] < 0 or r["dnc"] < 0]
A = [r for r in rows if r["grp"].startswith("A")]
B = [r for r in rows if r["grp"].startswith("B")]
A_nf_eq_ideal = [r for r in A if r["nf"] == r["ideal"]]
B_preempt0 = [r for r in B if r["nf"] - r["cap"] == 0]
B_up_eq_ideal = [r for r in B if r["up"] == r["ideal"]]
cap_eq_ideal = [r for r in rows if r["cap"] == r["ideal"]]
print("decomp 违例 =", len(decomp_bad), " 非负违例 =", len(nonneg_bad))
print("A =", len(A), " B =", len(B), " A+B =", len(A)+len(B))
print("A 族 noFalse==ideal =", len(A_nf_eq_ideal), "/", len(A))
print("B 族 noFalse-captured==0 =", len(B_preempt0), "/", len(B),
      " 其中 capUpper==ideal =", sum(1 for r in B_preempt0 if r["up"] == r["ideal"]))
print("B 族 capUpper==ideal =", len(B_up_eq_ideal), "  全体 captured==ideal =", len(cap_eq_ideal))
print("C_RECHECK_OK =", (len(rows) == 156 and not decomp_bad and not nonneg_bad
      and len(A) == 54 and len(B) == 102 and len(A_nf_eq_ideal) == 54
      and len(B_preempt0) == 71 and len(B_up_eq_ideal) == 73 and not cap_eq_ideal))
