# -*- coding: utf-8 -*-
"""R214 §2.12 规则 D 主会话独立复算源：不复用 ex1/ex2 代码，重写表重建后逐项核对双方报数。
防 OOM：capstone 只对 adjustor 候选与少量点位开小窗口（md.disasm(count<=4)）。
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

# ---------- 表重建（独立实现） ----------
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COLA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COLA[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PRED=collections.Counter()
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text':
            PRED[w[k]]+=1
VIEWS=[]   # (coladdr, base, slots, mdisp, name)
for col,(md_,ptd,pchd,nm) in COLA.items():
    # 视图起点 = 唯一前驱位点 + 4（前驱位点未单独存地址，这里按扫描重取）
    pass
# 重取前驱位点地址
PREDADDR=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text':
            PREDADDR[w[k]].append(base+4*k)
starts=sorted(min(v) +4 for v in PREDADDR.values() if len(v)==1)
S2C={}
for col,v in PREDADDR.items():
    if len(v)==1: S2C[min(v)+4]=col
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[]; a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a)); a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,name=nm.decode() if False else nm))
print('VIEWS=%d COL=%d'%(len(VIEWS),len(COLA)))
for v in VIEWS:
    v['nm']=v['name'][1:] if v['name'].startswith('.') else v['name']
MAIN=[v for v in VIEWS if v['mdisp']==0]
SEC=[v for v in VIEWS if v['mdisp']!=0]
NM=collections.defaultdict(list)
for v in VIEWS: NM[v['nm']].append(v)
ck('A1 视图=1214 主视图=954 次视图=260', len(VIEWS)==1214 and len(MAIN)==954 and len(SEC)==260,
   '%d/%d/%d'%(len(VIEWS),len(MAIN),len(SEC)))
TS=sum(len(v['slots']) for v in VIEWS)
ck('A2 槽总数=14044', TS==14044,TS)
secs=collections.Counter(P.where(x) for v in VIEWS for x in v['slots'])
ck('A3 槽目标全落 .text（14044/14044）', secs=={'.text':14044}, dict(secs))
TGT=collections.Counter(x for v in VIEWS for x in v['slots'])
ck('A4 distinct 槽目标=6692', len(TGT)==6692,len(TGT))
TM=set(x for v in MAIN for x in v['slots']); TSec=set(x for v in SEC for x in v['slots'])
ck('A5 主/次 distinct 与交集', (len(TM),len(TSec),len(TM&TSec),len(TM-TSec),len(TSec-TM))==(6345,348,1,6344,347),
   '%d/%d/%d/%d/%d'%(len(TM),len(TSec),len(TM&TSec),len(TM-TSec),len(TSec-TM)))
ck('A6 反控 COL+4 口径取 .text 指针 = 0/954', sum(1 for v in MAIN if P.where(P.dw(v['col']+4))=='.text')==0,'')

# ---------- B 组 slot18 ----------
def slot(v,i): return v['slots'][i] if i<len(v['slots']) else None
has18=[v for v in VIEWS if len(v['slots'])>18]
ck('B1 槽数>18 的视图=137（主125 次12）', len(has18)==137 and sum(1 for v in has18 if v['mdisp']==0)==125 and sum(1 for v in has18 if v['mdisp']!=0)==12,
   '%d 主%d 次%d'%(len(has18),sum(1 for v in has18 if v['mdisp']==0),sum(1 for v in has18 if v['mdisp']!=0)))
c18=collections.Counter(slot(v,18) for v in has18)
ck('B2 slot18 distinct=27 且 all .text', len(c18)==27 and all(P.where(a)=='.text' for a in c18),len(c18))
ck('B3 slot18 top3 = 0x4104c0x56 / 0x5f65a0x19 / 0x4e1960x17',
   c18.most_common(3)==[(0x4104c0,56),(0x5f65a0,19),(0x4e1960,17)],c18.most_common(3))
for nm,exp0,exp18,expn in [('?AVMouseClass@@',0x4f4240,0x5bda80,55),
                           ('?AVTabClass@@',0x4f4240,0x4c9150,55),
                           ('?AVScrollClass@@',0x4f4240,0x4c9150,55)]:
    vs=[v for v in NM[nm] if v['mdisp']==0]
    ok=len(vs)==1 and vs[0]['slots'][0]==exp0 and len(vs[0]['slots'])==expn and slot(vs[0],18)==exp18
    ck('B4 %s 主视图 slot0/slot18/槽数'%nm, ok,
       '%s %s n=%d'%(hex(vs[0]['slots'][0]) if vs else '-',hex(slot(vs[0],18)) if vs and slot(vs[0],18) else '-',len(vs[0]['slots']) if vs else 0))
for nm in ('?AVMouseClass@@','?AVTabClass@@','?AVScrollClass@@'):
    vs=[v for v in NM[nm] if v['mdisp']==21784]
    ck('B5 %s 21784 次视图仅1槽且 slot0=0x6d1770'%nm,
       len(vs)==1 and len(vs[0]['slots'])==1 and vs[0]['slots'][0]==0x6d1770,
       '%s'%(hex(vs[0]['slots'][0]) if vs else '-'))
c17=collections.Counter(slot(v,17) for v in VIEWS if len(v['slots'])>17)
c19=collections.Counter(slot(v,19) for v in VIEWS if len(v['slots'])>19)
ck('B6 控制组 slot17/19 distinct=28/27', len(c17)==28 and len(c19)==27,'%d/%d'%(len(c17),len(c19)))

# ---------- B7 0x723ea0/0x723eb0 引用（独立扫 e8，不用正则） ----------
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
t=P.B['.text']; tb=t['lo']; tn=t['rawsize']
raw=P.RAW
hits=[]
o=t['rawptr']; end=o+tn
i=o
while i<end-5:
    if raw[i]==0xe8:
        rel=struct.unpack_from('<i',raw,i+1)[0]
        tgt=tb+(i-o)+5+rel
        if tgt in (0x723ea0,0x723eb0): hits.append((tb+(i-o),tgt))
    i+=1
ck('B7 0x723ea0/0x723eb0 的 e8 直接调用位点=19', len(hits)==19,len(hits))
ck('B8 这两地址不作为任何 vftable 槽值（0/14044）', not (0x723ea0 in TGT or 0x723eb0 in TGT),
   '%d'%(TGT.get(0x723ea0,0)+TGT.get(0x723eb0,0)))
# 用 capstone 复核每条命中确实是 call 到该目标
bad=0
for a,tg in hits:
    off=P.r2o(a); ins=list(md.disasm(raw[off:off+5],a,count=1))
    if not ins or ins[0].mnemonic!='call' or not ins[0].op_str.startswith('0x%x'%tg): bad+=1
ck('B9 capstone 逐条复核 19 处均为 call 且目标相符', bad==0,'bad=%d'%bad)

# ---------- C 组 adjustor ----------
md2=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md2.detail=True
def adj(a):
    off=P.r2o(a)
    if off is None: return None
    ins=list(md2.disasm(raw[off:off+16],a,count=3))
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4]' not in i0.op_str: return None
    if i1.mnemonic!='jmp': return None
    imm=None
    for op in i0.operands:
        if op.type==capstone.x86.X86_OP_IMM: imm=op.imm
    if imm is None: return None
    tgt=None
    for op in i1.operands:
        if op.type==capstone.x86.X86_OP_IMM: tgt=op.imm
    if tgt is None: return None
    return (imm & 0xffffffff,tgt & 0xffffffff,len(i0.bytes),len(i1.bytes))
ALLADJ=[]
for v in SEC:
    for i,val in enumerate(v['slots']):
        r=adj(val)
        if r: ALLADJ.append(dict(col=v['col'],name=(v['name'][1:] if v['name'].startswith('.') else v['name']),mdisp=v['mdisp'],idx=i,val=val,imm=r[0],tgt=r[1],l0=r[2],l1=r[3]))
ck('C1 次视图内 adjustor 槽=305', len(ALLADJ)==305,len(ALLADJ))
ok=[x for x in ALLADJ if x['imm']==x['mdisp']]
bad2=[x for x in ALLADJ if x['imm']!=x['mdisp']]
ck('C2 imm==mdisp 通过 303 / 例外 2', len(ok)==303 and len(bad2)==2,'%d/%d'%(len(ok),len(bad2)))
ck('C3 两例外均为 ?AVHouseClass@@ mdisp=40 idx3/idx4 imm=4 目标 0x4f6e60/0x4f6950',
   sorted((x['name'],x['mdisp'],x['idx'],x['imm'],x['tgt']) for x in bad2)==
   [('?AVHouseClass@@',40,3,4,0x4f6e60),('?AVHouseClass@@',40,4,4,0x4f6950)],
   [('?AVHouseClass@@',x['mdisp'],x['idx'],x['imm'],hex(x['tgt'])) for x in bad2])
ck('C4 主视图内 adjustor 槽=0', sum(1 for v in MAIN for x in v['slots'] if adj(x))==0,'')
ck('C5 每张次视图 adjustor 数分布 {0:159,3:100,5:1}',
   collections.Counter(collections.Counter(x['col'] for x in ALLADJ).get(v['col'],0) for v in SEC)==
   collections.Counter({0:159,3:100,5:1}),
   dict(collections.Counter(collections.Counter(x['col'] for x in ALLADJ).get(v['col'],0) for v in SEC)))
ck('C6 adjustor jmp 目标 distinct=40 全 .text 且无跳回自身',
   len(set(x['tgt'] for x in ALLADJ))==40 and all(P.where(x['tgt'])=='.text' for x in ALLADJ)
   and all(x['tgt']!=x['val'] for x in ALLADJ),len(set(x['tgt'] for x in ALLADJ)))
# HouseClass 细节：例外目标落在 mdisp=36 次视图 idx3/idx4
H=[v for v in VIEWS if v['nm']=='?AVHouseClass@@']
ck('C7 HouseClass 视图数=7 且 mdisp 集={0,4,8,12,36,40,44}',
   len(H)==7 and sorted(v['mdisp'] for v in H)==[0,4,8,12,36,40,44],[(hex(v['col']),v['mdisp'],len(v['slots'])) for v in H])
h36=[v for v in H if v['mdisp']==36][0]; h0=[v for v in H if v['mdisp']==0][0]
ck('C8 例外目标 0x4f6e60/0x4f6950 落 mdisp=36 视图 idx3/idx4，不在主视图',
   slot(h36,3)==0x4f6e60 and slot(h36,4)==0x4f6950 and 0x4f6e60 not in h0['slots'] and 0x4f6950 not in h0['slots'],
   '%s/%s 主视图含?%s'%(hex(slot(h36,3)),hex(slot(h36,4)),(0x4f6e60 in h0['slots'],0x4f6950 in h0['slots'])))
ck('C9 imm=40-36=4 成立', 40-36==4 and all(x['tgt'] not in h0['slots'] for x in bad2),'')
# C10 mdisp 元组分布
MT=collections.Counter()
for v in NM:
    tup=tuple(sorted(x for x in (y['mdisp'] for y in NM[v]) if x!=0))
    if tup: MT[tup]+=1
ck('C10 mdisp 元组只有 6 种且分布相符',
   dict(MT)=={(4,8,12):76,(4,):7,(4,24):6,(21784,):3,(4,8,12,36,40,44):1,(4,8,12,1728):1},dict(MT))
ck('C11 adjustor 指令模板 2 种（5B sub x302 / 8B sub x3）',
   collections.Counter((x['l0'],x['l1']) for x in ALLADJ)==collections.Counter({(5,5):302,(8,5):3}),
   dict(collections.Counter((x['l0'],x['l1']) for x in ALLADJ)))
# D 组：m1 前缀法失效的量化复核
LEN=collections.Counter(len(v['slots']) for v in MAIN)
long=[v for v in MAIN if len(v['slots'])>=100]
ck('D1 前缀法失效量化：主视图最长 344 槽、长度层 55 层（前缀法据此产生 93 类歧义与深度 75 退化链）',
   max(len(v['slots']) for v in MAIN)==344 and len(LEN)==55 and len(long)==21,
   'len>=100 类=%d max=%d 长度层=%d'%(len(long),max(len(v['slots']) for v in MAIN),len(LEN)))
print('\n断言 %d 条 FAIL %d 条 %s'%(NA,len(F),F if F else ''))
json.dump(dict(adj=len(ALLADJ),bad=len(bad2),hits=len(hits),distinct_target=len(TGT),
               fail=F,nassert=NA),open('/home/t628/projects/ra2-campaign-forge/_r214/a1.json','w'))
