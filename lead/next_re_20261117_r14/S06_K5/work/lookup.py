
import csv,sys
from pathlib import Path
R=Path(r"D:\Project\ra2-campaign-forge")
COV=R/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=R/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
def rows(p): return list(csv.DictReader(open(p,encoding='utf-8',newline=''),delimiter='\t'))
cov={r['entry'].upper():r for r in rows(COV)}
atl={r['entry'].upper():r for r in rows(ATL)}
targets=['00483710','00483780','00487190','005FDD20','004838E0','00485020','0047C620','00487180','00487200']
for t in targets:
    c=cov.get(t); a=atl.get(t)
    print("=== "+t+" ===")
    print("  COV:", c)
    print("  ATL:", a)
print("\n--- atlas entries in 0x483700..0x483B00 ---")
for e,a in sorted(atl.items()):
    v=int(e,16)
    if 0x483700<=v<=0x483B00:
        c=cov.get(e)
        print(e,"size",a['size'],"grade",c['grade'] if c else '-',"name",(c['name'] if c else '-'))
