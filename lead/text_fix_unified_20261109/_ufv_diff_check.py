# _ufv_diff_check.py — 复核员独立复算 CANDIDATE_LF.diff（只读）
# 核：hunk 数、+/- 行数（+255/-13）、逐 hunk - 侧行数分布、- 侧区间与 E 判据块 5984-5990 是否相交
import re

DIFF = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff"
with open(DIFF, "rb") as f:
    lines = f.read().splitlines()

hunks = []
plus = minus = 0
cur = None
for ln in lines:
    if ln.startswith(b"@@"):
        m = re.match(rb"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", ln)
        assert m, ln
        old_start, old_cnt = int(m.group(1)), int(m.group(2) or 1)
        cur = {"old_start": old_start, "old_cnt": old_cnt, "m": 0, "p": 0}
        hunks.append(cur)
    elif ln.startswith(b"+++") or ln.startswith(b"---"):
        continue
    elif cur is not None:
        if ln.startswith(b"+"):
            plus += 1
            cur["p"] += 1
        elif ln.startswith(b"-"):
            minus += 1
            cur["m"] += 1

print(f"hunk 数 = {len(hunks)}")
print(f"总计 +{plus}/-{minus}")
E_LO, E_HI = 5984, 5990
for i, h in enumerate(hunks, 1):
    lo, hi = h["old_start"], h["old_start"] + h["old_cnt"] - 1
    overlap = not (hi < E_LO or lo > E_HI)
    print(f"H{i:02d} -侧区间 {lo}..{hi} 删 {h['m']} 行  含E块5984-5990={overlap}")
print(f"E块相交的 hunk 数 = {sum(1 for h in hunks if not (h['old_start']+h['old_cnt']-1 < E_LO or h['old_start'] > E_HI))}")
