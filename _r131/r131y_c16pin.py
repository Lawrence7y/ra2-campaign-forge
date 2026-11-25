#!/usr/bin/env python3
# R131 r131y: pin the new section 2.135 into C16_FLOORS (half-measure rule) + refresh
# C16_FLOORS_SHA256. Without this the new section silently gains a permanent no-check
# ticket -- the exact failure this repo has been bitten by repeatedly. Measured, not guessed.
import hashlib, io, json, os, re, subprocess, sys
R14='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE=os.path.join(R14,'check_disc.py'); COMMON=os.path.join(R14,'R14_COMMON.md')
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131y_pin.json'
A=[]
def chk(n,c,d=''):
    A.append({'assert':n,'ok':bool(c),'detail':d}); print(('PASS ' if c else 'FAIL ')+n+(' :: '+str(d) if d else ''))

rc=''.join(io.open(COMMON,encoding='utf-8').readlines() if False else io.open(COMMON,encoding='utf-8').read())
blocks={}; cur=None; buf=[]
for l in rc.split('\n'):
    m=re.match(r'^##\s+2\.(\d+)\b',l)
    if m:
        if cur is not None: blocks[cur]='\n'.join(buf)
        cur=int(m.group(1)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: blocks[cur]='\n'.join(buf)
def size(k): return len(blocks[k].encode('utf-8'))
NEW=135
chk('section 2.135 exists in R14_COMMON', NEW in blocks, sorted(blocks)[-3:])
raw=size(NEW); floor=raw//2
print('   2.135 body bytes = %d -> half = %d' % (raw, floor))
chk('the half-measure floor is > 0 and <= the body', 0 < floor <= raw, (raw, floor))

g=io.open(GATE,encoding='utf-8').read(); gsha0=hashlib.sha256(g.encode()).hexdigest(); gcr0=g.count('\r\n')
m=re.search(r'C16_FLOORS = \{(.*?)\n\}', g, re.S)
chk('found the C16_FLOORS literal', bool(m))
entry='\n    132: 5998, 133: 4747, 134: 941'
chk('the literal ends with the last pinned triple (132/133/134)', entry in m.group(1),
    m.group(1).strip().splitlines()[-1])
newg=g.replace(entry, '\n    132: 5998, 133: 4747, 134: 941, 135: %d'%floor, 1)
# recompute sha exactly the way the gate does
mm=re.search(r'C16_FLOORS = \{(.*?)\n\}', newg, re.S)
body=mm.group(1)
pairs=re.findall(r'(\d+)\s*:\s*(\d+)', body)
tbl={int(k):int(v) for k,v in pairs}
chk('table now has 129 entries', len(tbl)==129, len(tbl))
chk('entry 135 present with the measured half', tbl.get(NEW)==floor, tbl.get(NEW))
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
sha=hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('   new C16_FLOORS_SHA256 = %s' % sha)
old_sha=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", newg).group(1)
newg=newg.replace(old_sha, sha, 1)
chk('sha constant replaced with exactly one new value', newg.count(sha)==1)
newg=newg.replace("GATE_VER = 'R131'","GATE_VER = 'R131'",1)
try:
    io.open(GATE,'wb').write(newg.encode('utf-8'))
    p=subprocess.run([sys.executable,GATE],capture_output=True,text=True,timeout=600)
    out=p.stdout+p.stderr
    print(p.stdout[-1100:])
    chk('gate exits 0 after pinning',p.returncode==0,p.returncode)
    chk('C16 shows unpinned 0 and pinned 129',
        'pinned 129' in out and 'unpinned 0' in out,
        [l.strip() for l in out.splitlines() if 'C16 per-section' in l])
    chk('C16d pin reports OK', 'C16d floor-table pin' in out and '(OK)' in out,
        [l.strip() for l in out.splitlines() if 'C16d' in l])
    # SELF-ERROR S-208: the first version tested `'FAIL' not in out`, which matches the
    # NOTE text "gap(claims-none, can never FAIL)=12" -- a substring test on a word that
    # also appears inside explanatory prose. Must test the failure LINE PREFIX.
    bad_lines = [l for l in out.splitlines() if l.strip().startswith('FAIL ')]
    chk('no FAIL lines (testing the line prefix, not the substring)', not bad_lines,
        bad_lines[:3])
    ok = p.returncode==0
except Exception:
    io.open(GATE,'wb').write(g.encode('utf-8'))   # in-memory recovery only
    raise
if not ok:
    io.open(GATE,'wb').write(g.encode('utf-8'))
    print('   ROLLED BACK from memory')
res={'raw_bytes':raw,'floor':floor,'old_sha256':old_sha,'new_sha256':sha,
     'entries':len(tbl),'gate_sha_before':gsha0,'gate_sha_after':hashlib.sha256(io.open(GATE,'rb').read()).hexdigest(),
     'gate_cr_after':io.open(GATE,'rb').read().count(b'\r\n'),'ok':ok}
chk('gate CR stayed 0',res['gate_cr_after']==0,res['gate_cr_after'])
res['assertions']=A; res['summary']={'total':len(A),'pass':sum(1 for x in A if x['ok']),
  'fail':[x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'%(res['summary']['total'],res['summary']['pass'],len(res['summary']['fail'])))
json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
raise SystemExit(0 if res['summary']['fail']==[] and ok else 1)
