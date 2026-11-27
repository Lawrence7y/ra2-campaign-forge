# -*- coding: utf-8 -*-
"""R180：给 facts_floors.py 增加 D10 —— 当前版指针必须与 CUR 常量/实物一致。
补丁先在**沙箱镜像**上验证（不碰生产），四条破坏性工况全过才写生产。"""
import hashlib, io, os, re, shutil, subprocess, sys, tempfile
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
FF=os.path.join(ROOT,'_r160','facts_floors.py')
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()

BLOCK = """
# ---- D10 [R180 新增] 当前版指针必须与 CUR 常量/实物一致 ----
# 存在理由（实测，连续 8 轮登记未闭合）：D0/D9 只钉 CUR 指向的那份文件；
# FACT_INDEX_CURRENT.md 承载「哪一份是当前版」的声明，却在 check_disc / gate_runner /
# 本脚本三者中读取次数各 0（_r180/r180a A 段实测）⇒ 指针静默漂移时三门全绿。
# 判据是两条**独立**事实的相等，不是文本相似：
#   (1) 指针声明的 sha256/字节数 == 本文件 CUR_SHA256/TOTAL_BYTES（同一物件的两种登记）
#   (2) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。
PTR_FILE = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
print('  D10 pointer file: %s' % ('present' if os.path.exists(PTR_FILE) else 'MISSING'))
if not os.path.exists(PTR_FILE):
    F('D10 pointer file missing: %s' % PTR_FILE)
else:
    _pt = io.open(PTR_FILE, encoding='utf-8', newline='').read()
    _ms = re.search(r'\\| sha256 \\| ([0-9a-f]{64}) \\|', _pt)
    _mb = re.search(r'\\| 字节数 \\| (\\d+) \\|', _pt)
    if not _ms or not _mb:
        F('D10 pointer fields unparseable (sha256_found=%r bytes_found=%r)' % (bool(_ms), bool(_mb)))
    else:
        _ps, _pb = _ms.group(1), int(_mb.group(1))
        _ds = hashlib.sha256(open(CUR, 'rb').read()).hexdigest()
        # 打印与 FAIL 消息一律用**全文** sha：R180 自测发现只打前 16 位时，
        # 末位被改的漂移在日志里与基线逐字相同（判据仍会 FAIL，但事后无法从日志分辨）。
        if not IGNORE_PIN and _ps != CUR_SHA256:
            F('D10 pointer sha %s != CUR_SHA256 %s (pointer names a different version)'
              % (_ps, CUR_SHA256))
        if not IGNORE_PIN and _pb != TOTAL_BYTES:
            F('D10 pointer bytes %d != TOTAL_BYTES %d' % (_pb, TOTAL_BYTES))
        if not IGNORE_PIN and _ps != _ds:
            F('D10 pointer sha %s != on-disk sha of CUR %s (declared version is not this file)'
              % (_ps, _ds))
        print('  D10 pointer sha=%s bytes=%d vs CUR %s/%d (on-disk %s)'
              % (_ps, _pb, CUR_SHA256, TOTAL_BYTES, _ds))
"""

src=rb(FF).decode('utf-8')
ck('B0 生产 facts_floors 补丁前不含 D10', 'D10' not in src)
ck('B1 D9 锚点唯一', src.count("if fails:\n    for m in fails: print('  FAIL  ' + m)")==1)
ck('B2 需要 import re（当前没有）', not re.search(r'^import re$',src,re.M))
patched=src.replace("import os\nimport sys\nfrom collections import Counter",
                    "import os\nimport re\nimport sys\nfrom collections import Counter",1)
ck('B3 import re 注入成功', patched!=src and re.search(r'^import re$',patched,re.M) is not None)
anchor="if fails:\n    for m in fails: print('  FAIL  ' + m)"
patched2=patched.replace(anchor, BLOCK.strip('\n')+"\n\n"+anchor, 1)
ck('B4 D10 块已插在 fails 汇总之前',
   patched2!=patched and patched2.index('D10 pointer file')<patched2.index(anchor))
ck('B5 既有 pin 常量行逐行未变',
   [l for l in patched2.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))]
   ==[l for l in src.split('\n') if l.startswith(('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','EXPECT_CUR'))])
