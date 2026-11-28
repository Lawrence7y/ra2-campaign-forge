# -*- coding: utf-8 -*-
"""R216 m7：律 U（次级视图 slot0 = this-adjustor thunk，imm == mdisp_self - mdisp_target）
与律 V（律 T 的 A 族 46 条：写入点前 48 字节内是否有 lea reg,[reg+disp] 且 disp == 该视图 mdisp）。"""
import sys,struct,json,collections
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
    sl=[];a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a));a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
VB={v['base']:v for v in VIEWS}
def head(va,n=16):
    return [(i[0],i[1],i[2],i[3]) for i in mdl.disasm_lite(P.RAW[o(va):o(va)+n],va)]
print('=== 律 U ===')
SEC=[v for v in VIEWS if v['mdisp']!=0]
form=collections.Counter(); ok=[];bad=[];na=[]
for v in SEC:
    if not v['slots']: form['空视图']+=1; continue
    h=head(v['slots'][0],16)
    if not h: form['无法解码']+=1; continue
    m0,o0=h[0][2],h[0][3]
    if m0 not in ('sub','add') or not o0.startswith('dword ptr [esp + 4], '):
        form['非 adjustor 首指令:'+m0]+=1; na.append(('0x%08x'%v['base'],v['nm'],v['mdisp'],m0,o0)); continue
    imm=int(o0.split(', ')[1],0)
    sgn = 1 if m0=='sub' else -1
    eff = sgn*imm                      # sub 4 => 后移 4 -> target 在前
    jmp=[x for x in h if x[2]=='jmp']
    if not jmp: form['thunk 无 jmp']+=1; continue
    jt=int(jmp[0][3],16)
    tv=None
    for b,vv in VB.items():
        if vv['slots'] and vv['slots'][0]==jt: tv=vv; break
    if tv is None: form['jmp 目标非视图 slot0']+=1; na.append(('0x%08x'%v['base'],v['nm'],v['mdisp'],'jmp','0x%08x'%jt)); continue
    pred=v['mdisp']-tv['mdisp']
    if eff==pred: ok.append((v,tv,imm,eff))
    else: bad.append(('0x%08x'%v['base'],v['nm'],v['mdisp'],imm,eff,pred,tv['nm'],tv['mdisp']))
print('次级视图=%d 形态=%s'%(len(SEC),form.most_common(6)))
print('律 U 成立=%d 不成立=%d'%(len(ok),len(bad)))
print('反例:',bad[:8])
print('非 thunk 明细前6:',na[:6])
# 每类次级视图 mdisp 与 target mdisp 组合
combo=collections.Counter((a[0]['mdisp'],a[1]['mdisp'],a[2]) for a in ok)
print('(self_mdisp, target_mdisp, imm) top12:',combo.most_common(12))
print('\n=== 律 V：A 族写入点前驱 lea ===')
base_t=P.B['.text']['lo']
A=[]
for a,off,imm in []: pass
# 重新算 A 族（复用 m5 口径）
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
n=len(tb)
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
    if imm in VB and off==0 and VB[imm]['mdisp']!=0: A.append((base_t+k,imm))
print('A 族=%d'%len(A))
res=[]
for a,imm in A:
    md_=VB[imm]['mdisp']
    back=head(a-40,48) if P.where(a-40)=='.text' else []
    # 取位点之前的指令（最后 10 条）
    prev=[x for x in back if x[0]<a][-10:]
    hit=[x for x in prev if x[2]=='lea' and ('+ %d]'%md_) in x[3] or (x[2]=='lea' and x[3].endswith('+ 0x%x]'%md_))]
    add=[x for x in prev if x[2] in ('add','sub') and x[3]==('ecx, %d'%md_ if x[2]=='add' else 'ecx, %d'%md_)]
    res.append((a,imm,md_,bool(hit),bool(add),[ (x[0],x[2],x[3]) for x in prev[-4:] ]))
nh=sum(1 for r in res if r[3]); nad=sum(1 for r in res if r[4])
print('  A 族中前驱有 lea [reg+%d] 的=%d/%d ; 有 add/sub ecx,%d 的=%d'%(0,nh,len(A),0,nad))
print('  样例（含前驱 4 指令）:')
for a,imm,md_,h1,h2,prev in res[:12]:
    print('   0x%08x imm=0x%08x mdisp=%d lea=%s addsub=%s prev=%s'%(a,imm,md_,h1,h2,prev))
json.dump({'lawU':{'sec':len(SEC),'ok':len(ok),'bad':len(bad),'forms':dict(form),
  'combo':[[k[0],k[1],k[2],v] for k,v in combo.most_common()],'bad_ex':bad[:20],'na':na[:20]},
  'lawV':{'A':len(A),'lea_hit':nh,'addsub_hit':nad,
  'rows':[['0x%08x'%a,'0x%08x'%i,m,h1,h2,[list(p) for p in prev]] for a,i,m,h1,h2,prev in res]}},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m7.json','w'),indent=1)
