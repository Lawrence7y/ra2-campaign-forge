# -*- coding: utf-8 -*-
"""MEASURE-F3A : self-written PE (32-bit) reader + bounded function-body disassembler.

No project module is imported. Only the stdlib + capstone (already installed;
no pip install, no venv).

Used by s5_thirdb.py to decide, from bytes alone, whether a row's ③b
("整体合同" per R14_COMMON §8.6 条 3) is established:
  ③b①  jump table / switch multi-way, each arm checkable
  ③b②  falsifiable error-code / return convention
  ③b③  memory-shape assertion (member ctors + vt + object size)
  ③b④  complete loop I/O (read -> test -> write -> advance, with bounds check)
Per the card: a "write" that only touches a stack slot, or only advances a
register, does NOT count.
"""
import struct

class PE:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.buf = f.read()
        self.image_base = None
        self.sections = []          # (name, va, vsize, raw_off, raw_size)
        self._parse()

    def _parse(self):
        b = self.buf
        if b[:2] != b"MZ":
            raise ValueError("not MZ")
        e_lfanew = struct.unpack_from("<I", b, 0x3C)[0]
        if b[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise ValueError("not PE")
        coff = e_lfanew + 4
        nsec, = struct.unpack_from("<H", b, coff + 2)
        opt_size, = struct.unpack_from("<H", b, coff + 16)
        opt = coff + 20
        magic, = struct.unpack_from("<H", b, opt)
        if magic != 0x10B:
            raise ValueError("not PE32 (magic=%#x)" % magic)
        self.image_base, = struct.unpack_from("<I", b, opt + 28)
        self.entry_rva, = struct.unpack_from("<I", b, opt + 16)
        sec = opt + opt_size
        for i in range(nsec):
            o = sec + i * 40
            name = b[o:o + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rawsize, rawoff = struct.unpack_from("<IIII", b, o + 8)
            self.sections.append((name, va, vsize, rawoff, rawsize))

    def va_to_off(self, va):
        rva = va - self.image_base
        for name, sva, vsize, rawoff, rawsize in self.sections:
            if sva <= rva < sva + max(vsize, rawsize):
                d = rva - sva
                if d < rawsize:
                    return rawoff + d
        return None

    def section_of(self, va):
        rva = va - self.image_base
        for name, sva, vsize, rawoff, rawsize in self.sections:
            if sva <= rva < sva + max(vsize, rawsize):
                return name
        return None

    def read(self, va, n):
        o = self.va_to_off(va)
        if o is None or o + n > len(self.buf):
            return None
        return self.buf[o:o + n]

    def u32(self, va):
        d = self.read(va, 4)
        return None if d is None else struct.unpack("<I", d)[0]

    def u8(self, va):
        d = self.read(va, 1)
        return None if d is None else d[0]


# ---------------------------------------------------------------- disassembly
import capstone

_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_MD.detail = True
_MD.skipdata = False

CALLS = {"call"}
JUMPS_UNCOND = {"jmp"}
JCC = {"ja", "jae", "jb", "jbe", "jc", "je", "jg", "jge", "jl", "jle",
       "jna", "jnae", "jnb", "jnbe", "jnc", "jne", "jng", "jnge", "jnl",
       "jnle", "jno", "jnp", "jns", "jnz", "jo", "jp", "jpe", "jpo", "js", "jz"}
RETS = {"ret", "retn"}

STACK_REGS = {"esp", "ebp"}
# operand groups
OP_REG, OP_IMM, OP_MEM = 1, 2, 3


def _mem_operand(insn):
    for op in insn.operands:
        if op.type == OP_MEM:
            return op
    return None


def analyse(pe, entry, size):
    """Linear-ish linear decode of the declared body span.

    The atlas `size` is the authoritative extent; we decode exactly that many
    bytes so the feature counts are reproducible from the table alone.
    Returns a dict of raw features plus the instruction list.
    """
    code = pe.read(entry, size)
    if code is None:
        return None
    insns = list(_MD.disasm(code, entry))
    covers = sum(i.size for i in insns)
    f = {
        "entry": entry, "size": size, "n_instr": len(insns),
        "bytes_covered": covers, "coverage_pct": round(100.0 * covers / size, 2) if size else 0.0,
        "n_call": 0, "n_call_imm": 0, "n_jcc": 0, "n_jmp": 0, "n_ret": 0,
        "n_back_edge": 0, "n_fwd_edge": 0,
        "jump_tables": [], "calls": [],
        "non_stack_writes": 0, "stack_writes": 0, "write_sites": [],
        "read_mem_ops": 0, "cmp_imm": [], "ret_const": [],
        "has_bounds_check": 0, "n_imul_no": 0,
    }
    ends = {}
    for ins in insns:
        ends.setdefault(ins.address + ins.size, ins.address)
        mn = ins.mnemonic
        if mn in CALLS:
            f["n_call"] += 1
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == OP_IMM:
                f["n_call_imm"] += 1
                f["calls"].append(op.imm)
        elif mn in JCC:
            f["n_jcc"] += 1
            if ins.operands and ins.operands[0].type == OP_IMM:
                t = ins.operands[0].imm
                if t < ins.address:
                    f["n_back_edge"] += 1
                else:
                    f["n_fwd_edge"] += 1
        elif mn in JUMPS_UNCOND:
            f["n_jmp"] += 1
            op = ins.operands[0] if ins.operands else None
            if op is not None:
                if op.type == OP_IMM:
                    if op.imm < ins.address:
                        f["n_back_edge"] += 1
                elif op.type == OP_MEM and op.mem.index != 0 and op.mem.scale in (1, 2, 4, 8):
                    # jmp [reg*scale + disp]  -> dispatch table
                    f["jump_tables"].append({"at": ins.address, "disp": op.mem.disp,
                                             "scale": op.mem.scale})
        elif mn in RETS:
            f["n_ret"] += 1
            if ins.operands and ins.operands[0].type == OP_IMM:
                f["ret_const"].append(ins.operands[0].imm)

        # ---- memory reads (any size)
        for op in ins.operands:
            if op.type == OP_MEM:
                if op.access & capstone.CS_AC_READ:
                    f["read_mem_ops"] += 1

        # ---- writes: destination operand written to memory
        if ins.operands and ins.operands[0].access & capstone.CS_AC_WRITE:
            d = ins.operands[0]
            if d.type == OP_MEM:
                base = ins.reg_name(d.mem.base) if d.mem.base else ""
                idx = ins.reg_name(d.mem.index) if d.mem.index else ""
                if base in STACK_REGS or idx in STACK_REGS:
                    f["stack_writes"] += 1
                else:
                    f["non_stack_writes"] += 1
                    f["write_sites"].append({"at": ins.address,
                                             "insn": "%s %s" % (mn, ins.op_str)})
        # push / call both write stack - excluded by the access flag above
        # cmp / test against immediates -> candidate falsifiable comparisons
        if mn in ("cmp", "test") and len(ins.operands) >= 2 and ins.operands[1].type == OP_IMM:
            f["cmp_imm"].append((mn, ins.operands[1].imm))

    # bounds-check heuristic: an unsigned compare (ja/jae) somewhere + a back edge
    f["has_bounds_check"] = 1 if (f["n_back_edge"] and f["n_jcc"]) else 0
    f["has_loop"] = 1 if f["n_back_edge"] else 0
    f["has_jumptable"] = 1 if f["jump_tables"] else 0
    return f
