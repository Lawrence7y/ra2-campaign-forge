# -*- coding: utf-8 -*-
"""_kd_selftest.py -- negative/positive control fixtures for the semantic detector.

Every fixture is an in-memory SOURCE STRING only: no file outside the write
domain is created, no fixture is executed, no game binary / process is touched.
The detector's analyse() is imported and called directly on the bytes.
"""
import importlib.util
import json
import sys
from pathlib import Path

WD = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_kd_detect", WD / "_kd_detect.py")
kd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd)

# name, expected verdict, source
FIX = []

# ---- NEGATIVE CONTROLS: legal aggregates -----------------------------------
FIX.append(("N1_all_AND_over_k_tokens", "LEGAL_AGGREGATE", '''
def main():
    words = ("外推", "卡顿不存在")
    body = "正文"
    if not all(word in body for word in words):
        print("FAIL [1]")
        return 1
    print("PASS")
    return 0
'''))

FIX.append(("N2_all_bound_bool_list", "LEGAL_AGGREGATE", '''
def main():
    words = ("历史数字", "1681")
    present = [word in body for word in words]
    if not all(present):
        print("FAIL")
        return 1
    print("PASS")
    return 0
'''))

FIX.append(("N3_any_over_samples_single_literal", "LEGAL_AGGREGATE", '''
def main():
    bodies = ["a", "b", "c"]
    if not any("本次不授权" in body for body in bodies):
        print("FAIL")
        return 1
    print("PASS")
    return 0
'''))

FIX.append(("N4_count_preserving_sum", "LEGAL_AGGREGATE", '''
def main():
    words = ("A", "B", "C")
    hits = [w for w in words if w in body]
    if len(hits) < 2:
        print("FAIL")
        return 1
    print("PASS hits=%d" % len(hits))
    return 0
'''))

FIX.append(("N5_OR_with_per_token_attribution", "LEGAL_AGGREGATE", '''
def main():
    words = ("外推", "卡顿不存在")
    hits = {}
    for word in words:
        hits[word] = word in body
        print("PER_TOKEN %s %s" % (word, hits[word]))
    if not any(word in body for word in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
'''))

FIX.append(("N6_no_any_at_all_d25_style", "LEGAL_AGGREGATE", '''
def main():
    ok = True
    if "本次不授权" not in body:
        ok = False
    if not ok:
        print("FAIL")
        return 1
    print("RESULT: PASS")
    return 0
'''))

# ---- POSITIVE CONTROLS: the required k->1bit shapes ------------------------
FIX.append(("P1_generator_any", "CONFIRMED_K1BIT", '''
def main():
    for number, title, keywords in (
        (6, "未背书", ("外推", "卡顿不存在")),
    ):
        if not any(keyword in body for body in bodies.get(title, [])
                   for keyword in keywords):
            print("FAIL")
            return 1
    print(f"PASS")
    return 0
'''))

FIX.append(("P2_bound_bool_list_any_Name", "CONFIRMED_K1BIT", '''
def main():
    requirements = ((4, "D 链处置", ("历史数字", "1681"), False),)
    for number, title, words, require_all in requirements:
        present = [word in body for word in words]
        if not (all(present) if require_all else any(present)):
            print("FAIL")
            return 1
    print("PASS")
    return 0
'''))

FIX.append(("P3_ternary_any_matches", "CONFIRMED_K1BIT", '''
def main():
    requirements = ((4, "冲突是否成立", ("互斥", "前提"), False),)
    for number, title, words, require_all in requirements:
        matches = [
            all(word in body for word in words) if require_all
            else any(word in body for word in words)
            for body in bodies
        ]
        if not any(matches):
            print("FAIL")
            return 1
    print("PASS")
    return 0
'''))

FIX.append(("P4_ok_bitand_and_argmin_carrier", "CONFIRMED_K1BIT", '''
import argparse
def classify_line(line, needles):
    pos = min((line.find(n) for n in needles if n in line), default=-1)
    return pos
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--needle", action="append", required=True)
    a = ap.parse_args()
    if not any(n in txt for n in a.needle):
        print("FAIL")
        return 1
    ok = True
    for rel, n, want in checks:
        good = (got == want)
        ok &= good
    print("SELF_TEST = %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1
'''))


def main():
    out = []
    passed = 0
    for name, want, src in FIX:
        r = kd.analyse(name, src.encode("utf-8"))
        got = r["verdict"]
        ok = (got == want)
        passed += ok
        out.append(dict(name=name, want=want, got=got, ok=ok,
                        has_k=r.get("has_k"), collapse=r.get("collapse"),
                        legal=r.get("legal"), output=r.get("output")))
        print("%-4s %-38s want=%-20s got=%-20s k=%s collapse=%s" % (
            "PASS" if ok else "FAIL", name, want, got, r.get("has_k"),
            [c["kind"] for c in r.get("collapse", [])]))
    res = dict(n=len(FIX), passed=passed, failed=len(FIX) - passed,
               negatives=sum(1 for x in out if x["want"] == "LEGAL_AGGREGATE"),
               positives=sum(1 for x in out if x["want"] == "CONFIRMED_K1BIT"),
               all_negatives_correct=all(
                   x["got"] == "LEGAL_AGGREGATE" for x in out
                   if x["want"] == "LEGAL_AGGREGATE"),
               all_positives_correct=all(
                   x["got"] == "CONFIRMED_K1BIT" for x in out
                   if x["want"] == "CONFIRMED_K1BIT"),
               rows=out)
    (WD / "_kd_selftest_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n=res["n"], passed=res["passed"], failed=res["failed"],
                          all_negatives_correct=res["all_negatives_correct"],
                          all_positives_correct=res["all_positives_correct"]),
                     ensure_ascii=False))
    print("WROTE", (WD / "_kd_selftest_out.json").as_posix())
    return 0 if res["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
