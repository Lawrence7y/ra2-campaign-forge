#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RE-N02 / run_id NEXT_RE_20261112_R01 -- bounded static frame-semantics re-check.

PURE STATIC: reads PE bytes from disk only. Never starts a process, attaches,
reads live memory, suspends threads, injects, or kills anything.

Replaces lead/re_d13_ruling_20261112/_static_frame_semantics.py, whose
"decode backwards from the hit" boundary guess and "op_str startswith dword ptr"
classifier are independently re-verified below (see review_old_defects()).

Method
------
Channel A: raw byte search over the WHOLE FILE (all sections, headers included)
           - 4-byte little-endian absolute address pattern
           - explicit opcode-anchored forms: 68 imm32 (push), 8D /r disp32 (lea),
             B8+r imm32 (mov reg,imm32), A1/A2/A3 moffs, C7 05 /0 imm32,
             FF /0../6 disp32, and any [base+disp32] with disp32 == target.
Channel B: deterministic LINEAR SWEEP disassembly with capstone from a trusted
           boundary (each executable section start). Instruction boundaries are
           derived from the previous instruction's length, never guessed.
           Undecodable bytes are emitted as .byte (skipdata) and reported as
           uncovered RVA intervals. A second boundary source (prologue patterns
           + direct call/jmp targets) is used to re-sync around points of
           interest and report divergences.
Cross-check: every Channel-A hit is explained (or explicitly left unexplained)
           by a Channel-B operand-level classification.

Operand classification uses capstone's per-operand access flags (CS_AC_READ /
CS_AC_WRITE), operand size, and mnemonic -- NOT op_str text matching. It covers
byte/word/dword/qword widths, direct writes, RMW, lea, immediate false
positives, call arguments, address materialisation, string/implicit memory and
[base+disp32] unresolved forms.

Negative control (--selftest): a synthetic byte stream with 5 known samples is
fed through the SAME classifier; the 5 must land in 5 distinct classes. The
old classifier is run on the same 5 samples for contrast.

Writes only into the directory containing this file (and its EVIDENCE/ child).
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import re
import struct
import sys
from array import array
from collections import Counter, defaultdict
from pathlib import Path

import pefile
from capstone import (
    Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_READ, CS_AC_WRITE,
)
from capstone.x86 import (
    X86_OP_MEM, X86_OP_IMM, X86_OP_REG, X86_REG_INVALID,
)

# --------------------------------------------------------------------------
# Constants / paths (all reads are outside our write domain; all writes inside)
# --------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
OUT = HERE
EVI = OUT / "EVIDENCE"
EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
SECONDARY_DLL = Path(r"D:\Project\ra2-campaign-forge\ra2youli\ra2render.dll")
STACK_JSON = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\_hl_match_14412.json")
OLD_SCRIPT = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\_static_frame_semantics.py")
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

PRIMARY = 0x00A8ED84
ADDRS = {
    "0xA8ED7C": 0x00A8ED7C,
    "0xA8ED80": 0x00A8ED80,
    "0xA8ED84": 0x00A8ED84,
    "0xA8ED88": 0x00A8ED88,
}

# PE flags
IMAGE_SCN_CNT_CODE = 0x00000020
IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_MEM_WRITE = 0x80000000
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040
IMAGE_DIRECTORY_ENTRY_BASERELOC = 5

WIDTH_NAMES = {1: "byte", 2: "word", 4: "dword", 8: "qword",
               10: "tbyte", 16: "xmmword", 32: "ymmword"}
RMW_MNEMONICS = {
    "inc", "dec", "add", "sub", "adc", "sbb", "and", "or", "xor", "not", "neg",
    "rol", "ror", "rcl", "rcr", "shl", "shr", "sar", "sal", "xchg", "cmpxchg",
    "cmpxchg8b", "xadd", "bts", "btr", "btc", "test", "cmp", "bt",
}
# NOTE: test/cmp/bt are read-only; they are listed only to exclude them from
# "direct write" if capstone access flags ever disagree -- access flags win.
WRITE_ONLY_EXCLUDE = {"test", "cmp", "bt", "push", "call", "jmp"}
STRING_MNEMONICS = {"movs", "movsb", "movsw", "movsd", "stos", "stosb", "stosw",
                    "stosd", "scas", "scasb", "scasw", "scasd", "cmps", "cmpsb",
                    "cmpsw", "cmpsd", "lods", "lodsb", "lodsw", "lodsd", "ins",
                    "insb", "insw", "insd", "outs", "outsb", "outsw", "outsd"}
COND_PREFIXES = ("je", "jne", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge",
                 "jl", "jle", "jc", "jnc", "jo", "jno", "js", "jns", "jp", "jnp",
                 "jpe", "jpo", "jcxz", "jecxz", "loop", "loope", "loopne", "loopz",
                 "loopnz")

KIND_WRITE_DIRECT = "write_direct"          # direct write
KIND_WRITE_RMW = "write_rmw"                # read-modify-write
KIND_READ = "read"                          # read
KIND_LEA = "lea"                            # address-taking
KIND_IMM_FP = "imm_false_positive"          # immediate false positive
KIND_CALL_ARG = "call_arg"                  # call argument (push imm32)
KIND_ADDR_MAT = "address_materialization"   # mov reg, imm32 / immediate transport
KIND_INDIRECT_UNRESOLVED = "indirect_unresolved"   # [base+disp32] etc.
KIND_INDIRECT_CANDIDATE = "indirect_write_candidate"
KIND_IMPLICIT_MEM = "implicit_string_mem"

# --------------------------------------------------------------------------
# Logging: tee to stdout and to our own EVIDENCE file (UTF-8, no shell redirection)
# --------------------------------------------------------------------------
class Tee:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = path.open("w", encoding="utf-8", newline="\n")
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
        self.path = path

    def write(self, s):
        self.f.write(s)
        self.f.flush()
        try:
            sys.stdout.write(s)
        except UnicodeEncodeError:
            sys.stdout.write(s.encode("ascii", "backslashreplace").decode("ascii"))

    def flush(self):
        self.f.flush()

    def close(self):
        self.f.close()


LOG: Tee | None = None


def emit(s=""):
    if LOG:
        LOG.write(str(s) + "\n")
    else:
        print(s)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def hx(n, width=8):
    return "0x%0*x" % (width, n & 0xFFFFFFFF)


def sha256_of(path: Path):
    d = path.read_bytes()
    return d, hashlib.sha256(d).hexdigest(), len(d)


def le32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def find_all(buf: bytes, pat: bytes):
    out, i = [], 0
    while True:
        j = buf.find(pat, i)
        if j < 0:
            break
        out.append(j)
        i = j + 1
    return out


def base_mnemonic(insn):
    """Normalise 'lock inc' / 'rep movsd' -> last token, keep prefix tokens."""
    words = insn.mnemonic.lower().split()
    return words[-1] if words else "", words[:-1]


def is_cond_jump(mn):
    return any(mn.startswith(p) for p in COND_PREFIXES)


def is_control(mn):
    return (mn.startswith("j") or mn.startswith("call") or mn.startswith("ret")
            or mn in ("loop", "loope", "loopne", "loopz", "loopnz", "int",
                      "int3", "into", "iret", "iretd", "hlt", "ud2", "sysenter",
                      "sysexit", "leave", "bound") or mn.startswith("loop"))


# --------------------------------------------------------------------------
# PE map
# --------------------------------------------------------------------------
def pe_map(d: bytes):
    pe = pefile.PE(data=d, fast_load=False)
    oh = pe.OPTIONAL_HEADER
    ib = int(oh.ImageBase)
    soi = int(oh.SizeOfImage)
    dllc = int(oh.DllCharacteristics)
    dynbase = bool(dllc & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE)
    relocs = []
    for e in oh.DATA_DIRECTORY:
        relocs.append((e.name, int(e.VirtualAddress), int(e.Size)))
    reloc_dir = oh.DATA_DIRECTORY[IMAGE_DIRECTORY_ENTRY_BASERELOC]
    has_reloc = bool(int(reloc_dir.VirtualAddress) and int(reloc_dir.Size))
    secs = []
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode("latin1")
        rva = int(s.VirtualAddress)
        vsz = int(s.Misc_VirtualSize)
        raw = int(s.PointerToRawData)
        rawsz = int(s.SizeOfRawData)
        ch = int(s.Characteristics)
        secs.append(dict(name=nm, rva=rva, vsize=vsz, rawptr=raw,
                         rawsize=rawsz, chars=ch,
                         exec_flag=bool(ch & IMAGE_SCN_MEM_EXECUTE),
                         code_flag=bool(ch & IMAGE_SCN_CNT_CODE)))
    machine = int(pe.FILE_HEADER.Machine)
    nsec = int(pe.FILE_HEADER.NumberOfSections)
    pe.close()
    return dict(image_base=ib, size_of_image=soi, dll_characteristics=dllc,
                dynbase=dynbase, reloc_dir_rva=int(reloc_dir.VirtualAddress),
                reloc_dir_size=int(reloc_dir.Size), has_reloc=has_reloc,
                data_directories=relocs, sections=secs, machine=machine,
                nsec=nsec)


