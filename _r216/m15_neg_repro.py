# -*- coding: utf-8 -*-
"""R216 m15：完整复刻审计员 #560 的前向状态机（audit_ds16.py 口径），跑 E1..E6 六变体，
把 E3 的 4 条负偏移样本连同完整上下文打印出来，并判定它们是否真为「C7 写视图基址」。
关键：审计员在 C7 位点**之后**才执行状态更新也不影响（它先读 st 再更新）；
      但其 st 只在 mov/lea/add/sub/xor/call/ret/jmp/int3 更新，**其它指令不清寄存器**，
      且在 E3(nocall) 下 call 不作废 eax/ecx/edx ⇒ 跨 call 的陈旧值会被误当 this 偏移。"""
import sys,struct,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True
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
PRE=collections.defaultdict(list) if False else {}
PRE=__import__('collections').defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PRE[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PRE.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PRE.items() if len(v)==1}
VM={}
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    a0=st
    while a0<end and P.where(P.dw(a0))=='.text': a0+=4
    VM[st]=COLA[S2C[st]][0]
VSET=set(VM)
t=P.B['.text']; lo=t['lo']; hi=t['hi_file']
RXC7=re.compile(r'^\[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$')
# 注意：审计员的正则只支持 '+' 与无符号；先照抄以便对账
RXMV=re.compile(r'^([a-z0-9]{2,3}),\s*(.+)$')
RXLD=re.compile(r'^\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$')
COMBOS=[('E1 inherit jres ccall',True,True,True,True),
        ('E2 inherit nojres ccall',True,True,False,True),
        ('E3 inherit jres nocall',True,True,True,False),
        ('E4 noinherit jres ccall',False,True,True,True),
        ('E5 inherit noargload',True,False,True,True),
        ('E6 inherit jres ccall no-ecx0',True,True,True,True)]
S={i:{} for i in range(len(COMBOS))}
R={i:{'sol':0,'eq':0,'ne':0,'neg':0,'d':[]} for i in range(len(COMBOS))}
NEGS={i:[] for i in range(len(COMBOS))}
HIST={}   # 记录每个 C7 位点前 12 条指令，用于负值样本上下文
tail=[]
c7=nonesp=0
blob=P.RAW
va=lo
while va<hi:
    n=min(0x10000,hi-va)
    for off,sz,mn,ops in MD.disasm_lite(blob[o(va):o(va)+n],va):
        raw=blob[o(off):o(off)+sz]
        if mn=='mov' and raw and raw[0]==0xC7 and (raw[1]&0x38)==0:
            c7+=1
            m=RXC7.match(ops)
            if m:
                imm=int(m.group(3),16)
                if imm in VSET and m.group(1)!='esp':
                    nonesp+=1
                    reg=m.group(1); disp=int(m.group(2),0) if m.group(2) else 0; md=VM[imm]
                    for i in S:
                        stt=S[i]
                        if reg in stt:
                            dv=disp+stt[reg]-md
                            R[i]['sol']+=1
                            if dv==0: R[i]['eq']+=1
                            else:
                                R[i]['ne']+=1; R[i]['d'].append(dv)
                                if dv<0:
                                    R[i]['neg']+=1
                                    if len(NEGS[i])<12: NEGS[i].append((off,ops,reg,disp,stt[reg],md,dv,list(tail)))
        for i,(lab,inh,argo,jres,ccall) in enumerate(COMBOS):
            stt=S[i]
            if mn=='call':
                if ccall:
                    for x in ('eax','ecx','edx'): stt.pop(x,None)
            elif mn in ('ret','retf','int3'): stt.clear(); stt['ecx']=0
            elif mn=='jmp':
                if jres: stt.clear(); stt['ecx']=0
            elif mn=='mov':
                m=RXMV.match(ops)
                if not m: continue
                d,src=m.group(1),m.group(2).strip()
                if re.match(r'^0x[0-9a-f]+$',src): stt.pop(d,None); continue
                l=RXLD.match(src)
                if l:
                    b=l.group(1); k2=int(l.group(3),0)*(1 if l.group(2)!='-' else -1) if l.group(3) else 0
                    if b in ('esp','ebp'): stt[d]=k2 if argo else 0
                    elif inh and b in stt: stt[d]=stt[b]+k2
                    elif inh: stt[d]=0
                    else: stt.pop(d,None)
                    continue
                if re.match(r'^[a-z0-9]{2,3}$',src):
                    if src in stt: stt[d]=stt[src]
                    else: stt.pop(d,None)
                    continue
                stt.pop(d,None)
            elif mn=='lea':
                m=RXMV.match(ops)
                if not m: continue
                d,src=m.group(1),m.group(2).strip()
                l=RXLD.match(src)
                if l:
                    b=l.group(1); k2=int(l.group(3),0)*(1 if l.group(2)!='-' else -1) if l.group(3) else 0
                    if b in ('esp','ebp'): stt[d]=k2
                    elif b in stt: stt[d]=stt[b]+k2
                    else: stt.pop(d,None)
                    continue
                stt.pop(d,None)
            elif mn in ('add','sub'):
                m=re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$',ops)
                if m:
                    r2=m.group(1); v=int(m.group(2),0)*(1 if mn=='add' else -1)
                    if r2 in stt: stt[r2]+=v
                    else: stt.pop(r2,None)
                    continue
                r2=re.sub(r'^(dword ptr|byte ptr) ','',ops.split(',')[0].strip()); stt.pop(r2,None)
            elif mn=='xor':
                d=ops.split(',')[0].strip(); stt.pop(d,None)
        tail.append((off,mn,ops)); tail=tail[-12:]
print('C7/0=%d  non-esp+imm-in-VSET=%d'%(c7,nonesp))
for i,(lab,_,_,_,_) in enumerate(COMBOS):
    r=R[i]
    print(' %-28s sol=%d eq=%d ne=%d neg=%d'%(lab,r['sol'],r['eq'],r['ne'],r['neg']))
print('\n=== 全部负偏移样本（各变体）===')
for i,(lab,_,_,_,_) in enumerate(COMBOS):
    if not NEGS[i]: continue
    print('\n---- %s ----'%lab)
    for off,ops,reg,disp,delta,md,dv,tn in NEGS[i]:
        print('  0x%08x  %-40s reg=%s disp=%d delta=%d mdisp=%d diff=%d'%(off,ops,reg,disp,delta,md,dv))
        for a,mn,o2 in tn[-8:]: print('       %08x %-7s %s'%(a,mn,o2))
json.dump({'c7':c7,'nonesp':nonesp,
 'res':{COMBOS[i][0]:{k:v for k,v in R[i].items() if k!='d'} for i in range(len(COMBOS))},
 'negs':{COMBOS[i][0]:[['0x%08x'%x[0],x[1],x[2],x[3],x[4],x[5],x[6]] for x in NEGS[i]] for i in range(len(COMBOS))}},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m15.json','w'),indent=1)
