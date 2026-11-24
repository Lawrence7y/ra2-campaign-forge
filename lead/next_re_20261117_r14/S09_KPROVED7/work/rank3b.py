"""Refined ③b ranking: for each candidate compute distinct direct-call targets that
sit in DIFFERENT jcc gate branches, guarded-write+bool-return, and clamp+return.
Flag M4 risk when multiple gates funnel into same call target."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
cov=open(BASE+r'\COVERAGE\coverage.tsv',encoding='utf-8'); cov.readline(); dn={}
for line in cov:
    p=line.rstrip('\n').split('\t')
    if len(p)>=5: dn[p[0]]=p[2]
cov.close()
for r in sorted(pool,key=lambda x:x['entry']):
    d=r['_det']
    if d['size']>3000: continue
    txt='\n'.join(r['_disasm'])
    # direct call targets
    calls=[]
    for l in r['_disasm']:
        if ' call ' in l and ('0x' in l):
            calls.append(l.split('call',1)[1].strip())
    dcalls=set(calls)
    # gate count = internal jcc targets
    gates=d['jcc_distinct']
    # bool return
    boolret = ('xor eax, eax' in txt and ('mov eax, 1' in txt or 'mov al, 1' in txt))
    setcc = ('sete al' in txt or 'setne al' in txt)
    clamp = ('dec eax' in txt and 'cmp edx, eax' in txt)
    if gates>=2 or boolret or setcc:
        print('%-10s %-22s g=%d dcalls=%d W=%d bool=%s setcc=%s clamp=%s | %s' % (
            r['entry'], dn.get(r['entry'],r['name'])[:22], gates, len(dcalls), d['nwrites'],
            boolret, setcc, clamp, sorted(dcalls)[:6]))
