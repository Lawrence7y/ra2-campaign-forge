# -*- coding: utf-8 -*-
# _g9v_empty.py — 复核 ④：空清单用例是否 FAIL（0 项不得 PASS）；附非空对照。
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _g9_gate import check_deliverable, REPO_ROOT  # noqa: E402

probes = [
    "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",          # 撰写人 self_test 用的探针件
    "lead/gate_r9r12_20261109/_g9_regression.md",          # 换一件（报告本体）交叉验证
]

out = []
for rel in probes:
    r = check_deliverable(REPO_ROOT / rel, [], [])
    kongs = [x["msg"] for x in r["problems"] if "空跑" in x["msg"]]
    pv = {k: r["predicates"][k]["verdict"] for k in ("R9", "R10", "R12", "R11")}
    out.append({"probe": rel, "verdict": r["verdict"], "pv": pv,
                "n_problems": len(r["problems"]), "kongpao": kongs})
    print(json.dumps(out[-1], ensure_ascii=False, indent=1))

# 非空对照：单要素在场（应 R9 PASS，总体 FAIL 仅因 R11 绑定行——即 FAIL_EMPTY 只针对 0 项）
r = check_deliverable(REPO_ROOT / probes[0], ["被核对象"], [])
print("CONTROL single-element: R9=%s overall=%s nprob=%d"
      % (r["predicates"]["R9"]["verdict"], r["verdict"], len(r["problems"])))
out.append({"control": probes[0], "R9": r["predicates"]["R9"]["verdict"],
            "overall": r["verdict"], "n_problems": len(r["problems"])})

ok = all(x["verdict"] == "FAIL" and len(x.get("kongpao", [])) == 3 for x in out if "probe" in x)
print("EMPTY_CHECKLIST_VERDICT:", "FAIL_AS_EXPECTED" if ok else "NOT_AS_EXPECTED")
(HERE / "_g9v_empty_out.json").write_text(
    json.dumps({"cases": out, "empty_fails": ok}, ensure_ascii=False, indent=1), encoding="utf-8")
