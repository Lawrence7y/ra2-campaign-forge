# -*- coding: utf-8 -*-
r"""_cfa_probe.py -- CHECK-FALSE-POSITIVE AUDIT of the new L1/L2/L3 checker.

SOLE WRITE DOMAIN: lead/check_fp_audit_20261109/
READ-ONLY INPUTS (never written):
  lead/falsifiable_no_relax_20261109/_fnr_check.py  (imported as a module; main() NOT called)
  lead/falsifiable_no_relax_20261109/_fnr_check_out.json
  lead/falsifiable_no_relax_20261109/_fnr_REPORT.md
  lead/falsifiable_no_relax_20261109/_fnr_replay_out.json
  lead/falsifiable_no_relax_20261109/_fnrd_verify_out.json
  lead/gate_r9sem_20261109/_r9s_regress_out.json
  lead/gate_r9sem_20261109/_r9s_predicates.py
  lead/gate_r9sem_20261109/_r9s_regress.py
  lead/PENDING_DECISIONS.md, lead/GOAL_THREE_TARGETS_20261018.md
  lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md

This script does NOT modify any predicate / regression / whitelist / existing file.
All worlds are in-memory dicts. Zero real-machine, zero sampling code.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfa_probe.py
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "check_fp_audit_20261109"

# ---- import the checker as a MODULE (main() is NOT executed) ----------------
_spec = importlib.util.spec_from_file_location("cfa_fnr_check", FNR / "_fnr_check.py")
fnr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fnr)
R9S = fnr.R9S
CERTS = fnr.CERTS
ADVERSARIAL = fnr.ADVERSARIAL
SPEC_ROLES = fnr.SPEC_ROLES

# ---- verbatim re-implementation of _fnr_check.py:471-483 repaired_predicate --
AUTHOR_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
    r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
    r"输出数据待补|返回值详见附件"
)


def repaired_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if AUTHOR_GUARD.search(text):
        return (False, "", {"rejected_by": "pending/pointer guard"})
    return (ok, layer, detail)


# ---- rebuild `base` exactly as _fnr_check.py:355-373 ------------------------
REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))


def build_base():
    flips = [{"domain": f["domain"], "token": f["token"]}
             for f in REF["domains32"]["flips"]]
    items = []
    for r in REF["domains32"]["rows"]:
        if r.get("main_missing"):
            continue
        for e in r["per_element"]:
            items.append({"domain": r["domain"], "token": e["token"]})
    wl = [tuple(x) for x in REF["domains32"]["whitelist"]]
    return dict(items=items, flips=flips, whitelist=wl,
                registered_tokens=set(R9S.SPECS.keys()),
                spec_keys=set(R9S.SPECS.keys()),
                certificates=copy.deepcopy(CERTS), spec_roles=SPEC_ROLES,
                predicate=R9S.r9s_element_present,
                adversarial_corpus=list(ADVERSARIAL),
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)


def build_good():
    """The author's synthetic known-good world (_fnr_check.py:485-488)."""
    g = build_base()
    g["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    g["predicate"] = repaired_predicate
    return g


ALL_ITEM_TOKENS = {i["token"] for i in build_base()["items"]}
# audit-only side data (NOT passed to the checker's strict 13-param signature)
SCENARIO_SIDE = {}


def real_seal(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


# ===========================================================================
# BENIGN SCENARIOS -- each is a world in which "no relaxation" GENUINELY holds
# (all 5 flips semantically delivered, independent oracle, all adversarial
# caught, whitelist sealed & independent). Such a world SHOULD PASS.
# ===========================================================================

def s01_current_assumption():
    """现状假设成立: 5 白名单项内容正确且语义在场 (沿用上游 5/5 裁决).
    本该 PASS 的依据: WHITELIST_AUDIT.md:498/:516 判 5/5 应保留、语义在场.
    注意: 现盘 R9S 谓词自身有 6 条对抗泄漏 —— 该场景的 ALARM 需按层分解."""
    return build_base()


def s02_full_coverage():
    """谓词覆盖全部 token, 无结构性未测 (coverage_ratio=1.0)."""
    g = build_good()
    g["registered_tokens"] = set(ALL_ITEM_TOKENS)
    return g


def s03_third_party_oracle():
    """有第三方盲标注真值表: 每份证书附真实 sha256 封印, 标注者与谓词作者异源."""
    g = build_good()
    certs = copy.deepcopy(g["certificates"])
    for k, c in certs.items():
        c["oracle_author"] = "independent_blind_adjudicator"
        c["predicate_author"] = "author_of_V1"
        c["oracle_sealed"] = True
    SCENARIO_SIDE["S03"] = {
        "oracle_seal_sha256_per_cert": {str(k): real_seal({"k": list(k), "truth": True})
                                        for k in certs},
        "note": "Real hashlib seals computed; checker never reads them "
                "(certificate_ok():116-123 only checks the boolean oracle_sealed)."}
    g["certificates"] = certs
    return g


def s04_all_adversarial_caught():
    """对抗样本全被抓: 在 13 条基础上扩到 16 条, 16/16 全抓."""
    g = build_good()
    extra = [
        ("EX1", "需谁批准", "## 5 清单\n批准人待判，本件不另下结论。\n"),
        ("EX2", "改前改后", "## 4 草案\n【改前】详见台账。\n【改后】本件不重录。\n"),
        ("EX3", "可重建", "## 4 结论\n是否【可唯一重建】尚需核对。\n"),
    ]
    g["adversarial_corpus"] = list(ADVERSARIAL) + extra
    return g


def s05_compliant_same_source():
    """合规同源: SPECS 就是白名单 5 项的逐角色展开 (本项目真实设计), 其余全部合规.
    _r9s_regress.py:112-119 白名单 = 任务书指名的 5 处; _r9s_predicates.py:371-402
    SPECS = 恰好这 5 个 token 的角色规格. => 同源是合规设计, 不是缺陷."""
    g = build_good()
    g["spec_keys"] = set(R9S.SPECS.keys())
    return g


def s06_same_source_full_coverage_sealed():
    """合规同源 + 全覆盖 + 真第三方封印: 最大化合规的同源世界."""
    g = s05_compliant_same_source()
    g["registered_tokens"] = set(ALL_ITEM_TOKENS)
    g["certificates"] = s03_third_party_oracle()["certificates"]
    return g


def s07_same_source_independent_whitelist():
    """合规同源 + 白名单确由第三方封印且独立 (whitelist_author=independent,
    sealed=True, 附真实 wl 哈希). L1 的 self_certified 判定完全不看这些."""
    g = s05_compliant_same_source()
    g["whitelist_author"] = "independent"
    g["whitelist_sealed"] = True
    SCENARIO_SIDE["S07"] = {
        "whitelist_seal_sha256": real_seal([list(x) for x in g["whitelist"]]),
        "note": "Real hashlib seal computed for the whitelist; L1 never reads it."}
    return g


def s08_extra_true_flip():
    """追加 1 条真·语义等价翻案 (旧检验 fp_extra_true_flip 本该 PASS 的场景),
    白名单/证书同步配齐."""
    g = build_good()
    dom = "lead/handoff_pack_20261109/"
    tok = "需谁批准"
    g["flips"] = list(g["flips"]) + [{"domain": dom, "token": tok}]
    g["whitelist"] = list(g["whitelist"]) + [(dom, tok)]
    certs = copy.deepcopy(g["certificates"])
    certs[(dom, tok)] = {
        "anchor": "lead/handoff_pack_20261109/HANDOFF_PACK.md:12",
        "quote": "批准人一律 = 乙设计责任人，逐项对应",
        "roles": {"批准人角色头": "批准人", "赋值算子": "一律 =",
                  "具体施事值": "乙设计责任人"},
        "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
        "predicate_author": "author_of_V1", "oracle_sealed": True}
    g["certificates"] = certs
    return g


def s09_benign_reword():
    """良性变体: 证书引文合法改写 (作者自己的 g_reworded_quote)."""
    g = build_good()
    certs = copy.deepcopy(g["certificates"])
    k0 = list(certs)[0]
    certs[k0]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节）"
    g["certificates"] = certs
    return g


def s10_drop_one_pair():
    """良性变体: 删 1 对白名单并同步删对应 flip/证书 (旧检验
    fp_drop_one_whitelist_pair 本该 PASS 的场景), 原文语义全不动."""
    g = build_good()
    target = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    g["flips"] = [f for f in g["flips"]
                  if (f["domain"], f["token"]) != target]
    g["whitelist"] = [w for w in g["whitelist"] if tuple(w) != target]
    certs = copy.deepcopy(g["certificates"])
    certs.pop(target, None)
    g["certificates"] = certs
    return g


SCENARIOS = [
    ("S01", "现状假设成立(白名单5项内容正确且语义在场)", s01_current_assumption),
    ("S02", "谓词覆盖全部token(无结构性未测)", s02_full_coverage),
    ("S03", "有第三方盲标注真值表(真sha256封印)", s03_third_party_oracle),
    ("S04", "对抗样本全被抓(16/16)", s04_all_adversarial_caught),
    ("S05", "合规同源:SPECS是白名单的展开", s05_compliant_same_source),
    ("S06", "合规同源+全覆盖+真第三方封印", s06_same_source_full_coverage_sealed),
    ("S07", "合规同源+白名单第三方封印且独立", s07_same_source_independent_whitelist),
    ("S08", "追加1条真语义等价翻案", s08_extra_true_flip),
    ("S09", "良性引文改写", s09_benign_reword),
    ("S10", "删1对白名单并同步删flip", s10_drop_one_pair),
]


def run_scenarios():
    rows = []
    for sid, name, fn in SCENARIOS:
        w = fn()
        r = fnr.no_relaxation_check(**w)
        row = {
            "id": sid, "name": name,
            "VERDICT": r["VERDICT"],
            "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
            "L1_problems": r["L1"]["problems"],
            "L1_detail": r["L1"]["detail"],
            "L3_n_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "L3_n_total": r["L3"]["detail"]["n_adversarial"],
            "L3_problem_count": len(r["L3"]["problems"]),
        }
        row["triggered_layers"] = [L for L in ("L1", "L2", "L3")
                                   if not row[L + "_ok"]]
        row["false_alarm"] = (r["VERDICT"] == "ALARM")
        rows.append(row)
    return rows


# ===========================================================================
# INDEPENDENCE / META-TEST PROBES
# ===========================================================================

def p1_forged_certificates():
    """L2 degenerates to self-certification: fabricated anchors/quotes with
    self-declared independence flags -> L2 ok=True (no file/seal resolution)."""
    g = build_good()
    forged = copy.deepcopy(g["certificates"])
    for i, (k, c) in enumerate(forged.items()):
        c["anchor"] = "nowhere/FAKE_%d.md:999" % i
        c["quote"] = "这是一条由审计员凭空编造的引文，未在任何文件中出现。"
        c["oracle_truth"] = True
        c["oracle_author"] = "independent_blind_adjudicator"
        c["predicate_author"] = "author_of_V1"
        c["oracle_sealed"] = True
    g["certificates"] = forged
    r = fnr.no_relaxation_check(**g)
    return {"VERDICT": r["VERDICT"], "L2_ok": r["L2"]["ok"],
            "L1_ok": r["L1"]["ok"], "L3_ok": r["L3"]["ok"],
            "anchor_files_exist": False,
            "note": "L2 never resolves file:line, never verifies a hash seal; "
                    "it only reads caller-supplied booleans."}


def p2_guard_fit_and_novel():
    """L3 self-certification: is the good-world guard regex fitted to the
    author's own 13 adversarial payloads? What about novel empties?"""
    fit = []
    for cid, tok, txt in ADVERSARIAL:
        hits = [w for w in ("待判", "待定", "尚需", "尚未", "不另下结论",
                            "暂不作判定", "本件不重录", "见台账", "详见台账",
                            "详见附件", "并非【", "是否【", "不可重建",
                            "输出数据待补", "返回值详见附件") if w in txt]
        fit.append({"id": cid, "n_guard_hits": len(hits), "hits": hits})
    novel = [
        ("N-EMPTY-1", "需谁批准", "## 5 改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准。\n"),
        ("N-EMPTY-2", "改前改后", "## 4 订正草案\n【改前】旧句共 13 项分写。\n【改后】新句见另册对应行。\n逐处对照表另附。\n"),
        ("N-EMPTY-3", "可重建", "## 4 重建可行性\n判定：正确算法【可唯一重建】。原始采样记录见归档索引。\n"),
    ]
    nrows = []
    for cid, tok, txt in novel:
        nrows.append({"id": cid, "guard_hit": bool(AUTHOR_GUARD.search(txt)),
                      "r9s_present": bool(R9S.r9s_element_present(txt, tok)[0]),
                      "repaired_present": bool(repaired_predicate(txt, tok)[0]),
                      "caught": not bool(repaired_predicate(txt, tok)[0])})
    g = build_good()
    g["adversarial_corpus"] = list(ADVERSARIAL) + novel
    r = fnr.no_relaxation_check(**g)
    return {"guard_word_fit": fit,
            "n_corpus_with_guard_word": sum(1 for x in fit if x["n_guard_hits"] > 0),
            "n_corpus_total": len(fit),
            "novel_empties": nrows,
            "good_world_plus_novel_VERDICT": r["VERDICT"],
            "good_world_plus_novel_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "good_world_plus_novel_total": r["L3"]["detail"]["n_adversarial"]}


def p3_meta_baseline_not_asserted():
    """meta_test() does NOT include baseline_VERDICT in CHECKER_VALID
    (_fnr_check.py:258,275,280). Executable proof: 0 wrongs + 0 goods on the
    REAL (ALARM) baseline -> CHECKER_VALID = true."""
    m = fnr.meta_test(build_base(), [], [])
    return {"baseline_VERDICT": m["baseline_VERDICT"],
            "n_wrong": m["n_wrong"], "n_wrong_caught": m["n_wrong_caught"],
            "n_good": m["n_good"], "n_false_alarms": m["n_false_alarms"],
            "CHECKER_VALID": m["CHECKER_VALID"],
            "note": "CHECKER_VALID=true although baseline is ALARM. "
                    "The formula omits baseline entirely."}


def p4_first_run_baseline_sensitivity():
    """Reproduce the recorded first-run state: using the REAL state as baseline
    makes both benign variations inherit ALARM -> 2 false alarms,
    CHECKER_VALID=false (_fnr_REPORT.md:239)."""
    def g_reword(kw):
        d = dict(kw)
        certs = copy.deepcopy(kw["certificates"])
        certs[list(certs)[0]]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节）"
        d["certificates"] = certs
        return d

    def g_extra(kw):
        d = dict(kw)
        d["adversarial_corpus"] = list(kw["adversarial_corpus"]) + [
            ("EXTRA", "可重建", "## 4 结论\n不可重建：证据待补。\n")]
        return d

    m = fnr.meta_test(build_base(), [], [("reworded_quote_still_true", g_reword),
                                         ("extra_adversarial_case_caught", g_extra)])
    return {"baseline_VERDICT": m["baseline_VERDICT"],
            "good_variations": m["good_variations"],
            "n_false_alarms": m["n_false_alarms"],
            "CHECKER_VALID": m["CHECKER_VALID"]}


def p5_l1_signature():
    """L1 alone: does the checker have ANY delivered-artifact input?"""
    import inspect
    names = list(inspect.signature(fnr.no_relaxation_check).parameters)
    exact = {"artifacts", "artifact", "artifact_text", "text", "texts", "main",
             "mains", "source", "sources", "documents", "docs", "deliverables",
             "files", "file_texts"}
    l1_names = list(inspect.signature(fnr.check_l1).parameters)
    return {"checker_params": names, "n_params": len(names),
            "has_artifact_text_param": bool(set(names) & exact),
            "check_l1_params": l1_names,
            "note": "check_l1 has no certificate / artifact / oracle parameter; "
                    "it can only see set structure."}


def p6_real_leaks():
    """Confirm exactly which 6 of 13 adversarial payloads the REAL R9S leaks."""
    rows = []
    for cid, tok, txt in ADVERSARIAL:
        present = bool(R9S.r9s_element_present(txt, tok)[0])
        rows.append({"id": cid, "token": tok, "present": present,
                     "caught": not present})
    return {"rows": rows, "n": len(rows),
            "n_caught": sum(1 for r in rows if r["caught"]),
            "leaked_ids": [r["id"] for r in rows if not r["caught"]]}


def p7_zero_of_two_ci():
    """Statistical power of the meta-test: with 9/9 caught and 0/2 false alarms,
    what are the one-sided 95% bounds on sensitivity and FP rate?"""
    n_wrong, caught = 9, 9
    n_good, n_fp = 2, 0
    sens_lower = 0.05 ** (1.0 / n_wrong)
    fp_upper = 1.0 - (0.05 ** (1.0 / n_good))
    return {"n_wrong": n_wrong, "n_wrong_caught": caught,
            "one_sided_95pct_sensitivity_lower_bound": round(sens_lower, 6),
            "n_good": n_good, "n_false_alarms": n_fp,
            "one_sided_95pct_FP_upper_bound": round(fp_upper, 6),
            "note": "9/9 caught only supports 'sensitivity >= 71.7%'; 0/2 "
                    "cannot rule out a 77.6% false-positive rate."}


def p8_all_defects_repaired_same_source():
    """DECISIVE: repair every REAL defect (use the author's repaired predicate so
    all 13 adversarial are caught, full token coverage, third-party sealed
    oracle) but keep the compliant same-source SPECS=whitelist expansion.
    If ALARM persists, the checker is over-strict rather than reporting a
    real defect of the world."""
    g = build_good()                 # repaired predicate + 13/13 caught
    g["spec_keys"] = set(R9S.SPECS.keys())          # remove the dummy padding
    g["registered_tokens"] = set(ALL_ITEM_TOKENS)   # coverage_ratio = 1.0
    g["certificates"] = s03_third_party_oracle()["certificates"]
    r = fnr.no_relaxation_check(**g)
    l1 = fnr.check_l1(g["items"], g["flips"], g["whitelist"],
                      g["registered_tokens"], g["spec_keys"],
                      g["whitelist_sealed"], g["whitelist_author"])
    return {"VERDICT": r["VERDICT"],
            "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
            "L1_problems": r["L1"]["problems"],
            "L1_coverage_ratio": l1[2]["coverage_ratio"],
            "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "L3_total": r["L3"]["detail"]["n_adversarial"],
            "all_real_defects_repaired": True,
            "note": "All real defects repaired, yet L1 still ALARMs solely on "
                    "the same-source identity. This is over-strictness."}


def p9_padding_trick():
    """Show the sole difference between the author's PASS good-base and the
    ALARM same-source world is one unrelated dummy spec key."""
    a = build_good()                                   # has dummy key -> PASS
    b = build_good()
    b["spec_keys"] = set(R9S.SPECS.keys())             # no dummy key -> ALARM
    ra = fnr.no_relaxation_check(**a)
    rb = fnr.no_relaxation_check(**b)
    return {"with_dummy_key_VERDICT": ra["VERDICT"],
            "with_dummy_key_L1_ok": ra["L1"]["ok"],
            "without_dummy_key_VERDICT": rb["VERDICT"],
            "without_dummy_key_L1_ok": rb["L1"]["ok"],
            "without_dummy_key_L1_problems": rb["L1"]["problems"],
            "dummy_key": "额外预留要素",
            "spec_keys_with": sorted(a["spec_keys"]),
            "spec_keys_without": sorted(b["spec_keys"]),
            "note": "Adding one unrelated key flips ALARM->PASS. The criterion "
                    "measures set inequality, not provenance independence."}


def p10_which_layer_catches_wrong_injections():
    """From the recorded meta-test: how many of the 9 known-wrong injections
    does EACH layer catch? Says what L1 alone is worth."""
    d = json.loads((FNR / "_fnr_check_out.json").read_text(encoding="utf-8"))
    rows = d["new_check_meta_test"]["wrong_injections"]
    counts = {"L1": 0, "L2": 0, "L3": 0}
    for r in rows:
        for L in counts:
            if not r["layers"][L]:
                counts[L] += 1
    return {"n_wrong": len(rows), "per_layer_alarm_counts": counts,
            "L1_alone_recall": round(counts["L1"] / len(rows), 4),
            "note": "L1 alone catches only %d/%d known-wrong worlds." %
                    (counts["L1"], len(rows))}


def p11_coverage_never_fails():
    """Verify coverage_ratio is reported but NEVER a FAIL condition:
    set registered_tokens=empty (coverage 0.0) and see L1 ok."""
    g = build_good()
    r0 = fnr.no_relaxation_check(**g)
    g["registered_tokens"] = set()          # coverage_ratio -> 0.0
    r1 = fnr.no_relaxation_check(**g)
    l1 = fnr.check_l1(g["items"], g["flips"], g["whitelist"],
                      g["registered_tokens"], g["spec_keys"], True, "independent")
    return {"baseline_coverage": r0["L1"]["detail"]["coverage_ratio"],
            "zero_coverage_L1_ok": r1["L1"]["ok"],
            "zero_coverage_ratio": l1[2]["coverage_ratio"],
            "zero_coverage_problems": l1[1],
            "VERDICT_with_zero_coverage": r1["VERDICT"],
            "note": "coverage is decorative: 0.0 coverage still PASSes."}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]


def main():
    out = {}
    # fingerprints of every read-only input touched
    fps = {}
    for rel in ["lead/falsifiable_no_relax_20261109/_fnr_check.py",
                "lead/falsifiable_no_relax_20261109/_fnr_check_out.json",
                "lead/falsifiable_no_relax_20261109/_fnr_REPORT.md",
                "lead/falsifiable_no_relax_20261109/_fnr_replay_out.json",
                "lead/falsifiable_no_relax_20261109/_fnrd_verify_out.json",
                "lead/gate_r9sem_20261109/_r9s_regress_out.json",
                "lead/gate_r9sem_20261109/_r9s_predicates.py",
                "lead/gate_r9sem_20261109/_r9s_regress.py",
                "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",
                "lead/PENDING_DECISIONS.md",
                "lead/GOAL_THREE_TARGETS_20261018.md"]:
        b = (ROOT / rel).read_bytes()
        fps[rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
    out["input_fingerprints"] = fps

    rows = run_scenarios()
    out["benign_scenarios"] = rows
    out["scenario_side_data"] = SCENARIO_SIDE
    n = len(rows)
    n_fp = sum(1 for r in rows if r["false_alarm"])
    # strict subset: exclude S01 (confounded by real R9S leaks)
    strict = [r for r in rows if r["id"] != "S01"]
    n_fp_strict = sum(1 for r in strict if r["false_alarm"])
    out["fp_rate"] = {
        "n_benign_ask_minimum_8": 8,
        "n_false_alarms_first8": sum(1 for r in rows[:8] if r["false_alarm"]),
        "fp_rate_first8": round(sum(1 for r in rows[:8] if r["false_alarm"]) / 8, 6),
        "wilson95_first8": wilson(sum(1 for r in rows[:8] if r["false_alarm"]), 8),
        "n_benign": n, "n_false_alarms": n_fp,
        "fp_rate_all10": round(n_fp / n, 6),
        "wilson95_all10": wilson(n_fp, n),
        "n_benign_strict9": len(strict), "n_false_alarms_strict9": n_fp_strict,
        "fp_rate_strict9": round(n_fp_strict / len(strict), 6),
        "wilson95_strict9": wilson(n_fp_strict, len(strict)),
        "false_alarm_ids": [r["id"] for r in rows if r["false_alarm"]],
        "note": "S01 is confounded: its L3 alarm is a REAL R9S predicate leak; "
                "its L1 alarm is spurious. Strict9 = S02..S10 (all built on the "
                "known-good world, so any ALARM is unambiguously a false alarm).",
    }
    out["p1_forged_certificates"] = p1_forged_certificates()
    out["p2_guard_fit_and_novel"] = p2_guard_fit_and_novel()
    out["p3_meta_baseline_not_asserted"] = p3_meta_baseline_not_asserted()
    out["p4_first_run_baseline_sensitivity"] = p4_first_run_baseline_sensitivity()
    out["p5_l1_signature"] = p5_l1_signature()
    out["p6_real_leaks"] = p6_real_leaks()
    out["p7_zero_of_two_ci"] = p7_zero_of_two_ci()
    out["p8_all_defects_repaired_same_source"] = p8_all_defects_repaired_same_source()
    out["p9_padding_trick"] = p9_padding_trick()
    out["p10_which_layer_catches_wrong_injections"] = p10_which_layer_catches_wrong_injections()
    out["p11_coverage_never_fails"] = p11_coverage_never_fails()

    # independent recomputation of L1 numbers
    b = build_base()
    reg = set(R9S.SPECS.keys())
    untested = [i for i in b["items"] if i["token"] not in reg]
    wl_tokens = {k for _, k in b["whitelist"]}
    out["l1_recompute"] = {
        "n_items": len(b["items"]), "n_flips": len(b["flips"]),
        "n_whitelist": len(b["whitelist"]),
        "n_spec_keys": len(R9S.SPECS),
        "registered_tokens": sorted(reg),
        "n_structurally_untested": len(untested),
        "n_tested": len(b["items"]) - len(untested),
        "coverage_ratio": round((len(b["items"]) - len(untested)) / len(b["items"]), 4),
        "wl_tokens": sorted(wl_tokens),
        "spec_keys": sorted(reg),
        "wl_tokens_eq_spec_keys": wl_tokens == reg,
        "code_uses_set_not_multiset": True,
    }

    (WDIR / "_cfa_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    # ---------------- console summary ----------------
    print("=== INPUT FINGERPRINTS (hashlib.sha256) ===")
    for k, v in fps.items():
        print("  %s sha256=%s bytes=%d" % (k, v["sha256"], v["bytes"]))
    print("\n=== L1 RECOMPUTE ===")
    print(json.dumps(out["l1_recompute"], ensure_ascii=False, indent=1))
    print("\n=== 10 BENIGN SCENARIOS ===")
    for r in rows:
        print("  %-4s %-42s VERDICT=%-5s layers_false=%-14s FP=%s" %
              (r["id"], r["name"][:42], r["VERDICT"],
               ",".join(r["triggered_layers"]) or "-", r["false_alarm"]))
    print("\n  FP RATE (all 10)   = %d/%d = %.4f  wilson95=%s" %
          (n_fp, n, n_fp / n, wilson(n_fp, n)))
    print("  FP RATE (strict 9) = %d/%d = %.4f  wilson95=%s" %
          (n_fp_strict, len(strict), n_fp_strict / len(strict),
           wilson(n_fp_strict, len(strict))))
    print("  false_alarm_ids =", out["fp_rate"]["false_alarm_ids"])
    print("\n=== PROBES ===")
    print("P1 forged certs        :", json.dumps(out["p1_forged_certificates"], ensure_ascii=False))
    print("P2 guard fit           : %d/%d corpus items contain >=1 guard word" %
          (out["p2_guard_fit_and_novel"]["n_corpus_with_guard_word"],
           out["p2_guard_fit_and_novel"]["n_corpus_total"]))
    print("P2 novel empties       :", json.dumps(out["p2_guard_fit_and_novel"]["novel_empties"], ensure_ascii=False))
    print("P2 good+novel          : %s caught=%d/%d" %
          (out["p2_guard_fit_and_novel"]["good_world_plus_novel_VERDICT"],
           out["p2_guard_fit_and_novel"]["good_world_plus_novel_caught"],
           out["p2_guard_fit_and_novel"]["good_world_plus_novel_total"]))
    print("P3 meta baseline       :", json.dumps(out["p3_meta_baseline_not_asserted"], ensure_ascii=False))
    print("P4 first-run baseline  :", json.dumps(out["p4_first_run_baseline_sensitivity"], ensure_ascii=False))
    print("P5 L1 signature        :", json.dumps(out["p5_l1_signature"], ensure_ascii=False))
    print("P6 real R9S leaks      : %d/%d caught, leaked=%s" %
          (out["p6_real_leaks"]["n_caught"], out["p6_real_leaks"]["n"],
           out["p6_real_leaks"]["leaked_ids"]))
    print("P7 9/9 & 0/2 bounds  :", json.dumps(out["p7_zero_of_two_ci"], ensure_ascii=False))
    print("P8 all-repaired      :", json.dumps(out["p8_all_defects_repaired_same_source"], ensure_ascii=False))
    print("P9 padding trick     :", json.dumps(out["p9_padding_trick"], ensure_ascii=False))
    print("P10 per-layer recall :", json.dumps(out["p10_which_layer_catches_wrong_injections"], ensure_ascii=False))
    print("P11 coverage 0.0     :", json.dumps(out["p11_coverage_never_fails"], ensure_ascii=False))
    print("\nWROTE _cfa_out.json")


if __name__ == "__main__":
    main()
