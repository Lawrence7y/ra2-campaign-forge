# -*- coding: utf-8 -*-
"""R217 m1：MI 视图骨架/转发桩/QI 偏移律 本地基准（只读，一次全输出）。
COL 记录(24B)：+0 sig +4 mdisp +8 cdOffset +0xc pTD +0x10 pCHD +0x14 self
vtable V 满足 dw(V-4)==COL。
正控：AbstractClass 四视图 slot 数与 mdisp 一一对上；反控见下。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; TLO=t['lo']; THI=TLO+t['rawsize']
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def dis(va,n):
    o=P.r2o(va); return list(md.disasm(P.RAW[o:o+n],va))
# --- COL 候选 ---
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL)
# --- vtable = 某个 dword==COL 的位置 +4 ---
VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
VTS=sorted(VT)
def slots(vt,cap=256):
    out=[]
    for i in range(cap):
        v=P.dw(vt+4*i)
        if not (TLO<=v<THI): break
        out.append(v)
    return out
SL={v:slots(v) for v in VTS}
print('[骨架] COL候选=%d  vtable=%d  mdisp!=0视图=%d'%(len(COL),len(VTS),sum(1 for v in VTS if COL[VT[v]]['md_']!=0)))
# --- 律U: sub dword[esp+4],N ; jmp ---
def adj(vt):
    s=SL[vt]
    if not s: return None
    ins=dis(s[0],16)
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4' not in i0.op_str or i1.mnemonic!='jmp': return None
    if not i1.op_str.startswith('0x'): return None
    try: n=int(i0.op_str.split(',')[-1].strip().rstrip(']'),16)
    except Exception: return None
    return (n,int(i1.op_str,16),i0.bytes.hex()+i1.bytes.hex())
ADJ={v:adj(v) for v in VTS}
nz=[v for v in VTS if COL[VT[v]]['md_']!=0]
lawU=[v for v in nz if ADJ[v]]
ok=bad=0; bt=[];neg0=0
tmap={}
for v in VTS:
    if SL[v]: tmap.setdefault(SL[v][0],[]).append(v)
for v in lawU:
    n,tgt,_=ADJ[v]
    exp=None
    if tgt in tmap:
        # 目标视为 slot0 入口相同的某视图
        cand=[tv for tv in tmap[tgt] if tv!=v]
    else: cand=[]
    if not cand: bt.append(('noTgt',hex(v),hex(tgt),n)); continue
    e=COL[VT[v]]['md_']-COL[VT[cand[0]]]['md_']
    if n==e: ok+=1
    else:
        bad+=1; bt.append(('mismatch',hex(v),hex(tgt),n,e))
print('[律U] slot0=adjustor 视图=%d 成立=%d 违例=%d'%(len(lawU),ok,bad)) ; print('   异常样本',bt[:8])
print('[反控U] 判据改 N==mdisp-1 ->', sum(1 for v in lawU if (lambda a:(a[0]==COL[VT[v]]['md_']-1))(ADJ[v])))
# --- 转发桩（thunk-to-primary）：mov eax,[esp+4];mov reg,[eax-4];lea reg,[eax-4];call [reg+K];ret N ---
def fwd(vt):
    res=[]
    for f in SL[vt]:
        ins=dis(f,24)
        if len(ins)<5: continue
        if ins[0].mnemonic!='mov' or '[esp + 4]' not in ins[0].op_str: continue
        if ins[1].mnemonic!='mov' or '- 4' not in ins[1].op_str: continue
        if ins[2].mnemonic!='lea' or '- 4' not in ins[2].op_str: continue
        if ins[3].mnemonic!='call' or '[edx +' not in ins[3].op_str: continue
        if not ins[4].mnemonic.startswith('ret'): continue
        try: k=int(ins[3].op_str.split('+')[1].strip().rstrip(']'),16)
        except Exception: continue
        res.append((f,k,ins[4].mnemonic+' '+ins[4].op_str,b''.join(i.bytes for i in ins[:5]).hex()))
    return res
FW={v:fwd(v) for v in VTS}
tot=sum(len(x) for x in FW.values())
print('[转发桩] 总数=%d 视图=%d'%(tot,sum(1 for v in VTS if FW[v])))
KS=collections.Counter()
for v in VTS:
    for f,k,r,h in FW[v]:
        KS[k]+=1
        print('   view %08x %-42s mdisp=%2d slot? fwd=%08x K=%#x %s'%(v,COL[VT[v]]['name'],COL[VT[v]]['md_'],f,k,h))
print('   K 分布', {hex(k):n for k,n in KS.items()})
# --- QI 偏移律：repe cmpsd 后方 lea reg,[ebx+d] 的 d ---
hits=[i for i in range(t['rawsize']-1) if P.RAW[t['rawptr']+i]==0xf3 and P.RAW[t['rawptr']+i+1]==0xa7]
offs=collections.Counter(); sites=[]
for i in hits:
    va=TLO+i
    ins=dis(va+2,32); d=None
    for x in ins[:4]:
        if x.mnemonic=='lea':
            op=x.op_str.split(',')[-1].strip()
            if '+' in op:
                try: d=int(op.split('+')[1].strip().rstrip(']'),16)
                except Exception: d=None
                break
    if d is not None: offs[d]+=1; sites.append((hex(va),d))
print('[QI律] repe cmpsd 站点=%d 其中后接 lea +d = %d, d分布=%s'%(len(hits),len(sites),{hex(k):n for k,n in offs.items()}))
json.dump(dict(COLN=len(COL),VTN=len(VTS),lawU=len(lawU),lawUok=ok,lawUbad=bad,
  fwd=tot,fwdK={hex(k):n for k,n in KS.items()},qi=dict(n=len(sites),dist={hex(k):v for k,v in offs.items()})),
  open('_r217/m1.json','w'),indent=1)
