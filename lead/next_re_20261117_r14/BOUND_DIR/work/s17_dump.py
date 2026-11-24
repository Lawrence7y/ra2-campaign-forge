# -*- coding: utf-8 -*-
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
rows = [r for r in list(csv.reader(open(COV, encoding="utf-8-sig"), delimiter="\t"))[1:] if len(r) >= 8]
s17 = [r for r in rows if r[1].strip() == "S17" and r[4].strip() == "[已证]" and "[未证]" not in r[3]]
print("S17 strict rows =", len(s17))
for r in s17:
    print("%s | %-46s | %s" % (r[0], r[2].strip()[:46], r[3][:150].replace("\t", " ")))
