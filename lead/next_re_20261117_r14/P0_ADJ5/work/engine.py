#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ5 analysis engine.

Builds, from the read-only binary + vtables_v2.json:
  - call_targets : VA hit by an E8 rel32 at an instruction boundary (linear sweep, skipdata=True)
  - jmp_targets  : VA hit by an E9 rel32 at an instruction boundary (weaker per R14 错源②)
  - vt_slots     : VA that is a slot value in a resolvable-RTTI vtable (binary bytes, JSON class)
and computes per-address features / verdict for candidate sets.

Evidence roles (per task):
  PRECONDITIONS (not criteria, pool definition only): align16, pred in TERM, first byte not E8/E9/EB.
  PRIMARY: (a) E8/E9 rel32 boundary hit ; (b) vtable slot value with RTTI.
  SUPPORT : (c) predecessor is a real ret/jmp/int3/padding boundary proven by decoding;
            (d) standard prologue + self-consistent body to a ret.
"""
import struct, json, pefile, capstone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EXE  = ROOT / r"ra2youli\gamemd.exe"
VTJ  = ROOT / r"lead\next_re_20261112_r10\W130_atlas\vtables_v2.json"
IB   = 0x400000

class Bin:
    def __init__(self):
        self.pe = pefile.PE(str(EXE), fast_load=True)
        self.data = self.pe.__data__
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            self.secs.append(dict(name=s.Name.decode(errors='replace').rstrip('\x00'),
                                  va=self.ib+s.VirtualAddress, vsize=s.Misc_VirtualSize,
                                  raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
        self.text = self.sec('.text')
        self.rdata = self.sec('.rdata')
    def sec(self,n):
        for s in self.secs:
            if s['name']==n: return s
        raise KeyError(n)
    def sec_of(self,va):
        for s in self.secs:
            if s['va']<=va<s['va']+s['vsize']: return s
        return None
    def read(self,va,n):
        s=self.sec_of(va)
        if s is None or va+n>s['va']+s['rawsize']: return None
        off=s['raw']+(va-s['va']); return self.data[off:off+n]
    def u8(self,va):
        b=self.read(va,1); return b[0] if b else None
    def u32(self,va):
        b=self.read(va,4); return struct.unpack('<I',b)[0] if b and len(b)==4 else None

def in_text(va, text):
    return text['va'] <= va < text['va']+text['vsize']

def sweep_rel32(bin_):
    """Return dict target->list sites for E8 (call) and E9 (jmp), instruction-boundary only."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True; md.skipdata = True
    t=bin_.text
    data=bin_.data[t['raw']:t['raw']+t['rawsize']]
    calls={}; jmps={}; nins=0; nskip=0
    for insn in md.disasm(data, t['va']):
        if insn.id==0:
            nskip+=insn.size; continue
        nins+=1
        b=insn.bytes
        # E8 call rel32 / E9 jmp rel32 (5 bytes, no prefix) — exact byte check avoids op_str parse issues
        if len(b)==5 and b[0]==0xE8:
            rel=struct.unpack('<i', b[1:5])[0]
            tgt=insn.address+5+rel
            calls.setdefault(tgt,[]).append(insn.address)
        elif len(b)==5 and b[0]==0xE9:
            rel=struct.unpack('<i', b[1:5])[0]
            tgt=insn.address+5+rel
            jmps.setdefault(tgt,[]).append(insn.address)
    return calls, jmps, dict(insns=nins, skipped_bytes=nskip, text_bytes=len(data),
                             text_start=t['va'], text_end=t['va']+t['vsize'])

def rtti_name(bin_, vt):
    """Verify COL chain from binary: [vt-4]=COL, [COL+0xC]=TD, TD+8 inline ASCII name.
       Return name string (RTTI resolvable) or None (fail-closed)."""
    col=bin_.u32(vt-4)
    if col is None: return None
    td=bin_.u32(col+0xC) if col else None
    if td is None or td==0: return None
    raw=bin_.read(td+8, 64)
    if not raw: return None
    name=raw.split(b'\x00',1)[0]
    try: s=name.decode('ascii')
    except Exception: return None
    if '.?A' not in s: return None
    return s

