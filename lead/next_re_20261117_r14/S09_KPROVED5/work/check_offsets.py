"""Report every key_offset in CONTRACT_3B vs DISASM, with the actual instruction lines
near each offset, so mismatches can be corrected to exact entry-relative values."""
import csv, re
from pathlib import Path
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
EV=OUT/'EVIDENCE'
contract={}
with (EV/'CONTRACT_3B.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): contract[r['entry']]=r
for e,r in contract.items():
    dis=(EV/('DISASM_%s.txt'%e)).read_text(encoding='utf-8').splitlines()
    offs=[int(x,16) for x in re.findall(r'\+0x([0-9A-Fa-f]{4})',r['key_offsets'])]
    present=set(int(re.search(r'\+0x([0-9A-Fa-f]{4})',ln).group(1),16) for ln in dis if re.search(r'\+0x([0-9A-Fa-f]{4})',ln))
    miss=[o for o in offs if o not in present]
    print('===',e,'missing:',['+0x%04X'%m for m in miss])
    if miss:
        for m in miss:
            nearby=[ln for ln in dis if re.search(r'\+0x([0-9A-Fa-f]{4})',ln) and abs(int(re.search(r'\+0x([0-9A-Fa-f]{4})',ln).group(1),16)-m)<=3]
            for ln in nearby: print('   ',ln)