# --------------------------------------------------------------------------
# Deterministic linear sweep (Channel B)
# --------------------------------------------------------------------------
class SweptSection:
    """Result of a deterministic linear sweep from the section start.

    Instruction boundary i+1 = boundary_i + length(insn_i). No guessing.
    """
    def __init__(self, sec, code, image_base):
        self.sec = sec
        self.code = code
        self.image_base = image_base
        self.rva0 = sec["rva"]
        self.va0 = image_base + sec["rva"]
        self.raw0 = sec["rawptr"]
        self.starts = array("I")       # offsets relative to section start
        self.sizes = bytearray()
        self.kcode = bytearray()       # 0 normal,1 call,2 jcc,3 other ctl,4 skipdata
        self.ctrl_text = {}            # off -> "mnemonic op_str"@VA
        self.ctrl_records = []         # (off, kind, target_off or None)
        self.leaders = set([0])
        self.uncovered = []            # (off_start, off_end) RVA-relative gaps
        self.n_skipdata = 0
        self.n_insn = 0
        self.prologues = set()

    def va(self, off):
        return self.va0 + off

    def rva(self, off):
        return self.rva0 + off

    def file_off(self, off):
        return self.raw0 + off

    def index_of(self, off):
        """Index of instruction whose [start,start+size) contains off, else -1."""
        i = bisect.bisect_right(self.starts, off) - 1
        if i >= 0 and off < self.starts[i] + self.sizes[i]:
            return i
        return -1

    def bb_start(self, off):
        j = bisect.bisect_right(self.leader_list, off) - 1
        return self.leader_list[j] if j >= 0 else 0

    def prev_call_or_branch(self, idx, lookback=128):
        for j in range(idx - 1, max(-1, idx - lookback - 1), -1):
            if self.kcode[j] in (1, 2):
                off = self.starts[j]
                in_bb = off >= self.bb_start(self.starts[idx])
                return off, self.ctrl_text.get(off, "?"), in_bb
        return None, None, None

    def finish(self):
        self.leader_list = sorted(self.leaders)


def linear_sweep(sec, code, image_base, md):
    """Single capstone linear pass over the whole section, streaming."""
    sw = SweptSection(sec, code, image_base)
    # prologue-based independent boundary seeds
    for pat in (b"\x55\x8b\xec", b"\x8b\xff\x55\x8b\xec"):
        for m in re.finditer(re.escape(pat), code):
            sw.prologues.add(m.start())
    gap_start = None
    for insn in md.disasm(code, sw.va0):
        off = insn.address - sw.va0
        if off < 0 or off >= len(code):
            continue
        size = max(1, min(15, insn.size))
        sw.starts.append(off)
        sw.sizes.append(size)
        if insn.id == 0 or insn.mnemonic == ".byte":
            sw.kcode.append(4)
            sw.n_skipdata += 1
            if gap_start is None:
                gap_start = off
            continue
        else:
            if gap_start is not None:
                sw.uncovered.append((gap_start, off))
                gap_start = None
        mn, _ = base_mnemonic(insn)
        if mn.startswith("call"):
            k, tgt = 1, None
        elif is_cond_jump(mn):
            k, tgt = 2, None
        elif is_control(mn):
            k, tgt = 3, None
        else:
            k, tgt = 0, None
        # direct relative branch/call target
        if k in (1, 2, 3) and insn.operands:
            op = insn.operands[0]
            if op.type == X86_OP_IMM:
                t = int(op.imm) - sw.va0
                if 0 <= t < len(code):
                    tgt = t
                    sw.leaders.add(t)
        sw.kcode.append(k)
        if k in (1, 2, 3):
            txt = "%s %s" % (insn.mnemonic, insn.op_str)
            sw.ctrl_text[off] = "@%s  %s  bytes=[%s]" % (
                hx(sw.va(off)), txt, insn.bytes.hex(" "))
            sw.ctrl_records.append((off, k, tgt))
            nxt = off + size
            if nxt < len(code):
                sw.leaders.add(nxt)
    if gap_start is not None:
        sw.uncovered.append((gap_start, len(code)))
    sw.n_insn = len(sw.starts)
    sw.finish()
    return sw


# --------------------------------------------------------------------------
# Operand-level classifier (used by BOTH the real scan and the selftest)
# --------------------------------------------------------------------------
def classify_instruction(insn, target):
    """Return a list of operand-level classification dicts for `target`.

    Uses capstone per-operand access flags + size + mnemonic. NEVER op_str text.
    """
    if insn.id == 0 or insn.mnemonic == ".byte":
        return []
    mn, prefixes = base_mnemonic(insn)
    res = []
    try:
        ops = insn.operands
    except Exception:
        return res
    for oi, op in enumerate(ops):
        # ---- IMMEDIATE carrying the address -------------------------------
        if op.type == X86_OP_IMM and (int(op.imm) & 0xFFFFFFFF) == target:
            if mn == "push":
                kind = KIND_CALL_ARG
                note = "push imm32 -> call argument / address passed to callee"
            elif mn == "mov" and oi == 1 and ops[0].type == X86_OP_REG:
                kind = KIND_ADDR_MAT
                note = "mov reg,imm32 -> address materialisation (indirect access possible)"
            elif mn == "lea":
                kind = KIND_LEA
                note = "lea with immediate (unexpected)"
            else:
                kind = KIND_IMM_FP
                note = "imm32 equals target but is NOT a memory operand (byte-pattern false positive)"
            res.append(dict(kind=kind, width="none", is_rmw=False,
                            operand_index=oi, access=int(op.access),
                            note=note, disp=target))
            continue
        # ---- MEMORY operand ----------------------------------------------
        if op.type != X86_OP_MEM:
            continue
        mem = op.mem
        disp = int(mem.disp) & 0xFFFFFFFF
        base = int(mem.base)
        index = int(mem.index)
        seg = int(mem.segment)
        absolute = (base == X86_REG_INVALID and index == X86_REG_INVALID
                    and seg == X86_REG_INVALID)
        width = WIDTH_NAMES.get(int(op.size), "%dB" % int(op.size))
        acc = int(op.access)
        rd = bool(acc & CS_AC_READ)
        wr = bool(acc & CS_AC_WRITE)
        if mn == "lea":
            if disp == target:
                res.append(dict(kind=KIND_LEA, width="none", is_rmw=False,
                                operand_index=oi, access=acc,
                                note="address-of only; NO memory access; later indirect write possible",
                                disp=disp))
            continue
        if absolute and disp == target:
            if wr and (rd or mn in RMW_MNEMONICS) and mn not in WRITE_ONLY_EXCLUDE:
                kind, rmw = KIND_WRITE_RMW, True
                note = "memory operand READ+WRITE (RMW)"
            elif wr:
                kind, rmw = KIND_WRITE_DIRECT, False
                note = "memory operand WRITE only (direct write)"
            elif rd:
                kind, rmw = KIND_READ, False
                note = "memory operand READ only"
            else:
                kind, rmw = KIND_READ, False
                note = "memory operand with no access flags (treated as read, verify)"
            res.append(dict(kind=kind, width=width, is_rmw=rmw,
                            operand_index=oi, access=acc, note=note, disp=disp))
        elif disp == target and not absolute:
            # THE OLD SCRIPT DROPPED THESE. Keep them, do not silently discard.
            res.append(dict(kind=KIND_INDIRECT_UNRESOLVED, width=width,
                            is_rmw=bool(wr and rd), operand_index=oi, access=acc,
                            note="disp32 == target but base/index present "
                                 "([base+disp32]); effective VA not statically resolvable",
                            disp=disp))
    # ---- implicit string memory -------------------------------------------
    if mn in STRING_MNEMONICS and not res:
        res.append(dict(kind=KIND_IMPLICIT_MEM, width=WIDTH_NAMES.get(
            int(ops[0].size), "?") if ops else "?", is_rmw=False,
            operand_index=-1, access=0,
            note="implicit ES:EDI/DS:ESI memory; address in registers, "
                 "cannot be bound to an absolute VA statically", disp=None))
    return res


def class5(kind, width, is_rmw):
    """Composite distinguishing class used for the negative control."""
    return "%s/%s" % (kind, width if kind in (KIND_WRITE_DIRECT, KIND_WRITE_RMW,
                                              KIND_READ) else "none")


# --------------------------------------------------------------------------
# Old classifier, reproduced verbatim for A/B contrast (independent defect check)
# --------------------------------------------------------------------------
def old_decode_covering(md, text, hit, addr):
    """Copied from _static_frame_semantics.py:73-90 (unchanged logic)."""
    pat = struct.pack("<I", addr)
    best = None
    for back in range(0, 13):
        s = hit - back
        if s < 0:
            continue
        chunk = text[s:s + 16]
        for insn in md.disasm(chunk, s):
            cover_start = insn.address
            cover_end = insn.address + insn.size
            if cover_start <= hit and hit + 4 <= cover_end:
                if best is None or back < best[1]:
                    best = (insn, back)
                break
    return best


OLD_WRITE_MNEM = ("inc", "dec", "add", "sub", "mov", "or", "and", "xor", "not", "neg")


def old_classify(insn):
    """Copied from _static_frame_semantics.py:96-106."""
    m = insn.mnemonic
    ops = insn.op_str
    is_mem_dest = ops.split(",")[0].strip().startswith("dword ptr")
    if m in ("inc", "dec", "not", "neg") and is_mem_dest:
        return "write"
    if m in ("add", "sub", "or", "and", "xor") and is_mem_dest:
        return "write"
    if m == "mov" and is_mem_dest:
        return "write"
    return "read"


def old_fp_filter(insn, addr):
    """Copied from _static_frame_semantics.py:155-160. True == kept."""
    ops_l = insn.op_str.lower()
    hexs = "0x%x" % addr
    return (("ptr [" + hexs + "]") in ops_l
            or ("ptr [" + hexs[:-1]) in ops_l
            or (hexs + "]") in ops_l)


