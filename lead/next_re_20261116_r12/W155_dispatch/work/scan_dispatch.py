#!/usr/bin/env python3
# W155 dispatch site discovery -- byte-level (capstone) channel.
# Produces instruction-boundary map by linear disassembly from every
# function_atlas.tsv entry (size column is DECIMAL), then scans raw .text
# for indirect call [reg+0x5C] byte patterns and reports boundary status.
# Also dumps context windows around boundary-confirmed sites and around
# a fixed set of TARGET addresses (W151 claims, BulletClass::AI).
import os, sys, re, csv, collections

ROOT = r'D:\Project\ra2-campaign-forge'
CARD = os.path.join(ROOT, r'lead\next_re_20261116_r12\W155_dispatch')
EVID = os.path.join(CARD, 'EVIDENCE')
os.makedirs(EVID, exist_ok=True)

EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
# locate .text
text = None
for s in pe.sections:
    if s.Name.rstrip(b'\0') == b'.text':
        text = s
        break
if text is None:
    raise SystemExit('no .text')
TEXT_VA = IMAGE_BASE + text.VirtualAddress
TEXT_RAW = text.PointerToRawData
TEXT_SIZE = min(text.SizeOfRawData, text.Misc_VirtualSize)
raw = open(EXE, 'rb').read()
text_bytes = raw[TEXT_RAW:TEXT_RAW+TEXT_SIZE]

def va2off(va):
    return va - TEXT_VA

def valid_va(va):
    o = va2off(va)
    return 0 <= o < len(text_bytes)

# ---- atlas ----
funcs = []
with open(ATLAS, 'r', encoding='utf-8', errors='replace') as f:
    rdr = csv.DictReader(f, delimiter='\t')
    for row in rdr:
        try:
            entry = int(row['entry'], 16)
            size = int(row['size'], 10)
        except Exception:
            continue
        funcs.append((entry, size, row))
funcs.sort()
func_at = {e:(e,s,r) for e,s,r in funcs}

# index: sorted entries for containing-function lookup
entries = [e for e,s,r in funcs]
import bisect
def containing_func(va):
    i = bisect.bisect_right(entries, va) - 1
    if i < 0: return None
    e,s,r = funcs[i]
    if va < e + max(s,1): return (e,s,r)
    return None

# ---- instruction boundary map (linear from each atlas entry) ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
insn_at = {}          # va -> (size, mnemonic, opstr, byteshex, func_entry)
insn_starts = []
func_insns = collections.defaultdict(list)  # func_entry -> list of (va,size,mnem,opstr,byteshex)
for e,s,r in funcs:
    if s <= 0 or not valid_va(e):
        continue
    code = text_bytes[va2off(e):va2off(e)+s]
    for ins in md.disasm(code, e):
        va = ins.address
        if va in insn_at:
            continue
        h = ins.bytes.hex()
        rec = (ins.size, ins.mnemonic, ins.op_str, h, e)
        insn_at[va] = rec
        insn_starts.append(va)
        func_insns[e].append((va, ins.size, ins.mnemonic, ins.op_str, h))
insn_starts.sort()
insn_start_set = set(insn_starts)
print('funcs=%d insn_map=%d text_bytes=%d imagebase=0x%x text_va=0x%x' % (
    len(funcs), len(insn_at), len(text_bytes), IMAGE_BASE, TEXT_VA))

# ---- pattern scan ----
# call near indirect, mod=01 reg=2: FF 5? disp8  (disp8=0x5C)
# mod=01 rm=4 SIB:                 FF 54 24 5C
# mod=10 reg=2 disp32:            FF 9? 5C 00 00 00
# mod=10 rm=4 SIB disp32:         FF 94 24 5C 00 00 00
pats = []
for rm in range(8):
    pats.append((bytes([0xFF, 0x50+rm, 0x5C]), 'FF5x5C'))
    pats.append((bytes([0xFF, 0x90+rm, 0x5C,0,0,0]), 'FF9x5C000000'))
pats.append((bytes([0xFF,0x54,0x24,0x5C]), 'FF54245C'))
pats.append((bytes([0xFF,0x94,0x24,0x5C,0,0,0]), 'FF94245C000000'))

hits = []
seen_hit = set()
for pat, pname in pats:
    start = 0
    while True:
        idx = text_bytes.find(pat, start)
        if idx < 0: break
        va = TEXT_VA + idx
        start = idx + 1
        key = (va, pname)
        if key in seen_hit: continue
        seen_hit.add(key)
        rec = insn_at.get(va)
        boundary = bool(rec and rec[3] == pat.hex())
        if boundary:
            f = containing_func(va)
            fentry = f[0] if f else -1
        else:
            fentry = -1
        hits.append((va, pname, pat.hex(), boundary, rec, fentry))
hits.sort()

