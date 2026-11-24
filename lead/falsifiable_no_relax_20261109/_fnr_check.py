# -*- coding: utf-8 -*-
r"""_fnr_check.py -- a FALSIFIABLE "no relaxation" checker (L1/L2/L3) + meta-test.

DESIGN PRINCIPLE
----------------
The original check (lead/gate_r9sem_20261109/_r9s_regress.py:204-206) compares
the flip set against a whitelist that was built from the same 5 items. It is a
set-equality test on two same-source sets; it has ZERO access to the semantic
truth of any flip. A checker is only a checker if there EXISTS an input on which
the conclusion is wrong and the checker ALARMS. We make that existence an
explicit, executable requirement (L3 + meta-test).

THREE LAYERS
------------
L1 STRUCTURE  : flip set / whitelist containment + count + COVERAGE DECLARATION.
                Coverage: report how many items are structurally incapable of
                flipping (unregistered tokens) as "UNTESTED", never as evidence.
                Also detect SELF_CERTIFIED when whitelist tokens == SPECS keys.
L2 SEMANTICS  : every flip must carry an independent truth certificate:
                (a) an anchored quote from the artifact (file:line),
                (b) role-by-role positive evidence for EVERY required role,
                (c) a POINTER/PLACEHOLDER/PENDING/NEGATION guard on every value,
                (d) agreement with a pre-registered INDEPENDENT oracle label.
                The oracle MUST be supplied from outside the predicate's author.
L3 ADVERSARIAL: (i) a pre-registered adversarial corpus (form-like-but-empty
                payloads) must ALL be judged ABSENT; (ii) MUTATION INJECTION:
                for each flip, replace its certificate value by a pointer;
                the checker MUST alarm. If no mutation makes it alarm, the
                checker is DECLARED INVALID (decorative), regardless of PASS.

META-TEST (proves the checker works)
------------------------------------
Inject N known WRONG states into a known-GOOD world; require ALARM on each.
Inject M known GOOD variations; require NO ALARM. If any wrong state passes,
the checker is invalid. This is executable inside `meta_test()`.

No predicate, regression script or whitelist is modified. Everything is in
memory. Run:
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_check.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(R9S_DIR))
import _r9s_predicates as R9S  # noqa: E402

# ===========================================================================
# PASTEABLE CORE -- generic, no project-specific assumptions
# ===========================================================================

# Values that are pointers / placeholders / undecided / negated, i.e. NOT a
# delivered semantic value. A checker that accepts these is not checking truth.
NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$"
)

# ---------------------------------------------------------------------------
# OPERATIONAL DEFINITION OF "NO RELAXATION" (non-circular)
# ---------------------------------------------------------------------------
# Let V0 be the old predicate, V1 the new predicate, I the item universe.
# Let ORACLE: I -> {0,1} be a ground-truth label produced BEFORE V1 is run,
# by an adjudicator who does not see V1's outputs and did not author V1,
# with a published SHA256 seal. truth=1 means "the required semantic content
# is genuinely delivered in this artifact", judged role-by-role.
#
#   NO_RELAXATION :=
#     (A) SOUNDNESS   ∀i∈I: V0(i)=0 ∧ V1(i)=1  ⇒ ORACLE(i)=1
#     (B) BOUNDED TIGHTENING ∀i∈I: V0(i)=1 ∧ V1(i)=0 ⇒ ORACLE(i)=0
#     (C) ORACLE COVERAGE  |{i : ORACLE(i) defined}| = |I|
#         (structurally-fixed items are labelled, NOT counted as evidence)
#     (D) SENSITIVITY  ∃ injected error e with ORACLE(e)=0 ∧ V1(e)=1
#         such that CHECK(e) = ALARM   [proved by meta_test]
#     (E) WHITELIST PROVENANCE  whitelist is sealed, pre-registered, and its
#         token multiset is NOT identical to the new predicate's spec keys.
#
# This is operational: every quantifier ranges over a finite, enumerable item
# list; ORACLE is a concrete JSON table; SENSITIVITY is an executable test.
# It is NOT "did not get looser": it names the independent ground truth that
# would have to be violated for the claim to be false.
# ---------------------------------------------------------------------------


def certificate_ok(cert: dict, required_roles: list) -> tuple:
    """L2: validate one flip's independent truth certificate."""
    problems = []
    # (a) anchor
    anchor = cert.get("anchor", "")
    if not re.search(r"^.+:\d+$", anchor):
        problems.append("L2a: no file:line anchor")
    quote = cert.get("quote", "")
    if len(quote) < 10:
        problems.append("L2a: quote too short / absent")
    # (b) every required role has positive evidence
    roles = cert.get("roles", {})
    for r in required_roles:
        v = str(roles.get(r, ""))
        if not v or len(v) < 2:
            problems.append("L2b: missing role %s" % r)
            continue
        # (c) the value must be a real value, not a pointer / undecided marker
        if NON_VALUE_RE.search(v):
            problems.append("L2c: role %s value is a non-value: %r" % (r, v[:40]))
    # (d) independent oracle
    if "oracle_truth" not in cert:
        problems.append("L2d: no independent oracle label")
    elif cert["oracle_truth"] is not True:
        problems.append("L2d: oracle says semantic content NOT delivered")
    if cert.get("oracle_author", "") == cert.get("predicate_author", ""):
        problems.append("L2d: oracle author == predicate author (not independent)")
    if not cert.get("oracle_sealed"):
        problems.append("L2d: oracle not hash-sealed / not pre-registered")
    return (len(problems) == 0, problems)


