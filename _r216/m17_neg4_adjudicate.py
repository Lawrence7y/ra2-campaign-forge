# -*- coding: utf-8 -*-
"""R216 m17：裁定审计员 E3 变体的 4 条负偏移样本。
逐条给出：该 C7 之前 40 条指令全文 + 手工判定 this 来源，并断言「存在 mov <reg>, ecx」
（即该 reg 直接等于 this，delta 必为 0）⇒ 真实 diff = 0 - mdisp = 0 ⇒ 符号成立。
正控：0x4105a0 的 4 条（mov esi,ecx 之后）必须同样判 delta=0。
反控：把 mov esi,ecx 这条抹掉，正确的 delta 反解必须失败（返回 None），证明是这条指令在撑结论。"""
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
A=[];M=[];O=[]
for off in range(0,sz,64*1024):
    va=lo+off; c=P.RAW[o(va):o(va)+min(64*1024,sz-off)]
    for it in mdl.disasm_lite(c,va): A.append(it[0]);M.append(it[2]);O.append(it[3])
    del c
IX={a:k for k,a in enumerate(A)}
RNV={'eax','ecx','edx','ebx','ebp','esi','edi'}
def resolve(i,reg,WIN=64,drop=None):
    """返回 (delta, 链) 或 None；drop=(addr) 用于反控（跳过指定指令）"""
    if WIN<=0: return None
    for j in range(i-1,max(i-WIN,-1),-1):
        if drop is not None and A[j]==drop: continue
        mn=M[j]; ops=O[j]
        if not ops or ',' not in ops: continue
        dst,src=ops.split(',',1); dst=dst.strip(); src=src.strip()
        if dst!=reg: continue
        if mn=='mov':
            if src=='ecx': return (0,'this')
            if src in RNV:
                r=resolve(j,src,WIN-1,drop); return (r[0],'mov|'+r[1]) if r else None
            if src.startswith('[') and src.endswith(']'):
                body=src[1:-1]
                parts=[x.strip() for x in body.replace('-','+-').split('+')]
                base=None;d=0
                for p in parts:
                    if p in RNV: base=p
                    else:
                        try: d+=int(p,0)
                        except Exception: base=None;break
                if base and base!='esp' and base!='ebp':
                    if base=='ecx': return (d,'leb')
                    r=resolve(j,base,WIN-1,drop); return (r[0]+d,'mov[%s]|%s'%(base,r[1])) if r else None
            return None
        if mn=='lea':
            body=src[1:-1]
            parts=[x.strip() for x in body.replace('-','+-').split('+')]
            base=None;d=0
            for p in parts:
                if p in RNV: base=p
                else:
                    try: d+=int(p,0)
                    except Exception: base=None;break
            if base and base!='esp' and base!='ebp':
                if base=='ecx': return (d,'lea')
                r=resolve(j,base,WIN-1,drop); return (r[0]+d,'lea[%s]|%s'%(base,r[1])) if r else None
            return None
        if mn in ('add','sub') and src.isdigit():
            r=resolve(j,reg,WIN-1,drop); v=int(src)
            return (r[0]+(v if mn=='add' else -v),'addsub|'+r[1]) if r else None
        if mn in ('pop','xor','movzx','movsx'): return None
    return None
SAMPLES=[(0x7ca986,0x7f95d0,-36),(0x7caad8,0x7f95dc,-64),(0x7cac07,0x7f9660,-72),(0x7dcdd2,0x7fa498,-16)]
CK=[]
def ck(n,ok,d=''):
    CK.append((n,bool(ok),str(d))); print('[%s] %-56s %s'%('PASS' if ok else 'FAIL',n,d))
print('=== 4 条负值样本逐条裁定 ===')
for va,imm,adv_delta in SAMPLES:
    i=IX[va]; md_=VB[imm]['mdisp']
    r=resolve(i,'esi')
    print('\n0x%08x  imm=0x%08x mdisp=%d  审计员口径 delta=%d'%(va,imm,md_,adv_delta))
    for j in range(max(i-8,0),i+1):
        print('   %s %08x %-7s %s'%('>>' if A[j]==va else '  ',A[j],M[j],O[j]))
    print('   主会话语义反解: %s'%(r,))
    ck('0x%08x 反解成功'%va, r is not None, r)
    if r:
        eff=0+r[0]; dd=eff-md_
        ck('0x%08x eff(%d)==mdisp(%d) 即符号成立'%(va,eff,md_), eff==md_, 'diff=%d'%dd)
        ck('0x%08x 链上出现 mov esi,ecx（this 直赋）'%va, 'this' in r[1], r[1])
# 反控：把 mov esi,ecx 抹掉后反解必须失败
print('\n=== 反控：抹掉 mov esi,ecx 后反解 ===')
for va,imm,_ in SAMPLES:
    i=IX[va]
    mec=None
    for j in range(i-1,i-12,-1):
        if M[j]=='mov' and O[j].replace(' ','')=='esi,ecx': mec=A[j]; break
    r2=resolve(i,'esi',drop=mec) if mec else resolve(i,'esi')
    nosp=resolve(i,'esi',drop=mec)
    print('   0x%08x 抹掉 %s 后 -> %s'%(va,hex(mec) if mec else None,nosp))
# 正控：0x4105a0 四条
print('\n=== 正控 0x4105a0 ===')
for va in (0x4105a9,0x4105af,0x4105b6,0x4105bd):
    i=IX[va]; r=resolve(i,'esi')
    imm=int(O[i].split(', ')[1],16); disp=int(O[i].split(',')[0].split('+')[1].rstrip(']'),16) if '+' in O[i].split(',')[0] else 0
    md_=VB[imm]['mdisp']
    ck('0x%08x 反解 delta=0 且 disp+delta==mdisp'%va, r is not None and r[0]==0 and disp+r[0]==md_, (r,disp,md_))
print('\n=== 汇总 PASS=%d FAIL=%d ==='%(sum(1 for _,ok,_ in CK if ok),sum(1 for _,ok,_ in CK if not ok)))
json.dump({'ck':[[a,b,c] for a,b,c in CK]},open('/home/t628/projects/ra2-campaign-forge/_r216/m17.json','w'),indent=1)
