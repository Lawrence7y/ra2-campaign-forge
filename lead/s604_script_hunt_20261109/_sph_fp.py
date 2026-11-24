import hashlib, os, time

BASE = r"D:\Project\ra2-campaign-forge"
EXPECT = [
    (r"lead\s604_script_gap_20261109\S604_SCRIPT_GAP.md",
     "593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    (r"lead\s604_exclusive_20261109\S604_EXCLUSIVITY.md",
     "823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    (r"lead\s604_attribution_20261108\S604_ATTRIBUTION.md",
     "8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
    (r"lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
     "5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    (r"lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    (r"lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
]

print("== A. six-file fingerprint recheck (hashlib, this round) ==")
for rel, esha, eb in EXPECT:
    p = os.path.join(BASE, rel)
    t0 = time.perf_counter()
    with open(p, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    st = os.stat(p)
    mt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
    print(f"{rel}|bytes={len(b)}|exp_bytes={eb}|bytes_match={len(b)==eb}|sha_match={h==esha}|sha256={h}|mtime={mt}|elapsed={time.perf_counter()-t0:.3f}s")

print("== B. ledger CR fingerprint and line count ==")
p = os.path.join(BASE, r"lead\GOAL_THREE_TARGETS_20261018.md")
with open(p, "rb") as f:
    b = f.read()
nl = b.count(b"\n")
crt = b.count(b"\r")
parts = b.split(b"\n")
crlines = [i + 1 for i, seg in enumerate(parts) if b"\r" in seg]
first = min(crlines) if crlines else None
last = max(crlines) if crlines else None
print(f"total_newlines={nl}|split_segments={len(parts)}|CR_total={crt}|CR_lines_count={len(crlines)}|CR_first_line={first}|CR_last_line={last}")

print("== C. write-domain inventory (bounded walk, prune .git/__pycache__/node_modules, cap 500 files) ==")
WD = os.path.join(BASE, r"lead\s604_script_hunt_20261109")
t0 = time.perf_counter()
dirs_v = 0
files = []
stop = False
for root, ds, fs in os.walk(WD):
    dirs_v += 1
    ds[:] = [d for d in ds if d not in (".git", "__pycache__", "node_modules")]
    for name in fs:
        fp = os.path.join(root, name)
        try:
            sz = os.path.getsize(fp)
        except OSError:
            sz = -1
        files.append((os.path.relpath(fp, WD), sz))
        if len(files) >= 500:
            ds[:] = []
            stop = True
            break
    if stop:
        break
print(f"dirsVisited={dirs_v}|files={len(files)}|elapsed={time.perf_counter()-t0:.3f}s")
for name, sz in sorted(files):
    print(f"  {sz}\t{name}")
