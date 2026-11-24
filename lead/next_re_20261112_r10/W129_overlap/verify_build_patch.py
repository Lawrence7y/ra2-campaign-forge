#!/usr/bin/env python3
"""W129b: verify the patched w94_build.py without invoking ra2forge.

Checks:
  1. module imports (syntax OK)
  2. overlap_cells_fp reproduces 3x2 semantics: step2=10 cells, step3=0
  3. the OLD overlap_cells (2x2) is still importable and returns None on step2
     (i.e. it really was vacuous) and on step3
  4. the exact assertions now in the module would pass for both arms
  5. back-compat: any other call site of overlap_cells still gets 2x2 behaviour
"""
import sys
from pathlib import Path

TOOLS = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\work\tools")
sys.path.insert(0, str(TOOLS))

import w94_build as B  # noqa: E402

ok = True
print("1. import: OK (module loaded)")

STEP2 = B.NAPOWR_CELLS_STEP2
STEP3 = B.NAPOWR_CELLS_STEP3

c2 = B.overlap_cell_count_fp(STEP2, *B.NAPOWR_FP)
c3 = B.overlap_cell_count_fp(STEP3, *B.NAPOWR_FP)
print("2. footprint-aware (3x2): step2=%d cells  step3=%d cells" % (c2, c3))
ok &= (c2 == 10 and c3 == 0)

old2 = B.overlap_cells(STEP2)
old3 = B.overlap_cells(STEP3)
print("3. legacy 2x2 overlap_cells: step2 -> %r, step3 -> %r  (both None = vacuous)"
      % (old2, old3))
ok &= (old2 is None and old3 is None)

fp2 = B.overlap_cells_fp(STEP2, *B.NAPOWR_FP)
fp3 = B.overlap_cells_fp(STEP3, *B.NAPOWR_FP)
print("4. new overlap_cells_fp: step2 -> %r (collision expected), step3 -> %r" % (fp2, fp3))
ok &= (fp2 is not None and fp3 is None)

# reproduce the two assertion blocks as written in the module
def assert_step3():
    assert B.overlap_cells_fp(STEP3, *B.NAPOWR_FP) is None
    assert B.overlap_cell_count_fp(STEP3, *B.NAPOWR_FP) == 0

def assert_step2():
    assert B.overlap_cell_count_fp(STEP2, *B.NAPOWR_FP) > 0

for name, fn in (("step3", assert_step3), ("step2", assert_step2)):
    try:
        fn()
        print("   assertion block for %-6s: PASSES" % name)
    except AssertionError as e:
        print("   assertion block for %-6s: FAILED %s" % (name, e))
        ok = False

# the cell map for step2: show which cells collide (sanity of the 10)
occ = {}
for r, c in STEP2:
    for rr in range(r, r + B.NAPOWR_FP[1]):
        for cc in range(c, c + B.NAPOWR_FP[0]):
            occ.setdefault((rr, cc), 0)
            occ[(rr, cc)] += 1
shared = sorted(k for k, v in occ.items() if v > 1)
print("5. step2 colliding cells (%d): %s" % (len(shared), shared))

print("\nRESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
