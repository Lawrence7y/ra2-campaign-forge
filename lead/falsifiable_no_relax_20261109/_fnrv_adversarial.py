# -*- coding: utf-8 -*-
"""Adversarial review of _fnr_check.py's meta-test.

Tests whether the NEW checker really alarms when conclusions are wrong, and
whether its "independent oracle" requirement is substantive or merely a
self-declared string flag that any author (including me) can forge.

Also injects the reviewer's OWN 3 novel semantic-empty payloads into the
adversarial corpus to see whether L3's predicate catches them.
"""
import copy
import hashlib
import importlib.util
import json
import sys

ROOT = "D:/Project/ra2-campaign-forge/"
CHECK = ROOT + "lead/falsifiable_no_relax_20261109/_fnr_check.py"
REPLAY = ROOT + "lead/falsifiable_no_relax_20261109/_fnrv_replay_out.json"
OUT = ROOT + "lead/falsifiable_no_relax_20261109/_fnrv_adversarial_out.json"

spec = importlib.util.spec_from_file_location("fnr_check_under_review", CHECK)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ref = json.loads(open(ROOT + "lead/gate_r9sem_20261109/_r9s_regress_out.json", encoding="utf-8").read())
my = json.loads(open(REPLAY, encoding="utf-8").read())

items, flips, wl = [], [], []
for r in ref["domains32"]["rows"]:
    if r.get("main_missing"):
        continue
    for e in r["per_element"]:
        items.append({"domain": r["domain"], "token": e["token"]})
for f in ref["domains32"]["flips"]:
    flips.append({"domain": f["domain"], "token": f["token"]})
wl = [tuple(x) for x in ref["domains32"]["whitelist"]]

base = dict(items=items, flips=flips, whitelist=wl,
            registered_tokens=set(m.R9S.SPECS.keys()),
            spec_keys=set(m.R9S.SPECS.keys()) | {"额外预留要素"},
            certificates=m.CERTS, spec_roles=m.SPEC_ROLES,
            predicate=lambda t, k: m.R9S.r9s_element_present(t, k),
            adversarial_corpus=m.ADVERSARIAL)

print("=== (1) FORGE TEST: can a reviewer fabricate a 'fully independent' certificate? ===")
# Take the real (self-authored demo) certificates, then change ONLY the strings
# that the checker uses to decide independence. Semantic content stays EMPTY.
forged = copy.deepcopy(m.CERTS)
for c in forged.values():
    for k in c["roles"]:
        c["roles"][k] = "见台账登记，本件不重录"   # semantic value is a POINTER
    c["oracle_truth"] = True                      # oracle CLAIMS content delivered
    c["oracle_author"] = "independent_blind_adjudicator"  # self-declared
    c["predicate_author"] = "author_of_V1"
    c["oracle_sealed"] = True                     # self-declared flag, no real seal check
kw = dict(base); kw["certificates"] = forged
r = m.no_relaxation_check(**kw)
print("  forged_world: all 5 role values are pointers; oracle_truth=True;")
print("                oracle_author = 'independent_blind_adjudicator' (a string I typed)")
print("                oracle_sealed  = True (a bool I typed, no hash verified)")
print("  checker VERDICT = %s  L2_ok=%s  L2_problems=%s" % (r["VERDICT"], r["L2"]["ok"], r["L2"]["problems"]))
print("  => L2 detects pointer values? %s" % (not r["L2"]["ok"]))
print("  => but oracle independence itself is UNVERIFIABLE from checker inputs: "
      "certificate_ok only compares two author STRINGS (:120) and a BOOL (:122)")

# Stronger: make values real-looking but fabricated, keep independence flags.
forged2 = copy.deepcopy(m.CERTS)
for c in forged2.values():
    c["quote"] = "这是一条由复核员凭空编造的引文，未在任何文件中出现。"
    c["anchor"] = "nowhere/FAKE.md:999"
    c["oracle_truth"] = True
    c["oracle_author"] = "independent_blind_adjudicator"
    c["oracle_sealed"] = True
kw2 = dict(base); kw2["certificates"] = forged2
r2 = m.no_relaxation_check(**kw2)
print("\n  forged_world_2: anchor='nowhere/FAKE.md:999', quote explicitly fabricated,")
print("                  role values left intact, independence flags self-declared")
print("  checker VERDICT = %s  L2_ok=%s  L2_problems=%s" % (r2["VERDICT"], r2["L2"]["ok"], r2["L2"]["problems"]))
print("  => anchor is only regex-checked (:100), NOT resolved against any file")

