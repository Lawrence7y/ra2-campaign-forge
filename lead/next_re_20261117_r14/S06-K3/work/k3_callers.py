"""Resolve semantics of the 7 caller functions of 0x485020 and the INI-read helper 0x5276D0."""
from lib import *
import bisect
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
cov={}
with open(COV,encoding='utf-8') as f:
    next(f)
    for ln in f:
        q=ln.rstrip('\n').split('\t')
        if len(q)>=5: cov[q[0].upper()]=(q[1],q[2],q[3],q[4])
for e in ['005276D0','00424000','004DE000','004DE200','00568070','00685000','006D7A00','0070F950',
          '006D8DB0','006D97D0','00485100']:
    c=cov.get(e)
    print(f"{e}: atlas_size={atlas.get(int(e,16))} cov={c}")