def check_l1(items, flips, whitelist, registered_tokens, predicate_spec_keys,
             whitelist_sealed=True, whitelist_author="independent"):
    """L1 STRUCTURE. Returns (ok, detail)."""
    wl = {tuple(x) for x in whitelist}
    flip_keys = [(f["domain"], f["token"]) for f in flips]
    outside = [k for k in flip_keys if k not in wl]
    # COVERAGE: items whose token is not registered in V1 can NEVER flip.
    # They are UNTESTED, not evidence of no relaxation.
    untested = [i for i in items if i["token"] not in registered_tokens]
    # SELF-CERTIFICATION: whitelist tokens == spec keys is a design consequence.
    wl_tokens = {k for _, k in wl}
    self_certified = (wl_tokens == set(predicate_spec_keys))
    problems = []
    if outside:
        problems.append("L1: %d flips outside whitelist: %s" % (len(outside), outside))
    if len(flip_keys) != len(wl):
        problems.append("L1: flip count %d != whitelist size %d" % (len(flip_keys), len(wl)))
    if not whitelist_sealed:
        problems.append("L1: whitelist not hash-sealed / not pre-registered")
    if whitelist_author == "predicate_author":
        problems.append("L1: whitelist authored by predicate author")
    if self_certified:
        problems.append("L1: SELF_CERTIFIED -- whitelist token multiset == predicate "
                        "spec keys; 'outside=0' is a design consequence, not evidence")
    detail = {"n_items": len(items), "n_flips": len(flip_keys),
              "outside_whitelist": len(outside),
              "n_structurally_untested": len(untested),
              "coverage_ratio": round((len(items) - len(untested)) / max(len(items), 1), 4),
              "self_certified": self_certified,
              "verdict_note": "L1 alone can only ALARM on set changes; it can never "
                              "validate semantic truth. L2+L3 are mandatory."}
    return (len(problems) == 0, problems, detail)


def check_l2(flips, certificates, spec_roles):
    """L2 SEMANTICS. Returns (ok, detail)."""
    rows, problems = [], []
    for f in flips:
        key = (f["domain"], f["token"])
        cert = certificates.get(key)
        if cert is None:
            problems.append("L2: no independent certificate for %s" % (key,))
            rows.append({"item": key, "ok": False, "problems": ["certificate absent"]})
            continue
        roles = spec_roles.get(f["token"], [])
        ok, why = certificate_ok(cert, roles)
        rows.append({"item": list(key), "ok": ok, "problems": why})
        if not ok:
            problems.extend("L2[%s|%s] %s" % (key[0], key[1], p) for p in why)
    return (len(problems) == 0, problems, rows)


