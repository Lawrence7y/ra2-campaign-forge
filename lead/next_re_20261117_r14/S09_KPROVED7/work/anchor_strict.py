"""Strict anchor verification: each '+0xNN mnemonic' token in the 锚 section must
match the actual mnemonic at that offset in the EVIDENCE DISASM file (纪律7逐字符)."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
D = BASE + r'\S09_KPROVED7'
EV = D + r'\EVIDENCE'
rows=[l.rstrip('\n').split('\t') for l in open(D+r'\coverage_delta.tsv',encoding='utf-8')][1:]
fail=0
for p in rows:
    entry,sem=p[0],p[3]
    m=re.search(r'锚 (.*?)；④',sem)
    anchor=m.group(1)
    dis=open(EV+r'\DISASM_%s.txt'%entry,encoding='utf-8').read()
    # parse EVIDENCE offset->mnemonic: lines like +0x0004  8b5130  mov edx, ...
    off2mn={}
    for mm in re.finditer(r'\+0x([0-9A-Fa-f]{4})\s+[0-9a-f]+\s+(\S+)',dis):
        off2mn[int(mm.group(1),16)]=mm.group(2)
    for tok in anchor.split(' / '):
        ma=re.match(r'\+0x([0-9A-Fa-f]{2,4})\s+(\S+)',tok.strip())
        if not ma: 
            print('WARN unparsed token',entry,tok); continue
        off=int(ma.group(1),16); mnem=ma.group(2)
        actual=off2mn.get(off)
        if actual is None:
            print('FAIL no such offset',entry,'+0x%x'%off); fail+=1
        elif actual!=mnem:
            print('FAIL mnemonic mismatch',entry,'+0x%x'%off,'sem=',mnem,'evidence=',actual); fail+=1
print('strict anchor verify fails =',fail)
