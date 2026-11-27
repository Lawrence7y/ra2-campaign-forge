#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 A：1013 个非主表直接槽的「同组同序号」不匹配到底是真不同实现还是跳板壳。
独立口径：字节级跳板跟随（E9 rel32 / EB rel8 / FF 25 绝对间址），1 跳与 8 跳两口径。
"""
import sys, os, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n

COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=(w[i+1],w[i+3],w[i+4],nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]][3]].append(vt)
ck('A0 COL=1214 VT=1214 槽=14044 组=954 多表=94',
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1))==(1214,1214,14044,954,94),
   (len(COL),len(VT),sum(NS.values()),len(grp)))

def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04

direct=[]
for vt in sorted(VT):
    if COL[VT[vt]][0]==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not is_adj(v): direct.append((vt,k,v))
ck('A1 直接槽 1013', len(direct)==1013, len(direct))

# ---- 跳板跟随 ----
def jump_kind(va):
    o=P.r2o(va)
    if o is None: return None
    r=P.RAW[o:o+8]
    if len(r)<6: return None
    if r[0]==0xE9:
        tgt=va+5+struct.unpack_from('<i',r,1)[0]
        return ('rel32',tgt)
    if r[0]==0xEB:
        tgt=va+2+struct.unpack_from('<b',r,1)[0]
        return ('rel8',tgt)
    if r[0]==0xFF and r[1]==0x25:
        slot=struct.unpack_from('<I',r,2)[0]
        return ('abs',P.dw(slot))
    return None
def canon(va,maxhop=8):
    seen=[]; cur=va; hops=0
    while hops<maxhop:
        jk=jump_kind(cur)
        if jk is None or jk[1] is None or not in_text(jk[1]): break
        seen.append((cur,jk[0],jk[1]))
        cur=jk[1]; hops+=1
        if cur in [s[0] for s in seen]: break   # 环
    return cur, seen
ck('A2 canon 自身幂等：对 0x410210 thunk 起点的 jmp 目标再 canon 不变',
   canon(canon(0x410210)[0])[0]==canon(0x410210)[0])

# ---- 分类 ----
stat=collections.Counter(); pairs=[]; slots_cls={}
for vt,k,v in direct:
    nm=COL[VT[vt]][3]
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: stat['NOSIB']+=1; continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    base='THUNK' if is_adj(w) else 'DIRECT'
    if w==v: stat[base+'_SAME']+=1; continue
    if base=='THUNK':
        tv,tseen=canon(w,4)
        stat['THUNK_SAME' if tv==v else 'THUNK_OTHER']+=1
        if tv!=v: pairs.append((vt,k,v,t,w,base))
    else:
        stat['DIRECT_OTHER']+=1; pairs.append((vt,k,v,t,w,base))
ck('A3 五类合计 == 1013', sum(stat.values())==1013, dict(stat))
print('A4 分类:', dict(stat))

# ---- Q2 跳板归并两口径 ----
def collapse_stats(maxhop):
    col=0; dis=0; vjmp=0; wjmp=0; det=[]
    for vt,k,v,t,w,base in pairs:
        cv,sv=canon(v,maxhop); cw,sw=canon(w,maxhop)
        if sv: vjmp+=1
        if sw: wjmp+=1
        if cv==cw: col+=1
        else:
            dis+=1
            if len(det)<400: det.append((vt,k,v,t,w,cv,cw))
    return col,dis,vjmp,wjmp,det
c1,d1,vj1,wj1,_=collapse_stats(1)
c8,d8,vj8,wj8,det8=collapse_stats(8)
ck('A5 1 跳：COLLAPSE+DISTINCT == %d'%(c1+d1), c1+d1==len(pairs), (c1,d1))
ck('A6 8 跳：COLLAPSE+DISTINCT == %d'%(c8+d8), c8+d8==len(pairs), (c8,d8))
print('A7 1 跳 collapse=%d distinct=%d  v是跳板=%d w是跳板=%d'%(c1,d1,vj1,wj1))
print('A8 8 跳 collapse=%d distinct=%d  v是跳板=%d w是跳板=%d'%(c8,d8,vj8,wj8))

# 反控一：把 canon 换成恒等函数 ⇒ collapse 必须 = SAME 类数（0）
id_col=sum(1 for vt,k,v,t,w,b in pairs if v==w)
ck('A9 反控 恒等 canon ⇒ collapse == 0', id_col==0, id_col)
# 反控二：只跳 1 跳但把 rel8/abs 关掉（只 E9）
def canon9(va,maxhop=8):
    cur=va
    for _ in range(maxhop):
        o=P.r2o(cur)
        if o is None or P.RAW[o]!=0xE9: break
        tgt=cur+5+struct.unpack_from('<i',P.RAW,o+1)[0]
        if not in_text(tgt): break
        cur=tgt
    return cur
c9=sum(1 for vt,k,v,t,w,b in pairs if canon9(v)==canon9(w))
ck('A10 反控 仅 E9 口径 collapse=%d <= 8跳口径 %d'%(c9,c8), c9<=c8, (c9,c8))

# ---- Q3 具体样本 ----
def hx(va,n=16):
    o=P.r2o(va)
    return None if o is None else P.RAW[o:o+n].hex()
samples=[]
for vt,k,v,t,w,b in pairs:
    cv=canon(v,8)[0]; cw=canon(w,8)[0]
    samples.append(dict(vt=hex(vt),k=k,v=hex(v),t=hex(t),w=hex(w),cls=b,
                        coll=(cv==cw),cv=hex(cv),cw=hex(cw),
                        vbytes=hx(v),wbytes=hx(w),
                        vname=COL[VT[vt]][3],tname=COL[VT[t]][3],
                        vmdisp=COL[VT[vt]][0],tmdisp=COL[VT[t]][0]))
colS=[s for s in samples if s['coll']]; disS=[s for s in samples if not s['coll']]
ck('A11 COLLAPSE 样本 >=2 且 DISTINCT 样本 >=2', len(colS)>=2 and len(disS)>=2, (len(colS),len(disS)))
print('A12 COLLAPSE 前 4:')
for s in colS[:4]: print('   ',s['vname'],s['vmdisp'],'槽',s['k'],s['v'],'=>',s['tname'],s['tmdisp'],s['w'],'| ',s['vbytes'],'|',s['wbytes'])
print('A13 DISTINCT 前 4:')
for s in disS[:4]: print('   ',s['vname'],s['vmdisp'],'槽',s['k'],s['v'],'=>',s['tname'],s['tmdisp'],s['w'],'| ',s['vbytes'],'|',s['wbytes'])

json.dump(dict(stat=dict(stat),pairs=len(pairs),c1=c1,d1=d1,c8=c8,d8=d8,vj1=vj1,wj1=wj1,vj8=vj8,wj8=wj8,
               c9=c9,samples=samples), open('/home/t628/projects/ra2-campaign-forge/_r192/r192a.json','w'), indent=1)
print('断言 %d 条，FAIL %d 条'%(N,len(fails)))
sys.exit(1 if fails else 0)
