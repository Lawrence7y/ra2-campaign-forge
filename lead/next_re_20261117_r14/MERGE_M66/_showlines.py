p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
lines = open(p, encoding="utf-8").read().split("\n")
for n in (1, 17, 60, 74, 76, 77, 98, 110, 124, 126, 127, 141):
    ln = lines[n-1]
    print(f"===== LINE {n} (len={len(ln)}) =====")
    print(ln[:1200] + (" ...[TRUNC]" if len(ln) > 1200 else ""))
    print()
