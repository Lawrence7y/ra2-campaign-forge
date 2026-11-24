# -*- coding: utf-8 -*-
r"""_r9s_minpatch.py — 最小改动方案实证（把 R9S 接进 check_deliverable）。

做法：读**只读**的 _g9_gate.py 源文本，做 3 处字符串替换，把结果写到本写域
_r9s_g9_candidate.py；再 importlib 加载候选模块，跑 self_test 与 4 个真实域。
绝不修改 _g9_gate.py / _g7_predicates.py 原件。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
sys.path.insert(0, str(WDIR))

src = G9.read_text(encoding="utf-8")
assert hashlib.sha256(G9.read_bytes()).hexdigest() == \
    "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6"

# --- 替换 1/3：import sys + 引入新层（在 r9_check 调用处） ---
old1 = "    r9_problems, r9_warnings = g7.r9_check(text, req)"
new1 = (
    "    import _r9s_predicates as r9s   # 新增层：R9 保持只读不改\n"
    "    r9_problems, r9_warnings = r9s.r9s_check(text, req)"
)
assert src.count(old1) == 1
src = src.replace(old1, new1)

# --- 替换 2/3：逐要素统计改走新层（第三个返回值是审计 detail，弃用） ---
old2 = "        ok, layer = g7.r9_element_present(text, k)"
new2 = "        ok, layer, _ = r9s.r9s_element_present(text, k)"
assert src.count(old2) == 1
src = src.replace(old2, new2)

# --- 替换 3/3：R9 展示名标注语义层（可选，纯展示） ---
old3 = '"name": "包裹归一化要素匹配（第 5 类）",'
new3 = '"name": "包裹归一化 + 语义要素匹配（R9 + R9S）",'
assert src.count(old3) == 1
src = src.replace(old3, new3)

cand = WDIR / "_r9s_g9_candidate.py"
cand.write_text(src, encoding="utf-8", newline="\n")
print("candidate =", cand, "bytes =", cand.stat().st_size,
      "sha256 =", hashlib.sha256(cand.read_bytes()).hexdigest())

spec = importlib.util.spec_from_file_location("_r9s_g9_candidate", cand)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("\n=== (i) self_test of patched check_deliverable ===")
checks, ok = m.self_test()
print(json.dumps({"checks": checks, "all_pass": ok}, ensure_ascii=False, indent=1))
print("self_test_all_pass =", ok)

print("\n=== (ii) 4 真实域经 patched check_deliverable（只看 R9 谓词） ===")
BASE = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json")
                  .read_text(encoding="utf-8"))
FOUR = ("lead/matrix_ab_ruling_20261109/", "lead/matrix_reach_20261109/",
        "lead/n11_wording_fix_20261108/", "lead/s604_script_gap_20261109/")
# 各域自己的必现要素清单（取自 _r9s_regress_out.json 的 (B) 段实跑结果）
import json as _json
_reg = _json.loads((WDIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
ELEMS_BY_DOMAIN = {x["domain"]: x["elements"] for x in _reg["four_domains"]}
ELEMS = ["需谁批准", "实跑输出", "改前改后", "脚本存在性", "可重建"]  # 仅用于 (iii) 对照
out = []
for r in BASE["rows"]:
    if r["domain"] not in FOUR:
        continue
    p = ROOT / r["domain"].rstrip("/") / r["main"]
    elems = ELEMS_BY_DOMAIN[r["domain"]]
    res = m.check_deliverable(p, elems, [], old_gate_contrast=False)
    rec = {"domain": r["domain"], "elements": elems,
           "R9_verdict": res["predicates"]["R9"]["verdict"],
           "R9_problems": res["predicates"]["R9"]["problems"],
           "R9_warnings": res["predicates"]["R9"]["warnings"],
           "present": res["predicates"]["R9"]["present"],
           "raw_hits": res["predicates"]["R9"]["raw_hits"],
           "normalized_only_hits": res["predicates"]["R9"]["normalized_only_hits"]}
    out.append(rec)
    print("  %-46s verdict=%-5s problems=%s" %
          (r["domain"], rec["R9_verdict"], json.dumps(rec["R9_problems"], ensure_ascii=False)))
    print("     warnings=%s" % json.dumps(rec["R9_warnings"], ensure_ascii=False))

print("\n=== (iii) 未登记 token 的 check_deliverable 对照（R9S ≡ R9） ===")
probe = ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md"
r_old_spec = importlib.util.spec_from_file_location("_r9s_g9_orig", G9)
old = importlib.util.module_from_spec(r_old_spec)
r_old_spec.loader.exec_module(old)
for toks in (["「被核对象」"], ["APPROVE_SCOPE"], ["被核对象", "已生效"]):
    a = old.check_deliverable(probe, toks, [], old_gate_contrast=False)
    b = m.check_deliverable(probe, toks, [], old_gate_contrast=False)
    # 语义等价判据：verdict + present/raw_hits + problems 的**条数与所指 token**相同。
    # 「缺要素 X」的诊断措辞由 R9 改成了 R9S，但所指要素与 FAIL 结论不变。
    def miss_tokens(rec):
        return [x.split("缺要素 ", 1)[1].split("（", 1)[0]
                for x in rec["predicates"]["R9"]["problems"] if x.startswith("缺要素")]
    same = (a["predicates"]["R9"]["verdict"] == b["predicates"]["R9"]["verdict"]
            and a["predicates"]["R9"]["present"] == b["predicates"]["R9"]["present"]
            and a["predicates"]["R9"]["raw_hits"] == b["predicates"]["R9"]["raw_hits"]
            and miss_tokens(a) == miss_tokens(b)
            and a["verdict"] == b["verdict"])
    print("  toks=%-28s old=%-5s new=%-5s missing=%s identical=%s"
          % (json.dumps(toks, ensure_ascii=False),
             a["predicates"]["R9"]["verdict"], b["predicates"]["R9"]["verdict"],
             json.dumps(miss_tokens(b), ensure_ascii=False), same))

(WDIR / "_r9s_minpatch_out.json").write_text(
    json.dumps({"candidate_bytes": cand.stat().st_size,
                "candidate_sha256": hashlib.sha256(cand.read_bytes()).hexdigest(),
                "self_test": {"checks": checks, "all_pass": ok},
                "four_domains": out}, ensure_ascii=False, indent=1),
    encoding="utf-8", newline="\n")
print("\nwrote _r9s_minpatch_out.json")
