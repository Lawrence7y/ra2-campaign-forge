# -*- coding: utf-8 -*-
"""R218 m21：冻结本轮最终引用数字（一条命令）。含正反控。
输出：真虚表/幻影/槽数/主视图/A 段父类/BCD 布局/disp 扫描 全部终值。
"""
import sys,collections,struct
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VA[base+4*k+4]=v
VT={v:c for v,c in VA.items() if P.where(P.dw(v))=='.text'}
PH=sorted(v for v in VA if v not in VT)
def slots(vt,cap=65536):
    o=[]
    while len(o)<cap and P.where(P.dw(vt+4*len(o)))=='.text': o.append(P.dw(vt+4*len(o)))
    return o
S={v:slots(v) for v in VT}
print('== 虚表口径 ==')
print('  COL=%d  候选(V-4==COL)=%d  真虚表(dw(V)落.text)=%d  幻影=%d'%(len(COL),len(VA),len(VT),len(PH)))
print('  双射: 单射=%s 满射=%s'%(len(set(VT.values()))==len(VT), set(VT.values())==CS))
print('  幻影清单 %s  内容(V 起 16B) %s'%([hex(x) for x in PH],[P.RAW[P.r2o(x):P.r2o(x)+16].hex() for x in PH]))
traw=P.RAW[P.B['.text']['rawptr']:P.B['.text']['rawptr']+P.B['.text']['rawsize']]
def refs(va):
    pat=struct.pack('<I',va); n=0; s=0
    while True:
        i=traw.find(pat,s)
        if i<0: break
        n+=1; s=i+1
    return n
print('  .text 内 dword 引用: 幻影=%s  0x7e8278=%d  0x7e1f50=%d'%([refs(x) for x in PH],refs(0x7e8278),refs(0x7e1f50)))
print('  总槽数(真)=%d  含幻影=%d   mdisp!=0 视图(真)=%d  含幻影=%d'%(
    sum(len(S[v]) for v in VT),sum(len(S[v]) for v in VT)+sum(len(slots(v)) for v in PH),
    sum(1 for v in VT if COL[VT[v]]['md_']!=0),sum(1 for v in VA if COL[VA[v]]['md_']!=0)))
FAM=collections.defaultdict(list)
for v,c in VT.items(): FAM[COL[c]['pCHD']].append(v)
fams=[(g,vs) for g,vs in FAM.items() if any(COL[VT[v]]['md_']==0 for v in vs)]
prim=[sorted([v for v in vs if COL[VT[v]]['md_']==0])[0] for g,vs in fams]
print('  族数=%d 主视图=%d 主视图 slot>=3=%d  全表 slot>=3=%d'%(len(fams),len(prim),
  sum(max(0,len(S[v])-3) for v in prim),sum(max(0,len(S[v])-3) for v in VT)))
print('\n== A 段：6 张超 256 表 ==')
PAR={0x7f5c70:0x7e8c94,0x7eb058:0x7e8c94,0x7e22a4:0x7e8c94,0x7e8c94:0x7f4960,0x7e3ebc:0x7f4960,0x7f4960:0x7f0508}
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
exp={0x7f5c70:'.?AVFootClass@@',0x7eb058:'.?AVFootClass@@',0x7e22a4:'.?AVFootClass@@',
     0x7e8c94:'.?AVTechnoClass@@',0x7e3ebc:'.?AVTechnoClass@@',0x7f4960:'.?AVRadioClass@@'}
def bcnames(vt):
    chd=COL[VT[vt]]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+0xc); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i); td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append((e,(nm or b'').decode('latin1'),P.dw(e+4)))
    return out
cov=diff=oob=0; ok=0
for vt in TGT:
    b=bcnames(vt); nm=COL[VT[vt]]['name']
    i=[k for k,x in enumerate(b) if x[1]==nm][0]
    if b[i+1][1]==exp[vt]: ok+=1
    S1=S[vt]; S2=S[PAR[vt]]
    for k in range(256,len(S1)):
        if k>=len(S2): oob+=1
        elif S1[k]==S2[k]: cov+=1
        else: diff+=1
    print('  %08x %-22s n=%3d 父=%-22s 6/6序=%s'%(vt,nm,len(S1),b[i+1][1],b[i+1][1]==exp[vt]))
