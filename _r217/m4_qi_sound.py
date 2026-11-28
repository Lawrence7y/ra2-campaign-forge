# -*- coding: utf-8 -*-
"""R217 m4：律V 修正版。QI 函数判据 = 体内含 repe cmpsd(f3a7) 且以 ret 0xc 收尾。
对每个 QI 函数，取『lea R,[reg+imm] 后 6 条指令内出现 mov dword ptr [eax],R』的 imm 作为交给 ppv 的偏移。
律V：非零偏移必须等于同类（同 pCHD 视图族）某视图的 mdisp。
正控：0x410260 必须识别出偏移集合 {0(来自 mov [eax],ebx 的 this), 4}，family mdisp={0,4,8,12}。
反控：把窗口 6 改为 1 时命中数应下降；把判据改为全局 mdisp 集合时违例数应 >= 类内违例数。
m3 的两个自错（在首个 ret 截断 / 扫描超出函数体 0x400B）在本脚本中已修。
"""
import sys,struct,collections,json,re
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; TLO=t['lo']; THI=TLO+t['rawsize']; D=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
def slots(vt,cap=256):
    out=[]
    for i in range(cap):
        v=P.dw(vt+4*i)
        if not (TLO<=v<THI): break
        out.append(v)
    return out
SL={v:slots(v) for v in VT}
def fn_end(va,cap=512):
    """返回到达首个 ret 的指令列表（含 ret）。"""
    o=P.r2o(va); out=[]
    for i in md.disasm(D[o-t['rawptr']:o-t['rawptr']+cap],va):
        out.append(i)
        if i.mnemonic.startswith('ret'): break
    return out
def is_qi(va):
    ins=fn_end(va)
    if not ins: return None
    last=ins[-1]
    if last.mnemonic!='ret' or last.op_str.replace(' ','')!='0xc': return None
    if not any(i.mnemonic=='repe' or (i.mnemonic.startswith('repe') and 'cmps' in i.op_str) for i in ins):
        # capstone 通常给 mnemonic='repe' ops='cmpsd ...'；兼容直接 f3a7 扫描
        o=P.r2o(va)
        if b'\xf3\xa7' not in P.RAW[o:o+512]: return None
    return ins
def ppv_offsets(ins,win=6):
    res=set()
    for k,i in enumerate(ins):
        if i.mnemonic!='lea': continue
        parts=i.op_str.split(',')
        if len(parts)!=2 or '+' not in parts[1]: continue
        dst=parts[0].strip()
        try: imm=int(parts[1].split('+')[1].strip().rstrip(']'),16)
        except: continue
        for j in range(k+1,min(k+1+win,len(ins))):
            x=ins[j]
            if x.mnemonic=='mov' and x.op_str.startswith('dword ptr [eax]') and parts[0].strip() in x.op_str.split(',')[-1]:
                res.add(imm); break
    return res
FAM=collections.defaultdict(list)
for v,col in VT.items(): FAM[COL[col]['pCHD']].append(v)
GLOBAL_MD={COL[c]['md_'] for c in COL}
# 缓存每个 QI 函数
QIC={}
def qi_of(fn):
    if fn not in QIC: QIC[fn]=is_qi(fn)
    return QIC[fn]
nqi=0; rows=[]; ok=bad=0; badr=[]
for fam,vs in sorted(FAM.items()):
    mdset={COL[VT[v]]['md_'] for v in vs}
    for v in sorted(vs):
        s=SL[v]
        if not s: continue
        ins=qi_of(s[0])
        if not ins or ins is True or not isinstance(ins,list): continue
        offs=ppv_offsets(ins)
        if not offs: continue
        nqi+=1
        extra=offs-mdset
        # 0 偏移来自 mov [eax],ebx（this），也必须在集合内（主视图 mdisp=0）
        rows.append(dict(vt=hex(v),cls=COL[VT[v]]['name'],qifn=hex(s[0]),md=COL[VT[v]]['md_'],mdset=sorted(mdset),offs=sorted(hex(x) for x in offs),extra=sorted(hex(x) for x in extra)))
        if extra: bad+=1; badr.append(rows[-1])
        else: ok+=1
print('[律V] 可测 QI 视图=%d 成立=%d 违例=%d'%(nqi,ok,bad))
print('[正控] 0x410260 ->',[r for r in rows if r['qifn']=='0x410260'][:2])
for b in badr[:10]: print('   VIOL',b['cls'],'md',b['md'],'mdset',b['mdset'],'offs',b['offs'],'extra',b['extra'])
# 反控1: 窗口=1
def ppv1(ins): return ppv_offsets(ins,1)
n1=sum(1 for r in rows if ppv1(qi_of(int(r['qifn'],16))))
print('[反控1] 窗口 6 -> %d 调用点；窗口 1 -> %d 调用点'%(sum(len(ppv_offsets(qi_of(int(r['qifn'],16)))) for r in rows),n1))
# 反控2: 全局 mdisp 判据
bad2=sum(1 for r in rows if {int(x,16) for x in r['offs']}-(GLOBAL_MD))
print('[反控2] 全局 mdisp 判据下违例=%d，类内判据违例=%d'%(bad2,bad))
print('[族] 视图族=%d 多mdisp族=%d 全局不同mdisp值=%d'%(len(FAM),sum(1 for f,vs in FAM.items() if len({COL[VT[v]]['md_'] for v in vs})>1),len(GLOBAL_MD)))
json.dump(dict(meas=nqi,ok=ok,bad=bad,badrows=badr[:20],alt_bad=bad2,fam=len(FAM)),open('_r217/m4.json','w'),indent=1)
