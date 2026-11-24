"""Report YRpp-name coverage of C01 slice and dump sample for manual verification."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ATLAS = os.path.join(PROJECT, 'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB = chr(9)
with open(ATLAS, encoding='utf-8', errors='replace') as f:
    lines = f.read().splitlines()
sl = lines[1:1293]
entries = [int(r.split(TAB)[0],16) for r in sl]
yrpp = json.load(open(os.path.join(HERE,'yrpp_names.json'),encoding='utf-8'))
named = [e for e in entries if str(e) in yrpp or hex(e) in yrpp or ('%08X'%e) in yrpp]
# build exact int-key dict
yin = {}
for k,v in yrpp.items():
    yin[int(k,16) if k.lower().startswith('0x') else int(k)] = v
named = [e for e in entries if e in yin]
print('slice size', len(entries), 'named by YRpp', len(named))
for e in named:
    v = yin[e]
    for r in v:
        print('%08X' % e, r['full'], '|', r['decl'][:80], '|', r['file'], r['line'])
