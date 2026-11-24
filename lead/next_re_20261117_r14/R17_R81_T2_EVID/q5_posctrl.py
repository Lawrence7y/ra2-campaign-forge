#!/usr/bin/env python3
"""R44-T2-EVID Q5 正控：Python 独立实现（csv.DictReader + 独立分类，不复用 analyze_q2.py）。"""
import csv, os
TSV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R78_T1_RECLASS\files_excluded_prime.tsv"
ue = []
with open(TSV, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["label"] == "UNDECIDED" and "evidence" in r["rel"].lower():
            ue.append(r)
print("TOTAL=" + str(len(ue)))
g = {"stdout":0,"stderr":0,"_out":0,"report":0,"result":0,"OTHER":0}
for r in ue:
    bn = os.path.basename(r["rel"]).lower()
    if "stdout" in bn: g["stdout"]+=1
    elif "stderr" in bn: g["stderr"]+=1
    elif "_out" in bn: g["_out"]+=1
    elif "report" in bn: g["report"]+=1
    elif "result" in bn: g["result"]+=1
    else: g["OTHER"]+=1
for k in ["stdout","stderr","_out","report","result","OTHER"]:
    print(f"{k}={g[k]}")
