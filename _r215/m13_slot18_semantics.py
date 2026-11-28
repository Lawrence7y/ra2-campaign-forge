# -*- coding: utf-8 -*-
"""R215 m13：slot18 落点的『12 字节描述符』假设检验。
H: slot18 的函数体把 3 个 dword 写到 [esp+4] 传入的指针（12 字节描述符）；
   配套证据是 slot19 的默认桩 0x4104f0 会 vcall [eax+0x48] 并把返回的 3 个 dword 拷给它的出参。
测法：对每个落点，capstone 顺序反汇编到首个 ret 为止，统计对 [reg] / [reg+4] / [reg+8] 的 dword 写次数
      以及是否出现 vcall [reg+0x48]。
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
h18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in h18)
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def body(a,limit=40):
    o=P.r2o(a); out=[]
    for x in md.disasm(raw[o:o+400],a):
        out.append(x)
        if x.mnemonic=='ret' or x.mnemonic.startswith('ret'): break
        if len(out)>=limit: break
    return out
print('=== 每个落点（按视图数降序）：体长 / dword 写次数 / 写的目标偏移 / vcall+0x48 / 返回值 ===')
RES={}
for T,n in c18.most_common():
    ins=body(T)
    stores=[]; vc48=0; retval=None; mn=[]
    for x in ins:
        mn.append(x.mnemonic)
        if x.mnemonic=='mov' and len(x.operands)==2:
            d,s=x.operands
            if d.type==capstone.x86.X86_OP_MEM and s.type==capstone.x86.X86_OP_REG and d.size==4:
                stores.append((d.mem.base and md.reg_name(d.mem.base), d.mem.disp))
        if x.mnemonic=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_MEM:
            if x.operands[0].mem.disp==0x48: vc48+=1
        if x.mnemonic in ('ret',): retval='ret'
    disp=sorted(set(d for _,d in stores))
    ok12 = len(stores)>=3 and disp[:3]==[0,4,8]
    RES['0x%08x'%T]=dict(n=n,ilen=len(ins),stores=len(stores),disps=disp,vc48=vc48,ok12=ok12,
        bytes=ins[0].bytes.hex() if ins else '', mn=mn[:12])
    print('0x%08x 视图%2d 体长%2d dword写=%d 偏移=%s 12B描述符=%s vcall48=%d 首字节=%s'%(
        T,n,len(ins),len(stores),disp,ok12,vc48,ins[0].bytes.hex() if ins else ''))
tot12=sum(1 for k,v in RES.items() if v['ok12'])
print('落点中符合『写 3 个 dword 偏移 0/4/8』的=%d/27'%tot12)
print('=== slot19 默认桩 0x4104f0 的完整体（3 个 dword 拷贝来源） ===')
for x in body(0x4104f0,30):
    print('   %08x %-16s %s %s'%(x.address,x.bytes.hex(),x.mnemonic,x.op_str))
print('=== slot20/21/22 默认桩体（0x410520 / 0x410530 / 0x410540） ===')
for A in (0x410520,0x410530,0x410540):
    print('-- 0x%x'%A)
    for x in body(A,20): print('   %08x %-16s %s %s'%(x.address,x.bytes.hex(),x.mnemonic,x.op_str))
json.dump(RES,open('/home/t628/projects/ra2-campaign-forge/_r215/m13.json','w'),indent=1)
