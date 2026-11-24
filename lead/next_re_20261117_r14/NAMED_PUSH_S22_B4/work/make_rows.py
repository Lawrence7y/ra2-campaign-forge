# -*- coding: utf-8 -*-
"""NAMED-PUSH S22 B4: generate b4_rows.json from hits_detail.tsv.
Filter: subsystem==S22 AND p3b2_named==True, exclude fn_XXXXXXXX / sub_XXXXXXXX
pseudo-names, sort by entry ascending. B1=[0:18], B2=[18:36], B3=[36:49]
already checked; B4 = slice [49:end] (end via env B4_END, default 62 -> 13 rows).
Read-only on target; writes only b4_rows.json in this work dir.
"""
import csv, os, re, json

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
HERE = os.path.dirname(os.path.abspath(__file__))
FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

with open(HITS, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
named = [r for r in rows if r["subsystem"] == "S22" and r["p3b2_named"] == "True"]
pseudo = [r for r in named if FN.match(r["name"]) or SUB.match(r["name"])]
filtered = [r for r in named if not (FN.match(r["name"]) or SUB.match(r["name"]))]
filtered.sort(key=lambda r: int(r["entry"], 16))
end = int(os.environ.get("B4_END", "62"))
sel = filtered[49:end]
for r in sel:
    r["entry"] = r["entry"].strip().upper()
    r["name"] = r["name"].strip()
    for k in ("size", "n_insn", "n_call", "n_site", "n_valid"):
        r[k] = int(r[k])
with open(os.path.join(HERE, "b4_rows.json"), "w", encoding="utf-8") as f:
    json.dump({"rows": sel}, f, ensure_ascii=False, indent=1)
print("named=%d pseudo=%d filtered=%d slice=[49:%d] -> %d rows" % (
    len(named), len(pseudo), len(filtered), end, len(sel)))
for r in sel:
    print(r["entry"], r["name"], r["size"])
