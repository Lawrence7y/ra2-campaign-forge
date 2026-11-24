# -*- coding: utf-8 -*-
"""NAMED-PUSH S05 B2 候选筛选：subsystem=S05 & p3b2_named=True，排除 fn_/sub_ 伪名，
按 entry 升序取第 19..36 个（1-indexed），落 b2_rows.json。"""
import csv, json, os, hashlib

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WORK = os.path.dirname(os.path.abspath(__file__))

# SHA256 自校验
h = hashlib.sha256()
with open(EXE, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("EXE SHA256 =", h.hexdigest().upper())
assert h.hexdigest().upper() == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

rows = []
with open(HITS, encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] == "S05" and row["p3b2_named"] == "True":
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):
                continue
            rows.append(row)
rows.sort(key=lambda x: int(x["entry"], 16))
print("named-real S05 total =", len(rows))
batch = rows[18:36]  # 第19..36
out = []
for i, r in enumerate(batch, 19):
    d = {"entry": r["entry"].strip().upper(), "subsystem": "S05", "name": r["name"],
         "grade": r["grade"], "size": int(r["size"]), "p3b2_named": r["p3b2_named"]}
    out.append(d)
    print(i, d["entry"], d["name"], "size=%d" % d["size"], "grade=%s" % d["grade"])

with open(os.path.join(WORK, "b2_rows.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote b2_rows.json (%d rows)" % len(out))
