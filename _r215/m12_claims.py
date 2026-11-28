# -*- coding: utf-8 -*-
"""R215 m12：主会话自核（供与审计 #557 逐条对照）。覆盖 AUD1 的 10 条 + 反控。"""
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
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def show(a,k=10):
    o=P.r2o(a)
    return [(x.address,x.bytes.hex(),x.mnemonic,x.op_str) for x in md.disasm(raw[o:o+64],a,count=k)]
print('=== 反控：槽号阈值扫描 ===')
for N in (17,18,19,20,21):
    h=[v for v in VIEWS if len(v['slots'])>N]
    c=collections.Counter(v['slots'][N] for v in h)
    multi=[t for t,n in c.items() if n>=2]
    print('slot%2d 视图=%3d distinct=%2d 多类目标=%2d(覆盖 %d 视图) 单类目标=%2d'%(
        N,len(h),len(c),len(multi),sum(c[t] for t in multi),sum(1 for t in c if c[t]==1)))
h18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in h18)
multi=[t for t,n in c18.items() if n>=2]
ck('1 137 = 多类覆盖 %d + 单类 %d'%(sum(c18[t] for t in multi),sum(1 for t in c18 if c18[t]==1)),
   sum(c18[t] for t in multi)+sum(1 for t in c18 if c18[t]==1)==137)
print('   多类组:',[(hex(t),c18[t]) for t in sorted(multi,key=lambda x:-c18[x])])
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1
ck('2 0x4104c0 仅出现在 slot18',set(POS[0x4104c0])=={18},dict(POS[0x4104c0]))
ck('2b 0x4104c0 出现次数=56',sum(POS[0x4104c0].values())==56,sum(POS[0x4104c0].values()))
ab=[v for v in VIEWS if v['nm']=='?AVAbstractClass@@' and v['mdisp']==0]
ck('3 AbstractClass 主视图 slot18=0x4104c0',len(ab)==1 and len(ab[0]['slots'])>18 and ab[0]['slots'][18]==0x4104c0,
   (hex(ab[0]['base']),len(ab[0]['slots'])) if ab else None)
print('  0x4104c0 前 10 条:')
for x in show(0x4104c0,10): print('    %08x %-18s %s %s'%x)
V=[P.dw(0x887680+4*i) for i in range(3)]
print('  全局 0x887680/84/88 =',[None if x is None else hex(x) for x in V],
      '段=',[P.where(0x887680+4*i) for i in range(3)],
      '（None = virt-only BSS，须 win-main 动态取证）')
for A in (0x4104f0,0x410540):
    ins=show(A,16)
    hit=[x for x in ins if x[2]=='call' and '0x48]' in x[3]]
    ck('4 0x%x 含 call dword [eax+0x48]'%A,len(hit)==1,hit)
ck('4b 0x4104f0 出现73 且仅 slot19',sum(POS[0x4104f0].values())==73 and set(POS[0x4104f0])=={19},
   (sum(POS[0x4104f0].values()),dict(POS[0x4104f0])))
ck('4c 0x410540 出现77 且仅 slot22',sum(POS[0x410540].values())==77 and set(POS[0x410540])=={22},
   (sum(POS[0x410540].values()),dict(POS[0x410540])))
t=P.B['.text'];tb=t['lo'];n=t['rawsize'];o0=t['rawptr']
call=[];jmp=[];sib=[]
i=o0;end=o0+n-4
while i<end:
    if raw[i]==0xff:
        m=raw[i+1];mod=m>>6;reg=(m>>3)&7;rm=m&7
        if mod==1:
            if rm==4:
                if raw[i+3]==0x48 and reg in (2,4): sib.append((tb+(i-o0),reg,raw[i+2]))
            elif raw[i+2]==0x48:
                if reg==2: call.append(tb+(i-o0))
                elif reg==4: jmp.append(tb+(i-o0))
    i+=1
