#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m0：核实 R200 的 11 条 main11 与 11 个 only_main 宿主是否同一批，并给出宿主真实边界口径。
一条命令输出全部基线；正反控同命令内完成。"""
import sys, struct, json, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']; RAW=P.RAW
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
NS={}
def nslot(vt):
    if vt in NS: return NS[vt]
    k=0
    while True:
        if not in_text(P.dw(vt+4*k)): break
        k+=1
    NS[vt]=k; return k
MD={vt:COL[VT[vt]]['mdisp'] for vt in VT}
CLS={vt:COL[VT[vt]]['name'] for vt in VT}

REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
recs=[]
pos=T['rawptr']; end=T['rawptr']+T['rawsize']
while pos<end-6:
    if RAW[pos]!=0xC7: pos+=1; continue
    modrm=RAW[pos+1]; mod=modrm>>6; reg=(modrm>>3)&7; rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1; continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        disp=struct.unpack_from('<b',RAW,pos+2)[0]; imm=struct.unpack_from('<I',RAW,pos+3)[0]
        recs.append((va,REGNAME[rm],disp,imm)); pos+=7
    elif mod==2:
        disp=struct.unpack_from('<i',RAW,pos+2)[0]; imm=struct.unpack_from('<I',RAW,pos+6)[0]
        recs.append((va,REGNAME[rm],disp,imm)); pos+=10
    else: pos+=1
sub=[r for r in recs if 1<=r[2]<=9 and r[3] in VT]
ck('B0a 697 条复现', len(sub)==697, len(sub))
main11=[r for r in sub if MD[r[3]]==0]
ck('B0b 11 条 main11 复现', len(main11)==11, len(main11))

BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
CALLAT=[]
p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
SORT=sorted(set(t for _,t in CALLAT))
ck('B0c call 目标集去重', len(SORT)>1000, len(SORT))
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def next_entry(c):
    i=bisect.bisect_right(SORT,c)
    return SORT[i] if i<len(SORT) else HI

# 重算 262 宿主的三分类
byhost=collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
both=only_sub=only_main=0; only_main_hosts=[]
for h,rs in byhost.items():
    if h is None: continue
    hi=min(next_entry(h),h+4096); o=P.r2o(h)
    if o is None: continue
    has_main=has_sub=False
    for i in md.disasm(RAW[o:o+(hi-h)],h):
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv=int(i.op_str.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv not in VT: continue
            if MD[iv]==0: has_main=True
            else: has_sub=True
    if has_main and has_sub: both+=1
    elif has_sub: only_sub+=1
    else: only_main+=1; only_main_hosts.append((h,rs))
ck('B0d 262 宿主复现', len(byhost)==262, len(byhost))
ck('B0e both/only_sub/only_main = 251/0/11', (both,only_sub,only_main)==(251,0,11), (both,only_sub,only_main))

m11h=sorted(set(host_of(r[0]) for r in main11))
omh=sorted(h for h,_ in only_main_hosts)
ck('B0f main11 的宿主去重数', len(m11h)>0, [hex(x) for x in m11h])
print('   main11 宿主:', [hex(x) for x in m11h])
print('   only_main 宿主:', [hex(x) for x in omh])
ck('B0g main11 宿主集合 == only_main 宿主集合', set(m11h)==set(omh), {'eq':set(m11h)==set(omh),'m11':len(m11h),'om':len(omh)})

# 879 条 disp8==mdisp 的对照基数
eq_md=[r for r in sub if r[2]==MD[r[3]]]
ne_md=[r for r in sub if r[2]!=MD[r[3]]]
ck('B0h disp8==mdisp 686 / 不等 11', (len(eq_md),len(ne_md))==(686,11), (len(eq_md),len(ne_md)))
ck('B0i 11 条不等 == main11', set(x[0] for x in ne_md)==set(x[0] for x in main11), len(ne_md))

# 宿主真实起点：候选 CALLAT 目标里，真正的函数入口应满足前一字节 ∈ {C3,CC,90,00} 或 有 push ebp 之类
def prec(h):
    o=P.r2o(h)
    return RAW[o-1] if o and o>0 else None
prec_c=collections.Counter(prec(h) for h in omh)
print('   only_main 宿主前一字节:', {hex(k) if k is not None else None:v for k,v in prec_c.items()})
def headbytes(h,n=12):
    o=P.r2o(h); return RAW[o:o+n].hex() if o else None
for h in omh:
    print('   host %s prevbyte=%s head=%s' % (hex(h), hex(prec(h)) if prec(h) is not None else None, headbytes(h)))

json.dump(dict(sub=len(sub),main11=[(hex(r[0]),r[1],r[2],hex(r[3]),CLS[r[3]]) for r in main11],
               m11_hosts=[hex(x) for x in m11h], om_hosts=[hex(x) for x in omh],
               both=both,only_sub=only_sub,only_main=only_main,hosts=len(byhost),
               eq_md=len(eq_md),ne_md=len(ne_md),asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m0_baseline.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
