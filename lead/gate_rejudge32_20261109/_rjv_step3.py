# -*- coding: utf-8 -*-
"""_rjv_step3.py — 独立核验：任务书原句、提取器假象、判不了项、片段静态可执行性、只读边界。
不采信 _rj_* 结论。全部写 _rjv_*，只读其它。片段只做 ast 解析/静态符号分析，不 exec。
"""
import ast
import hashlib
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_rejudge32_20261109"
WFR = ROOT / ".zcode" / "workflow-runs"
BASE = json.loads((ROOT / "lead" / "gate_doc_name_fix_20261109" / "_dn_regate_out.json").read_text(encoding="utf-8"))
out = {}

# ---------- (A) 任务书原句：从历史 payload 的 lowered 段逐字找，不采信转述 ----------
TASK_TOKENS = ["是否已填", "多处同步排查表", "已删除", "必现要素", "实跑输出", "改前改后",
               "脚本存在性", "可重建", "需谁批准", "不签 APPROVE_SCOPE", "绑定行", "被核对象 SHA256"]
DOMAINS_OF_INTEREST = [
    "c07_slot_20261109", "c07_truth_protocol_20261109", "s604_script_hunt_20261109",
    "matrix_ab_ruling_20261109", "matrix_reach_20261109", "n11_wording_fix_20261108",
    "s604_script_gap_20261109", "ledger_appendix_20261108", "n4_yi_final_20261108",
    "s604_attribution_20261108", "c07_protocol_attacks_20261109", "c07_gate_audit_20261109",
    "n10c04_ruling_20261108",
]
mjs_sorted = sorted([p for p in WFR.iterdir() if p.is_file() and p.suffix == ".mjs"])
tasks = {}
for dom in DOMAINS_OF_INTEREST:
    hits = []
    for p in mjs_sorted:
        text = p.read_text(encoding="utf-8", errors="replace")
        if dom not in text or ("ASK_" not in text and "唯一写域" not in text):
            continue
        for tok in TASK_TOKENS:
            for m in re.finditer(re.escape(tok), text):
                s = max(0, m.start() - 200)
                e = min(len(text), m.end() + 200)
                snippet = text[s:e].replace("\\n", " ").replace('\\"', '"')
                hits.append({"run": p.name, "token": tok, "snippet": snippet})
    tasks[dom] = hits[:40]
out["taskbook_hits"] = tasks

# ---------- (B) 提取器假象：独立复算 bindings=0 的 6 域真实绑定行 ----------
ZERO = [r for r in BASE["rows"] if r.get("bindings") == 0]
extract = {}
for row in ZERO:
    dom = row["domain"]
    run_name = row.get("run")
    p = WFR / run_name
    low = ""
    if p.is_file():
        txt = p.read_text(encoding="utf-8", errors="replace")
        i = txt.find("export const payload = ")
        if i >= 0:
            try:
                val, _ = json.JSONDecoder().raw_decode(txt[i + len("export const payload = "):])
                low = val.get("lowered") or ""
            except Exception:
                pass
    all_findall = re.findall(r"re\.findall\(r'([^']+)'", low)
    all_findall_double = re.findall(r're\.findall\(r"([^"]+)"', low)
    mp = ROOT / dom.rstrip("/") / row["main"]
    t = mp.read_text(encoding="utf-8", errors="replace")
    per = []
    for rgx in all_findall + all_findall_double:
        try:
            n = len(re.findall(rgx, t))
        except re.error:
            n = -1
        per.append({"regex": rgx, "count": n})
    strict = re.findall(r"被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?", t)
    backticks = re.findall(r"SHA256\s*=\s*`([0-9a-fA-F]{64})`", t)
    hex_all = re.findall(r"SHA256\s*=\s*`?([0-9a-fA-F]{64})`?", t)
    extract[dom] = {"run": run_name, "baseline_bindings": row.get("bindings"),
                    "all_findall_regexes": per,
                    "strict_adjacent_binding_count": len(strict),
                    "any_SHA256_backtick_hex_count": len(backticks),
                    "any_SHA256_hex_count": len(hex_all),
                    "sha_lines": [{"line": i, "text": ln} for i, ln in enumerate(t.split("\n"), 1) if "SHA256" in ln][:20]}
out["extractor"] = extract

