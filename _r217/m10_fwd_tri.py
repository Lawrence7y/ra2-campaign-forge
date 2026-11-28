# -*- coding: utf-8 -*-
"""R217 m10：转发桩三口径对照，裁定 card A 报 0 与主会话报 76 的分歧。
口径1（主会话 m7）：五条指令 mov eax,[esp+4] / mov R,[eax-4] / lea R,[eax-4] / call [R+K] / ret imm
口径2（card A）：要求五个槽位的寄存器名严格一致（如 eax/edx/ecx 各就各位）=> 报 0 的原因是 card A 用了 eax/edx
                 固定名而真实字节是 mov edx,[eax-4] / lea ecx,[eax-4]。
口径3（放宽）：只要求 mov 与 lea 的基址寄存器同为 eax 且偏移 -4，call 走 [reg+K]，ret 带 imm。
正控：0x410210 必须命中；反控：把 -4 改成 -8 后命中应为 0。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; TLO=t['lo']; THI=TLO+t['rawsize']
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
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
def nslots(vt,cap=65536):
    n=0
    while n<cap and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
ALL={v:nslots(v) for v in VT}
def ins5(va):
    o=P.r2o(va); return list(md.disasm(P.RAW[o:o+32],va))[:5]
def kit(va,disp='- 4'):
    ins=ins5(va)
    if len(ins)<5: return None
    m=[i.mnemonic for i in ins]
    if m[0]!='mov' or '[esp + 4]' not in ins[0].op_str: return None
    if m[1]!='mov' or disp not in ins[1].op_str or '[eax' not in ins[1].op_str: return None
    if m[2]!='lea' or disp not in ins[2].op_str or '[eax' not in ins[2].op_str: return None
    if m[3]!='call' or 'dword ptr [' not in ins[3].op_str: return None
    import re as _re
    _mm=_re.search(r'\+ (0x[0-9a-f]+)',ins[3].op_str)
    if not _mm: return None
    if not m[4].startswith('ret') or not ins[4].op_str: return None
    r1=ins[1].op_str.split(',')[0].strip(); r2=ins[2].op_str.split(',')[0].strip()
    reg=ins[3].op_str.split('[')[1].split('+')[0].strip()
    if reg!=r1: return None
    K=int(_mm.group(1),16)
    return dict(dst_mov=r1,dst_lea=r2,K=K,ret=ins[4].op_str,bytes=b''.join(i.bytes for i in ins).hex(),
                addrs=[i.address for i in ins])
hits={}; slots=collections.Counter(); tabs=collections.Counter()
for v in VT:
    for i in range(ALL[v]):
        fn=P.dw(v+4*i)
        if fn in hits: 
            pass
        r=kit(fn)
        if r: hits.setdefault(fn,r); slots[i]+=1; tabs[fn]+=1
print('[口径3] 命中函数=%d 槽位=%d'%(len(hits),sum(slots.values())))
print('  槽序号分布',dict(sorted(slots.items())))
print('  K 分布',dict(collections.Counter(r['K'] for r in hits.values())))
print('  ret 分布',dict(collections.Counter(r['ret'] for r in hits.values())))
print('  寄存器组合',dict(collections.Counter((r['dst_mov'],r['dst_lea']) for r in hits.values())))
print('[正控] 0x410210:',hits.get(0x410210))
print('[反控] -8 判据命中数=',len({fn for v in VT for i in range(ALL[v]) if kit(P.dw(v+4*i),'- 8')}))
# 口径1：严格要求 eax/edx/ecx（card A 的假设）
n_strict=0
for fn in hits:
    ins=ins5(fn)
    ops=[i.op_str for i in ins]
    if ops[0]=='eax, dword ptr [esp + 4]' and ops[1]=='edx, dword ptr [eax - 4]' and ops[2]=='ecx, [eax - 4]': n_strict+=1
print('[口径1-cardA] 严格 eax/edx/ecx 命名命中=%d => 证实 card A 的 0 是命名假设错，不是桩不存在'%n_strict)
json.dump(dict(hits=len(hits),slots=dict(slots),K={hex(k):v for k,v in collections.Counter(r['K'] for r in hits.values()).items()},
  regs={str(k):v for k,v in collections.Counter((r['dst_mov'],r['dst_lea']) for r in hits.values()).items()},
  strict=n_strict,sample={'vt_addr':hex(0x410210),'dst_mov':hits[0x410210]['dst_mov'],'dst_lea':hits[0x410210]['dst_lea'],
   'K':hits[0x410210]['K'],'ret':hits[0x410210]['ret'],'bytes':hits[0x410210]['bytes'],'addrs':hits[0x410210]['addrs']},
  regs_all={str(k):v for k,v in collections.Counter((r['dst_mov'],r['dst_lea']) for r in hits.values()).items()},
  ret_all=dict(collections.Counter(r['ret'] for r in hits.values()))),
  open('_r217/m10.json','w'),indent=1)
