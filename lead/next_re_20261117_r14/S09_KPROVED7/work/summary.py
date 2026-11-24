"""Compact control-flow summary for all remaining candidates."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
# focus on candidates with size>0 and reasonably bounded extent (<3000)
for r in sorted(pool, key=lambda x: x['entry']):
    d = r['_det']
    if d['size'] > 3000: continue
    dis = r['_disasm']
    # summarize: count ret, distinct eax-const before ret, cmp imm, setxx, vt-write (mov [..],0x7e..)
    nret = sum(1 for l in dis if ' ret' in l or l.rstrip().endswith('\tret'))
    cmpimm = [l for l in dis if (' cmp ' in l) and ('0x' in l)]
    setxx = [l for l in dis if ' set' in l.split('\t')[-1][:5] or ' sete ' in l or ' setne ' in l or ' setg ' in l or ' setl ' in l]
    vtwrites = [l for l in dis if 'mov dword ptr' in l and '0x7' in l and '],eax' in l and ('0x7e' in l or '0x7f' in l)]
    print('%-10s %-22s sz=%3d ins=%3d ret=%d jcc=%d call=%d W=%d cmpImm=%d set=%d' % (
        r['entry'], r['name'][:22], d['size'], d['nins'], nret, d['jcc_distinct'], d['calls_distinct'],
        d['nwrites'], len(cmpimm), len(setxx)))
