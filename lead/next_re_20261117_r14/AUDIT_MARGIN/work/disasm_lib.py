# -*- coding: utf-8 -*-
"""AUDIT-MARGIN: minimal PE reader + capstone feature extractor for ③b rechecks.
Read-only: opens gamemd.exe r+b? no -> 'rb'. Nothing is written back.
"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE_DEFAULT = 0x400000


class PE:
    def __init__(self, path=EXE):
        with open(path, 'rb') as f:
            self.d = f.read()
        if self.d[:2] != b'MZ':
            raise SystemExit('not MZ')
        e_lfanew = struct.unpack_from('<I', self.d, 0x3C)[0]
        if self.d[e_lfanew:e_lfanew + 4] != b'PE\0\0':
            raise SystemExit('not PE')
        coff = e_lfanew + 4
        self.nsec = struct.unpack_from('<H', self.d, coff + 2)[0]
        self.opt_size = struct.unpack_from('<H', self.d, coff + 16)[0]
        opt = coff + 20
        self.image_base = struct.unpack_from('<I', self.d, opt + 28)[0]
        self.entry_rva = struct.unpack_from('<I', self.d, opt + 16)[0]
        secs = []
        so = opt + self.opt_size
        for i in range(self.nsec):
            b = so + i * 40
            name = self.d[b:b + 8].rstrip(b'\0').decode('latin1')
            vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', self.d, b + 8)
            secs.append((name, vaddr, max(vsize, rawsize), rawptr, rawsize))
        self.secs = secs

    def va2off(self, va):
        rva = va - self.image_base
        for name, vaddr, vsz, rawptr, rawsz in self.secs:
            if vaddr <= rva < vaddr + vsz:
                rel = rva - vaddr
                if rel < rawsz:
                    return rawptr + rel
                return None
        return None

    def read(self, va, n):
        off = self.va2off(va)
        if off is None:
            return b''
        return self.d[off:off + n]


def disasm(pe, va, size, max_instr=4000):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    code = pe.read(va, size)
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
        if len(out) >= max_instr:
            break
    return out


STACK_REGS = {'esp', 'sp'}


def features(insns, va, size):
    """Return a feature dict describing ③b-relevant properties of ONE function body."""
    f = dict(n=len(insns), calls=[], indirect_calls=[], rets=0,
             back_jumps=[], fwd_jumps=0, cond_branches=0, loop_hint=[],
             mem_writes=[], stack_writes=0, nonspace_writes=[], jump_table=False,
             neg1_returns=[], min_va=va, max_va=va)
    for ins in insns:
        f['max_va'] = max(f['max_va'], ins.address + ins.size)
        m = ins.mnemonic
        ops = ins.operands
        # control flow
        if m.startswith('ret'):
            f['rets'] += 1
        if m == 'call':
            if ops and ops[0].type == X86_OP_IMM:
                f['calls'].append(ops[0].imm)
            else:
                f['indirect_calls'].append(ins.address)
        if m.startswith('j'):
            tgt = None
            if ops and ops[0].type == X86_OP_IMM:
                tgt = ops[0].imm
            if tgt is not None:
                if tgt <= ins.address:
                    f['back_jumps'].append((ins.address, m, tgt))
                    f['loop_hint'].append(m)
                else:
                    f['fwd_jumps'] += 1
            if m not in ('jmp',) :
                f['cond_branches'] += 1
            # switch/jump-table form: jmp dword ptr [reg*4 + disp]
            if m == 'jmp' and ops and ops[0].type == X86_OP_MEM and ops[0].mem.index:
                f['jump_table'] = True
        # memory writes  (mov [mem], reg/imm  /  or/and/add/sub [mem], ...)
        if len(ops) >= 1 and ops[0].type == X86_OP_MEM:
            dst = ops[0]
            if ops[0].access and (ops[0].access & 2):  # CS_AC_WRITE
                base = ins.reg_name(dst.mem.base) if dst.mem.base else ''
                idx = ins.reg_name(dst.mem.index) if dst.mem.index else ''
                is_stack = base in STACK_REGS or (base == 'ebp' and dst.mem.disp < 0)
                ent = (ins.address, m, base, idx, dst.mem.disp)
                f['mem_writes'].append(ent)
                if is_stack:
                    f['stack_writes'] += 1
                else:
                    f['nonspace_writes'].append(ent)
        # -1 return convention
        if m in ('or', 'mov') and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[1].type == X86_OP_IMM and (ops[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF:
            f['neg1_returns'].append((ins.address, m, ins.reg_name(ops[0].reg)))
    return f


def fmt_feat(f):
    return ('n_instr=%d rets=%d calls=%d indirect_calls=%d cond_br=%d back_jumps=%d '
            'jump_table=%s mem_writes=%d stack_writes=%d non_stack_writes=%d neg1=%d'
            % (f['n'], f['rets'], len(f['calls']), len(f['indirect_calls']),
               f['cond_branches'], len(f['back_jumps']), f['jump_table'],
               len(f['mem_writes']), f['stack_writes'], len(f['nonspace_writes']),
               len(f['neg1_returns'])))


def text(insns, limit=None):
    lines = []
    for ins in insns:
        lines.append('%08X  %-22s %s %s' % (ins.address, ins.bytes.hex(),
                                            ins.mnemonic, ins.op_str))
        if limit and len(lines) >= limit:
            lines.append('... (truncated)')
            break
    return '\n'.join(lines)


if __name__ == '__main__':
    pe = PE()
    print('image_base=%08X entry=%08X nsec=%d' % (pe.image_base, pe.entry_rva, pe.nsec))
    for s in pe.secs:
        print('  %-8s vaddr=%08X vsize=%08X rawptr=%08X rawsize=%08X' % s)
    va = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x00401000
    sz = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x40
    ins = disasm(pe, va, sz)
    print(text(ins))
    print(fmt_feat(features(ins, va, sz)))
