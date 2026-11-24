# -*- coding: utf-8 -*-
"""把 builder 打出的 unified diff 原样切成 9 个 ```diff 代码块，供设计稿拼接。"""
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = io.open(HERE / "_draft_semantics_build_out.txt", encoding="utf-8").read().splitlines()
i = next(k for k, l in enumerate(src) if l.startswith("--- a/qc151_trip.py"))
j = next(k for k, l in enumerate(src) if l.startswith("HUNK_HEADERS ="))
block = "\n".join(src[i:j]).rstrip("\n")

hunks = []
cur = None
for l in block.split("\n"):
    if l.startswith("@@ "):
        if cur:
            hunks.append(cur)
        cur = [l]
    elif cur is not None:
        cur.append(l)
if cur:
    hunks.append(cur)

assert len(hunks) == 9, f"期望 9 个 hunk，实得 {len(hunks)}"
FENCE = "`" * 3
OUT = "\n\n".join(FENCE + "diff\n" + "\n".join(h) + "\n" + FENCE for h in hunks)
p = HERE / "_hunks_frag.md"
p.write_text(OUT + "\n", encoding="utf-8", newline="\n")
print("HUNKS", len(hunks))
print("FRAG_BYTES", len((OUT + "\n").encode("utf-8")))
print("FENCE_COUNT", OUT.count(FENCE + "diff"))
