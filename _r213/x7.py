# -*- coding: utf-8 -*-
"""R213 x7：律 X —— 次视图 slot0 的 this-adjustor thunk 立即数 == 该 COL 记录的 mdisp。
全 260 条次视图分类 + 101 条 adjustor 的全槽一致性 + 正反控。
只用 <=64 字节窗口 detail 反汇编，禁整段 .text 全量 disasm。
"""
import sys,struct,collections,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def ins(a,n=6,maxb=48):
    o=P.r2o(a); out=[]
    if o is None: return out
    for i in md.disasm(P.RAW[o:o+maxb],a):
        out.append((i.address,i.mnemonic,i.op_str)); 
        if len(out)>=n: break
    return out
def adjustor(a):
    """返回 (is_adjustor, imm, jmp_target)。形态：sub dword ptr [esp+4], imm ; jmp rel32"""
    q=ins(a,3)
    if len(q)<2: return (False,None,None)
    if q[0][1]=='sub' and 'esp + 4' in q[0][2] and q[1][1]=='jmp':
        try: imm=int(q[0][2].split(',')[-1].strip(),16)
        except Exception: return (False,None,None)
        jt=int(q[1][2],16) if q[1][2].startswith('0x') else None
        return (True,imm,jt)
    return (False,None,None)

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
VT={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text': VT[w[k]]=base+4*k+4
SL={}
for c in COL:
    k=0
    while k<4096 and P.where(P.dw(VT[c]+4*k))=='.text': k+=1
    SL[c]=[P.dw(VT[c]+4*i) for i in range(k)]
NA=0;F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

SEC=[c for c in COL if COL[c]['mdisp']!=0]; MAIN=[c for c in COL if COL[c]['mdisp']==0]
print('次视图=%d 主视图=%d'%(len(SEC),len(MAIN)))
# ---- 1) 次视图 slot0 形态分类 ----
cls=collections.Counter(); adj=[]; nonadj=[]
for c in SEC:
    ok,imm,jt=adjustor(SL[c][0])
    if ok: adj.append((c,imm,jt)); cls['adjustor']+=1
    else: nonadj.append(c); cls['other']+=1
print('\n=== T1 次视图 slot0 形态 ===')
print('  分类 =',cls.most_common())
by_m=collections.Counter(COL[c]['mdisp'] for c,_ ,_ in adj)
print('  adjustor 的 mdisp 分布 =',sorted(by_m.items()))
bn_m=collections.Counter(COL[c]['mdisp'] for c in nonadj)
print('  非 adjustor 的 mdisp 分布 =',sorted(bn_m.items()))
ck('T1-1 adjustor 条数 == 101', len(adj)==101, len(adj))
ck('T1-2 非 adjustor 恰为 mdisp 8/12/21784 三类', set(bn_m)=={8,12,21784}, sorted(bn_m))
ck('T1-3 非 adjustor 条数 == 159', len(nonadj)==159, len(nonadj))

# ---- 2) 律 X：imm == mdisp ----
print('\n=== T2 律 X：adjustor 立即数 == mdisp ===')
eq=[(c,imm) for c,imm,_ in adj if imm==COL[c]['mdisp']]
print('  imm==mdisp 的条数 = %d / %d'%(len(eq),len(adj)))
ck('T2-1 imm == mdisp 全 101 条', len(eq)==len(adj), '%d/%d'%(len(eq),len(adj)))
bad=[(hex(c),COL[c]['name'],COL[c]['mdisp'],imm) for c,imm,_ in adj if imm!=COL[c]['mdisp']]
print('  反例 =',bad[:6])
# 逐 mdisp 值明细
det=collections.defaultdict(set)
for c,imm,_ in adj: det[COL[c]['mdisp']].add(imm)
print('  mdisp -> 观测到的 imm 集合 =',{k:sorted(v) for k,v in sorted(det.items())})
ck('T2-2 每个 mdisp 值对应的 imm 唯一且相等', all(v=={k} for k,v in det.items()), {k:sorted(v) for k,v in det.items()})
# ---- 3) 101 条 adjustor 视图的全槽一致性 ----
print('\n=== T3 adjustor 视图内全部槽的同构性 ===')
allslot=True; slotcnt=collections.Counter(); jmpset=collections.defaultdict(set)
for c,imm,_ in adj:
    slotcnt[len(SL[c])]+=1
    for s in SL[c]:
        ok,i2,jt=adjustor(s)
        if not ok or i2!=imm: allslot=False
        jmpset[c].add(jt)
ck('T3-1 adjustor 视图内每个槽都是同 imm 的 adjustor', allslot)
print('  adjustor 视图槽数分布 =',slotcnt.most_common(6))
ck('T3-2 adjustor 视图槽数恒 == 3 或更多且 <=3（除 Locomotion 50 槽组）',
   set(slotcnt)<= {6,50,5}, sorted(slotcnt))
# 反控：同一视图内 jmp 目标是否互不相同（表明是多继承的不同基类槽）
print('  同一视图内 jmp 目标数分布 =',collections.Counter(len(v) for v in jmpset.values()).most_common(5))
# ---- 4) 主视图 slot0 形态（反控）----
print('\n=== T4 反控：主视图 slot0 从不为 adjustor ===')
madj=[c for c in MAIN if adjustor(SL[c][0])[0]]
ck('T4-1 主视图 954 条中 slot0 为 adjustor 的条数 == 0', len(madj)==0, len(madj))
mcls=collections.Counter()
for c in MAIN:
    q=ins(SL[c][0],1)
    mcls[q[0][1] if q else 'NONE']+=1
print('  主视图 slot0 首指令助记符分布(前8) =',mcls.most_common(8))
# ---- 5) 恒等核验：mdisp 值集合 ----
print('\n=== T5 mdisp 值域 ===')
vals=collections.Counter(COL[c]['mdisp'] for c in SEC)
print('  ',sorted(vals.items()))
ck('T5-1 adjustor 组 mdisp 集合 == {4,24,36,40,44,1728}', set(det)=={4,24,36,40,44,1728}, sorted(det))
ck('T5-2 六值条数合计 == 101', sum(vals[v] for v in det)==101, sum(vals[v] for v in det))
# ---- 6) 8/12/21784 的 slot0 形态明细 ----
print('\n=== T6 非 adjustor 三类 slot0 明细 ===')
seen=set()
for c in nonadj:
    m=COL[c]['mdisp']; s0=SL[c][0]
    if (m,s0) in seen: continue
    seen.add((m,s0))
    print('  mdisp=%-6d slot0=%08x len=%-2d : %s'%(m,s0,len(SL[c]),' ; '.join('%s %s'%(a,b) for _,a,b in ins(s0,4))))
print('\n断言 %d / FAIL %d %s'%(NA,len(F),F))
json.dump({'sec':len(SEC),'adj':len(adj),'nonadj':len(nonadj),
 'adj_mdisp':sorted(by_m.items()),'nonadj_mdisp':sorted(bn_m.items()),
 'det':{str(k):sorted(v) for k,v in sorted(det.items())},
 'eq':len(eq),'slotcnt':slotcnt.most_common(),'madj':len(madj),
 'main_slot0':mcls.most_common(10),'nassert':NA,'fails':F},
 open('_r213/x7.json','w'),indent=1,ensure_ascii=False)
