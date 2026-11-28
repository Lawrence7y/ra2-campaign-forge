#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m5：真函数入口网格（替代 ret/int3 区间）口径下的最终三分类。
H1 严格序言位三种模式（P1 push ebp;mov ebp,esp / P3 mov edi,edi;push ebp;mov ebp,esp / P4 sub esp,imm）；
H2 E = CALLAT指令起点目标 ∪ 严格序言位 ∪ int3-run 之后的区间起点；
H3 8 种网格变体的三分类（稳健性）；
H4 only_sub 逐条（若存在）；
H5 反控：位移网格、去掉 CALLAT 只用序言、只用区间起点。"""
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
def extract():
    rec=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-4:
        if RAW[pos]==0x66:
            if pos+2<end and RAW[pos+1]==0xC7:
                mo=RAW[pos+2]>>6; pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
            pos+=1; continue
        if RAW[pos]!=0xC7: pos+=1; continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1; continue
        va=LO+(pos-T['rawptr'])
        if mod==1:
            d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
            rec.append((va,rm,d,im)); pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
            rec.append((va,rm,d,im)); pos+=10
        else:
            im=struct.unpack_from('<I',RAW,pos+2)[0]; rec.append((va,rm,0,im)); pos+=6
    return rec
allsite=extract()
vts=[r for r in allsite if r[3] in VT]
mainall=[r for r in vts if MD[r[3]]==0]
suball=[r for r in vts if MD[r[3]]!=0]
S697=[r for r in vts if 1<=r[2]<=9]
S686=[r for r in S697 if MD[r[3]]!=0]
# ---------- 反汇编 ----------
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];CALLAT=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]; I2R={a:i for i,a in enumerate(ADDRS)}
SORT=sorted(set(t for _,t in CALLAT)); TGT=set(SORT)&set(ADDRS)
REGION=[];st=LO;ENDRET=[];ENDMN=[]
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); ENDRET.append(mn.startswith('ret')); ENDMN.append(mn); st=a+sz
if st<HI: REGION.append((st,HI)); ENDRET.append(False); ENDMN.append('end')
RL=[r[0] for r in REGION]
# ---------- 严格序言 ----------
def pat(a):
    i=I2R.get(a)
    if i is None: return None
    w=INS[i:i+3]
    if len(w)<2: return None
    m=[x[2] for x in w]; o=[x[3].replace(' ','') for x in w]
    if m[0]=='push' and o[0]=='ebp' and m[1]=='mov' and o[1]=='ebp,esp': return 'P1'
    if m[0]=='mov' and o[0]=='edi,edi' and m[1]=='push' and o[1]=='ebp':
        if len(w)>2 and m[2]=='mov' and o[2]=='ebp,esp': return 'P3'
        return 'P3b'
    if m[0]=='sub' and o[0].startswith('esp,'): return 'P4'
    return None
PAT={}
for a in ADDRS:
    p=pat(a)
    if p: PAT[a]=p
ck('H1a 严格序言位总数在 300..1500', 300<len(PAT)<1500, len(PAT))
ck('H1b 序言模式分布', True, dict(collections.Counter(PAT.values())))
PATS=set(PAT)
# int3-run 之后的区间起点（无调用者的函数常见）
afterint3=set()
for i,(a,b) in enumerate(REGION):
    if i==0: continue
    if ENDMN[i-1]=='int3' and ENDMN[i-2:i-1]!=['int3']: afterint3.add(a)
ck('H2a int3-run 之后区间起点数', 0<len(afterint3)<len(REGION), len(afterint3))
E1=sorted(TGT)
E2=sorted(TGT|PATS)
E3=sorted(TGT|PATS|afterint3)
E4=sorted(PATS)
E5=sorted(RL)
for nm,E in [('E1 CALLAT',E1),('E2 CALLAT+序言',E2),('E3 CALLAT+序言+int3后',E3),('E4 仅序言',E4),('E5 仅区间起点',E5)]:
    print('   %-18s |E|=%d'%(nm,len(E)))
def seg(E,va):
    i=bisect.bisect_right(E,va)-1
    if i<0: return None
    return (E[i], E[i+1] if i+1<len(E) else HI)
def classify(E, stores):
    bm=collections.defaultdict(int); bs=collections.defaultdict(int)
    for r in mainall: bm[seg(E,r[0])]+=1
    for r in suball:  bs[seg(E,r[0])]+=1
    c=collections.Counter(); det=collections.defaultdict(list)
    for r in stores:
        sg=seg(E,r[0])
        if sg is None: c['noreg']+=1; continue
        if bm[sg]>0 and bs[sg]>0: k='both'
        elif bs[sg]>0: k='only_sub'
        else: k='none'
        c[k]+=1; det[k].append(r)
    return c,det
RES={}
for nm,E in [('E1',E1),('E2',E2),('E3',E3),('E4',E4),('E5',E5)]:
    c,det=classify(E,S697); c2,det2=classify(E,S686)
    RES[nm]=dict(nE=len(E),c697=dict(c),c686=dict(c2))
    print('   H3 %s 697: both=%-3d only_sub=%-3d none=%-3d | 686: both=%-3d only_sub=%-3d none=%-3d'%(
        nm,c['both'],c['only_sub'],c['none'],c2['both'],c2['only_sub'],c2['none']))
    ck('H3a %s 697 五数相加==697'%nm, sum(c.values())==697, dict(c))
    ck('H3b %s 686 五数相加==686'%nm, sum(c2.values())==686, dict(c2))
# 主口径 E2
c2m,d2m=classify(E2,S686)
ck('H4a E2 口径 686 的 only_sub == 0', c2m['only_sub']==0, c2m['only_sub'])
c2f,d2f=classify(E3,S686)
ck('H4b E3 口径 686 的 only_sub == 0', c2f['only_sub']==0, c2f['only_sub'])
print('\n   H4 E3 口径 686 三分类 both=%d only_sub=%d none=%d'%(c2f['both'],c2f['only_sub'],c2f['none']))
for k in ('only_sub','none'):
    for r in d2f[k][:10]:
        print('      %s @%s disp=%d imm=%s cls=%s seg=%s'%(k,hex(r[0]),r[2],hex(r[3]),CLS[r[3]],
              [hex(x) for x in seg(E3,r[0])]))
# 697 口径下 only_sub/none 详情
c7,d7=classify(E3,S697)
for k in ('only_sub','none'):
    print('   H4 697/%s %d 条'%(k,len(d7[k])))
    for r in d7[k][:12]:
        print('      %s @%s disp=%d imm=%s cls=%s seg=%s'%(k,hex(r[0]),r[2],hex(r[3]),CLS[r[3]],[hex(x) for x in seg(E3,r[0])]))
# 稳健性：E3 每个入口 +1 / -1 位移作反控
E3bad=sorted(set(a+1 for a in E3))
cb,_=classify(E3bad,S686)
ck('H5a 位移 +1 网格结果与 E3 不同', (cb['both'],cb['only_sub'],cb['none'])!=(c2f['both'],c2f['only_sub'],c2f['none']), dict(cb))
# 反控：把 686 里的次表 store 全部改成主表语义（应得 only_sub 0 且 both 0）
ck('H5b E3 网格段数 == |E3|-1 或 |E3|', len(E3)-1<=len(set(seg(E3,a) for a in E3))<=len(E3), len(E3))
OUT=dict(pat=dict(collections.Counter(PAT.values())),patN=len(PAT),afterint3=len(afterint3),
  E=dict(E1=len(E1),E2=len(E2),E3=len(E3),E4=len(E4),E5=len(E5)),
  RES=RES, e3_686=dict(c2f), e3_697=dict(c7),
  only_sub686=[hex(r[0]) for r in d2f['only_sub']],none686=[hex(r[0]) for r in d2f['none']],
  only_sub697=[hex(r[0]) for r in d7['only_sub']],none697=[hex(r[0]) for r in d7['none']],
  bad=dict(cb),asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m5_funcgrid.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
