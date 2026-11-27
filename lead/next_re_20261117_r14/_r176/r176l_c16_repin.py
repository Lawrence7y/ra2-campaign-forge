# -*- coding: utf-8 -*-
"""R176 C16 重钉 174 -> 175 节（只插 181）。旧表重算 sha 命中 0bfc18cd… 作硬闸；三反控。"""
import ast,hashlib,os,re,sys,time
CD='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py'
RC='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R14_COMMON.md'
BASE='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
src=open(CD,encoding='utf-8').read()
tree=ast.parse(src)
fl=None; pin=None
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        if node.targets[0].id=='C16_FLOORS': fl=ast.literal_eval(node.value)
        if node.targets[0].id=='C16_FLOORS_SHA256': pin=ast.literal_eval(node.value)
ck('A1 C16_FLOORS via ast',isinstance(fl,dict) and len(fl)==174,'%d'%(len(fl) if fl else -1))
ck('A2 pin via ast',pin=='0bfc18cd3c2df25f98c8add57819d1d023c8d9408f0c92414ea56176c8ac78db',pin[:16])
norm='\n'.join('%d:%d'%(k,fl[k]) for k in sorted(fl))
oldsha=hashlib.sha256(norm.encode()).hexdigest()
ck('B1 HARD GATE old table reproduces pin',oldsha==pin,oldsha[:16])
# 实测 §2.181 的字节
rc=open(RC,'rb').read().decode('utf-8')
secs={}
cur=None; buf=[]
for ln in rc.split('\n'):
    m=re.match(r'^##\s+2\.(\d+)\b',ln)
    if m:
        if cur is not None: secs[cur]=len('\n'.join(buf).encode())
        cur=int(m.group(1)); buf=[ln]
    elif cur is not None: buf.append(ln)
if cur is not None: secs[cur]=len('\n'.join(buf).encode())
ck('C1 section count',len(secs)==175,'%d'%len(secs))
ck('C2 181 measured',181 in secs,'%d'%secs.get(181,-1))
ck('C3 181 not in old table',181 not in fl,'in=%s'%(181 in fl))
floor=secs[181]//2
print('  §2.181 = %d B -> floor %d'%(secs[181],floor))
# 反控 A：floor 取实测值本身则「不缩水」语义退化（记录用）
ck('D0 sanity floor < measured',floor<secs[181],'%d<%d'%(floor,secs[181]))
newfl=dict(fl); newfl[181]=floor
newnorm='\n'.join('%d:%d'%(k,newfl[k]) for k in sorted(newfl))
newsha=hashlib.sha256(newnorm.encode()).hexdigest()
ck('E1 new sha differs',newsha!=oldsha,newsha[:16])
# 反控 1：floor +1 使 sha 变
f1=dict(newfl); f1[181]=floor+1
ck('E2 neg-ctrl floor+1 changes sha',hashlib.sha256('\n'.join('%d:%d'%(k,f1[k]) for k in sorted(f1)).encode()).hexdigest()!=newsha)
# 反控 2：删 181 使 sha 回旧
f2=dict(newfl); del f2[181]
ck('E3 neg-ctrl removing 181 returns old sha',hashlib.sha256('\n'.join('%d:%d'%(k,f2[k]) for k in sorted(f2)).encode()).hexdigest()==oldsha)
# 反控 3：改 180 抄 179
f3=dict(newfl); f3[180]=fl[179]
ck('E4 neg-ctrl 180:=179 changes sha',hashlib.sha256('\n'.join('%d:%d'%(k,f3[k]) for k in sorted(f3)).encode()).hexdigest()!=newsha)
ck('E5 other 174 keep values',all(fl[k]==newfl[k] for k in fl))
if F: print('ABORT'); sys.exit(1)
ts=time.strftime('%Y%m%d_%H%M%S')
bp=os.path.join(BASE,'check_disc.py.before_r176c16_%s.bak'%ts)
with open(bp,'xb') as f: f.write(src.encode())
new=src.replace('   180: %d,\n}'%fl[180], '   180: %d,\n   181: %d,\n}'%(fl[180],floor))
ck('F1 insert applied',new!=src and new.count('   181: %d,\n'%floor)==1)
new=new.replace("C16_FLOORS_SHA256 = '%s'"%pin, "C16_FLOORS_SHA256 = '%s'"%newsha)
ck('F2 pin replaced',new.count(newsha)==1)
tree2=ast.parse(new)
fl2=None;pin2=None
for node in tree2.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        if node.targets[0].id=='C16_FLOORS': fl2=ast.literal_eval(node.value)
        if node.targets[0].id=='C16_FLOORS_SHA256': pin2=ast.literal_eval(node.value)
ck('G1 new table 175',len(fl2)==175,'%d'%len(fl2))
ck('G2 new table self-consistent',hashlib.sha256('\n'.join('%d:%d'%(k,fl2[k]) for k in sorted(fl2)).encode()).hexdigest()==pin2)
with open(CD,'wb') as f: f.write(new.encode())
ck('H1 readback',open(CD,encoding='utf-8').read()==new)
print('NEW pin = %s  (181 floor %d)'%(newsha,floor))
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
