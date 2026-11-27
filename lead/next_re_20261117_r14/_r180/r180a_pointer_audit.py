# -*- coding: utf-8 -*-
"""R180 取证：FACT_INDEX_CURRENT.md 是否被任何门禁读取；指针四字段与 facts_floors 常量/现盘是否一致。
一次命令输出全部证据 + 正反控，不拆单点。"""
import hashlib, io, os, re, sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
FF=os.path.join(ROOT,'_r160','facts_floors.py')
GR=os.path.join(ROOT,'_r161','gate_runner.py')
CD=os.path.join(TIER,'check_disc.py')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()

# ---- A：三门是否读指针（三条独立文本计数）----
# R180 自错 S-670：A 段首版断言「三门读指针次数各 0」，那描述的是**补丁前**状态；
# D10 落地后 facts_floors 自身已会读（2 次），复跑该断言即假 FAIL。
# 改为**前后对照**：补丁前状态以 R17_LEAD_BASELINE 的首个备份为准，现态另行断言。
import glob
BAKS=sorted(glob.glob(os.path.join(TIER,'R17_LEAD_BASELINE','facts_floors.py.before_r180_D10_*.bak')))
PRE=BAKS[0] if BAKS else None
ck('A0 补丁前的 facts_floors 备份存在（前后对照的基准）', PRE is not None, PRE)
def cnt(p,tok):
    r=rb(p).decode('utf-8'); return r.count(tok)
for name,path in (('facts_floors',FF),('gate_runner',GR),('check_disc',CD)):
    _raw=rb(path); raw=_raw.decode('utf-8')
    n1=raw.count('FACT_INDEX_CURRENT')
    n2=len(re.findall(r'FACT_INDEX_CURRENT',raw))
    n3=raw.count('CURRENT.md')
    print('A %-13s FACT_INDEX_CURRENT=%d current_md=%d CURRENT.md=%d bytes=%d sha16=%s'
          %(name,n1,n2,n3,len(_raw),sh(_raw)[:16]))
    if name=='facts_floors':
        ck('A..facts_floors 补丁前读指针 0 次（以备份为准）', PRE and cnt(PRE,'FACT_INDEX_CURRENT')==0,
           cnt(PRE,'FACT_INDEX_CURRENT') if PRE else None)
        ck('A..facts_floors 现态读指针 >0（D10 已注入）', n1>0, n1)
    else:
        ck('A..%s 读指针次数为 0（本轮未改）'%name, n1==0 and n3==0, (n1,n3))
# 反控：同一计数法在**确实**引用了该文件名的脚本上必须非零
ref=os.path.join(ROOT,'_r173','r173o_pointer.py')
if os.path.exists(ref):
    rn=rb(ref).decode('utf-8').count('FACT_INDEX_CURRENT')
    ck('A.rc 反控：r173o_pointer.py 计数非零（同法有分辨力）', rn>0, rn)

# ---- B：指针四字段解析 ----
txt=io.open(PTR,encoding='utf-8',newline='').read()
rawp=rb(PTR)
print('B pointer bytes=%d sha16=%s CR=%d'%(len(rawp),sh(rawp)[:16],rawp.count(b'\r')))
m_dir=re.search(r'\| 版本目录 \| ([^ |]+) \|',txt)
m_pth=re.search(r'\| 相对路径 \| ([^ |]+) \|',txt)
m_sha=re.search(r'\| sha256 \| ([0-9a-f]{64}) \|',txt)
m_byt=re.search(r'\| 字节数 \| (\d+) \|',txt)
m_row=re.search(r'\| 行数 \| (\d+)',txt)
for nm,m in (('版本目录',m_dir),('相对路径',m_pth),('sha256',m_sha),('字节数',m_byt),('行数',m_row)):
    ck('B..指针字段可解析：%s'%nm, m is not None, (m.group(1)[:40] if m else None))
p_dir=m_dir.group(1); p_pth=m_pth.group(1); p_sha=m_sha.group(1); p_byt=int(m_byt.group(1))
p_row=int(m_row.group(1))

# ---- C：指针 vs facts_floors 常量 ----
fft=rb(FF).decode('utf-8')
c_sha=re.search(r"^CUR_SHA256 = '([0-9a-f]{64})'",fft,re.M).group(1)
c_byt=int(re.search(r'^TOTAL_BYTES = (\d+)$',fft,re.M).group(1))
c_cur=re.search(r"^EXPECT_CUR = os\.path\.join\(TIER, '([^']+)'",fft,re.M).group(1)
print('C facts CUR_SHA256=%s TOTAL_BYTES=%d EXPECT_CUR_dir=%s'%(c_sha[:16],c_byt,c_cur))
ck('C1 指针 sha256 == facts CUR_SHA256', p_sha==c_sha, (p_sha[:16],c_sha[:16]))
ck('C2 指针字节数 == facts TOTAL_BYTES', p_byt==c_byt, (p_byt,c_byt))
ck('C3 指针版本目录 == facts EXPECT_CUR 目录名', p_dir==c_cur, (p_dir,c_cur))

# ---- D：指针所指文件现盘一致性 ----
disk=os.path.join(ROOT,p_pth)
ck('D1 指针相对路径在盘上存在', os.path.exists(disk), disk)
if os.path.exists(disk):
    b=rb(disk)
    ck('D2 该文件实测 sha256 == 指针声明', sh(b)==p_sha, (sh(b)[:16],p_sha[:16]))
    ck('D3 该文件实测字节数 == 指针声明', len(b)==p_byt, (len(b),p_byt))
    ck('D4 该文件实测行数 == 指针声明', len([l for l in io.open(disk,encoding='utf-8',newline='').read().split('\n') if l])==p_row)
    ck('D5 该文件 CR=0（LF-only）', b.count(b'\r')==0)
    ck('D6 该文件 == EXPECT_CUR 所指（同目录同文件）', os.path.realpath(disk)==os.path.realpath(os.path.join(TIER,c_cur,'FACT_INDEX.tsv')), (disk,))

# ---- E：反控 —— 把指针 sha 改 1 位，D2 判据必须翻红 ----
bad=p_sha[:-1]+('0' if p_sha[-1]!='0' else '1')
b2=rb(disk)
ck('E1 反控：篡改后 sha 判据翻红（有分辨力）', (bad!=p_sha) and (sh(b2)!=bad), (bad[:16],))

# ---- F：指针声明的「版本号 530..563 共 34 份」现盘重数 ----
# 注意：V53/V58/V511 是早期命名（v5.3/v5.8/v5.11），与 V530 起的三位序号不同族
# （S-665：首版正则 _V(\d+)$ 把它们算成 53/58/511，得出「不连续」的假 FAIL）
alld=[d for d in os.listdir(TIER) if re.match(r'R17_R\d+_FACTINDEX_V\d+$',d)]
dirs=[d for d in alld if int(re.search(r'_V(\d+)$',d).group(1))>=530]
legacy=sorted(int(re.search(r'_V(\d+)$',d).group(1)) for d in alld if int(re.search(r'_V(\d+)$',d).group(1))<530)
print('F legacy-命名目录（已排除）=%r'%(legacy,))
vers=sorted(int(re.search(r'_V(\d+)$',d).group(1)) for d in dirs)
print('F snapshot dirs=%d versions=%d..%d contiguous=%s'%(len(dirs),vers[0],vers[-1],vers==list(range(vers[0],vers[-1]+1))))
ck('F1 现盘版本目录数 == 指针所称 34', len(dirs)==34, len(dirs))
ck('F2 版本号连续 530..563', vers==list(range(530,564)), (vers[0],vers[-1]))

print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
