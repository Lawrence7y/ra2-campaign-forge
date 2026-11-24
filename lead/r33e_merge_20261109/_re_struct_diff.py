# -*- coding: utf-8 -*-
"""_re_struct_diff.py — 并入版结构核验：difflib 比对只读原件与并入版，断言全部差异
hunk 落在白名单（模块 docstring、link() docstring、link_triple() docstring、
DECL_RE 插入、J4 块插入、tier 三元、merged elif 插入、usage 行）。
输出落本写域 _re_struct_diff_out.json。只读 + 本写域一件输出；-B 防 __pycache__。"""
import difflib
import hashlib
import json
from pathlib import Path

SL_PY = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109\_sl_link.py")
RE_PY = Path(r"D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_linked.py")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_struct_diff_out.json")

b_sl = SL_PY.read_bytes()
b_re = RE_PY.read_bytes()
guard = {
    "sl_link": {"sha256": hashlib.sha256(b_sl).hexdigest(), "bytes": len(b_sl),
                "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
                "expect_bytes": 12475},
    "re_linked": {"sha256": hashlib.sha256(b_re).hexdigest(), "bytes": len(b_re)},
}
assert guard["sl_link"]["sha256"] == guard["sl_link"]["expect_sha"], "GUARD FAIL: original drifted"
assert guard["sl_link"]["bytes"] == guard["sl_link"]["expect_bytes"], "GUARD FAIL: original drifted"

orig_lines = b_sl.decode("utf-8").splitlines()
new_lines = b_re.decode("utf-8").splitlines()
sm = difflib.SequenceMatcher(None, orig_lines, new_lines, autojunk=False)
ops = sm.get_opcodes()
# 白名单（1-based 原件行号）：
#   replace 允许跨 (2,24)=模块 docstring；(139,141)=link() docstring；
#           (225,226)=link_triple() docstring；229=tier 三元；243=usage 行
#   insert  允许锚 48=DECL_RE 之后；210=multi 分支 warning 之后（J4 块）；236=unique rec 块之后
ALLOWED_REPLACE_SPANS = [(2, 24), (139, 141), (225, 226), (229, 229), (243, 243)]
ALLOWED_INSERT_AFTER = [48, 210, 236]
diff_hunks, struct_ok = [], True
for tag, i1, i2, j1, j2 in ops:
    if tag == "equal":
        continue
    if tag == "insert":
        ok = i1 in ALLOWED_INSERT_AFTER
        where = "after line %d" % i1
    else:
        span = (i1 + 1, i2)
        ok = any(span[0] >= a and span[1] <= b for a, b in ALLOWED_REPLACE_SPANS)
        where = "lines %d-%d" % span
    diff_hunks.append({"op": tag, "orig": where, "new": "new lines %d-%d" % (j1 + 1, j2)})
    struct_ok = struct_ok and ok
unified = "".join(difflib.unified_diff(
    [ln + "\n" for ln in orig_lines], [ln + "\n" for ln in new_lines],
    fromfile="_sl_link.py", tofile="_re_linked.py", n=1))

out = {"guard": guard, "struct_ok": struct_ok, "hunks": diff_hunks, "unified_diff": unified}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("STRUCT_OK:", struct_ok)
print("HUNKS:", json.dumps(diff_hunks, ensure_ascii=False))
print("GUARD:", guard["sl_link"]["sha256"][:12], "/", guard["sl_link"]["bytes"],
      "| RE:", guard["re_linked"]["sha256"][:12], "/", guard["re_linked"]["bytes"])
print("OUT:", OUT)
