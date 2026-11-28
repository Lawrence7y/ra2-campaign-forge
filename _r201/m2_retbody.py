#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m2：用 ret 终止的真实函数体重算 262 宿主的装填结构，订正 R200 的 CALLAT 截断口径。
正控：对 R200 的 11 个 only_main 与 251 个 both 逐宿主给「真实体内 main/sub 有无」。
反控：同一宿主用 CALLAT 窗口 vs ret 体，两口径的 only_main 数对比。"""
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
byhost=collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
ck('N0a 262 宿主', len(byhost)==262, len(byhost))

def body_ret(h,cap=65536):
    """从 h 线性反汇编到第一条 ret/retn/jmp 终止或 cap 字节。返回 [(ad,sz,mn,op)]。"""
    o=P.r2o(h)
    if o is None: return []
    out=[]
    for i in md.disasm(RAW[o:o+cap],h):
        out.append((i.address,i.size,i.mnemonic,i.op_str))
        if i.mnemonic.startswith('ret') or i.mnemonic=='jmp': break
        if len(out)>16000: break
    return out

def classify(ins):
    has_main=has_sub=False; det=[]
    for ad,sz,mn,op in ins:
        if mn=='mov' and op.startswith('dword ptr [') and ', 0x' in op:
            try: iv=int(op.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv not in VT: continue
            k='main' if MD[iv]==0 else 'sub'
            det.append((hex(ad),hex(iv),k,CLS[iv]))
            if k=='main': has_main=True
            else: has_sub=True
    return has_main,has_sub,det

rows=[];cats=collections.Counter();cats_callat=collections.Counter()
for h,rs in sorted(byhost.items()):
    ins=body_ret(h)
    hm,hs,det=classify(ins)
    cat='both' if (hm and hs) else ('only_sub' if hs else ('only_main' if hm else 'none'))
    cats[cat]+=1
    # CALLAT 口径对照
    nxt=HI
    i=bisect.bisect_right(SORT,h)
    if i<len(SORT): nxt=SORT[i]
    hi=min(nxt,h+4096);o=P.r2o(h)
    ins2=[(j.address,j.size,j.mnemonic,j.op_str) for j in md.disasm(RAW[o:o+(hi-h)],h)]
    hm2,hs2,_=classify(ins2)
    cat2='both' if (hm2 and hs2) else ('only_sub' if hs2 else ('only_main' if hm2 else 'none'))
    cats_callat[cat2]+=1
    rows.append(dict(h=hex(h),cat=cat,cat_callat=cat2,bodylen=len(ins),
                     end=hex(ins[-1][0]) if ins else None,
                     last=ins[-1][2] if ins else None,n_det=len(det),det=det))
print('   ret 体口径三分类:',dict(cats))
print('   CALLAT 口径三分类（复现 R200）:',dict(cats_callat))
ck('N0b CALLAT 口径复现 251/0/11', (cats_callat['both'],cats_callat['only_sub'],cats_callat['only_main'])==(251,0,11), dict(cats_callat))
ck('N0c ret 体口径 only_sub==0', cats['only_sub']==0, dict(cats))
print('\n   ret 体口径下 only_main 逐宿主:')
om=[r for r in rows if r['cat']=='only_main']
for r in om: print('     %s bodylen=%d end=%s last=%s det=%s' % (r['h'],r['bodylen'],r['end'],r['last'],r['det']))
print('\n   ret 体口径下 none 逐宿主:')
for r in rows:
    if r['cat']=='none': print('     %s bodylen=%d end=%s last=%s' % (r['h'],r['bodylen'],r['end'],r['last']))
# 关键对照：CALLAT 口径判 only_main 的 11 个，在 ret 体口径下是什么
c11=[r for r in rows if r['cat_callat']=='only_main']
for r in c11: print('     [c11] %s callat=only_main -> ret=%s bodylen=%d' % (r['h'],r['cat'],r['bodylen']))
ck('N0d CALLAT 判 only_main 的 11 个在 ret 体口径下不全为 only_main',
   any(r['cat']!='only_main' for r in c11), [(r['h'],r['cat']) for r in c11])
json.dump(dict(rows=rows,cats=dict(cats),cats_callat=dict(cats_callat),asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m2_retbody.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
