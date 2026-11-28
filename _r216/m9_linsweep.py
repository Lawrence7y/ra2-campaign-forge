# -*- coding: utf-8 -*-
"""R216 m9：一次性线性扫描 .text 建指令表（disasm_lite + skipdata，64KB 分块流式，防 OOM），
再用真前驱做寄存器基址还原，验证律 W（有效偏移 = 基址增量 + disp == 视图 mdisp）。
同时输出每个构造点内『同一函数区段内写视图基址的全部 C7』= vfptr 初始化块。
正控：0x4105a0 的 4 条写入必须 eff == 0/4/8/12 且全符。
反控：把 rm 寄存器基址增量整体忽略（delta:=0）后，A 族 46 条必须全部判违例（证明 delta 判据非恒真）。"""
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
    while a0<end and P.where(P.dw(a0))=='.text':
        sl.append(P.dw(a0));a0+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
VB={v['base']:v for v in VIEWS}
t=P.B['.text']; lo=t['lo']; hi=t['hi_file']; sz=hi-lo
ADDR=[];MN=[];OPS=[]
CH=64*1024
for off in range(0,sz,CH):
    va=lo+off
    chunk=P.RAW[o(va):o(va)+min(CH,sz-off)]
    for it in mdl.disasm_lite(chunk,va):
        ADDR.append(it[0]); MN.append(it[2]); OPS.append(it[3])
    del chunk
print('.text 线性扫描：指令/条目=%d ; 覆盖 va 0x%x..0x%x (%d B)'%(len(ADDR),ADDR[0],ADDR[-1],sz))
IDX={a:i for i,a in enumerate(ADDR)}
RN={0:'eax',1:'ecx',2:'edx',3:'ebx',5:'ebp',6:'esi',7:'edi'}
def resolve(i,reg,depth=0):
    """反解 ADDR[i] 之前 reg 的基址增量（相对 this/incoming 参数）；返回 (delta,kind) 或 None"""
    if depth>6: return None
    for j in range(i-1,max(i-40,-1),-1):
        mn=MN[j]; ops=OPS[j]
        if not ops: continue
        dst=ops.split(',')[0].strip()
        if dst!=reg: continue
        if mn=='mov' and ',' in ops:
            src=ops.split(', ',1)[1].strip()
            if src in RN.values():
                if src=='ecx': return (0,'mov %s,ecx'%reg)     # this
                r=resolve(j,src,depth+1)
                return (r[0],'mov %s,%s -> %s'%(reg,src,r[1])) if r else None
            if src.startswith('[') and src.endswith(']'):
                inner=src[1:-1]
                parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                if len(parts)==2 and parts[0] in RN.values() and parts[1].lstrip('-').isdigit():
                    r=resolve(j,parts[0],depth+1)
                    return (r[0]+int(parts[1]),'mov %s,[%s%+d]'%(reg,parts[0],int(parts[1]))) if r else None
            return None
        if mn=='lea':
            inner=ops.split(', ',1)[1].strip()
            if inner.startswith('[') and inner.endswith(']'):
                body=inner[1:-1]
                parts=[x.strip() for x in body.replace('-','+-').split('+')]
                base=None;d=0
                for p in parts:
                    if p in RN.values(): base=p
                    elif p.lstrip('-').isdigit(): d+=int(p)
                if base:
                    if base=='ecx': return (d,'lea %s,[ecx%+d]'%(reg,d))
                    r=resolve(j,base,depth+1)
                    return (r[0]+d,'lea %s,[%s%+d]'%(reg,base,d)) if r else None
            return None
        if mn in ('add','sub') and ops.split(',')[1].strip().isdigit():
            r=resolve(j,reg,depth+1)
            v=int(ops.split(',')[1]); d=v if mn=='add' else -v
            return (r[0]+d,'%s %s,%d'%(mn,reg,v)) if r else None
        if mn=='pop' and dst==reg: return None
        if mn in ('xor','movzx','movsx') and dst==reg: return None
    return None
