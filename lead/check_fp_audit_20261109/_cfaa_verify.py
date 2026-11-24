# -*- coding: utf-8 -*-
r"""_cfaa_verify.py -- consolidation run for CHECK_FALSE_ALARM_AUDIT.md.

SOLE WRITE DOMAIN: lead/check_fp_audit_20261109/  (only NEW files, prefix _cfaa_)
Read-only inputs are opened read-only.  _fnr_check.py is loaded as a MODULE with
sys.dont_write_bytecode=True; main() is NEVER called (it writes back into the
read-only dir at :548-549).  Zero real-machine, zero sampling code.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfaa_verify.py
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import ast
import copy
import hashlib
import importlib.util
import inspect
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WL_DIR = ROOT / "lead" / "whitelist_audit_20261109"
WDIR = ROOT / "lead" / "check_fp_audit_20261109"

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


def sha_of(rel):
    b = (ROOT / rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def line_of(rel, n):
    p = ROOT / rel
    ls = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return (ls[n - 1], len(ls)) if 1 <= n <= len(ls) else ("<OUT OF RANGE>", len(ls))


# ---- load object under test as module (main NOT executed) -------------------
_spec = importlib.util.spec_from_file_location("cfaa_fnr", FNR / "_fnr_check.py")
fnr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fnr)
R9S = fnr.R9S
CERTS = fnr.CERTS
ADVERSARIAL = fnr.ADVERSARIAL
SPEC_ROLES = fnr.SPEC_ROLES
REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))

AUTHOR_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
    r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
    r"输出数据待补|返回值详见附件")
MY_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|见台账|详见台账|详见附件|"
    r"并非【|是否【|不可重建|输出数据待补|返回值详见附件|以.{0,10}为准|见上|见下表|"
    r"见另册|另附|另见|证据待补|未列出|待确认|未定|具体施事姓名以|以密封附件为准|"
    r"归档编号|归档索引|见方案|对应行")


def my_robust_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if MY_GUARD.search(text):
        return (False, "", {"rejected_by": "cfaa broad guard (fitted; disclosed)"})
    return (ok, layer, detail)


def author_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if AUTHOR_GUARD.search(text):
        return (False, "", {"rejected_by": "author guard"})
    return (ok, layer, detail)


def seal(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def real_base(predicate=None):
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
                predicate=predicate or R9S.r9s_element_present,
                adversarial_corpus=list(ADVERSARIAL),
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)


def third_party_certs(world_certs):
    c = copy.deepcopy(world_certs)
    for v in c.values():
        v["oracle_author"] = "independent_blind_adjudicator"
        v["predicate_author"] = "author_of_V1"
        v["oracle_truth"] = True
        v["oracle_sealed"] = True
    return c


def good_skeleton(predicate=None, with_genuine_sixth=False):
    g = real_base(predicate or my_robust_predicate)
    if with_genuine_sixth:
        g["spec_keys"] = set(R9S.SPECS.keys()) | {"交付清单"}
        g["registered_tokens"] = set(R9S.SPECS.keys()) | {"交付清单"}
    else:
        g["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    g["certificates"] = third_party_certs(CERTS)
    return g


def verdict(kw):
    r = fnr.no_relaxation_check(**kw)
    return {"VERDICT": r["VERDICT"],
            "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
            "L1_problems": list(r["L1"]["problems"]),
            "L1_coverage": r["L1"]["detail"]["coverage_ratio"],
            "L1_self_certified": r["L1"]["detail"]["self_certified"],
            "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "L3_total": r["L3"]["detail"]["n_adversarial"]}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]


# ===========================================================================
# (A) fingerprints
# ===========================================================================
def sec_a():
    rows = []
    for rel, (eh, en) in BASELINE_8.items():
        h, n = sha_of(rel)
        rows.append({"file": rel, "sha256": h, "bytes": n,
                     "match": (h == eh and n == en)})
    return {"rows": rows, "ALL_EIGHT_MATCH": all(r["match"] for r in rows)}


# ===========================================================================
# (B) three-layer result review + L1 recompute
# ===========================================================================
def sec_b():
    b = real_base()
    r = fnr.no_relaxation_check(**b)
    reg = set(R9S.SPECS.keys())
    untested = [i for i in b["items"] if i["token"] not in reg]
    wl_tokens = {k for _, k in b["whitelist"]}
    cnt = Counter(i["token"] for i in b["items"] if i["token"] in reg)
    leaks = [x["id"] for x in r["L3"]["detail"]["adversarial"] if not x["caught"]]
    return {
        "VERDICT": r["VERDICT"],
        "L1": {"ok": r["L1"]["ok"], "problems": r["L1"]["problems"],
               "detail": r["L1"]["detail"]},
        "L2": {"ok": r["L2"]["ok"], "n_rows": len(r["L2"]["rows"]),
               "all_ok": all(x["ok"] for x in r["L2"]["rows"])},
        "L3": {"ok": r["L3"]["ok"], "n_problems": len(r["L3"]["problems"]),
               "problems": r["L3"]["problems"],
               "n_caught": r["L3"]["detail"]["n_adversarial_caught"],
               "n_total": r["L3"]["detail"]["n_adversarial"],
               "leaked_ids": leaks,
               "n_mutations": r["L3"]["detail"]["n_mutations"],
               "n_mutation_alarms": r["L3"]["detail"]["n_mutation_alarms"]},
        "l1_recompute": {
            "rows": len(REF["domains32"]["rows"]), "n_items": len(b["items"]),
            "n_flips": len(b["flips"]), "n_whitelist": len(b["whitelist"]),
            "n_spec_keys": len(R9S.SPECS),
            "tested_token_counts": dict(cnt),
            "n_tested": len(b["items"]) - len(untested),
            "n_structurally_untested": len(untested),
            "coverage_ratio": round((len(b["items"]) - len(untested)) / len(b["items"]), 4),
            "wl_tokens_eq_spec_keys": wl_tokens == reg,
            "self_certified_formula": "set(wl tokens) == set(predicate_spec_keys)  [_fnr_check.py:137-138]",
        }}


# ===========================================================================
# (C) same-source prohibition lines (the refutation crux)
# ===========================================================================
def sec_c():
    refs = [
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 506),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 476),
        ("lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md", 458),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 256),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 85),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 86),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 467),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 498),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 516),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 517),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 522),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 517),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 338),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 239),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 427),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 137),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 149),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 238),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 280),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 486),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 548),
    ]
    return {("%s:%d" % (rel.split("/")[-1], n)): {"text": line_of(rel, n)[0][:230],
                                                  "total_lines": line_of(rel, n)[1]}
            for rel, n in refs}


# ===========================================================================
# (D) benign scenarios -- 8 spec-consistent + 3 same-source variants +
#     factorial sweep (does "always ALARM" hold on compliant designs?)
# ===========================================================================
NOVEL = [
    ("N-EMPTY-1", "需谁批准", "## 5 改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准。\n"),
    ("N-EMPTY-2", "改前改后", "## 4 订正草案\n【改前】旧句共 13 项分写。\n【改后】新句见另册对应行。\n逐处对照表另附。\n"),
    ("N-EMPTY-3", "可重建", "## 4 重建可行性\n判定：正确算法【可唯一重建】。原始采样记录见归档索引。\n"),
]
# guard-word-bearing extras used only in the 64-world factorial sweep
EXTRA3 = [
    ("X1", "需谁批准", "## 5 清单\n批准人待判，本件不另下结论。\n"),
    ("X2", "改前改后", "## 4 草案\n【改前】详见台账。\n【改后】本件不重录。\n"),
    ("X3", "可重建", "## 4 结论\n是否【可唯一重建】尚需核对。\n"),
]


def b1():
    return good_skeleton(with_genuine_sixth=True)


def b2():
    g = good_skeleton(with_genuine_sixth=False)
    g["spec_keys"] = set(R9S.SPECS.keys())
    g["whitelist_author"] = "independent"
    g["whitelist_sealed"] = True
    return g


def b3():
    g = good_skeleton()
    g["registered_tokens"] = {i["token"] for i in g["items"]}
    return g


def b4():
    g = good_skeleton()
    # real sha256 seals computed as side-data; checker has no slot to read them
    return g


def b5():
    g = good_skeleton()
    g["adversarial_corpus"] = list(ADVERSARIAL) + NOVEL
    return g


def b6():
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


def b7():
    g = good_skeleton()
    c = copy.deepcopy(g["certificates"])
    c[list(c)[0]]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节的正式裁决）"
    g["certificates"] = c
    return g


def b8():
    g = good_skeleton()
    t = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    g["flips"] = [x for x in g["flips"] if (x["domain"], x["token"]) != t]
    g["whitelist"] = [x for x in g["whitelist"] if tuple(x) != t]
    c = copy.deepcopy(g["certificates"])
    c.pop(t, None)
    g["certificates"] = c
    return g


BENIGN_SPEC_CONSISTENT = [
    ("B1", "理想世界:满足(E)且有第6个真实注册要素", b1),
    ("B3", "全覆盖:registered_tokens=全部item token", b3),
    ("B4", "第三方ORACLE真值表(旁路真sha256封印)", b4),
    ("B5", "对抗样本含3条novel全抓(16/16)", b5),
    ("B6", "追加1条真语义等价翻案", b6),
    ("B7", "良性引文改写", b7),
    ("B8", "删1对白名单并同步删flip/证书", b8),
    ("B9", "真第6要素+全覆盖+full adversarial+全独立标志", None),
]

SAME_SOURCE_VARIANTS = [
    ("S05", "合规同源(自造范畴):SPECS是白名单展开", b2),
    ("S06", "同源+全覆盖+自声明第三方封印", None),
    ("S07", "同源+白名单第三方封印且作者独立", None),
]


def b9():
    g = good_skeleton(with_genuine_sixth=True)
    g["registered_tokens"] = {i["token"] for i in g["items"]}
    g["adversarial_corpus"] = list(ADVERSARIAL) + NOVEL
    return g


def s06():
    g = b2()
    g["registered_tokens"] = {i["token"] for i in g["items"]}
    return g


def s07():
    g = s06()
    g["whitelist_author"] = "independent_alt"
    return g


def sec_d():
    specs = [(sid, name, (b9 if fn is None else fn)) for sid, name, fn in BENIGN_SPEC_CONSISTENT]
    ss = [(sid, name, (s06 if sid == "S06" else (s07 if sid == "S07" else fn)))
          for sid, name, fn in SAME_SOURCE_VARIANTS]
    rows = []
    for sid, name, fn in specs + ss:
        r = verdict(fn())
        r.update({"id": sid, "name": name,
                  "class": "spec_consistent" if sid.startswith("B") else "same_source_variant",
                  "trigger_layers": [L for L in ("L1", "L2", "L3") if not r[L + "_ok"]]})
        rows.append(r)

    # 64-world 7-axis factorial sweep
    axes = {
        "spec_keys": ["same_source_5", "plus_dummy_6"],
        "registered_tokens": ["five", "all_item_tokens"],
        "predicate": ["author_guard", "cfaa_guard"],
        "corpus": ["adversarial_13", "adversarial_16"],
        "certs": ["self_declared", "third_party_sealed"],
        "whitelist_author": ["independent", "independent_alt"],
        "whitelist_sealed": [True],
    }
    names = list(axes)
    all_item_tokens = {i["token"] for i in real_base()["items"]}
    sweep = []
    for combo in itertools.product(*(axes[n] for n in names)):
        cfg = dict(zip(names, combo))
        w = real_base(author_predicate if cfg["predicate"] == "author_guard" else my_robust_predicate)
        if cfg["spec_keys"] == "plus_dummy_6":
            w["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
        if cfg["registered_tokens"] == "all_item_tokens":
            w["registered_tokens"] = set(all_item_tokens)
        if cfg["corpus"] == "adversarial_16":
            # SAME construction as _cfav_probe2.py:121-122 / :88-92: three
            # guard-word-bearing EXTRA payloads, NOT the three guard-free NOVEL
            # empties.  Using NOVEL here would make 8 of 64 worlds genuinely
            # defective (author guard leaks 14/16), so they would not be benign.
            w["adversarial_corpus"] = list(ADVERSARIAL) + EXTRA3
        if cfg["certs"] == "third_party_sealed":
            w["certificates"] = third_party_certs(CERTS)
        w["whitelist_author"] = cfg["whitelist_author"]
        w["whitelist_sealed"] = cfg["whitelist_sealed"]
        rr = fnr.no_relaxation_check(**w)
        sweep.append({"cfg": cfg, "VERDICT": rr["VERDICT"],
                      "L1_ok": rr["L1"]["ok"], "L2_ok": rr["L2"]["ok"], "L3_ok": rr["L3"]["ok"]})

    def summ(key):
        s = [x for x in sweep if x["cfg"]["spec_keys"] == key]
        na = sum(1 for x in s if x["VERDICT"] == "ALARM")
        return {"n": len(s), "n_ALARM": na, "ALARM_rate": round(na / len(s), 6),
                "n_L1_false": sum(1 for x in s if not x["L1_ok"]),
                "n_non_L1_false": sum(1 for x in s if (not x["L2_ok"]) or (not x["L3_ok"]))}
    return {"scenarios": rows,
            "factorial": {"n_axes": len(names), "n_worlds": len(sweep),
                          "same_source_5": summ("same_source_5"),
                          "plus_dummy_6": summ("plus_dummy_6")},
            "fp_spec_consistent_8": {"n": 8,
                                     "n_false_alarms": sum(1 for r in rows if r["class"] == "spec_consistent" and r["VERDICT"] == "ALARM"),
                                     "wilson95": wilson(sum(1 for r in rows if r["class"] == "spec_consistent" and r["VERDICT"] == "ALARM"), 8)},
            "fp_if_same_source_counted_11": {"n": 11,
                                             "n_false_alarms": sum(1 for r in rows if r["VERDICT"] == "ALARM"),
                                             "wilson95": wilson(sum(1 for r in rows if r["VERDICT"] == "ALARM"), 11)}}


# ===========================================================================
# (E) three-layer independence probes
# ===========================================================================
def sec_e():
    src = (FNR / "_fnr_check.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    io = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        calls = set()
        for c in ast.walk(node):
            if isinstance(c, ast.Call):
                f = c.func
                calls.add(f.id if isinstance(f, ast.Name) else
                          (f.attr if isinstance(f, ast.Attribute) else ""))
        io[node.name] = {"lineno": node.lineno,
                         "opens_file": any(x in ("open", "read_text", "read_bytes") for x in calls),
                         "computes_hash": any(x in ("sha256", "hexdigest") for x in calls),
                         "writes_file": any(x in ("write_text", "write_bytes") for x in calls)}
    # P1 forged anchors/quotes
    w = good_skeleton()
    fake = copy.deepcopy(w["certificates"])
    for i, c in enumerate(fake.values()):
        c["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        c["quote"] = "本复核凭空编造的引文，未见于任何交付件。"
    w["certificates"] = fake
    r_forge = verdict(w)
    r_forge["anchor_files_exist"] = [(ROOT / c["anchor"].split(":")[0]).exists()
                                     for c in fake.values()]
    # P5 artifact slot
    w2 = dict(good_skeleton())
    w2["artifact_text"] = "REAL DELIVERABLE TEXT"
    try:
        fnr.no_relaxation_check(**w2)
        slot = {"extra_kwarg_accepted": True}
    except TypeError as e:
        slot = {"extra_kwarg_accepted": False, "TypeError": str(e)}
    # P10 per-layer recall from read-only json
    d = json.loads((FNR / "_fnr_check_out.json").read_text(encoding="utf-8"))
    wr = d["new_check_meta_test"]["wrong_injections"]
    per_layer = {L: sum(1 for r in wr if not r["layers"][L]) for L in ("L1", "L2", "L3")}
    # P11 coverage 0.0
    g = good_skeleton()
    g["registered_tokens"] = set()
    r_zero = fnr.check_l1(g["items"], g["flips"], g["whitelist"],
                          g["registered_tokens"], g["spec_keys"], True, "independent")
    # P2 guard fit + novel + provenance
    author_words = ["待判", "待定", "尚需", "尚未", "不另下结论", "暂不作判定",
                    "本件不重录", "见台账", "详见台账", "详见附件", "并非【",
                    "是否【", "不可重建", "输出数据待补", "返回值详见附件"]
    fit = sum(1 for _, _, t in ADVERSARIAL if any(w in t for w in author_words))
    novel_rows = [{"id": cid, "author_guard_hit": bool(AUTHOR_GUARD.search(t)),
                   "present_r9s": bool(R9S.r9s_element_present(t, tok)[0]),
                   "present_author_guard": bool(author_predicate(t, tok)[0])}
                  for cid, tok, t in NOVEL]
    ga = good_skeleton(author_predicate)
    ga["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    ga["adversarial_corpus"] = list(ADVERSARIAL) + NOVEL
    r_ga = fnr.no_relaxation_check(**ga)
    provenance = []
    for p in sorted(WL_DIR.rglob("*.py")) + sorted(WL_DIR.rglob("*.md")) + sorted(WL_DIR.rglob("*.txt")):
        try:
            provenance.append((str(p.relative_to(ROOT)), p.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            pass
    frag_hits = 0
    for _, _, t in ADVERSARIAL:
        frag = t.strip().split("\n")[-1][:24]
        if frag and any(frag in txt for _, txt in provenance):
            frag_hits += 1
    # ORACLE/seal file search in three dirs
    oracle_files = []
    for dr in (FNR, WL_DIR, R9S_DIR):
        for p in dr.rglob("*"):
            if p.is_file() and ("oracle" in p.name.lower() or "seal" in p.name.lower()):
                oracle_files.append(str(p.relative_to(ROOT)))
    return {
        "ast_io": io,
        "signatures": {"no_relaxation_check": list(inspect.signature(fnr.no_relaxation_check).parameters),
                       "check_l1": list(inspect.signature(fnr.check_l1).parameters),
                       "certificate_ok": list(inspect.signature(fnr.certificate_ok).parameters)},
        "P1_forged_certs": r_forge,
        "P5_artifact_slot": slot,
        "P10_per_layer_recall": {"n_wrong": len(wr), "counts": per_layer},
        "P11_coverage_zero": {"ok": r_zero[0], "coverage": r_zero[2]["coverage_ratio"],
                              "problems": r_zero[1]},
        "P2_guard_fit": {"n_fitted": fit, "n_total": len(ADVERSARIAL)},
        "P2_novel": novel_rows,
        "P2_author_guard_caught": "%d/%d" % (r_ga["L3"]["detail"]["n_adversarial_caught"],
                                             r_ga["L3"]["detail"]["n_adversarial"]),
        "P2_upstream_fragment_hits": "%d/%d" % (frag_hits, len(ADVERSARIAL)),
        "oracle_seal_files_found": oracle_files,
    }


# ===========================================================================
# (F) meta-test limits
# ===========================================================================
def sec_f():
    m_empty = fnr.meta_test(real_base(), [], [])
    def g1(kw):
        d = dict(kw)
        c = copy.deepcopy(kw["certificates"])
        c[list(c)[0]]["quote"] = "批准人一律 = 乙设计责任人（另见第 5.2 节）"
        d["certificates"] = c
        return d
    def g2(kw):
        d = dict(kw)
        d["adversarial_corpus"] = list(kw["adversarial_corpus"]) + [
            ("EXTRA", "可重建", "## 4 结论\n不可重建：证据待补。\n")]
        return d
    m_wrongbase = fnr.meta_test(real_base(), [], [("reworded_quote_still_true", g1),
                                                   ("extra_adversarial_case_caught", g2)])
    d = json.loads((FNR / "_fnr_check_out.json").read_text(encoding="utf-8"))
    mt = d["new_check_meta_test"]
    # padding P9
    a = good_skeleton()
    b = good_skeleton()
    b["spec_keys"] = set(R9S.SPECS.keys())
    return {
        "P3_empty_lists_on_ALARM_baseline": {
            "baseline_VERDICT": m_empty["baseline_VERDICT"],
            "n_wrong": m_empty["n_wrong"], "n_good": m_empty["n_good"],
            "CHECKER_VALID": m_empty["CHECKER_VALID"]},
        "P4_wrong_baseline": {
            "baseline_VERDICT": m_wrongbase["baseline_VERDICT"],
            "n_false_alarms": m_wrongbase["n_false_alarms"],
            "CHECKER_VALID": m_wrongbase["CHECKER_VALID"]},
        "P7_power_bounds": {
            "n_wrong": mt["n_wrong"], "n_wrong_caught": mt["n_wrong_caught"],
            "sensitivity_lower_95": round(0.05 ** (1.0 / 9), 6),
            "n_good": mt["n_good"], "n_false_alarms": mt["n_false_alarms"],
            "fp_upper_95": round(1 - 0.05 ** (1.0 / 2), 6)},
        "P9_padding": {"with_dummy_key": verdict(a)["VERDICT"],
                       "without_dummy_key": verdict(b)["VERDICT"],
                       "dummy_key": "额外预留要素"},
        "shipped_meta": {"baseline_VERDICT": mt["baseline_VERDICT"],
                         "synthetic_baseline_VERDICT": mt["synthetic_baseline_VERDICT"],
                         "CHECKER_VALID": mt["CHECKER_VALID"],
                         "synthetic_catch": "%d/%d" % (mt["synthetic_predicate_adversarial_catch"],
                                                       mt["synthetic_predicate_adversarial_total"])},
    }


# ===========================================================================
# (G) read-only unchanged + git hygiene
# ===========================================================================
def sec_g():
    before = {rel: sha_of(rel) for rel in BASELINE_8}
    return {"recomputed": {rel.split("/")[-1]: {"sha256": h, "bytes": n}
                           for rel, (h, n) in before.items()}}


def main():
    out = {}
    out["A_fingerprints"] = sec_a()
    out["B_three_layers"] = sec_b()
    out["C_prohibition_lines"] = sec_c()
    out["D_benign_and_factorial"] = sec_d()
    out["E_independence"] = sec_e()
    out["F_meta"] = sec_f()
    out["G_readonly_recheck"] = sec_g()
    (WDIR / "_cfaa_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("=== A. 8 ORCHESTRATOR FINGERPRINTS (hashlib, this session) ===")
    for r in out["A_fingerprints"]["rows"]:
        print("  %-46s %s bytes=%d match=%s" %
              (r["file"].split("/")[-1], r["sha256"], r["bytes"], r["match"]))
    print("  ALL_EIGHT_MATCH =", out["A_fingerprints"]["ALL_EIGHT_MATCH"])

    print("\n=== B. THREE-LAYER RESULT REVIEW (module load, main NOT run) ===")
    b = out["B_three_layers"]
    print("  VERDICT=%s L1_ok=%s L2_ok=%s L3_ok=%s" %
          (b["VERDICT"], b["L1"]["ok"], b["L2"]["ok"], b["L3"]["ok"]))
    print("  L1_problems =", json.dumps(b["L1"]["problems"], ensure_ascii=False))
    print("  L1_detail   =", json.dumps(b["L1"]["detail"], ensure_ascii=False))
    print("  L2 n_rows=%d all_ok=%s" % (b["L2"]["n_rows"], b["L2"]["all_ok"]))
    print("  L3 caught=%d/%d leaked=%s mutations=%d/%d" %
          (b["L3"]["n_caught"], b["L3"]["n_total"], b["L3"]["leaked_ids"],
           b["L3"]["n_mutation_alarms"], b["L3"]["n_mutations"]))
    print("  L1_RECOMPUTE =", json.dumps(b["l1_recompute"], ensure_ascii=False))

    print("\n=== C. SAME-SOURCE PROHIBITION / CONTESTED LINES ===")
    for k, v in out["C_prohibition_lines"].items():
        print("  %-42s %s" % (k, v["text"]))

    print("\n=== D. BENIGN SCENARIOS (per-scenario VERDICT + trigger layer) ===")
    for r in out["D_benign_and_factorial"]["scenarios"]:
        print("  %-4s %-46s VERDICT=%-5s trigger=%-12s L1=%-5s L2=%-5s L3=%-5s cov=%s" %
              (r["id"], r["name"][:46], r["VERDICT"], ",".join(r["trigger_layers"]) or "-",
               r["L1_ok"], r["L2_ok"], r["L3_ok"], r["L1_coverage"]))
    print("  FACTORIAL =", json.dumps(out["D_benign_and_factorial"]["factorial"], ensure_ascii=False))
    print("  FP_spec_consistent_8    =", json.dumps(out["D_benign_and_factorial"]["fp_spec_consistent_8"], ensure_ascii=False))
    print("  FP_if_same_source_11    =", json.dumps(out["D_benign_and_factorial"]["fp_if_same_source_counted_11"], ensure_ascii=False))

    print("\n=== E. INDEPENDENCE PROBES ===")
    e = out["E_independence"]
    for name in ("certificate_ok", "check_l1", "check_l2", "check_l3", "no_relaxation_check", "meta_test", "main"):
        v = e["ast_io"].get(name)
        if v:
            print("  AST %-22s line=%-4d opens=%-5s hash=%-5s writes=%s" %
                  (name, v["lineno"], v["opens_file"], v["computes_hash"], v["writes_file"]))
    print("  signatures =", json.dumps(e["signatures"], ensure_ascii=False))
    print("  P1 forged certs  =", json.dumps(e["P1_forged_certs"], ensure_ascii=False))
    print("  P5 artifact slot =", json.dumps(e["P5_artifact_slot"], ensure_ascii=False))
    print("  P10 per layer    =", json.dumps(e["P10_per_layer_recall"], ensure_ascii=False))
    print("  P11 coverage 0.0 =", json.dumps(e["P11_coverage_zero"], ensure_ascii=False))
    print("  P2 guard fit     =", json.dumps(e["P2_guard_fit"], ensure_ascii=False),
          "novel caught=", e["P2_author_guard_caught"],
          "upstream_frag=", e["P2_upstream_fragment_hits"])
    print("  P2 novel rows    =", json.dumps(e["P2_novel"], ensure_ascii=False))
    print("  oracle/seal files=", json.dumps(e["oracle_seal_files_found"], ensure_ascii=False))

    print("\n=== F. META-TEST LIMITS ===")
    print(json.dumps(out["F_meta"], ensure_ascii=False, indent=1))

    print("\n=== G. READ-ONLY 8 RECHECK (post-run) ===")
    print(json.dumps(out["G_readonly_recheck"]["recomputed"], ensure_ascii=False, indent=1))
    print("\nWROTE _cfaa_out.json")


if __name__ == "__main__":
    main()
