#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m3：store 级（而非宿主级）验证「主表+子表双装」——用 ret/int3 边界定义真实函数体，
避开 R200 已证「宿主不可当函数」的缺陷。
正控：697 条 sub store 逐条给出其所属真实函数体内是否另有 main store。
反控：同一 store 在 CALLAT 窗口口径下的判据结果，两口径并置。"""
import sys, struct, json, bisect, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MD={vt:COL[VT[vt]]['mdisp'] for vt in VT}
CLS={vt:COL[VT[vt]]['name'] for vt in VT}
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
while pos<end-6:
    if RAW[pos]!=0xC7: pos+=1;continue
    modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=10
    else: pos+=1
sub=[r for r in recs if 1<=r[2]<=9 and r[3] in VT]
allvt=[r for r in recs if r[3] in VT]
ck('S0a 697 复现', len(sub)==697, len(sub))
mainall=[r for r in allvt if MD[r[3]]==0]
suball=[r for r in allvt if MD[r[3]]!=0]
print('   任意位移装表: main=%d sub=%d total=%d' % (len(mainall),len(suball),len(allvt)))

# 真实函数体边界：用 CAPSTONE 全段单次线性反汇编，记录 ret/int3 位置作为边界
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
BOUND=[];p2=0;INS=[]
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True
        INS.append((off,sz,mn,op))
        if mn.startswith('ret') or mn=='int3':
            BOUND.append(off+sz)
        p2+=sz
    if not got: p2+=1
INS.sort()
ck('S0b 指令流条数', len(INS)>400000, len(INS))
ADDRS=[a for a,_,_,_ in INS]
def idx_of(va):
    i=bisect.bisect_right(ADDRS,va)-1
    return i if i>=0 and ADDRS[i]<=va else None
def func_span(va):
    """返回 (lo,hi) 真实函数体：向前到上一边界，向后到下一边界。"""
    i=idx_of(va)
    if i is None: return None
    # 向后
    j=i
    while j<len(INS) and not (INS[j][2].startswith('ret') or INS[j][2]=='int3'):
        j+=1
    hi=INS[j][0]+INS[j][1] if j<len(INS) else HI
    # 向前：找最近的边界结束位置
    k=bisect.bisect_left(BOUND,va)-1
    lo=BOUND[k] if k>=0 else LO
    return lo,hi
def stores_in(lo,hi,arr):
    return [r for r in arr if lo<=r[0]<hi]

rows=[];cat=collections.Counter()
for r in sub:
    sp=func_span(r[0])
    if sp is None: cat['nospan']+=1; continue
    lo,hi=sp
    ma=stores_in(lo,hi,mainall); su=stores_in(lo,hi,suball)
    k='both' if (ma and su) else ('only_sub' if su else 'none')
    cat[k]+=1
    rows.append(dict(at=hex(r[0]),disp=r[2],imm=hex(r[3]),cls=CLS[r[3]],
                     lo=hex(lo),hi=hex(hi),span=hi-lo,n_main=len(ma),n_sub=len(su),k=k))
print('   697 条 sub store 的真实函数体内结构:',dict(cat))
ck('S0c 无 nospan', cat['nospan']==0, cat['nospan'])
ck('S0d 真实函数体内 both 占多数（>85%）', cat['both']>697*0.85, '%d/697 = %.2f%%'%(cat['both'],100.0*cat['both']/697))
# 与 R200 的 251/0/11 对照
print('   R200 CALLAT 宿主口径: 251 both / 0 only_sub / 11 only_main（宿主级，分母 262）')
print('   R201 ret 体 store 口径: %d both / %d only_sub / %d none（store 级，分母 697）'%(cat['both'],cat['only_sub'],cat['none']))
# only_sub 与 none 的 store 逐条
print('\n   非 both 的 store 明细:')
for x in rows:
    if x['k']!='both': print('     %s k=%s span=%d %s..%s n_main=%d n_sub=%d cls=%s'%(x['at'],x['k'],x['span'],x['lo'],x['hi'],x['n_main'],x['n_sub'],x['cls']))
# 11 条 mdisp==0 特例
m11=[r for r in sub if MD[r[3]]==0]
ck('S0e 11 条 mdisp==0 特例', len(m11)==11, len(m11))
print('\n   11 条 mdisp==0（主表装 +4/+8）在真实函数体内的位置:')
for r in m11:
    sp=func_span(r[0]); lo,hi=sp
    ma=stores_in(lo,hi,mainall); su=stores_in(lo,hi,suball)
    print('     at=%s disp=%d imm=%s cls=%s span=%s..%s n_main=%d n_sub=%d'%(hex(r[0]),r[2],hex(r[3]),CLS[r[3]],hex(lo),hex(hi),len(ma),len(su)))
json.dump(dict(cat=dict(cat),rows=rows,n_main=len(mainall),n_sub=len(suball),asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m3_storelevel.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
