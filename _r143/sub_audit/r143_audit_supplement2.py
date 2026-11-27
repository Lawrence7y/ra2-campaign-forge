#!/usr/bin/env python3
"""R143 复核第三件：修正版 ctor->load->dispatch 同寄存器链；负位移 dword 装载取证；vt[+disp] 落点分析。"""
import re, json, struct, collections, random
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P = 'ra2bench/gamemd.exe'; DATA = open(P,'rb').read()
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
SECS=[dict(name=s.Name.decode().rstrip('\x00'),va=s.VirtualAddress,vs=s.Misc_VirtualSize,
           raw=s.PointerToRawData,rs=s.SizeOfRawData) for s in pe.sections]
T=[s for s in SECS if s['name']=='.text'][0]
def va2off(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']):
            d=va-lo; return s['raw']+d if d<s['rs'] else None
def rd(va,l):
    o=va2off(va); return None if o is None else DATA[o:o+l]
def dw(va):
    b=rd(va,4); return None if b is None else struct.unpack('<I',b)[0]
def sec_of(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']): return s['name']
def build_vtset():
    pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@'); TDs={}
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for m in pat.finditer(blob):
                S=IB+s['va']+m.start(); v=dw(S-8)
                if v is not None and dw(S-4)==0 and sec_of(v) in ('.data','.rdata'): TDs[S-8]=1
    td=set(TDs); COL=set()
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in td:
                    c=IB+s['va']+i*4-12
                    if dw(c)==0 and dw(c+12)==v and dw(c+16)!=0: COL.add(c)
    V=set()
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in COL:
                    vt=IB+s['va']+i*4+4
                    if dw(vt-4)==v: V.add(vt)
    return V
VTS=build_vtset()
GEN=('eax','ebx','ecx','edx','esi','edi')
SZ=('byte','word','dword','qword')
MEM=re.compile(r'^(?:(%s) ptr )?\[(.+)\]$'%'|'.join(SZ))
def pm(s):
    m=MEM.match(s or '')
    if not m: return None
    toks=[t for t in re.split(r'\+',re.sub(r'\s+','',m.group(2)).replace('-','+-')) if t]
    b=i=None; sc=1; d=0
    for t in toks:
        if '*' in t:
            r,c=t.split('*'); i,sc=r.strip(),int(c,0)
        elif re.fullmatch(r'[a-z]{2,3}',t):
            if b is None: b=t
            else: i,sc=t,1
        else:
            try: d+=int(t,0)
            except ValueError: return None
    return m.group(1),b,i,sc,d
IMM=re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
def iv(t): return (int(t,16) if t.lstrip('-').startswith('0x') else int(t))&0xFFFFFFFF
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
def sweep(chunk=32768):
    off=T['raw']; end=T['raw']+T['rs']
    while off<end:
        blob=DATA[off:min(off+chunk,end)]
        base=IB+(T['va']+(off-T['raw'])); cons=0
        for a,sz,mn,op in md.disasm_lite(blob,base):
            d=a-base
            if d+sz>len(blob): break
            cons=d+sz; yield a,sz,mn,op
        off+=cons if cons else 1
KILL={'mov','movzx','movsx','lea','pop','bswap','lods'}
links=[]; link_samples=[]
chain={}   # reg -> (store_idx, base_reg, vt, load_idx)
neg_load=collections.Counter(); neg_load_s=[]
disp_at_dispatch=collections.Counter()
vt_hit=collections.Counter()
idx=0
for a,sz,mn,op in sweep():
    if not op: idx+=1; continue
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',op)]
    mems=[pm(o) for o in ops]; mems=[m for m in mems if m]
    # 先做派发判定（用当前 chain 状态）
    if mn in ('call','jmp') and len(ops)==1 and mems and mems[0][0]=='dword' and mems[0][1] in GEN:
        b=mems[0][1]; d=mems[0][4]; disp_at_dispatch[d]+=1
        if b in chain:
            st,lb,vt,li=chain[b]
            links.append((a,b,d,lb,vt));
            if len(link_samples)<12: link_samples.append([hex(a),op,hex(vt),lb,hex(li),d])
    # 状态更新：先 kill 再 store/load（同一指令只有一个目标寄存器）
    if ops and ops[0] in GEN and mn in KILL:
        chain.pop(ops[0],None)
    if mn=='mov' and len(ops)==2:
        m1=pm(ops[0]); m2=pm(ops[1])
        if m1 and m1[0]=='dword' and m1[1] in GEN and m1[2] is None and m1[4]==0 and IMM.match(ops[1]):
            v=iv(ops[1])
            if v in VTS: chain[m1[1]]=(idx,m1[1],v,idx)
        if m2 and m2[0]=='dword' and ops[0] in GEN:
            src=m2[1]
            if src in chain and m2[4]==0:
                st,lb,vt,li=chain[src]
                if idx-li<=60: chain[ops[0]]=(st,lb,vt,idx)  # disp==0 only
                else: chain.pop(ops[0],None)
            else:
                chain.pop(ops[0],None)
            # 负位移 dword 装载取证
            if m2[4]<0:
                neg_load[(m2[1],m2[4])]+=1
                if len(neg_load_s)<8: neg_load_s.append([hex(a),op,m2[1],m2[4]])
    idx+=1
# vt[+disp] 落点：对 812 个 slot0 派发点，其 +disp 在 vt 表内是否同样落在 .text
slot_targets=0; slot_ok=0
for vt in VTS:
    t=dw(vt+0x48)
    if t is not None and sec_of(t)=='.text': slot_targets+=1
res={
 'ctor_to_dispatch_links': len(links),
 'ctor_link_samples': link_samples,
 'dispatch_disp_hist_top10': disp_at_dispatch.most_common(10),
 'neg_disp_dword_loads_total': sum(neg_load.values()),
 'neg_disp_dword_load_examples': neg_load_s,
 'neg_disp_dword_load_top': [[k[0],k[1],v] for k,v in neg_load.most_common(8)],
 'vt48_text_targets': slot_targets, 'vt_total': len(VTS),
}
json.dump(res,open('_r143/sub_audit/audit_supplement2.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False,indent=1))
