# -*- coding: utf-8 -*-
"""R217 m5：律V 最终版（按填充边界切函数，不用 ret 截断）。
QI 函数判据：函数体内含 f3a7（repe cmpsd）且至少一个 ret imm16。
偏移抽取：函数体内 lea R,[基址寄存器+imm] 之后 8 条内出现 mov dword ptr [eax],R  => imm 为该 IID 对应的子对象偏移；
          另记 mov dword ptr [eax],基址寄存器（偏移 0）作为 0。
律V：抽取到的偏移集合 必须 ⊆ 同类（同 pCHD 视图族）视图的 mdisp 集合。
自错登记：m3 在首个 ret 截断（0x41026f 是 E_POINTER 提前返回）=> 0 命中；m4 同病。本脚本按 0x90/0xcc 填充边界取函数跨度。
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
# 填充边界：>=4 连续 0x90 或 0xcc
pad=[False]*len(D)
run=0
for i,b in enumerate(D):
    pass
def span_end(va,cap=0x400):
    o=P.r2o(va)-t['rawptr']; n=0
    j=o
    while j<o+cap and j<len(D):
        if D[j] in (0x90,0xcc) and D[j:j+4] in (b'\x90\x90\x90\x90',b'\xcc\xcc\xcc\xcc',b'\x90\x90\x90\xcc',b'\xcc\xcc\xcc\x90'):
            break
        j+=2; n+=1
    return j
def fn_ins(va,cap=0x400):
    o=P.r2o(va)-t['rawptr']
    end=min(o+cap,len(D))
    blob=D[o:end]
    # 截到首个 >=4 填充
    for j in range(len(blob)-3):
        if blob[j:j+4] in (b'\x90\x90\x90\x90',b'\xcc\xcc\xcc\xcc'):
            blob=blob[:j]; break
    return list(md.disasm_lite(blob,va))
def is_qi(va):
    o=P.r2o(va)-t['rawptr']
    if b'\xf3\xa7' not in D[o:o+0x200]: return None
    ins=fn_ins(va)
    if not any(mn.startswith('ret') for a,s,mn,op in ins): return None
    return ins
def offsets(ins,win=8):
    res=set()
    for k,(a,s,mn,ops) in enumerate(ins):
        if mn=='mov' and ops.startswith('dword ptr [eax],') and ops.split(',')[-1].strip() in ('ebx','esi','edi','ebp','ecx','edx'):
            res.add(('reg0',ops.split(',')[-1].strip(),a))
        if mn!='lea': continue
        p=ops.split(',')
        if len(p)!=2 or '+' not in p[1]: continue
        dst=p[0].strip()
        try: imm=int(p[1].split('+')[1].strip().rstrip(']'),16)
        except: continue
        for j in range(k+1,min(k+1+win,len(ins))):
            a2,s2,mn2,ops2=ins[j]
            if mn2=='mov' and ops2.startswith('dword ptr [eax],') and ops2.split(',')[-1].strip()==dst:
                res.add((imm,dst,a2)); break
    return res
FAM=collections.defaultdict(list)
for v,col in VT.items(): FAM[COL[col]['pCHD']].append(v)
rows=[];ok=bad=0;badr=[];nq=0
for fam,vs in sorted(FAM.items()):
    mdset={COL[VT[v]]['md_'] for v in vs}
    for v in sorted(vs):
        s=SL[v]
        if not s: continue
        ins=is_qi(s[0])
        if not ins: continue
        nq+=1
        offs=offsets(ins)
        vals={o for o,_,_ in offs if isinstance(o,int)}|({0} if any(isinstance(o,str) for o,_,_ in offs) else set())
        extra=vals-mdset
        r=dict(vt=hex(v),cls=COL[VT[v]]['name'],qifn=hex(s[0]),md=COL[VT[v]]['md_'],mdset=sorted(mdset),offs=sorted(hex(x) for x in vals),extra=sorted(hex(x) for x in extra))
        rows.append(r)
        if extra: bad+=1; badr.append(r)
        else: ok+=1
print('[律V] QI 函数识别数=%d 可判视图=%d 成立=%d 违例=%d'%(nq,nq,ok,bad))
print('[正控] 0x410260:',[r for r in rows if r['qifn']=='0x410260'])
for b in badr[:12]: print('   VIOL',b['cls'],'md',b['md'],'mdset',b['mdset'],'offs',b['offs'],'extra',b['extra'])
GLOBAL_MD={COL[c]['md_'] for c in COL}
bad2=sum(1 for r in rows if {int(x,16) for x in r['offs']}-GLOBAL_MD)
print('[反控2] 全局 mdisp 判据违例=%d vs 类内违例=%d'%(bad2,bad))
json.dump(dict(nq=nq,ok=ok,bad=bad,badrows=badr[:20],alt_bad=bad2),open('_r217/m5.json','w'),indent=1)
