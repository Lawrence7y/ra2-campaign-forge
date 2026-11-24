"""S09-KPROVED3 own RE helpers. Independent of any other card's work code."""
from __future__ import annotations

import os
import struct
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_GRP_JUMP, X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BASE = Path(r"D:\Project\ra2-campaign-forge")
EXE = BASE / "ra2youli" / "gamemd.exe"
OUT = BASE / "lead" / "next_re_20261117_r14" / "S09_KPROVED3"
IB = 0x400000

DATA = EXE.read_bytes()
PE = pefile.PE(str(EXE), fast_load=True)

SECS = []
for _s in PE.sections:
    SECS.append(
        {
            "name": _s.Name.rstrip(b"\0").decode("ascii", "replace"),
            "rva": IB + _s.VirtualAddress,
            "vsize": _s.Misc_VirtualSize,
            "raw": _s.PointerToRawData,
            "rsize": _s.SizeOfRawData,
        }
    )

TEXT = next(s for s in SECS if s["name"] == ".text")
TEXT_LO = TEXT["rva"]
TEXT_HI = TEXT_LO + TEXT["vsize"]

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def va_off(va: int) -> int | None:
    for s in SECS:
        if s["rva"] <= va < s["rva"] + max(s["vsize"], s["rsize"]):
            off = s["raw"] + (va - s["rva"])
            if 0 <= off < min(s["raw"] + s["rsize"], len(DATA)):
                return off
    return None


def sec_of(va: int) -> str | None:
    for s in SECS:
        if s["rva"] <= va < s["rva"] + max(s["vsize"], s["rsize"]):
            return s["name"]
    return None


def u32(va: int) -> int | None:
    off = va_off(va)
    if off is None or off + 4 > len(DATA):
        return None
    return struct.unpack_from("<I", DATA, off)[0]


def cstr(va: int, maxlen: int = 200) -> str | None:
    off = va_off(va)
    if off is None:
        return None
    end = DATA.find(b"\0", off, min(off + maxlen, len(DATA)))
    if end < 0:
        return None
    try:
        return DATA[off:end].decode("ascii")
    except UnicodeDecodeError:
        return None


def is_text(va: int | None) -> bool:
    return va is not None and TEXT_LO <= va < TEXT_HI


def is_rdata(va: int | None) -> bool:
    return sec_of(va) in (".rdata", ".data")


def decode_one(va: int):
    off = va_off(va)
    if off is None:
        return None
    return next(MD.disasm(DATA[off : off + 16], va, count=1), None)


def decode_range(start: int, end: int):
    off = va_off(start)
    if off is None:
        return []
    size = min(end, TEXT_HI) - start
    if size <= 0:
        return []
    return list(MD.disasm(DATA[off : off + size], start))


def imm_target(insn) -> int | None:
    for op in insn.operands:
        if op.type == X86_OP_IMM:
            return op.imm
    return None


def mem_operand(insn):
    for op in insn.operands:
        if op.type == X86_OP_MEM:
            return op
    return None


def imm_operand(insn):
    for op in insn.operands:
        if op.type == X86_OP_IMM:
            return op.imm
    return None


def reg_name(insn, op_index: int = 0) -> str | None:
    if 0 <= op_index < len(insn.operands) and insn.operands[op_index].type == X86_OP_REG:
        return insn.reg_name(insn.operands[op_index].reg)
    return None


def rtti_tables(max_slots: int = 1024):
    """Enumerate every RTTI vtable: valid COL structure -> its vt-4 pointer slot -> .text slot run."""
    valid_cols = {}
    for s in SECS:
        if s["name"] not in (".rdata", ".data", ".rsrc"):
            continue
        start, end = s["raw"], min(s["raw"] + s["rsize"], len(DATA))
        for off in range(start + (-start % 4), end - 4, 4):
            col = s["rva"] + (off - start)
            td = u32(col + 0xC)
            if not td or not is_rdata(td):
                continue
            name = cstr(td + 8)
            if name and (name.startswith(".?AV") or name.startswith(".?AU")):
                valid_cols[col] = (td, name)

    tables = []
    for s in SECS:
        if s["name"] not in (".rdata", ".data", ".rsrc"):
            continue
        start, end = s["raw"], min(s["raw"] + s["rsize"], len(DATA))
        for off in range(start + (-start % 4), end - 4, 4):
            slot_addr = s["rva"] + (off - start)
            col = u32(slot_addr)
            if col not in valid_cols:
                continue
            td, name = valid_cols[col]
            vt = slot_addr + 4
            slots = []
            for i in range(max_slots):
                v = u32(vt + 4 * i)
                if not is_text(v):
                    break
                slots.append(v)
            if slots:
                tables.append(
                    {
                        "vt": vt,
                        "col": col,
                        "col_slot": slot_addr,
                        "td": td,
                        "name": name,
                        "slots": slots,
                    }
                )
    return tables


def tables_holding(tables, entry: int):
    hits = []
    for t in tables:
        for slot, val in enumerate(t["slots"]):
            if val == entry:
                hits.append((t, slot))
                break
    return hits


def cfg_extent(entry: int, cap: int = 6000):
    """CFG extent from entry; never reads function_atlas.tsv."""
    work = [entry]
    seen = {}
    while work and len(seen) < cap:
        va = work.pop()
        if va in seen or not is_text(va):
            continue
        insn = decode_one(va)
        if insn is None or insn.mnemonic == ".byte":
            continue
        seen[va] = insn
        nxt = va + insn.size
        if insn.mnemonic.startswith("ret"):
            continue
        if insn.group(X86_GRP_JUMP):
            tgt = imm_target(insn)
            if tgt is not None and is_text(tgt):
                work.append(tgt)
            if insn.mnemonic != "jmp":
                work.append(nxt)
        else:
            work.append(nxt)
    if not seen:
        return entry, entry, []
    lo = min(seen)
    hi = max(va + ins.size for va, ins in seen.items())
    ordered = [seen[a] for a in sorted(seen)]
    return lo, hi, ordered


def full_e8_sweep():
    """Full .text VirtualSize sweep; returns (insns, e8_calls)."""
    off = TEXT["raw"]
    insns = list(MD.disasm(DATA[off : off + TEXT["vsize"]], TEXT_LO))
    calls = []
    for ins in insns:
        if len(ins.bytes) >= 5 and ins.bytes[0] == 0xE8 and ins.mnemonic == "call":
            tgt = imm_target(ins)
            if tgt is not None:
                calls.append(
                    {
                        "site": ins.address,
                        "target": tgt,
                        "rel": struct.unpack_from("<i", ins.bytes, 1)[0],
                        "bytes": ins.bytes.hex(),
                    }
                )
    return insns, calls


def direct_sites_for(entry: int, calls=None):
    if calls is None:
        _, calls = full_e8_sweep()
    lo, hi, _ = cfg_extent(entry)
    sites = []
    for c in calls:
        if c["target"] != entry:
            continue
        site = c["site"]
        sites.append(
            {
                **c,
                "lo": lo,
                "hi": hi,
                "in_body": lo <= site < hi,
                "selfloop": site == entry,
                "ok": (not (lo <= site < hi)) and site != entry,
            }
        )
    return lo, hi, sites
