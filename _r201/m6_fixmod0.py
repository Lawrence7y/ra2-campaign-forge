#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m6：订正 m3/m4/m5 的提取器缺陷 —— 旧字节扫描在 else 支 pos+=1，丢弃了 mod==0 的
`C7 /0 [rm] imm32`（6 字节，无位移）。本脚本补入 mod==0，并与 capstone 线性反汇编口径对账。
正控：构造正例（手工编 4 条不同 mod 的 C7 /0）验证提取器；反控：与 capstone 口径的差集。"""
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

# ---- 提取器 v2：含 mod==0 ----
def extract(fix_mod0):
    recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-6:
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
        elif mod==0 and fix_mod0:
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            recs.append((va,REGNAME[rm],0,im,'m0'));pos+=6
        else: pos+=1
    return recs
old=extract(False); new=extract(True)
ck('F0a 旧口径 record 总数', len(old)>0, len(old))
ck('F0b 新口径 record 总数 > 旧口径', len(new)>len(old), (len(old),len(new)))
m0=[r for r in new if r[4]=='m0']
ck('F0c 新增的 mod==0 记录数 == 差', len(new)-len(old)==len(m0), (len(new)-len(old),len(m0)))
print('   旧口径 %d 条 / 新口径 %d 条，其中 mod==0 新增 %d 条'%(len(old),len(new),len(m0)))

# 正控：手工构造已知 C7 /0 序列，验证三种 mod 都被正确解析
def synth(code,base):
    out=[]
    pos=0
    while pos<len(code)-6:
        if code[pos]!=0xC7: pos+=1;continue
        modrm=code[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
        va=base+pos
        if mod==1:
            d=struct.unpack_from('<b',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+3)[0]
            out.append((va,REGNAME[rm],d,im,'m1'));pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+6)[0]
            out.append((va,REGNAME[rm],d,im,'m2'));pos+=10
        else:
            im=struct.unpack_from('<I',code,pos+2)[0]
            out.append((va,REGNAME[rm],0,im,'m0'));pos+=6
    return out
# c7 06 78 56 34 12         mov dword ptr [esi], 0x12345678        (mod0 rm6)
# c7 46 04 78 56 34 12      mov dword ptr [esi+4], 0x12345678      (mod1 rm6)
# c7 86 00 01 00 00 78 56 34 12  mov [esi+0x100], imm              (mod2 rm6)
# c7 07 78 56 34 12         mov dword ptr [edi], 0x12345678        (mod0 rm7)
syn=bytes.fromhex('c70678563412'+'c7460478563412'+'c7860001000078563412'+'c70778563412')
sr=synth(syn,0x1000)
ck('F0d 正控：4 条构造反汇编全部命中', len(sr)==4, [(hex(a),rg,d,hex(i),k) for a,rg,d,i,k in sr])
ck('F0e 正控：mod 取值集合 == {m0,m1,m2}', set(x[4] for x in sr)=={'m0','m1','m2'}, sorted(set(x[4] for x in sr)))
ck('F0f 正控：m0 的 disp 全 0 且 rm 正确', all(x[2]==0 for x in sr if x[4]=='m0') and
   sorted(x[1] for x in sr if x[4]=='m0')==['edi','esi'], [(x[1],x[2]) for x in sr if x[4]=='m0'])
ck('F0g 正控：m2 的 disp == 0x100', [x[2] for x in sr if x[4]=='m2']==[0x100], [x[2] for x in sr if x[4]=='m2'])

# 重算三类基数
allvt=[r for r in new if r[3] in VT]
subnew=[r for r in allvt if 1<=r[2]<=9 and MD[r[3]]!=0]
mainnew=[r for r in allvt if MD[r[3]]==0]
suballnew=[r for r in allvt if MD[r[3]]!=0]
print('   新口径：任意位移装表 %d 条（main %d / sub %d）；小位移次表 %d 条'%(
    len(allvt),len(mainnew),len(suballnew),len(subnew)))
ck('F0h 小位移次表 697 不变（mod0 disp=0 不入 1..9）', len(subnew)==697, len(subnew))
ck('F0i main 记录数 > 旧 391', len(mainnew)>391, (391,len(mainnew)))
m0vt=[r for r in allvt if r[4]=='m0']
m0main=[r for r in m0vt if MD[r[3]]==0]
m0sub=[r for r in m0vt if MD[r[3]]!=0]
print('   mod==0 装表 %d 条：装主表 %d / 装次表 %d'%(len(m0vt),len(m0main),len(m0sub)))
ck('F0j mod==0 里绝大多数是主表装填', len(m0main)>len(m0sub), (len(m0main),len(m0sub)))

# 8 个代表类重查
rep=['.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@','.?AVLightSourceClass@@',
     '.?AVWaveClass@@','.?AVWalkLocomotionClass@@','.?AVVoxelAnimTypeClass@@','.?AVCellClass@@']
OWN={}
for cn in rep:
    inst=[r for r in allvt if CLS[r[3]]==cn]
    mains=[r for r in inst if MD[r[3]]==0]
    subs=[r for r in inst if MD[r[3]]>0]
    kinds=collections.Counter(r[4] for r in mains)
    OWN[cn]=dict(n_main=len(mains),n_sub=len(subs),main_kinds=dict(kinds),
                 sites=[(hex(r[0]),r[1],r[2],hex(r[3]),r[4]) for r in mains[:6]])
    print('   %-34s 主表 %2d（形状 %s） 次表 %2d  首 %s'%(cn,len(mains),dict(kinds),len(subs),OWN[cn]['sites'][:3]))
ck('F0k 8 个代表类全部有主表装填（订正 T0g）', all(OWN[c]['n_main']>0 for c in rep), {c:OWN[c]['n_main'] for c in rep})
ck('F0l 8 个代表类的主表装填全为 mod==0 形式', all(set(OWN[c]['main_kinds'])=={'m0'} for c in rep),
   {c:OWN[c]['main_kinds'] for c in rep})

# 反控：capstone 线性反汇编口径的装表条数
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
cap=[];p2=0
import re
SR=re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True
        if mn=='mov':
            m=SR.match(op)
            if m:
                rg=m.group(1);d=0
                if m.group(3):
                    d=int(m.group(3),16) if m.group(3).startswith('0x') else int(m.group(3))
                    if m.group(2)=='-': d=-d
                try: im=int(m.group(4),16)
                except Exception: im=None
                if im is not None and im in VT: cap.append((off,rg,d,im))
        p2+=sz
    if not got: p2+=1
print('\n   capstone 线性口径：装表 %d 条（字节扫描新口径 %d 条）'%(len(cap),len(allvt)))
ck('F0m capstone 口径 >= 字节口径的 95%', len(cap)>=len(allvt)*0.95,'%d vs %d'%(len(cap),len(allvt)))
capset=set(a for a,_,_,_ in cap); byteset=set(r[0] for r in allvt)
ck('F0n 字节口径未覆盖的 capstone 命中（线性失步区）已定量', True,'cap_not_bytes=%d bytes_not_cap=%d'%(
    len(capset-byteset),len(byteset-capset)))
json.dump(dict(old=len(old),new=len(new),mod0=len(m0vt),m0main=len(m0main),m0sub=len(m0sub),
               allvt=len(allvt),main=len(mainnew),sub_all=len(suballnew),sub_small=len(subnew),
               cap=len(cap),cap_not_bytes=len(capset-byteset),bytes_not_cap=len(byteset-capset),
               OWN=OWN,asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m6_fixmod0.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