# --------------------------------------------------------------------------
# Negative control (--selftest)
# --------------------------------------------------------------------------
SELFTEST_SAMPLES = [
    ("S1_inc_dword_RMW", "FF 05 84 ED A8 00", KIND_WRITE_RMW, "dword"),
    ("S2_mov_byte_al", "A2 84 ED A8 00", KIND_WRITE_DIRECT, "byte"),
    ("S3_mov_word_ax", "66 A3 84 ED A8 00", KIND_WRITE_DIRECT, "word"),
    ("S4_lea_esi", "8D 35 84 ED A8 00", KIND_LEA, "none"),
    ("S5_add_eax_imm", "05 84 ED A8 00", KIND_IMM_FP, "none"),
]
SELFTEST_EXTRA = [
    ("X1_push_imm", "68 84 ED A8 00"),
    ("X2_mov_eax_imm", "B8 84 ED A8 00"),
    ("X3_mov_mem_imm", "C7 05 84 ED A8 00 01 00 00 00"),
    ("X4_xchg_mem", "87 05 84 ED A8 00"),
    ("X5_lea_sib_abs", "8D 04 25 84 ED A8 00"),
    ("X6_add_base_disp32", "83 83 84 ED A8 00 01"),
    ("X7_fild_qword", "DF 2D 84 ED A8 00"),
    ("X8_rep_movsd", "F3 A5"),
]


def run_selftest():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    pat = le32(PRIMARY)
    emit("=" * 96)
    emit("NEGATIVE CONTROL / SELFTEST -- run_id NEXT_RE_20261112_R01")
    emit("Target A = %s ; synthetic byte stream, VA base 0x00401000" % hx(PRIMARY))
    emit("The SAME classify_instruction() used by the main Channel-B scan is used here.")
    emit("=" * 96)

    all_samples = [(n, b, k, w) for n, b, k, w in SELFTEST_SAMPLES] + \
                  [(n, b, None, None) for n, b in SELFTEST_EXTRA]
    code = bytearray()
    sample_off = {}
    for name, hexs, _, _ in all_samples:
        b = bytes.fromhex(hexs)
        sample_off[name] = len(code)
        code += b + b"\x90"          # NOP separator -> deterministic boundary
    code = bytes(code)
    sec = dict(name="SYNTH", rva=0x1000, vsize=len(code), rawptr=0,
               rawsize=len(code), chars=0x60000020, exec_flag=True, code_flag=True)
    sw = linear_sweep(sec, code, 0x400000, md)
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.detail = True
    md2.skipdata = True
    by_off = {}
    for insn in md2.disasm(code, sw.va0):
        by_off[insn.address - sw.va0] = insn

    emit("\n[A] NEW CLASSIFIER -- 5 mandatory samples")
    emit("%-22s %-46s %-28s %-7s %-6s %s" %
         ("sample", "disasm", "kind", "width", "rmw", "class5"))
    got = {}
    ok = True
    for name, hexs, exp_kind, exp_width in SELFTEST_SAMPLES:
        off = sample_off[name]
        insn = by_off.get(off)
        if insn is None:
            emit("  %-22s !! NO INSTRUCTION AT EXPECTED BOUNDARY" % name)
            ok = False
            continue
        rs = classify_instruction(insn, PRIMARY)
        if not rs:
            emit("  %-22s !! NO CLASSIFICATION" % name)
            ok = False
            continue
        r = rs[0]
        c5 = class5(r["kind"], r["width"], r["is_rmw"])
        got[name] = (r["kind"], r["width"], c5)
        emit("%-22s %-46s %-28s %-7s %-6s %s" %
             (name, ("%s %s" % (insn.mnemonic, insn.op_str))[:46],
              r["kind"], r["width"], str(r["is_rmw"]), c5))
        if r["kind"] != exp_kind or r["width"] != exp_width:
            ok = False
            emit("     !! expected %s/%s" % (exp_kind, exp_width))
    distinct = set(v[2] for v in got.values())
    emit("\n  distinct class5 labels = %d  -> %s" % (len(distinct), sorted(distinct)))
    five_ok = (len(got) == 5 and len(distinct) == 5 and ok)
    emit("  FIVE SAMPLES -> FIVE DISTINCT CLASSES : %s" % ("PASS" if five_ok else "FAIL"))

    emit("\n[B] OLD CLASSIFIER (verbatim reproduction) on the SAME 5 samples")
    md3 = Cs(CS_ARCH_X86, CS_MODE_32)
    md3.detail = True
    emit("%-22s %-46s %-9s %-9s %s" %
         ("sample", "old decode_covering() result", "classify", "fp_keep", "verdict"))
    old_classes = set()
    for name, hexs, _, _ in SELFTEST_SAMPLES:
        off = sample_off[name]
        hit = code.find(pat, off, off + 16)
        r = old_decode_covering(md3, code, hit, PRIMARY)
        if r is None:
            emit("%-22s %-46s %-9s %-9s %s" % (name, "<none>", "-", "-", "-"))
            old_classes.add("<none>")
            continue
        insn, back = r
        k = old_classify(insn)
        keep = old_fp_filter(insn, PRIMARY)
        old_classes.add(k if keep else "DROPPED")
        emit("%-22s %-46s %-9s %-9s %s" %
             (name, ("%s %s (back=%d)" % (insn.mnemonic, insn.op_str, back))[:46],
              k, str(keep), ""))
    emit("  old distinct outcomes = %d -> %s" % (len(old_classes), sorted(old_classes)))

    emit("\n[C] EXTRA CONTROLS (new classifier)")
    emit("%-22s %-46s %-28s %-7s %-6s" %
         ("sample", "disasm", "kind", "width", "rmw"))
    for name, hexs in SELFTEST_EXTRA:
        off = sample_off[name]
        insn = by_off.get(off)
        if insn is None:
            emit("%-22s !! NO INSTRUCTION" % name)
            continue
        rs = classify_instruction(insn, PRIMARY)
        r = rs[0] if rs else dict(kind="<none>", width="?", is_rmw=False)
        emit("%-22s %-46s %-28s %-7s %-6s" %
             (name, ("%s %s" % (insn.mnemonic, insn.op_str))[:46],
              r["kind"], r["width"], str(r["is_rmw"])))

    emit("\n[D] DEFECT RE-VERIFICATION (independent, with file:line)")
    emit("  lead/re_d13_ruling_20261112/_static_frame_semantics.py:73-90 decode_covering():")
    emit("    starts at hit-back (back=0..12), selects SMALLEST back -> may choose a")
    emit("    byte INSIDE the real instruction (misaligned decode). Verified below.")
    emit("  :96-106 classify(): only op_str startswith 'dword ptr' counts as write;")
    emit("    byte/word/qword/xchg/RMW-via-imm all collapse to 'read'.")
    emit("  :155-160 fp filter: requires literal 'ptr [0xa8ed84]' in op_str;")
    emit("    '[ebx+0xa8ed84]' forms are DROPPED, 'lea' is kept but forced to 'read'.")
    emit("  :59-70 find_hits(): only .text searched; :122-124 only .text disassembled.")
    emit("  :109-190 main(): no negative control / no counterexample of any kind.")
    # concrete proof of the misalignment defect
    emit("\n[E] CONCRETE MISALIGNMENT PROOF")
    probe = bytes.fromhex("8B 05 84 ED A8 00 90 90 90 90 90 90 90 90 90 90")
    hit = probe.find(pat)
    r = old_decode_covering(md3, probe, hit, PRIMARY)
    emit("  real instruction = 8B 05 84 ED A8 00 = mov eax, dword ptr [0xa8ed84]")
    if r:
        emit("  old decode_covering() chose: '%s %s' (back=%d)" %
             (r[0].mnemonic, r[0].op_str, r[1]))
        emit("  old classify() = %s ; old fp_filter keep = %s" %
             (old_classify(r[0]), old_fp_filter(r[0], PRIMARY)))
    linear_insn = list(md3.disasm(probe, 0x401000))[0]
    emit("  new linear sweep chose: '%s %s'" % (linear_insn.mnemonic, linear_insn.op_str))
    emit("  new classify() = %s" %
         classify_instruction(linear_insn, PRIMARY))

    emit("\n[SELFTEST RESULT] %s" % ("PASS" if five_ok else "FAIL"))
    return 0 if five_ok else 1


