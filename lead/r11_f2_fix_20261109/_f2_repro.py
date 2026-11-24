# -*- coding: utf-8 -*-
"""_f2_repro.py — F2 缺口复现（第一步）。

只读实跑：加载 lead/gate_fp7_20261108/_g7_predicates.py（加载前验指纹），
对 _g9_regression_out.json 里 results_30 的同一份 30 件清单重跑原版 r11_scan，
断言与本任务编排方给出的回归 JSON 中 binding_details 逐条一致，
然后 dump 每条绑定行的原文语境（前一行/本行/后一行 + 反引号跨度 + SHA 命中位置），
供 F2-a/F2-b/F2-c 形态人工核对与自动分类。

零真机、零采样；只读；输出落本写域 _f2_repro_out.json。
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G9OUT = REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json"
OUT = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_repro_out.json"

G7_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES = 11743

raw = G7.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == G7_SHA and len(raw) == G7_BYTES, "g7 指纹失配 %s/%d" % (sha, len(raw))
spec = importlib.util.spec_from_file_location("_g7_predicates_f2", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

reg = json.loads(G9OUT.read_text(encoding="utf-8"))
files = [r["file"] for r in reg["results_30"]]
assert len(files) == 30

BIND_RE = g7.BIND_RE
BIND_PATH_BACK = g7.BIND_PATH_BACK

rows = []
mismatch_json = []
for r in reg["results_30"]:
    p = Path(r["file"])
    text = p.read_bytes().decode("utf-8")
    d_dir = p.parent
    problems, warnings, bindings = g7.r11_scan(text, d_dir, root=REPO)
    orig_bd = r["predicates"]["R11"].get("binding_details", [])
    # 断言：本跑 binding_details 与回归 JSON 逐条一致（declared/path/match）
    mine = [(b["declared"], b["path"], b["match"]) for b in bindings]
    theirs = [(b["declared"], b["path"], b["match"]) for b in orig_bd]
    if mine != theirs:
        mismatch_json.append({"file": str(p), "mine": mine, "json": theirs})
    lines = text.split("\n")
    # 逐条绑定行定位原文语境
    for bi, m in enumerate(BIND_RE.finditer(text)):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        line_no = text.count("\n", 0, line_start) + 1
        cur = text[line_start:line_end]
        prev = lines[line_no - 2] if line_no >= 2 else ""
        nxt = lines[line_no] if line_no - 1 < len(lines) - 1 else ""
        sha_pos = m.start() - line_start  # hex 命中起点在本行内的列
        # 本行/前一行/后一行的全部反引号跨度（内容+列区间）
        def spans(line):
            out = []
            for sm in re.finditer(r"`([^`\n]{1,200})`", line):
                out.append({"content": sm.group(1), "col": [sm.start(1), sm.end(1)]})
            return out
        rec_bd = bindings[bi] if bi < len(bindings) else None
        rows.append({
            "file": str(p),
            "line_no": line_no,
            "declared": m.group(1),
            "orig_path": rec_bd["path"] if rec_bd else "!INDEX!",
            "orig_match": rec_bd["match"] if rec_bd else None,
            "sha_col": sha_pos,
            "cur_line": cur,
            "prev_line": prev,
            "next_line": nxt,
            "cur_spans": spans(cur),
            "prev_spans": spans(prev),
            "next_spans": spans(nxt),
            "r11_problems": list(problems),
            "r11_warnings": list(warnings),
        })

nulls = sum(1 for x in rows if x["orig_path"] is None)
print("复现：绑定行总数=%d，path=null=%d，path 非 null=%d" % (len(rows), nulls, len(rows) - nulls))
print("与回归 JSON binding_details 不一致的文件数=%d" % len(mismatch_json))
for x in mismatch_json:
    print("MISMATCH:", x["file"])
print()
for x in rows:
    print("=" * 100)
    print("%s  L%d  orig_path=%r orig_match=%r sha_col=%d" %
          (x["file"], x["line_no"], x["orig_path"], x["orig_match"], x["sha_col"]))
    print("  前一行: %s" % x["prev_line"][:160])
    print("  本行  : %s" % x["cur_line"][:200])
    print("  后一行: %s" % x["next_line"][:160])
    print("  本行反引号跨度: %s" % json.dumps(x["cur_spans"], ensure_ascii=False))
    print("  前行反引号跨度: %s" % json.dumps(x["prev_spans"], ensure_ascii=False))
    print("  后行反引号跨度: %s" % json.dumps(x["next_spans"], ensure_ascii=False))

OUT.write_text(json.dumps({
    "g7_sha": sha, "g7_bytes": len(raw),
    "total_bindings": len(rows), "null_path": nulls,
    "json_mismatch": mismatch_json,
    "rows": rows,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print()
print("已写 %s" % OUT)
