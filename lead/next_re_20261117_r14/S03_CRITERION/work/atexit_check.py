
# -*- coding: utf-8 -*-
# 错源㉓ 检查: atexit 注册集 + vt install site 分类
import json,struct,bisect,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_IMM,X86_OP_MEM
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
SEC={}
for s in pe.sections: SEC[s.Name.rstrip(b'\x00').decode('latin1')]=(s.VirtualAddress+base,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData)
TVA,Tvs,TPR,TRS=SEC['.text']; TL,TH=TVA,TVA+Tvs; text=blob[TPR:TPR+TRS][:Tvs]
atl={}
for l in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8').read().split('\n')[1:]:
    if not l.strip():continue
    f=l.split('\t'); atl[int(f[0],16)]=int(f[1])
as_=sorted(atl)
def containing(a):
    i=bisect.bisect_right(as_,a)-1
    if i<0:return None
    e=as_[i]
    return e if e<=a<e+atl[e] else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
ins=list(md.disasm(text,TL))
print('insns',len(ins))
# atexit: push imm32 ; call 0x7C978A
atexit=set(); ate_sites=[]
for i in range(len(ins)-1):
    a=ins[i]; b=ins[i+1]
    if a.mnemonic=='push' and len(a.operands)==1 and a.operands[0].type==X86_OP_IMM and b.mnemonic=='call':
        raw=text[b.address-TL:b.address-TL+5]
        if len(raw)==5 and raw[0]==0xE8:
            t=(b.address+5+struct.unpack_from('<i',raw,1)[0])&0xFFFFFFFF
            if t==0x7C978A:
                atexit.add(a.operands[0].imm); ate_sites.append((a.address,a.operands[0].imm))
print('atexit registrations',len(atexit),'sites',len(ate_sites))
json.dump({'n_atexit':len(atexit),'sample':[('%08X'%s,'%08X'%v) for s,v in ate_sites[:8]]},open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\atexit.json','w'),indent=1)
rows=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\rows.json'))
stat={'live_only':0,'dead_only':0,'mixed':0,'none':0}
out={}
for r in rows:
    if not r['rtti']: stat['none']+=1; continue
    verdicts=[]
    for h in r['rtti']:
        insts=h['vt_installs']
        fn=[containing(int(x['site'],16)) for x in insts]
        isdead=[f in atexit for f in fn if f]
        glob_=[x for x in insts if x['ins'].startswith('mov dword ptr [0x')]
        if any(not d for d in isdead) or glob_: verdicts.append('live')
        else: verdicts.append('dead')
    if all(v=='live' for v in verdicts): stat['live_only']+=1; lab='live'
    elif all(v=='dead' for v in verdicts): stat['dead_only']+=1; lab='dead'
    else: stat['mixed']+=1; lab='mixed'
    out[r['hex']]=lab
print(json.dumps(stat))
json.dump(out,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\liveness.json','w'),indent=0)
# per-grade
from collections import Counter
print('liveness by grade:',Counter((r['grade'],out.get(r['hex'],'none')) for r in rows))