print("\n=== (2) MY 3 NOVEL semantic-empty payloads vs the checker's L3 corpus ===")
my_corpus = [
    ("RV-E1", "需谁批准", "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准，本件不重录。\n"),
    ("RV-E2", "改前改后", "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A\n- 【改前】旧句共 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】新句见方案 B 的对应行，本件不重录。\n- 【要点】逐处对照表另附。\n"),
    ("RV-E3", "可重建", "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n判定：正确算法【可唯一重建】。已有四重独立实现逐位一致，max|Δ|=0.000000；原始采样记录见归档索引，本件不重录。\n"),
]
for cid, tok, txt in my_corpus:
    present = m.R9S.r9s_element_present(txt, tok)[0]
    print("  %-6s %-10s R9S_present=%-5s  => caught(ABSENT)? %s" % (cid, tok, present, not present))

# Add them to the adversarial corpus and run the FULL checker (real predicate).
kw3 = dict(base); kw3["adversarial_corpus"] = list(m.ADVERSARIAL) + my_corpus
r3 = m.no_relaxation_check(**kw3)
print("  full checker with my 3 added: VERDICT=%s  L3_adversarial=%d/%d caught, L3_ok=%s" %
      (r3["VERDICT"], r3["L3"]["detail"]["n_adversarial_caught"],
       r3["L3"]["detail"]["n_adversarial"], r3["L3"]["ok"]))

print("\n=== (3) META-TEST sensitivity: does the checker alarm on a NEW error class? ===")
# Error class NOT in the author's 9 injections: adversarially append ONE of my
# empty payloads to the corpus but supply a leaky predicate that returns PRESENT
# for it. Author's w_adversarial_leak covers pending markers; mine uses a
# different marker ("以密封附件为准") to test generality.
def leaky_new(text, token):
    if "以密封附件为准" in text or "逐处对照表另附" in text or "见归档索引" in text:
        return (True, "semantic", {})
    return m.R9S.r9s_element_present(text, token)
kw4 = dict(base)
kw4["adversarial_corpus"] = list(m.ADVERSARIAL) + my_corpus
kw4["predicate"] = leaky_new
r4 = m.no_relaxation_check(**kw4)
print("  novel-marker leaky predicate + my corpus: VERDICT=%s  L3_ok=%s  n_caught=%d/%d" %
      (r4["VERDICT"], r4["L3"]["ok"], r4["L3"]["detail"]["n_adversarial_caught"],
       r4["L3"]["detail"]["n_adversarial"]))

print("\n=== (4) Re-run author's meta_test() as-is (independent import) ===")
def repaired(text, token):
    ok, layer, detail = m.R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    bad = __import__("re").search(
        r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|见台账|详见台账|"
        r"详见附件|并非【|是否【|不可重建|输出数据待补|返回值详见附件", text)
    if bad:
        return (False, "", {"rejected_by": "pending/pointer guard"})
    return (ok, layer, detail)
good = dict(base)
good["spec_keys"] = set(m.R9S.SPECS.keys()) | {"额外预留要素"}
good["predicate"] = repaired
wrongs = [
    ("all5_empty", lambda kw: {**dict(kw), "certificates": forged}),
    ("1_oracle_false", lambda kw: {**dict(kw), "certificates": {
        **copy.deepcopy(m.CERTS), list(m.CERTS)[0]: {**copy.deepcopy(m.CERTS[list(m.CERTS)[0]]),
                                                      "oracle_truth": False}}}),
    ("unsealed_wl", lambda kw: {**dict(kw), "whitelist_sealed": False}),
    ("self_certified", lambda kw: {**dict(kw), "spec_keys": set(kw["registered_tokens"])}),
]
goods = [("reworded", lambda kw: {**dict(kw), "certificates": {
    **copy.deepcopy(m.CERTS), list(m.CERTS)[0]: {**copy.deepcopy(m.CERTS[list(m.CERTS)[0]]),
                                                  "quote": "批准人一律 = 乙设计责任人（另见第 5.2 节）"}}})]
meta = m.meta_test(good, wrongs, goods)
print("  baseline=%s  n_wrong=%d n_caught=%d  n_good=%d n_false=%d  CHECKER_VALID=%s" %
      (meta["baseline_VERDICT"], meta["n_wrong"], meta["n_wrong_caught"],
       meta["n_good"], meta["n_false_alarms"], meta["CHECKER_VALID"]))

out = {"forged_world_1": {"VERDICT": r["VERDICT"], "L2_ok": r["L2"]["ok"], "L2_problems": r["L2"]["problems"]},
       "forged_world_2": {"VERDICT": r2["VERDICT"], "L2_ok": r2["L2"]["ok"], "L2_problems": r2["L2"]["problems"]},
       "my_corpus_full_check": {"VERDICT": r3["VERDICT"], "n_caught": r3["L3"]["detail"]["n_adversarial_caught"],
                                "n_total": r3["L3"]["detail"]["n_adversarial"]},
       "novel_leak": {"VERDICT": r4["VERDICT"], "n_caught": r4["L3"]["detail"]["n_adversarial_caught"],
                      "n_total": r4["L3"]["detail"]["n_adversarial"]},
       "meta_rerun": meta,
       "check_sha256": hashlib.sha256(open(CHECK, "rb").read()).hexdigest()}
open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
print("WROTE _fnrv_adversarial_out.json")
