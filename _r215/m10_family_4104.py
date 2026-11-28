# -*- coding: utf-8 -*-
"""R215 m10：slot17/18/19 的 top1 目标是否构成同一函数族。
0x410440(slot17 top,57) / 0x4104c0(slot18 top,56) / 0x4104f0(slot19 top,73) 地址相邻。
测：①0x410400-0x4105a0 区间的全部函数边界与全局变量引用；②三者的指令级差异；
③这些目标各自作为哪些槽号的槽值（跨槽号复用矩阵）。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def show(a0,a1):
    o=P.r2o(a0); d=list(md.disasm(raw[o:P.r2o(a1)],a0))
    for x in d:
        glob=''
        for op in x.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp:
                glob=' ;glob 0x%x'%(op.mem.disp&0xffffffff)
        print('  %08x %-18s %-28s%s'%(x.address,x.bytes.hex(),x.mnemonic+' '+x.op_str,glob))
print('=== 0x410400 - 0x4105a0 区域 ===')
show(0x410400,0x4105a0)
# 跨槽号复用矩阵：这些目标出现在哪些槽号
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),s['lo']
COLA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COLA[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PRE=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PRE[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PRE.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PRE.items() if len(v)==1}
VIEWS=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[];a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a));a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1
print('=== 三目标跨槽号复用 ===')
for T in (0x410440,0x4104c0,0x4104f0,0x410460,0x410480,0x4104b0,0x4104e0):
    print('0x%08x 出现 %d 次 槽号分布=%s'%(T,sum(POS[T].values()),dict(sorted(POS[T].items()))))
# 该区域内所有函数被哪些槽号引用
print('=== 0x410400-0x4105a0 区间入口被槽引用情况 ===')
for a in range(0x410400,0x4105a0,0x10):
    if POS.get(a): print('  0x%08x 次数=%d 槽号=%s'%(a,sum(POS[a].values()),dict(sorted(POS[a].items()))))
# slot17/18/19 三组的 distinct 目标与"是否共享调用者"
h17=[v for v in VIEWS if len(v['slots'])>17]; h19=[v for v in VIEWS if len(v['slots'])>19]
c17=collections.Counter(v['slots'][17] for v in h17)
c18=collections.Counter(v['slots'][18] for v in [v for v in VIEWS if len(v['slots'])>18])
c19=collections.Counter(v['slots'][19] for v in h19)
print('=== slot17/18/19 交集 ===')
print('17∩18=%d 18∩19=%d 17∩19=%d 17∩18∩19=%d'%(
    len(set(c17)&set(c18)),len(set(c18)&set(c19)),len(set(c17)&set(c19)),
    len(set(c17)&set(c18)&set(c19))))
print('17-only=%d 18-only=%d 19-only=%d'%(len(set(c17)-set(c18)-set(c19)),
    len(set(c18)-set(c17)-set(c19)),len(set(c19)-set(c17)-set(c18))))
json.dump({'pos':{('0x%08x'%k):dict(sorted(v.items())) for k,v in POS.items() if k<0x410600 and k>=0x410400},
 'inter':{'17_18':len(set(c17)&set(c18)),'18_19':len(set(c18)&set(c19)),'17_19':len(set(c17)&set(c19)),
          'all3':len(set(c17)&set(c18)&set(c19))},
 'trio':[('0x%08x'%k,v) for k,v in c17.most_common(3)]+[('0x%08x'%k,v) for k,v in c18.most_common(3)]+[('0x%08x'%k,v) for k,v in c19.most_common(3)]},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m10.json','w'),indent=1)
