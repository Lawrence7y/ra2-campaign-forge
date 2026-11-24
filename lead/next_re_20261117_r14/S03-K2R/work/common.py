#!/usr/bin/env python3
"""S03-K2R common PE/disassembly helpers. Read-only on target binary."""
from __future__ import annotations
import os, struct
import pefile, capstone
from capstone.x86 import X86_OP_REG, X86_OP_IMM, X86_OP_MEM

ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXPECT_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def sha256_file(path=TARGET):
    import hashlib
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest().upper()

class Image:
    def __init__(self, path=TARGET, verify_sha=True):
        self.path=path
        self.blob=open(path,'rb').read()
        if verify_sha:
            got=sha256_file(path)
            if got != EXPECT_SHA256:
                raise SystemExit(f"SHA256 mismatch: {got} != {EXPECT_SHA256}")
        self.pe=pefile.PE(path, fast_load=True)
        self.ib=self.pe.OPTIONAL_HEADER.ImageBase
        self.sections=[]
        for s in self.pe.sections:
            name=s.Name.rstrip(b'\x00').decode('latin1')
            self.sections.append({'name':name,'va':self.ib+s.VirtualAddress,'rva':s.VirtualAddress,
                                  'vsize':s.Misc_VirtualSize,'raw':s.PointerToRawData,'rsize':s.SizeOfRawData,
                                  'chars':s.Characteristics})
        t=[s for s in self.sections if s['name']=='.text']
        if len(t)!=1: raise SystemExit('expected one .text section')
        self.text=t[0]
        self.text_va=self.text['va']
        self.text_bytes=self.blob[self.text['raw']:self.text['raw']+self.text['rsize']]
        self.md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.skipdata=True
        self.md.detail=True

    def section_at(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va']+max(s['vsize'],s['rsize']):
                return s
        return None

    def in_image(self, va):
        return self.section_at(va) is not None

    def read_va(self, va, n):
        s=self.section_at(va)
        if s is None: raise KeyError(hex(va))
        off=s['raw']+(va-s['va'])
        return self.blob[off:off+n]

    def u32(self, va):
        return struct.unpack('<I', self.read_va(va,4))[0]

    def u16(self, va):
        return struct.unpack('<H', self.read_va(va,2))[0]

    def opdict(self, ins, op):
        d={'type':None,'size':op.size,'access':op.access}
        if op.type==X86_OP_REG:
            d['type']='reg'; d['reg']=ins.reg_name(op.reg)
        elif op.type==X86_OP_IMM:
            d['type']='imm'; d['imm']=op.imm & 0xFFFFFFFF
        elif op.type==X86_OP_MEM:
            m=op.mem
            d['type']='mem'
            d['base']=ins.reg_name(m.base) if m.base else None
            d['index']=ins.reg_name(m.index) if m.index else None
            d['scale']=m.scale
            d['disp']=m.disp & 0xFFFFFFFF
            d['segment']=ins.reg_name(m.segment) if m.segment else None
        else:
            d['type']=str(op.type)
        return d

    def disasm_text(self):
        out=[]
        for ins in self.md.disasm(self.text_bytes, self.text_va):
            ops=[]
            if ins.mnemonic != '.byte':
                for op in ins.operands:
                    ops.append(self.opdict(ins,op))
            out.append({'addr':ins.address,'size':ins.size,'mn':ins.mnemonic,'opstr':ins.op_str,
                        'bytes':bytes(ins.bytes),'ops':ops,'id':ins.id})
        return out

def index_insns(insns):
    return {x['addr']:i for i,x in enumerate(insns)}

def imm_call_target(ins):
    if ins['mn']=='call' and ins['ops'] and ins['ops'][0]['type']=='imm':
        return ins['ops'][0]['imm']
    return None

def is_mem(ins,k):
    return k < len(ins['ops']) and ins['ops'][k]['type']=='mem'

def access_kind(ins,k):
    """Audit-compatible W/R convention: op0 (except cmp/test/push) = W; op>0 or cmp/test = R.
    RMW ops (inc/add [mem],reg) are counted W only, matching prior audit."""
    m=ins['mn']
    write = (k==0 and m not in ('cmp','test','push'))
    read = (k>0) or m in ('cmp','test')
    out=[]
    if write: out.append('W')
    if read: out.append('R')
    return out

def fmt_ins(x):
    return f"{x['addr']:08X}  {x['bytes'].hex():<18} {x['mn']:<8} {x['opstr']}"

def dump_range(insns, start, stop):
    for x in insns:
        if x['addr']<start: continue
        if x['addr']>=stop: break
        print(fmt_ins(x))
