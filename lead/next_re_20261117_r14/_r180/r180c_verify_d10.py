# -*- coding: utf-8 -*-
"""R180 复算：直查 r180b 两条可疑断言的真值 —— 篡改工况输出里的 sha 摘要是否真变了。"""
import hashlib,io,os,re,shutil,subprocess,sys,tempfile
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
PATCH=os.path.join(os.path.dirname(os.path.abspath(__file__)),'r180b_patched.py')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()
patched=rb(PATCH)
ck('V0 补丁文件存在且含 D10', b'D10 pointer' in patched, len(patched))

sbt=tempfile.mkdtemp(prefix='/tmp/r180c_')
sbroot=os.path.join(sbt,'root'); os.makedirs(sbroot)
for n in os.listdir(ROOT):
    if n in ('lead','_r160'): continue
    os.symlink(os.path.join(ROOT,n), os.path.join(sbroot,n))
os.makedirs(os.path.join(sbroot,'_r160'))
os.makedirs(os.path.join(sbroot,'lead'))
for n in os.listdir(os.path.join(ROOT,'lead')):
    if n=='next_re_20261117_r14': continue
    os.symlink(os.path.join(ROOT,'lead',n), os.path.join(sbroot,'lead',n))
sbtier=os.path.join(sbroot,'lead','next_re_20261117_r14'); os.makedirs(sbtier)
for n in os.listdir(TIER):
    if n in ('FACT_INDEX_CURRENT.md','R17_R131_FACTINDEX_V563'): continue
    os.symlink(os.path.join(TIER,n), os.path.join(sbtier,n))
shutil.copytree(os.path.join(TIER,'R17_R131_FACTINDEX_V563'), os.path.join(sbtier,'R17_R131_FACTINDEX_V563'))
sff=os.path.join(sbroot,'_r160','facts_floors.py'); open(sff,'wb').write(patched)
sptr=os.path.join(sbtier,'FACT_INDEX_CURRENT.md'); shutil.copy2(PTR,sptr)
def run(ff,*args):
    e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
    r=subprocess.run([sys.executable,ff]+list(args),cwd=ROOT,capture_output=True,text=True,env=e,timeout=180)
    return r.returncode,(r.stdout+r.stderr)
def d10lines(out): return [l.strip() for l in out.split('\n') if 'D10' in l]

good=io.open(sptr,encoding='utf-8',newline='').read()
gs=re.search(r'\| sha256 \| ([0-9a-f]{64}) \|',good).group(1)
real=sh(rb(os.path.join(TIER,'R17_R131_FACTINDEX_V563','FACT_INDEX.tsv')))
ck('V1 基线：指针 sha == 实物 sha', gs==real, (gs[:16],real[:16]))
rc,out=run(sff)
ck('V2 基线 exit 0', rc==0, rc)
base_d10=d10lines(out)
print('   基线 D10 行:',base_d10)
ck('V3 基线 D10 行含实物 sha 全文', any(gs in l for l in base_d10), [l[:60] for l in base_d10])

# 篡改：改最后 1 位
bs=gs[:-1]+('0' if gs[-1]!='0' else '1')
ck('V4 篡改值确实不同（比全文，不是前 16 位）', bs!=gs, (gs[-8:],bs[-8:]))
ck('V4b 前 16 位摘要对末位篡改不可见（S-667：这正是前 16 位判据失明的原因）',
   gs[:16]==bs[:16], (gs[:16],bs[:16]))
io.open(sptr,'w',encoding='utf-8',newline='').write(good.replace(gs,bs,1))
rc2,out2=run(sff)
t_d10=d10lines(out2)
print('   篡改后 D10 行（末 8 位对照）:',[l.replace(gs[:16],'<%s..%s>'%(gs[:8],gs[-8:])).replace(bs[:16],'<%s..%s>'%(bs[:8],bs[-8:])) for l in t_d10])
ck('V5 篡改后 exit 1', rc2==1, rc2)
ck('V6 篡改后 print 行显示篡改值全文；FAIL 行左值也是篡改值全文',
   any(('pointer sha=%s '%bs) in l for l in t_d10) and any(('pointer sha %s !='%bs) in l for l in t_d10),
   [l[:80] for l in t_d10])
ck('V7 篡改后 FAIL 行不再出现原值全文作左值（无基线残留）',
   not any(('pointer sha %s !='%gs) in l for l in t_d10), [l[:80] for l in t_d10 if 'FAIL' in l])
# 关键复核：原 r180b 打印的 detail 是 [l for l in out if 'D10' in l][:2]，若基线 D10 行先出现就会被取到
ck('V8 r180b 的 detail 取法（前 2 条含 D10 的行）在篡改工况下会先取到 print 行 ⇒ 摘要含原值',
   t_d10[0].startswith('D10 pointer sha=') or 'D10 pointer file' in t_d10[0],
   t_d10[0] if t_d10 else None)
shutil.rmtree(sbt,ignore_errors=True)
print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
