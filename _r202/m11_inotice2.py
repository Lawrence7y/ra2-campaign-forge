#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m11：displacement 8 vs 4 的真因 —— 把三个区间整段线性反汇编并跟踪基址寄存器赋值。
N1 每区间整段反汇编（含地址/字节/助记符），标出对基址寄存器的写；
N2 判定 eax 在 0x410174 与 0x4101a5 之间是否被重装；
N3 INoticeSink 主表装填的 5 处全段位移 + 每处的基址来源；
N4 反控：若基址未重装则两次写同一字段属矛盾，统计全段「同区间同基址同 disp 不同 imm」的 store 数。"""
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
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[]
p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op)); p2+=sz
    if not got: p2+=1
INS.sort(); I2R={a:i for i,a in enumerate(INS)}
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
ADDRS=[x[0] for x in INS]
def first_ge(a):
    j=bisect.bisect_left(ADDRS,a)
    return j
def dump(a,b,mark=()):
    i=first_ge(a)
    if i>=len(INS): return []
    out=[]
    while i<len(INS) and INS[i][0]<b:
        ad,sz,mn,op=INS[i]
        tag=''
        if ad in mark: tag=' <<<< STORE'
        out.append((ad,sz,mn,op))
        i+=1
    return out
nstart_gap=sum(1 for a,b in REGION if a not in I2R)
ck('N0a 区间起点不是指令起点的区间数', nstart_gap>=0, nstart_gap)
print('   N0: %d/%d 个区间起点不是指令起点（线性反汇编失同步留下的间隙）'%(nstart_gap,len(REGION)))
for va in (0x410174,0x4101c2,0x6e8008):
    a,b=reg_of(va)
    stores=[r for r in vts if a<=r[0]<b]
    smap={r[0]:r for r in stores}
    print('\n===== 区间 %s..%s ====='%(hex(a),hex(b)))
    for ad,sz,mn,op in dump(a,b,set(smap)):
        extra=''
        if ad in smap:
            r=smap[ad]; extra=' [disp=%d imm=%s mdisp=%d %s]'%(r[2],hex(r[3]),MD[r[3]],CLS[r[3]])
        print('   %s %-20s %-8s %s%s'%(hex(ad),md.disasm(RAW[P.r2o(ad):P.r2o(ad)+sz],ad).__next__().bytes.hex(),mn,op,extra))
# N2 eax 是否被重装
def reloads(a,b,reg='eax'):
    i=first_ge(a); out=[]
    while i<len(INS) and INS[i][0]<b:
        ad,sz,mn,op=INS[i]
        if mn in ('mov','lea','xor','add','sub','pop','and','or') and op.startswith(reg+','):
            out.append((hex(ad),mn+' '+op))
        i+=1
    return out
for va in (0x410174,0x4101c2,0x6e8008):
    a,b=reg_of(va)
    rl=reloads(a,b,'eax')
    print('\n   N2 %s 区间内对 eax 的写：%s'%(hex(va),rl))
    ck('N2x %s eax 在区间内被重装'%hex(va), len(rl)>0, len(rl))
# N3 全段 INoticeSink 5 处
allIN=[r for r in vts if CLS[r[3]]=='.?AVINoticeSink@@']
print('\n   N3 全段 INoticeSink 主表装填 5 处：')
for r in allIN:
    a,b=reg_of(r[0])
    print('      %s 基=%s disp=%d 区间 %s..%s'%(hex(r[0]),['eax','ecx','edx','ebx','esp','ebp','esi','edi'][r[1]],r[2],hex(a),hex(b)))
ck('N3a 5 处中位移 8 的 3 处 == 本轮三条', sum(1 for r in allIN if r[2]==8)==3, sum(1 for r in allIN if r[2]==8))
# N4 同区间同基址同 disp 不同 imm
g=collections.defaultdict(set)
for r in vts: g[(reg_of(r[0]),r[1],r[2])].add(r[3])
conf=[k for k,v in g.items() if len(v)>1]
ck('N4a 「同区间同基址同位移不同 imm」组数 > 0', len(conf)>0, len(conf))
print('   N4: 同区间同基址同位移不同 imm 的组数 %d（说明同区间内基址在重装，位移不代表静态对象布局的唯一映射）'%len(conf))
for k in conf[:6]: print('      %s 基=%s disp=%d imm=%s'%(hex(k[0][0]),['eax','ecx','edx','ebx','esp','ebp','esi','edi'][k[1]],k[2],sorted(hex(x) for x in g[k])))
OUT=dict(IN5=[(hex(r[0]),r[2],CLS[r[3]]) for r in allIN],conflict=len(conf),
   conf_detail=[dict(seg=hex(k[0][0]),disp=k[2],imms=sorted(hex(x) for x in g[k])) for k in conf[:12]],
   asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m11_inotice2.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
