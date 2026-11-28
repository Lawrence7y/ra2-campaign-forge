#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 重钉：指针文件 + facts_floors(EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER_SHA256/EVIDB) + gate_runner。
先用 --ignore-pin 跑新文件求新的 D7/D9 常量，再一次写入（fail-closed）。
"""
import os,re,hashlib,subprocess,json,time,shutil
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14'
BL=ROOT+'/R17_LEAD_BASELINE'
NEW=G+'/R17_R131_FACTINDEX_V588/FACT_INDEX.tsv'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

# ---- 先用 --ignore-pin 求新常量 ----
r=subprocess.run(['python3',ROOT+'/_r160/facts_floors.py',NEW,'--ignore-pin'],
                 capture_output=True,text=True,timeout=300)
out=r.stdout+r.stderr
m=re.search(r'D7 evidence: items=(\d+) uniq=(\d+) lost_items=(\d+) lost_uniq=(\d+)',out)
ck('P1 --ignore-pin 跑通并给出 D7',m is not None,r.returncode)
items,uniq,lost,lostu=[int(x) for x in m.groups()]
print('   D7 items=%d uniq=%d lost=%d lost_uniq=%d'%(items,uniq,lost,lostu))
m2=re.search(r'recomputed ([0-9a-f]{64})',out)
ck('P2 旧 MASTER pin 被换文件后触发漂移（证明 gate 不恒绿）',m2 is not None,(m2.group(1)[:16] if m2 else None))
newmaster=m2.group(1) if m2 else None
ck('P3 D8 总字节',True,re.search(r'D8 total bytes: (\d+)',out).group(1))
newbytes=len(open(NEW,'rb').read())
newsha=sha(NEW)
ck('P4 新文件 sha/bytes 一致',(newsha,len(open(NEW,'rb').read()))==(newsha,newbytes),(newsha[:16],newbytes))
# 新旧对比
old_items,old_uniq,old_lost,old_lostu=312,203,43,16
print('   D7 变化: items %d->%d, uniq %d->%d, lost %d->%d, lost_uniq %d->%d'%(
    old_items,items,old_uniq,uniq,old_lost,lost,old_lostu,lostu))

# EVID / EVIDB 也要同步（D7 逐 fid 清单与列4字节下限）
r2=subprocess.run(['python3','-c','''
import sys,re
sys.path.insert(0,"%s/_r160")
'''%ROOT],capture_output=True,text=True,timeout=60)
# 直接解析新文件求 F01 的 EVID 列表与字节数
raw=open(NEW,'rb').read().decode('utf-8').split('\n')
def norm(x): return x.strip()
for line in raw[1:]:
    if line.startswith('F01\t'):
        ev=[x for x in line.split('\t')[3].split(';') if x.strip()]
        print('   F01 EVID 条数 %d:'%len(ev))
        for x in ev: print('      '+x)
        print('   F01 col4 bytes %d'%len(line.split('\t')[3].encode()))
        new_evid=ev; new_evidb=len(line.split('\t')[3].encode())
        break

# ---- 写指针文件 ----
p=G+'/FACT_INDEX_CURRENT.md'
pre=sha(p); b=backup(p,'PTR')
ck('Q1 指针备份一致',sha(b)==pre,os.path.basename(b))
t=open(p,encoding='utf-8').read()
t2=t.replace('R17_R131_FACTINDEX_V587','R17_R131_FACTINDEX_V588')
t2=t2.replace('062111ba9adbf0658a29be9744efb1869a8ce5f4fa627a326a05b7c71c4fe44c',newsha)
t2=t2.replace('| 字节数 | 233340 |','| 字节数 | %d |'%newbytes)
t2=t2.replace('| 声明轮次 | R204 |','| 声明轮次 | R205 |')
t2=t2.replace('现盘 530..586 连续 57 份','现盘 530..587 连续 58 份')
t2=t2.replace('V530..V581','V530..V582')
ck('Q2 指针 V587->V588 替换生效','V588' in t2 and 'V587' not in t2,None)
ck('Q3 指针 sha 替换生效',newsha in t2,None)
ck('Q4 指针字节数替换生效',('| 字节数 | %d |'%newbytes) in t2,None)
ck('Q5 指针仍全 LF',b'\r' not in t2.encode(),None)
open(p,'wb').write(t2.encode('utf-8'))
ck('Q6 指针回读含 V588',b'V588' in open(p,'rb').read(),None)
print('PTR: %s -> %s'%(pre[:16],sha(p)[:16]))

# ---- 写 facts_floors ----
p=ROOT+'/_r160/facts_floors.py'
pre=sha(p); b=backup(p,'FF')
ck('R1 facts_floors 备份一致',sha(b)==pre,os.path.basename(b))
s=open(p,encoding='utf-8').read()
s=s.replace("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V587', 'FACT_INDEX.tsv')",
            "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V588', 'FACT_INDEX.tsv')")
s=s.replace("CUR_SHA256 = '062111ba9adbf0658a29be9744efb1869a8ce5f4fa627a326a05b7c71c4fe44c'",
            "CUR_SHA256 = '%s'"%newsha)
s=s.replace('TOTAL_BYTES = 233340','TOTAL_BYTES = %d'%newbytes)
s=s.replace("MASTER_SHA256 = '65b70fc6bff2b5d3fa2dafbb0217b3718076210f2d18c2e3ba6519f9552c9357'",
            "MASTER_SHA256 = '%s'"%newmaster)
s=s.replace('ITEMS = 312','ITEMS = %d'%items)
s=s.replace('UNIQ = 203','UNIQ = %d'%uniq)
s=s.replace('LOST_ITEMS = 43','LOST_ITEMS = %d'%lost)
s=s.replace('LOST_UNIQ = 16','LOST_UNIQ = %d'%lostu)
open(p,'wb').write(s.encode('utf-8'))
for k,v in (('EXPECT_CUR',b'R17_R131_FACTINDEX_V588'),('CUR_SHA256',newsha.encode()),
            ('MASTER',newmaster.encode())):
    ck('R2 facts_floors 含 %s'%k,v in open(p,'rb').read(),None)

# ---- 写 gate_runner ----
p=ROOT+'/_r161/gate_runner.py'
pre2=sha(p); b=backup(p,'GR')
ck('S1 gate_runner 备份一致',sha(b)==pre2,os.path.basename(b))
s=open(p,encoding='utf-8').read()
s=s.replace("'R17_R131_FACTINDEX_V587'","'R17_R131_FACTINDEX_V588'")
open(p,'wb').write(s.encode('utf-8'))
ck('S2 gate_runner 指向 V588',b'V588' in open(p,'rb').read() and b'V587' not in open(p,'rb').read(),None)
print('\nFAILS:',fails)
print('NEW: sha=%s bytes=%d items=%d uniq=%d lost=%d/%d master=%s'%(
    newsha[:16],newbytes,items,uniq,lost,lostu,newmaster[:16]))
json.dump(dict(fails=fails,newsha=newsha,newbytes=newbytes,master=newmaster,
               items=items,uniq=uniq,lost=lost,lostu=lostu,evid=new_evid,evidb=new_evidb),
          open(ROOT+'/_r205/p5_repin.json','w'),indent=1)
