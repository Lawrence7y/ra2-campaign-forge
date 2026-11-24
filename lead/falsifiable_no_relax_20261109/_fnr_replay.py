# -*- coding: utf-8 -*-
r"""_fnr_replay.py -- ISOLATED in-memory replay of the R9S regression formula.

WHY: lead/gate_r9sem_20261109/_r9s_regress.py:235-236 writes into an ABSOLUTE
READ-ONLY directory, so it must NOT be executed here. This module re-implements
the *exact* formulas of :204-206 (no_relaxation) and :223-229 (VERDICT), plus
:52-68 (samples), :125-157 (four_domains), :162-206 (32-domain flips), with
identical element extraction (:75-109). No predicate, script or whitelist is
modified. Substitutions live only in memory.

Scenarios:
  k0        : no substitution (fidelity check vs recorded _r9s_regress_out.json)
  k1..k5    : k of the 5 whitelist items replaced by semantically-empty payloads
  fp_extra  : 6th SEMANTICALLY-CORRECT flip added (truth intact, gate says relax)
  fp_raw    : one whitelist item made literally present (truth improved, gate says relax)
  fp_dropwl : WHITELIST minus one pair (truth intact, gate says relax)

Run:
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_replay.py
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(R9S_DIR))
import _r9s_predicates as R9S  # noqa: E402
import _r9s_samples as S       # noqa: E402

BASE = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json")
                  .read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}
REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))

# ---- exact copy of _r9s_regress.py:75-109 ---------------------------------
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


def elements_of(r) -> list:
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


# ---- exact copy of _r9s_regress.py:113-120 ---------------------------------
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
FOUR = {d for d, _ in WHITELIST}

# ---- the 5 semantically-empty payloads, verbatim from
#      lead/whitelist_audit_20261109/_wl_selfproof.py:21-32 ------------------
EMPTY = {
 ("lead/matrix_ab_ruling_20261109/", "需谁批准"):
   "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n",
 ("lead/matrix_reach_20261109/", "实跑输出"):
   "## 3 五处缺陷逐处可达性实证\n### 3.1 W1\n- **构造输入 → 实跑返回**：classify 直调，16/16 格实跑：\n```\n  verdict='详见台账' conf='none'\n```\n- 落哪一行 / 与矩阵声称是否一致：16/16，out:159-174。\n",
 ("lead/n11_wording_fix_20261108/", "改前改后"):
   "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n",
 ("lead/s604_script_gap_20261109/", "脚本存在性"):
   "## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.5 存在性判定\n**结论：生成脚本【不存在且从未落盘】（以台账记载为准，本件不另下结论）。**\n",
 ("lead/s604_script_gap_20261109/", "可重建"):
   "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n",
}
EMPTY_ORDER = list(EMPTY.keys())

# semantically-correct equivalence form (R9 literal absent, R9S semantic hit)
TRUE_EQUIV = "## 5 附：批准人复核\n审批人 = 丙复核责任人。\n"
# a domain carrying a registered token but NOT in the whitelist
EXTRA_DOMAIN = "lead/handoff_pack_20261109/"
EXTRA_TOKEN = "需谁批准"
# literal insertion: makes the element literally present (truth strictly improved)
LITERAL_INSERT = "\n需谁批准：见本件第 5 节，批准人一律 = 乙设计责任人。\n"


def texts_for(dom: str, main: str):
    return (ROOT / dom.rstrip("/") / main).read_text(encoding="utf-8", errors="replace")


def run(name: str, subs: dict, extra_flip: bool = False,
        literal_insert: bool = False, whitelist=None, note: str = ""):
    """One full replay. subs maps (domain, token) -> replacement text."""
    WL = WHITELIST if whitelist is None else whitelist
    FOURx = {d for d, _ in WL}

    def pick(dom, tok, real):
        if (dom, tok) in subs:
            return subs[(dom, tok)]
        if literal_insert and (dom, tok) == ("lead/matrix_ab_ruling_20261109/", "需谁批准"):
            return real + LITERAL_INSERT
        return real

    # (A) samples -- _r9s_regress.py:52-68
    sample_rows = []
    for s in S.SAMPLES:
        ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
        sample_rows.append({"id": s["id"], "token": s["token"], "expect": s["expect"],
                            "present": ok, "layer": layer, "pass": (ok == s["expect"])})
    pos_n = sum(1 for x in sample_rows if x["expect"])
    neg_n = sum(1 for x in sample_rows if not x["expect"])
    pos_pass = sum(1 for x in sample_rows if x["expect"] and x["pass"])
    neg_pass = sum(1 for x in sample_rows if not x["expect"] and x["pass"])
    samples_all_pass = (pos_pass == pos_n and neg_pass == neg_n)

    # (B) four real domains -- _r9s_regress.py:125-157 (per-token text selection)
    four_rows = []
    for r in ROWS:
        if r["domain"] not in FOURx:
            continue
        real = texts_for(r["domain"], r["main"])
        elems = elements_of(r)
        missing_r9, missing_r9s, warns = [], [], []
        for k in elems:
            txt = pick(r["domain"], k, real)
            ok0, _l0 = R9S.R9.r9_element_present(txt, k)
            ok1, lay1, _d = R9S.r9s_element_present(txt, k)
            if not ok0:
                missing_r9.append("缺要素 " + k)
            if not ok1:
                missing_r9s.append("缺要素 " + k)
            elif lay1 == "semantic":
                warns.append(k)
        other = [p for p in r["gateProblems"] if not p.startswith("缺要素")]
        remaining = missing_r9s + other
        four_rows.append({"domain": r["domain"], "n_remaining": len(remaining),
                          "remaining": remaining,
                          "non_element_baseline_problems": other,
                          "n_baseline_missing": sum(1 for p in r["gateProblems"]
                                                    if p.startswith("缺要素")),
                          "r9_missing": missing_r9, "r9s_missing": missing_r9s,
                          "warnings": warns})

    # (C) 32 domains -- _r9s_regress.py:162-206
    flips, tightens, n_items = [], [], 0
    for r in ROWS:
        dom = r["domain"]
        real = texts_for(dom, r["main"])
        elems = elements_of(r)
        for k in elems:
            n_items += 1
            txt = pick(dom, k, real)
            ok0, lay0 = R9S.R9.r9_element_present(txt, k)
            ok1, lay1, _ = R9S.r9s_element_present(txt, k)
            if (not ok0) and ok1:
                flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WL,
                              "semantically_empty": (dom, k) in subs})
                if extra_flip and dom == EXTRA_DOMAIN and k == EXTRA_TOKEN:
                    pass
            if ok0 and (not ok1):
                tightens.append({"domain": dom, "token": k})
    if extra_flip:
        # inject a 6th, SEMANTICALLY CORRECT flip: real text of an
        # out-of-whitelist domain replaced by a genuine equivalence form.
        txt = TRUE_EQUIV
        ok0, _ = R9S.R9.r9_element_present(txt, EXTRA_TOKEN)
        ok1, lay1, _ = R9S.r9s_element_present(txt, EXTRA_TOKEN)
        flips.append({"domain": EXTRA_DOMAIN, "token": EXTRA_TOKEN,
                      "whitelisted": (EXTRA_DOMAIN, EXTRA_TOKEN) in WL,
                      "semantically_empty": False,
                      "injected": True, "r9": ok0, "r9s": ok1, "layer": lay1})

    # _r9s_regress.py:204-206 -- VERBATIM
    no_relaxation = (len([f for f in flips if not f["whitelisted"]]) == 0
                     and len(flips) == len(WL)
                     and all(f["whitelisted"] for f in flips))
    # _r9s_regress.py:223-229 -- VERBATIM
    verdict = ("PASS" if (samples_all_pass
                          and no_relaxation
                          and all(x["n_remaining"] == 0 or
                                  all(p in x["non_element_baseline_problems"]
                                      for p in x["remaining"])
                                  for x in four_rows))
               else "FAIL")
    return {
        "scenario": name, "note": note,
        "subs": [[list(k), "semantically_empty"] for k in subs],
        "n_items": n_items,
        "samples": {"positive": pos_n, "negative": neg_n,
                    "positive_pass": pos_pass, "negative_pass": neg_pass,
                    "all_pass": samples_all_pass},
        "n_flips": len(flips), "flips": flips,
        "outside_whitelist": len([f for f in flips if not f["whitelisted"]]),
        "n_tightens": len(tightens),
        "four_domains": four_rows,
        "no_relaxation": no_relaxation,
        "verdict": verdict,
    }


def fidelity(row, ref):
    """Compare k0 replay against the recorded real-run JSON, field by field."""
    checks = {
        "samples.positive": (row["samples"]["positive"], ref["samples"]["positive"]),
        "samples.negative": (row["samples"]["negative"], ref["samples"]["negative"]),
        "samples.positive_pass": (row["samples"]["positive_pass"], ref["samples"]["positive_pass"]),
        "samples.negative_pass": (row["samples"]["negative_pass"], ref["samples"]["negative_pass"]),
        "samples.all_pass": (row["samples"]["all_pass"], ref["samples"]["all_pass"]),
        "n_flips": (row["n_flips"], ref["domains32"]["n_flips"]),
        "n_tightens": (row["n_tightens"], ref["domains32"]["n_tightens"]),
        "outside_whitelist": (row["outside_whitelist"], len(ref["domains32"]["flips_outside_whitelist"])),
        "no_relaxation": (row["no_relaxation"], ref["no_relaxation"]),
        "verdict": (row["verdict"], ref["verdict"]),
        "four_domains_total_remaining": (sum(x["n_remaining"] for x in row["four_domains"]),
                                         ref["four_domains_total_remaining"]),
    }
    flips_a = sorted((f["domain"], f["token"]) for f in row["flips"])
    flips_b = sorted((f["domain"], f["token"]) for f in ref["domains32"]["flips"])
    checks["flip_pairs_identical"] = (flips_a, flips_b)
    return {k: {"replay": a, "recorded": b, "match": a == b} for k, (a, b) in checks.items()}


def main():
    out = {"harness": "in-memory replay; _r9s_regress.py NOT executed (it writes to a read-only dir)",
           "ref_sha256": hashlib.sha256((R9S_DIR / "_r9s_regress_out.json").read_bytes()).hexdigest(),
           "scenarios": []}

    k0 = run("k0_baseline", {})
    out["fidelity_vs_recorded"] = fidelity(k0, REF)
    out["fidelity_all_match"] = all(v["match"] for v in out["fidelity_vs_recorded"].values())
    out["scenarios"].append(k0)

    for k in (1, 2, 3, 4, 5):
        subs = {key: EMPTY[key] for key in EMPTY_ORDER[:k]}
        out["scenarios"].append(run("k%d_empty" % k, subs,
                                    note="%d of 5 whitelist items replaced by semantically-empty text" % k))

    out["scenarios"].append(run(
        "fp_extra_true_flip", {}, extra_flip=True,
        note="6th flip is a GENUINE semantic equivalence (truth correct), outside whitelist"))
    out["scenarios"].append(run(
        "fp_literal_insert", {}, literal_insert=True,
        note="one whitelist item made literally present (truth improved), flip disappears"))
    wl4 = set(WHITELIST) - {("lead/matrix_ab_ruling_20261109/", "需谁批准")}
    out["scenarios"].append(run(
        "fp_drop_one_whitelist_pair", {}, whitelist=wl4,
        note="all 5 flips semantically intact; one pair removed from the whitelist set"))

    print(json.dumps({
        "fidelity_all_match": out["fidelity_all_match"],
        "fidelity_vs_recorded": out["fidelity_vs_recorded"],
        "summary": [{
            "scenario": s["scenario"], "n_items": s["n_items"],
            "n_flips": s["n_flips"], "outside": s["outside_whitelist"],
            "n_tightens": s["n_tightens"],
            "n_semantically_empty_flips": sum(1 for f in s["flips"] if f.get("semantically_empty")),
            "samples_all_pass": s["samples"]["all_pass"],
            "four_remaining": sum(x["n_remaining"] for x in s["four_domains"]),
            "no_relaxation": s["no_relaxation"], "VERDICT": s["verdict"],
        } for s in out["scenarios"]],
    }, ensure_ascii=False, indent=1))

    (WDIR / "_fnr_replay_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\nWROTE _fnr_replay_out.json (write domain only)")


if __name__ == "__main__":
    main()