ck('B6 MASTER 未变（D10 不引入新 pin，不进 D9 payload）',
   re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",patched2,re.M).group(1)
   ==re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",src,re.M).group(1))

# ---------------- 沙箱镜像：/tmp/sb/{_r160,lead/next_re_20261117_r14} ----------------
sbt=tempfile.mkdtemp(prefix='/tmp/r180d10_')
sbroot=os.path.join(sbt,'root')
# 仓库根下除 lead/ 与 _r160/ 外全部软链：D7 的 lost 多重集要看 _r139/* 等真实路径，
# 不镜像会得到 +3 个假 FAIL（首版 S0 就是这么红的两条）。
os.makedirs(sbroot)
for n in os.listdir(ROOT):
    if n in ('lead','_r160'): continue
    os.symlink(os.path.join(ROOT,n), os.path.join(sbroot,n))
os.makedirs(os.path.join(sbroot,'_r160'))
sbtier=os.path.join(sbroot,'lead','next_re_20261117_r14')
os.makedirs(sbtier)
# lead/ 下除 tier 外全部软链（facts_floors 的 ROOT 判定需要 ROOT/lead 存在）
for n in os.listdir(os.path.join(ROOT,'lead')):
    if n=='next_re_20261117_r14': continue
    os.symlink(os.path.join(ROOT,'lead',n), os.path.join(sbroot,'lead',n))
# tier 内除「指针 + V563 目录」外全部软链
MU={'FACT_INDEX_CURRENT.md','R17_R131_FACTINDEX_V563'}
for n in os.listdir(TIER):
    if n in MU: continue
    os.symlink(os.path.join(TIER,n), os.path.join(sbtier,n))
shutil.copytree(os.path.join(TIER,'R17_R131_FACTINDEX_V563'), os.path.join(sbtier,'R17_R131_FACTINDEX_V563'))
# 仓库根下 _r160 只放本脚本；ROOT 判定看 ROOT/lead 是否存在 ⇒ 满足
sff=os.path.join(sbroot,'_r160','facts_floors.py')
open(sff,'wb').write(patched2.encode('utf-8'))
sptr=os.path.join(sbtier,'FACT_INDEX_CURRENT.md')
shutil.copy2(PTR, sptr)
def run(ff):
    e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
    r=subprocess.run([sys.executable,ff],cwd=ROOT,capture_output=True,text=True,env=e,timeout=180)
    return r.returncode,(r.stdout+r.stderr)
ck('S0 沙箱镜像保真：沙箱 facts_floors 基线 exit 0',
   *(lambda rc,out:(rc==0,(rc,[l.strip() for l in out.split('\n') if 'FAIL' in l][:3])))(*run(sff)))
rc0,out0=run(sff)
ck('S1 基线输出含 D10 pointer 行', 'D10 pointer sha=' in out0, [l.strip() for l in out0.split('\n') if 'D10' in l][:2])

good=rb(sptr).decode('utf-8')
gs=re.search(r'\| sha256 \| ([0-9a-f]{64}) \|',good).group(1)
# 工况 A：指针 sha 改 1 位
bs=gs[:-1]+('0' if gs[-1]!='0' else '1')
open(sptr,'w',encoding='utf-8',newline='').write(good.replace(gs,bs,1))
rcA,outA=run(sff)
ck('SA 指针 sha 改 1 位 ⇒ exit 1 且报 D10', rcA==1 and any('D10' in l and 'FAIL' in l for l in outA.split('\n')),
   (rcA,[l.strip()[:80] for l in outA.split('\n') if 'D10' in l and 'FAIL' in l][:2]))
# 工况 B：指针字节数改 1
gb=re.search(r'\| 字节数 \| (\d+) \|',good).group(1)
open(sptr,'w',encoding='utf-8',newline='').write(good.replace('| 字节数 | %s |'%gb,'| 字节数 | %d |'%(int(gb)+1),1))
rcB,outB=run(sff)
ck('SB 指针字节数 +1 ⇒ exit 1 且报 D10 bytes', rcB==1 and any('D10 pointer bytes' in l for l in outB.split('\n')),
   (rcB,[l.strip()[:80] for l in outB.split('\n') if 'D10 pointer bytes' in l][:1]))
# 工况 C：指针文件缺失
os.remove(sptr)
rcC,outC=run(sff)
ck('SC 指针文件缺失 ⇒ exit 1 且报 D10 missing', rcC==1 and any('D10 pointer file missing' in l for l in outC.split('\n')),
   (rcC,))
# 工况 D：反向假通过检查 —— 指针正确但 --ignore-pin 下不报 D10 FAIL（证明 D10 由 pin 驱动而非恒真）
shutil.copy2(PTR,sptr)
e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
r=subprocess.run([sys.executable,sff,'--ignore-pin'],cwd=ROOT,capture_output=True,text=True,env=e,timeout=180)
ck('SD --ignore-pin 下 exit 0（D10 与 D0 同受 pin 约束，可被隔离）', r.returncode==0, r.returncode)
# 工况 E：指针指向**另一版**（V562）⇒ 必须 FAIL（这是本补丁要拦的真实漂移场景）
v562=os.path.join(TIER,'R17_R130_FACTINDEX_V562','FACT_INDEX.tsv')
b562=rb(v562); s562=sh(b562)
open(sptr,'w',encoding='utf-8',newline='').write(
    re.sub(r'\| sha256 \| [0-9a-f]{64} \|','| sha256 | %s |'%s562, good, count=1))
rcE,outE=run(sff)
ck('SE 指针改指 V562 ⇒ exit 1 且报 D10（拦得住真实漂移）',
   rcE==1 and any('D10' in l and 'FAIL' in l for l in outE.split('\n')),
   (rcE,[l.strip()[:80] for l in outE.split('\n') if 'D10' in l][:2]))

print('\n== 沙箱 %d PASS / %d FAIL ==  patch_sha16=%s'%(P,Fl,sh(patched2.encode())[:16]))
if Fl==0:
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'r180b_patched.py'),'wb').write(patched2.encode('utf-8'))
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'r180b_sandbox_root.txt'),'w').write(sbroot+'\n')
    print('已写出 _r180/r180b_patched.py（未写生产）')
shutil.rmtree(sbt,ignore_errors=True)
sys.exit(1 if Fl else 0)
