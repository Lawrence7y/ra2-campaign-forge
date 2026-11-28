# -*- coding: utf-8 -*-
"""R208 m5：14043 vs R207 的 14044 差异定位（逐 COL 比对），并给槽目标的 .text 覆盖普查。
正控：逐 COL vlen 与本轮 m4 一致
反控：把 vlen 判据换成「槽值落在任意段」会得到荒谬大数
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(start,cap=4096):
    k=0
    while k<cap and P.where(P.dw(start+4*k))=='.text': k+=1
    return k
L={c:vlen(v) for c,v in vt.items()}
print('业务 COL %d，槽合计 %d，长度分布 %s' % (len(L),sum(L.values()),collections.Counter(L.values()).most_common(10)))
print('最长 vftable: ',sorted(L.items(),key=lambda kv:-kv[1])[:5])
# 段内覆盖：槽目标是否只落 .text 且分布
tgt=collections.Counter()
for c,s in vt.items():
    for k in range(L[c]): tgt[P.dw(s+4*k)]+=1
print('槽目标不同地址 %d，总槽 %d' % (len(tgt),sum(tgt.values())))
lo=min(tgt); hi=max(tgt)
print('地址范围 0x%x..0x%x (.text 0x401000..0x7e1000)' % (lo,hi))
# 按 64KB 桶
b=collections.Counter((a>>16) for a in tgt)
print('按 64KB 桶 top8', [(hex(k<<16),v) for k,v in b.most_common(8)])
# 最高频目标是不是同一个函数（前 8 条反汇编）
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
for a in [0x4c9150,0x410590,0x410220]:
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+16],a))
    print('  0x%x: %s' % (a,'; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins)))
# 1 槽 vftable 的槽值分布
one=[c for c in L if L[c]==1]
print('1 槽 vftable %d，其槽值 top5 %s' % (len(one),collections.Counter(P.dw(vt[c]) for c in one).most_common(5)))
# 反控：vlen 判据放宽为「任意段」
def vlen_any(start,cap=4096):
    k=0
    while k<cap and P.where(P.dw(start+4*k)) is not None: k+=1
    return k
LA={c:vlen_any(v) for c,v in vt.items()}
print('反控 放宽判据后槽合计 %d（应远大于 %d）' % (sum(LA.values()),sum(L.values())))
json.dump(dict(bizCols=len(L),slots=sum(L.values()),distinct=len(tgt),
               dist=[[k,v] for k,v in collections.Counter(L.values()).most_common(12)],
               top=[[hex(k),v] for k,v in tgt.most_common(12)]),
          open('_r208/m5_slots.json','w'),ensure_ascii=False,indent=1)
