# -*- coding: utf-8 -*-
"""读 ddraw.ini 的游戏专属段（生效覆盖值）。只读。"""
P = r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.ini"
txt = open(P, encoding="latin1").read()
lines = txt.split("\n")
want = {"[gamemd]", "[ra2md]", "[Yuri's Revenge]", "[ddraw]"}
cur = None
buf = {k: [] for k in want}
for i, l in enumerate(lines, 1):
    s = l.strip()
    if s.startswith("[") and s.endswith("]"):
        cur = s
    elif cur in want and ("=" in s) and s and not s.startswith(";"):
        buf[cur].append((i, s))
for k in ("[ddraw]", "[gamemd]", "[ra2md]", "[Yuri's Revenge]"):
    print("=" * 60)
    print(k, "  (%d 键)" % len(buf[k]))
    for ln, s in buf[k][:40]:
        print("   L%-4d %s" % (ln, s))
