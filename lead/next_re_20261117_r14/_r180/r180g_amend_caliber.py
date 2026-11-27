# -*- coding: utf-8 -*-
"""R180 修正（采纳审计 #429 的 B4/D1/D2，主会话已 r180f 逐条复算成立）：
1) D10 注释口径：把「三条独立事实」改为「两条独立判据 + 一条连带等价式」，并写明原因。
2) D9 日志：打印与 FAIL 消息各补全文 sha（同一缺陷在 D9 上原封不动）。
沙箱验证 → 写入纪律落盘。"""
import hashlib,io,os,re,shutil,subprocess,sys,tempfile,time
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
old=rb(FF); src=old.decode('utf-8')
ck('A1 旧 sha16 == r180e 写后实测', sh(old)[:16]=='15d48bcd86841bc5', sh(old)[:16])

# --- 修正 1：D10 注释口径 ---
o1="""# 判据是两条**独立**事实的相等，不是文本相似：
#   (1) 指针声明的 sha256/字节数 == 本文件 CUR_SHA256/TOTAL_BYTES（同一物件的两种登记）
#   (2) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。"""
n1="""# 判据是两条**独立**事实的相等，不是文本相似：
#   (A) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
#   (B) 指针声明的字节数 == 本文件 TOTAL_BYTES（规模声明 vs 规模常量）
# 另有第三条 (C) 指针 sha256 == 本文件 CUR_SHA256，但它**不独立**：D0 已保证
#   sha(CUR) == CUR_SHA256，故 (A) 绿 + D0 绿 ⇒ (C) 必绿，三者同真同假。
#   R180 审计 #429 的 B4 指出卡面写「三条相等」夸大了独立性，主会话 r180f 复算成立，
#   此处按源码口径订正为「两条独立 + 一条连带」，判定逻辑不变（多留一条是防御性冗余）。
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。"""
ck('A2 D10 口径注释锚点唯一', src.count(o1)==1, src.count(o1))
s1=src.replace(o1,n1,1)
ck('A3 口径注释已改', s1!=src)

# --- 修正 2：D9 日志补全文 sha ---
o2="""    F('D9 MASTER pin drifted: constants were edited together with data')"""
n2="""    # R180 修正（审计 #429 的 D1/D2，主会话 r180f 复算成立）：原文只打前 16 位且 FAIL
    # 消息完全不含 sha ⇒ 末位被改的漂移在日志里与基线逐字相同。此处补全文。
    F('D9 MASTER pin drifted: recomputed %s != pinned %s (constants were edited together with data)'
      % (_master, MASTER_SHA256))"""
ck('A4 D9 FAIL 消息锚点唯一', src.count(o2)==1, src.count(o2))
s2=s1.replace(o2,n2,1)
ck('A5 D9 FAIL 消息已改', s2!=s1)
o3="""print('  D9 master pin: %s' % _master[:16])"""
n3="""print('  D9 master pin: %s (pinned %s)' % (_master, MASTER_SHA256))"""
ck('A6 D9 打印行锚点唯一', src.count(o3)==1, src.count(o3))
s3=s2.replace(o3,n3,1)
ck('A7 D9 打印行已改为全文', s3!=s2)

new=s3
ck('A8 既有 pin 常量行逐字未变',
   [l for l in new.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))]
   ==[l for l in src.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))])
ck('A9 D9 payload 拼接内容未变（只改日志，不改指纹）',
   '_master = hashlib.sha256(' in new and "canon_l(LOST),\n                                      str(ITEMS)" in new.replace('\r',''))
# payload 逻辑不变的第二证明：新旧 MASTER 常量字面量相同
ck('A10 MASTER 常量未变',
   re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",new,re.M).group(1)
   ==re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",src,re.M).group(1))

# --- 沙箱：真实归档软链，只换 facts_floors ---
sbt=tempfile.mkdtemp(prefix='/tmp/r180g_')
sbroot=os.path.join(sbt,'root'); os.makedirs(sbroot)
for n in os.listdir(ROOT):
    if n in ('lead','_r160'): continue
    os.symlink(os.path.join(ROOT,n), os.path.join(sbroot,n))
os.makedirs(os.path.join(sbroot,'_r160')); os.makedirs(os.path.join(sbroot,'lead'))
for n in os.listdir(os.path.join(ROOT,'lead')):
    os.symlink(os.path.join(ROOT,'lead',n), os.path.join(sbroot,'lead',n))
sff=os.path.join(sbroot,'_r160','facts_floors.py'); open(sff,'wb').write(new.encode('utf-8'))
e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
r=subprocess.run([sys.executable,sff],cwd=ROOT,capture_output=True,text=True,env=e,timeout=200)
out=r.stdout+r.stderr
ck('A11 沙箱基线 exit 0', r.returncode==0, (r.returncode,[l.strip() for l in out.split('\n') if 'FAIL' in l][:3]))
ck('A12 沙箱 D9 打印行含全文 64 位', bool(re.search(r'D9 master pin: [0-9a-f]{64} \(pinned [0-9a-f]{64}\)',out)),
   [l.strip()[:80] for l in out.split('\n') if 'D9 master pin' in l])
# 反控：篡改 MASTER 常量 ⇒ FAIL 消息必须同时含两个全文 sha
mut=new.replace(re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",new,re.M).group(1),
                'f'*64,1)
sff2=os.path.join(sbroot,'_r160','ff_mut.py'); open(sff2,'wb').write(mut.encode('utf-8'))
r2=subprocess.run([sys.executable,sff2],cwd=ROOT,capture_output=True,text=True,env=e,timeout=200)
out2=r2.stdout+r2.stderr
d9f=[l.strip() for l in out2.split('\n') if 'D9 MASTER pin drifted' in l]
ck('A13 反控：篡改 MASTER 常量 ⇒ exit 1 且 FAIL 消息含两个全文 sha',
   r2.returncode==1 and d9f and len(re.findall(r'[0-9a-f]{64}',d9f[0]))==2,
   (r2.returncode,[x[:140] for x in d9f]))
ck('A14 反控：篡改后日志可分辨（pinned 是 ffff 开头）',
   d9f and 'f'*64 in d9f[0], [x[:90] for x in d9f])

if Fl==0:
    ts=time.strftime('%Y%m%d_%H%M%S')
    bak=os.path.join(BL,'facts_floors.py.before_r180_caliber_%s.bak'%ts)
    with open(bak,'xb') as f: f.write(old)
    ck('A15 备份独占创建', os.path.exists(bak), bak)
    ck('A16 备份 == 写入前逐字节', rb(bak)==old)
    open(FF,'wb').write(new.encode('utf-8'))
    ck('A17 回读 sha == 新内容', sh(rb(FF))==sh(new.encode('utf-8')), sh(rb(FF))[:16])
    print('   生产新 sha256=%s bytes=%d'%(sh(rb(FF)),len(rb(FF))))
shutil.rmtree(sbt,ignore_errors=True)
print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