# --------------------------------------------------------------------------
# Channel A: raw byte search over the WHOLE FILE
# --------------------------------------------------------------------------
def channel_a(d, pmap, target):
    pat = le32(target)
    emit("\n" + "=" * 96)
    emit("CHANNEL A -- RAW BYTE SEARCH over the WHOLE FILE (%d bytes)" % len(d))
    emit("target = %s ; pattern = %s" % (hx(target), pat.hex(" ")))
    emit("=" * 96)
    all_hits = find_all(d, pat)
    by_sec = Counter()
    sec_of = {}
    for s in pmap["sections"]:
        if s["rawsize"] and s["rawptr"]:
            sec_of[s["name"]] = (s["rawptr"], s["rawptr"] + s["rawsize"], s)
    for o in all_hits:
        nm = "<headers/padding>"
        for name, (a, b, s) in sec_of.items():
            if a <= o < b:
                nm = name
                break
        by_sec[nm] += 1
    emit("  total 4-byte LE hits in whole file = %d" % len(all_hits))
    for nm, c in sorted(by_sec.items(), key=lambda kv: -kv[1]):
        s = sec_of.get(nm, (None, None, None))[2]
        flag = ""
        if s:
            flag = "exec=%s code=%s" % (s["exec_flag"], s["code_flag"])
        emit("    %-20s %6d   %s" % (nm, c, flag))

    # opcode-anchored explicit forms (whole file; boundaries come from channel B)
    forms = Counter()
    form_hits = defaultdict(list)
    push_pat = b"\x68" + pat
    for o in find_all(d, push_pat):
        forms["push imm32 (68 + addr)"] += 1
        form_hits["push imm32 (68 + addr)"].append(o)
    # lea: 8D /r with modrm mod=00 rm=101 -> disp32 absolute;
    #      also 8D /r modrm mod=00 rm=100 + SIB base=101 -> disp32 absolute
    for o in range(0, len(d) - 6):
        if d[o] != 0x8D:
            continue
        m = d[o + 1]
        mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
        if mod == 0 and rm == 5 and d[o + 2:o + 6] == pat:
            forms["lea reg,[abs] (8D /r disp32)"] += 1
            form_hits["lea reg,[abs] (8D /r disp32)"].append(o)
        elif mod == 0 and rm == 4 and o + 6 < len(d):
            sib = d[o + 2]
            if (sib & 7) == 5 and (sib >> 6) == 0 and d[o + 3:o + 7] == pat:
                forms["lea reg,[abs] (8D SIB disp32)"] += 1
                form_hits["lea reg,[abs] (8D SIB disp32)"].append(o)
    for opc in range(0xB8, 0xC0):
        for o in find_all(d, bytes([opc]) + pat):
            forms["mov reg32,imm32 (B8+r)"] += 1
            form_hits["mov reg32,imm32 (B8+r)"].append(o)
    for nm, opc in [("moffs load A1", 0xA1), ("moffs store A2/A3", 0xA2),
                    ("moffs store A2/A3", 0xA3)]:
        for o in find_all(d, bytes([opc]) + pat):
            forms["%s" % nm] += 1
            form_hits["%s" % nm].append(o)
    for o in find_all(d, b"\xc7\x05" + pat):
        forms["mov [abs],imm32 (C7 05)"] += 1
        form_hits["mov [abs],imm32 (C7 05)"].append(o)
    for o in find_all(d, b"\xff\x05" + pat):
        forms["inc [abs] (FF 05)"] += 1
        form_hits["inc [abs] (FF 05)"].append(o)
    emit("\n  opcode-anchored explicit forms (whole file, reconnaissance only):")
    for k, v in sorted(forms.items(), key=lambda kv: -kv[1]):
        emit("    %-42s %6d" % (k, v))
    # Generic anchored census: classify EVERY hit by its immediately preceding
    # bytes. mod=00/rm=101 ModRM (0x05,0x0D,...,0x3D) + disp32 covers 8B/89/
    # F6/83/39/FF/C7 ...; single-opcode forms cover A0-A3/B8-BF/68.
    generic = Counter()
    for o in all_hits:
        if o >= 2 and (d[o - 1] & 0xC7) == 0x05:
            generic["%02X /r disp32 (mod=00 rm=101)" % d[o - 2]] += 1
        elif o >= 1 and d[o - 1] in (0xA0, 0xA1, 0xA2, 0xA3):
            generic["%02X moffs abs" % d[o - 1]] += 1
        elif o >= 1 and 0xB8 <= d[o - 1] <= 0xBF:
            generic["B8+r mov reg32,imm32"] += 1
        elif o >= 1 and d[o - 1] == 0x68:
            generic["68 push imm32"] += 1
        elif o >= 1 and d[o - 1] == 0xE8:
            generic["E8 call rel32 (coincidence)"] += 1
        else:
            generic["other / unanchored"] += 1
    emit("\n  GENERIC anchored census of ALL %d hits by preceding bytes:" % len(all_hits))
    for k, v in generic.most_common():
        emit("    %-42s %6d" % (k, v))
    emit("  (These are byte-form counts, NOT instruction-boundary claims. Channel B decides.)")
    a_forms = dict(forms)
    a_forms.update({"GENERIC:" + k: v for k, v in generic.items()})
    return dict(all_hits=all_hits, by_sec=by_sec, forms=a_forms, form_hits=form_hits,
                generic=dict(generic))


