# -*- coding: utf-8 -*-
"""R216 m8：try-align 反解前驱，把律 T 升级为律 W（有效偏移 = 寄存器基址增量 + disp）。
try-align 规则：对命中点 a，试每个起点 s in [a-24, a-1]，capstone 从 s 顺序解码，
若某条指令的结束地址恰为 a 且总指令数 <=6，则接受该序列为对齐前驱（多个候选按指令数最少优先）。
正控：0x4105a0 体内 4 条写入，esi=ecx=对象首址 ⇒ 基址增量 0，有效偏移 = 0/4/8/12 = mdisp。
反控：把候选窗口改成 [a-24,a-1] 内的随机错位起点集合，对齐成功率必须显著下降。"""
import sys,struct,json,collections,random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
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
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]; base=t['lo']
def allc7():
    hits=[];n=len(tb)
    for k in range(n-6):
        if tb[k]!=0xc7: continue
        m=tb[k+1];mod=m>>6;reg=(m>>3)&7;rm=m&7
        if reg!=0 or rm==4 or (mod==0 and rm==5): continue
        if mod==0: off=0;io=k+2
        elif mod==1: off=s32(struct.pack('<i',tb[k+2] if tb[k+2]<0x80 else tb[k+2]-256));io=k+3
        elif mod==2: off=s32(tb[k+2:k+6]);io=k+6
        else: continue
        if io+4>n: continue
        imm=struct.unpack_from('<I',tb,io)[0]
        if imm in VB: hits.append((base+k,off,imm,rm))
    return hits
H=allc7()
print('C7 命中视图基址 = %d'%len(H))
def try_align(a,win=24,maxins=6):
    """返回 (起点, [(addr,mnem,ops)]) ；失败 None"""
    best=None
    for s in range(a-win,a):
        if P.where(s)!='.text': continue
        try:
            ins=list(mdl.disasm_lite(P.RAW[o(s):o(s)+win+24],s))
        except Exception: continue
        if not ins or ins[0][0]!=s: continue
        acc=s;seq=[]
        for it in ins:
            if it[0]!=acc: break
            seq.append(it);acc=it[0]+it[1]
            if acc==a:
                if best is None or len(seq)<len(best[1]): best=(s,seq)
                break
            if acc>a or len(seq)>maxins: break
    return best
def regbase(seq, rm, base_off):
    """在 try-align 序列里反解 rm 寄存器的基址增量；返回 delta 或 None"""
    RN={0:'eax',1:'ecx',2:'edx',3:'ebx',6:'esi',7:'edi'}
    tgt=RN[rm]; delta=0; found=False
    for (ad,sz,mn,ops) in seq:
        if mn in ('mov','lea') and ops.startswith(tgt+', '):
            rhs=ops[len(tgt)+2:]
            if mn=='lea' and rhs.startswith('[') and rhs.endswith(']'):
                inner=rhs[1:-1]
                # 形式 [reg + N] / [reg] / [reg - N]
                parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                if len(parts)==2 and parts[0] in RN.values() and parts[1].lstrip('-').isdigit():
                    delta=int(parts[1]); found=True
                elif len(parts)==1 and parts[0] in RN.values():
                    delta=0; found=True
            elif mn=='mov' and 'dword ptr [esp' in rhs:
                return None
            elif mn=='mov' and rhs.startswith('[') and ']' in rhs:
                inner=rhs[1:rhs.index(']')]
                parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                if len(parts)==2 and parts[1].lstrip('-').isdigit():
                    delta=int(parts[1]); found=True
            elif mn=='mov' and (rhs in RN.values() or rhs.isdigit() or rhs.startswith('0x')):
                return None
        if mn in ('add','sub') and ops.startswith(tgt+', ') and ops.split(', ')[1].isdigit():
            v=int(ops.split(', ')[1]); delta += v if mn=='add' else -v; found=True
        if mn in ('push','pop','call','xor','test','cmp') and ops.split(',')[0].strip()==tgt:
            if mn in ('xor','pop','call'): return None
    return delta if found else None
# 先做正控
pc=[h for h in H if 0x4105a0<=h[0]<0x4105d3]
print('[正控] 0x4105a0 命中=%d'%len(pc))
for a,off,imm,rm in pc:
    al=try_align(a)
    d=regbase(al[1],rm,off) if al else None
    print('   0x%08x off=%d imm=0x%08x rm=%d align=%s delta=%s eff=%s mdisp=%d'%(
        a,off,imm,rm,'Y' if al else 'N',d,(off+d) if d is not None else None,VB[imm]['mdisp']))
neg=0;okn=0
random.seed(7)
sample=random.sample([h for h in H if not(0x4105a0<=h[0]<0x4105d3)],300)
for a,off,imm,rm in sample:
    if try_align(a): okn+=1
    # 错位反控：窗口整体平移 -60..-40
    bad=try_align(a-50)
    if bad: neg+=1
print('[反控] 随机 300 条 try-align 成功=%d ; 把命中点前移 50B 再对齐成功=%d'%(okn,neg))
# 全量律 W
stat=collections.Counter(); viol=[]
for a,off,imm,rm in H:
    al=try_align(a)
    if not al: stat['无对齐前驱']+=1; continue
    d=regbase(al[1],rm,off)
    if d is None: stat['基址未还原']+=1; continue
    eff=off+d; md_=VB[imm]['mdisp']
    if eff==md_: stat['符(律W)']+=1
    else:
        stat['违例']+=1; viol.append((a,off,d,eff,imm,md_,VB[imm]['nm']))
print('=== 律 W 全量 ===',stat.most_common())
print('违例 %d 条，前 20：'%len(viol))
for a,off,d,eff,imm,md_,nm in viol[:20]:
    print('   0x%08x off=%d delta=%d eff=%d imm=0x%08x mdisp=%d %s'%(a,off,d,eff,imm,md_,nm))
vc=collections.Counter((nm,eff,md_) for a,off,d,eff,imm,md_,nm in viol)
print('违例按(类,eff,mdisp) top15:',vc.most_common(15))
json.dump({'c7_total':len(H),'stat':dict(stat),'viol':[['0x%08x'%a,off,d,eff,'0x%08x'%imm,md_,nm] for a,off,d,eff,imm,md_,nm in viol[:200]],
 'neg':neg,'pos_align':okn},open('/home/t628/projects/ra2-campaign-forge/_r216/m8.json','w'),indent=1)
