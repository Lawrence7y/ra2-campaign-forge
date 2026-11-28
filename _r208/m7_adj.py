# -*- coding: utf-8 -*-
"""R208 m7（本轮主攻）：COL.mdisp 与 vftable slot0 的 this 调整 thunk 位移量逐条对齐（字节实证）。
主张 H：额外视图 COL（mdisp != 0）的 vftable 的 slot0 是 MSVC this 调整 thunk：
        sub dword [esp+4], mdisp ; jmp <real scalar deleting dtor>
  ⇒ 反汇编 slot0 得到的立即数应恒等于该 COL 的 mdisp。
正控：260 条额外视图逐条
反控：(a) 内嵌主视图（mdisp==0）的 slot0 应无 sub 位移；(b) 把 mdisp 随机置换后对齐率应崩
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
md=Cs(CS_ARCH_X86,CS_MODE_32)
def dis1(a,maxn=8):
    o=P.r2o(a)
    if o is None: return []
    return list(md.disasm(P.RAW[o:o+40],a))[:maxn]
def subimm(a):
    """若 slot0 形如 sub dword ptr [esp+4], imm ; jmp X 返回 (imm, target)，否则 None"""
    ins=dis1(a,3)
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4' not in i0.op_str.replace('[esp+4]','[esp + 4]'): return None
    try: imm=int(i0.op_str.split(',')[-1].strip(),16)
    except Exception: return None
    if i1.mnemonic!='jmp': return None
    return (imm,i1.op_str.strip())
emb=[c for c in COL if c==COL[c]['pCHD']+16]
extra=[c for c in COL if c!=COL[c]['pCHD']+16]
print('内嵌 %d 额外 %d' % (len(emb),len(extra)))
res={}
for c in COL:
    s0=P.dw(vt[c]) if c in vt else None
    res[c]=dict(mdisp=COL[c]['mdisp'],slot0=s0,adj=subimm(s0) if s0 else None,name=COL[c]['name'])
ok=sum(1 for c in extra if res[c]['adj'] and res[c]['adj'][0]==res[c]['mdisp'])
nz=[c for c in extra if res[c]['mdisp']!=0]
oknz=sum(1 for c in nz if res[c]['adj'] and res[c]['adj'][0]==res[c]['mdisp'])
print('== A 逐条对齐 ==')
print('  额外视图 %d 条中 mdisp!=0 的 %d 条' % (len(extra),len(nz)))
print('  全额外视图对齐 %d/%d；仅 mdisp!=0 对齐 %d/%d' % (ok,len(extra),oknz,len(nz)))
print('  mdisp 取值分布(额外视图) %s' % collections.Counter(res[c]['mdisp'] for c in extra).most_common())
print('  未对齐明细(前 12):')
bad=[c for c in nz if not (res[c]['adj'] and res[c]['adj'][0]==res[c]['mdisp'])]
for c in bad[:12]:
    print('   0x%x mdisp=%-4d slot0=0x%x adj=%s %s' % (c,res[c]['mdisp'],res[c]['slot0'] or 0,res[c]['adj'],res[c]['name']))
print('== B 内嵌主视图 slot0 形态 ==')
bz=[c for c in emb if subimm(P.dw(vt[c]) if c in vt else 0)]
print('  954 内嵌视图中 slot0 是 sub-adj 形态的 %d 条（应为 0）' % len(bz))
for c in bz[:5]: print('   0x%x %s adj=%s' % (c,res[c]['name'],res[c]['adj']))
print('== C 反控：mdisp 随机置换 ==')
import random
random.seed(208)
vals=[res[c]['mdisp'] for c in nz]
hit=[]
for _ in range(3):
    random.shuffle(vals)
    hit.append(sum(1 for c,v in zip(nz,vals) if res[c]['adj'] and res[c]['adj'][0]==v))
print('  置换后对齐 %s（真值 %d/%d）' % (hit,oknz,len(nz)))
print('== D thunk 目标（真实析构）频次 ==')
tg=collections.Counter(res[c]['adj'][1] for c in nz if res[c]['adj'])
print('  %s' % tg.most_common(6))
json.dump(dict(extra=len(extra),nz=len(nz),okAll=ok,okNz=oknz,ctrl=hit,
               mdispDist=[[k,v] for k,v in collections.Counter(res[c]['mdisp'] for c in extra).most_common()],
               bad=[[hex(c),res[c]['mdisp'],hex(res[c]['slot0'] or 0),str(res[c]['adj']),res[c]['name']] for c in bad[:20]],
               targets=tg.most_common(8)),
          open('_r208/m7_adj.json','w'),ensure_ascii=False,indent=1)