print('5 byte 口径: call=%d jmp=%d SIB=%d 合计=%d'%(len(call),len(jmp),len(sib),len(call)+len(jmp)+len(sib)))
ck('5 call 非SIB=928',len(call)==928,len(call))
ck('5b jmp 非SIB=2',len(jmp)==2,len(jmp))
ck('5c SIB=1 且为 call [esp+0x48]',len(sib)==1 and sib[0][1]==2,sib)
CH=0x10000
def lite(skip):
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    if skip: m.skipdata=True
    hits=0;cov=0;tot=0;trunc=0
    for base in range(o0,o0+n,CH):
        chunk=raw[base:min(base+CH,o0+n)]
        va=tb+(base-o0);last=0
        for a,sz,mn,op in m.disasm_lite(chunk,va):
            last=(a-va)+sz
            if mn in ('call','jmp') and op.endswith('+ 0x48]') and ',' not in op.split('[')[0]: hits+=1
        cov+=last;tot+=len(chunk)
        if last<len(chunk): trunc+=1
    return hits,cov/tot,trunc
h1,c1,t1=lite(True);h0,c0,t0=lite(False)
print('6 skipdata hits=%d cover=%.4f | no-skip hits=%d cover=%.4f 截断块=%d'%(h1,c1,h0,c0,t0))
ck('6 skipdata hits=931 覆盖100%',h1==931 and abs(c1-1.0)<1e-9,(h1,c1))
ck('6b no-skip=765 且截断块=53',h0==765 and t0==53,(h0,t0))
for nm in ('?AVLocomotionClass@@','?AVDriveLocomotionClass@@','?AVFlyLocomotionClass@@'):
    g=sorted([v for v in VIEWS if v['nm']==nm],key=lambda v:v['base'])
    print('7 %-32s'%nm,[(hex(v['base']),v['mdisp'],len(v['slots']),hex(v['slots'][18]) if len(v['slots'])>18 else '-') for v in g])
loco=[v for v in VIEWS if v['nm'].endswith('LocomotionClass@@') and not v['nm'].startswith('?AV?$') and v['mdisp']==4]
mm=min(len(v['slots']) for v in loco)
same=[i for i in range(mm) if len(set(v['slots'][i] for v in loco))==1]
print('8 12 视图共同槽=%d 全同槽=%s'%(mm,same))
ck('8 视图=12 共同槽=50 全同仅[21,22]',len(loco)==12 and mm==50 and same==[21,22],(len(loco),mm,same))
INS=[v for v in VIEWS if v['nm']=='?AVINoticeSink@@']
ck('9 INoticeSink 单视图 mdisp0 1槽 0x4c9150',
   len(INS)==1 and INS[0]['mdisp']==0 and INS[0]['slots']==[0x4c9150],
   [(hex(v['base']),v['mdisp'],len(v['slots'])) for v in INS])
ck('9b mdisp==8 视图=78',sum(1 for v in VIEWS if v['mdisp']==8)==78,sum(1 for v in VIEWS if v['mdisp']==8))
m21=[v for v in VIEWS if v['mdisp']==21784]
ck('9c mdisp==21784 视图=3 Mouse/Tab/Scroll',
   len(m21)==3 and sorted(v['nm'] for v in m21)==sorted(['?AVMouseClass@@','?AVTabClass@@','?AVScrollClass@@']),
   [v['nm'] for v in m21])
# 反控：disp8 邻值
for D in (0x44,0x47,0x48,0x49,0x4c):
    cnt=0;i=o0
    while i<end:
        if raw[i]==0xff:
            m=raw[i+1];mod=m>>6;reg=(m>>3)&7;rm=m&7
            if mod==1 and rm!=4 and raw[i+2]==D and reg in (2,4): cnt+=1
        i+=1
    print('反控 disp8=0x%02x 的 FF /2|/4 数=%d'%(D,cnt))
# 反控：同类 mdisp=0 主视图是否有 slot18
cnt=0;names=[]
for v in VIEWS:
    if v['mdisp']==0 and len(v['slots'])>18:
        cnt+=1
print('反控 主视图(mdisp=0) 中槽数>18 的视图数=%d（这些也有 slot18）'%cnt)
print('ASSERT=%d FAIL=%d %s'%(NA,len(F),F))
json.dump({'fail':F,'n':NA,'c18':{('0x%08x'%k):v for k,v in c18.most_common()},
 'call':len(call),'jmp':len(jmp),'sib':len(sib),'skip_hits':h1,'noskip_hits':h0,'trunc':t0,
 'loco_same':same},open('/home/t628/projects/ra2-campaign-forge/_r215/m12.json','w'),indent=1)
