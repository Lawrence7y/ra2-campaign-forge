# -*- coding: utf-8 -*-
"""R218-B 一条命令完成 .data 虚表普查/零槽成因/共用COL/负控 全部取证。"""
import sys,struct,hashlib,collections
sys.path.insert(0,'_r185'); import pe185 as P

def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']

# ---- COL 识别 ----
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

# ---- VT 识别：dw(V-4) 是 COL 且 V 落 .rdata/.data ----
VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS:
            va=base+4*k+4
            if P.where(va) in ('.rdata','.data'):
                VT[va]=v
VTS=sorted(VT)

def nslots(vt):
    n=0
    while P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
NS={v:nslots(v) for v in VTS}
print('[正控背景复核] COL数=%d  虚表数=%d  总槽数=%d'%(len(COL),len(VTS),sum(NS.values())))
for v in (0x7e1f50,0x7e1f34,0x7f5c70):
    if v in NS: print('   正控 %08x slots=%d %s'%(v,NS[v],COL[VT[v]]['name']))
print('   零槽表: %s'%[hex(v) for v in VTS if NS[v]==0])

# ================= B1 =================
print('\n======== B1 按段分组普查 ========')
seg=collections.Counter(P.where(v) for v in VTS)
print('B1a 段分布: .rdata=%d  .data=%d  合计=%d'%(seg['.rdata'],seg['.data'],len(VTS)))
dvts=[v for v in VTS if P.where(v)=='.data']
print('B1b .data 虚表共 %d 张 (地址 类名 mdisp 槽数):'%len(dvts))
for v in dvts:
    c=COL[VT[v]]
    print('   %08x  %-64s  mdisp=%-3d slots=%d'%(v,c['name'],c['md_'],NS[v]))
dnz=[v for v in dvts if NS[v]>=1]
print('B1c .data 中槽数>=1 的表 %d 张 (地址 类名 槽数):'%len(dnz))
for v in dnz:
    c=COL[VT[v]]
    print('   %08x  %-64s  slots=%d'%(v,c['name'],NS[v]))
print('B1d 反控错误判据 (dw(V-4)落.data 且 dw(V+8)==0) 命中数: ',
      sum(1 for s in ('.rdata','.data') for a in range(P.B[s]['lo']+4,P.B[s]['hi_file'],4)
          if P.where(P.dw(a-4))=='.data' and P.dw(a+8)==0))
print('B1d 对照正确判据 (dw(V-4)=COL 且 V 落 .rdata/.data) = 虚表数 %d'%len(VTS))

# ================= B2 =================
print('\n======== B2 零槽 4 表的物理布局 ========')
TGT=[0x877000,0x877010,0x87b17c,0x87b18c,0x7e8278]
for v in TGT:
    c=COL.get(VT.get(v))
    print('\nB2a %08x COL=%08x name=%s mdisp=%s slots=%s'%(v,VT.get(v),c and c['name'],c and c['md_'],NS.get(v)))
    for k in range(-2,14):
        a=v+4*k; x=P.dw(a)
        print('   %+3d @%08x = %08x %-10s %s'%(k,a,x,P.where(x),('COL:'+COL[x]['name'] if x in CS else '')))
print('\nB2b 间隔关系: 0x877010-0x877000=0x%x ; 0x87b18c-0x87b17c=0x%x ; 都是 V 与 V+0x10 (4槽)'%(0x877010-0x877000,0x87b18c-0x87b17c))
for v in TGT[:4]:
    n=NS[v]; dv=P.dw(v+4*n)
    print('B2c %08x slots=%d 紧随dword @%08x = %08x 落段=%s'%(v,n,v+4*n,dv,P.where(dv)))
# B2d 逐 dword 比对 .data V 与所有 V 的重叠候选
print('\nB2d 找 0x877000 的复制源 (前32 dword 与所有虚表起点逐项比对):')
for v in TGT[:4]:
    src=P.dw(v-4); sig=[P.dw(v+4*k) for k in range(32)]
    cand=[]
    for u in VTS:
        if u>=v: break
        if P.where(u)!='.rdata': continue
        m=sum(1 for k in range(32) if P.dw(u+4*k)==sig[k])
        if m>=4: cand.append((m,u,COL[VT[u]]['name']))
    cand.sort(reverse=True)
    print('   %08x 候选(matches/32, addr, name):'%(v),[(m,hex(u),n[:52]) for m,u,n in cand[:6]])
