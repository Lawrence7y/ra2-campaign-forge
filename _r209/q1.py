# -*- coding: utf-8 -*-
"""R209 q1: .text 全域 this 调整 thunk 普查（83/81 6C 24 04 imm E9 rel32）+ 直接 call 引用图
+ 0x6d1770 (S 形态表) 的 cmp 立即数 0x11c7 语义线索 + 表结构范围。
正控：在 .text 内人为构造已知 thunk 字节串，检测器必须命中；反控：.rdata/.data 同样扫描必须 0。
"""
import sys, struct, collections, json, re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

TE = P.B['.text']
TB = P.RAW[TE['rawptr']:TE['rawptr']+TE['rawsize']]
BASE = TE['lo']
def o2v(off): return BASE+off

fails=[]; NA=0
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]

# ---------- 1. thunk 检测 ----------
def scan_thunks(buf, base):
    out=[]
    # A83
    i=0
    pat=b'\x83\x6c\x24\x04'
    while True:
        i=buf.find(pat,i)
        if i<0: break
        if i+9<=len(buf) and buf[i+5:i+6]==b'\xe9':
            imm=s32(buf[i+4])
            rel=s32(struct.unpack_from('<I',buf,i+6)[0])
            tgt=(base+i+10+rel)&0xffffffff
            out.append(dict(off=i,va=base+i,kind='A83',imm=imm,jmp=tgt,raw=buf[i:i+10].hex()))
        i+=1
    # B81
    i=0
    pat=b'\x81\x6c\x24\x04'
    while True:
        i=buf.find(pat,i)
        if i<0: break
        if i+13<=len(buf) and buf[i+9:i+10]==b'\xe9':
            imm=s32(struct.unpack_from('<I',buf,i+4)[0])
            rel=s32(struct.unpack_from('<I',buf,i+10)[0])
            tgt=(base+i+14+rel)&0xffffffff
            out.append(dict(off=i,va=base+i,kind='B81',imm=imm,jmp=tgt,raw=buf[i:i+14].hex()))
        i+=1
    out.sort(key=lambda x:x['off'])
    return out
TH=scan_thunks(TB, BASE)
A83=[t for t in TH if t['kind']=='A83']; B81=[t for t in TH if t['kind']=='B81']
ck('1.1 .text A83 thunk 计数', len(A83)>0, 'n=%d'%len(A83))
ck('1.2 .text B81 thunk 计数', len(B81)>=1, 'n=%d'%len(B81))
# 正控：合成 thunk
syn=b'\x83\x6c\x24\x04\x20\xe9'+struct.pack('<i',0x10)+b'\x90'*6
det=scan_thunks(syn, 0x500000)
ck('1.3 正控 合成 A83 命中 1', len(det)==1 and det[0]['imm']==0x20 and det[0]['jmp']==0x500000+10+0x10, det)
# 反控：非 .text 段
neg=0
for sn in ('.rdata','.data','.rsrc'):
    s=P.B.get(sn)
    if not s: continue
    neg+=len(scan_thunks(P.RAW[s['rawptr']:s['rawptr']+s['rawsize']], s['lo']))
ck('1.4 反控 非 .text 段 thunk 数 == 0', neg==0, 'n=%d'%neg)

# ---------- 2. 直接 call/jmp 引用图 ----------
calls=collections.defaultdict(list)   # target -> [caller va]
i=0
while True:
    i=TB.find(b'\xe8',i)
    if i<0: break
    if i+5<=len(TB):
        rel=s32(struct.unpack_from('<I',TB,i+1)[0])
        tgt=(BASE+i+5+rel)&0xffffffff
        calls[tgt].append(BASE+i)
    i+=1
jmpdir=collections.defaultdict(list)
i=0
while True:
    i=TB.find(b'\xe9',i)
    if i<0: break
    if i+5<=len(TB):
        rel=s32(struct.unpack_from('<I',TB,i+1)[0])
        tgt=(BASE+i+5+rel)&0xffffffff
        jmpdir[tgt].append(BASE+i)
    i+=1
print('# E8 total sites=%d, distinct targets=%d'%(sum(len(v) for v in calls.values()), len(calls)))

