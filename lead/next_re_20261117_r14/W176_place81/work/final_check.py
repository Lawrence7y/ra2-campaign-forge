import os, json, hashlib, subprocess, sys
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81"
need = ["PROGRESS.md","PROBE_TABLE.md","UNKNOWNS.md","DISAGREE.md","coverage_delta.tsv",
        r"EVIDENCE\T1_byte81_channelA.txt", r"EVIDENCE\T1_byte81_all.json",
        r"EVIDENCE\T1_byte81_channelB.txt", r"EVIDENCE\T1_byte81_by_function.txt",
        r"EVIDENCE\T1_disasm_0043F180.txt", r"EVIDENCE\T1_disasm_007014A0.txt",
        r"EVIDENCE\T1_disasm_005F4D30.txt", r"EVIDENCE\T1_disasm_005F4EC0.txt",
        r"EVIDENCE\T2_branchA_canplace1.txt", r"EVIDENCE\T2_branchB_cellfail.txt",
        r"EVIDENCE\T2_branchC_check_canplace2.txt", r"EVIDENCE\T2_branchC_failure_ret.txt",
        r"EVIDENCE\T2_cfg_mode1.txt", r"EVIDENCE\T2_cfg_mode3.txt",
        r"EVIDENCE\T3_overlap_causes.md"]
missing = [p for p in need if not os.path.isfile(os.path.join(BASE,p))]
print("missing", missing)
print("PROGRESS lines", sum(1 for _ in open(os.path.join(BASE,"PROGRESS.md"),encoding="utf-8")))
d = json.load(open(os.path.join(BASE,r"EVIDENCE\T1_byte81_all.json"),encoding="utf-8"))
h = d["hits"]
print("core1: total",len(h),"write",sum(x["write"] for x in h),"read",sum(x["read"] for x in h))
print("core1: w1", sum(x["size"]==1 for x in h), "w4", sum(x["size"]==4 for x in h))
# no ellipsis in key traces
for p in [r"EVIDENCE\T2_branchA_canplace1.txt",r"EVIDENCE\T2_branchB_cellfail.txt"]:
    txt=open(os.path.join(BASE,p),encoding="utf-8").read()
    print(p,"has ...", "..." in txt)
print("work scripts", len([f for f in os.listdir(os.path.join(BASE,"work")) if f.endswith(".py")]))
