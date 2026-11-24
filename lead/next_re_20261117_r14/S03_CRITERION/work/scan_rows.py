
# -*- coding: utf-8 -*-
import json, struct, bisect
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work'
blob=open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress+base, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
SECMAP={n:(va,vs,pr,rs) for n,va,vs,pr,rs in SECS}
def sec_of(va):
    for n,va0,vs,pr,rs in SECS:
        if va0<=va<va0+min(vs,rs): return n,va0,pr,vs,rs
    return None
def rd32(va):
    s=sec_of(va)
    if not s: return None
    n,va0,pr,vs,rs=s
    return struct.unpack_from('<I', blob, pr+(va-va0))[0]
def rd16(va):
    s=sec_of(va)
    if not s: return None
    n,va0,pr,vs,rs=s
    return struct.unpack_from('<H', blob, pr+(va-va0))[0]
def cstr(va,n=160):
    s=sec_of(va)
    if not s: return None
    nme,va0,pr,vs,rs=s
    o=pr+(va-va0); e=blob.find(b'\x00',o,min(o+n,len(blob)))
    if e<0: return None
    try: return blob[o:e].decode('latin1')
    except: return None

TVA,Tvs,TPR,TRS=SECMAP['.text']; TEXT_LO=TVA; TEXT_HI=TVA+Tvs
text=blob[TPR:TPR+TRS][:Tvs]
RD_LO,RD_HI=SECMAP['.rdata'][0], SECMAP['.rdata'][0]+SECMAP['.rdata'][1]

cov=[]
for l in open(COV,encoding='utf-8').read().split('\n')[1:]:
    if not l.strip(): continue
    f=l.split('\t')
    if len(f)<8: continue
    cov.append({'entry':int(f[0],16),'hex':f[0].upper(),'sub':f[1].strip(),'name':f[2],'sem':f[3],'grade':f[4],'nsrc':f[6],'conf':f[7]})
atl={}
for l in open(ATL,encoding='utf-8').read().split('\n')[1:]:
    if not l.strip(): continue
    f=l.split('\t'); atl[int(f[0],16)]={'size':int(f[1]),'ninstr':int(f[2]),'ncallers':int(f[3]),'ncallees':int(f[4])}
atl_s=sorted(atl)
grades={r['entry']:r['grade'] for r in cov}
S03=[r for r in cov if r['sub']=='S03']
interest={r['entry'] for r in S03}

# ---- vtable inventory: dword in .rdata pointing to a COL in .rdata whose COL+0xC -> TD (name at TD+8) ----
vt_all={}
vt_hits={}
for a in range(RD_LO, RD_HI-8, 4):
    col=rd32(a)
    if col is None or not (RD_LO<=col<RD_HI): continue
    td=rd32(col+0xC)
    if td is None: continue
    nm=cstr(td+8)
    if not nm or not (nm.startswith('.?A') or nm.startswith('.?V')): continue
    vt=a+4
    slots=[]; k=0
    while k<=400:
        v=rd32(vt+4*k)
        if v is None or not (TEXT_LO<=v<TEXT_HI): break
        slots.append(v); k+=1
    if not slots: continue
    vt_all[vt]={'col':col,'td':td,'cls':nm,'nslots':len(slots)}
    for k,v in enumerate(slots): vt_hits.setdefault(v,[]).append({'cls':nm,'slot':k,'vt':vt})
print('vtables',len(vt_all),'distinct slot targets',len(vt_hits))

# ---- sweep ----
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
call_hits={}; imm_hits={}; vt_install={}   # vt -> [(site, kind, dest)]
vt_set=set(vt_all)
n_insn=0
for ins in md.disasm(text, TEXT_LO):
    n_insn+=1
    if ins.id==0: continue
    raw=text[ins.address-TEXT_LO:ins.address-TEXT_LO+ins.size]
    if ins.mnemonic=='call' and ins.size==5 and raw[0]==0xE8:
        tgt=(ins.address+5+struct.unpack_from('<i',raw,1)[0])&0xFFFFFFFF
        if tgt in interest: call_hits.setdefault(tgt,[]).append(ins.address)
    for i,op in enumerate(ins.operands):
        if op.type==X86_OP_IMM:
            if op.imm in interest and ins.mnemonic!='call':
                imm_hits.setdefault(op.imm,[]).append((ins.address, ins.mnemonic+' '+ins.op_str))
            if op.imm in vt_set:
                kind='install' if (ins.mnemonic=='mov' and ins.operands[0].type==X86_OP_MEM and ins.operands[0].mem.disp>=0x800000 and len(ins.operands)>1) else ins.mnemonic
                vt_install.setdefault(op.imm,[]).append((ins.address, ins.mnemonic+' '+ins.op_str))