# ---------- 3. COL/vftable 模型（复用 R208 判据）----------
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(mdisp=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
vt_of={}
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*k)
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt_of[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
VT={c:tuple(P.dw(vt_of[c]+4*k) for k in range(vlen(vt_of[c]))) for c in vt_of}
slot0_owner=collections.defaultdict(list)   # slot0 -> [col]
for c,t in VT.items(): slot0_owner[t[0]].append(c)
ck('3.1 vftable/COL 模型复现', len(COL)==1214 and len(G)==954 and len(VT)==1214, 'COL=%d CHD=%d VT=%d'%(len(COL),len(G),len(VT)))

# ---------- 4. thunk 与 slot0/主视图关系 ----------
rows=[]
for t in TH:
    owners=slot0_owner.get(t['jmp'],[])
    primary=[c for c in owners if COL[c]['mdisp']==0]
    rows.append(dict(va=t['va'],kind=t['kind'],imm=t['imm'],jmp=t['jmp'],
                     n_owner=len(owners), n_primary=len(primary),
                     prim_names=[COL[c]['name'] for c in primary][:3],
                     used_as_slot0=[c for c in COL if c in slot0_owner.get(t['va'],[])][:1]))
n_in_vt=sum(1 for r in rows if slot0_owner.get(r['va']))
print('# total thunks=%d, 被用作某 COL 的 slot0 的 thunk=%d'%(len(rows), n_in_vt))
# thunk 目标是否为主视图 slot0
nt=sum(1 for r in rows if r['n_primary']>0)
print('# thunk 的 jmp 目标 == 某主视图 slot0 的条数 = %d / %d'%(nt,len(rows)))
# 间接：thunk 目标 是否被直接 call
for r in rows:
    r['direct_calls_to_jmp']=len(calls.get(r['jmp'],[]))
    r['direct_calls_to_thunk']=len(calls.get(r['va'],[]))

# ---------- 5. 0x4105e0 家族 ----------
T410=[r for r in rows if 0x410000<=r['va']<0x411000]
print('# 0x410xxx 段 thunk 数=%d'%len(T410))
vt_use=collections.Counter(r['va'] for r in rows if slot0_owner.get(r['va']))
print('# thunk 被用作 slot0 的复用计数 top: %s'%vt_use.most_common(8))

# ---------- 6. 0x6d1770 ----------
F=0x6d1770
fb=P.RAW[P.r2o(F):P.r2o(F)+400]
print('== 0x6d1770 前 400B ==')
print(fb[:200].hex(' '))
# 0x11c7 出现统计
occ={}
for sn in ('.text','.rdata','.data'):
    s=P.B[sn]; buf=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    m=b'\xc7\x11\x00\x00'
    lst=[]; i=0
    while True:
        i=buf.find(m,i)
        if i<0: break
        lst.append(s['lo']+i); i+=1
    occ[sn]=lst
print('# imm32 0x11c7 出现: ' + str({k:(len(v),[hex(x) for x in v[:6]]) for k,v in occ.items()}))
occ2={}
for sn in ('.text','.rdata','.data'):
    s=P.B[sn]; buf=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    m=struct.pack('<I',0x11c7)
    lst=[]; i=0
    while True:
        i=buf.find(m,i)
        if i<0: break
        lst.append(s['lo']+i); i+=1
    occ2[sn]=lst
print('# dword 0x11c7 (任意对齐) 出现: ' + str({k:(len(v),[hex(x) for x in v[:8]]) for k,v in occ2.items()}))
# 0x6d1770 在 vftable 中的使用
print('# 0x6d1770 是哪些 COL 的 slot0: %s'%([ (hex(c),COL[c]['name']) for c in slot0_owner.get(F,[])][:5]))
# 0x6d1770 被直接 call
print('# 0x6d1770 直接 call 次数=%d, 直接 jmp 次数=%d'%(len(calls.get(F,[])), len(jmpdir.get(F,[]))))
json.dump(dict(thunks=rows, occ_imm11c7={k:[hex(x) for x in v] for k,v in occ.items()},
               occ_dw11c7={k:[hex(x) for x in v] for k,v in occ2.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q1.json','w'), indent=1)
print('\n== FAILS: %s (断言 %d) =='%(fails,NA))
