#!/usr/bin/env python3
"""S14-F1 reusable PE/capstone helpers.

Channel A deliberately uses raw PE bytes + capstone linear decode with
skipdata=True; it does not read function_atlas.tsv for discovery.
"""
from __future__ import annotations

import capstone
import pefile
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EXE = ROOT / "ra2youli" / "gamemd.exe"
IMAGE_BASE = 0x400000

_pe = None
_code = None
_bounds = None


def pe():
    global _pe
    if _pe is None:
        _pe = pefile.PE(str(EXE), fast_load=False)
    return _pe


def code_bytes():
    global _code
    if _code is None:
        p = pe()
        sec = next(s for s in p.sections if s.Name.rstrip(b"\0") == b".text")
        va = IMAGE_BASE + sec.VirtualAddress
        raw = sec.PointerToRawData
        size = min(sec.SizeOfRawData, sec.Misc_VirtualSize)
        _code = (va, raw, size, p.__data__[raw:raw + size])
    return _code


def va_to_off(va: int) -> int:
    p = pe()
    for s in p.sections:
        start = IMAGE_BASE + s.VirtualAddress
        end = start + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if start <= va < end:
            off = s.PointerToRawData + (va - start)
            if off < len(p.__data__):
                return off
    off = va - IMAGE_BASE
    if 0 <= off < len(p.__data__):
        return off
    raise ValueError(f"VA {va:#x} not mapped")


def read_bytes(va: int, size: int) -> bytes:
    off = va_to_off(va)
    return pe().__data__[off:off + size]


def md():
    return capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def decoder():
    d = md()
    d.detail = True
    d.skipdata = True
    return d


def disasm_linear(start: int, end: int | None = None, max_insn: int | None = None):
    """Decode [start,end) as one linear stream, skipdata=True.

    If end is None, decode at most max_insn instructions from start.
    Yields capstone CsInsn objects. Data pseudo-instructions are included.
    """
    d = decoder()
    if end is None:
        data = read_bytes(start, 4096 * 4096)
        limit = max_insn or 100000
        count = 0
        for insn in d.disasm(data, start):
            yield insn
            count += 1
            if count >= limit:
                break
        return
    data = read_bytes(start, end - start)
    for insn in d.disasm(data, start):
        yield insn


def insn_text(insn) -> str:
    return f"{insn.address:08X}  {insn.bytes.hex():<20} {insn.mnemonic:<8} {insn.op_str}"


def dump_range(start: int, end: int) -> str:
    return "\n".join(insn_text(i) for i in disasm_linear(start, end))


def call_target(insn):
    """Return direct call/jmp target VA if operand is an immediate rel32/rel8."""
    if insn.id not in (capstone.x86.X86_INS_CALL, capstone.x86.X86_INS_JMP):
        return None
    if not insn.operands:
        return None
    op = insn.operands[0]
    if op.type == capstone.x86.X86_OP_IMM:
        return op.imm & 0xFFFFFFFF
    return None


def linear_boundaries():
    """All instruction starts from .text linear decode; atlas-independent."""
    global _bounds
    if _bounds is not None:
        return _bounds
    va, _raw, size, _data = code_bytes()
    starts = set()
    for insn in disasm_linear(va, va + size):
        starts.add(insn.address)
    _bounds = starts
    return starts


def scan_direct_calls(target: int):
    """Exhaustive raw E8 scan, filtered by capstone linear boundary.

    Returns list of (call_site_va, target_va, bytes_hex).
    Channel A: no atlas entry/size involved.
    """
    va, _raw, size, data = code_bytes()
    bounds = linear_boundaries()
    d = decoder()
    out = []
    for i in range(size - 4):
        if data[i] != 0xE8:
            continue
        site = va + i
        if site not in bounds:
            continue
        blob = data[i:i + 16]
        insns = list(d.disasm(blob, site, count=1))
        if not insns or insns[0].id != capstone.x86.X86_INS_CALL:
            continue
        insn = insns[0]
        t = call_target(insn)
        if t == (target & 0xFFFFFFFF):
            out.append((site, t, insn.bytes.hex()))
    return out


def off_to_va(off: int) -> int:
    p = pe()
    for s in p.sections:
        lo = s.PointerToRawData
        hi = lo + s.SizeOfRawData
        if lo <= off < hi:
            return IMAGE_BASE + s.VirtualAddress + (off - lo)
    raise ValueError(f"file offset {off:#x} not mapped")


def scan_imm32_refs(value: int, include_mov=True):
    """Raw imm32 scan filtered by capstone linear instruction boundaries.

    Finds `push imm32`, `mov r32, imm32`, and `mov [mem], imm32` where the
    immediate equals value. Returns (site_va, insn_text). No atlas involved.
    """
    va, _raw, size, data = code_bytes()
    bounds = linear_boundaries()
    d = decoder()
    out = []
    pat = (value & 0xFFFFFFFF).to_bytes(4, "little")
    for i in range(size - 4):
        if data[i:i + 4] != pat:
            continue
        # The immediate may begin at i (push/mov r32) or i-? for C7 forms.
        candidates = [i]
        if i >= 6:
            candidates.append(i - 6)  # C7 /0 imm32, e.g. C7 05 <disp32> <imm32>
        elif i >= 2:
            candidates.append(i - 2)  # C7 /0 with 8-bit disp
        for j in candidates:
            site = va + j
            if site not in bounds:
                continue
            blob = data[j:j + 16]
            insns = list(d.disasm(blob, site, count=1))
            if not insns:
                continue
            insn = insns[0]
            ops = insn.operands
            hit = False
            for op in ops:
                if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == (value & 0xFFFFFFFF):
                    hit = True
            if hit and insn.id in (capstone.x86.X86_INS_PUSH,
                                   capstone.x86.X86_INS_MOV,
                                   capstone.x86.X86_INS_CMP,
                                   capstone.x86.X86_INS_ADD,
                                   capstone.x86.X86_INS_SUB):
                out.append((site, insn_text(insn)))
    return sorted(set(out))


def scan_push_va(value: int):
    """Raw `68 imm32` scan for a push of an exact VA; no boundary heuristic.

    A `68` byte inside another instruction could produce a false positive, so
    callers must confirm the surrounding instruction stream. This is intended
    for INI key addresses, where the following call sequence is distinctive.
    """
    va, _raw, size, data = code_bytes()
    pat = b"\x68" + (value & 0xFFFFFFFF).to_bytes(4, "little")
    out = []
    for i in range(size - 4):
        if data[i:i + 5] == pat:
            site = va + i
            insns = list(decoder().disasm(data[i:i + 5], site, count=1))
            if insns and insns[0].id == capstone.x86.X86_INS_PUSH:
                out.append((site, insn_text(insns[0])))
    return out


def scan_all_direct_calls():
    """All verified direct call sites in .text as (site,target)."""
    va, _raw, size, data = code_bytes()
    bounds = linear_boundaries()
    d = decoder()
    out = []
    for i in range(size - 4):
        if data[i] != 0xE8:
            continue
        site = va + i
        if site not in bounds:
            continue
        insns = list(d.disasm(data[i:i + 16], site, count=1))
        if not insns or insns[0].id != capstone.x86.X86_INS_CALL:
            continue
        t = call_target(insns[0])
        if t is not None:
            out.append((site, t))
    return out