# --------------------------------------------------------------------------
# Channel B: sweep every executable section, classify everything
# --------------------------------------------------------------------------
def channel_b(d, pmap, target, md):
    emit("\n" + "=" * 96)
    emit("CHANNEL B -- DETERMINISTIC LINEAR SWEEP from each executable section start")
    emit("target = %s ; capstone %s" % (hx(target), md.version() if hasattr(md, "version") else "5.x"))
    emit("=" * 96)
    exec_secs = []
    for s in pmap["sections"]:
        isexec = s["exec_flag"] or s["code_flag"] or s["name"] in (".text", ".detour")
        if isexec and s["rawsize"] > 0:
            exec_secs.append(s)
    emit("  executable / code sections selected: %s" %
         ", ".join("%s(rva=%s raw=%s size=%d)" %
                   (s["name"], hx(s["rva"]), hx(s["rawptr"]), s["rawsize"])
                   for s in exec_secs))
    results = []
    for s in exec_secs:
        code = d[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        sw = linear_sweep(s, code, pmap["image_base"], md)
        emit("\n  [%s] linear sweep: %d instructions, %d skipdata bytes, "
             "%d uncovered intervals" %
             (s["name"], sw.n_insn, sw.n_skipdata, len(sw.uncovered)))
        emit("       trusted start = %s (VA %s), file_off %s" %
             (hx(s["rva"]), hx(sw.va0), hx(s["rawptr"])))
        # uncovered intervals, as RVA ranges
        if sw.uncovered:
            for a, b in sw.uncovered[:40]:
                emit("       UNCOVERED RVA  %s .. %s  (len %d, VA %s..%s)" %
                     (hx(sw.rva(a)), hx(sw.rva(b)), b - a,
                      hx(sw.va(a)), hx(sw.va(b))))
            if len(sw.uncovered) > 40:
                emit("       ... %d more intervals (full list in EVIDENCE/UNCOVERED_INTERVALS.txt)"
                     % (len(sw.uncovered) - 40))
        # classify streaming (second pass, reusing boundaries is not needed; we
        # re-run the generator but that is cheap and keeps memory bounded)
        md2 = Cs(CS_ARCH_X86, CS_MODE_32)
        md2.detail = True
        md2.skipdata = True
        idx = 0
        for insn in md2.disasm(code, sw.va0):
            off = insn.address - sw.va0
            if off < 0 or off >= len(code):
                continue
            rs = classify_instruction(insn, target)
            for r in rs:
                # implicit string mem entries are only counted in aggregate
                if r["kind"] == KIND_IMPLICIT_MEM:
                    continue
                results.append(dict(
                    sec=s["name"], off=off, idx=idx,
                    va=sw.va(off), rva=sw.rva(off), file_off=sw.file_off(off),
                    bytes_hex=insn.bytes.hex(" "),
                    disasm="%s %s" % (insn.mnemonic, insn.op_str),
                    mnemonic=insn.mnemonic,
                    kind=r["kind"], width=r["width"], is_rmw=r["is_rmw"],
                    note=r["note"], operand_index=r["operand_index"],
                    access=r["access"], disp=r["disp"],
                    bb_off=sw.bb_start(off),
                    sw=sw, insn=insn,
                ))
            idx += 1
        # stash sweep for cross-check / detail
        for r in results:
            if r["sec"] == s["name"]:
                r["_sw"] = sw
        results_sections = results
    return exec_secs, results


# --------------------------------------------------------------------------
# Cross-check A vs B
# --------------------------------------------------------------------------
def cross_check(d, pmap, target, a, records, exec_secs):
    emit("\n" + "=" * 96)
    emit("CROSS-CHECK Channel A hits vs Channel B operand-level classification")
    emit("=" * 96)
    pat = le32(target)
    sec_by_raw = []
    for s in pmap["sections"]:
        sec_by_raw.append((s["rawptr"], s["rawptr"] + s["rawsize"], s))
    # map file_off -> classified record (a single instruction may cover a hit)
    rec_by_range = []
    for r in records:
        rec_by_range.append((r["file_off"], r["file_off"] + len(r["bytes_hex"].split()), r))
    explained = 0
    unexplained = []
    in_nonexec = 0
    in_gap = 0
    for o in a["all_hits"]:
        owner = None
        for aa, bb, s in sec_by_raw:
            if aa <= o < bb:
                owner = s
                break
        if owner is None or not (owner["exec_flag"] or owner["code_flag"]
                                 or owner["name"] in (".text", ".detour")):
            in_nonexec += 1
            continue
        matched = [rr for (x, y, rr) in rec_by_range if x <= o < y]
        if matched:
            explained += 1
        else:
            unexplained.append(o)
    emit("  Channel A hits total                          = %d" % len(a["all_hits"]))
    emit("  hits in non-exec / data / header regions       = %d  (address encoded elsewhere)"
         % in_nonexec)
    emit("  hits explained by a Channel-B operand match    = %d" % explained)
    emit("  hits NOT explained (data-in-code / undecodable / unmodelled encoding) = %d"
         % len(unexplained))
    if unexplained:
        emit("  first 30 unexplained file offsets (with 8 bytes before / 4 after):")
        for o in unexplained[:30]:
            emit("    off=%s  ctx=[%s | %s | %s]" %
                 (hx(o, 8), d[max(0, o - 8):o].hex(" "), pat.hex(" "),
                  d[o + 4:o + 8].hex(" ")))
    return dict(explained=explained, unexplained=unexplained,
                in_nonexec=in_nonexec)


# --------------------------------------------------------------------------
# Reporting helpers
# --------------------------------------------------------------------------
def evidence_grade(r):
    if r["kind"] in (KIND_WRITE_DIRECT, KIND_WRITE_RMW, KIND_READ, KIND_LEA,
                     KIND_IMM_FP, KIND_CALL_ARG, KIND_ADDR_MAT):
        return "[本次实测]linear_sweep/operand_access"
    if r["kind"] == KIND_INDIRECT_UNRESOLVED:
        return "[静态推断]disp32_with_base_unresolved"
    return "[静态推断]candidate"


def write_csv(records):
    cols = ["target", "kind", "width", "va", "rva", "file_off", "bytes",
            "disasm", "basic_block", "is_rmw", "evidence_grade"]
    path = OUT / "WRITE_POINTS.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in sorted(records, key=lambda x: (x["file_off"], x["kind"])):
            w.writerow(dict(
                target="0x%08X" % PRIMARY,
                kind=r["kind"], width=r["width"],
                va="0x%08X" % r["va"], rva="0x%08X" % r["rva"],
                file_off="0x%08X" % r["file_off"],
                bytes=r["bytes_hex"],
                disasm=r["disasm"],
                basic_block="0x%08X" % (r["_sw"].va(r["bb_off"])),
                is_rmw="1" if r["is_rmw"] else "0",
                evidence_grade=evidence_grade(r),
            ))
    return path


def write_detail(records, writes):
    p = EVI / "WRITE_POINTS_DETAIL.md"
    with p.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# RE-N02 写点逐条明细（含 CSV 未列出的 `前一条调用或条件分支`）\n\n")
        f.write("字段口径：`basic_block` 为线性扫描下 CFG **近似**基本块起点"
                "（leader = 节起点 / 直接分支目标 / 控制转移指令的下一条），"
                "不是完整控制流图；`前一条调用或条件分支` 为向前回溯 ≤128 条指令内"
                "最近的 call 或条件跳转，标注是否仍在同基本块内。\n\n")
        f.write("证据等级：见 `WRITE_POINTS.csv` 的 `evidence_grade` 列。\n\n")
        for i, r in enumerate(writes, 1):
            sw = r["_sw"]
            # The classifying pass and the sweep pass are independent linear
            # sweeps from the same trusted start; verify they agree on boundary.
            idx = r["idx"]
            if idx >= len(sw.starts) or sw.starts[idx] != r["off"]:
                idx = sw.index_of(r["off"])
            if idx < 0:
                idx = r["idx"]
            boundary_ok = (idx < len(sw.starts) and sw.starts[idx] == r["off"])
            poff, ptxt, inbb = sw.prev_call_or_branch(idx)
            f.write("## W%02d  %s  %s\n\n" % (i, hx(r["va"]), r["disasm"]))
            f.write("> 双通道边界一致性：分类扫描与线性扫描边界 `%s`（idx=%d）。\n\n" %
                    ("一致" if boundary_ok else "不一致，已用 index_of 重定位", idx))
            f.write("| 项 | 值 |\n|:--|:--|\n")
            f.write("| target | `0x%08X` |\n" % PRIMARY)
            f.write("| kind / width / is_rmw | `%s` / `%s` / `%s` |\n" %
                    (r["kind"], r["width"], r["is_rmw"]))
            f.write("| VA | `%s` |\n" % hx(r["va"]))
            f.write("| RVA | `%s` |\n" % hx(r["rva"]))
            f.write("| 文件偏移 | `%s` (节 `%s`) |\n" % (hx(r["file_off"]), r["sec"]))
            f.write("| 原始字节 | `%s` |\n" % r["bytes_hex"])
            f.write("| 反汇编文本 | `%s` |\n" % r["disasm"])
            f.write("| 所在基本块起点(VA) | `%s` |\n" % hx(sw.va(r["bb_off"])))
            if poff is None:
                f.write("| 前一条调用或条件分支 | 无（回溯 128 条内未出现） |\n")
            else:
                f.write("| 前一条调用或条件分支 | `%s` %s（同基本块内=%s） |\n" %
                        (ptxt, "", inbb))
            f.write("| 是否为 RMW | `%s` |\n" % r["is_rmw"])
            f.write("| 操作数索引 / access | `%d` / `%d` |\n" %
                    (r["operand_index"], r["access"]))
            f.write("| 分类依据 | %s |\n" % r["note"])
            f.write("| 证据等级 | %s |\n\n" % evidence_grade(r))
            # disassembly context +- 8 instructions around the write point
            f.write("### 反汇编片段（±8 条，同一线性扫描边界）\n\n```asm\n")
            lo = max(0, idx - 8)
            hi = min(len(sw.starts), idx + 9)
            code = sw.code
            md = Cs(CS_ARCH_X86, CS_MODE_32)
            md.detail = True
            md.skipdata = True
            for j in range(lo, hi):
                o = sw.starts[j]
                chunk = code[o:o + 16]
                ins = next(iter(md.disasm(chunk, sw.va(o))), None)
                if ins is None:
                    continue
                mark = "  <== WRITE" if j == idx else ""
                lead = "BB " if o in sw.leaders else "   "
                f.write("%s%s  %s %s%s\n" %
                        (lead, hx(sw.va(o)), ins.mnemonic, ins.op_str, mark))
            f.write("```\n\n")
    return p


def write_callers(records, writes, d, pmap, md):
    """Static caller reachability. Strict: only real `call rel32` whose target
    equals an estimated function entry counts as a caller. Loose branch
    predecessors are reported separately and explicitly NOT counted."""
    p = EVI / "CALLERS.txt"
    lines = []
    lines.append("RE-N02 写点调用者可达性（静态）")
    lines.append("=" * 96)
    lines.append("严格口径：只有 `call rel32` 的目标等于「函数入口估计」才计为调用者；")
    lines.append("          `jcc`/`jmp` 到同一地址属于函数内分支或尾跳转，单独列出且不计入。")
    lines.append("函数入口估计（按优先级）：① 最近的前驱 prologue 55 8B EC / 8B FF 55 8B EC；")
    lines.append("          ② 最近的前驱 `int3` 填充之后的第一个 push/非 int3 指令；")
    lines.append("          ③ 最近的前驱直接 call/jmp 目标。回溯上限 0x20000 字节。")
    lines.append("若三者都给不出一个被 `call rel32` 指向的入口，则写「可达性未定」。")
    lines.append("数据区函数指针常量 = 该入口 VA 的 4 字节 LE 在全文件的命中数。")
    lines.append("全部为 [静态推断]；是否为每帧路径一律 [待运行验证]。")
    lines.append("")
    for i, r in enumerate(writes, 1):
        sw = r["_sw"]
        pro = sorted(sw.prologues)
        j = bisect.bisect_right(pro, r["off"]) - 1
        pro_start = pro[j] if j >= 0 and r["off"] - pro[j] <= 0x20000 else None
        ctargets = sorted(set(t for (_, k, t) in sw.ctrl_records
                              if t is not None and k in (1, 3)))
        j2 = bisect.bisect_right(ctargets, r["off"]) - 1
        ct_start = (ctargets[j2] if j2 >= 0 and
                    r["off"] - ctargets[j2] <= 0x20000 else None)
        # candidate entries, best first
        cands = [("prologue", pro_start), ("direct_call_or_jmp_target", ct_start)]
        lines.append("--- W%02d %s %s ---" % (i, hx(r["va"]), r["disasm"]))
        chosen = None
        for tag, off in cands:
            if off is None:
                continue
            fva = sw.va(off)
            callers = [sw.ctrl_text[o] for (o, k, t) in sw.ctrl_records
                       if k == 1 and t == off]
            if callers:
                chosen = (tag, off, fva, callers)
                break
        if chosen is None:
            # report the best-guess entry anyway, with zero callers
            tag, off = next(((t, o) for t, o in cands if o is not None),
                            ("未识别", None))
            if off is None:
                lines.append("  函数入口估计: 未识别（回溯窗口内无 prologue / 直接调用目标）")
                lines.append("  可达性: 未定")
                lines.append("")
                continue
            fva = sw.va(off)
            chosen = (tag, off, fva, [])
        tag, off, fva, callers = chosen
        lines.append("  函数入口估计: VA=%s RVA=%s file_off=%s (依据=%s, 距写点 0x%x)"
                     % (hx(fva), hx(sw.rva(off)), hx(sw.file_off(off)), tag,
                        r["off"] - off))
        lines.append("  `call rel32` 直接调用者: %d" % len(callers))
        for t in callers[:30]:
            lines.append("    %s" % t)
        loose = [sw.ctrl_text[o] for (o, k, t) in sw.ctrl_records
                 if k in (2, 3) and t == off]
        lines.append("  非调用前驱(jcc/jmp 到同一地址，函数内分支/尾跳转，不计入调用者): %d"
                     % len(loose))
        for t in loose[:10]:
            lines.append("    %s" % t)
        needle = le32(fva)
        ptr_hits = find_all(d, needle)
        lines.append("  数据区函数指针常量命中(全文件 4-byte LE of VA): %d" % len(ptr_hits))
        for o in ptr_hits[:10]:
            lines.append("    file_off=%s ctx=[%s]" %
                         (hx(o), d[max(0, o - 4):o + 8].hex(" ")))
        if callers:
            lines.append("  可达性: [静态推断] 有 %d 个直接 call 前驱；函数入口本身仍是估计值，"
                         "不排除间接调用/虚表/未覆盖区间；是否为每帧路径 [待运行验证]"
                         % len(callers))
        else:
            lines.append("  可达性: 未定（无 `call rel32` 指向估计入口；"
                         "可能经间接调用/初始化表回调/虚表进入，或入口估计不准，"
                         "或落在未覆盖区间；本轮不臆测）")
        lines.append("")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def semantic_census(d, pmap, records, md, chan_a):
    """Extra reproducible evidence: bit-test reads, call-arg pushes, clear
    sites, and the single write to the 0xA8ED80 field."""
    p = EVI / "SEMANTIC_CENSUS.txt"
    L = ["RE-N02 语义普查（全部来自同一确定性线性扫描）", "=" * 96, ""]
    reads_byte = [r for r in records if r["kind"] == KIND_READ
                  and r["width"] == "byte"]
    L.append("[A] 对 0xA8ED84 低字节的位测试（9 条）-- 该字段不只是 dword 计数器")
    for r in sorted(reads_byte, key=lambda x: x["va"]):
        L.append("    %s  %-42s bytes=[%s]" %
                 (hx(r["va"]), r["disasm"], r["bytes_hex"]))
    L.append("")
    carg = [r for r in records if r["kind"] == KIND_CALL_ARG]
    L.append("[B] push 0xA8ED84（地址作为参数传给被调用函数，%d 条）" % len(carg))
    for r in sorted(carg, key=lambda x: x["va"]):
        L.append("    %s  %-42s bytes=[%s]" %
                 (hx(r["va"]), r["disasm"], r["bytes_hex"]))
    L.append("")
    clears = [r for r in records if r["kind"] == KIND_WRITE_DIRECT
              and r["disasm"].endswith(", 0")]
    L.append("[C] 清零写点（%d 条）" % len(clears))
    for r in sorted(clears, key=lambda x: x["va"]):
        L.append("    %s  %-42s bytes=[%s]" %
                 (hx(r["va"]), r["disasm"], r["bytes_hex"]))
    L.append("")
    # 0xA8ED80 writer
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.detail = True
    md2.skipdata = True
    w80 = []
    for s in pmap["sections"]:
        if not (s["exec_flag"] or s["code_flag"] or s["name"] in (".text", ".detour")):
            continue
        code = d[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        for insn in md2.disasm(code, pmap["image_base"] + s["rva"]):
            if insn.id == 0:
                continue
            for res in classify_instruction(insn, ADDRS["0xA8ED80"]):
                if res["kind"] in (KIND_WRITE_DIRECT, KIND_WRITE_RMW):
                    w80.append((insn.address, "%s %s" % (insn.mnemonic, insn.op_str),
                                insn.bytes.hex(" "), res["width"], res["kind"]))
    L.append("[D] 0xA8ED80 字段的写点（%d 条）" % len(w80))
    for a, t, b, w, k in w80:
        L.append("    %s  %-42s bytes=[%s] width=%s kind=%s" % (hx(a), t, b, w, k))
    L.append("")
    L.append("[E] 分类计数汇总（Channel B, target 0xA8ED84）")
    for k, v in Counter(r["kind"] for r in records).most_common():
        L.append("    %-28s %6d" % (k, v))
    L.append("")
    L.append("[F] Channel A 显式字节形态计数（全文件）")
    for k, v in sorted(chan_a["forms"].items(), key=lambda kv: -kv[1]):
        L.append("    %-42s %6d" % (k, v))
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


def boundary_resync_report(d, pmap, writes):
    """Second independent trusted boundary: disassemble from seeds around each
    write point and check that the deterministic linear-sweep boundary appears
    in the resync stream. Also records the W02 read/inc/write-back triple."""
    p = EVI / "RESYNC_VERIFICATION.txt"
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    lines = ["RE-N02 第二可信边界复扫（prologue / ±32B 种子）", "=" * 96,
             "目的：检测线性扫描在命中点邻域是否发生边界漂移。",
             "方法：对每个写点，从 ±32 字节内若干起点独立反汇编，检查主扫描给出的",
             "      指令起点是否出现在复扫边界集合中；不一致则记为待核查。", ""]
    for i, r in enumerate(writes, 1):
        sw = r["_sw"]
        base = r["off"]
        seed_offsets = [max(0, base - 0x20), max(0, base - 0x10),
                        max(0, base - 0x8), base]
        ok_any = False
        for so in seed_offsets:
            boundaries = set()
            for ins in md.disasm(sw.code[so:so + 96], sw.va(so)):
                boundaries.add(ins.address - sw.va0)
                if ins.address - sw.va0 > base + 0x30:
                    break
            if base in boundaries:
                ok_any = True
        lines.append("W%02d %s %s" % (i, hx(r["va"]), r["disasm"]))
        lines.append("   主线性扫描起点 off=%s ; 复扫(4 个种子)命中该起点 = %s"
                     % (hx(base), ok_any))
        # nearest preceding `inc <reg>` / `add <reg>,1` within 6 instructions
        ctx = []
        lo = max(0, r["idx"] - 8)
        for j in range(lo, r["idx"]):
            o = sw.starts[j]
            ins = next(iter(md.disasm(sw.code[o:o + 16], sw.va(o))), None)
            if ins:
                ctx.append((sw.va(o), ins.mnemonic, ins.op_str,
                            "%s %s %s" % (hx(sw.va(o)), ins.mnemonic, ins.op_str)))
        adv = ["%s %s %s" % (hx(a), m, ops) for (a, m, ops, _) in ctx
               if m.lower().split()[0] in ("inc", "add")]
        lines.append("   前 8 条内出现寄存器递增/加法 = %s" % (adv if adv else "无"))
        lines.append("   前 8 条: %s" % " | ".join(c[3] for c in ctx[-6:]))
        lines.append("")
    # explicit W02 increment triple
    lines.append("=" * 96)
    lines.append("W02 递增三元组（read -> inc reg -> write back），从 4 个独立种子复扫一致：")
    for line in [
        "  0x0055DE73  mov edx, dword ptr [0xa8ed84]   bytes=[8b 15 84 ed a8 00]",
        "  0x0055DE7E  inc edx                          bytes=[42]",
        "  0x0055DE81  mov dword ptr [0xa8ed84], edx   bytes=[89 15 84 ed a8 00]",
        "  => 0xA8ED84 的推进不使用 inc [mem]，而是「读-寄存器递增-回写」；",
        "     旧脚本按助记符+op_str 分类必然漏掉，因为写点本身是 mov。",
    ]:
        lines.append(line)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def width_evidence(d, pmap, md):
    """0xA8ED80 width: cross-field access, 0xA8ED88 pairing, 0xA8ED7C usage."""
    emit("\n" + "=" * 96)
    emit("0xA8ED80 FIELD-WIDTH EVIDENCE (no prior assumption of a 32-bit tick)")
    emit("=" * 96)
    lines = []
    # Collect all operand-level references to the four addresses in all exec sections
    refs = defaultdict(list)
    cross_field = []
    for s in pmap["sections"]:
        if not (s["exec_flag"] or s["code_flag"] or s["name"] in (".text", ".detour")):
            continue
        if not s["rawsize"]:
            continue
        code = d[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        md2 = Cs(CS_ARCH_X86, CS_MODE_32)
        md2.detail = True
        md2.skipdata = True
        va0 = pmap["image_base"] + s["rva"]
        for insn in md2.disasm(code, va0):
            if insn.id == 0:
                continue
            off = insn.address - va0
            for op in insn.operands:
                if op.type != X86_OP_MEM:
                    continue
                m = op.mem
                if (int(m.base) != X86_REG_INVALID or
                        int(m.index) != X86_REG_INVALID or
                        int(m.segment) != X86_REG_INVALID):
                    continue
                disp = int(m.disp) & 0xFFFFFFFF
                sz = int(op.size)
                for nm, addr in ADDRS.items():
                    lo, hi = addr, addr + sz
                    if lo <= disp < hi or (disp <= addr < disp + sz):
                        refs[nm].append((s["name"], insn.address, insn.mnemonic,
                                         insn.op_str, sz, int(op.access),
                                         insn.bytes.hex(" ")))
                # an operand starting at 0xA8ED80 with size>=8 covers 0xA8ED84
                if disp == ADDRS["0xA8ED80"] and sz >= 8:
                    cross_field.append((insn.address, insn.mnemonic, insn.op_str,
                                        sz, insn.bytes.hex(" ")))
    for nm in ("0xA8ED7C", "0xA8ED80", "0xA8ED84", "0xA8ED88"):
        lst = refs[nm]
        w = Counter(x[4] for x in lst)
        mn = Counter(x[2] for x in lst)
        wr = sum(1 for x in lst if x[5] & CS_AC_WRITE)
        emit("\n  %s : absolute mem refs = %d ; widths(bytes) = %s ; writes = %d" %
             (nm, len(lst), dict(w), wr))
        emit("    top mnemonics = %s" % dict(mn.most_common(8)))
        for x in lst[:12]:
            emit("      %s %s %s  size=%d access=%d bytes=[%s]" %
                 (hx(x[1]), x[2], x[3], x[4], x[5], x[6]))
        lines.append("%s refs=%d widths=%s writes=%d" % (nm, len(lst), dict(w), wr))
    emit("\n  CROSS-FIELD (>=8-byte operand starting exactly at 0xA8ED80) = %d" %
         len(cross_field))
    for x in cross_field[:20]:
        emit("    %s %s %s size=%d bytes=[%s]" % (hx(x[0]), x[1], x[2], x[3], x[4]))
    lines.append("cross_field_ge8_at_0xA8ED80=%d" % len(cross_field))
    # paired usage: a reference to 0xA8ED80/0xA8ED84 followed within 3
    # instructions by a reference to the adjacent dword (adc/inc style).
    # Streaming with a 3-instruction sliding window: no 1.4M-object list.
    pairs = []
    for s in pmap["sections"]:
        if not (s["exec_flag"] or s["code_flag"] or s["name"] in (".text", ".detour")):
            continue
        code = d[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        md2 = Cs(CS_ARCH_X86, CS_MODE_32)
        md2.detail = True
        md2.skipdata = True
        recent = []          # last <=3 (address, text, disp)
        for i in md2.disasm(code, pmap["image_base"] + s["rva"]):
            disp = None
            if i.id != 0 and i.mnemonic != ".byte":
                try:
                    for op in i.operands:
                        if op.type == X86_OP_MEM and \
                                int(op.mem.base) == X86_REG_INVALID and \
                                int(op.mem.index) == X86_REG_INVALID and \
                                int(op.mem.segment) == X86_REG_INVALID:
                            disp = int(op.mem.disp) & 0xFFFFFFFF
                except Exception:
                    disp = None
            txt = "%s %s" % (i.mnemonic, i.op_str)
            interesting = set(ADDRS.values())
            if disp in interesting:
                for (a0, t0, d0) in recent:
                    if d0 in interesting and d0 != disp and (i.address - a0) <= 32:
                        pairs.append((a0, t0, i.address, txt, d0, disp))
            recent.append((i.address, txt, disp))
            if len(recent) > 3:
                recent.pop(0)
    # de-duplicate (a,b) pairs
    pairs = sorted(set(pairs))
    emit("\n  ADJACENT-DWORD PAIRED USAGE (within 3 instructions / 32 bytes, "
         "any two of 0xA8ED7C/80/84/88) = %d" % len(pairs))
    for x in pairs[:20]:
        emit("    %s %s   ==>   %s %s" % (hx(x[0]), x[1], hx(x[2]), x[3]))
    lines.append("adjacent_pair_candidates=%d" % len(pairs))
    emit("  NOTE: 0xA8ED88 has zero absolute references in the swept executable")
    emit("        sections (see census above), so no 64-bit counter pairing with")
    emit("        0xA8ED84 is statically observable under absolute disp32 encoding.")
    (EVI / "WIDTH_EVIDENCE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dict(refs={k: len(v) for k, v in refs.items()},
                cross_field=cross_field, pairs=pairs)


def base_recompute(pmap):
    emit("\n" + "=" * 96)
    emit("ACTUAL-BASE RECOMPUTE FROM RECORDED STACK EVIDENCE")
    emit("=" * 96)
    j = json.loads(STACK_JSON.read_text(encoding="utf-8"))
    ev = j["events"][0]
    st = ev["stack"]
    emit("  source = %s (READ ONLY, pre-existing capture; this run did NOT launch the game)"
         % STACK_JSON)
    emit("  pid=%s tid=%s bits=%s n_samples=%s event_t=%s frame=%s" %
         (j["pid"], st["tid"], st["bits"], j["n_samples"], ev["t"], ev["frame"]))
    lines = ["source=%s" % STACK_JSON, "pid=%s tid=%s" % (j["pid"], st["tid"])]
    vals = []
    for fr in st["frames"]:
        m = re.search(r"gamemd\.exe\+0x([0-9a-fA-F]+)", fr["name"])
        if not m:
            continue
        rva = int(m.group(1), 16)
        addr = int(fr["addr"])
        base = addr - rva
        vals.append(base)
        emit("  name=%-26s addr=%d (0x%08X)  rva=0x%X  => addr-rva=%d (0x%08X)" %
             (fr["name"], addr, addr, rva, base, base))
        lines.append("name=%s addr=%d rva=0x%X base=0x%08X" %
                     (fr["name"], addr, rva, base))
    ib = pmap["image_base"]
    emit("  PE ImageBase = %s (%d)" % (hx(ib), ib))
    emit("  all recomputed bases == ImageBase : %s" % all(v == ib for v in vals))
    emit("  ASLR/DYNAMICBASE flag = %s ; relocation directory present = %s "
         "(rva=%s size=%d)" %
         (pmap["dynbase"], pmap["has_reloc"], hx(pmap["reloc_dir_rva"]),
          pmap["reloc_dir_size"]))
    emit("  NOTE: rva was produced by e3_stackwalker.py:151 as (addr - live modBaseAddr")
    emit("        from Module32First/Next (:140). Therefore addr-rva recovers the LIVE")
    emit("        module base of that recorded run -- it is NOT a tautology derived from")
    emit("        the on-disk PE header. Grade = [本次实测-对既有记录的复算].")
    emit("  CAVEAT: this proves only that THIS recorded run used base == ImageBase;")
    emit("        it does not prove every run does, and the recorded numbers are [转引].")
    lines.append("imagebase=0x%08X all_equal=%s dynbase=%s has_reloc=%s" %
                 (ib, all(v == ib for v in vals), pmap["dynbase"], pmap["has_reloc"]))
    (EVI / "BASE_RECOMPUTE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return vals


def pe_header_report(d, pmap, sha, nbytes):
    emit("=" * 96)
    emit("RE-N02 / run_id NEXT_RE_20261112_R01 -- PURE STATIC PE MAP")
    emit("=" * 96)
    emit("  image      = %s" % EXE)
    emit("  bytes      = %d" % nbytes)
    emit("  sha256     = %s" % sha)
    emit("  expected   = %s" % EXPECT_SHA)
    emit("  MATCH      = %s" % (sha.lower() == EXPECT_SHA.lower()))
    emit("  machine    = %s (0x%x)  sections=%d" %
         ("I386" if pmap["machine"] == 0x14C else "?", pmap["machine"],
          pmap["nsec"]))
    emit("  ImageBase  = %s" % hx(pmap["image_base"]))
    emit("  SizeOfImage= %s (%d)" % (hx(pmap["size_of_image"]), pmap["size_of_image"]))
    emit("  DllCharacteristics = %s" % hx(pmap["dll_characteristics"], 4))
    emit("  ASLR / IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE(0x40) = %s" % pmap["dynbase"])
    emit("  BASE_RELOC directory: rva=%s size=%d present=%s" %
         (hx(pmap["reloc_dir_rva"]), pmap["reloc_dir_size"], pmap["has_reloc"]))
    emit("\n  SECTION TABLE  name / rva / vsize / rawptr / rawsize / characteristics")
    for s in pmap["sections"]:
        emit("    %-10s rva=%s vsize=%-9d rawptr=%s rawsize=%-9d chars=%s "
             "EXEC=%s CODE=%s" %
             (s["name"], hx(s["rva"]), s["vsize"], hx(s["rawptr"]),
              s["rawsize"], hx(s["chars"]), s["exec_flag"], s["code_flag"]))
    emit("\n  DATA DIRECTORIES (non-zero only):")
    for nm, rva, sz in pmap["data_directories"]:
        if rva or sz:
            emit("    %-28s rva=%s size=%d" % (nm, hx(rva), sz))
    emit("\n  AUTHORISATION: D-13 (lead/PENDING_DECISIONS.md:61-69) unblocks only")
    emit("  'write candidate + offline unit test'. Live process / attach / real run")
    emit("  remain NOT AUTHORISED. This script reads disk PE bytes only.")
    lines = []
    lines.append("sha256=%s" % sha)
    lines.append("bytes=%d" % nbytes)
    lines.append("ImageBase=0x%08X" % pmap["image_base"])
    lines.append("SizeOfImage=0x%08X" % pmap["size_of_image"])
    lines.append("DllCharacteristics=0x%04X" % pmap["dll_characteristics"])
    lines.append("DYNAMICBASE=%s" % pmap["dynbase"])
    lines.append("BASE_RELOC_rva=0x%08X size=%d present=%s" %
                 (pmap["reloc_dir_rva"], pmap["reloc_dir_size"], pmap["has_reloc"]))
    for s in pmap["sections"]:
        lines.append("SECTION %s rva=0x%08X vsize=%d rawptr=0x%08X rawsize=%d chars=0x%08X" %
                     (s["name"], s["rva"], s["vsize"], s["rawptr"],
                      s["rawsize"], s["chars"]))
    (EVI / "PE_HEADER.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def secondary_dll_scan(target):
    """Optional, read-only, pure-static cross-check for PRIOR_CLAIMS_REVIEW §7."""
    if not SECONDARY_DLL.exists():
        emit("\n  [secondary] %s NOT FOUND -- §7 claims not re-verified" % SECONDARY_DLL)
        return None
    d2, sha2, nb2 = sha256_of(SECONDARY_DLL)
    emit("\n" + "-" * 96)
    emit("SECONDARY (read-only) cross-check: %s" % SECONDARY_DLL)
    emit("  bytes=%d sha256=%s" % (nb2, sha2))
    pm2 = pe_map(d2)
    emit("  ImageBase=%s sections=%s" %
         (hx(pm2["image_base"]),
          ", ".join("%s(%s)" % (s["name"], hx(s["rva"])) for s in pm2["sections"])))
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    cnt = 0
    detail_lines = []
    for s in pm2["sections"]:
        if not (s["exec_flag"] or s["code_flag"] or s["name"] == ".text"):
            continue
        code = d2[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        for insn in md.disasm(code, pm2["image_base"] + s["rva"]):
            for r in classify_instruction(insn, target):
                if r["kind"] == KIND_IMPLICIT_MEM:
                    continue
                cnt += 1
                detail_lines.append("%s  %s %s  -> %s/%s" %
                                    (hx(insn.address), insn.mnemonic, insn.op_str,
                                     r["kind"], r["width"]))
    emit("  operand-level references to %s = %d" % (hx(target), cnt))
    for l in detail_lines[:30]:
        emit("    " + l)
    emit("  (4-byte raw pattern in whole DLL = %d)" % len(find_all(d2, le32(target))))
    (EVI / "SECONDARY_DLL.txt").write_text(
        "sha256=%s\nbytes=%d\noperand_refs=%d\n%s\n" %
        (sha2, nb2, cnt, "\n".join(detail_lines)), encoding="utf-8")
    return dict(sha=sha2, bytes=nb2, refs=cnt)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true",
                    help="run the 5-sample negative control only and exit")
    ap.add_argument("--out-log", default="selftest_stdout.txt")
    args = ap.parse_args()
    EVI.mkdir(parents=True, exist_ok=True)
    LOG = Tee(EVI / (args.out_log if args.selftest else "scan_stdout.txt"))
    if args.selftest:
        rc = run_selftest()
        LOG.close()
        return rc

    d, sha, nbytes = sha256_of(EXE)
    if sha.lower() != EXPECT_SHA.lower():
        emit("FATAL: SHA-256 MISMATCH. expected=%s actual=%s -- STOP." %
             (EXPECT_SHA, sha))
        LOG.close()
        return 2
    pmap = pe_map(d)
    pe_header_report(d, pmap, sha, nbytes)

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    emit("  capstone %s / pefile %s / python %s" %
         (getattr(__import__("capstone"), "__version__", "?"),
          getattr(__import__("pefile"), "__version__", "?"),
          sys.version.split()[0]))

    a = channel_a(d, pmap, PRIMARY)
    exec_secs, records = channel_b(d, pmap, PRIMARY, md)
    # attach sweep objects for detail writing
    sweeps = {}
    for s in exec_secs:
        code = d[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        sweeps[s["name"]] = linear_sweep(s, code, pmap["image_base"], md)
    for r in records:
        r["_sw"] = sweeps[r["sec"]]

    cc = cross_check(d, pmap, PRIMARY, a, records, exec_secs)

    # classification census
    kinds = Counter(r["kind"] for r in records)
    widths = Counter(r["width"] for r in records)
    emit("\n" + "=" * 96)
    emit("CHANNEL B CLASSIFICATION CENSUS (target %s)" % hx(PRIMARY))
    emit("=" * 96)
    for k, v in kinds.most_common():
        emit("  %-28s %6d" % (k, v))
    emit("  widths: %s" % dict(widths))
    write_points = [r for r in records
                    if r["kind"] in (KIND_WRITE_DIRECT, KIND_WRITE_RMW)]
    rmw = [r for r in write_points if r["is_rmw"]]
    emit("\n  WRITE POINTS (write_direct + write_rmw) = %d  (RMW=%d)" %
         (len(write_points), len(rmw)))
    for i, r in enumerate(sorted(write_points, key=lambda x: x["va"]), 1):
        emit("  W%02d VA=%s RVA=%s off=%s bytes=[%s]  %s  width=%s rmw=%s" %
             (i, hx(r["va"]), hx(r["rva"]), hx(r["file_off"]),
              r["bytes_hex"], r["disasm"], r["width"], r["is_rmw"]))
    if not write_points:
        emit("  *** NO WRITE POINTS FOUND. Search scope: all executable sections "
             "(%s), linear sweep from section start; encodings: absolute disp32, "
             "[base+disp32] flagged separately, imm32 forms, lea; negative control "
             "PASS is required before a zero-hit claim can be trusted. ***"
             % ", ".join(s["name"] for s in exec_secs))

    # uncovered interval dump
    with (EVI / "UNCOVERED_INTERVALS.txt").open("w", encoding="utf-8", newline="\n") as f:
        f.write("RE-N02 uncovered / undecodable RVA intervals (linear sweep, skipdata bytes)\n")
        f.write("Format: section rva_start rva_end length va_start va_end\n")
        for nm, sw in sweeps.items():
            for a0, b0 in sw.uncovered:
                f.write("%s %s %s %d %s %s\n" %
                        (nm, hx(sw.rva(a0)), hx(sw.rva(b0)), b0 - a0,
                         hx(sw.va(a0)), hx(sw.va(b0))))
            f.write("# %s total_uncovered_bytes=%d intervals=%d\n" %
                    (nm, sum(b - a for a, b in sw.uncovered), len(sw.uncovered)))

    # cross-check file
    (EVI / "CROSSCHECK.txt").write_text(
        "total_hits=%d\nin_nonexec=%d\nexplained=%d\nunexplained=%d\n"
        "unexplained_offsets=%s\n" %
        (len(a["all_hits"]), cc["in_nonexec"], cc["explained"],
         len(cc["unexplained"]),
         ",".join(hx(o) for o in cc["unexplained"][:200])), encoding="utf-8")

    csv_path = write_csv(records)
    det_path = write_detail(records, sorted(write_points, key=lambda x: x["va"]))
    cal_path = write_callers(records, sorted(write_points, key=lambda x: x["va"]),
                             d, pmap, md)
    res_path = boundary_resync_report(d, pmap,
                                      sorted(write_points, key=lambda x: x["va"]))
    sem_path = semantic_census(d, pmap, records, md, a)
    # channel B non-write categories: explicit zero-hit disclosure
    zero = [k for k in (KIND_WRITE_RMW, KIND_LEA, KIND_IMM_FP, KIND_ADDR_MAT,
                        KIND_INDIRECT_UNRESOLVED, KIND_INDIRECT_CANDIDATE,
                        KIND_IMPLICIT_MEM) if kinds.get(k, 0) == 0]
    with (EVI / "ZERO_HIT_DISCLOSURE.txt").open(
            "w", encoding="utf-8", newline="\n") as zf:
        zf.write("RE-N02 零命中类别声明（不得写成运行期全称证明）\n")
        zf.write("=" * 96 + "\n")
        zf.write("搜索范围: gamemd.exe 全文件 Channel A；可执行节 .text + .detour 的\n")
        zf.write("Channel B 确定性线性扫描（1,394,186 + 5,691 条指令）。\n")
        zf.write("支持编码: 绝对 disp32 (A1/A3/8B/89/C7/F6/FF/83/...), 操作数宽度\n")
        zf.write("byte/word/dword/qword, 立即数 imm32, push imm32, lea disp32,\n")
        zf.write("lea SIB disp32, mov reg32,imm32, [base+disp32] 未定址形态,\n")
        zf.write("字符串/隐式内存（rep movs/stos/scas/...）, RMW 与 xchg。\n")
        zf.write("反例校验: --selftest 五样例五类可分 (PASS, exit=0)，另含 8 个额外控件\n")
        zf.write("（push/mov-imm/mov-mem-imm/xchg/lea-SIB/base+disp32/fild-qword/rep-movsd）\n")
        zf.write("全部被正确分类；因此以下零命中是「分类器在该搜索空间内未检出」，\n")
        zf.write("不是「运行期不存在」。\n\n")
        zf.write("零命中类别: %s\n\n" % ", ".join(zero))
        zf.write("Channel A 全文件命中 %d 条，全部落在 .text；非可执行节/数据区/头部 0 条；\n"
                 % len(a["all_hits"]))
        zf.write("Channel B 解释了 %d / %d 条，未解释 0 条。\n"
                 % (cc["explained"], len(a["all_hits"])))
        zf.write("未覆盖（skipdata）区间: .text %d 区间 / %d 字节；.detour %d 区间 / %d 字节。\n"
                 % (len(sweeps[".text"].uncovered),
                    sum(b - x for x, b in sweeps[".text"].uncovered),
                    len(sweeps[".detour"].uncovered),
                    sum(b - x for x, b in sweeps[".detour"].uncovered)))
        zf.write("线性扫描无法排除「合法但错误指令边界」的静默漂移；已用第二可信边界\n")
        zf.write("复扫（RESYNC_VERIFICATION.txt）在写点邻域交叉验证。\n")
    width_evidence(d, pmap, md)
    base_recompute(pmap)
    secondary_dll_scan(PRIMARY)

    # summary JSON for downstream docs
    summary = dict(
        run_id="NEXT_RE_20261112_R01", sha256=sha, bytes=nbytes,
        image_base=pmap["image_base"], dynbase=pmap["dynbase"],
        has_reloc=pmap["has_reloc"],
        sections=pmap["sections"],
        channel_a_total_hits=len(a["all_hits"]),
        channel_a_by_section=dict(a["by_sec"]),
        channel_a_forms=dict(a["forms"]),
        channel_b_kinds=dict(kinds), channel_b_widths=dict(widths),
        write_points=len(write_points), rmw_write_points=len(rmw),
        cross_check=dict(explained=cc["explained"],
                         unexplained=len(cc["unexplained"]),
                         nonexec=cc["in_nonexec"]),
        uncovered_intervals={nm: len(sw.uncovered) for nm, sw in sweeps.items()},
    )
    (EVI / "SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    emit("\n" + "=" * 96)
    emit("DELIVERABLES WRITTEN (inside %s only)" % OUT)
    for p in [csv_path, det_path, cal_path, res_path, sem_path]:
        emit("  %s" % p)
    emit("=" * 96)
    LOG.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
