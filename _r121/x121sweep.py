"""x121sweep.py -- streaming linear sweep of .text (no detail, no full-listing in RAM).

Stores only parallel uint32 arrays: va, size. ~12 MB for 1M insns.
Call targets (rel32 call/jmp and E9/EB jmp) are collected with lite decoding.
"""
import sys, struct, bisect
from array import array
sys.path.insert(0, '_r121')
from x121lib import PE
import capstone

MDL = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)  # lite
MDL.detail = False


class Sweep:
    def __init__(self, pe, secname='.text'):
        self.pe = pe
        s = next(x for x in pe.sections if x['name'] == secname)
        self.sec = s
        va0 = pe.image_base + s['va']
        va1 = va0 + s['vsize']
        o0 = s['raw']
        self.va = array('I')
        self.sz = array('H')
        self.targets = set()
        self.resync = []
        self.op_strs = {}   # va -> str  (only for jmp/call targets of interest)
        va = va0
        end = o0 + s['vsize']
        buf = pe.buf
        while va < va1:
            off = o0 + (va - va0)
            chunk = buf[off:min(off + 65536, end)]
            if not chunk:
                break
            nxt = va
            for ins in MDL.disasm(chunk, va):
                self.va.append(ins.address)
                self.sz.append(ins.size)
                if ins.mnemonic in ('call', 'jmp', 'jmpq') and not ins.op_str.startswith('dword ptr [') \
                        and not ins.op_str.startswith('qword ptr [') and ' ptr [' not in ins.op_str:
                    try:
                        t = int(ins.op_str, 16)
                        self.targets.add(t)
                    except ValueError:
                        pass
                nxt = ins.address + ins.size
                if nxt >= va + 65536:
                    break
            if nxt == va:
                self.resync.append(va)
                nxt = va + 1
            va = nxt

    def index(self, va):
        i = bisect.bisect_left(self.va, va)
        if i < len(self.va) and self.va[i] == va:
            return i
        return -1

    def is_boundary(self, va):
        return self.index(va) >= 0


_cache = {}


def get(pe):
    key = id(pe)
    if key not in _cache:
        _cache[key] = Sweep(pe)
    return _cache[key]