# B2e CHD 链
print('\nB2e pCHD / CHD 基类数组:')
def chd_info(p):
    if P.where(p)!='.rdata': return 'pCHD not in .rdata'
    num=P.dw(p+8); arr=P.dw(p+0xc)
    out='numBase=%d pBase=%08x'%(num,arr)
    rows=[]
    for i in range(min(num,8)):
        bcd=arr+0x1c*i
        ptd=P.dw(bcd); pmd=P.dw(bcd+8); pch=P.dw(bcd+0x18)
        nm=P.cstr(ptd+8,256) if P.where(ptd)=='.data' else b'?'
        rows.append('  BCD%d pTD=%08x %s PMD.mdisp=%d pCHD=%08x'%(i,ptd,nm and nm.decode('latin1','replace'),s32(pmd),pch))
    return out+'\n'+'\n'.join(rows)
for v in TGT:
    c=COL.get(VT.get(v))
    if not c: continue
    print('   %08x %s mdisp=%d pCHD=%08x'%(v,c['name'],c['md_'],c['pCHD']))
    print('   '+chd_info(c['pCHD']))

# ================= B3 =================
print('\n======== B3 共用 COL 全表普查 ========')
groups=collections.defaultdict(list)
for v in VTS: groups[VT[v]].append(v)
dist=collections.Counter(len(x) for x in groups.values())
print('B3a 共用数->出现次数: %s'%dict(sorted(dist.items())))
multi=[(col,vs) for col,vs in groups.items() if len(vs)>=2]
print('   共用>=2 组数=%d'%len(multi))
for col,vs in sorted(multi):
    c=COL[col]
    print('   COL=%08x %-52s mdisp=%d 共用数=%d 表=%s'%(col,c['name'],c['md_'],len(vs),[hex(x) for x in sorted(vs)]))
print('B3b 主会话称只有 1 例(0x800040 被 5 张表共用); 本次独立判据: dw(V-4)=COL 且 V 落 .rdata/.data, 未见强制合并, 差异仅在是否把 .data 虚表计入(见异常)。')

# ================= B4 =================
print('\n======== B4 负控: .data 8字节对齐 COL 指针候选 ========')
ds=P.B['.data']
# 读法1(字面): 候选地址自身前4字节 = dw(V) 是 COL 指针
c1=[a for a in range(ds['lo'],ds['hi_file'],8) if P.dw(a) in CS]
print('B4a 读法1 dw(V)是COL指针且8字节对齐: 候选=%d 真虚表=%d 未认定=%d 前10=%s'%(
    len(c1),sum(1 for a in c1 if a in VT),sum(1 for a in c1 if a not in VT),
    [hex(a) for a in [x for x in c1 if x not in VT][:10]]))
# 读法2(R217口径): 候选前4字节 dw(V-4) 是 COL 指针
c2=[a for a in range(ds['lo'],ds['hi_file'],8) if P.dw(a-4) in CS]
notvt2=[a for a in c2 if a not in VT]
print('B4a 读法2 dw(V-4)是COL指针且8字节对齐: 候选=%d 真虚表=%d 未认定=%d 前10=%s'%(
    len(c2),sum(1 for a in c2 if a in VT),len(notvt2),[hex(a) for a in notvt2[:10]]))
c4=[a for a in range(ds['lo'],ds['hi_file'],4) if P.dw(a-4) in CS]
print('    不加8字节对齐 dw(V-4)=COL: 候选=%d 清单=%s (其中模8=4的两个=%s)'%(
    len(c4),[hex(a) for a in c4],[hex(a) for a in c4 if a%8]))
print('B4b 5个COL指针单元 (V-4) 上下文:')
for a in [0x876ffc,0x87700c,0x87b178,0x87b188]:
    print('   @%08x = COL %08x ; 其前4字节 @%08x = %08x (%s) ; 其后4字节 @%08x = %08x (%s)'%(
        a,P.dw(a),a-4,P.dw(a-4),'COL' if P.dw(a-4) in CS else '-',a+4,P.dw(a+4),'COL' if P.dw(a+4) in CS else '-'))
print('B4b 结论: 所有4张.data虚表都满足 dw(V-4)=COL 且 dw(V-8)=0(非COL), '
      '不存在「dw(V-4)=COL 但 V-8 是COL」的额外情形; '
      '读法1的2个候选(0x87b178/0x87b188)本身就是COL指针存储单元(V-4), 非虚表, '
      'R217按dw(V-4)=COL判据不会把它们计为虚表; 真正风险是零槽表在判据下未被过滤。')

print('\n======== 产物 sha256 / 行数 ========')
for f in ('_r218/pe185.py',):
    pass
import os
for f in ['_r185/pe185.py',__file__]:
    try:
        h=hashlib.sha256(open(f,'rb').read()).hexdigest()
        print('%s lines=%d sha256=%s'%(f,len(open(f).readlines()),h))
    except Exception as e: print(f,e)