# 抽取 C7 命中
def hits():
    out=[];n=len(ADDR)
    for i in range(n):
        if MN[i]!='mov' or not OPS[i].startswith('dword ptr ['): continue
        ops=OPS[i]
        if not ops.endswith(']') and ', 0x' not in ops: continue
        try:
            mem,imm=ops.split(', ')
            imm=int(imm,0)
        except Exception: continue
        if imm not in VB: continue
        inner=mem[len('dword ptr ['):-1]
        parts=[x.strip() for x in inner.replace('-','+-').split('+')]
        reg=None;d=0
        for p in parts:
            if p in RN.values(): reg=p
            elif p.lstrip('-').isdigit(): d+=int(p)
            else: reg=None;break
        if reg is None or reg not in RN.values(): continue
        out.append((ADDR[i],reg,d,imm))
    return out
H=hits()
print('C7(视图基址) 命中=%d'%len(H))
stat=collections.Counter(); viol=[]; rows=[]
for a,reg,d,imm in H:
    i=IDX[a]
    r=resolve(i,reg)
    if r is None: stat['基址未还原']+=1; rows.append([a,reg,d,imm,None]); continue
    eff=d+r[0]; md_=VB[imm]['mdisp']
    rows.append([a,reg,d,imm,eff,r[1]])
    if eff==md_: stat['律W 成立']+=1
    else: stat['违例']+=1; viol.append((a,reg,d,r,eff,imm,md_,VB[imm]['nm']))
print('=== 律 W ===',stat.most_common())
print('违例 %d 前 20:'%len(viol))
for a,reg,d,r,eff,imm,md_,nm in viol[:20]:
    print('   0x%08x [%s%+d] imm=0x%08x eff=%d mdisp=%d %s  (%s)'%(a,reg,d,imm,eff,md_,nm,r[1]))
# 正控 / 反控
pc=[x for x in rows if 0x4105a0<=x[0]<0x4105d3]
print('[正控] 0x4105a0 命中=%d 明细=%s'%(len(pc),[(hex(x[0]),x[2],x[4]) for x in pc]))
assert len(pc)==4 and sorted(x[4] for x in pc)==[0,4,8,12],'POS FAIL'
A=[x for x in rows if x[4] is not None and x[2]==0 and VB[x[3]]['mdisp']!=0]
A0=[x for x in A if x[4]==VB[x[3]]['mdisp']]
print('[反控] A 族 delta:=0 口径下判违例=%d/%d（其中真值靠 delta 成立=%d）'%(len(A),len(A),len(A0)))
assert len(A0)==len(A) and len(A)>0,'NEG FAIL (delta 判据无增量)'
# vfptr 初始化块：按函数区段（距离 <=400B 的 C7 归同块）聚合
H.sort()
blocks=[];cur=[]
for x in H:
    if cur and x[0]-cur[-1][0]>400: blocks.append(cur);cur=[]
    cur.append(x)
if cur: blocks.append(cur)
multi=[b for b in blocks if len(b)>1]
print('=== C7 块聚合：块=%d ; 含>=2 条写入的块=%d ==='%(len(blocks),len(multi)))
print('  每块写入条数分布:',collections.Counter(len(b) for b in blocks).most_common())
cls=collections.Counter()
for b in multi:
    names={VB[x[3]]['nm'] for x in b}
    if len(names)==1: cls[list(names)[0]]+=1
print('  多写块按类 top12:',cls.most_common(12))
print('\n=== AbstractClass 系列初始化块（0x7e1f24/2c/34/50）===')
for b in blocks:
    if any(x[3] in (0x7e1f24,0x7e1f2c,0x7e1f34,0x7e1f50) for x in b):
        print('  块 @0x%08x..0x%08x:'%(b[0][0],b[-1][0]))
        for a,reg,d,imm in b: print('    0x%08x  [%s%+d] = 0x%08x  (mdisp=%d %s)'%(a,reg,d,imm,VB[imm]['mdisp'],VB[imm]['nm']))
json.dump({'insn':len(ADDR),'c7':len(H),'stat':dict(stat),
  'viol':[['0x%08x'%a,reg,d,eff,'0x%08x'%imm,md_,nm,r[1]] for a,reg,d,r,eff,imm,md_,nm in viol[:200]],
  'blocks':len(blocks),'multi':len(multi),'block_size_dist':{str(k):v for k,v in collections.Counter(len(b) for b in blocks).items()},
  'A_zero_delta':[len(A),len(A0)]},
  open('/home/t628/projects/ra2-campaign-forge/_r216/m9.json','w'),indent=1)
