# -*- coding: utf-8 -*-
"""NAMED-PUSH S05 B3 候选筛选：subsystem=S05 & p3b2_named=True，排除 fn_/sub_ 伪名，
按 entry 升序取第 37..54 个（1-indexed），落 b3_rows.json。
结果：S05 named-real 共 37 行，故第 37..54 只落 1 行（第 37 行）。"""
import csv, json, os, hashlib

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WORK = os.path.dirname(os.path.abspath(__file__))

# SHA256 自校验（目标二进制指纹）
h = hashlib.sha256()
with open(EXE, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("EXE SHA256 =", h.hexdigest().upper())
assert h.hexdigest().upper() == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

# ---- 候选筛选（写进 REPORT.md 的同一命令）----
rows = []
with open(HITS, encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] == "S05" and row["p3b2_named"] == "True":
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):
                continue          # 排除地址式伪名（② 物理不可得）
            rows.append(row)
rows.sort(key=lambda x: int(x["entry"], 16))
print("named-real S05 total =", len(rows))
batch = rows[36:54]  # 第37..54个（1-indexed）；实际仅第37行存在

out = []
for i, r in enumerate(batch, 37):
    d = {"entry": r["entry"].strip().upper(), "subsystem": "S05", "name": r["name"],
         "grade": r["grade"], "size": int(r["size"]), "p3b2_named": r["p3b2_named"]}
    out.append(d)
    print(i, d["entry"], d["name"], "size=%d" % d["size"], "grade=%s" % d["grade"])

with open(os.path.join(WORK, "b3_rows.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote b3_rows.json (%d rows)" % len(out))
