"""Reclassify channel B W/R properly and produce final census counts for both channels."""
import re, os, capstone
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"
LOG=os.path.join(OUT,"ghidra_W170Dump.log")

def classify(s):
    low=s.lower()
    m=re.search(r"\b(cmp|test|mov|add|sub|inc|dec|and|or|xor|not|neg|shl|shr|sal|sar)\b",low)
    if not m: return "?"
    op=m.group(1)
    if op in ("cmp","test"): return "R"
    if op=="mov":
        idx=low.find("byte ptr")
        comma=low.find(",")
        return "W" if (comma>=0 and idx<comma) else "R"
    return "RMW"

inB=False; recs=[]
for line in open(LOG,encoding="utf-8",errors="replace"):
    if "CHANNEL B" in line: inB=True; continue
    if not inB: continue
    if "insns=" in line: continue
    mm=re.search(r">\s+([0-9a-f]{8})\s+(.*?)\s{2,}([WR])\s+([0-9a-f]+)\s",line)
    if mm:
        va=int(mm.group(1),16); s=mm.group(2).strip()
        recs.append((va,s,classify(s),mm.group(3),mm.group(4)))
from collections import Counter
cnt=Counter(r[2] for r in recs)
print("channel B (Ghidra) object hits:",len(recs),"classification:",dict(cnt))
W=sum(1 for r in recs if r[2] in ("W","RMW"))
R=sum(1 for r in recs if r[2] in ("R","RMW"))
print("channel B writes(incl RMW)=",W,"reads(incl RMW)=",R)
# list writes
print("--- Ghidra channel B writes ---")
for va,s,c,_,_ in recs:
    if c in ("W","RMW"): print("  %08X %s"%(va,s))
# channel A counts from census (recompute properly by re-reading sections)
lines=open(os.path.join(OUT,"Q2_plus81_census.txt"),encoding="utf-8").read().splitlines()
sec=None; Aw=[]; Ar=[]; Aall=[]
for ln in lines:
    if ln.startswith("=== WRITES"): sec="W"; continue
    if ln.startswith("=== READS"): sec="R"; continue
    if ln.startswith("=== ALL"): sec="A"; continue
    mm=re.match(r"\s+([0-9A-F]{8})\s+(.*?)\s+base=",ln)
    if mm and sec in ("W","R"):
        (Aw if sec=="W" else Ar).append((int(mm.group(1),16),mm.group(2).strip()))
print("\nchannel A writes=",len(Aw),"reads=",len(Ar))
# object vs stack
def isstk(s): return bool(re.search(r"\[(esp|ebp)\s*\+\s*0x81\]",s,re.I))
print("channel A object writes=",sum(1 for _,s in Aw if not isstk(s)),"stack writes=",sum(1 for _,s in Aw if isstk(s)))
print("channel A object reads =",sum(1 for _,s in Ar if not isstk(s)),"stack reads =",sum(1 for _,s in Ar if isstk(s)))
