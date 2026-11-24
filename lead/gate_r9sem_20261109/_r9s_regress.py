# -*- coding: utf-8 -*-
r"""_r9s_regress.py — R9S 回归运行器（只读现盘，写仅落本写域）。

三段实跑：
  (A) 正负样本集：24 条样本逐条跑 r9s_element_present，逐条打印 expect/actual/layer/why。
  (B) 4 个真实域：从 32 域基线取「缺要素 X」条目，逐条对比 R9 与 R9S 判定，
      列出升级后 gateProblems 中还剩几条。
  (C) 32 域全量「不放松」证明：对全部 32 域的**每一个必现要素 token**，
      与现盘主件文本，逐项比对 R9 与 R9S 的 (present, layer)。
      判据：不得出现 R9=False → R9S=True 的翻案，除非该翻案落在 5 处白名单
      （域 + token）内；白名单外一律 FAIL。另印全部翻案逐条定性。

零真机、零采样代码；Python 一律 python -I -X utf8 + 绝对路径。
"""

from __future__ import annotations

import ast
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(WDIR))
import _r9s_predicates as R9S  # noqa: E402
import _r9s_samples as S       # noqa: E402

BASE = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json")
                  .read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

OUT = {
    "r9_pred_sha256": R9S.R9_SHA256,
    "r9_pred_bytes": R9S.R9_BYTES,
    "r9_pred_recomputed": hashlib.sha256(R9S.R9_PATH.read_bytes()).hexdigest(),
    "baseline_sha256": hashlib.sha256(
        (ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_bytes()
    ).hexdigest(),
    "spec_inventory": R9S.spec_inventory(),
}

# ---------------------------------------------------------------------------
# (A) 正负样本集
# ---------------------------------------------------------------------------
print("=== (A) 正负样本集（POS=%d NEG=%d） ===" % (len(S.POS), len(S.NEG)))
sample_rows = []
for s in S.SAMPLES:
    ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
    hit = (ok == s["expect"])
    sample_rows.append({"id": s["id"], "token": s["token"], "expect": s["expect"],
                        "present": ok, "layer": layer, "pass": hit, "why": s["why"]})
    print("  %-4s %-6s expect=%-5s actual=%-5s layer=%-10s %s  [%s]"
          % (s["id"], s["token"], s["expect"], ok, layer or "(none)",
             "PASS" if hit else "**FAIL**", s["why"][:52]))
pos_n = sum(1 for x in sample_rows if x["expect"])
neg_n = sum(1 for x in sample_rows if not x["expect"])
pos_pass = sum(1 for x in sample_rows if x["expect"] and x["pass"])
neg_pass = sum(1 for x in sample_rows if not x["expect"] and x["pass"])
OUT["samples"] = {"rows": sample_rows, "positive": pos_n, "negative": neg_n,
                  "positive_pass": pos_pass, "negative_pass": neg_pass,
                  "all_pass": pos_pass == pos_n and neg_pass == neg_n}
print("  → POS %d/%d  NEG %d/%d  all_pass=%s"
      % (pos_pass, pos_n, neg_pass, neg_n, OUT["samples"]["all_pass"]))

# ---------------------------------------------------------------------------
# 从各域 GATE_CODE 提取必现要素 token（与 _rj_final_checks.py:40,74-78 同法）
# ---------------------------------------------------------------------------
LOOP_RE = re.compile(
    r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)"
)


def gate_src(low: str) -> str:
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    if k < 0 or end < 0:
        return ""
    body = low[k + len("const GATE_CODE = ["):end]
    parts = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else ""


def elements_of(r) -> list[str]:
    p = RUNS.get(r["run"])
    elems = []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        if i >= 0:
            low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
            src = gate_src(low.get("lowered", ""))
            for m in LOOP_RE.finditer(src):
                try:
                    elems += ast.literal_eval(m.group(2))
                except Exception:
                    pass
    return [x for x in elems if x]


# 白名单：本次任务书指名要求改判的 5 处（域 + token）。
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
FOUR = {d for d, _ in WHITELIST}

# ---------------------------------------------------------------------------
# (B) 4 个真实域：升级后 gateProblems 还剩几条
# ---------------------------------------------------------------------------
print("\n=== (B) 4 个真实域：升级后 gateProblems ===")
four_rows = []
for r in ROWS:
    if r["domain"] not in FOUR:
        continue
    mp = ROOT / r["domain"].rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace")
    elems = elements_of(r)
    probs_r9, _ = R9S.R9.r9_check(text, elems)
    probs_r9s, warns_r9s = R9S.r9s_check(text, elems)
    # 只对「缺要素」类问题做本次升级的消解统计；断言词/绑定行问题不属本层职责
    missing_r9 = [p for p in probs_r9 if p.startswith("缺要素")]
    missing_r9s = [p for p in probs_r9s if p.startswith("缺要素")]
    other = [p for p in r["gateProblems"] if not p.startswith("缺要素")]
    remaining = missing_r9s + other
    rec = {"domain": r["domain"], "main": r["main"],
           "mainSha256": hashlib.sha256(mp.read_bytes()).hexdigest(),
           "mainBytes": mp.stat().st_size,
           "elements": elems, "baseline_gateProblems": r["gateProblems"],
           "r9_missing": missing_r9, "r9s_missing": missing_r9s,
           "r9s_warnings": warns_r9s,
           "non_element_baseline_problems": other,
           "remaining_gateProblems_after_r9s": remaining,
           "n_remaining": len(remaining)}
    four_rows.append(rec)
    print("  %-46s elems=%s" % (r["domain"], json.dumps(elems, ensure_ascii=False)))
    print("     R9  缺要素=%s" % json.dumps(missing_r9, ensure_ascii=False))
    print("     R9S 缺要素=%s" % json.dumps(missing_r9s, ensure_ascii=False))
    print("     R9S warnings=%s" % json.dumps(warns_r9s, ensure_ascii=False))
    print("     升级后 gateProblems 剩 %d 条 = %s"
          % (len(remaining), json.dumps(remaining, ensure_ascii=False)))
