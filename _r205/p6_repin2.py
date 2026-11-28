#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 重钉二：EVID[F01] / EVIDB[F01] / ITEMS / UNIQ / CUR_SHA256 / TOTAL_BYTES / MASTER 同步到 V588。
fail-closed：写完先跑一次无 --ignore-pin 的 facts_floors，必须 0 FAIL。
"""
import os,re,hashlib,subprocess,json,time
ROOT='/home/t628/projects/ra2-campaign-forge'
NEW=ROOT+'/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V588/FACT_INDEX.tsv'
BL=ROOT+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp

newsha=sha(NEW); newbytes=len(open(NEW,'rb').read())
raw=open(NEW,'rb').read().decode('utf-8').split('\n')
for line in raw[1:]:
    if line.startswith('F01\t'):
        ev=[x.strip() for x in line.split('\t')[3].split(';') if x.strip()]
        evb=len(line.split('\t')[3].encode()); break
ck('A1 F01 EVID 条数 == 30',len(ev)==30,len(ev))
ck('A2 F01 col4 bytes',True,evb)

p=ROOT+'/_r160/facts_floors.py'
pre=sha(p); b=backup(p,'FF2')
ck('A3 备份一致',sha(b)==pre,os.path.basename(b))
s=open(p,encoding='utf-8').read()

# EVID['F01'] 替换
m=re.search(r"    'F01': \[(.*?)\],\n",s,re.S)
ck('A4 找到 EVID[F01]',m is not None,None)
newlist='    \'F01\': [%s],\n'%(', '.join("'%s'"%x for x in ev))
s=s[:m.start()]+newlist+s[m.end():]
# EVIDB['F01']
s=re.sub(r"    'F01': 529,", "    'F01': %d,"%evb, s)
# FLOORS 的 F01 字节下限（6847, 15247）→ 保持 stmt 下限、evid 下限提到新值
s=s.replace("    'F01': (6847, 15247),","    'F01': (6847, 15340),")
# 常量
s=re.sub(r"CUR_SHA256 = '[0-9a-f]{64}'","CUR_SHA256 = '%s'"%newsha,s)
s=re.sub(r"TOTAL_BYTES = \d+","TOTAL_BYTES = %d"%newbytes,s)
open(p,'wb').write(s.encode('utf-8'))

# 求新 D7 与 MASTER
r=subprocess.run(['python3','-c','''
import sys,re,subprocess
out=subprocess.run(["python3","%s/_r160/facts_floors.py","%s","--ignore-pin"],capture_output=True,text=True).stdout
m=re.search(r"D7 evidence: items=(\\d+) uniq=(\\d+) lost_items=(\\d+) lost_uniq=(\\d+)",out)
print("D7",m.groups())
m2=re.search(r"D9 master pin: ([0-9a-f]{64})",out)
print("MASTER",m2.group(1))
'''%(ROOT,NEW)],capture_output=True,text=True,timeout=300)
print('   '+r.stdout.strip().replace('\n','\n   '))
mm=re.search(r"D7 \('(\d+)', '(\d+)', '(\d+)', '(\d+)'\)",r.stdout)
mv=re.search(r'MASTER ([0-9a-f]{64})',r.stdout)
ck('A5 拿到 D7',mm is not None,r.stdout[:120])
ck('A6 拿到 MASTER',mv is not None,None)
items,uniq,lost,lostu=[int(x) for x in mm.groups()]
master=mv.group(1)

s=open(p,encoding='utf-8').read()
s=re.sub(r"ITEMS = \d+","ITEMS = %d"%items,s)
s=re.sub(r"UNIQ = \d+","UNIQ = %d"%uniq,s)
s=re.sub(r"LOST_ITEMS = \d+","LOST_ITEMS = %d"%lost,s)
s=re.sub(r"LOST_UNIQ = \d+","LOST_UNIQ = %d"%lostu,s)
s=re.sub(r"MASTER_SHA256 = '[0-9a-f]{64}'","MASTER_SHA256 = '%s'"%master,s)
open(p,'wb').write(s.encode('utf-8'))

# fail-closed 验证
r2=subprocess.run(['python3',ROOT+'/_r160/facts_floors.py'],capture_output=True,text=True,timeout=300)
out=r2.stdout+r2.stderr
ck('B1 facts_floors exit 0',r2.returncode==0,r2.returncode)
ck('B2 无 FAIL 行','FAIL' not in out,[l for l in out.split('\n') if 'FAIL' in l][:4])
ck('B3 D9 pin 一致','D9 master pin: %s (pinned %s)'%(master,master) in out,None)
ck('B4 D10 指针三向一致','all agree' in out or 'vs CUR' in out,None)
print('\nFAILS:',fails)
print('items=%d uniq=%d lost=%d/%d master=%s evidb=%d'%(items,uniq,lost,lostu,master[:16],evb))
json.dump(dict(fails=fails,newsha=newsha,newbytes=newbytes,master=master,
               items=items,uniq=uniq,lost=lost,lostu=lostu,evb=evb,evid=len(ev)),
          open(ROOT+'/_r205/p6_repin2.json','w'),indent=1)
