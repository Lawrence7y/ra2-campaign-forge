
# --- 方案丙（推荐）：命中溯源 + 覆盖度门禁 -----------------------------------
# 在 classify_line 的结果里补一个字段 hits=[命中的 needle 下标]，输出时打印：
#   HITSET {0}, {1}, {0,1} ... 以及 EXCLUSIVE(k) 计数
# 无需多次跑；一次运行即可从输出直接读出掩蔽量。
import os, io
LEAD = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]

def corpus():
    for dp, dn, fn in os.walk(LEAD):
        d = os.path.relpath(dp, LEAD).replace("\\", "/")
        if (0 if d == "." else d.count("/") + 1) > 2: dn[:] = []; continue
        for f in sorted(fn):
            if not f.endswith(".md"): continue
            p = os.path.join(dp, f)
            try: b = open(p, "rb").read()
            except OSError: continue
            if b"\x00" in b: continue
            yield os.path.relpath(p, LEAD).replace("\\", "/"), b.decode("utf-8", "replace")

from collections import Counter
pat = Counter(); excl = Counter(); total = 0
for rel, txt in corpus():
    for L in txt.splitlines():
        hs = tuple(i for i, n in enumerate(NEEDLES) if n in L)
        if not hs: continue
        total += 1; pat[hs] += 1
        if len(hs) == 1: excl[hs[0]] += 1
print("=== HITSET PROVENANCE LEDGER ===")
for hs, c in sorted(pat.items()):
    print("  HITSET %-10s -> %d lines  %s" % (str(hs), c,
          "<-- MASKED by union" if len(hs) > 1 else "exclusive"))
print("  TOTAL carrier lines = %d" % total)
for k, n in enumerate(NEEDLES):
    print("  EXCLUSIVE(needle[%d]=%r) = %d  %s" %
          (k, n, excl[k], "OK" if excl[k] else "!! NO INDEPENDENT WITNESS"))
masked = total - sum(excl.values())
print("  MASKED_LINES = %d / %d  (%.1f%%)" %
      (masked, total, 100.0 * masked / total if total else 0.0))
print("  COVERAGE_GATE = %s  (every needle must own >=1 exclusive line)" %
      ("PASS" if all(excl[k] for k in range(len(NEEDLES))) else "FAIL"))
print("  PER_NEEDLE_SELFTEST = %s" %
      {k: ("PASS" if excl[k] else "UNPROVEN") for k in range(len(NEEDLES))})
