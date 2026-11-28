#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十一刀（权威口径）：单次连续 disasm_lite 全段扫描（不做分块，避免块边界失步）。
B1 全段指令条数 + 覆盖字节数（衡量线性扫描同步性）。
B2 L 的 78 张表头的指令级立即数引用：总条数 / 每表头计数 / 零命中张数。
B3 与 m9（64KB 分块）交叉校验：连续口径必须 >= 分块口径。
B4 install 形态分类：mov [reg],imm / mov [reg+disp],imm / push imm / 其它。
B5 每张表头的「安装者函数数」（按 call/jmp 起点 ∪ 填充 归属）。
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
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
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
Lset=set(LIN)
ck('B0 L=78 / 主表 954 / COL 1214',(len(LIN),len(MAIN),len(COL))==(78,954,1214),(len(LIN),len(MAIN),len(COL)))
# 单次连续扫描
allins=[]; nins=0; cov=0
hits=[]; starts=set(); prev_ret=False
for ins in md.disasm_lite(P.RAW[T['rawptr']:T['rawptr']+T['rawsize']],LO):
    a,sz,mn,op=ins[0],ins[1],ins[2],ins[3]
    nins+=1; cov+=sz
    allins.append((a,mn,op,sz))
    if '0x' in op:
        for m in re.finditer(r'(?:^|[ ,\[])(0x[0-9a-f]{6,8})(?=[,\] ]|$)',op):
            try: v=int(m.group(1),16)
            except: continue
            if v in Lset: hits.append((a,mn,op,v))
print('   B1 指令条数=%d  覆盖字节=%d / 段 rawsize=%d'%(nins,cov,T['rawsize']))
ck('B1a 线性扫描覆盖 >= 99% 段字节',cov>=0.99*T['rawsize'],(cov,T['rawsize']))
ck('B2a 连续口径命中数 >= 分块口径 285',len(hits)>=285,(len(hits),285))
cnt=collections.Counter(h[3] for h in hits)
nohit=[v for v in LIN if v not in cnt]
print('   B2 命中 %d 条 / 涉及表头 %d / 零命中 %d'%(len(hits),len(cnt),len(nohit)))
ck('B2b 零命中张数为 0（10 张均已被 m10 复现为指令立即数）',len(nohit)==0,len(nohit))
if nohit: print('      零命中：'+' '.join('%08X'%v for v in nohit))
# B4 形态
form=collections.Counter()
for a,mn,op,v in hits:
    if mn=='mov' and re.match(r'dword ptr \[[a-z]{2}(?: \+ 0x[0-9a-f]+)?\], 0x',op): f='mov[mem],imm'
    elif mn=='push': f='push imm'
    elif mn=='mov' and re.match(r'e[a-z]{2}, 0x',op): f='mov reg,imm'
    elif mn=='cmp': f='cmp'
    elif mn in ('lea','add','sub','and','or','call','jmp'): f=mn
    else: f='other:'+mn
    form[f]+=1
print('   B4 形态分布：%s'%dict(form))
mm=form.get('mov[mem],imm',0)
ck('B4a mov[mem],imm 是主形态（占比 >= 0.8）', mm>=0.8*len(hits), (mm,len(hits)))
# B5 表头被多少个不同函数安装（近似：按 4KB 窗口聚类）
blk=collections.defaultdict(set)
for a,mn,op,v in hits: blk[v].add(a>>12)
print('   B5 每表头的 4KB 安装窗口数分布：%s'%collections.Counter(len(s) for s in blk.values()))
json.dump(dict(nins=nins,cov=cov,hits=[[hex(a),mn,op,hex(v)] for a,mn,op,v in hits],
  cnt={'%08X'%k:v for k,v in cnt.items()},form=dict(form)),open('_r195/m11_auth.json','w'),indent=1)
print('\nFAILS=%d'%len(fails))