print('  父类判定 %d/6 PASS ; 464 = cov %d + diff %d + oob %d ; 覆盖率 %.2f%%'%(ok,cov,diff,oob,100.0*cov/(cov+diff)))
print('  slot>=256 去重目标=%d  在本表低 256 槽内重复=%d'%(len(set(t for v in TGT for t in S[v][256:])),
   sum(1 for v in TGT if True for t in S[v][256:] if t in set(S[v][:256]))))
print('\n== BCD 布局 ==')
el=[]
for vt in TGT:
    chd=COL[VT[vt]]['pCHD']; arr=P.dw(chd+0xc); nb=P.dw(chd+8)
    el+=[P.dw(arr+4*i) for i in range(nb)]
def good(td):
    nm=P.cstr(td+8,256)
    return bool(nm) and nm[:3]==b'.?A' and nm[-2:]==b'@@'
g0=sum(1 for e in el if good(P.dw(e))); g1=sum(1 for e in el if good(P.dw(e+0x1c))); g2=sum(1 for e in el if good(P.dw(e+0x18)))
print('  数组为 4B 指针数组: 元素数=%d  +0 合法 pTD=%d/94  +0x1c=%d/94(反控)  +0x18=%d/94(邻接证据)'%(len(el),g0,g1,g2))
print('\n== C 段：disp 扫描 ==')
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; lo=t['lo']; raw=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
pos=0;C=[];ins_n=0
while pos<len(raw):
    got=False
    for a,sz,mn,ops in mdl.disasm_lite(raw[pos:pos+64],lo+pos):
        got=True; ins_n+=1
        if mn in ('call','jmp'):
            s=ops.strip()
            if s.startswith('dword ptr ['):
                inner=s[s.index('[')+1:s.rindex(']')]
                if '*' not in inner and '[' not in inner:
                    parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                    if parts and len(parts)<=2 and parts[0] in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'):
                        d=0;okd=True
                        if len(parts)==2:
                            try: d=int(parts[1],0)
                            except: okd=False
                        if okd: C.append((a,parts[0],d))
        pos+=sz; break
    if not got: pos+=1
noesp=[c for c in C if c[1]!='esp']
hi=[c for c in noesp if c[2]>=0x400]
ss=collections.Counter(c[2]//4 for c in hi)
print('  指令数=%d  call/jmp[reg+disp] 全部=%d  排除 esp=%d'%(ins_n,len(C),len(noesp)))
print('  disp==0x2c=%d  disp==0=%d  disp==0x48=%d'%(sum(1 for c in noesp if c[2]==0x2c),
  sum(1 for c in noesp if c[2]==0),sum(1 for c in noesp if c[2]==0x48)))
print('  s>=256 位点=%d  不同 s=%d  非4对齐=%d'%(len(hi),len(ss),sum(1 for c in hi if c[2]%4)))
print('  s>344 的 s 值及次数: %s  合计 %d 处'%(
  [(s,ss[s]) for s in sorted(x for x in ss if x>344)],
  sum(ss[s] for s in ss if s>344)))
print('  0x41021a 命中=%s'%any(c[0]==0x41021a for c in noesp))
print('  含 esp 时 disp==0=%d、总候选=%d（card C 报 824 / 18935）'%(sum(1 for c in C if c[2]==0),len(C)))
print('\n== 反控 ==')
# 反控1：把 dw(V) 判据去掉 -> 1218
print('  反控1 去掉 dw(V)落.text 判据 -> %d（R217 口径）'%len(VA))
# 反控2：父类换成自身
print('  反控2 父类换自身 cov=%d（应 =464）'%sum(len(S[v])-256 for v in TGT))
# 反控3：disp 非4倍数
print('  反控3 disp 非4倍数计数=%d（应 0）'%sum(1 for c in hi if c[2]%4))