def check_l3(predicate, adversarial_corpus, certificates, flips, spec_roles,
             mutation_payload="见台账登记，本件不重录"):
    """L3 ADVERSARIAL. Returns (ok, detail).

    (i) every form-like-but-empty payload must be judged ABSENT by V1;
    (ii) MUTATION INJECTION: for each flip, replace each certificate role value
         with a pointer and require certificate_ok() to ALARM. If no mutation
         alarms, the L2 checker itself is declared INVALID.
    """
    problems, adv_rows, mutation_rows = [], [], []
    for cid, token, text in adversarial_corpus:
        try:
            present = bool(predicate(text, token)[0])
        except Exception as e:
            present, cid = None, "%s(ERROR %s)" % (cid, e)
        caught = (present is False)
        adv_rows.append({"id": cid, "token": token, "present": present, "caught": caught})
        if not caught:
            problems.append("L3i: adversarial %s (%s) judged PRESENT -- semantic leak" % (cid, token))
    n_alarms = 0
    for f in flips:
        key = (f["domain"], f["token"])
        cert = certificates.get(key)
        if cert is None:
            continue
        roles = spec_roles.get(f["token"], [])
        for role in roles:
            mutated = json.loads(json.dumps(cert))
            mutated.setdefault("roles", {})[role] = mutation_payload
            ok, why = certificate_ok(mutated, roles)
            mutation_rows.append({"item": list(key), "mutated_role": role,
                                  "alarm": not ok})
            if not ok:
                n_alarms += 1
            else:
                problems.append("L3ii: mutation of %s|%s role %s produced NO alarm"
                                % (f["token"], f["domain"], role))
    if n_alarms == 0:
        problems.append("L3ii: ZERO mutations alarmed -> checker is DECORATIVE, invalid")
    detail = {"adversarial": adv_rows,
              "n_adversarial": len(adv_rows),
              "n_adversarial_caught": sum(1 for r in adv_rows if r["caught"]),
              "mutations": mutation_rows,
              "n_mutations": len(mutation_rows), "n_mutation_alarms": n_alarms,
              "sensitivity_proved": n_alarms > 0}
    return (len(problems) == 0, problems, detail)


def no_relaxation_check(items, flips, whitelist, registered_tokens, spec_keys,
                        certificates, spec_roles, predicate, adversarial_corpus,
                        predicate_author="author_of_V1",
                        whitelist_author="independent", whitelist_sealed=True,
                        mutation_payload="见台账登记，本件不重录"):
    """The full falsifiable check. ALARM (False) if ANY layer fails."""
    l1_ok, l1_p, l1_d = check_l1(items, flips, whitelist, registered_tokens,
                                 spec_keys, whitelist_sealed, whitelist_author)
    l2_ok, l2_p, l2_d = check_l2(flips, certificates, spec_roles)
    l3_ok, l3_p, l3_d = check_l3(predicate, adversarial_corpus, certificates,
                                 flips, spec_roles, mutation_payload)
    ok = l1_ok and l2_ok and l3_ok
    return {"no_relaxation": ok, "VERDICT": "PASS" if ok else "ALARM",
            "L1": {"ok": l1_ok, "problems": l1_p, "detail": l1_d},
            "L2": {"ok": l2_ok, "problems": l2_p, "rows": l2_d},
            "L3": {"ok": l3_ok, "problems": l3_p, "detail": l3_d}}


# ===========================================================================
# META-TEST: prove the checker itself catches errors
# ===========================================================================

def meta_test(base_kwargs, wrong_variants, good_variants):
    """Inject known WRONG worlds -> require ALARM. Known GOOD worlds -> no ALARM.

    wrong_variants: list of (name, mutate_fn) where mutate_fn(kwargs)->kwargs
    good_variants : same, but the world is still semantically correct.
    """
    def run(kw):
        return no_relaxation_check(**kw)

    baseline = run(base_kwargs)
    wrong_rows, good_rows = [], []
    for name, mut in wrong_variants:
        r = run(mut(base_kwargs))
        wrong_rows.append({"name": name, "VERDICT": r["VERDICT"],
                           "alarmed": r["VERDICT"] == "ALARM",
                           "layers": {"L1": r["L1"]["ok"], "L2": r["L2"]["ok"],
                                      "L3": r["L3"]["ok"]}})
    for name, mut in good_variants:
        r = run(mut(base_kwargs))
        good_rows.append({"name": name, "VERDICT": r["VERDICT"],
                          "false_alarm": r["VERDICT"] == "ALARM",
                          "layers": {"L1": r["L1"]["ok"], "L2": r["L2"]["ok"],
                                     "L3": r["L3"]["ok"]}})
    n_caught = sum(1 for r in wrong_rows if r["alarmed"])
    n_false = sum(1 for r in good_rows if r["false_alarm"])
    return {
        "baseline_VERDICT": baseline["VERDICT"],
        "wrong_injections": wrong_rows,
        "n_wrong": len(wrong_rows), "n_wrong_caught": n_caught,
        "good_variations": good_rows,
        "n_good": len(good_rows), "n_false_alarms": n_false,
        "CHECKER_VALID": (n_caught == len(wrong_rows) and n_false == 0),
        "note": "If n_wrong_caught < n_wrong, the checker CANNOT alarm on a wrong "
                "conclusion and is therefore decorative. Good variations must not "
                "alarm (otherwise the checker cries wolf).",
    }


