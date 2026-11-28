# -*- coding: utf-8 -*-
"""R208 p6：把四件套与指针里「V588 / bfad05b0 / 239742」的过时引用订正为 V589 现盘值，
并补记本轮 FACT_INDEX 升版这一交付。CR 计数必须不变。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; BASE=LEAD+'/R17_LEAD_BASELINE'
NEW=LEAD+'/next_re_20261117_r14/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
S16=SHA[:8]
W=[('V588','V589',0),('bfad05b0',S16,0),('239742',str(BYTES),0)]
targets=[(LEAD+'/next_re_20261117_r14/R14_COMMON.md',1081,'r14b'),
         (LEAD+'/GOAL_THREE_TARGETS_20261018.md',337,'goalb'),
         (LEAD+'/LEAD_LOCK',137,'lockb'),
         (LEAD+'/next_re_20261117_r14/STATUS_BOARD.md',0,'boardb'),
         (LEAD+'/next_re_20261117_r14/FACT_INDEX_CURRENT.md',0,'ptrb')]
out=[]
for p,exp,tag in targets:
    b=open(p,'rb').read()
    cr0=b.count(b'\r\n'); assert cr0==exp,(p,cr0,exp)
    bak=BASE+'/'+os.path.basename(p)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    n1=t
    for old,new,_ in W:
        # 只替换本轮自己写进去的引用：R14/GOAL/LOCK/BOARD 里出现次数应很少
        n1=n1.replace(old,new)
    nb=n1.encode('utf-8')
    if nb!=b:
        tmp=p+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,p)
    d=open(p,'rb').read()
    cr1=d.count(b'\r\n')
    print('%-46s CR %d->%d %s  bytes %d->%d  replaced=%d' %
          (os.path.basename(p),cr0,cr1,'OK' if cr1==exp else 'BAD',len(b),len(d),sum(t.count(o) for o,_,_ in W)))
    assert cr1==exp,(p,cr1)
    out.append(dict(f=p,cr=cr1,bytes=len(d),sha=hashlib.sha256(d).hexdigest()))
# 指针的「声明依据」补一条 R208 订正（版本号区间 530..589）
P=LEAD+'/next_re_20261117_r14/FACT_INDEX_CURRENT.md'
b=open(P,'rb').read(); t=b.decode('utf-8')
old='现依据固定为「版本号最大（现盘 530..587 连续 58 份）+ 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」）。'
new='现依据固定为「版本号最大（现盘 530..589 连续 60 份）+ 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」）。**R208 订正**：R208 新增 V589（把 0x7f9594 = type_info 共享 vftable 的结案写入 F01），故上式区间由 530..587 改为 530..589。'
if old in t:
    t2=t.replace(old,new)
    open(P+'.t','wb').write(t2.encode('utf-8')); os.replace(P+'.t',P)
    print('pointer 声明依据 已订正')
else:
    print('!! pointer 声明依据 未命中，需人工确认')
json.dump(out,open(ROOT+'/_r208/p6_fixrefs.json','w'),ensure_ascii=False,indent=1)
