import os, sys, shutil, subprocess, tempfile, hashlib, json, re
ROOT='/home/t628/projects/ra2-campaign-forge'
SRC=ROOT+'/lead/next_re_20261117_r14'
A=1
RESULT=[]
def chk(n,c,x=''):
    global A
    print('  %s %-72s %s'%('PASS' if c else 'FAIL',n,x)); A+=1
    RESULT.append((n,c))

SBX='/tmp/r140_sbx'
if os.path.exists(SBX): shutil.rmtree(SBX)
os.makedirs(SBX)
# mirror required tree
for rel in ('lead/next_re_20261117_r14',):
    shutil.copytree(os.path.join(ROOT, rel), os.path.join(SBX, rel), symlinks=False,
                    ignore=shutil.ignore_patterns('__pycache__'))
for p in ('lead/LEAD_LOCK','lead/GOAL_THREE_TARGETS_20261018.md'):
    os.makedirs(os.path.dirname(os.path.join(SBX,p)), exist_ok=True)
    shutil.copy2(os.path.join(ROOT,p), os.path.join(SBX,p))

GATE=os.path.join(SBX,'lead/next_re_20261117_r14/check_disc.py')
def run():
    r=subprocess.run([sys.executable,'check_disc.py'], cwd=os.path.dirname(GATE),
                     capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout+r.stderr

rc,out=run()
chk('P0 baseline in sandbox exits 0', rc==0, 'rc=%d'%rc)

# N1: delete section 2.144 body entirely -> C15/C16 must FAIL
cp=open(GATE,encoding='utf-8').read()
rcf=os.path.join(SBX,'lead/next_re_20261117_r14/R14_COMMON.md')
orig=open(rcf,encoding='utf-8').read()
chk('sandbox R14_COMMON has 2.144', '## 2.144' in orig)
sec_start=orig.index('## 2.144')
stripped=orig[:sec_start]
open(rcf,'w',encoding='utf-8').write(stripped)
rc1,out1=run()
chk('N1 removing 2.144 makes the gate FAIL', rc1!=0, 'rc=%d'%rc1)
chk('N1 failure names the missing/absent section 144', '144' in out1, [l for l in out1.split('\n') if 'C15' in l or 'C16' in l][:2])
open(rcf,'w',encoding='utf-8').write(orig)
rc,out=run(); chk('P1 restore -> exit 0', rc==0)

# N2: hollow out 2.144 but keep the heading -> C16 floor must FAIL
hollow=orig[:sec_start] + '## 2.144 【R140】hollow\n'
open(rcf,'w',encoding='utf-8').write(hollow)
rc2,out2=run()
chk('N2 hollowing 2.144 (heading kept) FAILs on the C16 floor', rc2!=0, 'rc=%d'%rc2)
chk('N2 the failure is specifically C16 and names 144', 'C16' in out2 and '144' in out2,
    [l for l in out2.split('\n') if 'C16' in l and '144' in l][:2])
open(rcf,'w',encoding='utf-8').write(orig)
rc,out=run(); chk('P2 restore -> exit 0', rc==0)

# N3: revert GATE_VER only in DISC_RECHECK (not in check_disc.py) -> C7 must FAIL
drf=os.path.join(SBX,'lead/next_re_20261117_r14/DISC_RECHECK.tsv')
dro=open(drf,encoding='utf-8').read()
drn=dro.replace("grep=(?m)^GATE_VER = 'R140'","grep=(?m)^GATE_VER = 'R139'")
chk('N3 mutation actually applied', drn!=dro)
open(drf,'w',encoding='utf-8').write(drn)
rc3,out3=run()
chk('N3 stale row 20 makes the gate FAIL', rc3!=0, 'rc=%d'%rc3)
chk('N3 failure is C7 (live row pins the old version)', 'C7' in out3, [l for l in out3.split('\n') if l.startswith('  FAIL')][:2])
open(drf,'w',encoding='utf-8').write(dro)
rc,out=run(); chk('P3 restore -> exit 0', rc==0)

# N4: tamper the frozen registry WITHOUT re-pinning -> must report TAMPERED
duf=os.path.join(SBX,'lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv')
duo=open(duf,encoding='utf-8').read()
open(duf,'w',encoding='utf-8').write(duo+'\n')
rc4,out4=run()
chk('N4 frozen registry tamper makes the gate FAIL', rc4!=0, 'rc=%d'%rc4)
chk('N4 failure names C11 TAMPERED', 'TAMPERED' in out4, [l for l in out4.split('\n') if 'TAMPERED' in l][:1])
open(duf,'w',encoding='utf-8').write(duo)
rc,out=run(); chk('P4 restore -> exit 0', rc==0)

# N5: change a floor value in C16_FLOORS without re-pinning the sha -> C16d FAIL
cpn=cp.replace('144: 4010','144: 200')
chk('N5 mutation applied', cpn!=cp)
open(GATE,'w',encoding='utf-8').write(cpn)
rc5,out5=run()
chk('N5 lowering a floor without re-pin FAILs on C16d', rc5!=0, 'rc=%d'%rc5)
chk('N5 failure names C16d', 'C16d' in out5, [l for l in out5.split('\n') if 'C16d' in l][:1])
open(GATE,'w',encoding='utf-8').write(cp)
rc,out=run(); chk('P5 restore -> exit 0', rc==0)

# N6: pair control -- re-pin the sha as well, then N5-style edit is NOT caught (honest boundary)
cpn2=cp.replace('144: 4010','144: 200')
d=dict((int(a),int(b)) for a,b in re.findall(r'(\d+)\s*:\s*(\d+)', re.search(r'C16_FLOORS = \{(.*?)\n\}', cpn2, re.S).group(1)))
norm='\n'.join('%d:%d'%(k,d[k]) for k in sorted(d))
sh=hashlib.sha256(norm.encode()).hexdigest()
cpn2=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sh,cpn2,count=1)
open(GATE,'w',encoding='utf-8').write(cpn2)
rc6,out6=run()
chk('N6 (pair control) lowering floor AND re-pinning sha is NOT caught -- honest boundary',
    rc6==0, 'rc=%d'%rc6)
open(GATE,'w',encoding='utf-8').write(cp)
rc,out=run(); chk('P6 restore -> exit 0', rc==0)

shutil.rmtree(SBX)
print()
print('CONTROLS: %d  PASS=%d  FAIL=%d' % (len(RESULT), sum(1 for _,c in RESULT if c), sum(1 for _,c in RESULT if not c)))
json.dump([(n,c) for n,c in RESULT], open('/home/t628/projects/ra2-campaign-forge/_r140/r141_controls.json','w'), indent=1)
sys.exit(0 if all(c for _,c in RESULT) else 1)
