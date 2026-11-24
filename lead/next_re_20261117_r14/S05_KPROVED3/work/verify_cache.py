"""Verify the reused disasm cache against SURVEY baseline (independent channel:
full .text capstone skipdata sweep). Card S05-KPROVED3."""
import sys, pickle, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work")
from pe_helpers import *

D = pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
insns, call_sites, addr2i = D['insns'], D['call_sites'], D['addr2i']
print("insns (capstone skipdata) =", len(insns))
e8_boundary = sum(1 for a,sz,m,o,b in insns if len(b)>=5 and b[0]==0xE8 and sz==5)
print("E8@boundary =", e8_boundary)
print("distinct E8 targets =", len(call_sites))
# independent raw byte count of E8 (not instruction-boundary)
raw = bytes_at(TEXT_LO, TEXT_HI-TEXT_LO)
print("raw E8 bytes =", sum(1 for i in range(len(raw)-4) if raw[i]==0xE8))
# baseline from SURVEY_RING24: 1,392,592 insns / 68,253 E8@boundary / 6,728 distinct
ok = (len(insns)==1392592 and e8_boundary==68253 and len(call_sites)==6728)
print("BASELINE_MATCH =", ok)
assert ok, "cache does not match SURVEY baseline"
