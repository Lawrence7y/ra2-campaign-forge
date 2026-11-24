# -*- coding: utf-8 -*-
r"""_cfav_probe.py -- INDEPENDENT verification of the FP-audit reply.

SOLE WRITE DOMAIN: lead/check_fp_audit_20261109/  (files prefixed _cfav_)
All read-only inputs are opened read-only.  _fnr_check.py is loaded as a MODULE
with sys.dont_write_bytecode=True so NO .pyc is written into a read-only dir;
main() is NEVER called (it would write back into a read-only dir at :548-549).
Zero real-machine, zero sampling code.  Run:
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfav_probe.py
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True          # never write bytecode into read-only dirs

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "check_fp_audit_20261109"

# ---------------------------------------------------------------------------
# 0. Fingerprints of the 8 orchestrator-listed artifacts + 3 more read-only
#    inputs the FP-audit reply says it touched.  Recomputed with hashlib.
# ---------------------------------------------------------------------------
BASELINE_8 = {
 "lead/falsifiable_no_relax_20261109/_fnr_check.py": ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
 "lead/falsifiable_no_relax_20261109/_fnr_check_out.json": ("f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e", 8733),
 "lead/falsifiable_no_relax_20261109/_fnr_REPORT.md": ("80641e7dcc0cc3ebc61c2c39afe6757814fc6eb694a9559c4903ab9241ee6f06", 43390),
 "lead/falsifiable_no_relax_20261109/_fnr_replay_out.json": ("877f4ced0ab99562f776faa82015f742588c76fa9a63ee23b735f2fed61bd9fd", 27535),
 "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md": ("f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc", 52705),
 "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
EXTRA_3 = [
 "lead/falsifiable_no_relax_20261109/_fnrd_verify_out.json",
 "lead/gate_r9sem_20261109/_r9s_predicates.py",
 "lead/gate_r9sem_20261109/_r9s_regress.py",
]


def sha_of(rel):
    b = (ROOT / rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def fingerprint_table():
    out = {}
    for rel, (eh, en) in BASELINE_8.items():
        h, n = sha_of(rel)
        out[rel] = {"sha256": h, "bytes": n,
                    "matches_orchestrator_baseline": (h == eh and n == en)}
    for rel in EXTRA_3:
        h, n = sha_of(rel)
        out[rel] = {"sha256": h, "bytes": n, "matches_orchestrator_baseline": None}
    return out


# ---------------------------------------------------------------------------
# 1. Load the object under test (module only, main() NOT executed)
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location("cfav_fnr_check", FNR / "_fnr_check.py")
fnr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fnr)
R9S = fnr.R9S
CERTS = fnr.CERTS
ADVERSARIAL = fnr.ADVERSARIAL
SPEC_ROLES = fnr.SPEC_ROLES

REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))


def my_base():
    """Independent reconstruction of the real-world kwargs (no copy of _cfa_probe)."""
    dom = REF["domains32"]
    f = [{"domain": x["domain"], "token": x["token"]} for x in dom["flips"]]
    it = [{"domain": row["domain"], "token": el["token"]}
          for row in dom["rows"] if not row.get("main_missing")
          for el in row["per_element"]]
    w = [tuple(x) for x in dom["whitelist"]]
    return dict(items=it, flips=f, whitelist=w,
                registered_tokens=set(R9S.SPECS.keys()),
                spec_keys=set(R9S.SPECS.keys()),
                certificates=copy.deepcopy(CERTS), spec_roles=SPEC_ROLES,
                predicate=R9S.r9s_element_present,
                adversarial_corpus=list(ADVERSARIAL),
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)


# An INDEPENDENT guard, authored here with a broader lexicon than _fnr_check.py:478-480.
MY_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|见台账|详见台账|详见附件|"
    r"并非【|是否【|不可重建|输出数据待补|返回值详见附件|"
    r"以.{0,10}为准|见上|见下表|见另册|另附|另见|证据待补|未列出|待确认|未定|"
    r"具体施事姓名以|以密封附件为准|归档编号|归档索引|见方案|对应行|见下表"
)


def my_robust_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if MY_GUARD.search(text):
        return (False, "", {"rejected_by": "cfav independent guard"})
    return (ok, layer, detail)


def seal(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def third_party_certs(world_certs):
    """Attach REAL sha256 seals as side-data (the checker has no slot for them)."""
    c = copy.deepcopy(world_certs)
    for k, v in c.items():
        v["oracle_author"] = "independent_blind_adjudicator"
        v["predicate_author"] = "author_of_V1"
        v["oracle_truth"] = True
        v["oracle_sealed"] = True
    return c


SIDE = {}


def verdict(kw):
    r = fnr.no_relaxation_check(**kw)
    return {"VERDICT": r["VERDICT"],
            "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
            "L1_problems": list(r["L1"]["problems"]),
            "L1_coverage": r["L1"]["detail"]["coverage_ratio"],
            "L1_self_certified": r["L1"]["detail"]["self_certified"],
            "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "L3_total": r["L3"]["detail"]["n_adversarial"]}


# ---------------------------------------------------------------------------
# 2. MY OWN 8 benign worlds (constructed here, not copied from the reply) +
#    3 harder ones.  "benign" = every conclusion semantically delivered,
#    sealed independent whitelist, independent ORACLE, all adversarial caught.
# ---------------------------------------------------------------------------
def good_skeleton(predicate=None, with_sixth=False):
    """Baseline known-good skeleton.  with_sixth adds a genuine 6th registered
    element (no flip) so the whitelist token set differs from spec_keys --
    the ONLY spec-consistent way to avoid SELF_CERTIFIED without a fake key."""
    g = my_base()
    g["predicate"] = predicate or my_robust_predicate
    if with_sixth:
        g["spec_keys"] = set(R9S.SPECS.keys()) | {"交付清单"}
        g["registered_tokens"] = set(R9S.SPECS.keys()) | {"交付清单"}
    else:
        g["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    g["certificates"] = third_party_certs(CERTS)
    return g


def b1_ideal_per_checker_spec():
    """Known-good world that satisfies the checker's OWN condition (E)
    (whitelist tokens != spec keys) with a genuine 6th registered element."""
    return good_skeleton(with_sixth=True)


def b2_independent_sealed_whitelist_same_source():
    """Compliant same-source: whitelist independently authored + REAL sha256 seal,
    but its 5 token keys are forced by the task book -> equal to SPECS keys."""
    g = good_skeleton(with_sixth=False)
    g["spec_keys"] = set(R9S.SPECS.keys())          # no padding: compliant design
    g["whitelist_author"] = "independent"
    g["whitelist_sealed"] = True
    SIDE["B2"] = {"whitelist_seal_sha256": seal([list(x) for x in g["whitelist"]]),
                  "note": "real hashlib seal; checker has no parameter to read it"}
    return g


def b3_full_coverage():
    g = good_skeleton()
    g["registered_tokens"] = {i["token"] for i in g["items"]}
    return g


def b4_third_party_oracle_real_seal():
    g = good_skeleton()
    SIDE["B4"] = {"oracle_seals": {str(k): seal({"k": list(k), "truth": True})
                                   for k in g["certificates"]}}
    return g


def b5_all_adversarial_caught_plus_extra():
    g = good_skeleton()
    extra = [("X1", "需谁批准", "## 5 清单\n批准人待判，本件不另下结论。\n"),
             ("X2", "改前改后", "## 4 草案\n【改前】详见台账。\n【改后】本件不重录。\n"),
             ("X3", "可重建", "## 4 结论\n是否【可唯一重建】尚需核对。\n")]
    g["adversarial_corpus"] = list(ADVERSARIAL) + extra
    return g


def b6_extra_true_flip():
    g = good_skeleton()
    pair = ("lead/handoff_pack_20261109/", "需谁批准")
    g["flips"] = list(g["flips"]) + [{"domain": pair[0], "token": pair[1]}]
    g["whitelist"] = list(g["whitelist"]) + [pair]
    c = copy.deepcopy(g["certificates"])
    c[pair] = {"anchor": "lead/handoff_pack_20261109/HANDOFF_PACK.md:12",
               "quote": "批准人一律 = 乙设计责任人，逐项对应",
               "roles": {"批准人角色头": "批准人", "赋值算子": "一律 =",
                         "具体施事值": "乙设计责任人"},
               "oracle_truth": True, "oracle_author": "independent_blind_adjudicator",
               "predicate_author": "author_of_V1", "oracle_sealed": True}
    g["certificates"] = c
    return g


def b7_benign_reword():
    g = good_skeleton()
    c = copy.deepcopy(g["certificates"])
    k0 = list(c)[0]
    c[k0]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节的正式裁决）"
    g["certificates"] = c
    return g


def b8_drop_one_pair():
    g = good_skeleton()
    t = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    g["flips"] = [x for x in g["flips"] if (x["domain"], x["token"]) != t]
    g["whitelist"] = [x for x in g["whitelist"] if tuple(x) != t]
    c = copy.deepcopy(g["certificates"])
    c.pop(t, None)
    g["certificates"] = c
    return g


# ---- 3 HARDER tests -------------------------------------------------------
def h1_real_state_with_l3_defects_fixed_no_padding():
    """Repair the ONLY real defect (predicate leaks on 13 adversarial) but keep
    everything else at the real, compliant, same-source state. No dummy key."""
    g = my_base()
    g["predicate"] = my_robust_predicate
    g["certificates"] = third_party_certs(CERTS)
    return g


def h2_maximal_compliance_same_source():
    """Every independence attribute present + real seals + full coverage +
    robust predicate + all adversarial caught; only same-source remains."""
    g = h1_real_state_with_l3_defects_fixed_no_padding()
    g["registered_tokens"] = {i["token"] for i in g["items"]}
    g["whitelist_author"] = "independent"
    g["whitelist_sealed"] = True
    SIDE["H2"] = {"whitelist_seal_sha256": seal([list(x) for x in g["whitelist"]]),
                  "oracle_seals": {str(k): seal({"k": list(k), "truth": True})
                                   for k in g["certificates"]},
                  "note": "all real seals computed; checker cannot read any of them"}
    return g


def h3_known_wrong_but_unexposable():
    """A world that is semantically WRONG in the strongest sense expressible
    in the checker's 13-param contract: every certificate forged (fake anchor,
    fabricated quote), yet all flags self-declared benign and padded to PASS."""
    g = good_skeleton()
    fake = copy.deepcopy(g["certificates"])
    for i, (k, c) in enumerate(fake.items()):
        c["anchor"] = "cfav/NO_SUCH_FILE_%d.md:999999" % i
        c["quote"] = "此引文在本复核中凭空编造，未见于任何交付件。"
        c["oracle_author"] = "independent_blind_adjudicator"
        c["predicate_author"] = "author_of_V1"
        c["oracle_truth"] = True
        c["oracle_sealed"] = True
    g["certificates"] = fake
    SIDE["H3"] = {"all_five_anchors_point_to_nonexistent_files": True,
                  "all_five_quotes_fabricated": True}
    return g


BENIGN_8 = [
 ("B1", "理想世界:满足检验自身(E)条件(第6个真实注册要素)", b1_ideal_per_checker_spec),
 ("B2", "合规同源:第三方封印独立白名单,token集=SPECS键", b2_independent_sealed_whitelist_same_source),
 ("B3", "全覆盖:registered_tokens=全部item token", b3_full_coverage),
 ("B4", "第三方ORACLE真值表(真sha256封印)", b4_third_party_oracle_real_seal),
 ("B5", "对抗样本全抓(13+3=16)", b5_all_adversarial_caught_plus_extra),
 ("B6", "追加1条真语义等价翻案", b6_extra_true_flip),
 ("B7", "良性引文改写", b7_benign_reword),
 ("B8", "删1对白名单并同步删flip/证书", b8_drop_one_pair),
]
HARD_3 = [
 ("H1", "现盘真缺陷全修好且不加padding", h1_real_state_with_l3_defects_fixed_no_padding),
 ("H2", "最大合规(真封印+全覆盖+独立ORACLE)仅余同源", h2_maximal_compliance_same_source),
 ("H3", "已知错:5份证书全伪造锚点/引文(检验端不可见)", h3_known_wrong_but_unexposable),
]


def run_worlds():
    rows = []
    for sid, name, fn in BENIGN_8 + HARD_3:
        w = fn()
        r = verdict(w)
        r.update({"id": sid, "name": name, "kind": "benign" if sid.startswith("B") else "hard",
                  "false_alarm": (r["VERDICT"] == "ALARM") if sid.startswith("B") else None})
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# 3. Independent checks of the reply's other claims
# ---------------------------------------------------------------------------
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]


def l1_recompute():
    b = my_base()
    reg = set(R9S.SPECS.keys())
    untested = [i for i in b["items"] if i["token"] not in reg]
    wl_tokens = {k for _, k in b["whitelist"]}
    cnt = Counter(i["token"] for i in b["items"] if i["token"] in reg)
    return {"rows": len(REF["domains32"]["rows"]), "n_items": len(b["items"]),
            "n_flips": len(b["flips"]), "n_whitelist": len(b["whitelist"]),
            "n_spec_keys": len(R9S.SPECS),
            "tested_token_counts": dict(cnt),
            "n_tested": len(b["items"]) - len(untested),
            "n_structurally_untested": len(untested),
            "coverage_ratio": round((len(b["items"]) - len(untested)) / len(b["items"]), 4),
            "wl_tokens": sorted(wl_tokens), "spec_keys": sorted(reg),
            "wl_tokens_eq_spec_keys": wl_tokens == reg,
            "multiset_same_as_set_here": dict(Counter(k for _, k in b["whitelist"])) ==
                                         {k: 1 for k in reg}}


def ast_io_audit():
    """Static proof: does ANY checker function resolve anchors / verify seals /
    read artifact text?  Also confirm main() writes to the read-only dir."""
    src = (FNR / "_fnr_check.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    res = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = []
        for c in ast.walk(node):
            if isinstance(c, ast.Call):
                f = c.func
                if isinstance(f, ast.Name):
                    calls.append(f.id)
                elif isinstance(f, ast.Attribute):
                    calls.append(f.attr)
        res[node.name] = {"lineno": node.lineno,
                          "calls": sorted(set(calls)),
                          "opens_file": any(x in ("open", "read_text", "read_bytes") for x in calls),
                          "computes_hash": any(x in ("sha256", "hexdigest") for x in calls),
                          "writes_file": any(x in ("write_text", "write_bytes") for x in calls)}
    return res


def p_signatures():
    return {"no_relaxation_check_params": list(inspect.signature(fnr.no_relaxation_check).parameters),
            "check_l1_params": list(inspect.signature(fnr.check_l1).parameters),
            "certificate_ok_params": list(inspect.signature(fnr.certificate_ok).parameters)}


def p_meta_empty_on_alarm_baseline():
    m = fnr.meta_test(my_base(), [], [])
    return {"baseline_VERDICT": m["baseline_VERDICT"], "n_wrong": m["n_wrong"],
            "n_good": m["n_good"], "CHECKER_VALID": m["CHECKER_VALID"]}


def p_meta_wrong_baseline():
    def g1(kw):
        d = dict(kw); c = copy.deepcopy(kw["certificates"])
        c[list(c)[0]]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节）"
        d["certificates"] = c; return d
    def g2(kw):
        d = dict(kw)
        d["adversarial_corpus"] = list(kw["adversarial_corpus"]) + [
            ("EXTRA", "可重建", "## 4 结论\n不可重建：证据待补。\n")]
        return d
    m = fnr.meta_test(my_base(), [], [("reworded_quote_still_true", g1),
                                      ("extra_adversarial_case_caught", g2)])
    return {"baseline_VERDICT": m["baseline_VERDICT"],
            "n_false_alarms": m["n_false_alarms"], "CHECKER_VALID": m["CHECKER_VALID"]}


def p_power_bounds():
    return {"sensitivity_lower_9of9": round(0.05 ** (1.0 / 9), 6),
            "fp_upper_0of2": round(1 - 0.05 ** (1.0 / 2), 6)}


def p_padding():
    a = good_skeleton()
    b = good_skeleton()
    b["spec_keys"] = set(R9S.SPECS.keys())
    return {"with_dummy_extra_key": verdict(a), "without_dummy_extra_key": verdict(b),
            "dummy_key": "额外预留要素"}


def p_coverage_zero():
    g = good_skeleton()
    g["registered_tokens"] = set()
    r = verdict(g)
    r["check_l1_problems"] = fnr.check_l1(g["items"], g["flips"], g["whitelist"],
                                          g["registered_tokens"], g["spec_keys"],
                                          True, "independent")[1]
    return r


def p_real_leaks():
    rows = [{"id": cid, "token": tok,
             "present": bool(R9S.r9s_element_present(txt, tok)[0]),
             "my_guard_present": bool(my_robust_predicate(txt, tok)[0])}
            for cid, tok, txt in ADVERSARIAL]
    return {"n": len(rows), "leaked_by_real_R9S": [r["id"] for r in rows if r["present"]],
            "leaked_by_MY_guard": [r["id"] for r in rows if r["my_guard_present"]],
            "rows": rows}


def p_guard_fit_and_novel():
    author_guard_words = ["待判", "待定", "尚需", "尚未", "不另下结论", "暂不作判定",
                          "本件不重录", "见台账", "详见台账", "详见附件", "并非【",
                          "是否【", "不可重建", "输出数据待补", "返回值详见附件"]
    fit = [{"id": cid, "n_hits": sum(1 for w in author_guard_words if w in txt)}
           for cid, tok, txt in ADVERSARIAL]
    novel = [
        ("N-EMPTY-1", "需谁批准", "## 5 改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准。\n"),
        ("N-EMPTY-2", "改前改后", "## 4 订正草案\n【改前】旧句共 13 项分写。\n【改后】新句见另册对应行。\n逐处对照表另附。\n"),
        ("N-EMPTY-3", "可重建", "## 4 重建可行性\n判定：正确算法【可唯一重建】。原始采样记录见归档索引。\n"),
    ]
    nrows = [{"id": cid, "author_guard_hit": any(w in txt for w in author_guard_words),
              "my_guard_hit": bool(MY_GUARD.search(txt)),
              "real_r9s_present": bool(R9S.r9s_element_present(txt, tok)[0]),
              "my_robust_present": bool(my_robust_predicate(txt, tok)[0])}
             for cid, tok, txt in novel]
    g = good_skeleton()
    g["adversarial_corpus"] = list(ADVERSARIAL) + novel
    r = verdict(g)
    return {"n_corpus_with_author_guard_word": sum(1 for x in fit if x["n_hits"] > 0),
            "n_corpus_total": len(fit), "fit": fit,
            "novel": nrows,
            "good_world_plus_novel_VERDICT": r["VERDICT"],
            "good_world_plus_novel_caught": r["L3_caught"],
            "good_world_plus_novel_total": r["L3_total"]}


def p_forged_certs():
    g = h3_known_wrong_but_unexposable()
    r = verdict(g)
    r["anchor_files_exist"] = [(ROOT / c["anchor"].split(":")[0]).exists()
                               for c in g["certificates"].values()]
    return r


def p_per_layer_recall():
    d = json.loads((FNR / "_fnr_check_out.json").read_text(encoding="utf-8"))
    rows = d["new_check_meta_test"]["wrong_injections"]
    counts = {L: sum(1 for r in rows if not r["layers"][L]) for L in ("L1", "L2", "L3")}
    return {"n_wrong": len(rows), "per_layer_alarm_counts": counts}


def p_adversarial_provenance():
    """Are the 13 adversarial payloads authored in the same file as the guard?"""
    up = (ROOT / "lead/whitelist_audit_20261109/WHITELIST_AUDIT.md").read_text(encoding="utf-8")
    return {"ADVERSARIAL_defined_in_fnr_check_lines": "291-305",
            "author_guard_defined_in_fnr_check_lines": "471-483",
            "upstream_whitelist_audit_quotes_CF3": "CF3 改前改后并列但无对照" in up,
            "upstream_whitelist_audit_quotes_WCF5": "WCF5 = " in up,
            "note": "corpus text predates _fnr_check.py in upstream audit files; "
                    "the 13 payloads are NOT all authored in _fnr_check.py"}


def main():
    fps_start = fingerprint_table()
    out = {}
    out["step1_fingerprints"] = fps_start
    out["step1_all_eight_match"] = all(v["matches_orchestrator_baseline"]
                                       for k, v in fps_start.items()
                                       if v["matches_orchestrator_baseline"] is not None)
    out["step2_ast_io_audit"] = ast_io_audit()
    out["step2_signatures"] = p_signatures()
    out["step2_l1_recompute"] = l1_recompute()
    out["step3_worlds"] = run_worlds()
    out["step3_side_data"] = SIDE
    b = [r for r in out["step3_worlds"] if r["kind"] == "benign"]
    n_fp = sum(1 for r in b if r["false_alarm"])
    out["step3_fp_my8"] = {"n": len(b), "n_false_alarms": n_fp,
                           "rate": round(n_fp / len(b), 6),
                           "wilson95": wilson(n_fp, len(b)),
                           "false_alarm_ids": [r["id"] for r in b if r["false_alarm"]]}
    # spec-consistent subset: worlds that satisfy the checker's own condition (E)
    spec_ok = [r for r in b if r["id"] != "B2"]
    out["step3_fp_spec_consistent_7"] = {
        "n": len(spec_ok), "n_false_alarms": sum(1 for r in spec_ok if r["false_alarm"]),
        "wilson95": wilson(sum(1 for r in spec_ok if r["false_alarm"]), len(spec_ok))}
    out["step4_padding"] = p_padding()
    out["step4_coverage_zero"] = p_coverage_zero()
    out["step4_meta_empty_on_ALARM"] = p_meta_empty_on_alarm_baseline()
    out["step4_meta_wrong_baseline"] = p_meta_wrong_baseline()
    out["step4_power_bounds"] = p_power_bounds()
    out["step4_forged_certs"] = p_forged_certs()
    out["step4_guard_fit_and_novel"] = p_guard_fit_and_novel()
    out["step4_real_leaks"] = p_real_leaks()
    out["step4_per_layer_recall"] = p_per_layer_recall()
    out["step4_adversarial_provenance"] = p_adversarial_provenance()
    out["step5_reply_wilson_check"] = {"wilson95_4_of_8": wilson(4, 8),
                                       "wilson95_4_of_10": wilson(4, 10),
                                       "wilson95_3_of_9": wilson(3, 9)}
    fps_end = fingerprint_table()
    out["step6_readonly_unchanged_during_my_run"] = all(
        fps_start[k]["sha256"] == fps_end[k]["sha256"] and
        fps_start[k]["bytes"] == fps_end[k]["bytes"] for k in fps_start)

    (WDIR / "_cfav_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("=== STEP 1: 8 ORCHESTRATOR FINGERPRINTS (hashlib, independent) ===")
    for k, v in fps_start.items():
        print("  %-72s %s bytes=%d match=%s" %
              (k.split("/")[-1], v["sha256"], v["bytes"], v["matches_orchestrator_baseline"]))
    print("  ALL_EIGHT_MATCH =", out["step1_all_eight_match"])
    print("\n=== STEP 2: AST I/O AUDIT (which functions can read files / verify seals) ===")
    for name, v in out["step2_ast_io_audit"].items():
        print("  %-26s line=%-4d opens_file=%-5s computes_hash=%-5s writes_file=%s" %
              (name, v["lineno"], v["opens_file"], v["computes_hash"], v["writes_file"]))
    print("\n=== STEP 2: SIGNATURES ===")
    print(json.dumps(out["step2_signatures"], ensure_ascii=False))
    print("\n=== STEP 2: L1 RECOMPUTE ===")
    print(json.dumps(out["step2_l1_recompute"], ensure_ascii=False))
    print("\n=== STEP 3: MY OWN 8 BENIGN + 3 HARDER WORLDS ===")
    for r in out["step3_worlds"]:
        print("  %-3s %-52s VERDICT=%-5s L1=%-5s L2=%-5s L3=%-5s L1prob=%s" %
              (r["id"], r["name"][:52], r["VERDICT"], r["L1_ok"], r["L2_ok"],
               r["L3_ok"], r["L1_problems"]))
    print("  FP (my 8 benign)      :", json.dumps(out["step3_fp_my8"], ensure_ascii=False))
    print("  FP (spec-consistent 7):", json.dumps(out["step3_fp_spec_consistent_7"], ensure_ascii=False))
    print("  Reply's Wilson check  :", json.dumps(out["step5_reply_wilson_check"], ensure_ascii=False))
    print("\n=== STEP 4: PADDING / COVERAGE / META / FORGERY / GUARD / LEAKS ===")
    print("P9  padding      :", json.dumps(out["step4_padding"], ensure_ascii=False))
    print("P11 coverage 0.0 :", json.dumps(out["step4_coverage_zero"], ensure_ascii=False))
    print("P3  meta empty   :", json.dumps(out["step4_meta_empty_on_ALARM"], ensure_ascii=False))
    print("P4  wrong baseln :", json.dumps(out["step4_meta_wrong_baseline"], ensure_ascii=False))
    print("P7  power bounds :", json.dumps(out["step4_power_bounds"], ensure_ascii=False))
    print("P1  forged certs :", json.dumps(out["step4_forged_certs"], ensure_ascii=False))
    g = out["step4_guard_fit_and_novel"]
    print("P2  guard fit    : %d/%d corpus items contain >=1 author guard word" %
          (g["n_corpus_with_author_guard_word"], g["n_corpus_total"]))
    print("P2  novel        :", json.dumps(g["novel"], ensure_ascii=False))
    print("P2  good+novel   : %s caught=%d/%d" %
          (g["good_world_plus_novel_VERDICT"], g["good_world_plus_novel_caught"],
           g["good_world_plus_novel_total"]))
    print("P6  real leaks   :", json.dumps({k: v for k, v in out["step4_real_leaks"].items()
                                            if k != "rows"}, ensure_ascii=False))
    print("P10 per-layer    :", json.dumps(out["step4_per_layer_recall"], ensure_ascii=False))
    print("    provenance   :", json.dumps(out["step4_adversarial_provenance"], ensure_ascii=False))
    print("\n=== STEP 6: READ-ONLY INPUTS UNCHANGED DURING MY RUN ===")
    print("  ALL_UNCHANGED =", out["step6_readonly_unchanged_during_my_run"])
    print("\nWROTE _cfav_out.json")


if __name__ == "__main__":
    main()
