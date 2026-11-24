"""Final comprehensive ③b signal scan over all 59 remaining candidates.
Looks for: sbb/setcc/xor-based returns, error-code constants, multiple distinct
call targets gated by distinct jcc, and any loop with in-body nonstack write."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
for r in sorted(pool,key=lambda x:x['entry']):
    d=r['_det']
    if d['size']>3000: continue
    L=r['_disasm']; txt='\n'.join(L)
    sig=[]
    if ' sbb ' in txt: sig.append('sbb')
    if 'sete al' in txt or 'setne al' in txt or 'setg al' in txt or 'setl al' in txt or 'seta al' in txt or 'setb al' in txt: sig.append('setcc')
    # distinct direct-call targets
    dc=set()
    for l in L:
        if ' call ' in l:
            t=l.split('call',1)[1].strip()
            dc.add(t)
    # cmp reg, imm gates count
    gates=sum(1 for l in L if (' cmp ' in l) and ('0x' in l))
    if sig or gates>=3 or len(dc)>=3:
        print('%-10s %-22s g=%d dc=%d W=%d sig=%s | %s' % (
            r['entry'], r['name'][:22], gates, len(dc), d['nwrites'], ','.join(sig), sorted(dc)[:5]))
