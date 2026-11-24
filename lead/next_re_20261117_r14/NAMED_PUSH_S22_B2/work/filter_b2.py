# -*- coding: utf-8 -*-
"""NAMED-PUSH S22 B2: filter candidates.
subsystem == S22 AND p3b2_named == True, exclude fn_XXXXXXXX / sub_XXXXXXXX
pseudo-names, sort by entry ascending (int), take rows 19..36 (slice [18:36]).
"""
import csv, os, re

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"

FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

def main():
    with open(HITS, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    named = [r for r in rows if r["subsystem"] == "S22" and r["p3b2_named"] == "True"]
    def is_pseudo(n):
        return bool(FN.match(n) or SUB.match(n))
    filtered = [r for r in named if not is_pseudo(r["name"])]
    filtered.sort(key=lambda r: int(r["entry"], 16))
    b2 = filtered[18:36]
    print("S22 named=True rows:", len(named))
    print("pseudo (fn_/sub_) rows among named:", sum(1 for r in named if is_pseudo(r["name"])))
    print("after pseudo-exclusion:", len(filtered))
    print("B2 slice [18:36] count:", len(b2))
    print("entry\tsubsystem\tname\tgrade\tsize\tn_insn\tn_call\tn_site\tn_valid\tp3b2_named")
    for r in b2:
        print("\t".join(r[k] for k in ("entry","subsystem","name","grade","size","n_insn","n_call","n_site","n_valid","p3b2_named")))
    return b2

if __name__ == "__main__":
    main()
