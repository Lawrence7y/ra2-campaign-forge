#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 p4：把台账 V586 与 C16 重钉结果补进 LEAD_LOCK QE8 与 STATUS_BOARD 落盘行。
严格：写前 wx 备份、断言旧 sha/CR、单点精确替换（各 1 次）、回读校验。"""
import hashlib,os,time,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
LL=ROOT+'/lead/LEAD_LOCK'
BD=ROOT+'/lead/next_re_20261117_r14/STATUS_BOARD.md'
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def cr(p): return open(p,'rb').read().count(b'\r')

LL_OLD='落盘：R14_COMMON §2.207 CR 保持 1081；GOAL §1257 CR 保持 337；本段 CR 保持 137；STATUS_BOARD 第 202 轮 CR 保持 0。'
LL_NEW=('落盘：R14_COMMON §2.207 CR 保持 1081；GOAL §1257 CR 保持 337；本段 CR 保持 137；STATUS_BOARD 第 202 轮 CR 保持 0（开局 257 行 < 260 无需归档，收口 277 行）；'
 '台账 V585 → **V586**（只改 F55：stmt 39,304 → **45,252** B、lim 24,540 → **24,935** B、evid 1,879 → **2,360** B、总 219,024 → **225,848** B、sha 2d3d065a… → **07a55ac3…**、40 断言 0 FAIL；'
 '旧常量复算旧 MASTER a5c8c491… 命中旧 pin 作硬闸 ⇒ 新 MASTER **a8a54e49…**；ITEMS 272 → **295**、UNIQ 164 → **187**、LOST 43/16 未变、EVID 89 → **112** 条、'
 '指针 530..585/56 份 → **530..586/57 份**、声明轮次 R200 → **R201**）；C16_FLOORS 199 → **202**（钉 205=7,233 / 206=3,707 / 207=5,538，均为实测//2）并重算 sha dc0550b0 → **c8014bb3**；'
 '三门 exit 0（check_disc C16 unpinned 0 / C19 ok(07a55ac3/225848/V586) / C20 ok(V586)；facts_floors D8 225,848、D9+D10 双一致；gate_runner G1=G2=G3=ok）。')

BD_OLD='**落盘.** R14_COMMON 追加 §2.207 CR 保持 1081；GOAL 追加 §1257 CR 保持 337；LEAD_LOCK 追加 QE CR 保持 137；本看板追加第 202 轮 CR 保持 0（开局 257 行 < 260，无需归档）。'
BD_NEW=('**落盘.** R14_COMMON 追加 §2.207 CR 保持 1081；GOAL 追加 §1257 CR 保持 337；LEAD_LOCK 追加 QE CR 保持 137；本看板追加第 202 轮 CR 保持 0（开局 257 行 < 260，无需归档，收口 277 行）；'
 '台账 V585 → **V586**（只改 F55：stmt 45,252 B / evid 2,360 B / 总 225,848 B / sha 07a55ac3…、40 断言 0 FAIL、ITEMS 272→295、EVID 89→112 条、指针 530..586/57 份、声明轮次 R201）；'
 'C16_FLOORS 199 → **202**（钉 205/206/207）并重算 sha c8014bb3…；三门 exit 0。')

for path,old,new,tag,ecr in ((LL,LL_OLD,LL_NEW,'LL',137),(BD,BD_OLD,BD_NEW,'BOARD',0)):
    b=open(path,'rb').read()
    ck('PRE_%s CR'%tag, b.count(b'\r')==ecr, b.count(b'\r'))
    t=b.decode('utf-8')
    ck('PRE_%s 锚点出现恰好 1 次'%tag, t.count(old)==1, t.count(old))
    if fails: break
    STAMP=time.strftime('%Y%m%d_%H%M%S')
    bak='%s/lead/next_re_20261117_r14/R17_LEAD_BASELINE/%s.before_r202_ledgernote_%s.bak'%(
        ROOT,os.path.basename(path),STAMP)
    with open(bak,'xb') as f: f.write(b)
    ck('BAK_%s wx 独占'%tag, os.path.exists(bak), os.path.basename(bak))
    nt=t.replace(old,new,1)
    nb=nt.encode('utf-8')
    ck('W_%s CR 保持 %d'%(tag,ecr), nb.count(b'\r')==ecr, nb.count(b'\r'))
    ck('W_%s 字节增加'%tag, len(nb)>len(b), (len(b),len(nb)))
    open(path,'wb').write(nb)
    rb=open(path,'rb').read()
    ck('R_%s 新锚点存在'%tag, new.encode('utf-8') in rb, True)
    ck('R_%s 旧锚点已不在'%tag, old.encode('utf-8') not in rb, True)
    ck('R_%s CR 回读 %d'%(tag,ecr), rb.count(b'\r')==ecr, rb.count(b'\r'))
    print('   %-5s bytes %d -> %d CR=%d sha=%s'%(tag,len(b),len(rb),rb.count(b'\r'),hashlib.sha256(rb).hexdigest()[:16]))
bl=len(open(BD,'rb').read().split(b'\n'))-1
ck('BOARD 行数 <= 300', bl<=300, bl)
print('\nSUMMARY fails=%d %s'%(len(fails),fails))
if fails: sys.exit(1)
