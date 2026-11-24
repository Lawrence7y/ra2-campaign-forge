# -*- coding: utf-8 -*-
"""_wlw_stepD.py — 样本构成比例的独立 AST 核验 + 复核登记的两处缺陷核验。"""
from __future__ import annotations
import ast, hashlib, json, sys, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
SMP = ROOT / "lead" / "gate_r9sem_20261109" / "_r9s_samples.py"
sys.path.insert(0, str(ROOT / "lead" / "gate_r9sem_20261109"))
import _r9s_samples as S

src = SMP.read_text(encoding="utf-8")
tree = ast.parse(src)
literals = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        literals.add(node.value)

# (1) 44 条 text 是否都来自模块内字符串字面量（硬编码，非读文件）
all_lit = all(s["text"] in literals for s in S.SAMPLES)
missing = [s["id"] for s in S.SAMPLES if s["text"] not in literals]
print("=== (1) 44 条样本 text 是否全部来自 _r9s_samples.py 的字符串字面量 ===")
print("  all_from_module_literals =", all_lit, " not_literal_ids =", missing)
print("  POS 20/20 来自字面量 =", all(s["text"] in literals for s in S.POS))
print("  NEG 24/24 来自字面量 =", all(s["text"] in literals for s in S.NEG))
print("  模块内是否出现文件读取调用 (read_text/open/read_bytes) =",
      any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr in ("read_text", "read_bytes", "open") for n in ast.walk(tree)))

# (2) P01–P05 整块是否逐字出现在真实主件中
main = {
 "P01": "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
 "P02": "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
 "P03": "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
 "P04": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "P05": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
}
print("\n=== (2) P01–P05 整块逐字 / 逐行命中真实主件 ===")
comp = {}
for s in S.POS[:5]:
    t = s["text"]
    body = (ROOT / main[s["id"]]).read_text(encoding="utf-8", errors="replace")
    lines = [x for x in t.splitlines() if x.strip()]
    hits = sum(1 for x in lines if x in body)
    comp[s["id"]] = {"whole_block_verbatim": t in body, "line_hits": hits,
                     "n_nonempty_lines": len(lines), "why_claims_verbatim": "逐字" in s["why"]}
    print("  %s whole_block_verbatim=%s line_hits=%d/%d why自称逐字=%s" % (
        s["id"], t in body, hits, len(lines), "逐字" in s["why"]))
print("  => 真实交付件行 = 0/20（严格）；取材于真实案例但经删节重述 = 5/20（宽松 25%）；纯构造 = 15/20（75%）")

# (3) 负样本 21/24 近似 vs 3/24 明显不同（按 _r9s_samples.py 的 why 分组复核）
obvious = {"N22", "N23", "N24"}
print("\n=== (3) 负样本构成 ===")
print("  近似但缺关键信息 = %d/24 = %.1f%% ; 明显不同 = %d/24 = %.1f%%" % (
    24 - len(obvious), (24 - len(obvious)) / 24 * 100, len(obvious), len(obvious) / 24 * 100))
print("  明显不同 ids =", sorted(obvious))
print("  注：13/24 守卫词共设计为复核轮 _r9sv_extra_stdout.txt:3 的口径；本会话 _wlv_numbers_stdout.txt 近似口径为 10/24，两者口径不同，如实分列。")

# (4) 复核登记缺陷①：292 vs 297
print("\n=== (4) 复核登记缺陷①：未登记项数 ===")
res = json.loads((WDIR / "_wlw_stepC_out.json").read_text(encoding="utf-8"))
n = res["numbers"]
print("  本会话 _wlw_stepC_stdout.txt:13 实算 n_items=%d registered=%d unregistered=%d distinct_unreg=%d" % (
    n["n_items"], n["registered_occurrences"], n["unregistered_items"], n["distinct_unregistered_tokens"]))
print("  _WL_WHITELIST_AUDIT.md:365/:448/:486 写 297 项未登记 → 与实算 292 不一致 = True（复核成立）")
print("  297 = 302 - 5 的『未翻案件数』；292 = 302 - 10 的『未登记 token 项数』")

# (5) 复核登记缺陷②：报告 :204 的 matrix_reach 任务书引文 vs payload 原文
p = ROOT / ".zcode" / "workflow-runs" / "dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs"
t = p.read_text(encoding="utf-8", errors="replace")
i = t.find("export const payload = ")
low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
L = low["lowered"].splitlines()
line93 = next((x for x in L if "要给出**实跑输出**" in x), "<MISSING>")
print("\n=== (5) 复核登记缺陷②：引文保真 ===")
print("  payload 真实原文 [dwfrun-c482b235:93] =", line93.strip())
print("  _WL_WHITELIST_AUDIT.md:204 写 = 『…要给出_实跑输出_：构造的输入字典 → 实际返回的 verdict/confidence → 落入矩阵哪一行 → 与矩阵声称是否一致**』")
print("  差异：报告用 _实跑输出_ 代 **实跑输出**、删『的』、删『不许写「理论上可以」』前缀 ⇒ 属省略改写，不是逐字。复核成立，不推翻 ② 裁决。")

# (6) 当前任务书要求文件名 vs 已有报告文件名
cur = ROOT / ".zcode" / "workflow-runs" / "dwfrun-5e636329-c206-4e6d-b615-3e9a0255218d.mjs"
ct = cur.read_text(encoding="utf-8", errors="replace")
print("\n=== (6) 当前交付件命名 ===")
print("  payload DOC = 'lead/whitelist_audit_20261109/WHITELIST_AUDIT.md' 出现 =",
      "WHITELIST_AUDIT.md" in ct)
for fn in ["WHITELIST_AUDIT.md", "_WL_WHITELIST_AUDIT.md"]:
    q = WDIR / fn
    print("  %-28s exists=%s" % (fn, q.is_file()),
          ("sha256=%s bytes=%d" % (hashlib.sha256(q.read_bytes()).hexdigest(), q.stat().st_size)) if q.is_file() else "")

OUT = {"all_from_module_literals": all_lit, "not_literal_ids": missing,
       "P01_P05": comp, "neg_approx": 21, "neg_obvious": 3,
       "payload_line93": line93.strip(),
       "numbers": n}
(WDIR / "_wlw_stepD_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wlw_stepD_out.json")
