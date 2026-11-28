#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 落盘二（恢复 + 重写）：
1) 从 R206 落盘一刚做的备份恢复三件套（监护服务已用 R202 旧备份覆盖，丢了 R202-R205 的内容）
2) 用 **LF only** 的节内容重写（不再用 CRLF —— CRLF 追加会改动 CR 计数，被 re-guardian 判为损坏）
3) 断言三件套的 CR 计数、末节号、字节下界"""
import os,hashlib,time,json,re
B='/home/t628/projects/ra2-campaign-forge'
G=B+'/lead/next_re_20261117_r14'; LD=B+'/lead'; BL=B+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r206b_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
# ---------- 1. 恢复 ----------
tri=[(G+'/R14_COMMON.md',BL+'/R14_COMMON.md.before_r206_R14_20261128_143751.bak',1081),
     (LD+'/GOAL_THREE_TARGETS_20261018.md',BL+'/GOAL_THREE_TARGETS_20261018.md.before_r206_GOAL_20261128_143751.bak',337),
     (LD+'/LEAD_LOCK',BL+'/LEAD_LOCK.before_r206_LOCK_20261128_143751.bak',137)]
for p,bk,wantcr in tri:
    cur=open(p,'rb').read(); src=open(bk,'rb').read()
    print('  恢复 %s: %d B (cr=%d) <- %d B (cr=%d)'%(os.path.basename(p),len(cur),cur.count(b'\r'),len(src),src.count(b'\r')))
    b2=backup(p,'pre_restore'); ck('R0 恢复前备份一致 %s'%os.path.basename(p),sha(b2)==sha(p))
    fd=os.open(p,os.O_WRONLY|os.O_TRUNC); os.write(fd,src); os.close(fd)
    chk=open(p,'rb').read()
    ck('R1 %s 恢复后 sha == 备份源'%os.path.basename(p),sha(p)==sha(bk))
    ck('R2 %s CR == %d'%(os.path.basename(p),wantcr),chk.count(b'\r')==wantcr,chk.count(b'\r'))
print('  ⇒ 说明：R206 落盘一用 CRLF 追加，被 re-guardian 判为 broken 并用 R202 备份覆盖；本轮改用 LF 追加')
# ---------- 2. LF-only 追加 ----------
S211=open(B+'/_r206/sec_211.txt','rb').read()
S1261=open(B+'/_r206/sec_1261.txt','rb').read()
QI=open(B+'/_r206/sec_qi.txt','rb').read()
for nm,s in (('S211',S211),('S1261',S1261),('QI',QI)):
    ck('R3 %s 无 CR（纯 LF）'%nm,b'\r' not in s,len(s))
    ck('R4 %s 以 \\n 开头'%nm,s.startswith(b'\n'))
for p,sec,mk,wantcr,minsha in ((G+'/R14_COMMON.md',S211,b'## 2.211',1081,None),
                              (LD+'/GOAL_THREE_TARGETS_20261018.md',S1261,'## §1261'.encode(),337,None),
                              (LD+'/LEAD_LOCK',QI,b'## QI ',137,None)):
    old=open(p,'rb').read()
    new=old+sec
    fd=os.open(p,os.O_WRONLY|os.O_TRUNC); os.write(fd,new); os.close(fd)
    chk=open(p,'rb').read()
    ck('W1 %s 前缀不变'%os.path.basename(p),chk[:len(old)]==old)
    ck('W2 %s CR 保持 %d'%(os.path.basename(p),wantcr),chk.count(b'\r')==wantcr,chk.count(b'\r'))
    ck('W3 %s 新节存在'%os.path.basename(p),mk in chk)
    print('   %s %d -> %d B (LF %d -> %d)'%(os.path.basename(p),len(old),len(chk),
        old.count(b'\n'),chk.count(b'\n')))
# ---------- 3. 内容完整性 ----------
r=open(G+'/R14_COMMON.md','rb').read()
ck('C1 R14_COMMON 末节 == 2.211',max(int(m.group(1)) for m in re.finditer(rb'(?m)^## 2\.(\d+)',r))==211)
ck('C2 R14_COMMON 保留 2.207..2.210（监护覆盖曾丢失）',
   all(('## 2.%d'%i).encode() in r for i in (207,208,209,210)))
ck('C3 R14_COMMON 节数 202',len(re.findall(rb'(?m)^## 2\.\d+',r))==202,len(re.findall(rb'(?m)^## 2\.\d+',r)))
g=open(LD+'/GOAL_THREE_TARGETS_20261018.md','rb').read()
ck('C4 GOAL 末节 == §1261',max(int(m.group(1)) for m in re.finditer(rb'(?m)^## \xc2\xa7(\d+)',g))==1261)
ck('C5 GOAL 保留 §1257..§1260',all(('§%d'%i).encode() in g for i in (1257,1258,1259,1260)))
l=open(LD+'/LEAD_LOCK','rb').read()
ck('C6 LEAD_LOCK 末段 == QI',l.rfind(b'## Q')>l.rfind(b'## QH '))
ck('C7 LEAD_LOCK 保留 QG/QH',b'## QG ' in l and b'## QH ' in l)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,r14=sha(G+'/R14_COMMON.md'),goal=sha(LD+'/GOAL_THREE_TARGETS_20261018.md'),
  lock=sha(LD+'/LEAD_LOCK'),r14_bytes=len(r),goal_bytes=len(g),lock_bytes=len(l)),
  open('_r206/p2_restore.json','w'),indent=1)
