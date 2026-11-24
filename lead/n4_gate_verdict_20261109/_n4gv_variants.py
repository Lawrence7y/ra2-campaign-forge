# -*- coding: utf-8 -*-
# N4 gate reviewer: independently verify claimed post-change SHA256 values
# (author's _n4g_VERDICT.md §6 table / _n4g_exact_out.json). NOT written to disk
# except this one output file; the deliverable itself is NEVER modified.
import json, hashlib, re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
DOC = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
OUT = ROOT / "lead/n4_gate_verdict_20261109/_n4gv_variants_out.json"

b = DOC.read_bytes()
t = b.decode("utf-8")
lines = t.split("\n")   # split-newline convention; last element is '' (file ends with newline?)
L122 = lines[121]
CANON = "被核对象 SHA256 = ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e，字节数 = 11948"

def mk(lines_):
    s = "\n".join(lines_)
    bb = s.encode("utf-8")
    return {"sha256": hashlib.sha256(bb).hexdigest(), "bytes": len(bb),
            "gate_strict": len(re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?', s)),
            "iron_tight": len(re.findall(r'被核对象 SHA256 = ([0-9a-fA-F]{64})，字节数 = (\d+)', s))}

variants = {}
variants["original"] = mk(lines)
# B: replace line 122 with canonical
v = list(lines); v[121] = CANON
variants["B_replace_122"] = mk(v)
# B-alt: insert canonical line AFTER 122
v = list(lines); v.insert(122, CANON)
variants["B_insert_after_122"] = mk(v)
# append canonical at file end (before trailing empty element)
v = list(lines)
if v and v[-1] == "":
    v.insert(len(v)-1, CANON)
else:
    v.append(CANON)
variants["append_at_end"] = mk(v)
# A+B: remove backticks in lines 15 and 150 around APPROVE_SCOPE, plus B replace
v = list(lines)
v[14] = v[14].replace("不签 `APPROVE_SCOPE`", "不签 APPROVE_SCOPE")
v[149] = v[149].replace("不签 `APPROVE_SCOPE`", "不签 APPROVE_SCOPE")
v[121] = CANON
variants["A_plus_B"] = mk(v)

# author's claimed hashes for comparison
claimed = {
 "original": "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b",
 "B_replace_122": "abf90ca74dc886ef315beeb9306019120b7884fe10b667723db77e67e17e47ec",
 "B_insert_after_122": "50925ee9d183213831d9fd26b7d07007a8f6d7ba65867e19805efcf6814f1dce",
 "append_at_end": "23c264830de6f5177d1ba732037941deec730bec9623c33479fffea237f3e675",
}
cmp = {k: {"mine": variants[k]["sha256"], "claimed": claimed.get(k),
           "match": variants[k]["sha256"] == claimed.get(k),
           "bytes": variants[k]["bytes"]} for k in claimed}

res = {"note": "in-memory variants only; deliverable untouched",
       "canonical_line": CANON, "variants": variants, "compare_to_author": cmp,
       "A_plus_B_sha256": variants["A_plus_B"]["sha256"],
       "A_plus_B_bytes": variants["A_plus_B"]["bytes"]}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=2))
