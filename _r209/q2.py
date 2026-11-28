# -*- coding: utf-8 -*-
"""R209 q2: 70 个 this 调整 thunk 的**全槽**引用图（不只 slot0）+ 三 I 形态函数直接调用 + 0x410260/0x6d1770 语义。
B81 编码订正：81 6C 24 04 imm32(4B) E9 rel32  => E9 在 +8，rel 在 +9，落点 = va+13+rel。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
TE=P.B['.text']; TB=P.RAW[TE['rawptr']:TE['rawptr']+TE['rawsize']]; BASE=TE['lo']

def scan(buf,base):
    out=[]
    for pat,kind,ecut in ((b'\x83\x6c\x24\x04','A83',5),(b'\x81\x6c\x24\x04','B81',8)):
        i=0
        while True:
            i=buf.find(pat,i)
            if i<0: break
            if i+ecut+5<=len(buf) and buf[i+ecut]==0xe9:
                imm=s32(buf[i+4]) if kind=='A83' else s32(struct.unpack_from('<I',buf,i+4)[0])
                rel=s32(struct.unpack_from('<I',buf,i+ecut+1)[0])
                out.append(dict(va=base+i,kind=kind,imm=imm,
                                jmp=(base+i+ecut+5+rel)&0xffffffff,
                                raw=buf[i:i+ecut+5].hex(),len=ecut+5))
            i+=1
    out.sort(key=lambda x:x['va']); return out
TH=scan(TB,BASE)
A=[t for t in TH if t['kind']=='A83']; B=[t for t in TH if t['kind']=='B81']
ck('1 A83 .text 锚点=67', len(A)==67, len(A))
ck('2 B81 .text 锚点=3 且落点与 R208 QN1 一致',
   len(B)==3 and [hex(t['jmp']) for t in B]==['0x414290','0x4142f0','0x414300'],
   [(hex(t['va']),hex(t['imm']),hex(t['jmp'])) for t in B])
ck('3 合计 70 thunk', len(TH)==70, len(TH))
ck('4 全部 imm 为 4 的倍数 且 >0', all(t['imm']>0 and t['imm']%4==0 for t in TH))
# 反控：合成 B81
syn=b'\x81\x6c\x24\x04'+struct.pack('<I',1728)+b'\xe9'+struct.pack('<i',-33773)+b'\xcc'
d=scan(syn,0x41c670)
ck('5 正控 合成 B81 命中且落点=0x414290', len(d)==1 and d[0]['jmp']==0x414290, d)
neg=sum(len(scan(P.RAW[P.B[s]['rawptr']:P.B[s]['rawptr']+P.B[s]['rawsize']],P.B[s]['lo'])) for s in ('.rdata','.data','.rsrc'))
ck('6 反控 非 .text 段 0', neg==0, neg)

# COL / vftable 模型
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
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*k)
vt_of={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt_of[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
VT={c:tuple(P.dw(vt_of[c]+4*k) for k in range(vlen(vt_of[c]))) for c in vt_of}
ck('7 模型复现 1214/954/1214', len(COL)==1214 and len(G)==954 and len(VT)==1214,
   '%d/%d/%d'%(len(COL),len(G),len(VT)))
# 全槽引用：slot 值 -> [(col, slotidx)]
slothit=collections.defaultdict(list)
for c,t in VT.items():
    for i,v in enumerate(t): slothit[v].append((c,i))
THSET={t['va'] for t in TH}
used=[t for t in TH if t['va'] in slothit]
unused=[t for t in TH if t['va'] not in slothit]
ck('8 被任一 vftable 槽引用的 thunk 数 = 22', len(used)==22, len(used))
ck('9 未被任何 vftable 槽引用 = 48', len(unused)==48, len(unused))
s0=collections.Counter(); sn0=collections.Counter()
for t in TH:
    for (c,i) in slothit.get(t['va'],[]):
        if i==0: s0[t['va']]+=1
        else: sn0[t['va']]+=1
ck('10 slot0 命中 = 22 个 thunk（21 A83 + 1 B81）',
   len(s0)==22 and sum(1 for t in used if t['kind']=='B81' and s0.get(t['va']))==1,
   'A83 slot0 thunks=%d, B81 slot0 thunks=%d'%(sum(1 for t in TH if t['kind']=='A83' and s0.get(t['va'])),
                                               sum(1 for t in TH if t['kind']=='B81' and s0.get(t['va']))))
ck('11 非 slot0 命中 = 0', len(sn0)==0, dict(list(sn0.items())[:5]))
# 22 个 thunk 承载的 COL 数
tot_col=sum(len(slothit[t['va']]) for t in used)
ck('12 22 个 thunk 承载的额外视图 COL 总数 = 101', tot_col==101, tot_col)
ck('13 101 条 COL 的 mdisp 全 == 该 thunk 的 imm',
   all(COL[c]['mdisp']==t['imm'] for t in used for (c,i) in slothit[t['va']]),
   len({(COL[c]['mdisp'],t['imm']) for t in used for (c,i) in slothit[t['va']]}))

# 48 个未使用者：它们落在哪里？
print('\n## 48 个未被 vftable 引用的 thunk：')
rows=[]
for t in unused:
    rows.append('%08x %s imm=%d jmp=%08x'%(t['va'],t['kind'],t['imm'],t['jmp']))
print('\n'.join(rows))
print('imm 分布:', collections.Counter(t['imm'] for t in unused).most_common())
print('jmp 去重:', len({t['jmp'] for t in unused}), '个目标')
# 它们是否被直接 call（作为普通函数）？
calls=collections.defaultdict(list); jmps=collections.defaultdict(list)
i=0
while True:
    i=TB.find(b'\xe8',i)
    if i<0: break
    if i+5<=len(TB): calls[(BASE+i+5+s32(struct.unpack_from('<I',TB,i+1)[0]))&0xffffffff].append(BASE+i)
    i+=1
i=0
while True:
    i=TB.find(b'\xe9',i)
    if i<0: break
    if i+5<=len(TB): jmps[(BASE+i+5+s32(struct.unpack_from('<I',TB,i+1)[0]))&0xffffffff].append(BASE+i)
    i+=1
cnt=lambda t:len(calls.get(t['va'],[]))
print('48 个之中被直接 call 的:', sum(1 for t in unused if cnt(t)))
print('48 个之中被直接 jmp 的:', sum(1 for t in unused if jmps.get(t['va'])))
# 反控：21 个 slot0 thunk 被直接 call 的
print('22 个 used thunk 被直接 call 的:', sum(1 for t in used if cnt(t)))

# 0x4105e0 家族
t4105e0=[t for t in TH if t['va']==0x4105e0][0]
ck('14 0x4105e0 imm=4 jmp=0x410260', t4105e0['imm']==4 and t4105e0['jmp']==0x410260, t4105e0)
print('0x4105e0 承载 COL=%d 个，全部 mdisp=4' % len(slothit[t4105e0['va']]))
print('0x4105e0 = 0x4105e0 自身被直接 call/jmp: %d/%d'%(len(calls.get(0x4105e0,[])),len(jmps.get(0x4105e0,[]))))
print('jmp 目标 0x410260 被直接 call=%d / 直接 jmp=%d'%(len(calls.get(0x410260,[])),len(jmps.get(0x410260,[]))))
# 0x410260 完整反汇编（限于 400B 且 capstone 线性）
o=P.r2o(0x410260); ins=list(md.disasm(P.RAW[o:o+400],0x410260))
print('\n## 0x410260 反汇编（首 40 条）:')
for i in ins[:40]: print('   %08x %-20s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
# 三个 I 形态函数的直接调用
for fn in (0x41bc30,0x522a60,0x746100):
    print('I-form %08x: direct_call=%d %s ; direct_jmp=%d ; in_vftable_slots=%d'%(
        fn,len(calls.get(fn,[])),[hex(x) for x in calls.get(fn,[])[:6]],
        len(jmps.get(fn,[])), len(slothit.get(fn,[]))))
json.dump(dict(thunks=TH, slot0={hex(k):v for k,v in s0.items()},
               used=[[hex(t['va']),t['kind'],t['imm'],hex(t['jmp']),len(slothit[t['va']])] for t in used],
               unused=[[hex(t['va']),t['kind'],t['imm'],hex(t['jmp']),cnt(t)] for t in unused]),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q2.json','w'),indent=1)
print('\n== FAILS: %s (%d 断言) =='%(fails,NA))
