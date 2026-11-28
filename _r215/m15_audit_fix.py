# -*- coding: utf-8 -*-
"""R215 m15：复算审计 #557 的 3 条订正（§2.12 规则 D）。
C1 『305』双重含义：adjustor 出现次数 vs call [eax+0x48] 站点数，两者同为 305 —— 核实是否为巧合。
C2 Locomotion 组 = 11 派生 + 基类（非 12 派生）；Teleport 主视图 12 槽非 10。
C3 0x887680/684/688 落 virt-only（无文件字节）。
C4 桩形态拆分：imm8 (83 6c 24 04) 67 个 + imm32 (81 6c 24 04) 3 个 = 70 distinct。
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
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def adj_at(a):
    o=P.r2o(a)
    if o is None: return None
    ins=list(md.disasm(raw[o:o+24],a,count=3))
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4]' not in i0.op_str or not i1.mnemonic.startswith('jmp'): return None
    imm=None
    for op in i0.operands:
        if op.type==capstone.x86.X86_OP_IMM: imm=op.imm
    tgt=None
    for op in i1.operands:
        if op.type==capstone.x86.X86_OP_IMM: tgt=op.imm
    if imm is None or tgt is None: return None
    return (imm&0xffffffff,tgt&0xffffffff,len(i0.bytes),i0.bytes.hex())
SEC=[v for v in VIEWS if v['mdisp']!=0]
ALL=[(v,i,x)+adj_at(x) for v in SEC for i,x in enumerate(v['slots']) if adj_at(x)]
stubs={}
for v,i,x,imm,tgt,l0,b0 in ALL: stubs[x]=(imm,tgt,l0,b0)
print('=== C4 桩形态拆分 ===')
print('adjustor 出现次数=%d distinct 桩=%d'%(len(ALL),len(stubs)))
byL=collections.Counter(s[2] for s in stubs.values())
byI8=collections.Counter(s[0] for s in stubs.values() if s[2]==5)
byI32=collections.Counter(s[0] for s in stubs.values() if s[2]==8)
print('首指令长度分布:',dict(byL))
print('imm8(83 6c 24 04) IMM 分布:',{hex(k):v for k,v in sorted(byI8.items())},'合计',sum(byI8.values()))
print('imm32(81 6c 24 04) IMM 分布:',{hex(k):v for k,v in sorted(byI32.items())},'合计',sum(byI32.values()))
ck('C4a imm8 桩=67 imm32 桩=3 合计=70',sum(byI8.values())==67 and sum(byI32.values())==3 and len(stubs)==70,
   (sum(byI8.values()),sum(byI32.values()),len(stubs)))
ck('C4b imm32 三条 IMM 全 0x6c0',set(byI32)=={0x6c0},[hex(k) for k in byI32])
ck('C4c 全部 70 桩的 IMM 不含 8 / 21784',8 not in set(s[0] for s in stubs.values()) and 21784 not in set(s[0] for s in stubs.values()))
print('  桩字节前缀样例 imm8:',list(x for x in stubs.values() if x[2]==5)[0][3])
print('  桩字节前缀样例 imm32:',list(x for x in stubs.values() if x[2]==8)[0][3])
print('=== C1 『305』双重含义 ===')
# call [eax+0x48] 站点数（字节口径）
t=P.B['.text'];tb=t['lo'];n=t['rawsize'];o0=t['rawptr']
ea=0;i=o0;end=o0+n-4
while i<end:
    if raw[i]==0xff:
        m=raw[i+1]
        if (m>>6)==1 and ((m>>3)&7)==2 and (m&7)==0 and raw[i+2]==0x48: ea+=1
    i+=1
print('call [eax+0x48] 字节口径站点数=%d ; adjustor 出现次数=%d'%(ea,len(ALL)))
ck('C1 两者数值同为 305 属实（巧合，非同一口径）',ea==305 and len(ALL)==305,(ea,len(ALL)))

# 站点地址集合
st=[];i=o0
while i<end:
    if raw[i]==0xff:
        m=raw[i+1]
        if (m>>6)==1 and ((m>>3)&7)==2 and (m&7)==0 and raw[i+2]==0x48: st.append(tb+(i-o0))
    i+=1
ck('C1c 桩地址 ∩ call[eax+0x48]站点 = 空',len(set(stubs)&set(st))==0,len(set(stubs)&set(st)))
print('=== C2 Locomotion 组 ===')
loco=sorted([v for v in VIEWS if v['nm'].endswith('LocomotionClass@@') and not v['nm'].startswith('?AV?$') and v['mdisp']==4],key=lambda v:v['nm'])
print('mdisp=4 的 50 槽 loco 视图数=%d'%len(loco))
for v in loco: print('  %-32s 主视图槽数=%d slot18=%s'%(v['nm'],
    len([x for x in VIEWS if x['nm']==v['nm'] and x['mdisp']==0][0]['slots']),hex(v['slots'][18])))
ck('C2a 组内 12 个 = 11 派生 + 基类 ?AVLocomotionClass@@',len(loco)==12 and any(v['nm']=='?AVLocomotionClass@@' for v in loco))
tp=[v for v in VIEWS if v['nm']=='?AVTeleportLocomotionClass@@' and v['mdisp']==0]
ck('C2b Teleport 主视图 12 槽（非 10）',len(tp)==1 and len(tp[0]['slots'])==12,len(tp[0]['slots']) if tp else None)
print('=== C3 三全局 ===')
for g in (0x887680,0x887684,0x887688):
    print('  0x%x 段=%s r2o=%s'%(g,P.where(g),P.r2o(g)))
ck('C3 三全局全落 virt-only（无文件字节）',all(P.where(0x887680+4*i)=='virt-only' for i in range(3)))
print('ASSERT=%d FAIL=%d %s'%(NA,len(F),F))
json.dump({'fail':F,'n':NA,'occ':len(ALL),'stubs':len(stubs),'imm8':sum(byI8.values()),
 'imm32':sum(byI32.values()),'imm8_dist':{hex(k):v for k,v in byI8.items()},
 'ea_sites':ea,'loco':[v['nm'] for v in loco],
 'tp_slots':len(tp[0]['slots']) if tp else None},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m15.json','w'),indent=1)
