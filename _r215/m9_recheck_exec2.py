# -*- coding: utf-8 -*-
"""R215 m9：主会话独立复算 EX2 的 5 条结论（§2.12 规则 D）。
Q1 INoticeSink 视图数与槽；Q2 8 / 21784 的真实归属；Q3 全体 adjustor 的 IMM 中是否出现 8 / 21784；
Q4 0x7e2250/54/58 性质；Q5 三条 8B sub 桩地址与落点 + 律 X。
同时定位『305 vs 70』口径差（出现次数 vs distinct 桩地址）。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
NA=0;F=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c:F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
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
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def adj_at(a):
    o=P.r2o(a)
    if o is None: return None
    ins=list(md.disasm(raw[o:o+20],a,count=3))
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4]' not in i0.op_str or i1.mnemonic!='jmp': return None
    imm=None
    for op in i0.operands:
        if op.type==capstone.x86.X86_OP_IMM: imm=op.imm
    tgt=None
    for op in i1.operands:
        if op.type==capstone.x86.X86_OP_IMM: tgt=op.imm
    if imm is None or tgt is None: return None
    return (imm&0xffffffff,tgt&0xffffffff,len(i0.bytes),len(i1.bytes))
SEC=[v for v in VIEWS if v['mdisp']!=0]
ALL=[]      # (view, idx, stubaddr, imm, tgt, i0len)
for v in SEC:
    for i,x in enumerate(v['slots']):
        r=adj_at(x)
        if r: ALL.append((v,i,x)+r)
print('=== Q6 口径：adjustor 出现次数 vs distinct 桩地址 ===')
print('出现次数=%d distinct 桩地址=%d'%(len(ALL),len(set(a[2] for a in ALL))))
lens=collections.Counter(a[5] for a in ALL)
print('首指令长度分布:',dict(lens))
ck('Q6a 出现次数=305',len(ALL)==305,len(ALL))
ck('Q6b distinct 桩地址=70',len(set(a[2] for a in ALL))==70,len(set(a[2] for a in ALL)))
IMM=collections.Counter(a[3] for a in ALL)
print('IMM 取值种数=%d'%len(IMM))
ck('Q3 全体 305 条 adjustor 中 IMM==8 的条数',IMM.get(8,0)==0,IMM.get(8,0))
ck('Q3 全体 305 条 adjustor 中 IMM==21784 的条数',IMM.get(21784,0)==0,IMM.get(21784,0))
print('=== Q1 INoticeSink ===')
INS=[v for v in VIEWS if v['nm']=='?AVINoticeSink@@']
for v in INS: print('  0x%x mdisp=%d n=%d slots=%s'%(v['base'],v['mdisp'],len(v['slots']),[hex(x) for x in v['slots']]))
ck('Q1 INoticeSink 视图数=1 且 mdisp=0 且 1 槽 0x4c9150',
   len(INS)==1 and INS[0]['mdisp']==0 and len(INS[0]['slots'])==1 and INS[0]['slots'][0]==0x4c9150,
   len(INS))
print('=== Q2 mdisp 值 8 / 21784 的视图 ===')
m8=[v for v in VIEWS if v['mdisp']==8]; m21=[v for v in VIEWS if v['mdisp']==21784]
print('mdisp==8 视图数=%d 例:%s'%(len(m8),[(hex(v['base']),v['nm'],len(v['slots'])) for v in m8[:5]]))
print('mdisp==21784 视图数=%d 例:%s'%(len(m21),[(hex(v['base']),v['nm'],len(v['slots'])) for v in m21[:5]]))
ck('Q2 mdisp==8 视图数=78',len(m8)==78,len(m8))
ck('Q2 mdisp==21784 视图数=3',len(m21)==3,len(m21))
ck('Q2b 21784 三视图类名 = Mouse/Tab/Scroll',
   sorted(v['nm'] for v in m21)==sorted(['?AVMouseClass@@','?AVTabClass@@','?AVScrollClass@@']),
   sorted(v['nm'] for v in m21))
print('=== Q4/Q5 AircraftClass 视图与 0x7e2250 ===')
AC=[v for v in VIEWS if v['nm']=='?AVIAircraftClass@@']
AC2=[v for v in VIEWS if v['nm']=='?AVAircraftClass@@']
print('?AVIAircraftClass@@ 视图=%s'%[(hex(v['base']),v['mdisp'],len(v['slots'])) for v in AC])
print('?AVAircraftClass@@ 视图=%s'%[(hex(v['base']),v['mdisp'],len(v['slots'])) for v in AC2])
V=[v for v in AC2 if v['mdisp']==1728]
ck('Q4 ?AVAircraftClass@@ 有 mdisp=1728 单视图',len(V)==1,[ (hex(v['base']),len(v['slots'])) for v in AC2])
if V:
    v=V[0]
    print('1728 视图 起点=0x%x 槽数=%d slot0..5=%s'%(v['base'],len(v['slots']),[hex(x) for x in v['slots'][:6]]))
    ck('Q4b 该视图 slot0/1/2 地址 = 0x7e2250/54/58',
       [v['base']+4*i for i in range(3)]==[0x7e2250,0x7e2254,0x7e2258],
       [hex(v['base']+4*i) for i in range(3)])
    for i in range(3):
        a=v['slots'][i]; r=adj_at(a)
        print('  slot%d 桩=0x%x bytes=%s imm=%s tgt=%s i0len=%s'%(
            i,a,raw[P.r2o(a):P.r2o(a)+14].hex(),hex(r[0]) if r else '-',hex(r[1]) if r else '-',r[2] if r else '-'))
        if r:
            tgt=r[1]; owner=[(vv,vv['slots'].index(tgt)) for vv in VIEWS if tgt in vv['slots']]
            print('     tgt owner=%s'%[(hex(o['base']),o['nm'],o['mdisp'],k) for o,k in owner])
            print('     律X imm==mdisp_self-mdisp_target: %s'%(
                all(r[0]==v['mdisp']-o['mdisp'] for o,k in owner)))
    # 0x7e2250 是否出现在任何视图槽序列
    inT=[(vv['base'],vv['nm'],i) for vv in VIEWS for i,x in enumerate(vv['slots']) if x in (0x7e2250,0x7e2254,0x7e2258)]
    ck('Q4c 0x7e2250/54/58 不作为任何视图槽值',len(inT)==0,len(inT))
    print('  .rdata 内容 @0x7e2250.. :',[hex(P.dw(0x7e2250+4*i)) for i in range(6)])
print('ASSERT=%d FAIL=%d %s'%(NA,len(F),F))
json.dump({'fail':F,'n':NA,'adj_occ':len(ALL),'adj_distinct':len(set(a[2] for a in ALL)),
 'lens':dict(lens),'imm8':IMM.get(8,0),'imm21784':IMM.get(21784,0),
 'm8':len(m8),'m21784':len(m21),'ins':[(hex(v['base']),v['mdisp'],len(v['slots'])) for v in INS],
 'ac':[(hex(v['base']),v['mdisp'],len(v['slots'])) for v in AC2]},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m9.json','w'),indent=1)
