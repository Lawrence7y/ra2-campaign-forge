# -*- coding: utf-8 -*-
"""NAMED-PUSH S22 B3: filter candidates.
subsystem == S22 AND p3b2_named == True, exclude fn_XXXXXXXX / sub_XXXXXXXX
pseudo-names, sort by entry ascending (int). Subtract rows already covered by
NAMED_PUSH_S22_B1 (slice [0:18]) and NAMED_PUSH_S22_B2 (slice [18:36]); take
the remaining first 13 rows (slice [36:49]).
"""
import csv, re

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

def main():
    with open(HITS, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    named = [r for r in rows if r["subsystem"] == "S22" and r["p3b2_named"] == "True"]
    filtered = [r for r in named if not (FN.match(r["name"]) or SUB.match(r["name"]))]
    filtered.sort(key=lambda r: int(r["entry"], 16))
    b1 = filtered[0:18]
    b2 = filtered[18:36]
    b3 = filtered[36:49]
    print("S22 named=True rows:", len(named))
    print("pseudo (fn_/sub_) rows among named:", sum(1 for r in named if FN.match(r["name"]) or SUB.match(r["name"])))
    print("after pseudo-exclusion:", len(filtered))
    print("B1 [0:18]:", len(b1), "->", b1[0]["entry"], "..", b1[-1]["entry"])
    print("B2 [18:36]:", len(b2), "->", b2[0]["entry"], "..", b2[-1]["entry"])
    print("B3 [36:49]:", len(b3))
    print("entry\tsubsystem\tname\tgrade\tsize\tn_insn\tn_call\tn_site\tn_valid\tp3b2_named")
    for r in b3:
        print("\t".join(r[k] for k in ("entry","subsystem","name","grade","size","n_insn","n_call","n_site","n_valid","p3b2_named")))
    return b3

if __name__ == "__main__":
    main()