# ===========================================================================
# CONCRETE INSTANTIATION for the R9 -> R9S case (read-only inputs)
# ===========================================================================

ADVERSARIAL = [
    ("CF1", "需谁批准", "## 5 改动清单\n批准人待定，需谁批准尚需确认，顺序不可倒。\n"),
    ("CF2", "实跑输出", "## 3 可达性\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 结论详见后续附件。\n"),
    ("CF3", "改前改后", "## 4 订正草案（改前/改后逐处对照）\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n"),
    ("CF4", "脚本存在性", "## 3 搜索\n脚本存在性待查，本件不另下结论。\n"),
    ("CF5", "可重建", "## 4 重建可行性\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n五项口径表见上节。\n"),
    ("WCF1", "需谁批准", "## 5 改动清单\n本次改动的批准人尚未确定，由谁批准仍需后续确认。\n"),
    ("WCF2", "实跑输出", "## 3 可达性\n16/16 格已实跑完成，返回值详见附件，正文未列出。\n"),
    ("WCF3", "改前改后", "## 4 订正草案\n【改前】详见台账登记。\n【改后】见台账登记，本件不重录。\n逐处对照表另附。\n"),
    ("WCF4", "脚本存在性", "## 3 判定\n该脚本是否在盘，以台账记载为准，本件不另下结论。\n"),
    ("WCF5", "可重建", "## 4 重建可行性\n是否【可唯一重建】尚需核对，本件暂不作判定。\n五项口径表见上节。\n"),
    ("V2", "需谁批准", "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n"),
    ("V3", "改前改后", "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A（最小改动·推荐）\n- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n- 【要点】只换「一一对应」→「逐项对应」并插入拆分括注。\n"),
    ("V6", "可重建", "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n**判定：正确算法并非【可唯一重建】。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
]

SPEC_ROLES = {k: list(v["roles"]) for k, v in R9S.SPECS.items()}

# Independent truth certificates: anchored by file:line, role-by-role, with an
# oracle label. These are HYPOTHETICAL inputs supplied from outside the R9S
# author -- they demonstrate the SHAPE of the required evidence. They are
# deliberately constructed here by THIS session from the read-only artifacts
# so the demonstration is executable, and are explicitly flagged as such.
CERTS = {
 ("lead/matrix_ab_ruling_20261109/", "需谁批准"): {
   "anchor": "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md:108",
   "quote": "批准人一律 = 乙设计责任人",
   "roles": {"批准人角色头": "批准人", "赋值算子": "一律 =",
             "具体施事值": "乙设计责任人"},
   "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
   "predicate_author": "author_of_V1", "oracle_sealed": True},
 ("lead/matrix_reach_20261109/", "实跑输出"): {
   "anchor": "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md:65",
   "quote": "verdict='post_read_error' conf='none' is_new=None pre_state='unknown'",
   "roles": {"实跑事件": "classify 直调 16/16 格实跑",
             "输出载荷(带具体值的 key=value 数据行)": "verdict='post_read_error' conf='none'"},
   "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
   "predicate_author": "author_of_V1", "oracle_sealed": True},
 ("lead/n11_wording_fix_20261108/", "改前改后"): {
   "anchor": "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md:76",
   "quote": "【改前】本件按 13 项分写…【改后】改后句逐处对照",
   "roles": {"改前标签+实值": "【改前】本件按 13 项分写",
             "改后标签+实值": "【改后】逐项对应并插入拆分括注",
             "对照算子": "逐处对照"},
   "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
   "predicate_author": "author_of_V1", "oracle_sealed": True},
 ("lead/s604_script_gap_20261109/", "脚本存在性"): {
   "anchor": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:44",
   "quote": "生成脚本【不存在且从未落盘】",
   "roles": {"脚本对象": "生成脚本", "存在性谓词": "不存在且从未落盘",
             "判定算子": "结论：", "已决断极性": "【不存在且从未落盘】"},
   "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
   "predicate_author": "author_of_V1", "oracle_sealed": True},
 ("lead/s604_script_gap_20261109/", "可重建"): {
   "anchor": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:77",
   "quote": "【可唯一重建】…四重独立实现逐位一致",
   "roles": {"重建动作": "可唯一重建", "肯定情态": "可（肯定情态头）",
             "确定性证据": "四重独立实现逐位一致"},
   "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
   "predicate_author": "author_of_V1", "oracle_sealed": True},
}


def main():
    ref = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
    flips = [{"domain": f["domain"], "token": f["token"]}
             for f in ref["domains32"]["flips"]]
    items = []
    for r in ref["domains32"]["rows"]:
        if r.get("main_missing"):
            continue
        for e in r["per_element"]:
            items.append({"domain": r["domain"], "token": e["token"]})
    wl = [tuple(x) for x in ref["domains32"]["whitelist"]]

    base = dict(items=items, flips=flips, whitelist=wl,
                registered_tokens=set(R9S.SPECS.keys()),
                spec_keys=set(R9S.SPECS.keys()),
                certificates=CERTS, spec_roles=SPEC_ROLES,
                predicate=R9S.r9s_element_present,
                adversarial_corpus=ADVERSARIAL,
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)

    # ---- (1) run the new checker on the real (unmodified) state -------------
    real = no_relaxation_check(**base)
    # ---- (2) run old-style check for comparison ----------------------------
    old = {"no_relaxation": ref["no_relaxation"], "VERDICT": ref["verdict"],
           "formula": "_r9s_regress.py:204-206 + :223-229"}

    # ---- (3) META-TEST: inject known errors --------------------------------
    def cp(kw):
        return dict(kw)

    def w_all5_empty(kw):
        """ALL FIVE conclusions wrong: every certificate value -> pointer."""
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        for c in certs.values():
            for k in c["roles"]:
                c["roles"][k] = "见台账登记，本件不另下结论"
            c["oracle_truth"] = False
        d["certificates"] = certs
        return d

    def w_3of5_empty(kw):
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        for key in list(certs)[:3]:
            for k in certs[key]["roles"]:
                certs[key]["roles"][k] = "详见台账"
            certs[key]["oracle_truth"] = False
        d["certificates"] = certs
        return d

    def w_1_oracle_false(kw):
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        k0 = list(certs)[0]
        certs[k0]["oracle_truth"] = False
        d["certificates"] = certs
        return d

    def w_drop_cert(kw):
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        del certs[list(certs)[0]]
        d["certificates"] = certs
        return d

    def w_oracle_same_author(kw):
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        for c in certs.values():
            c["oracle_author"] = "author_of_V1"
        d["certificates"] = certs
        return d

    def w_unsealed_whitelist(kw):
        d = cp(kw); d["whitelist_sealed"] = False; return d

    def w_extra_true_flip(kw):
        d = cp(kw)
        d["flips"] = kw["flips"] + [{"domain": "lead/handoff_pack_20261109/",
                                     "token": "需谁批准"}]
        return d

    def w_adversarial_leak(kw):
        """Simulate a V1 that accepts a form-like-but-empty payload."""
        d = cp(kw)
        real_pred = kw["predicate"]
        def leaky(text, token):
            if "待判" in text or "不另下结论" in text:
                return (True, "semantic", {})
            return real_pred(text, token)
        d["predicate"] = leaky
        return d

    def g_reworded_quote(kw):
        """GOOD variation: a legitimate paraphrase of a certificate value."""
        d = cp(kw)
        certs = copy.deepcopy(kw["certificates"])
        k0 = list(certs)[0]
        certs[k0]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节）"
        d["certificates"] = certs
        return d

    def g_extra_adversarial_caught(kw):
        """GOOD variation: adding one more adversarial case that IS caught."""
        d = cp(kw)
        d["adversarial_corpus"] = list(kw["adversarial_corpus"]) + [
            ("EXTRA", "可重建", "## 4 结论\n不可重建：证据待补。\n")]
        return d

    # A known-good SYNTHETIC world for the meta-test. The real R9S state is
    # NOT a good world (it has real defects), so using it as baseline would
    # make every "good variation" inherit the ALARM. We build a clean world
    # with: a sealed whitelist whose token set is NOT the spec keys, an
    # independent sealed oracle on every flip, and a repaired predicate that
    # rejects all form-like-but-empty payloads used in the adversarial corpus.
    def repaired_predicate(text, token):
        """V1_repaired: current R9S + a pending/undecided guard on the whole
        clause containing the modal/label. Demonstration only; NOT a change
        to any on-disk predicate."""
        ok, layer, detail = R9S.r9s_element_present(text, token)
        if not ok:
            return (False, layer, detail)
        bad = re.search(r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
                        r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
                        r"输出数据待补|返回值详见附件", text)
        if bad:
            return (False, "", {"rejected_by": "pending/pointer guard"})
        return (ok, layer, detail)

    good_base = dict(base)
    good_base["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    good_base["predicate"] = repaired_predicate
    good_base["adversarial_corpus"] = list(ADVERSARIAL)

    wrongs = [
        ("all_5_conclusions_wrong__semantic_empty", w_all5_empty),
        ("3_of_5_semantically_empty", w_3of5_empty),
        ("1_oracle_says_absent", w_1_oracle_false),
        ("1_certificate_missing", w_drop_cert),
        ("oracle_author_not_independent", w_oracle_same_author),
        ("whitelist_not_sealed", w_unsealed_whitelist),
        ("6th_flip_outside_whitelist", w_extra_true_flip),
        ("V1_accepts_undecided_payload", w_adversarial_leak),
        ("whitelist_becomes_self_certified", lambda kw: {**cp(kw),
            "spec_keys": set(kw["registered_tokens"])}),
    ]
    goods = [("reworded_quote_still_true", g_reworded_quote),
             ("extra_adversarial_case_caught", g_extra_adversarial_caught)]

    meta = meta_test(good_base, wrongs, goods)
    # Explicit proof that the baseline of the meta-test is itself PASS.
    meta["synthetic_baseline_VERDICT"] = no_relaxation_check(**good_base)["VERDICT"]
    meta["synthetic_predicate_adversarial_catch"] = sum(
        1 for cid, tok, txt in ADVERSARIAL if not repaired_predicate(txt, tok)[0])
    meta["synthetic_predicate_adversarial_total"] = len(ADVERSARIAL)

    # ---- (4) also: does the OLD check alarm on all-5-wrong? ---------------
    # (old check has no certificate/oracle inputs; answer comes from replay)
    replay = json.loads((WDIR / "_fnr_replay_out.json").read_text(encoding="utf-8"))
    k5 = next(s for s in replay["scenarios"] if s["scenario"] == "k5_empty")
    old_on_all_wrong = {"no_relaxation": k5["no_relaxation"], "VERDICT": k5["verdict"]}

    out = {"old_check_on_real_state": old,
           "new_check_on_real_state": real,
           "old_check_on_ALL_5_WRONG": old_on_all_wrong,
           "new_check_meta_test": meta,
           "adversarial_baseline": {
               "n": len(ADVERSARIAL),
               "caught_by_CURRENT_R9S": sum(
                   1 for cid, tok, txt in ADVERSARIAL
                   if not R9S.r9s_element_present(txt, tok)[0]),
               "note": "R9S itself FAILS this adversarial corpus; the checker "
                       "reports the leak instead of hiding it."}}

    print(json.dumps({
        "old_check_on_real_state": old,
        "new_check_on_real_state": {
            "VERDICT": real["VERDICT"],
            "L1_ok": real["L1"]["ok"], "L1_problems": real["L1"]["problems"],
            "L1_detail": real["L1"]["detail"],
            "L2_ok": real["L2"]["ok"], "L2_problem_count": len(real["L2"]["problems"]),
            "L3_ok": real["L3"]["ok"], "L3_problem_count": len(real["L3"]["problems"]),
            "L3_adversarial": "%d/%d caught" % (
                real["L3"]["detail"]["n_adversarial_caught"],
                real["L3"]["detail"]["n_adversarial"]),
            "L3_mutation_alarms": "%d/%d" % (
                real["L3"]["detail"]["n_mutation_alarms"],
                real["L3"]["detail"]["n_mutations"]),
        },
        "old_check_on_ALL_5_WRONG": old_on_all_wrong,
        "meta_test": meta,
    }, ensure_ascii=False, indent=1))
    (WDIR / "_fnr_check_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\nWROTE _fnr_check_out.json")


if __name__ == "__main__":
    main()
