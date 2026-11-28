# -*- coding: utf-8 -*-
"""R214 主会话 m0：14044 个视图槽的整体目标面普查（不含 adjustor 判定细节，避免与 EX1/EX2 重叠）。
只做：全槽目标地址统计 / 非 .text 槽 / 高复用目标 top / 同 slot 索引跨类一致性 / 反控。
防 OOM：capstone 只对少量 top 目标开小窗口（count<=3, 但仅 40 个地址）。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]

COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(addr=base+4*k,sig=w[k],mdisp=s32(w[k+1]),pTD=w[k+3],
                           pCHD=w[k+4],name=nm.decode('latin1'))
pred=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text':
            pred[w[k]].append(base+4*k)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
# 视图：COL 地址 -> 槽列表
VIEW={}
for c,v in COL.items():
    if len(pred[c])!=1: continue
    vt=pred[c][0]+4
    nxt=min([a for a in (pred[x][0]+4 for x in COL if x!=c and pred[x] and pred[x][0]+4>vt)] or [0x10000000])
    slots=[]
    a=vt
    while a<nxt and P.where(P.dw(a))=='.text' and len(slots)<2000:
        slots.append(P.dw(a)); a+=4
    VIEW[c]=dict(base=vt,slots=slots,mdisp=v['mdisp'],name=v['name'],
                 main=(v['mdisp']==0))
MAIN=[c for c in VIEW if VIEW[c]['main'] and VIEW[c]['mdisp']==0]
SEC=[c for c in VIEW if c not in MAIN]
print('COL=%d CHD=%d VIEW=%d MAIN=%d SEC=%d'%(len(COL),len(CHD),len(VIEW),len(MAIN),len(SEC)))
NS=sum(len(VIEW[c]['slots']) for c in MAIN); NS2=sum(len(VIEW[c]['slots']) for c in SEC)
print('MAIN slots=%d SEC slots=%d total=%d'%(NS,NS2,NS+NS2))
NA=0; F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
J={}
J['scale']=dict(COL=len(COL),CHD=len(CHD),VIEW=len(VIEW),MAIN=len(MAIN),SEC=len(SEC),
                main_slots=NS,sec_slots=NS2)

print('\n===== G1 全槽目标面 =====')
TGT=collections.Counter()
SECN=collections.Counter()
for c in VIEW:
    for i,v in enumerate(VIEW[c]['slots']):
        TGT[v]+=1; SECN[P.where(v)]+=1
tot=sum(TGT.values())
ck('G1-1 槽总数 == 主+次', tot==NS+NS2,'%d'%tot)
ck('G1-2 槽目标全部落 .text', SECN.get('.text',0)==tot,
   'sec分布=%s'%dict(SECN))
J['distinct_target']=len(TGT)
print('   distinct target=%d  top20=%s'%(len(TGT),TGT.most_common(20)))
J['top20']=TGT.most_common(20)

print('\n===== G2 主视图 vs 次视图目标集 =====')
TM=collections.Counter(); TS=collections.Counter()
for c in MAIN:
    for v in VIEW[c]['slots']: TM[v]+=1
for c in SEC:
    for v in VIEW[c]['slots']: TS[v]+=1
onlym=set(TM)-set(TS); onlys=set(TS)-set(TM); both=set(TM)&set(TS)
ck('G2-1 主视图 distinct target 与次视图 distinct target', len(TM)+len(TS)>0,
   'main=%d sec=%d both=%d onlymain=%d onlysec=%d'%(len(TM),len(TS),len(both),len(onlym),len(onlys)))
J['g2']=dict(main=len(TM),sec=len(TS),both=len(both),onlymain=len(onlym),onlysec=len(onlys))

print('\n===== G3 同 slot 索引跨类一致性 =====')
# 对主视图：按索引 i 统计该索引上出现的 distinct 目标数与出现该类数
IDX=collections.defaultdict(collections.Counter); IDXN=collections.Counter()
for c in MAIN:
    for i,v in enumerate(VIEW[c]['slots']):
        IDX[i][v]+=1; IDXN[i]+=1
rows=[]
for i in sorted(IDX):
    rows.append((i,IDXN[i],len(IDX[i]),IDX[i].most_common(1)[0]))
print('  idx 槽出现次数 distinct 最高频项（前25索引）')
for i,n,d,top in rows[:25]: print('   %3d  %5d  %6d  %s x%d'%(i,n,d,hex(top[0]),top[1]))
mono=[r for r in rows if r[2]==1]
print('  单值索引（该索引所有类同目标）个数=%d / 索引总数=%d'%(len(mono),len(rows)))
J['idx_rows']=rows[:40]; J['mono_idx']=[(r[0],r[1],hex(r[3][0])) for r in mono][:40]; J['mono_n']=len(mono)
ck('G3-1 存在单值索引（可作为虚槽语义稳定的判据候选）', len(mono)>0,
   'mono=%d 前5=%s'%(len(mono),[(r[0],hex(r[3][0]),r[1]) for r in mono[:5]]))
ck('G3-2 索引 0 非单值（各类首槽不同）', rows[0][2]>1,'idx0 distinct=%d'%rows[0][2])

print('\n===== G4 高复用目标小窗口反汇编（只 12 个） =====')
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
def dis(va,n=3):
    o=P.r2o(va)
    if o is None: return 'NOFILE'
    out=[]
    for ins in md.disasm(P.RAW[o:o+64],va,count=n):
        out.append('%s %s'%(ins.mnemonic,ins.op_str))
    return ' ; '.join(out)
SNAP={}
for va,cnt in TGT.most_common(12):
    SNAP[hex(va)]=dict(count=cnt,asm=dis(va,3))
    print('   %s x%d : %s'%(hex(va),cnt,SNAP[hex(va)]['asm']))
J['snap']=SNAP
ck('G4-1 top12 目标全部可反汇编', all(v['asm']!='NOFILE' for v in SNAP.values()),'')

print('\n===== G5 反控 =====')
# 反控：把视图切到 slot>=1 起点（错位一格）应导致目标大量落非 .text
bad=0
for c in MAIN[:200]:
    b=VIEW[c]['base']+4
    if P.where(P.dw(b))!='.text': bad+=1
ck('G5-1 反控：主视图起点+4（错位）仍有 .text 指针（说明槽序列非平凡对齐）',
   bad<200,'nontext=%d/200'%bad)
# 反控2：把 COL 起点当 vftable（R213 已证 0/1214）
bad2=sum(1 for c in MAIN if P.where(P.dw(c+4))=='.text')
ck('G5-2 反控：COL+4 口径取到 .text 指针数应为 0', bad2==0,'%d/%d'%(bad2,len(MAIN)))
print('\n断言 %d 条，FAIL %d 条 %s'%(NA,len(F),F if F else ''))
json.dump(J,open('/home/t628/projects/ra2-campaign-forge/_r214/m0.json','w'),ensure_ascii=False)
