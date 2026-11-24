import os, re, hashlib
ROOT = "D:/Project/ra2-campaign-forge"
FILES = {
    "PENDING": "lead/PENDING_DECISIONS.md",
    "GOAL": "lead/GOAL_THREE_TARGETS_20261018.md",
    "FIX": "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",
}
data = {}
for k, rel in FILES.items():
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as f:
        data[k] = f.read().splitlines()
    print(f"{k} LINES = {len(data[k])}")

print("\n--- four-object exact name hits in two ledgers (reviewer correction) ---")
for name in ["check_d27", "check_d29", "check_d30", "check_d28", "check_d26", "check_d25", "_rs_carrier_scan", "carrier_scan", "SELF_TEST", "REFSYNC_SCOPE_FIX"]:
    hits = {k: [i+1 for i, l in enumerate(v) if name in l] for k, v in data.items() if k in ("PENDING", "GOAL")}
    print(f"{name}: PENDING={hits['PENDING']} GOAL={hits['GOAL']}")

print("\n--- GATE_RUN explicit '门禁 ... 实跑 ... exit=0' lines in PENDING ---")
for i, l in enumerate(data["PENDING"], 1):
    if "门禁" in l and "实跑" in l and "exit=0" in l:
        g = re.search(r"check_(d\d+|[A-Za-z0-9_-]+)\.py", l)
        print(f"PENDING:{i} script={g.group(0) if g else '<N-1 or none>'} | {l[:160]}")

print("\n--- exact phrases count in two ledgers ---")
for ph in ["验证通过", "机械检查通过", "逐项通过", "SELF_TEST", "REFSYNC_SCOPE_FIX"]:
    c = {k: sum(1 for l in v if ph in l) for k, v in data.items() if k in ("PENDING", "GOAL")}
    print(f"{ph!r}: PENDING={c['PENDING']} GOAL={c['GOAL']}")

print("\n--- token tallies (per-line counts) ---")
pat_exit0 = re.compile(r"exit\s*=\s*0|EXIT\s*=\s*0|CL_EXIT=0|LINK_EXIT=0|final_exit=0", re.I)
pat_pass = re.compile(r"\bPASS\b|SELF_TEST\s*=\s*PASS")
for k in ("PENDING", "GOAL"):
    v = data[k]
    e = [i+1 for i, l in enumerate(v) if pat_exit0.search(l)]
    p = [i+1 for i, l in enumerate(v) if pat_pass.search(l)]
    print(f"{k}: exit0-like={len(e)} PASS-token={len(p)}")
print("GATE_EXIT0_LINES(PENDING) =", [i+1 for i,l in enumerate(data["PENDING"]) if "门禁" in l and "实跑" in l and "exit=0" in l])

print("\n--- reviewer's 7 corrections: raw text ---")
for rel, n in [("lead/PENDING_DECISIONS.md",101),("lead/PENDING_DECISIONS.md",113),("lead/PENDING_DECISIONS.md",103),("lead/PENDING_DECISIONS.md",109),("lead/d29_ruling_20261106/RULING_D29.md",19),("lead/d29_ruling_20261106/RULING_D29.md",14),("lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",234),("lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",258),("lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md",380)]:
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as f:
        d = f.read().splitlines()
    print(f"{rel}:{n} = {d[n-1][:240]!r}")

print("\n--- RULING documents: check_d*.py / PASS / exit=0 occurrences and ## heading counts ---")
for d in ["d27", "d29", "d30", "d28"]:
    rel = f"lead/{d}_ruling_20261106/RULING_{d.upper()}.md"
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()
    lines = txt.splitlines()
    print(f"{rel}: lines={len(lines)} h2={sum(1 for x in lines if x.startswith('## '))} "
          f"check_d*={'check_d' in txt} PASS={'PASS' in txt} exit0_mentions={txt.count('exit=0')}")

print("\n--- strict binding lines in census report ---")
rel = "lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md"
with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as f:
    L = f.read().splitlines()
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
bs = [(i+1, m.group(1), m.group(2)) for i, l in enumerate(L) if (m := pat.match(l))]
print("STRICT_BINDING_LINES =", len(bs), "ALL_64HEX =", all(re.fullmatch(r"[0-9a-f]{64}", b[1]) for b in bs))
BASE9 = [
"3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
"2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
"99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c",
"2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f",
"3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c",
"2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14",
"6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd",
"9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57",
"83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e",
]
print("ALL_MATCH_BASE =", [b[1] for b in bs] == BASE9)
