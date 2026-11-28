# -*- coding: utf-8 -*-
"""R214 收口用定数：一次输出将写入 FACT_INDEX 的全部数字 + 正反控。"""
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
    V.append(dict(base=st,slots=sl,mdisp=md_,name=nm,col=S2C[st]))
MAIN=[v for v in V if v['mdisp']==0]; SEC=[v for v in V if v['mdisp']!=0]
NM=collections.defaultdict(list)
for v in V: NM[v['name']].append(v)
ck('N1 views/main/sec/slots = 1214/954/260/14044',
   (len(V),len(MAIN),len(SEC),sum(len(x['slots']) for x in V))==(1214,954,260,14044),
   '%d/%d/%d/%d'%(len(V),len(MAIN),len(SEC),sum(len(x['slots']) for x in V)))
ck('N2 主视图 12726 槽 / 次视图 1318 槽',
   sum(len(x['slots']) for x in MAIN)==12726 and sum(len(x['slots']) for x in SEC)==1318,
   '%d/%d'%(sum(len(x['slots']) for x in MAIN),sum(len(x['slots']) for x in SEC)))
TGT=collections.Counter(x for v in V for x in v['slots'])
ck('N3 distinct 目标 6692 / 全部 .text', len(TGT)==6692 and all(P.where(a)=='.text' for a in TGT),len(TGT))
TM=set(x for v in MAIN for x in v['slots']); TS=set(x for v in SEC for x in v['slots'])
ck('N4 主 6345 / 次 348 / 交 1 = 0x4c9150', (len(TM),len(TS),len(TM&TS))==(6345,348,1) and TM&TS=={0x4c9150},
   '%d/%d/%d 交集=%s'%(len(TM),len(TS),len(TM&TS),[hex(x) for x in TM&TS]))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; raw=P.RAW
def dis1(a,n=3):
    off=P.r2o(a)
    return list(md.disasm(raw[off:off+32],a,count=n)) if off is not None else []
ck('N5 0x4c9150 = xor eax,eax ; ret（主次交集唯一目标）',
   [i.mnemonic for i in dis1(0x4c9150,2)]==['xor','ret'] and dis1(0x4c9150,2)[0].op_str=='eax, eax',' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in dis1(0x4c9150)))
# slot18
has18=[v for v in V if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in has18)
ck('N6 slot18: 视图 137（主125/次12）/ distinct 27',
   len(has18)==137 and len(c18)==27,'%d/%d 主%d'%(len(has18),len(c18),sum(1 for v in has18 if v['mdisp']==0)))
ck('N7 slot18 top3 0x4104c0x56 / 0x5f65a0x19 / 0x4e1960x17',
   c18.most_common(3)==[(0x4104c0,56),(0x5f65a0,19),(0x4e1960,17)],c18.most_common(3))
# 0x723ea0/0x723eb0 e8 sites split
t=P.B['.text']; tb=t['lo']; o=t['rawptr']; end=o+t['rawsize']; i=o; H=[]
while i<end-5:
    if raw[i]==0xe8:
        rel=struct.unpack_from('<i',raw,i+1)[0]; tgt=tb+(i-o)+5+rel
        if tgt in (0x723ea0,0x723eb0): H.append((tb+(i-o),tgt))
    i+=1
sp=collections.Counter(x[1] for x in H)
ck('N8 e8 直接调用位点 19 = 0x723ea0 x10 / 0x723eb0 x9',
   len(H)==19 and sp=={0x723ea0:10,0x723eb0:9},'%d %s'%(len(H),{hex(k):v for k,v in sp.items()}))
ck('N9 两桩地址不作为任何槽值', 0x723ea0 not in TGT and 0x723eb0 not in TGT,'')
# 一般式律 X
def adj(a):
    ins=dis1(a,3)
    if len(ins)<2 or ins[0].mnemonic!='sub' or 'esp + 4]' not in ins[0].op_str or ins[1].mnemonic!='jmp': return None
    imm=tg=None
    for op in ins[0].operands:
        if op.type==capstone.x86.X86_OP_IMM: imm=op.imm
    for op in ins[1].operands:
        if op.type==capstone.x86.X86_OP_IMM: tg=op.imm
    return None if imm is None or tg is None else (imm&0xffffffff,tg&0xffffffff,len(ins[0].bytes))
A=[]
for v in SEC:
    for i,val in enumerate(v['slots']):
        r=adj(val)
        if r: A.append(dict(mdisp=v['mdisp'],name=v['name'],idx=i,imm=r[0],tgt=r[1],l0=r[2]))
OWN=collections.defaultdict(list)
for v in V:
    for i,val in enumerate(v['slots']): OWN[val].append((v['base'],v['mdisp'],i))
gen=sum(1 for x in A if any(tt[1]==x['mdisp']-x['imm'] for tt in OWN[x['tgt']]))
simp=sum(1 for x in A if x['imm']==x['mdisp'])
ck('N10 律 X 一般式 305/305（简化式 303/305 保留）', len(A)==305 and gen==305 and simp==303,
   'adj=%d gen=%d simp=%d'%(len(A),gen,simp))
ck('N11 adjustor 指令模板 (5,5)x302 / (8,5)x3', collections.Counter(x['l0'] for x in A)==collections.Counter({5:302,8:3}),
   dict(collections.Counter(x['l0'] for x in A)))
ck('N12 HouseClass 例外两目标 owner 唯一 = mdisp=36 idx3/idx4 且 imm=40-36',
   all(OWN[x['tgt']]==[(0x7ea834,36,3)] or OWN[x['tgt']]==[(0x7ea834,36,4)] for x in A if x['imm']!=x['mdisp']),
   [(hex(x['tgt']),OWN[x['tgt']]) for x in A if x['imm']!=x['mdisp']])
# 单值索引
IDX=collections.defaultdict(collections.Counter)
for v in MAIN:
    for i,val in enumerate(v['slots']): IDX[i][val]+=1
mono=[(i,sum(IDX[i].values())) for i in IDX if len(IDX[i])==1]
b=collections.Counter('1' if n==1 else '2-4' if n<=4 else '5-9' if n<=9 else '10-99' if n<=99 else '>=100' for _,n in mono)
ck('N13 单值索引 91/344 且分母>=100 为 0', len(mono)==91 and len(IDX)==344 and b['>=100']==0,
   '%d/%d 桶=%s'%(len(mono),len(IDX),dict(b)))
ck('N14 idx0 distinct=863 非单值', len(IDX[0])==863 and sum(IDX[0].values())==954,
   '%d/%d'%(len(IDX[0]),sum(IDX[0].values())))
print('\n断言 %d 条 FAIL %d 条 %s'%(NA,len(F),F if F else ''))
