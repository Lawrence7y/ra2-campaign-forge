# -*- coding: utf-8 -*-
"""R215 m14：+0x48 的消费者表——把 931 个 call/jmp [reg+0x48] 位点按其所属函数归并。
归属法：位点地址 A 向前回溯到最近 0x90/0xcc 填充后的指令边界（局部重同步），取该边界为函数起点候选，
        再用『该起点是否作为 vftable 槽值』做二次确认（命中即 owner=someslot）。
不做全段线性反汇编，全部局部窗口。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
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
raw=P.RAW; t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
# 1) 找 931 位点（skipdata lite）
CH=0x10000; hits=[]
m2=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m2.skipdata=True
for base in range(o0,o0+n,CH):
    chunk=raw[base:min(base+CH,o0+n)]; va=tb+(base-o0)
    for a,sz,mn,op in m2.disasm_lite(chunk,va):
        if mn in ('call','jmp') and op.endswith('+ 0x48]') and ',' not in op.split('[')[0]:
            hits.append((a,mn,op))
print('+0x48 位点=%d'%len(hits))
# 2) 位点 -> 所属函数起点：向前找最近的填充(0x90/0xcc>=1)之后的地址，且该地址可解出且不跨越位点
def owner(a):
    o=P.r2o(a)
    j=o-1; pad=0
    while j>0 and raw[j] in (0x90,0xcc): pad+=1; j-=1
    cand=tb+(j-o0)+1
    # 检查 cand..a 能否连续解出且恰停在 a
    oo=P.r2o(cand)
    if oo is None: return None,pad
    cur=cand
    for ins in md.disasm(raw[oo:oo+(a-cand)+8],cand):
        if ins.address==a: return cand,pad
        if ins.address>a: break
        cur=ins.address+ins.size
    return None,pad
OWN=collections.Counter(); NOSLOT=0; slotof=collections.Counter(); SLOTPOS=collections.Counter()
for a,mn,op in hits:
    c,pad=owner(a)
    if c is None: NOSLOT+=1; continue
    OWN[c]+=1
print('可归并到函数起点=%d ; 归并不出=%d ; distinct 函数=%d'%(sum(OWN.values()),NOSLOT,len(OWN)))
vt=[(f,c) for f,c in OWN.items() if POS.get(f)]
print('这些函数中作为 vftable 槽值出现的=%d'%len(vt))
for f,c in sorted(vt,key=lambda x:-x[1])[:20]:
    print('   函数 0x%08x 位点%2d 槽号分布=%s'%(f,c,dict(sorted(POS[f].items()))))
cnt_slot=collections.Counter()
for f,c in vt:
    for i in POS[f]: cnt_slot[i]+=c
print('按槽号聚合的 +0x48 消费位点:',dict(sorted(cnt_slot.items())))
# 3) slot18 的 27 落点里，哪些函数体自己消费 +0x48
T27=list(collections.Counter(v['slots'][18] for v in VIEWS if len(v['slots'])>18))
print('27 落点中自身含 call[?+0x48] 的:')
for T in T27:
    o=P.r2o(T)
    body=list(md.disasm(raw[o:o+400],T))
    c=0
    for x in body:
        if x.mnemonic=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_MEM and x.operands[0].mem.disp==0x48: c+=1
        if x.mnemonic.startswith('ret'): break
    if c: print('   0x%08x 含 %d 处'%(T,c))
json.dump({'hits':len(hits),'own':len(OWN),'noslot':NOSLOT,'vt_funcs':len(vt),
 'top':[['0x%08x'%f,c] for f,c in sorted(OWN.items(),key=lambda x:-x[1])[:30]],
 'by_slot':dict(sorted(cnt_slot.items()))},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m14.json','w'),indent=1)