with open(os.path.join(EVID,'bytescan_sites.tsv'),'w',encoding='utf-8') as out:
    out.write('va\tpattern\tbytes\tboundary\tinsn_size\tmnemonic\toperands\tfunc_entry\tinsn_hex\n')
    for va,pname,bhex,bdry,rec,fentry in hits:
        if rec:
            out.write('0x%08X\t%s\t%s\t%d\t%d\t%s\t%s\t%s\t%s\n' % (
                va,pname,bhex,bdry,rec[0],rec[1],rec[2],
                ('0x%08X'%fentry) if fentry>=0 else '-', rec[3]))
        else:
            out.write('0x%08X\t%s\t%s\t%d\t-\t-\t-\t-\t-\n' % (va,pname,bhex,bdry))

bdry_hits = [h for h in hits if h[3]]
nonbdry = [h for h in hits if not h[3]]
with open(os.path.join(EVID,'bytescan_stats.txt'),'w',encoding='utf-8') as out:
    out.write('W155 byte-scan stats\n')
    out.write('image_base=0x%08X text_va=0x%08X text_size=%d\n' % (IMAGE_BASE,TEXT_VA,TEXT_SIZE))
    out.write('atlas_funcs=%d mapped_instructions=%d\n' % (len(funcs),len(insn_at)))
    out.write('raw_pattern_hits=%d boundary_confirmed=%d non_boundary=%d\n' % (len(hits),len(bdry_hits),len(nonbdry)))
    bypat = collections.Counter(h[1] for h in hits)
    for k,v in sorted(bypat.items()): out.write('pattern %s: %d\n' % (k,v))
    out.write('\nboundary-confirmed sites grouped by function:\n')
    byfn = collections.Counter(h[5] for h in bdry_hits)
    for fe,cnt in sorted(byfn.items()):
        r = func_at.get(fe)
        out.write('func 0x%08X size=%d n_instr=%d call5c_sites=%d\n' % (
            fe, r[1] if r else -1, len(func_insns.get(fe,[])), cnt))

# ---- context dump around every boundary-confirmed site (+/- 18 insns) ----
def dump_window(out, va, before=18, after=18, label=''):
    f = containing_func(va)
    if not f:
        out.write('--- %s @0x%08X : NO CONTAINING ATLAS FUNCTION ---\n' % (label,va)); return
    fe,fs,row = f
    lst = func_insns.get(fe,[])
    idx = next((i for i,x in enumerate(lst) if x[0]==va), None)
    if idx is None:
        out.write('--- %s @0x%08X : not in linear insn map of func 0x%08X ---\n' % (label,va,fe)); return
    out.write('--- %s @0x%08X in func 0x%08X size=%d n_instr=%d ---\n' % (label,va,fe,fs,len(lst)))
    for x in lst[max(0,idx-before):min(len(lst),idx+after+1)]:
        mark = '>>' if x[0]==va else '  '
        out.write('%s 0x%08X  %-24s %s  ; %s\n' % (mark,x[0],x[2],x[3],x[4]))
    out.write('\n')

with open(os.path.join(EVID,'bytescan_context.txt'),'w',encoding='utf-8') as out:
    for va,pname,bhex,bdry,rec,fentry in bdry_hits:
        dump_window(out, va, 20, 20, 'CALL5C %s' % pname)

# ---- targeted windows ----
TARGETS = [0x55B8C3,0x55B8ED,0x55B8F0,0x55B912,0x55B960,0x4666E0,0x55D360,0x48CCC0]
with open(os.path.join(EVID,'bytescan_targets.txt'),'w',encoding='utf-8') as out:
    for t in TARGETS:
        out.write('===== TARGET 0x%08X =====\n' % t)
        f = containing_func(t)
        out.write('containing_func=%s\n' % (('0x%08X size=%d n_instr=%d'%(f[0],f[1],len(func_insns.get(f[0],[])))) if f else 'NONE'))
        rec = insn_at.get(t)
        out.write('insn_at=%s\n' % (('%s %s ; %s size=%d'%(rec[1],rec[2],rec[3],rec[0])) if rec else 'NONE'))
        if f:
            lst = func_insns.get(f[0],[])
            # dump from function entry for small funcs, else around target
            if len(lst) <= 80:
                for x in lst:
                    out.write('%s 0x%08X  %-24s %s  ; %s\n' % ('>>' if x[0]==t else '  ',x[0],x[2],x[3],x[4]))
            else:
                idx = next((i for i,x in enumerate(lst) if x[0]==t), None)
                if idx is None:
                    out.write('(target not in linear map)\n')
                else:
                    for x in lst[max(0,idx-30):min(len(lst),idx+30)]:
                        out.write('%s 0x%08X  %-24s %s  ; %s\n' % ('>>' if x[0]==t else '  ',x[0],x[2],x[3],x[4]))
        out.write('\n')

print('wrote', os.path.join(EVID,'bytescan_sites.tsv'))
print('boundary hits=%d, nonboundary=%d' % (len(bdry_hits),len(nonbdry)))
