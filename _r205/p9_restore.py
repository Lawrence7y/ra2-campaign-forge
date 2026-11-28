#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 紧急修复：p8_fix.py 用 open(...,encoding='utf-8') 文本模式读，Python 通用换行把 CRLF 规范成 LF，
写回后 CR 全丢（R14_COMMON 1081->0、GOAL 337->0、LEAD_LOCK 137->0）。
从本轮 p8 的 .bak 恢复，再用 bytes 模式重做替换。
"""
import os,glob,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14'; BL=ROOT+'/R17_LEAD_BASELINE'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n); print('FAIL '+n+' | '+str(d))
    else: print('PASS '+n)

targets=[('R14_COMMON.md',G+'/R14_COMMON.md',1081,'RC'),
         ('GOAL_THREE_TARGETS_20261018.md',ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',337,'GOAL'),
         ('LEAD_LOCK',ROOT+'/lead/LEAD_LOCK',137,'LL')]
for base,p,exp,tag in targets:
    ck('%s 当前 CR 坏掉（=0）'%base,crc(p)==0,crc(p))
    baks=sorted(glob.glob(BL+'/%s.before_r205fix_%s_*.bak'%(base,tag)))
    ck('%s 找到 p8 备份'%base,len(baks)==1,baks)
    bk=baks[0]
    ck('%s 备份 CR == %d'%(base,exp),crc(bk)==exp,crc(bk))
    raw=open(bk,'rb').read()
    open(p,'wb').write(raw)
    ck('%s 已从备份恢复'%base,open(p,'rb').read()==raw,None)
    ck('%s 恢复后 CR == %d'%(base,exp),crc(p)==exp,crc(p))
print('\nFAILS:',fails)
json.dump(dict(fails=fails),open(ROOT+'/_r205/p9_restore.json','w'),indent=1)
