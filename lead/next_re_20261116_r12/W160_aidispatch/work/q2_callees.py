"""Check which 0x55D360 direct callees touch object arrays and which slot they call."""
import os, bisect, re
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}
S=sorted(D)
# direct call targets from 0x55D360 range [0x55D360,0x55D360+2940)
targets=set()
for a in S:
    if 0x55D360<=a<0x55D360+2940:
        m=re.search(r'\tcall\t0x([0-9a-f]+)\t',D[a])
        if m: targets.add(int(m.group(1),16))
arrs=['8B4118','8B410C','A83DF8','A83DEC','A8EB50','A8EB44','A8E3A0','A8E394','A8ED50','A8ED44']
print('callees',len(targets))
for t in sorted(targets):
    # find extent: next atlas entry if available; use +0x2000 window heuristic cap on calls
    seq=[a for a in S if t<=a<t+0x3000]
    hits=[(hex(a),D[a]) for a in seq if any(x in D[a] for x in arrs)]
    sl=[(hex(a),D[a]) for a in seq if D[a].split('\t')[1]=='call' and '+ 0x5c]' in D[a]]
    if hits or sl:
        print(f'\n{t:08X}: arrayhits={len(hits)} slot5c={len(sl)}')
        for h in hits[:8]: print('  A',h[1])
        for h in sl[:8]: print('  C',h[1])
