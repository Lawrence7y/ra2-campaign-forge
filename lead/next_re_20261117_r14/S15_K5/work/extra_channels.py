from pathlib import Path
import sys,re,struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import ROOT, PE, IMAGE_BASE, read_va, off_to_va, containing_func
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,x86_const
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
EV=Path(__file__).resolve().parents[1]/'EVIDENCE'
targets=[0x006D0F00,0x006D6070,0x006E1830,0x006E4790,0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x00721270,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,0x00752460,0x00763610,0x00763690]
tset=set(targets)
# 1. YRpp exact address grep
yrpp=ROOT/'YRpp'
addr_regex=re.compile(r'(?i)(?:0x)?(?:'+'|'.join(f'{t:08X}' for t in targets)+r'|'+'|'.join(f'{t:06X}' for t in targets)+r')\b')
hits=[]
for p in sorted(yrpp.rglob('*')):
    if not p.is_file(): continue
    try: txt=p.read_text(encoding='utf-8',errors='replace')
    except Exception: continue
    for i,line in enumerate(txt.splitlines(),1):
        if addr_regex.search(line): hits.append((str(p.relative_to(ROOT)),i,line.strip()))
out=EV/'yrpp_residual_addr_matches.txt'
out.write_text(f'regex hits {len(hits)}\n'+'\n'.join(f'{p}:{i}:{line}' for p,i,line in hits)+'\n',encoding='utf-8')
print(out.name,'hits',len(hits))
# coverage names for function attribution
cov={}
with (ROOT/'lead'/'next_re_20261117_r14'/'COVERAGE'/'coverage.tsv').open('r',encoding='utf-8-sig',errors='replace') as f:
    for ln in f:
        r=ln.rstrip('\r\n').split('\t')
        if r and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()): cov[int(r[0],16)]=r[2] if len(r)>2 else ''
def nm(e): return cov.get(e,'')
# string list from already generated candidate dump
strs=[]
for ln in (EV/'strings_trigger_candidates.txt').read_text(encoding='utf-8').splitlines():
    parts=ln.split('\t',2)
    if len(parts)==3 and re.fullmatch(r'[0-9A-Fa-f]{8}',parts[0]): strs.append((int(parts[0],16),parts[1],parts[2]))
def valid_insn_refs(sva):
    needle=struct.pack('<I',sva); res=[]; pos=0; data=PE.__data__
    while True:
        i=data.find(needle,pos)
        if i<0: break
        va,sec=off_to_va(i); pos=i+1
        if sec!='.text' or va is None: continue
        found=None
        for delta in range(15,-1,-1):
            start=va-delta; code=read_va(start,32)
            if code is None: continue
            ins=next(md.disasm(code,start,1),None)
            if not ins or ins.size<=delta: continue
            refs=[]
            for op in ins.operands:
                if op.type==x86_const.X86_OP_IMM and op.imm==sva: refs.append('imm')
                if op.type==x86_const.X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp==sva: refs.append('disp')
            if refs:
                cf=containing_func(ins.address)
                found=(ins.address,ins.mnemonic+' '+ins.op_str,','.join(refs),cf)
                break
        if found: res.append(found)
    return res
for tag,pred,fn in [
    ('EVA', lambda s: bool(re.match(r'^EVA_[A-Za-z0-9_]+$',s)), EV/'eva_xrefs.txt'),
    ('INI', lambda s: s in {'Triggers','Events','Actions','Tags','Trigger','Event','Action','Tag','[Triggers]','[Events]','[Actions]','[Tags]','Waypoint','none','<none>'}, EV/'ini_key_xrefs.txt'),
]:
    lines=[]; overlap=[]; total=0
    for va,sec,s in strs:
        if not pred(s): continue
        refs=valid_insn_refs(va)
        if not refs: continue
        total+=1
        lines.append(f'===== string {va:08X} {sec} {s!r} valid_ref_sites {len(refs)} =====')
        for ins,text,refs_kind,cf in refs:
            cfs='NONE' if cf is None else f'{cf[0]:08X}+{cf[1]} name={nm(cf[0])}'
            lines.append(f'  {ins:08X}: {text} | refs={refs_kind} | contains={cfs}')
            if cf and cf[0] in tset: overlap.append((va,ins,cf[0]))
    lines.insert(0,f'{tag} strings with valid instruction xrefs: {total}; overlaps with residual target entries: {len(overlap)}')
    lines.append('overlap_list '+repr(overlap))
    fn.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(fn.name,'strings',total,'overlap',len(overlap))
# 3. residual channel matrix: direct call/jmp count from our call_xrefs file, raw dword hits already 0 from earlier scan but recompute
call_counts={t:0 for t in targets}
p=EV/'call_xrefs_residual_targets.tsv'
for ln in p.read_text(encoding='utf-8').splitlines():
    if ln.startswith('#'): continue
    r=ln.split('\t')
    if len(r)>=2:
        try: call_counts[int(r[0],16)]+=1
        except ValueError: pass
raw_counts={t:0 for t in targets}
data=PE.__data__
for t in targets:
    needle=struct.pack('<I',t); pos=0
    while True:
        i=data.find(needle,pos)
        if i<0: break
        raw_counts[t]+=1; pos=i+1
lines=['entry\tdirect_call_jmp_sites\traw_dword_pointer_hits\tin_atlas\tcoverage_name']
with (ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv').open('r',encoding='utf-8-sig',errors='replace') as f:
    atlas=set()
    for ln in f:
        r=ln.rstrip('\r\n').split('\t')
        if r and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()): atlas.add(int(r[0],16))
for t in targets:
    lines.append(f'{t:08X}\t{call_counts[t]}\t{raw_counts[t]}\t{str(t in atlas).lower()}\t{cov.get(t,"")}')
(EV/'residual_channel_matrix.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('matrix written')
