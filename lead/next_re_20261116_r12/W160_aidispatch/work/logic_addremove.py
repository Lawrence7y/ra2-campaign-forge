"""Find functions that call LogicClass vector Add/Remove via this=0x87F778."""
import os,re,bisect
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}; S=sorted(D)
hits=[]
for a in S:
    l=D[a]
    if '0x87f778' in l.lower() and ('mov' in l and 'ecx' in l or 'push' in l):
        # next few instructions
        seq=[D[x] for x in S[bisect.bisect_left(S,a):bisect.bisect_left(S,a+0x60)]]
        calls=[s for s in seq if s.split('\t')[1]=='call']
        hits.append((a,l,calls[:3]))
for a,l,c in hits[:40]:
    print(f'{a:08X} {l}')
    for x in c: print('    ',x)