def load_vt_slots(bin_):
    """Read vtables_v2.json, read slot values from the BINARY, verify RTTI from binary.
       Also read one extra slot (error①: 794 tables each miss terminal slot) and mark it separately.
       Returns dict target_va -> list of (cls, vt, slot_idx, terminal_bool)."""
    obj=json.loads(VTJ.read_text(encoding='utf-8'))
    vtabs=obj['vtables']
    tgt={}; ntable=0; nslot=0; n_rtti=0
    for v in vtabs:
        vt=int(v['vt']); nslot_decl=int(v.get('slots',0))
        cls_json=v.get('class','')
        cls_bin=rtti_name(bin_, vt)
        resolvable = cls_bin is not None
        if resolvable: n_rtti+=1
        # read nslot_decl+1 dwords (include possible terminal slot)
        vals=[]
        for i in range(nslot_decl+1):
            val=bin_.u32(vt+4*i)
            if val is None: break
            vals.append(val)
        for i,val in enumerate(vals):
            if in_text(val, bin_.text):
                terminal = i>=nslot_decl
                label = cls_bin if resolvable else (cls_json if cls_json else None)
                if label:  # only count slots whose table has a resolvable class name
                    tgt.setdefault(val,[]).append((label, vt, i, terminal, resolvable))
                    nslot+=1
        ntable+=1
    return tgt, dict(ntables=ntable, nslot_values=nslot, n_rtti_resolved=ntable and n_rtti)

def pred_boundary(bin_, va):
    """(c) predecessor boundary proof by decoding bytes right before va.
       Returns (bool, evidence_str)."""
    # look at up to 16 bytes before, try to find an instruction ending exactly at va
    back=bin_.read(va-16,16)
    if back is None: return (False,'no-bytes')
    for start in range(va-16, va):
        if start>=va: break
        seg=bin_.read(start, va-start+4)
        if not seg: continue
        md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=False; md.skipdata=True
        last=None
        for insn in md.disasm(seg, start):
            if insn.id==0: continue
            if insn.address+insn.size==va:
                m=insn.mnemonic
                if m in ('ret','retf','jmp','int3','hlt','ud2') or insn.bytes[0] in (0xC3,0xC2,0xCC,0xEB,0xE9,0xEA,0xCB,0xCA):
                    return (True, f'{m}@{start:X}+{insn.size}')
                return (False, f'prev={m}@{start:X} (not terminator)')
            if insn.address>va: break
    # padding: >=4 consecutive 0x90 (or 0xCC) immediately before
    pad=bin_.read(va-4,4)
    if pad and (all(x==0x90 for x in pad) or all(x==0xCC for x in pad)):
        return (True, 'padding 4x90/CC')
    return (False, 'no-boundary')

def prologue(bin_, va):
    """(d) standard prologue at va: push ebp;mov ebp,esp / sub esp,imm ; plus body to a ret."""
    b=bin_.read(va,8)
    if not b: return (False,'no-bytes')
    kind=None
    if len(b)>=3 and b[0]==0x55 and b[1] in (0x8B,0x89) and b[2] in (0xEC,0xFF,0xE5):
        kind='push ebp;mov ebp,esp'
    elif len(b)>=3 and b[0]==0x83 and b[1]==0xEC:
        kind='sub esp,imm8'
    elif len(b)>=6 and b[0]==0x81 and b[1]==0xEC:
        kind='sub esp,imm32'
    if kind is None: return (False,'no-prologue')
    # self-consistency: linear-decode forward from va, reach a ret within 2048 bytes, no early invalid run
    md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=False; md.skipdata=True
    chunk=bin_.read(va,2048)
    if not chunk: return (True, kind+';body=unreadable')
    nins=0; sawret=False
    for insn in md.disasm(chunk, va):
        if insn.id==0: continue
        nins+=1
        if insn.mnemonic in ('ret','retf'):
            sawret=True; break
        if nins>400: break
    return (sawret, f'{kind};body={"ret@"+format(insn.address,"X") if sawret else "no-ret-in-window"}')

if __name__=='__main__':
    bin_=Bin()
    calls,jmps,sweep=sweep_rel32(bin_)
    vtgt,vtstat=load_vt_slots(bin_)
    print('SWEEP', json.dumps(sweep))
    print('VTSTAT', json.dumps(vtstat))
    print('call targets', len(calls), 'jmp targets', len(jmps), 'vt targets', len(vtgt))
    # save index
    import pickle
    with open(ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work\idx.pkl','wb') as f:
        pickle.dump(dict(calls={k:v for k,v in calls.items()},
                         jmps={k:v for k,v in jmps.items()},
                         vtgt=vtgt, sweep=sweep, vtstat=vtstat), f)
    print('saved idx.pkl')
