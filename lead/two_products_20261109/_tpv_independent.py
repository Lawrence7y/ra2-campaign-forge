# -*- coding: utf-8 -*-
"""_tpv_independent.py — 独立复核员自用：从头读两份 JSON，独立重算 9 维 canonical。
不 import _tp_crosscheck，不采信撰写人的任何聚合结论。
"""
import json, os, sys, hashlib
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
R11 = REPO / "lead" / "r11_f2_fix_20261109"
A = json.loads((R11 / "_f2_compare_out.json").read_text(encoding="utf-8"))
B = json.loads((R11 / "_f2v_run_out.json").read_text(encoding="utf-8"))

print("== 顶层键 ==")
print("A top:", sorted(A.keys()), " B top:", sorted(B.keys()))
print("A totals:", json.dumps(A["totals"], ensure_ascii=False, sort_keys=True))
print("B totals:", json.dumps(B["totals"], ensure_ascii=False, sort_keys=True))
ka, kb = set(A["totals"]), set(B["totals"])
print("onlyA", sorted(ka - kb), "onlyB", sorted(kb - ka), "common", sorted(ka & kb))
print("common value_diff:", {k: (A["totals"][k], B["totals"][k]) for k in (ka & kb) if A["totals"][k] != B["totals"][k]})
print("alias orig: A.orig_path", A["totals"].get("orig_path"), "B.orig_collected", B["totals"].get("orig_collected"))
print("alias plus: A.plus_path", A["totals"].get("plus_path"), "B.plus_collected", B["totals"].get("plus_collected"))
print("n_results", len(A["results"]), len(B["results"]))
print("B declared_mismatch_files", B.get("declared_mismatch_files"))

print("== 文件集/顺序（normcase+normpath）与 realpath ==")
fa = [os.path.normcase(os.path.normpath(r["file"])) for r in A["results"]]
fb = [os.path.normcase(os.path.normpath(str(REPO / r["rel"].replace("/", os.sep)))) for r in B["results"]]
print("normcase set onlyA", sorted(set(fa) - set(fb)), "onlyB", sorted(set(fb) - set(fa)))
print("normcase common n", len(set(fa) & set(fb)), "order same", fa == fb)
ra = [os.path.normcase(os.path.realpath(r["file"])) for r in A["results"]]
rb = [os.path.normcase(os.path.realpath(str(REPO / r["rel"]))) for r in B["results"]]
print("realpath set onlyA", len(set(ra) - set(rb)), "onlyB", len(set(rb) - set(ra)), "order same", ra == rb)
print("A result keys:", sorted(A["results"][0].keys()))
print("B result keys:", sorted(B["results"][0].keys()))

print("== 独立重算 9 维（从各自 results[]，不看 totals）==")
def canonA(doc):
    R = doc["results"]
    return {
        "bindings": sum(len(r["orig"]["bindings"]) for r in R),
        "orig_collected": sum(1 for r in R for b in r["orig"]["bindings"] if b["path"]),
        "plus_collected": sum(1 for r in R for b in r["plus"]["bindings"] if b.get("path")),
        "orig_match": sum(1 for r in R for b in r["orig"]["bindings"] if b["match"] is True),
        "plus_match": sum(1 for r in R for b in r["plus"]["bindings"] if b.get("match") is True),
        "orig_problems": sum(len(r["orig"]["problems"]) for r in R),
        "plus_problems": sum(len(r["plus"]["problems"]) for r in R),
        "orig_warnings": sum(len(r["orig"]["warnings"]) for r in R),
        "plus_warnings": sum(len(r["plus"]["warnings"]) for r in R),
    }

def canonB(doc):
    R = doc["results"]
    return {
        "bindings": sum(r["n_bindings"] for r in R),
        "orig_collected": sum(1 for r in R for v in r["orig_paths"] if v),
        "plus_collected": sum(1 for r in R for v in r["plus_paths"] if v),
        "orig_match": sum(1 for r in R for v in r["orig_match"] if v is True),
        "plus_match": sum(1 for r in R for v in r["plus_match"] if v is True),
        "orig_problems": sum(len(r["orig_problems"]) for r in R),
        "plus_problems": sum(len(r["plus_problems"]) for r in R),
        "orig_warnings": sum(len(r["orig_warnings"]) for r in R),
        "plus_warnings": sum(len(r["plus_warnings"]) for r in R),
    }
ca, cb = canonA(A), canonB(B)
print("A canon:", json.dumps(ca, ensure_ascii=False, sort_keys=True))
print("B canon:", json.dumps(cb, ensure_ascii=False, sort_keys=True))
print("canonical_equal", ca == cb)

print("== 各自 totals 与自身 results 重算比较（别名映射）==")
ALIAS = {"bindings": ("bindings", "bindings"), "orig_collected": ("orig_path", "orig_collected"),
         "plus_collected": ("plus_path", "plus_collected"), "orig_match": ("orig_match", "orig_match"),
         "plus_match": ("plus_match", "plus_match"), "orig_problems": ("orig_problems", "orig_problems"),
         "plus_problems": ("plus_problems", "plus_problems"), "orig_warnings": (None, "orig_warnings"),
         "plus_warnings": (None, "plus_warnings")}
for label, doc, calc, i in (("A", A, ca, 0), ("B", B, cb, 1)):
    for k, pair in ALIAS.items():
        key = pair[i]
        if key is None:
            print(label, k, "not written in totals (expected for A warnings)")
            continue
        got, exp = doc["totals"].get(key, "<ABSENT>"), calc[k]
        print(label, key, got, "==", exp, got == exp)

print("== 逐绑定行投影 path/match/tier + B declared_seq_same/n_bindings ==")
mis = []
for i, (a, b) in enumerate(zip(A["results"], B["results"])):
    ob, pb = a["orig"]["bindings"], a["plus"]["bindings"]
    if len(ob) != b["n_bindings"]:
        mis.append((i, "n_bindings", len(ob), b["n_bindings"]))
    if [x["path"] for x in ob] != b["orig_paths"]:
        mis.append((i, "orig_paths"))
    if [x.get("path") for x in pb] != b["plus_paths"]:
        mis.append((i, "plus_paths"))
    if [x["match"] for x in ob] != b["orig_match"]:
        mis.append((i, "orig_match"))
    if [x.get("match") for x in pb] != b["plus_match"]:
        mis.append((i, "plus_match"))
    if [x.get("tier") for x in pb] != b["plus_tiers"]:
        mis.append((i, "plus_tiers"))
    if b["declared_seq_same"] is not True:
        mis.append((i, "declared_seq_same", b["declared_seq_same"]))
print("per-binding/tier mismatches:", mis[:20], "count", len(mis))
print("B declared_seq_same all True:", all(r["declared_seq_same"] is True for r in B["results"]))

print("== 是否有 counting_policy/schema_version/merged/by_kind 顶层标记 ==")
for label, doc in (("A", A), ("B", B)):
    print(label, [k for k in ("counting_policy", "schema_version", "merged", "by_kind") if k in doc])
