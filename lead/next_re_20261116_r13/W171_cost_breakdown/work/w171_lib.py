"""
W171 own PE + capstone helper.  Free of function_atlas.tsv dependency.

Design decisions (per R13 discipline):
  * capstone skipdata=True ALWAYS (default silently stops on undecodable bytes).
  * Two independent instruction-count channels:
      - lin:  linear sweep from entry, no jump following (what upstream cards used)
      - cfg:  recursive descent from entry, follows jcc / jmp / resolved jump tables
    `cfg` is the channel that does NOT depend on function_atlas entry+size for bounds:
    the function body is discovered by control flow, not by a size column.
  * reach(): same recursive descent but with an explicit *branch-decision override*,
    so "what executes when gate G is taken / not taken" is a mechanical answer.
"""
import struct
import pefile
import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
PE = pefile.PE(EXE, fast_load=True)
IB = PE.OPTIONAL_HEADER.ImageBase
DATA = PE.__data__

SECS = []
for s in PE.sections:
    SECS.append(dict(name=s.Name.decode('latin1').rstrip('\x00'),
                     va=IB + s.VirtualAddress,
                     vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData,
                     rawsize=s.SizeOfRawData))
TEXT = [s for s in SECS if s['name'] == '.text'][0]
TEXT_LO = TEXT['va']
TEXT_HI = TEXT['va'] + TEXT['rawsize']

memo = {}


def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


MD = md()


def sec_of(va):
    for s in SECS:
        if s['rawsize'] and s['va'] <= va < s['va'] + s['rawsize']:
            return s
    return None


def off(va):
    s = sec_of(va)
    if s is None:
        raise ValueError('VA %08X outside any section raw range' % va)
    return s['raw'] + (va - s['va'])


def rd(va, n):
    s = sec_of(va)
    if s is None or va + n > s['va'] + s['rawsize']:
        raise ValueError('read %08X+%d crosses section' % (va, n))
    o = s['raw'] + (va - s['va'])
    return DATA[o:o + n]


def u32(va):
    return struct.unpack('<I', rd(va, 4))[0]


def u16(va):
    return struct.unpack('<H', rd(va, 2))[0]


def u8(va):
    return rd(va, 1)[0]


def in_text(va):
    return TEXT_LO <= va < TEXT_HI


def lin(va, nbytes):
    """Linear sweep (no jump following)."""
    out = []
    for i in MD.disasm(rd(va, nbytes), va):
        out.append(i)
    return out


def lin_atlas(va, size):
    """Linear sweep over exactly `size` bytes (atlas channel: uses atlas size)."""
    return lin(va, size)


def fmt(i):
    return '%08X  %-32s %-7s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)


def _follow(insn):
    mn = insn.mnemonic
    if mn == 'call':
        return True
    if mn == 'jmp':
        return False
    if mn.startswith('j'):
        return True          # conditional jump: fallthrough continues
    return True


def _resolve_jmptable(insn, nmax=256):
    """jmp dword ptr [reg*4 + disp]  ->  read displacement table at disp."""
    for op in insn.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index != 0:
            tab = op.mem.disp & 0xFFFFFFFF
            out = []
            try:
                for k in range(nmax):
                    t = u32(tab + 4 * k)
                    if not in_text(t):
                        break
                    out.append(t)
            except Exception:
                pass
            return out
    return []


class Body:
    """Recursive-descent reachable instruction set from one entry."""

    def __init__(self):
        self.insns = {}        # addr -> insn
        self.calls = {}        # site -> target(imm) or None
        self.vcalls = []       # sites of indirect call
        self.jmps = {}         # site -> target
        self.unres = []        # unresolved indirect jumps
        self.table_jmps = []   # (site, [targets])

    def addrs(self):
        return sorted(self.insns)