# ---------- (C) R9 / R11 独立复核：「真问题」是否换判据即可消解 ----------
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
gb = G7.read_bytes()
spec = importlib.util.spec_from_file_location("_rjv_g7b", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

R9_TOKENS = {
    "lead/c07_gate_audit_20261109/": ["未改 _c7_selfcheck.py"],
    "lead/n4_yi_final_20261108/": ["不签 APPROVE_SCOPE"],
    "lead/matrix_ab_ruling_20261109/": ["需谁批准"],
    "lead/matrix_reach_20261109/": ["实跑输出"],
    "lead/n11_wording_fix_20261108/": ["改前改后"],
    "lead/s604_script_gap_20261109/": ["脚本存在性", "可重建"],
}
r9r11 = {}
for dom, toks in R9_TOKENS.items():
    row = next(r for r in BASE["rows"] if r["domain"] == dom)
    mp = ROOT / dom.rstrip("/") / row["main"]
    t = mp.read_text(encoding="utf-8", errors="replace")
    rec = {"domain": dom, "tokens": {}}
    for tok in toks:
        ok, layer = g7.r9_element_present(t, tok)
        rec["tokens"][tok] = {"raw": tok in t, "r9_present": ok, "r9_layer": layer}
    probs, warns, binds = g7.r11_scan(t, mp.parent, root=ROOT)
    rec["r11"] = {"problems": probs, "warnings": warns,
                  "bindings": [{"declared": b["declared"][:12], "path": b.get("path"),
                                "match": b.get("match"), "bytes": b.get("bytes")} for b in binds]}
    r9r11[dom] = rec
out["r9_r11"] = r9r11

# ---------- (D) 判不了项：统计被核对象文本中的回避性表述与结论覆盖 ----------
fj = (WD / "_rj_findings.md").read_text(encoding="utf-8")
out["unjudgeable"] = {
    "literal_判不了_count": fj.count("判不了"),
    "literal_未验_count": fj.count("未验"),
    "literal_需要人工看_count": fj.count("需要人工看"),
    "verdict_true_rows": len(re.findall(r"\| \*\*真问题", fj)),
    "verdict_false_rows": len(re.findall(r"\| \*\*误报", fj)),
    "section2_table_rows": len(re.findall(r"^\| \d+ \|", fj, re.M)),
    "has_10domains_unverified": ("10 域集合对齐标「未验」" in fj or "10 域枚举未验" in fj),
}

# ---------- (E) 片段静态可执行性：ast 解析 + 自由变量分析（不执行片段） ----------
code = re.search(r"```python\n(.*?)\n```", fj, re.S)
frag = {}
if code:
    src = code.group(1)
    frag["snippet_chars"] = len(src)
    frag["ast_parse_ok"] = True
    tree = ast.parse(src)  # 语法不合即抛异常
    frag["ast_parse_ok"] = True
    defined = set()
    loaded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.id)
        elif isinstance(node, ast.alias):
            defined.add(node.asname or node.name.split(".")[0])
    imports = {"json", "pathlib", "re", "hashlib", "importlib", "_ilu"}
    frag["names_defined_in_snippet"] = sorted(defined)
    frag["free_names_required_from_gate"] = sorted(loaded - defined - imports - {"print", "len", "str", "int"})
    frag["has_missing_file_fail_branch"] = "DOC.is_file()" in src
    frag["fail_branch_is_comment_only"] = bool(re.search(r"^\s*#\s*if not DOC\.is_file\(\)", src, re.M))
    frag["has_r12"] = "r12_scan" in src
    frag["has_pred_fingerprint"] = "_PRED_SHA" in src and "hashlib.sha256" in src
    frag["uses_raise_SystemExit"] = "raise SystemExit" in src
    frag["defines_STRUCT_regex"] = "STRUCT = re.compile" in src
    frag["defines_line_of"] = "def _line_of" in src
    frag["assumes_names"] = sorted(n for n in loaded - defined - imports - {"print", "len", "str", "int"})
out["fragment"] = frag

# ---------- (F) 只读边界：32 主件 + 七件 + 全部 mjs 现值 ----------
seven_rel = [
    "lead/gate_doc_name_fix_20261109/_dn_regate_out.json",
    "lead/gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md",
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/gate_r9r12_20261109/_g9_gate.py",
    "lead/r33e_merge_20261109/_re_linked.py",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
main_drift = []
for row in BASE["rows"]:
    p = ROOT / row["domain"].rstrip("/") / row["main"]
    if not p.is_file():
        main_drift.append({"domain": row["domain"], "state": "MISSING"})
        continue
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != row.get("mainSha256") or len(b) != row.get("mainBytes"):
        main_drift.append({"domain": row["domain"], "state": "DRIFT"})
mjs = sorted([p for p in WFR.iterdir() if p.is_file() and p.suffix == ".mjs"])
out["boundary"] = {
    "main_count": len(BASE["rows"]), "main_drift": main_drift,
    "seven_current": [{"rel": r, "sha256": hashlib.sha256((ROOT / r).read_bytes()).hexdigest(),
                       "bytes": (ROOT / r).stat().st_size} for r in seven_rel],
    "mjs_count": len(mjs),
    "mjs_sha256_concat": hashlib.sha256(b"".join(p.read_bytes() for p in mjs)).hexdigest(),
    "rj_files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                  "bytes": p.stat().st_size} for p in sorted(WD.iterdir())
                 if p.is_file() and p.name.startswith("_rj_") and not p.name.startswith("_rjv_")],
    "rjv_files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                   "bytes": p.stat().st_size} for p in sorted(WD.iterdir())
                  if p.is_file() and p.name.startswith("_rjv_")],
}

(WD / "_rjv_step3_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({
    "extractor": {k: {kk: vv for kk, vv in v.items() if kk not in ("sha_lines", "all_findall_regexes")}
                  for k, v in out["extractor"].items()},
    "extractor_all_findall": {k: v["all_findall_regexes"] for k, v in out["extractor"].items()},
    "r9_r11": out["r9_r11"],
    "unjudgeable": out["unjudgeable"],
    "fragment": out["fragment"],
    "boundary": {k: v for k, v in out["boundary"].items() if k not in ("rj_files", "rjv_files", "seven_current")},
    "boundary_seven": out["boundary"]["seven_current"],
}, ensure_ascii=False, indent=1))
