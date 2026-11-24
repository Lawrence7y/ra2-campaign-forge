"""Do the 1,392,592 instruction-start VAs (a2_sites.bounds) exist as object content anywhere else?
Test: for each bound VA, is there byte-bearing EVIDENCE that records the instruction at it?
Probe file: AUDIT_PROVED_UNNAMED/_audit/DIS/*.txt (address + instruction bytes + mnemonic)."""
import json, re, os, glob
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

bounds = json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json','rb').read().decode('utf-8'))['bounds']
bs = set(bounds)
P('bounds', len(bounds))

# collect every "VA  bytes  mnemonic" row in the whole tree's EVIDENCE dirs (small text files only)
pat = re.compile(r'^(?:\s*)([0-9A-F]{8})\s+((?:[0-9a-fA-F]{2}){2,20})\s+([a-z][a-z0-9.]{1,10})\b')
seen = {}
scanned = 0
for p in glob.glob(BASE + r'\**\*.txt', recursive=True):
    try:
        if os.path.getsize(p) > 4_000_000: continue
        t = open(p, 'rb').read().decode('utf-8', 'replace')
    except Exception:
        continue
    scanned += 1
    for ln in t.splitlines():
        m = pat.match(ln)
        if m and m.group(1) in bs and m.group(1) not in seen:
            seen[m.group(1)] = (p.replace(BASE + '\\', ''), m.group(2), m.group(3))
P('text files scanned', scanned)
P('distinct a2_sites bounds covered by a byte-bearing disasm row:', len(seen), '/', len(bounds),
  '(%.4f%%)' % (100*len(seen)/len(bounds)))
for k in list(seen)[:10]:
    P('   ', k, seen[k])
open(BASE + r'\R17_R95_T1_A2SITES\q4_covering.out','w',encoding='utf-8').write('\n'.join(LOG))
