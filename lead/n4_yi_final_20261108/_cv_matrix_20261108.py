# -*- coding: utf-8 -*-
# _cv_matrix_20261108.py — 独立解析 STATE_MATRIX.json 全文行数 + 逐行对照 V2 §4.2 表（只读）
import json, re

BASE = "D:/Project/ra2-campaign-forge/"
MJ = BASE + "lead/b2b_design_20261106/STATE_MATRIX.json"
V2 = BASE + "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"

raw = open(MJ, "rb").read().decode("utf-8")
jlines = raw.split("\n")
data = json.loads(raw)
print("JSON top-level type:", type(data).__name__)
print("JSON row count (len):", len(data))
# 逐行验证：文件行 2..15 每行恰一个 JSON 对象
objline = 0
for i, L in enumerate(jlines, 1):
    s = L.strip()
    if s.startswith('{"state"'):
        objline += 1
        o = json.loads(s.rstrip(","))
        assert o["state"] == data[i - 2]["state"], ("line map mismatch", i)
print("lines 2..15 each-one-object:", objline)

rows = data
pairs = sorted({(r["verdict"], r["confidence"]) for r in rows})
print("distinct (verdict,confidence) pairs in matrix:", len(pairs))
for p in pairs:
    print("   ", p)
print("usableAsCrashEvidence all False:", all(r["usableAsCrashEvidence"] is False for r in rows),
      "values:", sorted({r["usableAsCrashEvidence"] for r in rows}))
print("confidence domain in matrix:", sorted({r["confidence"] for r in rows}))
print("verdict domain in matrix:", sorted({r["verdict"] for r in rows}))
na_in_matrix = [ (i, r["confidence"]) for i, r in enumerate(rows) if "n/a" in (r["confidence"] or "").lower() ]
print("matrix confidence n/a rows:", na_in_matrix)

v2text = open(V2, "rb").read().decode("utf-8")
vlines = v2text.split("\n")
rowpat = re.compile(r"^\|\s*:(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
v2rows = []
for i, L in enumerate(vlines, 1):
    m = rowpat.match(L)
    if m and 110 <= i <= 135:
        v2rows.append((i, int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)))
print("V2 §4.2 table rows found (line, 文件行, preState, verdict, confidence, usable):")
for r in v2rows:
    print("   ", r)
print("V2 row count:", len(v2rows))

mismatch = 0
for (ln, no, pre, verd, conf, usable) in v2rows:
    j = rows[no - 2]           # 文件行 n ↔ data[n-2]
    verd2 = verd.split("（")[0].strip().replace("*", "")   # 去括注＋V2 表内 markdown 加粗
    pre2 = pre.split("（")[0].strip().replace("*", "")
    conf2 = conf.split("（")[0].strip().replace("*", "")
    ok = (j["verdict"] == verd2 and j["confidence"] == conf2 and j["preState"] == pre2
          and j["usableAsCrashEvidence"] == (usable.strip().lower() == "true"))
    if not ok: mismatch += 1
    print("row 文件行:%d JSON(v=%s,c=%s,pre=%s,u=%s) V2(v=%s,c=%s,pre=%s,u=%s) -> %s" %
          (no, j["verdict"], j["confidence"], j["preState"], j["usableAsCrashEvidence"],
           verd2, conf2, pre2, usable, "OK" if ok else "MISMATCH"))
print("V2-vs-JSON mismatch rows:", mismatch)
print("counts: json=%d v2=%d" % (len(rows), len(v2rows)))