def body(entry, maxspan=0x4000, keep=None):
    """CFG reachable body. `keep` = callable(addr) allowing override of branch decisions.

    Returns Body. Stops when leaving [entry, entry+maxspan) or .text.
    """
    if keep is None:
        keep = lambda a: True          # follow everything
    B = Body()
    hi = entry + maxspan
    work = [entry]
    seen = set()
    while work:
        a = work.pop()
        if a in seen or not in_text(a) or not (entry <= a < hi):
            continue
        try:
            ins = next(MD.disasm(rd(a, 16), a), None)
        except Exception:
            continue
        if ins is None or ins.id == 0:
            seen.add(a)
            continue
        seen.add(a)
        B.insns[a] = ins
        nxt = a + ins.size
        mn = ins.mnemonic
        if mn == 'call':
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == X86_OP_IMM:
                B.calls[a] = op.imm & 0xFFFFFFFF
            else:
                B.calls[a] = None
                B.vcalls.append(a)
            work.append(nxt)
            continue
        if mn == 'jmp':
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == X86_OP_IMM:
                B.jmps[a] = op.imm & 0xFFFFFFFF
                if keep(a):
                    work.append(op.imm & 0xFFFFFFFF)
            else:
                tg = _resolve_jmptable(ins)
                if tg:
                    B.table_jmps.append((a, tg))
                    for t in tg:
                        work.append(t)
                else:
                    B.unres.append(a)
            continue
        if mn.startswith('j') and len(ins.operands) >= 1 and ins.operands[0].type == X86_OP_IMM:
            tgt = ins.operands[0].imm & 0xFFFFFFFF
            B.jmps[a] = tgt
            if keep(a):
                work.append(tgt)
            work.append(nxt)
            continue
        if mn in ('ret', 'retf', 'iret', 'iretd', 'hlt'):
            continue
        work.append(nxt)
    return B


def closure(entry, depth, maxspan=0x4000):
    """Per-level instruction/function counts using the CFG channel."""
    levels = []
    frontier = [entry]
    seenfn = set()
    for d in range(depth + 1):
        fns = sorted(set(frontier) - seenfn)
        seenfn |= set(fns)
        tot = 0
        ncall = 0
        nxt = []
        for f in fns:
            B = body(f, maxspan=maxspan)
            tot += len(B.insns)
            for site, tgt in B.calls.items():
                ncall += 1
                if tgt is not None and in_text(tgt) and tgt not in seenfn:
                    nxt.append(tgt)
        levels.append(dict(depth=d, fns=len(fns), insns=tot, calls=ncall))
        frontier = nxt
    return levels


def describe_gate(ins):
    """Classify one instruction as a gate candidate."""
    mn = ins.mnemonic
    ops = ins.operands
    mem = None
    imm = None
    regs = []
    for op in ops:
        if op.type == X86_OP_MEM:
            mem = op
        elif op.type == X86_OP_IMM:
            imm = op.imm
        elif op.type == X86_OP_REG:
            regs.append(ins.reg_name(op.reg))
    return dict(mn=mn, mem=mem, imm=imm, regs=regs)


def memstr(ins, op):
    ms = ins.reg_name(op.mem.segment) + ':' if op.mem.segment else ''
    b = ins.reg_name(op.mem.base) if op.mem.base else ''
    i = ins.reg_name(op.mem.index) if op.mem.index else ''
    d = op.mem.disp
    if i:
        idx = '[%s%s*%d%s]' % (ms, i, op.mem.scale, ('%+d' % d) if d else '')
        if b:
            return '[%s+%s%s*%d%s]' % (ms, b, i, op.mem.scale, ('%+d' % d) if d else '')
        return idx
    if b:
        return '[%s%s%s]' % (ms, b, ('%+d' % d) if d else '')
    return '[%s%08X]' % (ms, d & 0xFFFFFFFF)


if __name__ == '__main__':
    print('ImageBase %08X' % IB)
    for s in SECS:
        print('  %-8s va=%08X raw=%08X rawsize=%08X' % (s['name'], s['va'], s['raw'], s['rawsize']))
    for va in (0x4B0500, 0x4D3920, 0x429A90, 0x4DA530, 0x47E8A0):
        B = body(va)
        print('%08X cfg_insns=%d calls=%d unresolved_indirect=%d'
              % (va, len(B.insns), len(B.calls), len(B.unres)))
