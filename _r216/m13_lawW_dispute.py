# -*- coding: utf-8 -*-
"""R216 m13：仲裁律 W 的基数分歧（主会话 2911/2551/360 vs 审计员 2560/2021/539）。
判据：双方都用 capstone 反汇编；差别只能来自 ①解析口径（文本正则 vs 结构化 op_str）②delta 反解窗口。
做法：同一份指令表上跑 4 种 delta 反解变体，报告每种变体的 (sol,eq,ne,neg,minpos)，
并用『同一视图同一构造块内、多条写入的 delta 是否一致』做外部一致性校验（不依赖任何一方实现）。"""
import sys,struct,json,collections,re
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
ADDR=[];MN=[];OPS=[];BYT=[]
CH=64*1024
for off in range(0,sz,CH):
    va=lo+off; c=P.RAW[o(va):o(va)+min(CH,sz-off)]
    for it in mdl.disasm_lite(c,va):
        ADDR.append(it[0]);MN.append(it[2]);OPS.append(it[3])
    del c
I={a:k for k,a in enumerate(ADDR)}
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
# 命中集（与 m10 同口径，独立重写）
H=[]
for k in range(len(ADDR)):
    if MN[k]!='mov' or not OPS[k].startswith('dword ptr [') or ', ' not in OPS[k]: continue
    mem,imm=OPS[k].split(', ',1); iv=P_(imm)
    if iv is None or iv not in VB: continue
    mp=memparse(mem[len('dword ptr ['):-1])
    if not mp or not mp[0]: continue
    H.append((ADDR[k],mp[0],mp[1],iv,k))
print('命中=%d'%len(H))
def resolve(i,reg,WIN,depth=0,strict_esp=False):
    if depth>6: return None
    for j in range(i-1,max(i-WIN,-1),-1):
        mn=MN[j];ops=OPS[j]
        if not ops or ',' not in ops: continue
        dst,src=ops.split(', ',1); dst=dst.strip(); src=src.strip()
        if dst!=reg: continue
        if mn=='mov':
            if src in RN.values():
                if src=='ecx': return (0,'this')
                r=resolve(j,src,WIN,depth+1,strict_esp)
                return (r[0],'m') if r else None
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'m')
                    r=resolve(j,mp[0],WIN,depth+1,strict_esp)
                    return (r[0]+mp[1],'m') if r else None
                if mp and mp[0] is None:
                    if 'esp' in src and not strict_esp: return (mp[1],'arg')
                    return None
            return None
        if mn=='lea':
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'l')
                    r=resolve(j,mp[0],WIN,depth+1,strict_esp)
                    return (r[0]+mp[1],'l') if r else None
            return None
        if mn in ('add','sub') and src.isdigit():
            r=resolve(j,reg,WIN,depth+1,strict_esp); v=int(src)
            return (r[0]+(v if mn=='add' else -v),'a') if r else None
        if mn=='pop': return None
        if mn in ('xor','movzx','movsx'): return None
    return None
def run(WIN,strict_esp,drop_arg):
    sol=eq=ne=0;neg=0;minpos=10**9;rows=[]
    for a,reg,d,imm,i in H:
        r=resolve(i,reg,WIN,0,strict_esp)
        if r is None: continue
        if drop_arg and r[1]=='arg': continue
        sol+=1; eff=d+r[0]; md_=VB[imm]['mdisp']; dd=eff-md_
        if dd==0: eq+=1
        else:
            ne+=1
            if dd<0:
                neg+=1
            else:
                minpos=min(minpos,dd)
        rows.append((a,reg,d,imm,eff,dd,r[0]))
    return dict(WIN=WIN,strict_esp=strict_esp,drop_arg=drop_arg,sol=sol,eq=eq,ne=ne,neg=neg,
                minpos=(minpos if minpos<10**9 else None)),rows
print('\n变体矩阵：')
res={}
for WIN in (16,32,64,128):
    for se,da in ((False,False),(True,False),(False,True)):
        r,_=run(WIN,se,da); key='W%d%s%s'%(WIN,'S' if se else '','D' if da else '')
        res[key]=r
        print('  %-8s sol=%-5d eq=%-5d ne=%-5d neg=%-3d minpos=%s'%(key,r['sol'],r['eq'],r['ne'],r['neg'],r['minpos']))
# 主会话口径（m10）复核
r0,rows0=run(64,False,False)
print('\n主会话 m10 口径 = W64 : sol=%d eq=%d ne=%d neg=%d minpos=%s'%(r0['sol'],r0['eq'],r0['ne'],r0['neg'],r0['minpos']))
# 审计员口径候选
print('\n=== 哪个变体等于审计员的 2560/2021/539 ? ===')
for k,v in res.items():
    if (v['sol'],v['eq'],v['ne'])==(2560,2021,539): print('  MATCH',k)
print('=== 哪个变体 eq/ne 总量 == 2610/2069/541（审计 E2）? ===')
for k,v in res.items():
    if (v['sol'],v['eq'],v['ne'])==(2610,2069,541): print('  MATCH',k)
# 外部一致性校验：同一视图的同一 C7 块内，delta 应恒定（若块内引用同一 this）
blk=collections.defaultdict(list)
for a,reg,d,imm,eff,dd,delta in rows0:
    blk[imm].append((a,delta,d))
bad=0;tot=0
for imm,v in blk.items():
    if len(v)<2: continue
    v.sort(); grp=[v[0]]
    for x in v[1:]:
        if x[0]-grp[-1][0]<=400: grp.append(x)
        else:
            deltas={g[1] for g in grp}
            if len(grp)>1: tot+=1; bad+= (len(deltas)>1)
            grp=[x]
    if len(grp)>1:
        tot+=1; bad+= (len({g[1] for g in grp})>1)
print('\n=== 外部校验：同视图同块内 delta 恒定性 === 块=%d 不一致块=%d'%(tot,bad))
json.dump({'variants':res,'m10':{'sol':r0['sol'],'eq':r0['eq'],'ne':r0['ne'],'neg':r0['neg'],'minpos':r0['minpos']},
 'blk_tot':tot,'blk_bad':bad},open('/home/t628/projects/ra2-campaign-forge/_r216/m13.json','w'),indent=1)
