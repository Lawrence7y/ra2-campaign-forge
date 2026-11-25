#!/usr/bin/env python3
# R131 r131z: negative controls for the C16 re-pin of section 2.135.
# A pin that cannot fail is not a pin. Each control mutates the gate, requires FAIL with
# the expected line, and restores from MEMORY only (S-203).
import hashlib, io, json, os, re, subprocess, sys
R14='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE=os.path.join(R14,'check_disc.py')
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131z_c16ctrl.json'
ORIG=io.open(GATE,'rb').read(); ORIG_SHA=hashlib.sha256(ORIG).hexdigest()
A=[]
def chk(n,c,d=''):
    A.append({'assert':n,'ok':bool(c),'detail':d}); print(('PASS ' if c else 'FAIL ')+n+(' :: '+str(d) if d else ''))
def run():
    p=subprocess.run([sys.executable,GATE],capture_output=True,text=True,timeout=600)
    return p.returncode,p.stdout+p.stderr
def mutate(old,new):
    src=ORIG.decode('utf-8')
    assert old in src, old[:50]
    try:
        io.open(GATE,'wb').write(src.replace(old,new,1).encode('utf-8'))
        return run()
    finally:
        io.open(GATE,'wb').write(ORIG)
        assert hashlib.sha256(io.open(GATE,'rb').read()).hexdigest()==ORIG_SHA
def fails_in(out): return [l.strip() for l in out.splitlines() if l.strip().startswith('FAIL ')]

R={}
rc,out=run(); R['P0']=rc
chk('P0 baseline gate is green with the 2.135 pin in place', rc==0 and 'pinned 129' in out, rc)

# P1: lower the 2.135 floor below the real body -> must still pass (floor is a floor)
rc,out=mutate('134: 941, 135: 3059','134: 941, 135: 1')
R['P1']={'rc':rc,'fails':fails_in(out)[:3]}
chk('P1 lowering the 2.135 floor to 1 must be caught by the sha guard (C16d)',
    rc==1 and any('C16d' in f for f in fails_in(out)), fails_in(out)[:2])

# P2: raise the floor ABOVE the body -> hollowed section must FAIL on C16
rc,out=mutate('134: 941, 135: 3059','134: 941, 135: 99999')
chk('P2 floor above the body FAILs (C16 hollow or C16d tampered)',
    rc==1 and any(('C16' in f) for f in fails_in(out)), fails_in(out)[:3])
R['P2']=rc

# P3: delete the 135 entry entirely -> unpinned section must FAIL (C16b, 1 > max? no: max 2)
rc,out=mutate('134: 941, 135: 3059','134: 941')
R['P3']={'rc':rc,'fails':fails_in(out)[:4]}
print('   P3 fails:', fails_in(out)[:4])
chk('P3 deleting the 135 entry leaves 1 unpinned section (within the cap of 2) so only the '
    'sha guard fires -- which is exactly the loudness required',
    rc==1 and any('C16d' in f for f in fails_in(out)), fails_in(out)[:2])

# P4: hollow out the BODY of 2.135 in R14_COMMON (not in the gate -- S-209: the first
# version applied the body regex to the gate source, which of course has no such heading,
# and then died on m.start()).
COMMON=os.path.join(R14,'R14_COMMON.md')
cb=io.open(COMMON,'rb').read(); csha=hashlib.sha256(cb).hexdigest(); ccr=cb.count(b'\r\n')
csrc=cb.decode('utf-8')
m=re.search(r'(## 2\.135\n)(.*?)(\n## |\Z)', csrc, re.S)
chk('found the 2.135 body block inside R14_COMMON.md', bool(m),
    'regex ran against R14_COMMON, not against the gate')
chk('the 2.135 body block is the last section (ends at EOF)', bool(m) and m.group(3)=='',
    repr(m.group(3)) if m else None)
if m:
    try:
        hollow=(csrc[:m.start(2)]+'X'+csrc[m.end(2):]).encode('utf-8')
        io.open(COMMON,'wb').write(hollow)
        rc,out=run()
        R['P4']={'rc':rc,'fails':fails_in(out)[:3]}
        chk('P4 hollowing out the 2.135 body makes the gate FAIL on C16',
            rc==1 and any('hollowed out' in f for f in fails_in(out)), fails_in(out)[:2])
    finally:
        io.open(COMMON,'wb').write(cb)
        nb=io.open(COMMON,'rb').read()
        chk('P4b R14_COMMON restored byte-identically from memory',
            hashlib.sha256(nb).hexdigest()==csha and nb.count(b'\r\n')==ccr)

# P5: restore + final green
rc,out=run(); R['P5']=rc
chk('P5 gate bytes identical to the pinned baseline',
    hashlib.sha256(io.open(GATE,'rb').read()).hexdigest()==ORIG_SHA)
chk('P5b final run green', rc==0 and 'pinned 129' in out and 'unpinned 0' in out, rc)
chk('P5c CR of every touched file still at baseline',
    io.open(GATE,'rb').read().count(b'\r\n')==0
    and io.open(os.path.join(R14,'R14_COMMON.md'),'rb').read().count(b'\r\n')==1081)
R['gate_sha']=ORIG_SHA
R['assertions']=A; R['summary']={'total':len(A),'pass':sum(1 for x in A if x['ok']),
  'fail':[x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'%(R['summary']['total'],R['summary']['pass'],len(R['summary']['fail'])))
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
