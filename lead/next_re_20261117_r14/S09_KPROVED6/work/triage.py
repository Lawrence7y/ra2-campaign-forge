"""
S09-KPROVED6 triage: for each remaining candidate compute
 (2) all holding RTTI tables + class names  (16) base attribution
 (4) direct call sites (from survey index) + livevt
 (3b) gear detection with entry-relative offsets (atlas-independent CFG extent)
"""
import json, sys
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT/'ra2youli'/'gamemd.exe'
SURV = ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw = EXE.read_bytes()
pe = pefile.PE(data=raw, fast_load=True); ib = pe.OPTIONAL_HEADER.ImageBase
secs = [dict(name=s.Name.rstrip(b'\0').decode('latin1'), va=ib+s.VirtualAddress,
             vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData) for s in pe.sections]
by = {s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va'] <= va < s['va']+s['rs']:
            o = s['ptr']+va-s['va']
            if o+4 <= len(raw): return o
    return None
def u32(va):
    o = va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else None
text = by['.text']; tva = text['va']; tlen = text['vs']
code = raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva <= v < tva+tlen

idx = json.load(open(SURV/'work'/'index.json'))
e2s = {int(k,16): v for k,v in idx['entry2slots'].items()}
direct = {int(k,16): v for k,v in idx['direct'].items()}
livevt = {int(k,16): v for k,v in idx['livevt'].items()}
vtables = {int(k,16): v for k,v in idx['vtables'].items()}

# atlas
ATLASP = ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
al = ATLASP.read_text(encoding='utf-8-sig').splitlines(); ah = al[0].split('\t')
atlas = {}
for l in al[1:]:
    if not l.strip(): continue
    q = l.split('\t'); q += ['']*(len(ah)-len(q)); r = dict(zip(ah,q[:len(ah)]))
    k = r['entry'].strip().upper().replace('0X','')
    try: atlas[k] = int(r['size'],0)
    except: pass

# classification (name)
CLF = SURV/'EVIDENCE'/'classification.tsv'
rows = {}
import csv
with open(CLF, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        rows[r['entry'].upper().replace('0X','')] = r

# full linear disasm of .text for CFG (skipdata)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True; md.skipdata = True
JCCS = {'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}
sz = bytearray(tlen+16); kind = bytearray(tlen+16); tgt = {}; insmap = {}
RET=1; JMP=2; JCC=3; CALL=4
for ins in md.disasm(code, tva):
    o = ins.address-tva
    if o >= len(sz): break
    sz[o] = ins.size; insmap[o] = ins
    mn = ins.mnemonic
    if mn == 'ret' or mn.startswith('ret'): kind[o]=RET
    elif mn == 'jmp':
        kind[o]=JMP
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn in JCCS:
        kind[o]=JCC
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn == 'call': kind[o]=CALL

def extent(entry, cap=8000):
    seen=set(); stack=[entry]; addrs=[]
    lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); addrs.append(a); n+=1
            if n>cap: stack=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t)
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s; continue
            a=a+s
    return lo,hi,sorted(addrs)

def analyze(entry):
    k = '%08X'%entry
    r = rows.get(k,{})
    slots = e2s.get(entry,[])
    # all distinct holding tables with class + slot
    tables = {}
    for vt,slot,cls in slots:
        tables.setdefault((vt,cls),set()).add(slot)
    dc = direct.get(entry,[])
    lv = livevt.get(entry,[])
    lo,hi,addrs = extent(entry)
    ats = atlas.get(k)
    # collect instruction text with relative offsets, flags
    shift=[]
    n_cmp=n_test=n_call=n_jcc=n_jmp_ind=n_loopback=0
    imm_m1=[]; vt_writes=[]; field_writes=set(); explicit_writes=[]
    jcc_targets=[]; call_targets=[]
    for a in addrs:
        o=a-tva; ins=insmap.get(o)
        if ins is None: continue
        rel=a-entry
        mn=ins.mnemonic; op=ins.op_str
        shift.append('%04X %s %s'%(rel,mn,op))
        if mn in JCCS:
            n_jcc+=1
            if ins.operands and ins.operands[0].type==X86_OP_IMM:
                jcc_targets.append((rel,int(ins.operands[0].imm)&0xffffffff))
        if mn=='cmp' or mn.startswith('cmp'): n_cmp+=1
        if mn=='test': n_test+=1
        if mn=='call':
            n_call+=1
            if ins.operands and ins.operands[0].type==X86_OP_IMM:
                call_targets.append((rel,int(ins.operands[0].imm)&0xffffffff))
        if mn=='jmp' and ins.operands and ins.operands[0].type!=X86_OP_IMM:
            n_jmp_ind+=1
        # backedge: any jump target <= current addr within body
        if a in tgt:
            t=tgt[o]
            if lo<=t<=a and kind[o] in (JMP,JCC): n_loopback+=1
        # -1 / sentinel compare
        if 'cmp' in mn and ('-1' in op or '0xffffffff' in op.lower()): imm_m1.append(rel)
        # writes: capstone mn starting with mov and op0 mem
        if ins.operands and ins.operands[0].type==X86_OP_MEM and (mn=='mov' or mn.startswith('mov') or mn in ('add','sub','inc','dec','and','or','xor')):
            explicit_writes.append((rel,mn,op))
            m=ins.operands[0].mem
            # count distinct displacement values >=0x8 on reg base as field writes
            if m.disp and m.disp>=8:
                field_writes.add(m.disp)
        # vtable ptr write: mov [..], imm in .rdata 0x7e/0x7f
        if ins.operands and ins.operands[0].type==X86_OP_MEM and mn=='mov' and ins.operands[1].type==X86_OP_IMM:
            v=int(ins.operands[1].imm)&0xffffffff
            if 0x7e0000<=v<0x800000: vt_writes.append((rel,v))
    return dict(k=k, entry=entry, name=r.get('name',''), slots=slots,
                tables=[[vt,c,sorted(s)] for (vt,c),s in tables.items()],
                direct=dc, livevt=lv, lo=lo, hi=hi, size=hi-lo, atlas=ats,
    addrs=addrs, nins=len(addrs), shift=shift, n_cmp=n_cmp,n_test=n_test,n_call=n_call,
    n_jcc=n_jcc,n_jmp_ind=n_jmp_ind,n_loopback=n_loopback,imm_m1=imm_m1,
    vt_writes=vt_writes, n_field=len(field_writes), field_writes=sorted(field_writes),
    explicit_writes=explicit_writes, jcc_targets=jcc_targets, call_targets=call_targets)

cands = [l.strip() for l in open(ROOT/'lead/next_re_20261117_r14/S09_KPROVED6/work/candidates.txt') if l.strip()]
out=[]
for k in cands:
    out.append(analyze(int(k,16)))
json.dump(out, open(ROOT/'lead/next_re_20261117_r14/S09_KPROVED6/work/triage.json','w'), ensure_ascii=False, indent=1)
# print compact
for r in out:
    cls = sorted({c for vt,c,s in r['tables']})
    tabdesc = ';'.join('%X:%s[%s]'%(vt,c.replace('.?AV','').replace('@@',''),','.join(map(str,s))) for vt,c,s in sorted(r['tables']))
    print('%s %-28s ins=%3d size=%4d atlas=%s | dir=%d lv=%d | jmpind=%d back=%d jcc=%d call=%d cmp_m1=%d vtW=%d fld=%d | %s'%(
        r['k'], r['name'][:28], r['nins'], r['size'], r['atlas'], len(r['direct']), len(r['livevt']),
        r['n_jmp_ind'], r['n_loopback'], r['n_jcc'], r['n_call'], len(r['imm_m1']), len(r['vt_writes']), r['n_field'], tabdesc))
