# -*- coding: utf-8 -*-
"""R216 m14：定位审计员 E3 变体的 4 条负偏移样本，并检验它们是否真为写 vfptr。
E3 = inherit jres nocall：delta 反解时要求该路径上出现过 jmp/res 边界，且不要求 call。
做法：在本会话指令表上复现「在窗口内命中 call/ret 则截断搜索」的变体，输出全部 neg<0 样本的完整上下文。"""
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
for off in range(0,sz,64*1024):
    va=lo+off; c=P.RAW[o(va):o(va)+min(64*1024,sz-off)]
    for it in mdl.disasm_lite(c,va): ADDR.append(it[0]);MN.append(it[2]);OPS.append(it[3])
    del c
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
H=[]
for k in range(len(ADDR)):
    if MN[k]!='mov' or not OPS[k].startswith('dword ptr [') or ', ' not in OPS[k]: continue
    mem,imm=OPS[k].split(', ',1); iv=P_(imm)
    if iv is None or iv not in VB: continue
    mp=memparse(mem[len('dword ptr ['):-1])
    if not mp or not mp[0]: continue
    H.append((ADDR[k],mp[0],mp[1],iv,k))
# E3 变体：搜索窗口 64；遇到 jmp/ret/call 视为边界（jres = jump/reset），但**不要求** call 出现过
def resolve_e3(i,reg,WIN=64,depth=0,saw_call=[False]):
    if depth>6: return None
    for j in range(i-1,max(i-WIN,-1),-1):
        mn=MN[j];ops=OPS[j]
        if mn in ('jmp','ret') : return None       # jres: 遇跳转/返回即断
        if not ops or ',' not in ops: continue
        dst,src=ops.split(',',1); dst=dst.strip(); src=src.strip()
        if dst!=reg: continue
        if mn=='mov':
            if src in RN.values():
                if src=='ecx': return (0,'this')
                r=resolve_e3(j,src,WIN,depth+1,saw_call); return (r[0],'m') if r else None
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'m')
                    r=resolve_e3(j,mp[0],WIN,depth+1,saw_call); return (r[0]+mp[1],'m') if r else None
            return None
        if mn=='lea':
            if src.startswith('['):
                mp=memparse(src[1:src.rindex(']')])
                if mp and mp[0]:
                    if mp[0]=='ecx': return (mp[1],'l')
                    r=resolve_e3(j,mp[0],WIN,depth+1,saw_call); return (r[0]+mp[1],'l') if r else None
            return None
        if mn in ('add','sub') and src.isdigit():
            r=resolve_e3(j,reg,WIN,depth+1,saw_call); v=int(src)
            return (r[0]+(v if mn=='add' else -v),'a') if r else None
        if mn in ('pop','xor','movzx','movsx'): return None
    return None
sol=eq=ne=0; negs=[]
for a,reg,d,imm,i in H:
    r=resolve_e3(i,reg)
    if r is None: continue
    sol+=1; eff=d+r[0]; md_=VB[imm]['mdisp']; dd=eff-md_
    if dd==0: eq+=1
    else:
        ne+=1
        if dd<0: negs.append((a,reg,d,r[0],eff,imm,md_,dd,VB[imm]['nm']))
print('E3 复现：sol=%d eq=%d ne=%d neg=%d'%(sol,eq,ne,len(negs)))
for a,reg,d,delta,eff,imm,md_,dd,nm in negs:
    print('\n--- 负偏移样本 0x%08x  [%s%+d] delta=%d eff=%d mdisp=%d diff=%d  %s'%(a,reg,d,delta,eff,md_,dd,nm))
    i=[k for k in range(len(ADDR)) if ADDR[k]==a][0]
    for j in range(max(i-14,0),i+2):
        mark='>>' if ADDR[j]==a else '  '
        print('   %s %08x %-7s %s'%(mark,ADDR[j],MN[j],OPS[j]))
json.dump({'sol':sol,'eq':eq,'ne':ne,'neg':len(negs),
 'negs':[['0x%08x'%a,reg,d,delta,eff,'0x%08x'%imm,md_,dd,nm] for a,reg,d,delta,eff,imm,md_,dd,nm in negs]},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m14.json','w'),indent=1)
