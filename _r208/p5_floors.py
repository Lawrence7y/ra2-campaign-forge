# -*- coding: utf-8 -*-
"""R208 p5：facts_floors 常量升版（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256）+ gate_runner LEDGER。
MASTER_SHA256 按 facts_floors 的 canon_* 规则重算（与 gate_runner.canon 同一规则），双脚本交叉校验。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
FF=ROOT+'/_r160/facts_floors.py'
def bakwrite(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b,bak
def commit(path,nb,ob):
    tmp=path+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-40s %d -> %d B'%(os.path.basename(path),len(ob),len(nb)))

b,bak=bakwrite(FF,'ff')
t=b.decode('utf-8')
t2=t.replace("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V588', 'FACT_INDEX.tsv')",
             "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V589', 'FACT_INDEX.tsv')")
assert t2!=t
t3=t2.replace("CUR_SHA256 = 'bfad05b0a5d95dbc9e9862d15fdd43f0427f02c276476319a2760b5835bc20b4'",
              "CUR_SHA256 = '%s'"%SHA)
assert t3!=t2
t4=re.sub(r"^TOTAL_BYTES = 239742$","TOTAL_BYTES = %d"%BYTES,t3,flags=re.M)
assert t4!=t3
# 重算 MASTER（复制 facts_floors 的 canon 规则）
def block(txt,name):
    m=re.search(r'^%s = \{\n(.*?)\n\}'%name,txt,re.S|re.M); return m.group(1)
def canon_g(d): return '\n'.join("    '%s': '%s',"%(k,sorted(re.findall(r"'([^']*)': '([^']*)'",d))[0][0] if False else k) for k in [])
g=block(t4,'GRADES'); f=block(t4,'FLOORS'); e=block(t4,'EVID'); eb=block(t4,'EVIDB'); l=block(t4,'LOST')
def canon_g2(txt): return '\n'.join(re.findall(r"(    '[^']*': '[^']*',)",txt))
def canon_f(txt): return '\n'.join(re.findall(r"(    '[^']*': \(\d+, \d+\),)",txt))
def canon_e(txt):
    out=[]
    for line in txt.split('\n'):
        s=line.strip()
        if s.startswith("'"): out.append('    '+s)
    return '\n'.join(out)
def canon_num(txt): return '\n'.join(re.findall(r"(    '[^']*': \d+,)",txt))
def one(txt,name):
    m=re.search(r'^%s = (\d+)$'%name,txt,re.M); return m.group(1)
payload='\n'.join([SHA,str(BYTES),canon_g2(g),canon_f(f),canon_e(e),canon_num(eb),canon_num(l),
                   one(t4,'ITEMS'),one(t4,'UNIQ'),one(t4,'LOST_ITEMS'),one(t4,'LOST_UNIQ')])
master=hashlib.sha256(payload.encode()).hexdigest()
print('recomputed master',master[:16])
t5=re.sub(r"^MASTER_SHA256 = '[0-9a-f]{64}'$","MASTER_SHA256 = '%s'"%master,t4,flags=re.M)
assert t5!=t4
commit(FF,t5.encode('utf-8'),b)

# gate_runner LEDGER
GR=ROOT+'/_r161/gate_runner.py'
b2,bak2=bakwrite(GR,'gr')
t=b2.decode('utf-8')
t2=t.replace("LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V588', 'FACT_INDEX.tsv')",
             "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V589', 'FACT_INDEX.tsv')")
assert t2!=t
commit(GR,t2.encode('utf-8'),b2)
json.dump(dict(sha=SHA,bytes=BYTES,master=master),open(ROOT+'/_r208/p5_floors.json','w'),ensure_ascii=False,indent=1)
