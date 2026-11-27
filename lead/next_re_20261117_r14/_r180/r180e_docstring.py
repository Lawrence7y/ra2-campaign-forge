# -*- coding: utf-8 -*-
"""R180 补：facts_floors.py 的 docstring 检查项清单补上 D10（自述与实现对齐）。
先沙箱验证，再按写入纪律落生产。"""
import hashlib,io,os,shutil,subprocess,sys,tempfile,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
FF=os.path.join(ROOT,'_r160','facts_floors.py')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()

OLD_SHA16='fe996a5b72e852ee'
old=rb(FF)
ck('E1 生产 sha16 == r180d 写后实测值（硬闸）', sh(old)[:16]==OLD_SHA16, (sh(old)[:16],OLD_SHA16))
src=old.decode('utf-8')
ck('E2 D10 实现已在（本步只补自述）', '# ---- D10 [R180 新增]' in src)
OLD_LINE='  D9  **单一主指纹覆盖全部常量**（含 grade/EVID/EVIDB/字节/GATE 计数）。'
ck('E3 待补锚点唯一', src.count(OLD_LINE)==1)
NEW_LINE=(OLD_LINE+'\n'
 '  D10 **当前版指针**必须与本文件 CUR_SHA256/TOTAL_BYTES 及 CUR 实物 sha 一致。\n'
 '      （R180 新增：此前该指针在 check_disc / gate_runner / 本脚本三者中读取次数各 0，\n'
 '      静默漂移时三门全绿；判据是两条独立事实的相等，不是文本相似。）')
new=src.replace(OLD_LINE,NEW_LINE,1)
ck('E4 只新增 3 行、既有行一字未改',
   new.count('\n')==src.count('\n')+3, (src.count('\n'),new.count('\n')))
ck('E5 既有 pin 常量行未变',
   [l for l in new.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))]
   ==[l for l in src.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))])
ck('E6 D9 payload 不含 docstring ⇒ MASTER 不变（G3f 仍应 ok）',
   __import__('re').search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",new,__import__('re').M).group(1)
   ==__import__('re').search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",src,__import__('re').M).group(1))

# 沙箱：只换 facts_floors.py 一件（其余全软链到生产），验证 exit 0
sbt=tempfile.mkdtemp(prefix='/tmp/r180e_')
sbroot=os.path.join(sbt,'root'); os.makedirs(sbroot)
for n in os.listdir(ROOT):
    if n in ('lead','_r160'): continue
    os.symlink(os.path.join(ROOT,n), os.path.join(sbroot,n))
os.makedirs(os.path.join(sbroot,'_r160')); os.makedirs(os.path.join(sbroot,'lead'))
for n in os.listdir(os.path.join(ROOT,'lead')):
    os.symlink(os.path.join(ROOT,'lead',n), os.path.join(sbroot,'lead',n))
sff=os.path.join(sbroot,'_r160','facts_floors.py')
open(sff,'wb').write(new.encode('utf-8'))
e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
r=subprocess.run([sys.executable,sff],cwd=ROOT,capture_output=True,text=True,env=e,timeout=200)
out=r.stdout+r.stderr
ck('E7 沙箱（软链真实归档）exit 0', r.returncode==0, (r.returncode,[l.strip() for l in out.split('\n') if 'FAIL' in l][:3]))
ck('E8 沙箱输出仍含 D10 pointer 行', 'D10 pointer sha=' in out)
ck('E9 docstring 已含 D10 说明', 'D10 **当前版指针**' in new)

if Fl==0:
    ts=time.strftime('%Y%m%d_%H%M%S')
    bak=os.path.join(BL,'facts_floors.py.before_r180_docstring_%s.bak'%ts)
    with open(bak,'xb') as f: f.write(old)
    ck('E10 备份独占创建', os.path.exists(bak), bak)
    ck('E11 备份 == 写入前逐字节', rb(bak)==old)
    open(FF,'wb').write(new.encode('utf-8'))
    ck('E12 回读 sha == 新内容', sh(rb(FF))==sh(new.encode('utf-8')), (sh(rb(FF))[:16],sh(new.encode('utf-8'))[:16]))
    print('   生产新 sha256=%s bytes=%d'%(sh(rb(FF)),len(rb(FF))))
shutil.rmtree(sbt,ignore_errors=True)
print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
