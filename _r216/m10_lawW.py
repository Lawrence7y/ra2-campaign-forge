# -*- coding: utf-8 -*-
"""R216 m10（m9 修正版）：律 W + 律 W2。
m9 自错订正：m9 用 ops 文本解析 disp 时用 p.lstrip('-').isdigit()，对 capstone 的十六进制形式
'0xc'/'0x88' 返回 False ⇒ 0x4105bd 那条被丢弃，正控 3/4 FAIL。改为 int(p,0) 尝试。
律 W ： eff = d + delta(reg) ，比较 eff 与视图 mdisp。
律 W2： 对 eff != mdisp 者，同一 (视图, 上下文) 内 eff - mdisp 是否为常数（宿主内嵌偏移假说）。
防 OOM：64KB 分块 disasm_lite + skipdata，一次性建表后释放 chunk。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.skipdata=True
def o(va): return P.r2o(va)
def s32(v): return struct.unpack('<i',v)[0] if isinstance(v,(bytes,bytearray)) else struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];nn=s['rawsize']//4
    return struct.unpack_from('<%dI'%nn,P.RAW,s['rawptr']),s['lo']
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
    sl=[];a0=st
    while a0<end and P.where(P.dw(a0))=='.text': sl.append(P.dw(a0));a0+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
VB={v['base']:v for v in VIEWS}
t=P.B['.text']; lo=t['lo']; sz=t['hi_file']-lo
ADDR=[];MN=[];OPS=[]
CH=64*1024
for off in range(0,sz,CH):
    va=lo+off; chunk=P.RAW[o(va):o(va)+min(CH,sz-off)]
    for it in mdl.disasm_lite(chunk,va):
        ADDR.append(it[0]);MN.append(it[2]);OPS.append(it[3])
    del chunk
IDX={a:i for i,a in enumerate(ADDR)}
print('.text 指令条目=%d'%len(ADDR))
RN={0:'eax',1:'ecx',2:'edx',3:'ebx',5:'ebp',6:'esi',7:'edi'}
def P_(p):
    try: return int(p,0)
    except Exception: return None
def memparse(inner):
    parts=[x.strip() for x in inner.replace('-','+-').split('+')]
    reg=None;d=0
    for p in parts:
        if p in RN.values():
            if reg is not None: return None
            reg=p
        else:
            v=P_(p)
            if v is None: return None
            d+=v
    return (reg,d)
WINDOW=64
def resolve(i,reg,depth=0):
    if depth>6: return None
    for j in range(i-1,max(i-WINDOW,-1),-1):
        mn=MN[j]; ops=OPS[j]
        if not ops or ',' not in ops: continue
        dst,src=ops.split(', ',1)
        dst=dst.strip(); src=src.strip()
        if dst!=reg: continue
        if mn=='mov':
            if src in RN.values():
                if src=='ecx': return (0,'this')
                r=resolve(j,src,depth+1); return (r[0],'mov %s,%s|%s'%(reg,src,r[1])) if r else None
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'mov %s,[ecx%+d]'%(reg,mp[1]))
                    r=resolve(j,mp[0],depth+1); return (r[0]+mp[1],'mov %s,[%s%+d]|%s'%(reg,mp[0],mp[1],r[1])) if r else None
                if mp and mp[0] is None and 'esp' in src: return (mp[1],'arg[esp%+d]'%mp[1])
            return None
        if mn=='lea':
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'lea %s,[ecx%+d]'%(reg,mp[1]))
                    r=resolve(j,mp[0],depth+1); return (r[0]+mp[1],'lea %s,[%s%+d]|%s'%(reg,mp[0],mp[1],r[1])) if r else None
            return None
        if mn in ('add','sub') and src.isdigit():
            r=resolve(j,reg,depth+1); v=int(src)
            return (r[0]+(v if mn=='add' else -v),'%s %s,%d|%s'%(mn,reg,v,r[1])) if r else None
        if mn=='pop': return None
        if mn in ('xor','movzx','movsx'): return None
    return None
H=[]
for i in range(len(ADDR)):
    if MN[i]!='mov' or not OPS[i].startswith('dword ptr ['): continue
    ops=OPS[i]
    if ', ' not in ops: continue
    mem,imm=ops.split(', ',1)
    iv=P_(imm)
    if iv is None or iv not in VB: continue
    mp=memparse(mem[len('dword ptr ['):-1])
    if not mp or not mp[0]: continue
    H.append((ADDR[i],mp[0],mp[1],iv,i))
print('C7(视图基址) 命中=%d'%len(H))
stat=collections.Counter(); viol=[]; rows=[]; unreason=collections.Counter()
for a,reg,d,imm,i in H:
    r=resolve(i,reg)
    if r is None or r[1].startswith('arg['):
        stat['基址入参/未还原']+=1
        unreason[('arg' if r and r[1].startswith('arg[') else 'unknown')]+=1
        rows.append([a,reg,d,imm,None,r[1] if r else None]); continue
    eff=d+r[0]; md_=VB[imm]['mdisp']
    rows.append([a,reg,d,imm,eff,r[1]])
    if eff==md_: stat['律W 成立']+=1
    else:
        stat['律W 违例']+=1; viol.append((a,reg,d,eff,imm,md_,VB[imm]['nm'],r[1]))
print('=== 律 W ===',stat.most_common())
print('未还原原因:',unreason.most_common())
pc=[x for x in rows if 0x4105a0<=x[0]<0x4105d3]
print('[正控] 0x4105a0 命中=%d 明细=%s'%(len(pc),[(hex(x[0]),x[2],x[4],x[5]) for x in pc]))
assert len(pc)==4 and sorted(x[4] for x in pc)==[0,4,8,12],'POS FAIL'
A=[x for x in rows if x[4] is not None and x[2]==0 and VB[x[3]]['mdisp']!=0]
A0=[x for x in A if x[4]==VB[x[3]]['mdisp']]
print('[反控] A 族(off=0 且 mdisp!=0) 共 %d 条 ; 忽略 delta 时全部判违例，靠 delta 成立 %d 条'%(len(A),len(A0)))
assert len(A0)==len(A) and len(A)>0,'NEG FAIL'
print('\n=== 律 W 违例 %d 条明细（前 25）==='%len(viol))
for a,reg,d,eff,imm,md_,nm,why in viol[:25]:
    print('   0x%08x [%s%+d] eff=%-6d mdisp=%-6d eff-mdisp=%+d  %-46s (%s)'%(a,reg,d,eff,md_,eff-md_,nm,why))
v2=collections.Counter((nm,eff-md_) for a,reg,d,eff,imm,md_,nm,why in viol)
print('\n=== 律 W2：(类, eff-mdisp) 聚合 ===')
for (nm,dd),c in v2.most_common(20): print('   %+5d  %-46s x%d'%(dd,nm,c))
json.dump({'insn':len(ADDR),'c7':len(H),'stat':dict(stat),'unreason':dict(unreason),
 'viol':[['0x%08x'%a,reg,d,eff,'0x%08x'%imm,md_,nm,eff-md_,why] for a,reg,d,eff,imm,md_,nm,why in viol],
 'w2':[[nm,dd,c] for (nm,dd),c in v2.most_common(60)],
 'pos':[(hex(x[0]),x[2],x[4]) for x in pc],'A':[len(A),len(A0)]},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m10.json','w'),indent=1)
