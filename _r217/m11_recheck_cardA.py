# -*- coding: utf-8 -*-
"""R217 m11：§2.12 规则 D —— 主会话独立复算 card A 的三条关键结论。
C1: COL 的 +0x14 是否等于自身（card A 报：不等，故 self 筛选得 0）。
C2: QI 0x410260 的 IID 指针来自原始 esp+8、输出指针来自原始 esp+0xC（card A 报）。
C3: COL 计数 1203(cardA) vs 1214(主会话/cardB) 的差异来源。
每条给正控与反控。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
# C1: 用 pTD 名筛选 COL，然后看 +0x14
COL={}; self_ok=0; self_bad=0; selfvals=collections.Counter()
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-6):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        a=base+4*k
        COL[a]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],self=w[k+5],name=nm.decode('latin1'))
        if w[k+5]==a: self_ok+=1
        else: self_bad+=1; selfvals[w[k+5]]+=1
print('[C1] COL 候选=%d   +0x14==自身:%d   !=自身:%d'%(len(COL),self_ok,self_bad))
print('     不等时 +0x14 取值 top6:',[(hex(k),v) for k,v in selfvals.most_common(6)])
print('[C1-正控] 0x7fb118 的 +0x14 =',hex(P.dw(0x7fb118+0x14)),'(自身=%s)'%(P.dw(0x7fb118+0x14)==0x7fb118))
print('[C1-反控] 若按 self==COL 筛选，可用 COL 数 =',sum(1 for a in COL if COL[a]['self']==a),'=> card A 报 0 成立' if sum(1 for a in COL if COL[a]['self']==a)==0 else '=> card A 报错')
# C2: QI esp 跟踪（严格按 push/pop 累计）
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
o=P.r2o(0x410260); ins=list(md.disasm(P.RAW[o:o+0x90],0x410260))
delta=0; reads=[]
for i in ins:
    op=i.op_str
    if i.mnemonic=='push': delta+=4
    elif i.mnemonic=='pop': delta-=4
    if i.mnemonic=='mov' and 'dword ptr [esp +' in op:
        # 源在栈上
        x=int(op.split('[esp +')[1].split(']')[0].strip(),16)
        reads.append((hex(i.address),x,x+delta,i.mnemonic+' '+op))
print('[C2] 栈读点（X=指令内偏移, delta=push 累计, 原 esp 偏移 = X+delta）:')
for r in reads: print('     %s instr_disp=%#x push_delta=%d => 原 esp+%#x   %s'%(r[0],r[1],r[2]-r[1],r[2],r[3]))
print('[C2-结论] IID 读点原 esp+%#x（cardA 报 8）; 输出指针原 esp+%#x（cardA 报 0xc）'%(reads[1][2],reads[0][2]))
# C3: 计数差
def cnt(require_pchd_valid, require_self):
    n=0; seen=set()
    for sn in ('.rdata','.data'):
        w,base=words(sn)
        for k in range(len(w)-6):
            if w[k]>2 or w[k+2]!=0: continue
            if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
            nm=P.cstr(w[k+3]+8,512)
            if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
            a=base+4*k
            if a in seen: continue
            if require_pchd_valid and P.where(w[k+4])!='.rdata': continue
            if require_self and w[k+5]!=a: continue
            seen.add(a); n+=1
    return n
print('[C3] 宽松(仅 pTD 名)=%d   加 pCHD 段校验=%d   加 self 校验=%d'%(cnt(False,False),cnt(True,False),cnt(False,True)))
# card A 说 1203 (chd_ok) 且 per-section .rdata 1203；card B/主会话 1214
print('[C3-说明] 差额 = 落在 .data 段的 COL 记录（主会话在 .rdata+.data 两段都扫）')
nrd=sum(1 for a in COL if P.where(a)=='.rdata'); nda=len(COL)-nrd
print('    .rdata COL=%d   .data COL=%d  合计=%d'%(nrd,nda,len(COL)))
json.dump(dict(col=len(COL),self_ok=self_ok,self_bad=self_bad,
  self_top=[[hex(k),v] for k,v in selfvals.most_common(6)],
  iid_orig_esp=reads[1][2],ppv_orig_esp=reads[0][2],
  c3=[cnt(False,False),cnt(True,False),cnt(False,True)],rdata=nrd,data=nda),open('_r217/m11.json','w'),indent=1)