OUT["four_domains"] = four_rows
OUT["four_domains_total_remaining"] = sum(x["n_remaining"] for x in four_rows)

# ---------------------------------------------------------------------------
# (C) 32 域全量不放松
# ---------------------------------------------------------------------------
print("\n=== (C) 32 域全量：R9 → R9S 逐要素翻案检查 ===")
all_rows = []
flips = []          # R9 False → R9S True（放松方向）
tightens = []       # R9 True → R9S False（收紧方向，承诺守卫）
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    if not mp.is_file():
        all_rows.append({"domain": dom, "main_missing": True,
                         "note": "主件不在盘，未跑（如实登记）"})
        print("  %-46s MAIN MISSING —— 未跑" % dom)
        continue
    text = mp.read_text(encoding="utf-8", errors="replace")
    elems = elements_of(r)
    per = []
    for k in elems:
        ok0, lay0 = R9S.R9.r9_element_present(text, k)
        ok1, lay1, _d = R9S.r9s_element_present(text, k)
        per.append({"token": k, "r9_present": ok0, "r9_layer": lay0,
                    "r9s_present": ok1, "r9s_layer": lay1})
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k,
                          "whitelisted": (dom, k) in WHITELIST,
                          "main": r["main"]})
        if ok0 and (not ok1):
            tightens.append({"domain": dom, "token": k, "main": r["main"],
                             "r9_layer": lay0})
    all_rows.append({"domain": dom, "main": r["main"], "elements": elems,
                     "baseline_gateProblems": r["gateProblems"], "per_element": per})
    changed = [x for x in per if x["r9_present"] != x["r9s_present"]
               or x["r9_layer"] != x["r9s_layer"]]
    print("  %-46s elems=%d changed=%s"
          % (dom, len(elems), json.dumps(
              [{"t": x["token"], "r9": x["r9_present"], "l0": x["r9_layer"],
                "r9s": x["r9s_present"], "l1": x["r9s_layer"]} for x in changed],
              ensure_ascii=False)))

OUT["domains32"] = {"n_domains": len(ROWS), "rows": all_rows,
                    "flips": flips, "n_flips": len(flips),
                    "tightens": tightens, "n_tightens": len(tightens),
                    "flips_outside_whitelist": [f for f in flips if not f["whitelisted"]],
                    "whitelist": [list(x) for x in sorted(WHITELIST)]}
OUT["no_relaxation"] = (len([f for f in flips if not f["whitelisted"]]) == 0
                        and len(flips) == len(WHITELIST)
                        and all(f["whitelisted"] for f in flips))
print("\n  n_flips=%d  whitelist=%d  outside_whitelist=%d  n_tightens=%d  no_relaxation=%s"
      % (len(flips), len(WHITELIST),
         len([f for f in flips if not f["whitelisted"]]), len(tightens),
         OUT["no_relaxation"]))
for f in flips:
    print("     FLIP %-46s %-12s whitelisted=%s —— %s"
          % (f["domain"], f["token"], f["whitelisted"],
             "本任务指名的 5 处措辞变体（语义在场、字面缺）" if f["whitelisted"]
             else "★ 意外翻案，必须 FAIL"))
for t in tightens:
    print("     TIGHTEN %-46s %-12s r9_layer=%s —— 承诺守卫取消未交付的字面命中"
          % (t["domain"], t["token"], t["r9_layer"]))

# ---------------------------------------------------------------------------
# 结论汇总
# ---------------------------------------------------------------------------
OUT["verdict"] = ("PASS" if (OUT["samples"]["all_pass"]
                             and OUT["no_relaxation"]
                             and all(x["n_remaining"] == 0 or
                                     all(p in x["non_element_baseline_problems"]
                                         for p in x["remaining_gateProblems_after_r9s"])
                                     for x in four_rows))
                  else "FAIL")
print("\n=== VERDICT = %s ===" % OUT["verdict"])
print("  samples all_pass=%s  no_relaxation=%s  4域剩余缺要素=%d"
      % (OUT["samples"]["all_pass"], OUT["no_relaxation"],
         sum(len(x["r9s_missing"]) for x in four_rows)))

(WDIR / "_r9s_regress_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
sys.exit(0 if OUT["verdict"] == "PASS" else 1)
