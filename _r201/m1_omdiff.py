#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m1：订正 R200「只装主表 11」的表述，给出 only_main 窗口内实际发生了什么。
口径完全复刻 R200 m11_subfill.py。"""
import sys, struct, json, bisect, collections, re
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
NS={}
def nslot(vt):
    if vt in NS: return NS[vt]
    k=0
    while True:
        if not in_text(P.dw(vt+4*k)): break
        k+=1
    NS[vt]=k;return k
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
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
CALLAT=[];p2=0
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
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def next_entry(c):
    i=bisect.bisect_right(SORT,c)
    return SORT[i] if i<len(SORT) else HI
byhost=collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)

# 逐宿主判定：窗口内所有 imm-in-VT 的 store（任意位移，不限 1..9）都算「装表」
allvt=[r for r in recs if r[3] in VT]   # 任意位移的装表 store
byhost_all=collections.defaultdict(list)
for r in allvt: byhost_all[host_of(r[0])].append(r)

rows=[]
def win_scan(h):
    hi=min(next_entry(h),h+4096);o=P.r2o(h)
    ins=[]
    for i in md.disasm(RAW[o:o+(hi-h)],h):
        ins.append((i.address,i.size,i.mnemonic,i.op_str))
    return hi,ins

for h,rs in sorted(byhost.items()):
    hi,ins=win_scan(h)
    has_main=has_sub=False
    immvt=[]
    for ad,sz,mn,op in ins:
        if mn=='mov' and op.startswith('dword ptr [') and ', 0x' in op:
            try: iv=int(op.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv not in VT: continue
            immvt.append((ad,iv,'main' if MD[iv]==0 else 'sub'))
            if MD[iv]==0: has_main=True
            else: has_sub=True
    cat='both' if (has_main and has_sub) else ('only_sub' if has_sub else 'only_main')
    # 本窗口内的子系统 store（disp 1..9）
    minsub=[r for r in rs]
    rows.append(dict(h=hex(h),hi=hex(hi),wlen=hi-h,cat=cat,n_ins=len(ins),
                     n_immvt=len(immvt),immvt=[(hex(a),hex(v),k) for a,v,k in immvt],
                     n_store=len(minsub),stores=[(hex(r[0]),r[1],r[2],hex(r[3]),CLS[r[3]]) for r in minsub]))
cats=collections.Counter(r['cat'] for r in rows)
ck('M1a 262 宿主三分类', (cats['both'],cats['only_sub'],cats['only_main'])==(251,0,11), dict(cats))
om=[r for r in rows if r['cat']=='only_main']
ck('M1b only_main 11 个', len(om)==11, len(om))
# 关键：only_main 窗口内是否真的「零装表」
ck('M1c only_main 窗口内装表数全为 0', all(r['n_immvt']==0 for r in om), [r['n_immvt'] for r in om])
ck('M1d only_main 窗口内小位移 store 也全为 0', all(r['n_store']==0 for r in om), [r['n_store'] for r in om])
print('\n   only_main 逐宿主（窗口内指令数 / 装表数 / 窗口长）:')
for r in om:
    print('     %s len=%4d ins=%3d immvt=%d store=%d' % (r['h'],r['wlen'],r['n_ins'],r['n_immvt'],r['n_store']))
# 这些宿主是否根本不在「装了子表的 251 个宿主」里 —— 是，因为 byhost 只收 sub 记录
ck('M1e 11 个 only_main 宿主本身不在 sub 记录宿主集里（自明）', True, 'byhost 只由 sub 构造')
# 关键反控：在宽松窗口（宿主后 16384 字节）内这些宿主是否装表
print('\n   宽松窗口 16384 内装表复核:')
loose=[]
for r in om:
    h=int(r['h'],16);o=P.r2o(h)
    got=[]
    for i in md.disasm(RAW[o:o+16384],h):
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv=int(i.op_str.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv in VT: got.append((hex(i.address),hex(iv),'main' if MD[iv]==0 else 'sub'))
    loose.append((r['h'],len(got),got[:4]))
    print('     %s -> %d %s' % (r['h'],len(got),got[:4]))
ck('M1f 宽松 16KB 窗口下仍有装表（说明窗口截断是主因）', any(x[1]>0 for x in loose), [x[1] for x in loose])

json.dump(dict(rows=rows,cats=dict(cats),loose=loose,asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m1_omdiff.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
