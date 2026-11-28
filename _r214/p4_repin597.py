# -*- coding: utf-8 -*-
"""R214 p4：指针 + facts_floors(EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER) + gate_runner.LEDGER + C16_FLOORS(222) 全重钉 V597。"""
import os,re,hashlib,importlib.util,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
osha,ob,nsha,nb=open(ROOT+'/_r214/p1_out.txt').read().split(); ob=int(ob); nb=int(nb)
print('V596 %s %d -> V597 %s %d'%(osha[:16],ob,nsha[:16],nb))
def wx(path,tag):
    raw=open(path,'rb').read()
    bak=BASE+'/R214_%s_20261128.bak'%tag
    if not os.path.exists(bak):
        fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
    assert open(bak,'rb').read()==raw,'备份与现盘不一致: '+bak
    return raw
# ---------- 1 指针 FACT_INDEX_CURRENT.md ----------
PTR=TIER+'/FACT_INDEX_CURRENT.md'
b=wx(PTR,'ptr597')
t=b.decode('utf-8')
for old,new,cnt in (('| sha256 | %s |'%osha,'| sha256 | %s |'%nsha,1),
                    ('| 字节数 | %d |'%ob,'| 字节数 | %d |'%nb,1),
                    ('R17_R131_FACTINDEX_V596','R17_R131_FACTINDEX_V597',2)):
    assert t.count(old)==cnt,(old,t.count(old)); t=t.replace(old,new)
t=t.replace('| 声明轮次 | R213（V596） |','| 声明轮次 | R214（V597） |')
t=t.replace('**R213 再升 V596**','**R214 再升 V597**')
open(PTR,'wb').write(t.encode('utf-8')); assert open(PTR,'rb').read()==t.encode('utf-8')
print('PTR -> V597  sha=%s bytes=%d'%(nsha[:16],nb))
# ---------- 2 facts_floors.py ----------
FF=ROOT+'/_r160/facts_floors.py'
raw=wx(FF,'floors597')
s=raw.decode('utf-8')
for old,new in (('R17_R131_FACTINDEX_V596','R17_R131_FACTINDEX_V597'),
                ("CUR_SHA256 = '%s'"%osha,"CUR_SHA256 = '%s'"%nsha),
                ('TOTAL_BYTES = %d'%ob,'TOTAL_BYTES = %d'%nb)):
    assert s.count(old)==1,(old,s.count(old)); s=s.replace(old,new)
open(FF,'wb').write(s.encode('utf-8')); assert open(FF,'rb').read()==s.encode('utf-8')
spec=importlib.util.spec_from_file_location('ff214',FF)
m=importlib.util.module_from_spec(spec); sys.argv=['x','--ignore-pin']
try: spec.loader.exec_module(m)
except SystemExit as e: print('floors exited %s (constants bound)'%e.code)
newmaster=hashlib.sha256(('\n'.join([m.CUR_SHA256,str(m.TOTAL_BYTES),m.canon_g(m.GRADES),m.canon_f(m.FLOORS),
  m.canon_e(m.EVID),m.canon_eb(m.EVIDB),m.canon_l(m.LOST),str(m.ITEMS),str(m.UNIQ),
  str(m.LOST_ITEMS),str(m.LOST_UNIQ)])).encode()).hexdigest()
print('MASTER %s -> %s'%(m.MASTER_SHA256[:16],newmaster[:16]))
r2=open(FF,'rb').read(); s2=r2.decode('utf-8')
oldm="MASTER_SHA256 = '%s'"%m.MASTER_SHA256
assert s2.count(oldm)==1,s2.count(oldm)
nb2=s2.replace(oldm,"MASTER_SHA256 = '%s'"%newmaster).encode('utf-8')
open(FF,'wb').write(nb2); assert open(FF,'rb').read()==nb2
print('floors 四常量 -> V597')
# ---------- 3 gate_runner.LEDGER ----------
GR=ROOT+'/_r161/gate_runner.py'
g=wx(GR,'gr597'); gt=g.decode('utf-8')
old="'R17_R131_FACTINDEX_V596'"
assert gt.count(old)==1,gt.count(old)
gt=gt.replace(old,"'R17_R131_FACTINDEX_V597'")
open(GR,'wb').write(gt.encode('utf-8')); assert open(GR,'rb').read()==gt.encode('utf-8')
print('gate_runner LEDGER -> V597')
# ---------- 4 C16_FLOORS 纳入 222 ----------
CD=TIER+'/check_disc.py'
src=open(TIER+'/R14_COMMON.md','r',encoding='utf-8').read()
mm=re.search(r"^## 2\.222 .*?(?=^## 2\.|\Z)",src,re.S|re.M)
assert mm,'§2.222 not found'
n=len(mm.group(0).encode('utf-8')); lo=int(n*0.75)
print('§2.222 bytes=%d floor=%d'%(n,lo))
cb=wx(CD,'cd222'); ct=cb.decode('utf-8')
blk=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',ct,re.S).group(0)
pairs=re.findall(r'^    (\d+): (\d+),$',blk,re.M)
print('pins before:',len(pairs),'last:',pairs[-1])
assert not any(k=='222' for k,v in pairs)
ct2=ct.replace(blk, blk.replace('\n}', '\n    222: %d,\n}'%lo))
blk2=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',ct2,re.S).group(1)
pairs2=re.findall(r'^    (\d+): (\d+),$',blk2,re.M)
norm='\n'.join('%s:%s'%p for p in pairs2)
sha=hashlib.sha256(norm.encode()).hexdigest()
oldsha=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",ct2).group(1)
ct2=ct2.replace(oldsha,sha)
open(CD,'wb').write(ct2.encode('utf-8')); assert open(CD,'rb').read()==ct2.encode('utf-8')
print('C16 pins after:',len(pairs2),'sha %s -> %s'%(oldsha[:12],sha[:12]))
