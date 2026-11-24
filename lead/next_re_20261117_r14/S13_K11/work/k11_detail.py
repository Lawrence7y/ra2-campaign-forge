# -*- coding: utf-8 -*-
# Second-pass evidence: full bodies, vtable slot dumps, occurrence context, contract features.
import json, os, struct
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
A = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ANALYSIS.json'),'r',encoding='utf-8'))
pe=pefile.PE(EXE,fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    n=s.Name.rstrip(bytes([0])).decode('ascii','replace')
    va=IB+s.VirtualAddress
    secs.append((n,va,va+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
def va2off(va):
    for n,a,b,pr,rs in secs:
        if a<=va<b:
            o=pr+(va-a)
            if o<len(raw): return o
    return None
def rb(va,n):
    o=va2off(va); return raw[o:o+n] if o is not None else b''
def rd(va):
    b=rb(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def cs(va,m=300):
    o=va2off(va)
    if o is None: return None
    e=raw.find(bytes([0]),o,o+m)
    if e<0:e=o+m
    return raw[o:e].decode('ascii','replace')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def disasm_full(entry,maxins=70):
    code=rb(entry,400); out=[]
    for insn in md.disasm(code,entry):
        if insn.mnemonic.startswith('.'):
            out.append({"addr":insn.address,"bytes":insn.bytes.hex(),"mn":insn.mnemonic,"op":insn.op_str});
            continue
        out.append({"addr":insn.address,"bytes":insn.bytes.hex(),"mn":insn.mnemonic,"op":insn.op_str})
        # stop at the LAST ret: only if next bytes are padding (0xCC or 0x90) or end of maxins
        if insn.mnemonic.startswith('ret') and len(out)>=8:
            nxt=rb(insn.address+insn.size,8)
            if all(b in (0xCC,0x90) for b in nxt[:4]): break
    return out[:maxins]

rows=A['rows']
out={"rows":{},"dispatch_anchors":{}}
for e,info in rows.items():
    va=int(e,16); slot=info['slot']
    body=disasm_full(va)
    feats={
      'or_eax_m1':[], 'ret4':[], 'call_free':[], 'writes':[], 'cmp_eax_m1':[], 'loop_back':[],
    }
    for b in body:
        ad=hex(b['addr']); mn=b['mn']; op=b['op']
        if 'or eax, -1' in op or 'or eax,0xffffffff' in op: feats['or_eax_m1'].append(ad)
        if mn.startswith('ret') and '4' in op: feats['ret4'].append(ad)
        if mn=='call' and op.startswith('0x7c8b3d'): feats['call_free'].append(ad)
        if mn.startswith('mov') and 'ptr [esi' in op or (mn.startswith('mov') and 'ptr [eax' in op):
            feats['writes'].append(ad+' '+mn+' '+op)
        if 'cmp eax, -1' in op: feats['cmp_eax_m1'].append(ad)
        if mn.startswith('j') and op.startswith('0x') and int(op,16)<b['addr']: feats['loop_back'].append(ad+' '+op)
    # vtable dumps
    vtdump=[]
    for v in info['vtables']:
        vt=int(v['vt'],16)
        slots=[]
        for i in range(8):
            d=rd(vt+i*4)
            slots.append((hex(vt+i*4), hex(d) if d is not None else None))
        # decode each slot's RTTI if slot function also appears in another valid vtable? skip
        vtdump.append({"vt":v['vt'],"name":v['name'],"td":v['td'],"col":v['col'],"slots":slots,
                       "vt_minus4":hex(rd(vt-4)) if rd(vt-4) is not None else None})
    # all occurrences with 3-dword context, and whether they form valid RTTI vtables at ANY slot 0..7
    occ=[]
    for hx in info['occurrences']:
        hv=int(hx,16)
        ctx=[]
        for k in range(-2,3):
            d=rd(hv+k*4)
            ctx.append([hex(hv+k*4),hex(d) if d is not None else None])
        valid_slots=[]
        for sl in range(0,8):
            vt=hv-sl*4
            col=rd(vt-4)
            if col is None: continue
            if rd(col)!=0: continue
            td=rd(col+0xC)
            if td is None: continue
            nm=cs(td+8)
            if nm and nm.startswith('.?A'): valid_slots.append((sl,hex(vt),nm))
        occ.append({"hit":hx,"ctx":ctx,"valid_rtti_slots":valid_slots})
    out['rows'][e]={"slot":slot,"kind":info['kind'],"body":body,"features":feats,
                    "vtdump":vtdump,"occurrences_context":occ,
                    "direct_calls":info['direct_calls'],"installs":info['installs']}

# verify dispatch anchors 0x4386AB / 0x43942B : bytes around
for a in (0x4386AB,0x43942B):
    out['dispatch_anchors'][hex(a)]=[{"addr":hex(i.address),"bytes":i.bytes.hex(),"mn":i.mnemonic,"op":i.op_str}
        for i in md.disasm(rb(a-16,48),a-16) if not i.mnemonic.startswith('.')]

p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'EVIDENCE_DETAIL.json')
open(p,'w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
print('WROTE',p)
for e,r in out['rows'].items():
    print('==',e,r['kind'],'slot',r['slot'])
    print('  feats:',json.dumps(r['features'],ensure_ascii=False)[:600])
    print('  n_body',len(r['body']),'last5',[(hex(b['addr']),b['mn'],b['op']) for b in r['body'][-5:]])
    for v in r['vtdump']:
        print('  VT',v['vt'],v['name'])
        print('    slots',v['slots'])
    print('  occ_count',len(r['occurrences_context']))
    for o in r['occurrences_context']:
        if o['valid_rtti_slots']: print('    occ',o['hit'],'slots',o['valid_rtti_slots'][:4])
print('anchors:',json.dumps(out['dispatch_anchors'],ensure_ascii=False)[:1200])
