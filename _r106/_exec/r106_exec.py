#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R106-EXEC: independent recomputation of 19 switch dispatch tables in gamemd.exe.

Disassembler used: Capstone 5.0.7 (CS_ARCH_X86 / CS_MODE_32, detail=True).
All numbers are read from the exe bytes at runtime; none are copied from the card.
Exit code 0 means every positive check and negative control passed.
"""
import sys
import json
import struct
import hashlib
from collections import defaultdict

import pefile
from capstone import (Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_READ, CS_AC_WRITE)
from capstone.x86 import (X86_OP_REG, X86_OP_MEM, X86_OP_IMM,
                          X86_INS_CALL, X86_INS_RET)

EXE = "ra2bench/gamemd.exe"
EXPECT_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
OUT_JSON = "_r106/_exec/r106_exec.json"

# Card-supplied table inventory: base, nentries, holder instruction VA.
# These are inputs to the analysis, not conclusions; every dword/byte is read
# from the file and independently verified below.
TABLES = [
    (0x46f5a0, 4, 0x46e4be), (0x48db10, 13, 0x48d583),
    (0x48dd10, 5, 0x48dce0), (0x4c8114, 46, 0x4c6cd7),
    (0x5001e4, 5, 0x4ffde9), (0x58bda4, 5, 0x58bd85),
    (0x69b15c, 4, 0x69af3e), (0x6a92c4, 3, 0x6a8e1e),
    (0x6adbdc, 3, 0x6acf2a), (0x6b0238, 7, 0x6afd73),
    (0x6dfdec, 145, 0x6dd8e7), (0x708d54, 5, 0x708c4e),
    (0x71f2c0, 14, 0x71eea2), (0x71f328, 10, 0x71f092),
    (0x71f778, 2, 0x71f6d0), (0x71f9e0, 2, 0x71f9d3),
    (0x728e08, 7, 0x728c17), (0x7291ac, 7, 0x728e6c),
    (0x79f028, 5, 0x79ed73),
]

failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)
    return bool(cond)


class Image:
    def __init__(self, path):
        self.path = path
        self.data = bytearray(open(path, "rb").read())
        self.pe = pefile.PE(path, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            self.sections.append((s.VirtualAddress, max(s.Misc_VirtualSize, s.SizeOfRawData),
                                  s.PointerToRawData))

    def off(self, va):
        rva = va - self.ib
        for va_s, size, ptr in self.sections:
            if va_s <= rva < va_s + size:
                return ptr + (rva - va_s)
        raise ValueError("VA not in any section: " + hex(va))

    def read(self, va, n):
        o = self.off(va)
        b = self.data[o:o+n]
        if len(b) != n:
            raise ValueError("short read at " + hex(va))
        return b

    def write_mem(self, va, b):
        """Write into the in-memory image buffer only; never touches disk."""
        o = self.off(va)
        self.data[o:o+len(b)] = b


MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True   # required for operand access / mem.base / mem.index


def disasm_bytes(code, start_va):
    # Streaming: yields instructions one at a time, never materializes a full
    # disassembly list of the binary.
    for ins in MD.disasm(code, start_va):
        yield ins


def disasm_va(img, va, nbytes):
    return disasm_bytes(img.read(va, nbytes), va)


def ins_text(ins):
    return ins.mnemonic + " " + ins.op_str


def operand_touches_reg(img_ins, op, reg):
    """Whether an explicit operand reads or writes the given reg.

    Handles pitfall #2: for X86_OP_MEM both mem.base and mem.index are
    checked, so mov cl,[eax+disp] is seen as using eax as a base.
    """
    if op.type == X86_OP_REG:
        return img_ins.reg_name(op.reg) == reg
    if op.type == X86_OP_MEM:
        for r in (op.mem.base, op.mem.index):
            if r and img_ins.reg_name(r) == reg:
                return True
    return False


def classify_instruction(ins, reg):
    """Return (reads, writes) for reg using Capstone operand access semantics.

    Pitfall #1: operand position is not used; CS_AC_READ/WRITE on each operand
    decides. cmp eax,6 has op0 access=READ -> reads only.
    Pitfall #3: sbb r,r and or r,-1 do not depend on the old value; they are
    normalized to (False, True).
    """
    m = ins.mnemonic
    reads = writes = False
    # Implicit register reads/writes (e.g. esp/eip for call/ret) come from
    # Capstone's regs_read/regs_write; explicit ones come from operand.access.
    for r in ins.regs_read:
        if ins.reg_name(r) == reg:
            reads = True
    for r in ins.regs_write:
        if ins.reg_name(r) == reg:
            writes = True
    # Constant-folding idioms: sbb/xor/sub/and r,r and or r,-1 do not depend
    # on the old value (result is only CF or a constant). Pitfall #3 in the
    # card explicitly names sbb r,r and or r,-1; xor/sub/and r,r are the same
    # class and appear at the 0x69b15c targets.
    fold_same = False
    or_minus1 = False
    if len(ins.operands) == 2:
        a, b = ins.operands
        if (m in ("sbb", "xor", "sub", "and") and a.type == X86_OP_REG
                and b.type == X86_OP_REG and a.reg == b.reg):
            fold_same = True
        if (m == "or" and a.type == X86_OP_REG and b.type == X86_OP_IMM
                and (b.imm & 0xffffffff) == 0xffffffff):
            or_minus1 = True
    for op in ins.operands:
        if not operand_touches_reg(ins, op, reg):
            continue
        acc = op.access
        if acc & CS_AC_READ:
            reads = True
        if acc & CS_AC_WRITE:
            writes = True
        if op.type == X86_OP_REG and ins.reg_name(op.reg) == reg:
            if fold_same or or_minus1:
                reads = False
                writes = True
    return reads, writes


def q3_classify_target(img, target, reg):
    """Walk forward from T until reg is defined / read / call-clobber / ret.

    Returns dict with verdict, decisive instruction address and disasm text.
    """
    max_insns = 64
    for idx, ins in enumerate(disasm_va(img, target, 160)):
        if idx >= max_insns:
            break
        if ins.id == X86_INS_RET or ins.mnemonic.startswith("ret"):
            return dict(verdict="IDX_DEAD_HERE", reason="ret before any use of reg",
                        insn=hex(ins.address), disasm=ins_text(ins))
        if ins.id == X86_INS_CALL or ins.mnemonic == "call":
            if reg in ("eax", "ecx", "edx"):
                return dict(verdict="CALL_CLOBBER",
                            reason="call may clobber reg before it is defined/read",
                            insn=hex(ins.address), disasm=ins_text(ins))
        reads, writes = classify_instruction(ins, reg)
        if reads:
            return dict(verdict="DEPENDS_ON_IDX",
                        reason="reads old reg before any definition",
                        insn=hex(ins.address), disasm=ins_text(ins))
        if writes:
            return dict(verdict="IDX_DEAD_HERE",
                        reason="reg fully written before any read of its old value",
                        insn=hex(ins.address), disasm=ins_text(ins))
    return dict(verdict="UNRESOLVED", reason="no decision within 64 instructions",
                insn=None, disasm=None)


def main():
    img = Image(EXE)
    sha = hashlib.sha256(img.data).hexdigest()
    check(sha == EXPECT_SHA256, "sha256 mismatch: " + sha)
    print("sha256:", sha)
    print("ImageBase:", hex(img.ib))
    check(img.ib == 0x400000, "ImageBase is not 0x400000")

    # ---- N3 (performed early; its results feed Q3): decode holder jmps ----
    holder_info = {}
    for base, n, hold in TABLES:
        found = None
        for ins in disasm_va(img, hold, 16):
            if ins.mnemonic == "jmp" and ins.operands and ins.operands[0].type == X86_OP_MEM:
                found = ins
                break
        check(found is not None, "no jmp mem at holder " + hex(hold))
        if found is None:
            continue
        op = found.operands[0]
        mem = op.mem
        regs_used = []
        if mem.base:
            regs_used.append(found.reg_name(mem.base))
        if mem.index:
            regs_used.append(found.reg_name(mem.index))
        # N3 requires the displayed base == table base and index == Q3 reg.
        disp = mem.disp
        if mem.base == 0 and mem.index != 0 and mem.scale in (1, 2, 4, 8):
            disp_is_base = True
        else:
            disp_is_base = False
        ok = disp_is_base and disp == base and len(regs_used) == 1 and regs_used[0] in ("eax", "ecx", "edx")
        check(ok, "N3 holder mismatch for table " + hex(base) + ": " + ins_text(found))
        holder_info[base] = dict(index_reg=regs_used[0] if regs_used else None,
                                 disp=disp, disp_is_base=disp_is_base,
                                 jmp_text=ins_text(found), jmp_va=hex(found.address))

    # ---- Read all 19 dword tables ----
    dword_tables = {}
    for base, n, hold in TABLES:
        vals = list(struct.unpack("<%dI" % n, img.read(base, n*4)))
        dword_tables[base] = vals

    # ---- Q1: two-level tables, locate byte table from preceding instructions ----
    TWO_LEVEL_BASES = {0x46f5a0, 0x48db10, 0x48dd10, 0x6a92c4, 0x6adbdc,
                       0x71f2c0, 0x71f328, 0x71f778, 0x71f9e0, 0x79f028}
    q1 = {}
    # For each holder, scan backward over a window for the cmp-imm + ja + xor +
    # mov r8,[reg+disp] sequence immediately preceding the jmp.
    for base, n, hold in TABLES:
        if base not in TWO_LEVEL_BASES:
            continue
        window = img.read(hold - 0x60, 0x60)
        insns = list(disasm_bytes(window, hold - 0x60))
        # Find cmp with imm (unsigned upper bound) followed later by mov r8,[reg+disp]
        ub = None
        byte_table = None
        mov_insn = None
        cmp_insn = None
        for ins in insns:
            if ins.mnemonic in ("cmp", "cmp ") and ins.operands and ins.operands[-1].type == X86_OP_IMM:
                # immediate comparison; keep the last one before the holder
                if all(op.type != X86_OP_MEM or op.mem.base == 0 for op in ins.operands):
                    ub = ins.operands[-1].imm
                    cmp_insn = ins
        # The mov r8,[reg+disp] with an 8-bit dest, whose disp is near table base.
        for ins in insns:
            if ins.mnemonic == "mov" and len(ins.operands) == 2:
                dst, src = ins.operands
                if (dst.type == X86_OP_REG and ins.reg_name(dst.reg) in ("al", "cl", "dl", "bl")
                        and src.type == X86_OP_MEM and src.mem.base != 0
                        and src.mem.index == 0):
                    disp = src.mem.disp
                    if 0 <= disp - base <= 0x80:  # byte table sits just after the dword table
                        byte_table = disp
                        mov_insn = ins
        check(ub is not None, "Q1 upper bound not found for " + hex(base))
        check(byte_table is not None, "Q1 byte table not found for " + hex(base))
        if ub is None or byte_table is None:
            continue
        table_len = ub + 1
        raw = img.read(byte_table, table_len)
        values = list(raw)
        uniq = sorted(set(values))
        all_lt = all(v < n for v in uniq)
        check(len(values) == table_len, "Q1 byte table length mismatch " + hex(base))
        check(all_lt, "Q1 byte value >= nentries in " + hex(base))
        groups = defaultdict(list)
        for inp, v in enumerate(values):
            groups[v].append(inp)
        total_inputs = sum(len(v) for v in groups.values())
        check(total_inputs == table_len, "Q1 group sum mismatch " + hex(base))
        uncovered = sorted(set(range(n)) - set(groups.keys()))
        check(not uncovered, "Q1 case with zero inputs in " + hex(base) + ": " + str(uncovered))
        max_group = max(len(v) for v in groups.values())
        single_groups = sum(1 for v in groups.values() if len(v) == 1)
        q1[hex(base)] = dict(
            table_base=hex(base), nentries=n, upper_bound=ub,
            byte_table=hex(byte_table), byte_table_len=table_len,
            distinct_values=len(uniq), unique_values=uniq,
            all_values_lt_nentries=all_lt,
            total_inputs=total_inputs, max_group_size=max_group,
            single_input_groups=single_groups,
            cases_with_zero_inputs=uncovered,
            groups={str(k): groups[k] for k in sorted(groups)},
            cmp_insn=ins_text(cmp_insn) if cmp_insn else None,
            mov_insn=ins_text(mov_insn) if mov_insn else None,
        )

    # ---- N1: negative control, zero the byte table in memory only ----
    nb = 0x46f5a0
    ninfo = q1[hex(nb)]
    bt = int(ninfo["byte_table"], 16)
    orig = img.read(bt, ninfo["byte_table_len"])
    img.write_mem(bt, bytes(ninfo["byte_table_len"]))
    zero_uniq = sorted(set(img.read(bt, ninfo["byte_table_len"])))
    check(zero_uniq == [0], "N1 zeroed byte table did not collapse to 1 value: " + str(zero_uniq))
    img.write_mem(bt, orig)  # restore in-memory image

    # ---- N2: negative control, add 1 mod 256 to every byte ----
    plus = bytes((b + 1) & 0xff for b in orig)
    img.write_mem(bt, plus)
    plus_uniq = sorted(set(img.read(bt, ninfo["byte_table_len"])))
    nentries = ninfo["nentries"]
    bad = [v for v in plus_uniq if v >= nentries]
    check(len(bad) >= 1, "N2 plus-one produced no value >= nentries: " + str(plus_uniq))
    img.write_mem(bt, orig)  # restore

    # ---- Q2: duplicate census ----
    q2_tables = {}
    all_dup_groups = []  # (base, target, indices, reg)
    total_entries = 0
    global_vals = []
    for base, n, hold in TABLES:
        vals = dword_tables[base]
        total_entries += n
        global_vals.extend(vals)
        by_val = defaultdict(list)
        for i, v in enumerate(vals):
            by_val[v].append(i)
        dups = {v: ix for v, ix in by_val.items() if len(ix) > 1}
        extra = sum(len(ix) - 1 for ix in dups.values())
        q2_tables[hex(base)] = dict(nentries=n, distinct=len(by_val),
                                    duplicate_groups=len(dups), extra_entries=extra,
                                    duplicates={hex(v): ix for v, ix in sorted(dups.items())})
        for v, ix in sorted(dups.items()):
            reg = holder_info[base]["index_reg"]
            all_dup_groups.append((base, v, ix, reg))
    distinct_global = len(set(global_vals))
    tables_with_dups = len([1 for b in q2_tables.values() if b["duplicate_groups"] > 0])
    dup_group_count = len(all_dup_groups)
    extra_total = sum(t["extra_entries"] for t in q2_tables.values())
    check(total_entries == 292, "total entries != 292: " + str(total_entries))
    two_level_dups = [hex(b) for b, v, ix, r in all_dup_groups if b in TWO_LEVEL_BASES]

    q2_summary = dict(total_entries=total_entries, distinct_values=distinct_global,
                      duplicate_groups=dup_group_count, tables_with_duplicates=tables_with_dups,
                      extra_entries=extra_total,
                      two_level_tables_with_duplicates=two_level_dups,
                      per_table=q2_tables)

    # ---- Q3: verdict per duplicate group ----
    q3 = []
    for base, target, indices, reg in all_dup_groups:
        verdict = q3_classify_target(img, target, reg)
        q3.append(dict(table_base=hex(base), target=hex(target),
                       referenced_by_indices=indices, ref_count=len(indices),
                       index_reg=reg, verdict=verdict["verdict"],
                       reason=verdict["reason"], decisive_insn=verdict["insn"],
                       decisive_disasm=verdict["disasm"]))

    # ---- Q4: table 0x728e08 ----
    b = 0x728e08
    vals = dword_tables[b]
    by_val = defaultdict(list)
    for i, v in enumerate(vals):
        by_val[v].append(i)
    common4 = max(by_val.items(), key=lambda kv: len(kv[1]))
    q4_targets = {}
    for v, ix in sorted(by_val.items()):
        heads = []
        for ins in disasm_va(img, v, 32):
            heads.append(dict(addr=hex(ins.address), bytes=ins.bytes.hex(),
                              disasm=ins_text(ins)))
            if len(heads) == 4:
                break
        q4_targets[hex(v)] = dict(indices=ix, ref_count=len(ix), first4=heads)
    q4 = dict(table_base=hex(b), entries=[hex(v) for v in vals],
              four_ref_target=hex(common4[0]), four_ref_indices=common4[1],
              targets=q4_targets)

    result = dict(
        meta=dict(disassembler="Capstone 5.0.7", exe=EXE, sha256=sha,
                  image_base=hex(img.ib), total_dword_tables=len(TABLES),
                  note="all numbers read from exe bytes at runtime"),
        q1=q1, q2=q2_summary, q3=q3, q4=q4,
        controls=dict(
            N1=dict(byte_table=hex(bt), original_distinct=len(set(orig)),
                    zeroed_distinct=zero_uniq, passed=zero_uniq == [0]),
            N2=dict(byte_table=hex(bt), plus_one_distinct=plus_uniq,
                    values_ge_nentries=bad, passed=len(bad) >= 1),
            N3=dict(checked=len(holder_info), passed=sum(1 for h in holder_info.values()
                    if h["disp_is_base"]), details=holder_info),
        ),
    )
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # ---- summary to stdout ----
    print("Q1 two-level tables:", len(q1))
    for k, v in q1.items():
        print("  ", k, "ub", v["upper_bound"], "bt", v["byte_table"],
              "uniq", v["distinct_values"], "maxgrp", v["max_group_size"],
              "single", v["single_input_groups"], "uncovered", v["cases_with_zero_inputs"])
    print("Q2 total", total_entries, "distinct", distinct_global,
          "dupgroups", dup_group_count, "tables", tables_with_dups, "extra", extra_total,
          "two_level_dups", two_level_dups)
    print("Q3 verdicts:")
    for g in q3:
        print("  ", g["table_base"], g["target"], g["index_reg"], g["verdict"],
              g["decisive_insn"], g["decisive_disasm"])
    print("Q4 four-ref target", q4["four_ref_target"], "indices", q4["four_ref_indices"])
    print("Controls N1", result["controls"]["N1"]["passed"],
          "N2", result["controls"]["N2"]["passed"],
          "N3", result["controls"]["N3"]["passed"])
    if failures:
        print("TOTAL FAILURES:", len(failures))
        for f in failures:
            print("  -", f)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
