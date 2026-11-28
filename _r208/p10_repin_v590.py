# -*- coding: utf-8 -*-
"""R208 p10：V590 升版后的指针/facts_floors/gate_runner 同步重钉（顺序：版本目录已先写）。
每处写入：wx 独占备份 -> 断言旧 sha -> 一次写入 -> 回读校验。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V590/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
print('V590 sha',SHA[:16],'bytes',BYTES,'lines',raw.count(b'\n'))
def edit(path,pairs,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1,'pattern %r count=%d'%(old[:70],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-42s %d -> %d B (cr %d)'%(os.path.basename(path),len(b),len(nb),nb.count(b'\r\n')))
edit(TIER+'/FACT_INDEX_CURRENT.md',[
 ('| 版本目录 | R17_R131_FACTINDEX_V589 |','| 版本目录 | R17_R131_FACTINDEX_V590 |'),
 ('| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv |',
  '| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V590/FACT_INDEX.tsv |'),
 ('| sha256 | 89bb71baea5299896a9a85df4029dfeeb07dc613bf381657365a56183d4b03f6 |','| sha256 | %s |'%SHA),
 ('| 字节数 | 240722 |','| 字节数 | %d |'%BYTES),
 ('| 声明轮次 | R208 |','| 声明轮次 | R208（V590） |'),
 ('故上式区间由 530..587 改为 530..589。','故上式区间由 530..587 改为 530..589；**R208 再订正**：R208 收口期又新增 V590（把 T 形态双编码 + I 形态 -8 调整写入 F29），区间改为 **530..590**。'),
],'ptr590')
FF=ROOT+'/_r160/facts_floors.py'
edit(FF,[
 ("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V589', 'FACT_INDEX.tsv')",
  "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V590', 'FACT_INDEX.tsv')"),
 ("CUR_SHA256 = '89bb71baea5299896a9a85df4029dfeeb07dc613bf381657365a56183d4b03f6'","CUR_SHA256 = '%s'"%SHA),
 ('TOTAL_BYTES = 240722','TOTAL_BYTES = %d'%BYTES),
],'ff590')
# MASTER 重算：按 facts_floors 既有 canon 规则（与 p5 同法）
t=open(FF,encoding='utf-8').read()
def block(name):
    m=re.search(r'^%s = \{\n(.*?)\n\}'%name,t,re.S|re.M); return m.group(1)
def canon_pairs(txt): return '\n'.join(re.findall(r"(    '[^']*': '[^']*',)",txt))
def canon_tuples(txt): return '\n'.join(re.findall(r"(    '[^']*': \(\d+, \d+\),)",txt))
def canon_evid(txt): return '\n'.join('    '+l.strip() for l in txt.split('\n') if l.strip().startswith("'"))
def canon_nums(txt): return '\n'.join(re.findall(r"(    '[^']*': \d+,)",txt))
def one(name):
    return re.search(r'^%s = (\d+)$'%name,t,re.M).group(1)
payload='\n'.join([SHA,str(BYTES),canon_pairs(block('GRADES')),canon_tuples(block('FLOORS')),
                   canon_evid(block('EVID')),canon_nums(block('EVIDB')),canon_nums(block('LOST')),
                   one('ITEMS'),one('UNIQ'),one('LOST_ITEMS'),one('LOST_UNIQ')])
master=hashlib.sha256(payload.encode()).hexdigest()
print('master recomputed',master[:16])
edit(FF,[("MASTER_SHA256 = '96f504e72a3da2d72cf674369bfe6886229aba2653dde60918822c2b4f3a4665'","MASTER_SHA256 = '%s'"%master)],'ff590b')
edit(ROOT+'/_r161/gate_runner.py',[
 ("LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V589', 'FACT_INDEX.tsv')",
  "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V590', 'FACT_INDEX.tsv')"),
],'gr590')
out={'sha':SHA,'bytes':BYTES,'master':master,'dir':'R17_R131_FACTINDEX_V590'}
json.dump(out,open(ROOT+'/_r208/p10_repin_v590.json','w'),ensure_ascii=False,indent=1)
