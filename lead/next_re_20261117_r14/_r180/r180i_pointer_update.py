# -*- coding: utf-8 -*-
"""R180：指针文件自述已过期两处 —— (1) 声明轮次 R179；(2) 「本文件不是门禁」边界
（D10 落地后已被 facts_floors 实读）。按写入纪律改正。"""
import hashlib,io,os,sys,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()
old=rb(PTR); src=old.decode('utf-8')
ck('P1 旧指针 sha256 == r180a 实测 ad5c1db9…', sh(old).startswith('ad5c1db9'), sh(old))
ck('P2 旧 CR == 0', old.count(b'\r')==0)

o1='| 声明轮次 | R179 |'
n1='| 声明轮次 | R180 |'
ck('P3 声明轮次锚点唯一', src.count(o1)==1)
s1=src.replace(o1,n1,1)

o2="""- 本文件**不是**门禁。守门脚本是 `_r160/facts_floors.py`（D0 已钉 V563 的 sha256）；
  两者若不一致，**以 facts_floors.py 的 D0 为准**（它每次运行都会实测 sha256，
  本文件只是静态文本）。"""
n2="""- 本文件**已被门禁读取**（R180 起）：`_r160/facts_floors.py` 的 **D10** 每轮比对本文件的
  sha256 / 字节数与 `CUR_SHA256` / `TOTAL_BYTES` 及台账**现盘实测** sha256，任一项不等即 FAIL。
  ⇒ R180 之前「本文件不是门禁、读不到就跳过」的旧边界**已作废**；现若本文件与本文件正文
  互相矛盾，`facts_floors.py` 会红，不再是「以 D0 为准」的单向约定。
- D10 的判据是**两条独立事实** + 一条防御性冗余（冗余那条在 D0 绿时与前者同真同假，
  由 R180 跨家族审计 #429 的 B4 指出、`_r180/r180f` 复算成立后订正）。
- 本文件仍**不声明其内容为真**：事实真假由 FACT_INDEX 正文及各条 limitations 的作用域决定。"""
ck('P4 旧边界段锚点唯一', src.count(o2)==1)
s2=s1.replace(o2,n2,1)
ck('P5 两处订正均已应用', s2!=src and 'R180' in s2 and 'D10' in s2)
ck('P6 新文本 CR==0', '\r' not in s2)
ck('P7 四字段行逐字未变（sha/字节/目录/路径）',
   [l for l in s2.split('\n') if l.startswith(('| 版本目录','| 相对路径','| sha256','| 字节数','| 行数'))]
   ==[l for l in src.split('\n') if l.startswith(('| 版本目录','| 相对路径','| sha256','| 字节数','| 行数'))])

newb=s2.encode('utf-8')
ts=time.strftime('%Y%m%d_%H%M%S')
bak=os.path.join(BL,'FACT_INDEX_CURRENT.md.before_r180_%s.bak'%ts)
with open(bak,'xb') as f: f.write(old)
ck('P8 备份独占创建', os.path.exists(bak), os.path.basename(bak))
ck('P9 备份 == 写入前逐字节', rb(bak)==old)
open(PTR,'wb').write(newb)
ck('P10 回读 sha == 新内容', sh(rb(PTR))==sh(newb), sh(rb(PTR))[:16])
ck('P11 CR 仍 0', rb(PTR).count(b'\r')==0)
print('   指针 %d -> %d B, sha=%s'%(len(old),len(newb),sh(newb)[:16]))

# D10 复跑必须仍绿（指针自身 sha 变了，但 D10 只读其内容字段）
import subprocess
e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
r=subprocess.run([sys.executable,os.path.join(ROOT,'_r160','facts_floors.py')],cwd=ROOT,
                 capture_output=True,text=True,env=e,timeout=200)
ck('P12 改后 facts_floors 仍 exit 0（D10 字段未动）', r.returncode==0,
   (r.returncode,[l.strip()[:70] for l in (r.stdout+r.stderr).split('\n') if 'FAIL' in l][:3]))
print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
