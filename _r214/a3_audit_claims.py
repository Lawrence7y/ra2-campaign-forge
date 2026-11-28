# -*- coding: utf-8 -*-
"""R214 §2.12 规则 D：复算审计员 #553 的三条订正 + 两条「口径恒真」判定。
1) B5 判据失效：d17=28 / d18=27 / d19=27，d18==d19 ⇒ 「三者不等」不成立；改用交并集判据。
2) 一般式 imm == mdisp_self - mdisp_target 应 305/305 成立（R213 律 X 的简化式只在 303 条成立）。
3) A1/A5 为定义恒真：去掉 .text 过滤（仅用下一起点截断）槽数应显著大于 14044（审计报 29580）。
4) 8 字节 sub 的 3 条应全属 AircraftClass mdisp=1728。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
NA=0; F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=(s32(w[k+1]),nm.decode('latin1')[1:])
PA=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COL and P.where(w[k+1])=='.text': PA[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PA.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PA.items() if len(v)==1}
V=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[]; a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a)); a+=4
    md_,nm=COL[S2C[st]]
    V.append(dict(base=st,slots=sl,mdisp=md_,name=nm))
SEC=[v for v in V if v['mdisp']!=0]; MAIN=[v for v in V if v['mdisp']==0]
print('views=%d main=%d sec=%d slots=%d'%(len(V),len(MAIN),len(SEC),sum(len(v['slots']) for v in V)))

print('\n===== 订正 1：slot17/18/19 判据 =====')
def col(i): return collections.Counter(v['slots'][i] for v in V if len(v['slots'])>i)
c17,c18,c19=col(17),col(18),col(19)
ck('1a 实测 distinct = 28/27/27（审计报数成立，「三者不等」表述失效）',
   (len(c17),len(c18),len(c19))==(28,27,27),'%d/%d/%d'%(len(c17),len(c18),len(c19)))
ck('1b d18 == d19（原判据失效的实证）', len(c18)==len(c19),'%d vs %d'%(len(c18),len(c19)))
i1819=len(set(c18)&set(c19)); o18=len(set(c18)-set(c19)); o19=len(set(c19)-set(c18))
ck('1c 替用判据：slot18∩slot19=1 且两侧各有独有目标（非平凡）',
   i1819==1 and o18>0 and o19>0,'∩%d 仅18=%d 仅19=%d 交集元素=%s'%(i1819,o18,o19,[hex(x) for x in set(c18)&set(c19)]))

print('\n===== 订正 2：一般式 imm == mdisp_self - mdisp_target =====')
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
raw=P.RAW
def adj(a):
    off=P.r2o(a)
    if off is None: return None
    ins=list(md.disasm(raw[off:off+16],a,count=3))
    if len(ins)<2 or ins[0].mnemonic!='sub' or 'esp + 4]' not in ins[0].op_str or ins[1].mnemonic!='jmp': return None
    imm=tgt=None
    for op in ins[0].operands:
        if op.type==capstone.x86.X86_OP_IMM: imm=op.imm
    for op in ins[1].operands:
        if op.type==capstone.x86.X86_OP_IMM: tgt=op.imm
    if imm is None or tgt is None: return None
    return (imm&0xffffffff,tgt&0xffffffff,len(ins[0].bytes))
A=[]
for v in SEC:
    for i,val in enumerate(v['slots']):
        r=adj(val)
        if r: A.append(dict(col=v['base'],name=v['name'],mdisp=v['mdisp'],idx=i,imm=r[0],tgt=r[1],l0=r[2]))
# 目标所属视图
OWN={}
for v in V:
    for i,val in enumerate(v['slots']):
        OWN.setdefault(val,[]).append((v['base'],v['mdisp'],i))
gen=[x for x in A if any(t[1]==x['mdisp']-x['imm'] for t in OWN.get(x['tgt'],[]))]
simp=[x for x in A if x['imm']==x['mdisp']]
ck('2a adjustor 总数 305', len(A)==305,len(A))
ck('2b 简化式 imm==mdisp_self 仅 303（R213 律 X 原口径，保留）', len(simp)==303,len(simp))
ck('2c 一般式 imm==mdisp_self-mdisp_target 在 305/305 全部成立（审计订正成立）',
   len(gen)==305,'%d/%d'%(len(gen),len(A)))
det=[(x['name'],x['mdisp'],x['idx'],x['imm'],[(hex(t[0]),t[1],t[2]) for t in OWN.get(x['tgt'],[])]) for x in A if x not in gen]
ck('2d 一般式反例 0 条', not det,det[:3])
for x in A:
    if x['imm']!=x['mdisp']:
        print('   例外 %s mdisp=%d idx=%d imm=%d -> %s owner=%s'%(x['name'],x['mdisp'],x['idx'],x['imm'],hex(x['tgt']),OWN.get(x['tgt'])))

print('\n===== 订正 3：去掉 .text 过滤后的槽数（A1/A5 恒真判定） =====')
tot=0; secs=collections.Counter()
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    a=st; n=0
    while a<end:
        secs[P.where(P.dw(a))]+=1; n+=1; a+=4
    tot+=n
ck('3a 无 .text 过滤的槽数显著大于 14044（审计报 29580，判 A1 为定义恒真）',
   tot>14044,'tot=%d 审计报 29580 一致=%s'%(tot,tot==29580))
print('   段分布=%s'%dict(secs))
ck('3b 3a 的分段口径与审计报数一致（29580）', tot==29580,tot)

print('\n===== 订正 4：8 字节 sub 的 3 条归属 =====')
e8=[x for x in A if x['l0']==8]
ck('4a 8 字节 sub 恰 3 条且全属 ?AVAircraftClass@@ mdisp=1728',
   len(e8)==3 and all(x['name']=='?AVAircraftClass@@' and x['mdisp']==1728 for x in e8),
   [(x['name'],x['mdisp'],x['idx']) for x in e8])
ck('4b 其 imm 均为 0x6c0=1728（需 4 字节立即数，故指令长 8B）',
   all(x['imm']==0x6c0 for x in e8),[hex(x['imm']) for x in e8])

print('\n===== 订正 5：单值索引的分母塌缩 =====')
IDX=collections.defaultdict(collections.Counter)
for v in MAIN:
    for i,val in enumerate(v['slots']): IDX[i][val]+=1
mono=[(i,sum(IDX[i].values())) for i in IDX if len(IDX[i])==1]
buckets=collections.Counter()
for i,n in mono:
    b='1' if n==1 else ('2-4' if n<=4 else ('5-9' if n<=9 else ('10-99' if n<=99 else '>=100')))
    buckets[b]+=1
ck('5a 单值索引 91 个且分母>=100 者为 0（审计分母塌缩判定成立）',
   len(mono)==91 and buckets['>=100']==0,'%d 桶=%s'%(len(mono),dict(buckets)))
ck('5b 唯一分母=954 的索引是 idx0 且 idx0 非单值',
   len(IDX[0])==863 and sum(IDX[0].values())==954,'idx0 distinct=%d n=%d'%(len(IDX[0]),sum(IDX[0].values())))
print('\n断言 %d 条 FAIL %d 条 %s'%(NA,len(F),F if F else ''))
json.dump(dict(gen=len(gen),simp=len(simp),tot=tot,buckets=dict(buckets),fail=F),
          open('/home/t628/projects/ra2-campaign-forge/_r214/a3.json','w'),ensure_ascii=False)
