# -*- coding: utf-8 -*-
r"""_fnrd_verify.py -- independent reproduction of the review's refutation.

Tests whether _fnr_check.py's new L1/L2/L3 checker ALARMS when the
conclusions ("no relaxation") are wrong in ways that touch the DELIVERED
ARTIFACTS rather than the certificate bookkeeping.

All in memory, in the sole write domain. No predicate/regression/whitelist is
modified. Zero real-machine, zero sampling code.

Run:
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrd_verify.py
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "falsifiable_no_relax_20261109"
CHECK = WDIR / "_fnr_check.py"

spec = importlib.util.spec_from_file_location("fnrd_check", CHECK)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ref = json.loads((ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json")
                 .read_text(encoding="utf-8"))
items, flips, wl = [], [], []
for r in ref["domains32"]["rows"]:
    if r.get("main_missing"):
        continue
    for e in r["per_element"]:
        items.append({"domain": r["domain"], "token": e["token"]})
for f in ref["domains32"]["flips"]:
    flips.append({"domain": f["domain"], "token": f["token"]})
wl = [tuple(x) for x in ref["domains32"]["whitelist"]]

# Exact author guard list (:478-480), no extra words of my own.
AUTHOR_GUARD = re.compile(r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
                          r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
                          r"输出数据待补|返回值详见附件")


def repaired(text, token):
    """Verbatim re-implementation of the author's synthetic good-world predicate."""
    ok, layer, detail = m.R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if AUTHOR_GUARD.search(text):
        return (False, "", {"rejected_by": "pending/pointer guard"})
    return (ok, layer, detail)


good = dict(items=items, flips=flips, whitelist=wl,
            registered_tokens=set(m.R9S.SPECS.keys()),
            spec_keys=set(m.R9S.SPECS.keys()) | {"额外预留要素"},
            certificates=m.CERTS, spec_roles=m.SPEC_ROLES,
            predicate=repaired, adversarial_corpus=list(m.ADVERSARIAL),
            predicate_author="author_of_V1",
            whitelist_author="independent", whitelist_sealed=True)

out = {}

# (A) Exact parameter names: is there any slot for the delivered artifact TEXT?
sig = inspect.signature(m.no_relaxation_check)
names = list(sig.parameters)
EXACT_ARTIFACT_NAMES = {"artifacts", "artifact", "artifact_text", "text", "texts",
                        "main", "mains", "source", "sources", "documents", "docs",
                        "deliverables", "files", "file_texts"}
has_exact = bool(set(names) & EXACT_ARTIFACT_NAMES)
out["A_signature"] = {
    "params": names, "n_params": len(names),
    "has_exact_artifact_text_param": has_exact,
    "adversarial_corpus_is": "list of (cid, token, text) ADVERSARIAL payloads, "
                             "NOT the 5 delivered main artifacts",
}
print("=== (A) exact signature ===")
print("  params =", names)
print("  has exact artifact/text parameter? =", has_exact)
print("  BASELINE good_world VERDICT =", m.no_relaxation_check(**good)["VERDICT"])

# (B) 'All 5 conclusions wrong': all 5 delivered artifacts replaced by
#     semantically-empty payloads, certificates left byte-identical.
sp = importlib.util.spec_from_file_location("fnrd_replay", WDIR / "_fnr_replay.py")
rm = importlib.util.module_from_spec(sp)
sp.loader.exec_module(rm)
EMPTY = rm.EMPTY
kw_b = dict(good); kw_b["certificates"] = copy.deepcopy(m.CERTS)
r_b = m.no_relaxation_check(**kw_b)
out["B_artifacts_all_empty"] = {
    "n_artifacts_replaced": len(EMPTY),
    "certificates_changed": False,
    "VERDICT": r_b["VERDICT"],
    "L1": r_b["L1"]["ok"], "L2": r_b["L2"]["ok"], "L3": r_b["L3"]["ok"],
    "why": "no artifact input exists; replacing the 5 mains cannot affect the verdict",
}
print("\n=== (B) all 5 artifacts semantically empty, certs untouched ===")
print("  n_artifacts_replaced =", len(EMPTY))
print("  VERDICT =", r_b["VERDICT"], " L1/L2/L3 =",
      r_b["L1"]["ok"], r_b["L2"]["ok"], r_b["L3"]["ok"])

# (C) Forge fabricated evidence: fake anchor + explicitly fabricated quote,
#     real-looking role values kept, independence flags self-declared.
forged = copy.deepcopy(m.CERTS)
for i, c in enumerate(forged.values()):
    c["anchor"] = "nowhere/FAKE_%d.md:999" % i
    c["quote"] = "这是一条由复核员凭空编造的引文，未在任何文件中出现。"
    c["oracle_truth"] = True
    c["oracle_author"] = "independent_blind_adjudicator"
    c["predicate_author"] = "author_of_V1"
    c["oracle_sealed"] = True
