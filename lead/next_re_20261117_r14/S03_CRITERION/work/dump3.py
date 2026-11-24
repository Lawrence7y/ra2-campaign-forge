
# -*- coding: utf-8 -*-
import json,struct,sys,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob=open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
SEC={}
for s in pe.sections: SEC[s.Name.rstrip(b'\x00').decode('latin1')]=(s.VirtualAddress+base,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData)
TVA,Tvs,TPR,TRS=SEC['.text']; TL,TH=TVA,TVA+Tvs; text=blob[TPR:TPR+TRS][:Tvs]
def sec_of(va):
    for n,(va0,vs,pr,rs) in SEC.items():
        if va0<=va<va0+min(vs,rs): return (n,va0,pr,vs,rs)
    return None
def rd32(va):
    s=sec_of(va)
    if not s: return None
    n,va0,pr,vs,rs=s
    return struct.unpack_from('<I',blob,pr+(va-va0))[0]
def cstr(va,n=200):
    s=sec_of(va)
    if not s: return None
    nme,va0,pr,vs,rs=s
    o=pr+(va-va0); e=blob.find(b'\x00',o,min(o+n,len(blob)))
    if e<0: return None
    return blob[o:e].decode('latin1')
rows={r['hex']:r for r in json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\rows.json'))}
atl={}
for l in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8').read().split('\n')[1:]:
    if not l.strip(): continue
    f=l.split('\t'); atl[int(f[0],16)]=int(f[1])
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
targets=sys.argv[1:]
out=[]
for hx in targets:
    e=int(hx,16); size=atl.get(e); r=rows.get(hx)
    body=text[e-TL:e-TL+size] if size else b''
    dis=list(md.disasm(body,e)) if size else []
    out.append('='*100)
    out.append(f'### {hx}  grade={r["grade"]}  name={r["name"]}  size={size}  ninstr={len(dis)}')
    out.append(f'sem: {r["sem"]}')
    out.append(f'pred: {r["pred"]}  align16={r["align16"]}  first_byte={r["first_byte"]}  bytes: {body[:16].hex(" ")}')
    rt=r['rtti']
    if rt:
        for x in rt:
            vt=int(x['vt'],16); col=rd32(vt-4); td=rd32(col+0xC) if col else None
            out.append(f'RTTI: vt={x["vt"]} vt-4(COL)={col and hex(col)} COL+0xC(TD)={td and hex(td)} TD+8 name={cstr(td+8) if td else None} slot={x["slot"]} -> vt[slot]={rd32(vt+4*x["slot"]) and hex(rd32(vt+4*x["slot"]))}')
            out.append(f'      vt install sites: {json.dumps(x["vt_installs"])}')
    else:
        out.append('RTTI: none (no vtable slot holds this entry)')
    out.append(f'direct sites ({r["n_direct"]}):')
    for c in r['callers']:
        s=int(c['site'],16); raw=text[s-TL:s-TL+5]
        rel=struct.unpack_from('<i',raw,1)[0]; tgt=(s+5+rel)&0xFFFFFFFF
        ok='OK' if tgt==e else 'MISMATCH'
        out.append(f'   site={c["site"]} bytes={raw.hex(" ")} rel32={rel} site+5+rel={hex(tgt)} {ok}  caller={c["caller"]} grade={c["grade"]}')
    if r['imm_refs']: out.append('imm refs: '+json.dumps(r['imm_refs']))
    out.append(f'--- disasm ({len(dis)} insns) ---')
    for ins in dis[:96]:
        out.append(f'  {ins.address:08X}  {ins.bytes.hex(" "):<20} {ins.mnemonic} {ins.op_str}')
    if len(dis)>24: out.append(f'  ... ({len(dis)-24} more)')
    out.append('')
open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\EVIDENCE\disasm_sample.txt','a',encoding='utf-8').write('\n'.join(out)+'\n')
print('\n'.join(out))
