#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m9（定稿）：字节扫描器 vs capstone 双口径对账，重点验 mod==0 主表装填是否被 0x66 前缀污染。
结论只采信两口径一致的部分。"""
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

# ---- 口径 D（字节扫描 + 66 前缀处理 + 正确边界）----
def extract_D():
    recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-4:
        if RAW[pos]==0x66:
            if pos+2<end and RAW[pos+1]==0xC7:
                m2=RAW[pos+2];mo=m2>>6
                pos += 6 if mo==0 else (7 if mo==1 else 11); continue
            pos+=1; continue
        if RAW[pos]!=0xC7: pos+=1;continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
        va=LO+(pos-T['rawptr'])
        if mod==1:
            d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
            recs.append((va,REGNAME[rm],d,im,'m1'));pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
            recs.append((va,REGNAME[rm],d,im,'m2'));pos+=10
        elif mod==0:
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            recs.append((va,REGNAME[rm],0,im,'m0'));pos+=6
        else: pos+=1
    return recs
D=extract_D()
Dvt=[r for r in D if r[3] in VT]
D_small=[r for r in Dvt if 1<=r[2]<=9]
D_main=[r for r in Dvt if MD[r[3]]==0]
ck('G0a 口径D 小位移装表 697', len(D_small)==697, len(D_small))
ck('G0b 口径D 小位移里 mdisp==0 的 11 条', len([r for r in D_small if MD[r[3]]==0])==11, len([r for r in D_small if MD[r[3]]==0]))
ck('G0c 口径D 小位移真次表 = 686', len([r for r in D_small if MD[r[3]]!=0])==686, len([r for r in D_small if MD[r[3]]!=0]))

# ---- 口径 E（capstone 线性反汇编，单次迭代 + 1 字节重同步）----
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
import re
SR=re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
E=[];INS=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True
        INS.append((off,sz,mn,op))
        if mn=='mov':
            m=SR.match(op)
            if m:
                rg=m.group(1);d=0
                if m.group(3):
                    d=int(m.group(3),16) if m.group(3).startswith('0x') else int(m.group(3))
                    if m.group(2)=='-': d=-d
                im=int(m.group(4),16)
                if im in VT: E.append((off,rg,d,im))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]
E_small=[r for r in E if 1<=r[2]<=9]
E_main=[r for r in E if MD[r[3]]==0]
print('   D: 全部 %d / 小位移 %d / 主表 %d'%(len(Dvt),len(D_small),len(D_main)))
print('   E: 全部 %d / 小位移 %d / 主表 %d'%(len(E),len(E_small),len(E_main)))
ck('G0d 两口径小位移数一致 697', len(E_small)==697, (len(D_small),len(E_small)))
ck('G0e 两口径主表装填数一致', len(E_main)==len(D_main), (len(D_main),len(E_main)))

# 关键：D 的 mod==0 主表装填，逐条与 E 对账
Dm0=set(r[0] for r in D_main if r[4]=='m0')
Em=set(r[0] for r in E_main)
inter=Dm0&Em
print('   D 的 mod==0 主表 %d 条；E 主表 %d 条；交集 %d'%(len(Dm0),len(Em),len(inter)))
only_D=sorted(Dm0-Em); only_E=sorted(Em-Dm0)
print('   只在 D（疑似 66 污染或失步）%d 条，样例 %s'%(len(only_D),[hex(x) for x in only_D[:6]]))
print('   只在 E（D 漏检）%d 条，样例 %s'%(len(only_E),[hex(x) for x in only_E[:6]]))
# 检查 only_D 是否是 66 前缀
def prefix66(va):
    o=P.r2o(va)
    return o is not None and o>0 and RAW[o-1]==0x66
p66c=sum(1 for a in only_D if prefix66(a))
ck('G0f only_D 里 66 前缀占比（应为 0，否则 D 仍污染）', p66c==0, '%d/%d'%(p66c,len(only_D)))
# only_D 的实际原因：看它们是否被 capstone 解成别的东西
print('\n   only_D 抽样反汇编上下文:')
for a in only_D[:5]:
    o=P.r2o(a)
    ctx=[]
    for i in md.disasm(RAW[o-8:o+12],a-8):
        ctx.append('%s %s %s'%(hex(i.address),i.mnemonic,i.op_str))
    print('     %s: %s'%(hex(a),' | '.join(ctx)))

# 8 个代表类：只用两口径交集
rep=['.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@','.?AVLightSourceClass@@',
     '.?AVWaveClass@@','.?AVWalkLocomotionClass@@','.?AVVoxelAnimTypeClass@@','.?AVCellClass@@']
OWN={}
for cn in rep:
    dsites=[r for r in D_main if CLS[r[3]]==cn]
    esites=[r for r in E_main if CLS[r[3]]==cn]
    common=sorted(set(r[0] for r in dsites)&set(r[0] for r in esites))
    OWN[cn]=dict(D=len(dsites),E=len(esites),common=len(common),
                 sites=[hex(x) for x in common[:8]])
    print('   %-34s D=%2d E=%2d 交集=%2d %s'%(cn,len(dsites),len(esites),len(common),OWN[cn]['sites'][:4]))
ck('G0g 8 个代表类在两口径交集下都有主表装填', all(OWN[c]['common']>0 for c in rep), {c:OWN[c]['common'] for c in rep})

# 主表装填的真实函数体（ret/int3）与函数数
BEND=sorted(a+sz for a,sz,mn,op in INS if mn.startswith('ret') or mn=='int3')
def span(va):
    i=bisect.bisect_right(ADDRS,va)-1
    if i<0: return None
    j=i
    while j<len(INS) and not (INS[j][2].startswith('ret') or INS[j][2]=='int3'): j+=1
    hi=INS[j][0]+INS[j][1] if j<len(INS) else HI
    k=bisect.bisect_left(BEND,va)-1
    return (BEND[k] if k>=0 else LO),hi
FUNC={}
for cn in rep:
    sites=[int(x,16) for x in OWN[cn]['sites']]
    fs=set()
    for s in sites:
        sp=span(s)
        if sp: fs.add(sp[0])
    FUNC[cn]=len(fs)
print('\n   交集主表装填的去重函数数:',dict(FUNC))
ck('G0h 每个代表类的主表装填分布在 >=2 个函数里', all(v>=2 for v in FUNC.values()), dict(FUNC))

json.dump(dict(D_all=len(Dvt),D_small=len(D_small),D_main=len(D_main),
               E_all=len(E),E_small=len(E_small),E_main=len(E_main),
               inter=len(inter),only_D=len(only_D),only_E=len(only_E),p66c=p66c,
               only_D_sample=[hex(x) for x in only_D[:12]],only_E_sample=[hex(x) for x in only_E[:12]],
               OWN=OWN,FUNC=FUNC,asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m9_final.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
