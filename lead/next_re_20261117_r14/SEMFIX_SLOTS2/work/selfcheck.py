#!/usr/bin/env python3
# Final self-check for SEMFIX-SLOTS2 delivery.
import os, csv
D=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS2"
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
EXPECT=["0047AE10","0065CDD0","0065D0D0","0065D190","004D82B0","004D5690","004DB260","00702D40","00706640","00708C30","004D94B0"]
FORBID=["未证","未定","弱信号","线索"]
errs=[]
rows=list(csv.reader(open(os.path.join(D,"coverage_delta.tsv"),encoding="utf-8"),delimiter="\t"))
hdr,data=rows[0],rows[1:]
if hdr!=["entry","subsystem","name","one_line_semantics","grade","evidence_path"]: errs.append("header mismatch: "+str(hdr))
if len(data)!=11: errs.append("data rows != 11: %d"%len(data))
got=[r[0] for r in data]
if got!=EXPECT: errs.append("entry set/order mismatch: "+str(got))
# disk names
disk={}
for line in open(COV,encoding="utf-8"):
    p=line.rstrip("\n").split("\t")
    if p and p[0] in EXPECT: disk[p[0]]=(p[1],p[2])
for r in data:
    e,sub,name,sem,grade,ev=r
    if disk.get(e,(sub,name))!=(sub,name): errs.append("%s name/sub mismatch disk=%s delta=%s"%(e,disk.get(e),(sub,name)))
    if grade!="[已证]": errs.append("%s grade=%s"%(e,grade))
    for w in FORBID:
        if w in sem: errs.append("%s semantics contains forbidden %r"%(e,w))
    if "（槽语义未证" in sem: errs.append("%s still placeholder"%e)
    # must carry tier + anchor
    if "③b" not in sem: errs.append("%s no tier"%e)
    if "+0x" not in sem: errs.append("%s no anchor"%e)
    if not os.path.exists(os.path.join(D,ev.replace("/",os.sep))): errs.append("%s evidence_path missing: %s"%(e,ev))
# forbidden word scan on whole semantics column already done; check EVIDENCE files count
evdir=os.path.join(D,"EVIDENCE")
anchors=[f for f in os.listdir(evdir) if f.startswith("ANCHOR_") and f.endswith(".txt") and f!="ANCHOR_SUMMARY.txt"]
if len(anchors)!=11: errs.append("anchor evidence files != 11: %d"%len(anchors))
prog=open(os.path.join(D,"PROGRESS.md"),encoding="utf-8").read().splitlines()
if len(prog)>60: errs.append("PROGRESS lines %d > 60"%len(prog))
print("SELF-CHECK:", "PASS" if not errs else "FAIL")
print("data rows:",len(data),"| grade [已证]:",sum(1 for r in data if r[4]=="[已证]"),"| forbidden hits:",sum(1 for r in data for w in FORBID if w in r[3]))
print("PROGRESS lines:",len(prog),"| anchor evidence:",len(anchors))
for e in errs: print("  ERR:",e)
