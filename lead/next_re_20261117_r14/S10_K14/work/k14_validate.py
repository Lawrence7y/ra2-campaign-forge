import os
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14"
rows = open(os.path.join(ROOT,"coverage_delta.tsv"),encoding="utf-8").read().rstrip("\n").split("\n")
assert len(rows)==1
c = rows[0].split("\t")
assert len(c)==9
assert c[0].upper()=="004D85D0"
assert c[1]=="S10"
assert c[4]=="[静态推断]"
assert c[5]=="EVIDENCE/PROOF_004D85D0.txt#004D85D0"
assert c[6]=="3" and c[7]=="0" and c[8]=="behavioral"
assert os.path.isfile(os.path.join(ROOT,c[5].split("#")[0]))
print("DELTA_ROWS=1 COLS=9 GRADE_OK PATH_OK NAME_KIND_OK")
