# -*- coding: utf-8 -*-
# _m5_extract.py —— 逐字抽取镜像区现状与三处源件改文（只读）
import json

BASE = "D:/Project/ra2-campaign-forge/"

def rd(rel):
    return open(BASE + rel, "r", encoding="utf-8").read().splitlines()

def show(rel, a, b, label, lenmarks=()):
    lines = rd(rel)
    print(f"===== {label} {rel} 行 {a}-{b}（文件总行数 {len(lines)}）=====")
    for i in range(a, b + 1):
        ln = lines[i - 1]
        extra = f"    [chars={len(ln)}]" if i in lenmarks else ""
        print(f"{i}: {ln}{extra}")
    print()

show("lead/b2b_design_20261106/B2B_DESIGN.md", 140, 168, "T1", lenmarks=(148, 150, 151))
show("lead/b2b_design_20261106/STATE_MATRIX.json", 1, 16, "T2")
show("lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md", 188, 196, "T3")
show("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md", 130, 136, "T4")
show("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md", 88, 112, "T5")

# 词频与行号核验
b2b_lines = rd("lead/b2b_design_20261106/B2B_DESIGN.md")
sm_lines = rd("lead/b2b_design_20261106/STATE_MATRIX.json")
b2b, sm = "\n".join(b2b_lines), "\n".join(sm_lines)
for pat in ("跑后任意", "任意文件状态", "下表与之逐行一致", "read_bytes/stat/write_bytes", "先于一切 pre 分支", "跑后读取正常"):
    print(f"count '{pat}': B2B_DESIGN.md={b2b.count(pat)}  STATE_MATRIX.json={sm.count(pat)}")
print("B2B_DESIGN.md 含「跑后任意」的行:", [i + 1 for i, l in enumerate(b2b_lines) if "跑后任意" in l])
print()

# STATE_MATRIX 每行键集合（验证无 is_new 键）
rows = json.loads(sm)
print(f"STATE_MATRIX.json 项数 = {len(rows)}")
for idx, r in enumerate(rows):
    print(f"  行:{idx+2} state={r['state']!r} keys={sorted(r.keys())}")
