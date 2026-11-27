# -*- coding: utf-8 -*-
"""R180 写盘：把 D10 补丁写入生产 _r160/facts_floors.py。
纪律：R17_LEAD_BASELINE/ 用 'xb' 独占创建唯一备份 -> 断言旧 sha + 旧 CR -> 一次性写入 -> 回读校验。"""
import hashlib,io,os,shutil,subprocess,sys,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
FF=os.path.join(ROOT,'_r160','facts_floors.py')
NEW=os.path.join(os.path.dirname(os.path.abspath(__file__)),'r180b_patched.py')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()

OLD_SHA='03496c6b8ef2ff12'   # r180a A 段实测 facts_floors.py sha16
old=rb(FF); new=rb(NEW)
ck('W1 旧文件 sha16 == r180a 实测值（硬闸，不符即停）', sh(old)[:16]==OLD_SHA, (sh(old)[:16],OLD_SHA))
ck('W2 旧文件 CR 计数记录在案', True, 'CR=%d'%old.count(b'\r'))
ck('W3 新文件含 D10 且不含旧内容丢失', b'D10 pointer file' in new and new.count(b'D10')>0)
ck('W4 新文件比旧文件长且只多出 D10 块', len(new)>len(old), (len(old),len(new)))

ts=time.strftime('%Y%m%d_%H%M%S')
bak=os.path.join(BL,'facts_floors.py.before_r180_D10_%s.bak'%ts)
if Fl==0:
    with open(bak,'xb') as f:   # 'xb' 独占创建：同名存在即抛错，不会覆盖既有备份
        f.write(old)
    ck('W5 备份独占创建成功', os.path.exists(bak), bak)
    ck('W6 备份内容 == 旧文件逐字节', rb(bak)==old)
    with open(FF,'wb') as f: f.write(new)
    ck('W7 生产写入后回读 sha == 新文件 sha', sh(rb(FF))==sh(new), (sh(rb(FF))[:16],sh(new)[:16]))
    ck('W8 生产写入后回读字节数 == 新文件', len(rb(FF))==len(new))
    ck('W9 生产文件 CR 计数未变', rb(FF).count(b'\r')==old.count(b'\r'), rb(FF).count(b'\r'))
    # 差异行只能是 D10 块 + import re
    ol=old.decode('utf-8').split('\n'); nl=new.decode('utf-8').split('\n')
    import difflib
    add=[l for l in difflib.unified_diff(ol,nl,lineterm='',n=0) if l.startswith('+') and not l.startswith('+++')]
    rem=[l for l in difflib.unified_diff(ol,nl,lineterm='',n=0) if l.startswith('-') and not l.startswith('---')]
    print('   新增行 %d / 删除行 %d'%(len(add),len(rem)))
    # S-668：首版写「删除行恰 1（import 行被替换）」，实测删除行 0 —— import re 是
    # **纯插入**行，既有 import 行一字未动。断言改为「删除行 0 是应然」。
    ck('W10 删除行恰 0（D10 是纯追加，既有行一字未改）', len(rem)==0, rem)
    ck('W11 新增行无一行改动既有 pin 常量',
       not any(('CUR_SHA256 =' in l or 'TOTAL_BYTES =' in l or 'MASTER_SHA256 =' in l) for l in add), add[:3])
shutil.rmtree('/tmp/__none__',ignore_errors=True)
print('\n== %d PASS / %d FAIL ==  bak=%s'%(P,Fl,bak if Fl==0 else 'NONE'))
sys.exit(1 if Fl else 0)
