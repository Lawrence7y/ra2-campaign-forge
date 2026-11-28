# -*- coding: utf-8 -*-
"""R218-B 复算：B1d 错判据、B2d 逐 dword 源比对、B2e CHD 原始布局、B4 正确候选判据。"""
import sys,struct,collections
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL)
VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS and P.where(base+4*k+4) in ('.rdata','.data'):
            VT[base+4*k+4]=v
VTS=sorted(VT)

print('=== B1d 错误判据复算 ===')
bad=[]
for lo,hi in ((P.B['.rdata']['lo'],P.B['.rdata']['hi_file']),(P.B['.data']['lo'],P.B['.data']['hi_file'])):
    for a in range(lo+4,hi,4):
        p=P.dw(a-4)
        if P.where(p)=='.data' and P.dw(a+8)==0: bad.append(a)
print('错误判据「dw(V-4)落.data 且 dw(V+8)==0」命中=%d (正确判据虚表数=%d)'%(len(bad),len(VTS)))
print('错误判据前10=%s'%[hex(x) for x in bad[:10]])

print('\n=== B2d 精确复制源搜索 (整文件字节匹配 + 逐dword错位比对) ===')
for v in (0x877000,0x877010,0x87b17c,0x87b18c):
    pat=b''.join(struct.pack('<I',P.dw(v+4*k)) for k in range(16))
    hits=[]; off=0
    while True:
        i=P.RAW.find(pat,off)
        if i<0: break
        # 文件偏移 -> VA
        va=None
        for s in P.SECS:
            if s['rawptr']<=i<s['rawptr']+s['rawsize']:
                va=s['lo']+i-s['rawptr']; break
        hits.append(hex(va) if va else hex(i)); off=i+1
    print('%08x 前16 dword(64B)整文件字节命中=%s'%(v,hits))
    # 与 0x7e8278 按 0..49 起点错位逐 dword 比对
    best=[]
    for u in (0x7e8278,):
        for st in range(0,50):
            m=sum(1 for k in range(16) if P.dw(v+4*k)==P.dw(u+4*(st+k)))
            best.append((m,st))
    best.sort(reverse=True)
    print('   与 0x7e8278 错位比对 best(matches/16,slot偏移)=%s'%best[:4])

print('\n=== B2e CHD 原始 dword 转储 ===')
for a in range(0x800030,0x800110,4):
    x=P.dw(a)
    nm=P.cstr(x+8,200) if P.where(x)=='.rdata' and x+8 else b''
    tag=''
    if x in CS: tag='COL:'+CS[x]['name']
    elif nm and nm[:3]==b'.?A': tag='TD:'+nm.decode('latin1','replace')
    print('%08x = %08x %-10s %s'%(a,x,P.where(x),tag))
print('pCHD=0x800098: +0=%08x +4=%08x +8=%08x(numBase) +c=%08x(pBaseArray)'%(
      P.dw(0x800098),P.dw(0x80009c),P.dw(0x8000a0),P.dw(0x8000a4)))
print('BCD 逐项: +0 pTD, +4 pCHD?, +8/+c/+10 PMD三元组, +14/+18?, +1c pCHD?')
arr=P.dw(0x8000a4)
for i in range(5):
    b=arr+0x1c*i
    vals=[P.dw(b+4*j) for j in range(7)]
    ptd=vals[0]
    nm=P.cstr(ptd+8,200) if P.where(ptd)=='.rdata' else b'?'
    print('BCD%d @%08x: %s  pTDname=%s'%(i,b,[hex(x) for x in vals],nm and nm.decode('latin1','replace')))

print('\n=== B4 正确候选判据复算: .data 中 8字节对齐且 dw(V-4)=COL ===')
cand=[]
s=P.B['.data']
for a in range(s['lo'],s['hi_file'],8):
    if P.dw(a-4) in CS: cand.append(a)
print('候选=%d ; 真虚表(在VT中)=%d ; 未认定=%d'%(len(cand),sum(1 for a in cand if a in VT),sum(1 for a in cand if a not in VT)))
print('候选清单=%s'%[hex(a) for a in cand])
for a in cand:
    c1=P.dw(a-4); c0=P.dw(a-8)
    print('   %08x dw(V-4)=%08x%s dw(V-8)=%08x%s V=%d dw(V)=%08x 落段=%s'%(
        a,c1,'COL' if c1 in CS else '-',c0,'COL' if c0 in CS else '-',a in VT,P.dw(a),P.where(P.dw(a))))
print('\n=== .data 所有 COL 指针位置(a-4) 不管对齐 ===')
allpos=[]
for a in range(s['lo'],s['hi_file'],4):
    if P.dw(a-4) in CS: allpos.append(a)
print('总数=%d 清单=%s'%(len(allpos),[hex(a) for a in allpos]))
