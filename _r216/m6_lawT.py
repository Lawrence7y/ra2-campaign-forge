# -*- coding: utf-8 -*-
"""R216 m6：律 T 违例族群量化 + 律 U（次级视图 slot0 = adjustor thunk，imm == mdisp_self - mdisp_target）。"""
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
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]; base=t['lo']
def scan(vbset):
    hits=[];n=len(tb)
    for k in range(n-6):
        if tb[k]!=0xc7: continue
        m=tb[k+1]; mod=m>>6; reg=(m>>3)&7; rm=m&7
        if reg!=0 or rm==4 or rm==5 and mod==0: continue
        if mod==0: off=0;io=k+2
        elif mod==1: off=s32(struct.pack('<i',tb[k+2] if tb[k+2]<0x80 else tb[k+2]-256));io=k+3
        elif mod==2: off=s32(tb[k+2:k+6]);io=k+6
        else: continue
        if io+4>n: continue
        imm=struct.unpack_from('<I',tb,io)[0]
        if imm in vbset: hits.append((base+k,off,imm))
    return hits
hits=scan(VB)
ok=[h for h in hits if h[1]==VB[h[2]]['mdisp']]
bad=[h for h in hits if h[1]!=VB[h[2]]['mdisp']]
print('律 T 总命中=%d ; 符=%d (%.2f%%) ; 违例=%d (%.2f%%)'%(len(hits),len(ok),100*len(ok)/len(hits),len(bad),100*len(bad)/len(hits)))
# 违例分族
fam=collections.Counter()
for a,off,imm in bad:
    v=VB[imm]; md_=v['mdisp']
    if off==0 and md_!=0: fam['A:off=0 写次级视图']+=1
    elif md_==0 and abs(off)>64: fam['B:大偏移写主视图(内嵌成员)']+=1
    elif abs(off-md_)<=64: fam['C:近邻偏移']+=1
    else: fam['D:其它']+=1
print('违例分族:',fam.most_common())
print('\n--- A 族 top15（写入对象 = 该类次级基址处）---')
for a,off,imm in [h for h in bad if h[1]==0 and VB[h[2]]['mdisp']!=0][:15]:
    print('  0x%08x  off=0  imm=0x%08x  mdisp=%d  %s'%(a,imm,VB[imm]['mdisp'],VB[imm]['nm']))
print('\n--- B 族（内嵌成员证据）按 (类,偏移) 聚合 top25 ---')
bc=collections.Counter((VB[i]['nm'],off) for a,off,i in bad if VB[i]['mdisp']==0 and abs(off)>64)
for (nm,off),c in bc.most_common(25): print('  %+6d  %-42s x%d'%(off,nm,c))
print('\n--- C 族明细 ---')
for a,off,imm in [h for h in bad if h[1]!=0 and VB[h[2]]['mdisp']==0 and abs(h[1])<=64][:12]:
    print('  0x%08x off=%d imm=0x%08x %s'%(a,off,imm,VB[imm]['nm']))
# ---- 律 U：mdisp!=0 视图 slot0 是否 thunk ----
print('\n=== 律 U：次级视图 slot0 形态 ===')
SEC=[v for v in VIEWS if v['mdisp']!=0]
st=collections.Counter(); lawU=[0,0]; ex=[]
for v in SEC:
    if not v['slots']: continue
    tgt=v['slots'][0]; cur=tgt; depth=0; imm=None; jt=None
    while depth<3:
        ins=list(mdl.disasm(P.RAW[o(cur):o(cur)+16],cur))
        if not ins: break
        i0=ins[0]
        if i0.mnemonic in ('sub','add') and i0.op_str.startswith('dword ptr [esp + 4], '):
            imm=int(i0.op_str.split(', ')[1],0); cur=ins[1].address if len(ins)>1 and ins[1].mnemonic=='jmp' else None
            break
        if i0.mnemonic=='push' : st['push 开头']+=1; break
        st['非 thunk:'+i0.mnemonic]+=1; break
    if imm is None: continue
    # jmp 目标
    ins=list(mdl.disasm(P.RAW[o(cur)-0:o(cur)+8],cur)) if cur else []
    jt=None
    if ins and ins[0].mnemonic=='jmp' and ins[0].operands and ins[0].operands[0].__class__.__name__=='X86Op':
        try: jt=ins[0].operands[0].imm
        except Exception: jt=None
    if jt is None:
        # 从前一条 jmp 指令解析
        pred=list(mdl.disasm(P.RAW[o(v['slots'][0]):o(v['slots'][0])+16],v['slots'][0]))
        for i in pred:
            if i.mnemonic=='jmp': jt=int(i.op_str,16) if i.op_str.startswith('0x') else int(i.op_str,0)
    tv=None
    for b,vv in VB.items():
        if vv['slots'] and vv['slots'][0]==jt: tv=vv
    if tv is None:
        st['thunk 目标非视图slot0']+=1; continue
    pred_md=v['mdisp']-tv['mdisp']
    if imm==pred_md: lawU[0]+=1
    else:
        lawU[1]+=1; ex.append(('0x%08x'%v['base'],v['nm'],v['mdisp'],imm,tv['mdisp'],'0x%08x'%jt))
print('  次级视图数=%d ; thunk 形态统计=%s'%(len(SEC),st.most_common(8)))
print('  律 U 成立=%d 不成立=%d'%(lawU[0],lawU[1]))
print('  反例前10:',ex[:10])
json.dump({'lawT':{'total':len(hits),'ok':len(ok),'bad':len(bad),'fam':dict(fam),
  'B_embedded':[[nm,off,c] for (nm,off),c in bc.most_common(80)]},
  'lawU':{'sec':len(SEC),'ok':lawU[0],'bad':lawU[1],'ex':ex[:30],'forms':dict(st)}},
  open('/home/t628/projects/ra2-campaign-forge/_r216/m6.json','w'),indent=1)
