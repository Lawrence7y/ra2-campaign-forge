# -*- coding: utf-8 -*-
"""_rjv_step4.py — 独立核验：片段 STRUCT 谓词实测、R11 回验、7 域谓词化模拟、只读边界。
不执行 _rj_findings.md 里的片段原文；按其逻辑独立复刻同名谓词做功能测试。
"""
import hashlib
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_rejudge32_20261109"
BASE = json.loads((ROOT / "lead" / "gate_doc_name_fix_20261109" / "_dn_regate_out.json").read_text(encoding="utf-8"))

G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
spec = importlib.util.spec_from_file_location("_rjv_g7c", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

out = {}

# ---------- (A) 片段 STRUCT 谓词：逐字照抄 _rj_findings.md:128 的正则，独立测 ----------
STRUCT = re.compile(r'^\s*(#{1,6}\s|\||\d+[\.、]\s)|<[^>\n]{1,40}>|是否已填|→|\b或\b')

def _line_of(t, pos):
    s = t.rfind('\n', 0, pos) + 1
    e = t.find('\n', pos); e = len(t) if e < 0 else e
    return t[s:e]

frag_test = {}
for dom in ["lead/c07_slot_20261109/", "lead/c07_truth_protocol_20261109/",
            "lead/s604_script_hunt_20261109/"]:
    row = next(r for r in BASE["rows"] if r["domain"] == dom)
    p = ROOT / dom.rstrip("/") / row["main"]
    t = p.read_text(encoding="utf-8", errors="replace")
    BAD = row["params"]["banned"]
    p10, w10, h10 = g7.r10_scan(t, BAD)
    kept, suppressed = [], []
    for h in h10:
        line = _line_of(t, h["pos"])
        rec = {"token": h["token"], "pos": h["pos"], "kind": h["kind"],
               "line": t.count("\n", 0, h["pos"]) + 1, "line_text": line[:180],
               "STRUCT_match": bool(STRUCT.search(line))}
        if h["kind"] == "assertion" and not STRUCT.search(line):
            kept.append(rec)
        else:
            suppressed.append(rec)
    frag_test[dom] = {"BAD": BAD, "r10_assertions": sum(1 for h in h10 if h["kind"] == "assertion"),
                      "kept_by_fragment": kept, "suppressed": suppressed}
out["fragment_functional"] = frag_test

# ---------- (B) 片段 STRUCT 的假阴面：真断言落在表格/编号行会不会被一并豁免 ----------
fake_lines = [
    "| 1 | **已改台账**（2026-11-09 完成） | 主件 X |",
    "1. 已改门禁，缺口已修补完毕。",
    "### 5.4 已填身份值（reviewerSessionId = real-value）",
    "| 状态 | 已生效 |",
    "- 处置：已填 → 见证同为声明",
]
out["fragment_false_negative_probe"] = [
    {"line": ln, "STRUCT_match": bool(STRUCT.search(ln)),
     "would_be_suppressed_even_if_true_assertion": bool(STRUCT.search(ln))}
    for ln in fake_lines]
# \b或\b 在 CJK 里是否真能命中
cjk = "通过档 或 存疑档，二者择一"
out["b_or_b_cjk_test"] = {"text": cjk, "match": bool(re.search(r"\b或\b", cjk)),
                          "note": "Python3 \\b 是 \\w/\\W 边界；CJK 属 \\w，故「或」夹在汉字间不命中"}

# ---------- (C) R11 独立回验：3 个「真问题（格式类）」域 ----------
r11 = {}
for dom in ["lead/ledger_appendix_20261108/", "lead/n4_yi_final_20261108/",
            "lead/s604_attribution_20261108/"]:
    row = next(r for r in BASE["rows"] if r["domain"] == dom)
    p = ROOT / dom.rstrip("/") / row["main"]
    t = p.read_text(encoding="utf-8", errors="replace")
    probs, warns, binds = g7.r11_scan(t, p.parent, root=ROOT)
    r11[dom] = {"strict_adjacent": len(re.findall(r"被核对象 SHA256\s*=\s*`?[0-9a-fA-F]{64}`?", t)),
                "r11_problems": probs, "r11_bindings": len(binds),
                "matches": [{"declared": b["declared"][:12], "path": b.get("path"),
                             "match": b.get("match"), "bytes": b.get("bytes")}
                            for b in binds]}
out["r11_true_problem_domains"] = r11

# ---------- (D) 独立全量谓词化模拟：13 域，R9 要素 + R10/R12 断言 + R11 绑定 + 小节 ----------
sim = []
for row in BASE["rows"]:
    if not row.get("gateProblems"):
        continue
    dom = row["domain"]
    p = ROOT / dom.rstrip("/") / row["main"]
    t = p.read_text(encoding="utf-8", errors="replace")
    params = row.get("params", {})
    problems = []
    # 缺小节（params 里没有 sections 原文；改用 gateProblems 里的「缺小节」项判断是否有此检查）
    for prob in row["gateProblems"]:
        if prob.startswith("缺小节 "):
            if prob[len("缺小节 "):] not in t:
                problems.append(prob)
        elif prob.startswith("缺要素 "):
            tok = prob[len("缺要素 "):]
            ok, _ = g7.r9_element_present(t, tok)
            if not ok:
                problems.append(prob + " (R9 双缺)")
    banned = params.get("banned", [])
    if banned:
        p10, _, _ = g7.r10_scan(t, banned)
        p12, _ = g7.r12_scan(t, banned)
        problems += ["R10:" + x for x in p10] + ["R12:" + x for x in p12]
    p11, w11, b11 = g7.r11_scan(t, p.parent, root=ROOT)
    # r11 的 warnings（缺显式路径）不算 fail
    problems += ["R11:" + x for x in p11]
    sim.append({"domain": dom, "predicatized_problems": problems,
                "fail": bool(problems)})
out["predicatized_sim"] = {"domains_checked": len(sim),
                           "fail_count": sum(1 for s in sim if s["fail"]),
                           "fail_domains": [s["domain"] for s in sim if s["fail"]],
                           "rows": sim}

# ---------- (E) 只读边界：32 主件现值 vs 基线 + git 状态 ----------
drift = []
for row in BASE["rows"]:
    p = ROOT / row["domain"].rstrip("/") / row["main"]
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != row.get("mainSha256") or len(b) != row.get("mainBytes"):
        drift.append(row["domain"])
out["no_modification"] = {"main_drift": drift, "main_count": len(BASE["rows"]),
                          "banned_words_still_present": {
                              "lead/c07_slot_20261109/": ROOT.joinpath("lead/c07_slot_20261109/C07_IDENTITY_SLOT.md").read_text(encoding="utf-8", errors="replace").count("已填"),
                              "lead/s604_script_hunt_20261109/": ROOT.joinpath("lead/s604_script_hunt_20261109/S604_SCRIPT_HUNT.md").read_text(encoding="utf-8", errors="replace").count("已删除"),
                          }}

(WD / "_rjv_step4_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({
    "fragment_functional": {k: {"BAD": v["BAD"], "r10_assertions": v["r10_assertions"],
                                "kept_count": len(v["kept_by_fragment"]),
                                "suppressed_count": len(v["suppressed"]),
                                "suppressed_lines": [(s["line"], s["token"], s["kind"], s["STRUCT_match"], s["line_text"][:90]) for s in v["suppressed"]],
                                "kept_lines": [(s["line"], s["line_text"][:90]) for s in v["kept_by_fragment"]]}
                            for k, v in out["fragment_functional"].items()},
    "fragment_false_negative_probe": out["fragment_false_negative_probe"],
    "b_or_b_cjk_test": out["b_or_b_cjk_test"],
    "r11_true_problem_domains": out["r11_true_problem_domains"],
    "predicatized_sim": {k: v for k, v in out["predicatized_sim"].items() if k != "rows"},
    "predicatized_sim_rows": [{"domain": s["domain"], "n": len(s["predicatized_problems"]),
                               "problems": s["predicatized_problems"][:6]} for s in out["predicatized_sim"]["rows"] if s["fail"]],
    "no_modification": out["no_modification"],
}, ensure_ascii=False, indent=1))
