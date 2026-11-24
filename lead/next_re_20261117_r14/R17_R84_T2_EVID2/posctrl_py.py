#!/usr/bin/env python3
# Q5 正控 法1 (Python)：独立实现，计算 Q1 的 266 与 Q4 的 _audit 件数/字节
import csv, os
R=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
EP=os.path.join(R,"R17_R78_T1_RECLASS","files_excluded_prime.tsv")
VD=os.path.join(R,"R17_R81_T2_EVID","_verdicts.tsv")
CP=os.path.join(R,"R17_R78_T1_RECLASS","files_tier_Cprime.tsv")
def rows(p):
    with open(p,encoding="utf-8",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
# Q1: 1242(UNDECIDED & EVIDENCE, 大小写不敏感) - 976(已裁)
ep=rows(EP)
n1242=sum(1 for r in ep if r["label"]=="UNDECIDED" and "evidence" in r["rel"].lower())
vd=rows(VD)
n976=sum(1 for r in vd if r["verdict"] in ("对象抄本","过程输出"))
n_tie_by_diff=n1242-n976
n_tie_direct=sum(1 for r in vd if r["verdict"]=="无法判定")
n_tie_reason=sum(1 for r in vd if r["reason"]=="tie")
# Q4: Cprime 中 rel 含目录段 _audit
cp=rows(CP)
audit=[r for r in cp if "_audit" in r["rel"].replace("\\","/").split("/")]
ac=len(audit); ab=sum(int(r["bytes"]) for r in audit)
p1a=[r for r in audit if r["why"].startswith("P1a")]
pc=len(p1a); pb=sum(int(r["bytes"]) for r in p1a)
print("Q1: n1242=%d n976=%d diff=%d direct=%d reason_tie=%d"%(n1242,n976,n_tie_by_diff,n_tie_direct,n_tie_reason))
print("Q4: _audit count=%d bytes=%d P1a=%d P1abytes=%d pct_count=%.2f pct_bytes=%.2f"%(ac,ab,pc,pb,100*pc/ac,100*pb/ab))
