# -*- coding: utf-8 -*-
"""R209 p3：facts_floors MASTER_SHA256 重算（复制 facts_floors 的 canon_* 规则，与 gate_runner.canon 交叉校验）
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V591/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
FF=ROOT+'/_r160/facts_floors.py'
def bakwrite(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r209_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b,bak
def commit(path,nb,ob):
    tmp=path+'.r209tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-40s %d -> %d B'%(os.path.basename(path),len(ob),len(nb)))

b,bak=bakwrite(FF,'ffm')
t=b.decode('utf-8')
def block(txt,name):
    m=re.search(r'^%s = \{\n(.*?)\n\}'%name,txt,re.S|re.M); return m.group(1)
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
payload='\n'.join([SHA,str(BYTES),canon_g2(block(t,'GRADES')),canon_f(block(t,'FLOORS')),
                   canon_e(block(t,'EVID')),canon_num(block(t,'EVIDB')),canon_num(block(t,'LOST')),
                   one(t,'ITEMS'),one(t,'UNIQ'),one(t,'LOST_ITEMS'),one(t,'LOST_UNIQ')])
master=hashlib.sha256(payload.encode()).hexdigest()
old=re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'$",t,re.M).group(1)
print('master %s -> %s'%(old[:16],master[:16]))
t2=re.sub(r"^MASTER_SHA256 = '[0-9a-f]{64}'$","MASTER_SHA256 = '%s'"%master,t,flags=re.M)
assert t2!=t
assert re.search(r"^EXPECT_CUR = os\.path\.join\(TIER, 'R17_R131_FACTINDEX_V591'",t2,re.M)
commit(FF,t2.encode('utf-8'),b)
# gate_runner
GR=ROOT+'/_r161/gate_runner.py'
b2,_=bakwrite(GR,'gr591')
t=b2.decode('utf-8')
import re as _re
oldline=_re.search(r"LEDGER = os\.path\.join\(TIER, 'R17_R131_FACTINDEX_V\d+', 'FACT_INDEX\.tsv'\)",t)
assert oldline, 'LEDGER 行未找到'
print('gate_runner LEDGER 原行:',oldline.group(0))
t2=t.replace(oldline.group(0),"LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V591', 'FACT_INDEX.tsv')")
assert t2!=t
commit(GR,t2.encode('utf-8'),b2)
json.dump(dict(sha=SHA,bytes=BYTES,master=master,old_master=old),
          open(ROOT+'/_r209/p3_master.json','w'),ensure_ascii=False,indent=1)
