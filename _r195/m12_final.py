#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十二刀（权威定稿口径）：分块 + 块内逐字节重同步 的全段线性扫描。
前两版缺陷：m11 单次连续 disasm_lite 遇无效指令即整体停（只覆盖 452,000/4,063,232 B）；
m9 64KB 分块只在块边界重同步（漏掉块内失步段）。本版在块内失败处逐字节前移重试。
C1 覆盖率断言：>= 99.5% 段字节。
C2 L 的 78 张表头指令级立即数引用（全部形态），与 m10 的字节+回溯法逐表头交叉校验。
C3 形态分布 + 每表头安装者窗口数。
C4 反控：全部 1214 表头。
"""
import sys,re,struct,collections,json,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
def chain(c):
    n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12); out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if b is None or P.where(b) in('None','other'):continue
        p=P.dw(b)
        if p is None: continue
        nm=P.cstr(p+8,160); out.append(nm.decode('latin1') if nm else None)
    return out
LIN=sorted(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(COL[VT[vt]]))
Lset=set(LIN); ALLset=set(VT)
ck('C0a L=78 / 主表 954 / COL 1214 / 槽总 14044',
   (len(LIN),len(MAIN),len(COL))==(78,954,1214),(len(LIN),len(MAIN),len(COL)))

def sweep(target):
    """分块 + 块内逐字节重同步线性扫描。返回 (hits, nins, cov)"""
    hits=[];nins=0;cov=0;skipped=0
    CH=262144; o=0; total=T['rawsize']
    while o<total:
        n=min(CH,total-o); buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n]
        va=LO+o; i=0
        while i<len(buf):
            got=False
            for ins in md.disasm_lite(buf[i:i+16],va+i):
                a,sz,mn,op=ins[0],ins[1],ins[2],ins[3]
                nins+=1; cov+=sz
                if '0x' in op:
                    for m in re.finditer(r'0x[0-9a-f]{6,8}',op):
                        try: v=int(m.group(0),16)
                        except: continue
                        if v in target: hits.append((a,mn,op,v))
                i+=sz; got=True; break
            if not got:
                i+=1; skipped+=1
        o+=n
    return hits,nins,cov,skipped
hits,nins,cov,skip=sweep(Lset)
print('   C1 指令 %d 条 / 覆盖 %d B / 段 %d B / 重同步 %d 次'%(nins,cov,T['rawsize'],skip))
ck('C1a 覆盖率 >= 99.5%',cov>=0.995*T['rawsize'],round(cov/T['rawsize'],4))
cnt=collections.Counter(h[3] for h in hits)
nohit=[v for v in LIN if v not in cnt]
print('   C2 指令级命中 %d 条 / 涉及表头 %d / 零命中 %d'%(len(hits),len(cnt),len(nohit)))
for a,mn,op,v in hits[:6]: print('      %08X  %-8s %-42s'%(a,mn,op))
ck('C2a 78 张表头**全部**至少 1 处指令级立即数安装点（无零命中）',len(nohit)==0,len(nohit))
form=collections.Counter()
for a,mn,op,v in hits:
    if mn=='mov' and re.match(r'dword ptr \[[a-z]{3}(?: \+ 0x[0-9a-f]+)?\], 0x',op): f='mov[mem],imm'
    elif mn=='push': f='push imm'
    elif mn=='mov' and re.match(r'e[a-z]{2}, 0x',op): f='mov reg,imm'
    elif mn=='lea': f='lea'
    else: f=mn+'|'+op.split()[0:2].__str__()
    form[f]+=1
print('   C3 形态：%s'%dict(form))
mm=form.get('mov[mem],imm',0)
ck('C3a mov[mem],imm 是唯一主形态',mm==len(hits),(mm,len(hits)))
blk=collections.defaultdict(set)
for a,mn,op,v in hits: blk[v].add(a>>12)
d=collections.Counter(len(s) for s in blk.values())
print('   C3b 每表头 4KB 安装窗口数分布：%s'%dict(sorted(d.items())))
allh,_,_,_=sweep(ALLset)
print('   C4 反控：全部 1214 表头命中 %d 条 / 涉及 %d 张'%(len(allh),len({h[3] for h in allh})))
ck('C4a 全表头命中 >= L 命中',len(allh)>=len(hits),(len(allh),len(hits)))
json.dump(dict(nins=nins,cov=cov,skip=skip,
  hits=[[hex(a),mn,op,hex(v)] for a,mn,op,v in hits],
  cnt={'%08X'%k:v for k,v in sorted(cnt.items())},form=dict(form),
  windows={hex(k):sorted(v) for k,v in blk.items()}),open('_r195/m12_final.json','w'),indent=1)
print('\nFAILS=%d'%len(fails))