print('insn',n_insn)
# live vptr install check via C7 05 pattern: mov dword ptr [imm], imm
for vt in list(vt_install):
    lst=vt_install[vt]
    vt_install[vt]=[{'site':'%08X'%s,'ins':t} for s,t in lst[:6]]

# ---- predecessor index ----
md2=Cs(CS_ARCH_X86,CS_MODE_32); md2.skipdata=True
insn_index={}
for ins in md2.disasm(text, TEXT_LO): insn_index[ins.address]=(ins.size, ins.mnemonic, ins.op_str)
baddrs=sorted(insn_index)
TERM={'ret','jmp','int3','nop','iret','hlt','ud2'}
def pred_of(a):
    i=bisect.bisect_left(baddrs,a)-1
    if i<0: return None
    p=baddrs[i]; size,mn,ops=insn_index[p]
    if p+size!=a: return None
    return (p,mn,ops)
def containing(addr):
    i=bisect.bisect_right(atl_s,addr)-1
    if i<0: return None
    e=atl_s[i]
    return e if e<=addr<e+atl[e]['size'] else None

rows=[]
for r in S03:
    e=r['entry']; body=atl.get(e)
    dc=call_hits.get(e,[])
    cl=[]
    for site in dc:
        c=containing(site); cl.append({'site':'%08X'%site,'caller':c and '%08X'%c,'grade':grades.get(c) if c else None})
    self_l=[c for c in cl if body and e<=int(c['site'],16)<e+body['size']]
    outside=[c for c in cl if c not in self_l]
    pr=pred_of(e)
    vh=vt_hits.get(e,[])
    rows.append({'hex':r['hex'],'entry':e,'grade':r['grade'],'name':r['name'],'sem':r['sem'],'nsrc':r['nsrc'],'conf':r['conf'],
      'size':body['size'] if body else None,'ninstr':body['ninstr'] if body else None,'in_atlas':body is not None,
      'n_direct':len(outside),'sites':[c['site'] for c in outside],'selfloop':len(self_l),
      'callers':outside,
      'imm_refs':[{'site':'%08X'%s,'ins':t} for s,t in imm_hits.get(e,[])],
      'n_rtti':len(vh),'rtti':[{'cls':h['cls'],'slot':h['slot'],'vt':'%08X'%h['vt'],
              'vt_installs':vt_install.get(h['vt'],[])} for h in vh][:5],
      'align16':e%16==0,'first_byte':'%02X'%text[e-TEXT_LO],
      'pred':('%08X'%pr[0],pr[1],pr[2]) if pr else None,'pred_term':(pr[1] in TERM) if pr else None,
      'inside_other':(lambda c: c is not None and c!=e)(containing(e))})
json.dump(rows,open(OUT+r'\rows.json','w'),indent=0)
json.dump({'n_vtables':len(vt_all),'n_slot_targets':len(vt_hits)},open(OUT+r'\vt_summary.json','w'))

from collections import Counter
for g in ('[已证]','[静态推断]','[未证]'):
    sub=[r for r in rows if r['grade']==g]
    print('\n==',g,len(sub))
    print(' direct>=1:',sum(1 for r in sub if r['n_direct']>0),
          ' imm:',sum(1 for r in sub if r['imm_refs']),
          ' rtti>0:',sum(1 for r in sub if r['n_rtti']>0),
          ' rtti&direct:',sum(1 for r in sub if r['n_rtti']>0 and r['n_direct']>0))
    print(' align16:',sum(1 for r in sub if r['align16']),' firstbyte:',Counter(r['first_byte'] for r in sub).most_common(6))
    print(' pred_term T/F/N:',sum(1 for r in sub if r['pred_term'] is True),sum(1 for r in sub if r['pred_term'] is False),sum(1 for r in sub if r['pred'] is None))
    print(' inside_other:',sum(1 for r in sub if r['inside_other']))
    print(' median size:', sorted([r['size'] for r in sub if r['size']])[len(sub)//2] if sub else None)