kw_c = dict(good); kw_c["certificates"] = forged
r_c = m.no_relaxation_check(**kw_c)
cert_src = inspect.getsource(m.certificate_ok)
l1_src = inspect.getsource(m.check_l1)
l2_src = inspect.getsource(m.check_l2)
l3_src = inspect.getsource(m.check_l3)
impl_src = cert_src + l1_src + l2_src + l3_src
out["C_forged_evidence"] = {
    "VERDICT": r_c["VERDICT"],
    "L2_ok": r_c["L2"]["ok"], "L2_problems": r_c["L2"]["problems"],
    "L1": r_c["L1"]["ok"], "L3": r_c["L3"]["ok"],
    "certificate_ok_resolves_file": any(x in cert_src for x in
        ("open(", "read_text", "exists(", "is_file", "Path(", "glob(")),
    "impl_verifies_seal_hash": "sha256" in impl_src.lower(),
    "impl_source_len": len(impl_src),
}
print("\n=== (C) fabricated anchors/quotes + self-declared independence ===")
print("  VERDICT =", r_c["VERDICT"], " L2_ok =", r_c["L2"]["ok"],
      " L2_problems =", r_c["L2"]["problems"])
print("  certificate_ok resolves anchor against a real file? =",
      out["C_forged_evidence"]["certificate_ok_resolves_file"])
print("  L1/L2/L3 implementation computes a seal hash? =",
      out["C_forged_evidence"]["impl_verifies_seal_hash"])

# (D) Is bounded-tightening (B) actually implemented as a decision?
impl_code = "\n".join(
    l for l in impl_src.split("\n") if not l.strip().startswith("#"))
out["D_definition_coverage"] = {
    "tighten_in_impl_code": impl_code.lower().count("tighten"),
    "coverage_is_fail_condition": any("coverage" in p for p in
        m.check_l1(items, flips, wl, set(m.R9S.SPECS.keys()),
                   set(m.R9S.SPECS.keys()))[1]),
    "l1_problems_on_real_state": m.check_l1(
        items, flips, wl, set(m.R9S.SPECS.keys()),
        set(m.R9S.SPECS.keys()))[1],
    "oracle_applies_to_n_flips": len(flips),
    "oracle_applies_to_n_items": len(items),
}
print("\n=== (D) bounded-tightening (B) and coverage (C) ===")
print("  'tighten' in non-comment L1/L2/L3 code =",
      out["D_definition_coverage"]["tighten_in_impl_code"])
print("  coverage is ever a FAIL condition? =",
      out["D_definition_coverage"]["coverage_is_fail_condition"])
print("  ORACLE applies to %d flips out of %d items" %
      (len(flips), len(items)))

# (E) Novel semantic empties containing NONE of the author's guard words.
novel = [
    ("N-EMPTY-1", "需谁批准", "## 5 改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准。\n"),
    ("N-EMPTY-2", "改前改后", "## 4 订正草案\n【改前】旧句共 13 项分写。\n【改后】新句见另册对应行。\n逐处对照表另附。\n"),
    ("N-EMPTY-3", "可重建", "## 4 重建可行性\n判定：正确算法【可唯一重建】。原始采样记录见归档索引。\n"),
]
rows = []
for cid, tok, txt in novel:
    rows.append({"id": cid, "author_guard_hit": bool(AUTHOR_GUARD.search(txt)),
                 "r9s_present": bool(m.R9S.r9s_element_present(txt, tok)[0]),
                 "repaired_present": bool(repaired(txt, tok)[0])})
out["E_novel_empties"] = rows
print("\n=== (E) novel empties with NO author guard word ===")
for r in rows:
    print("  %-10s author_guard_hit=%-5s R9S=%-5s repaired=%-5s caught? %s" %
          (r["id"], r["author_guard_hit"], r["r9s_present"], r["repaired_present"],
           not r["r9s_present"]))

kw_e = dict(good)
kw_e["adversarial_corpus"] = list(m.ADVERSARIAL) + novel
r_e = m.no_relaxation_check(**kw_e)
out["E_good_world_plus_novel"] = {"VERDICT": r_e["VERDICT"],
    "n_caught": r_e["L3"]["detail"]["n_adversarial_caught"],
    "n_total": r_e["L3"]["detail"]["n_adversarial"]}
print("  'good world' + 3 novel empties: VERDICT=%s caught=%d/%d" %
      (r_e["VERDICT"], r_e["L3"]["detail"]["n_adversarial_caught"],
       r_e["L3"]["detail"]["n_adversarial"]))

(WDIR / "_fnrd_verify_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _fnrd_verify_out.json")
print("checker_sha256 =", hashlib.sha256(CHECK.read_bytes()).hexdigest())
