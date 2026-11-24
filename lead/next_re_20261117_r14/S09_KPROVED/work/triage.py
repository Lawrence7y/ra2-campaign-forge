#!/usr/bin/env python3
"""Quick triage of S09 has4_strict=1 candidates: verify RTTI ② chain and body ③b features.
Read-only on target. Writes only inside S09_KPROVED/work.
"""
import csv, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_SKIPDATA_SETUP
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
CLASS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\work\triage.txt'

pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
SECTIONS = [(s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def rva2off(rva):
    for va, vsz, praw, rawsz in SECTIONS:
        if va <= rva < va + max(vsz, rawsz):
            off = praw + (rva - va)
            if off < len(pe.__data__):
                return off
    return None

def va2off(va):
    return rva2off(va - IMAGE_BASE)

def read_u32(va):
    o = va2off(va)
    if o is None or o + 4 > len(pe.__data__):
        return None
    return struct.unpack_from('<I', pe.__data__, o)[0]

def read_cstr(va, maxlen=120):
    o = va2off(va)
    if o is None:
        return None
    data = pe.__data__
    end = data.find(b'\x00', o, min(o+maxlen, len(data)))
    if end < 0:
        return None
    try:
        return data[o:end].decode('ascii')
    except UnicodeDecodeError:
        return None

def rtti(vt_va, slot, entry):
    """Return (name, ok) where ok means vt[slot]==entry and chain readable."""
    col = read_u32(vt_va - 4)
    if col is None or col == 0:
        return ('<COL_UNREADABLE>', False)
    td = read_u32(col + 0xC)
    if td is None or td == 0:
        return ('<TD_UNREADABLE>', False)
    name = read_cstr(td + 8)
    if not name or not (name.startswith('.?AV') or name.startswith('.?AU')):
        return ('<NAME_BAD:%r>' % name, False)
    slotval = read_u32(vt_va + slot*4)
    ok = (slotval == entry)
    return (name, ok)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

rows = []
with open(CLASS, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['subsystem']=='S09' and r['has4_strict']=='1':
            rows.append(r)

def body_features(entry, hi):
    lo = int(entry,16)
    hi = int(hi,16) if hi else lo+64
    if hi <= lo or hi-lo > 8000:
        hi = lo+8000
    o = va2off(lo)
    if o is None:
        return None
    code = pe.__data__[o:o+(hi-lo)]
    insns = list(md.disasm(code, lo))
    n = len(insns)
    e8 = 0; jcc=0; back=0; indjmp=0; scales=0; cmps=0; negeax=0
    for ins in insns:
        m = ins.mnemonic
        if m=='call' and ins.bytes and ins.bytes[0]==0xE8:
            e8+=1
        if m.startswith('j') and m not in ('jmp',):
            jcc+=1
            if ins.operands and ins.operands[0].type==X86_OP_IMM:
                if ins.operands[0].imm < ins.address:
                    back+=1
        if m=='jmp' and ins.operands and ins.operands[0].type==X86_OP_MEM:
            indjmp+=1
            if ins.operands[0].mem.scale in (2,4,8):
                scales+=1
        if m.startswith('cmp'):
            cmps+=1
        if m in ('sbb','or') and 'eax' in ins.op_str:
            negeax+=1
    return dict(n=n,e8=e8,jcc=jcc,back=back,indjmp=indjmp,scales=scales,cmps=cmps,negeax=negeax)

with open(OUT,'w',encoding='utf-8') as f:
    f.write('entry\thas2rtti\tname_class\trtti_ok\trtti_name\tslot\tvt\tdirout\tsize\tbodyn\te8\tjcc\tback\tindjmp\tscale4\tcmps\tnegeax\n')
    for r in rows:
        entry=int(r['entry'],16)
        slot=int(r['rtti_slot']) if r['rtti_slot'] else -1
        vt=r['rtti_vt']
        nm=''; ok=False
        if vt and slot>=0:
            try:
                nm,ok=rtti(int(vt,16),slot,entry)
            except Exception as e:
                nm='ERR:'+str(e)
        bf=body_features(r['entry'], r['ext_hi'])
        f.write('%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
            r['entry'], r['has2_rtti'], r['name'], '1' if ok else '0', nm,
            slot, vt, r['n_direct_out'], r['atlas_size'],
            bf['n'] if bf else 'NA', bf['e8'] if bf else 'NA', bf['jcc'] if bf else 'NA',
            bf['back'] if bf else 'NA', bf['indjmp'] if bf else 'NA', bf['scales'] if bf else 'NA',
            bf['cmps'] if bf else 'NA', bf['negeax'] if bf else 'NA'))
print('WROTE', OUT)
print('rows', len(rows))
