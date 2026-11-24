# -*- coding: utf-8 -*-
"""_rjv_step2.py — 独立抽查：13 域主件逐字原句 + 上下文 + 命中定位 + 词仍在场校验。
不采信 _rj_* 结论，直接读现盘交付件。全部写 _rjv_*，只读其它。
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_rejudge32_20261109"
BASE = json.loads((ROOT / "lead" / "gate_doc_name_fix_20261109" / "_dn_regate_out.json").read_text(encoding="utf-8"))

# 抽查重点：命中词 → 期望行号（来自被核对象自述，仅作定位提示，不采信其判定）
FOCUS = {
    "lead/c07_gate_audit_20261109/": {"tokens": ["未改", "_c7_selfcheck.py", "SHA256"], "lines": [17, 239]},
    "lead/c07_protocol_attacks_20261109/": {"tokens": ["SHA256", "被核对象"], "lines": [8, 102]},
    "lead/c07_slot_20261109/": {"tokens": ["已填", "SHA256", "未填", "代填"], "lines": [79, 103, 110, 112, 116, 117, 118, 119, 120, 136, 137, 138, 139, 140]},
    "lead/c07_truth_protocol_20261109/": {"tokens": ["已填", "SHA256", "不含任何真实身份值"], "lines": [6, 151, 228, 240]},
    "lead/ledger_appendix_20261108/": {"tokens": ["已生效", "SHA256", "被核对象"], "lines": [146, 177, 186, 194]},
    "lead/matrix_ab_ruling_20261109/": {"tokens": ["已改矩阵", "已收紧", "已施行", "需谁批准", "批准人"], "lines": [4, 108, 138]},
    "lead/matrix_reach_20261109/": {"tokens": ["实跑输出", "实跑返回", "out:"], "lines": [26, 65, 74]},
    "lead/n10c04_ruling_20261108/": {"tokens": ["授实施权", "解除 PAUSE"], "lines": [5, 44, 348, 425]},
    "lead/n11_wording_fix_20261108/": {"tokens": ["改前改后", "改前", "改后"], "lines": [76, 81, 82]},
    "lead/n4_yi_final_20261108/": {"tokens": ["APPROVE_SCOPE", "可应用母本", "放行 N-5", "SHA256", "被核对象"], "lines": [15, 17, 122, 130, 150, 155]},
    "lead/s604_attribution_20261108/": {"tokens": ["SHA256", "被核对象", "字节数"], "lines": [160, 161]},
    "lead/s604_script_gap_20261109/": {"tokens": ["脚本存在性", "可重建", "存在性判定", "可唯一重建"], "lines": [10, 32, 69, 73, 87]},
    "lead/s604_script_hunt_20261109/": {"tokens": ["已删除"], "lines": [143]},
}

out = {}
for row in BASE["rows"]:
    dom = row["domain"]
    if dom not in FOCUS:
        continue
    p = ROOT / dom.rstrip("/") / row["main"]
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    f = FOCUS[dom]
    rec = {"domain": dom, "main": row["main"], "bytes": p.stat().st_size,
           "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "gateProblems": row.get("gateProblems", []), "bindings": row.get("bindings"),
           "banned": row.get("params", {}).get("banned", []),
           "token_counts": {}, "exact_lines": {}, "token_hit_lines": {},
           "all_banned_hits": {}}
    for tok in f["tokens"]:
        rec["token_counts"][tok] = text.count(tok)
        hits = []
        for i, ln in enumerate(lines, 1):
            for m in re.finditer(re.escape(tok), ln):
                hits.append({"line": i, "col": m.start() + 1,
                             "sentence": ln})
        rec["token_hit_lines"][tok] = hits
    # 期望行号处的逐字原句 + 前后各 2 行上下文
    for n in f["lines"]:
        ctx = []
        for i in range(max(1, n - 2), min(len(lines), n + 2) + 1):
            ctx.append({"line": i, "text": lines[i - 1]})
        rec["exact_lines"][str(n)] = ctx
    # 全量 banned 词命中（含行号、逐字原句）
    for bad in rec["banned"]:
        hs = []
        for i, ln in enumerate(lines, 1):
            for m in re.finditer(re.escape(bad), ln):
                hs.append({"line": i, "col": m.start() + 1, "sentence": ln})
        rec["all_banned_hits"][bad] = hs
    # 全文 SHA256 相关行（绑定行核验）
    rec["sha_lines"] = [{"line": i, "text": ln} for i, ln in enumerate(lines, 1)
                        if "SHA256" in ln or "字节数" in ln]
    out[dom] = rec

(WD / "_rjv_step2_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

# 打印摘要：token 计数 + 各域关键逐字行
for dom, rec in out.items():
    print("=" * 100)
    print(dom, rec["main"], "bytes=%d" % rec["bytes"], "sha=%s" % rec["sha256"][:12])
    print("  gateProblems:", rec["gateProblems"])
    print("  bindings:", rec["bindings"], " banned:", rec["banned"])
    print("  token_counts:", {k: v for k, v in rec["token_counts"].items()})
    for n in FOCUS[dom]["lines"]:
        ctx = rec["exact_lines"][str(n)]
        for c in ctx:
            mark = ">>" if c["line"] == n else "  "
            print("  %s L%d: %s" % (mark, c["line"], c["text"][:300]))
