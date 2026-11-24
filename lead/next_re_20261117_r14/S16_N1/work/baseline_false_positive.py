# -*- coding: utf-8 -*-
# work/baseline_false_positive.py -- baseline for naming criteria
# Question: if we pick equally many arbitrary S16 sub_ entries and apply the SAME criteria,
# how many would falsely pass as "named"?
import sys,os,re
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_N1\work")
import re_tools as R
# YRpp address bindings for the 5 target addresses (source channel B)
YRPP_BIND = {
 0x0053A0E0:"Ion::HasDeferment",
 0x0053AE50:"PsyDom::Start",
 0x006CE2C0:"TimerStruct::StartIfEmpty",
 0x006CE270:"LocomotionClass::AddRef2",
}
# all 17 S16 sub_ entries
SUBS=[0x00430BA0,0x00539EB0,0x0053A0E0,0x0053A6C0,0x0053AE00,0x0053AE50,0x0053B410,
      0x0053D8E0,0x0053DDA0,0x0065E660,0x006CE240,0x006CE270,0x006CE280,0x006CE2C0,
      0x006CE2D0,0x006CE320,0x0071AB60]
# channel B test: does YRpp source bind this address?
def yrpp_bind(a): return YRPP_BIND.get(a)
# channel A test: signature unique full-.text (only for Pause)
SIG_UNIQUE={0x006CE280}
passed=[]
for a in SUBS:
    reasons=[]
    if a in YRPP_BIND: reasons.append('YRpp-address-binding')
    if a in SIG_UNIQUE: reasons.append('unique-byte-signature')
    if reasons: passed.append((a,reasons))
print("S16 sub_ pool N=",len(SUBS))
print("criterion pass count=",len(passed),"=",passed)
# baseline 1: random pick of 5 among 17 -> expected false positives
# positive set size K=5 (4 with yrpp binding + 1 with sig unique, which overlaps 0? Pause not in yrpp binding so 5 distinct)
# if choose sample of 5 uniformly at random from all 17, expected # in pass set = 5*5/17
print("baseline(random 5 from 17, pass set 5): expected false hits = 5*5/17 = %.3f"%(5*5/17))
# baseline 2: pick 5 from the 14 non-audited sub_ (exclude 3 reused)
NONAUD=[a for a in SUBS if a not in (0x00539EB0,0x0053AE00,0x0053B410)]
ps=[a for a in NONAUD if a in YRPP_BIND or a in SIG_UNIQUE]
print("non-audited pool N=",len(NONAUD),"pass K=",len(ps))
print("baseline(random 5 from 14): expected false hits = 5*%d/%d = %.3f"%(len(ps),len(NONAUD),5*len(ps)/len(NONAUD)))
# baseline 3: YRpp address binding coverage in whole S16 atlas (90 entries)
# how many of the 90 S16 entries have a YRpp address binding? (approx by scanning all S16 coverage names)
cov=open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv",encoding='utf8').read().splitlines()[1:]
atl=set(x.split('\t')[0].lower() for x in open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv",encoding='utf8').read().splitlines()[1:] if x.strip())
s16=[x.split('\t') for x in cov if len(x.split('\t'))>=5 and x.split('\t')[1]=='S16' and x.split('\t')[0].lower() in atl]
# exact YRpp bindings across all S16 addresses -- extract from YRpp headers/docs via simple scan
yrpp_all=set()
for root,dirs,files in os.walk(r"D:\Project\ra2-campaign-forge\YRpp"):
  for f in files:
    if not f.lower().endswith(('.h','.html','.cpp')):continue
    try:s=open(os.path.join(root,f),encoding='utf8',errors='ignore').read()
    except:continue
    for m in re.finditer(r'0x([0-9A-Fa-f]{6})\b',s): yrpp_all.add(m.group(1).upper())
bound=[x for x in s16 if ('0'+x[0].upper()) in yrpp_all or x[0].upper() in yrpp_all]
print("S16 atlas entries with any YRpp address mention: %d/%d (%.1f%%)"%(len(bound),len(s16),100*len(bound)/len(s16)))
# positive-control: verify each of 4 YRpp bindings appears in at least 2 independent YRpp files (h + html), minus .mimosa copies
print("Yrpp binding file independence: see E02 raw dump (SuperClass.h + Documentation/*.html for 3/4; LocomotionClass.h + Doc for 1)")
