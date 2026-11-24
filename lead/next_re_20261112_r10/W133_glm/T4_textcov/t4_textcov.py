#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T4_textcov.py -- quantify how much of gamemd.exe .text is NOT covered by the W130
function_atlas, and decide per uncovered byte-range: missed real function entry
point vs CC/90 padding vs jump table / inline pointer data vs still unexplained.

Strictly offline. Never launches the binary. Writes ONLY inside OUTDIR.

Inputs (read-only):
  ra2youli\\gamemd.exe                                   (PE32, ImageBase 0x400000)
  W130_atlas\\function_atlas.tsv                          (entry,size[, ...] hex)
  W130_atlas\\vtables_canonical.json                      ({"vtables":[{vt,col,...}]})

Outputs:
  uncovered_runs.tsv   start,end,size
  candidates.tsv       addr,source_of_evidence,verdict,reason,decoded_len,ends_with
  new_functions.tsv    entry,size,evidence,first_bytes       (strong accepts only)
  unexplained_runs.tsv start,end,size,prev_cov_end,next_cov_start,first_bytes
  report.md            numbers, method, limits

Determinism: no timestamps, no randomness; all iterations sorted; identical reruns
produce byte-identical files.
"""
import os
import re
import sys
import json
import array
import hashlib
from bisect import bisect_right, bisect_left, insort

import pefile
import capstone as cs
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

# ---------------------------------------------------------------- constants
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
VTABLES = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W133_glm\T4_textcov"

EXPECT_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
TEXT_START = 0x401000
TEXT_END = 0x7E038D          # exclusive, per task

MAX_FUNC_LEN = 0x8000        # candidate validation decode cap (32 KiB)
MAX_INSTRS = 120000
WAVES = 3                    # wave 0 = atlas funcs, waves 1..2 = refs from accepted funcs
JT_REF_MIN = 3               # min entries for a table referenced by jmp/call [reg*4+base]
JT_MONO_MIN = 5              # min entries for unreferenced monotonic pointer run
JT_DENSE_MIN = 8             # min entries for unreferenced dense pointer run
WEAK_MIN_LEN = 16            # min decoded length for prologue-only ACCEPT_WEAK

X86 = cs.x86
STRONG_KINDS = ("call", "jmp", "jt", "vt", "ptr_rdata", "ptr_data")
XREF_KINDS = ("call", "jmp", "jcc")

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


class DecodeError(Exception):
    pass


# ---------------------------------------------------------------- globals
TEXT = b""
IMAGE_BASE = 0x400000
COV_S = []                   # sorted covered interval starts
COV_E = []                   # matching ends
UNC_S = []
UNC_E = []
ACC = {}                     # addr -> {"size","weak","ends","wave","ev"}
ACC_S = []                   # sorted accepted starts
ACC_E = []
TAB = []                     # [(start, end, kind, n)] merged, sorted
REFS = {}                    # addr -> set of evidence strings
CANDS = {}                   # addr -> {"ev","verdict","reason","len","ends","wave","evlen"}
STATS = {}


# ---------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def merge_intervals(pairs):
    iv = sorted((a, b) for a, b in pairs if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            if b > out[-1][1]:
                out[-1][1] = b
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def dword(a):
    o = a - TEXT_START
    return int.from_bytes(TEXT[o:o + 4], "little")


def refresh_cov(covered_iv):
    global COV_S, COV_E
    COV_S = [a for a, b in covered_iv]
    COV_E = [b for a, b in covered_iv]


def refresh_unc(uncovered_iv):
    global UNC_S, UNC_E
    UNC_S = [a for a, b in uncovered_iv]
    UNC_E = [b for a, b in uncovered_iv]


def is_covered(a):
    i = bisect_right(COV_S, a) - 1
    return i >= 0 and a < COV_E[i]


def run_of(a):
    """uncovered run (rs, re) containing a, or None"""
    i = bisect_right(UNC_S, a) - 1
    if i >= 0 and a < UNC_E[i]:
        return (UNC_S[i], UNC_E[i])
    return None


def refresh_acc():
    global ACC_S, ACC_E
    ACC_S = sorted(ACC)
    ACC_E = [a + ACC[a]["size"] for a in ACC_S]


def in_accepted(a):
    i = bisect_right(ACC_S, a) - 1
    return i >= 0 and a < ACC_E[i]


def in_table(a):
    for s, e, kind, n in TAB:
        if s <= a < e:
            return kind
    return None


# ---------------------------------------------------------------- decoding
def iter_insns(addr, limit):
    off = addr - TEXT_START
    end_off = min(limit, TEXT_END) - TEXT_START
    code = TEXT[off:end_off]
    if not code:
        return
    try:
        for insn in MD.disasm(code, addr):
            yield insn
    except cs.CsError:
        raise DecodeError("invalid")


def branch_kind(insn):
    g = insn.groups
    if cs.CS_GRP_CALL in g:
        return "call"
    if cs.CS_GRP_JUMP in g:
        return "jmp" if insn.id == X86.X86_INS_JMP else "jcc"
    return None


def term_kind(insn):
    if insn.id == X86.X86_INS_RET:
        return "ret"
    if insn.id == X86.X86_INS_INT3:
        return "int3"
    if insn.id == X86.X86_INS_JMP:
        t = insn.operands[0].type
        if t == X86.X86_OP_IMM:
            return "jmp"
        if t == X86.X86_OP_MEM:
            return "jmp[mem]"
        return "jmp[reg]"
    return None


def first_barrier(addr):
    best, bk = TEXT_END, "text_end"
    i = bisect_right(COV_S, addr)
    if i < len(COV_S) and COV_S[i] < best:
        best, bk = COV_S[i], "covered_function"
    j = bisect_right(ACC_S, addr)
    if j < len(ACC_S) and ACC_S[j] < best:
        best, bk = ACC_S[j], "accepted_function"
    for s, e, kind, n in TAB:
        if s > addr and s < best:
            best, bk = s, "pointer_table"
    return best, bk


def try_decode(addr):
    """Linear decode from addr until first terminator.
    Returns (ok, reason, decoded_len, ends_with)."""
    b, bk = first_barrier(addr)
    limit = min(b, addr + MAX_FUNC_LEN, TEXT_END)
    if limit <= addr:
        return (False, "at_text_end", 0, "-")
    n = 0
    term = None
    term_end = 0
    term_txt = "-"
    last_end = addr
    try:
        for insn in iter_insns(addr, limit):
            n += 1
            if n > MAX_INSTRS:
                return (False, "too_long", 0, "-")
            last_end = insn.address + insn.size
            t = term_kind(insn)
            if t == "int3":
                return (False, "int3_before_end", 0, "-")
            if t:
                term = t
                term_end = last_end
                term_txt = insn.mnemonic + (" " + insn.op_str if insn.op_str else "")
                break
    except DecodeError:
        return (False, "invalid_decode", 0, "-")
    if term is None:
        if last_end < limit:
            return (False, "invalid_decode", 0, "-")
        return (False, "no_terminator", 0, "-")
    if term_end > b:
        return (False, "overlaps_" + bk, 0, "-")
    return (True, "clean_decode_to_" + term, term_end - addr, term_txt)


def collect_refs(addr, length):
    """Decode [addr, addr+length) and record xref / pointer / table-base evidence."""
    end = min(addr + length, TEXT_END)
    n = 0
    try:
        for insn in iter_insns(addr, end):
            n += 1
            if n > MAX_INSTRS:
                break
            if insn.id == 0:
                continue
            bk = branch_kind(insn)
            ops = insn.operands
            if bk:
                if ops and ops[0].type == X86.X86_OP_IMM:
                    tgt = (insn.address + insn.size + ops[0].imm) & 0xFFFFFFFF
                    if TEXT_START <= tgt < TEXT_END and not is_covered(tgt):
                        add_cand(tgt, "%s@%X" % (bk, insn.address))
                if ops and ops[0].type == X86.X86_OP_MEM:
                    m = ops[0].mem
                    if m.index and m.scale == 4:
                        base = m.disp & 0xFFFFFFFF
                        if TEXT_START <= base < TEXT_END:
                            globals().setdefault("_TBL", set()).add(base)
                continue
            for op in ops:
                if op.type == X86.X86_OP_IMM:
                    v = op.imm & 0xFFFFFFFF
                    if TEXT_START <= v < TEXT_END and not is_covered(v):
                        add_cand(v, "imm@%X" % insn.address)
                elif op.type == X86.X86_OP_MEM:
                    m = op.mem
                    if m.index and m.scale == 4:
                        base = m.disp & 0xFFFFFFFF
                        if TEXT_START <= base < TEXT_END:
                            globals().setdefault("_TBL", set()).add(base)
                    elif m.base == 0 and m.index == 0:
                        v = m.disp & 0xFFFFFFFF
                        if TEXT_START <= v < TEXT_END and not is_covered(v):
                            add_cand(v, "abs@%X" % insn.address)
    except DecodeError:
        pass


# ---------------------------------------------------------------- candidates
def add_cand(addr, ev):
    if addr < TEXT_START or addr >= TEXT_END:
        return
    if is_covered(addr):
        return
    if in_accepted(addr):
        return
    c = CANDS.get(addr)
    if c is None:
        CANDS[addr] = {"ev": {ev}, "verdict": None, "reason": "", "len": 0,
                       "ends": "-", "wave": -1, "evlen": -1}
    else:
        c["ev"].add(ev)


def scan_prologues():
    n = 0
    for rs, re_ in zip(UNC_S, UNC_E):
        for a in range(rs, re_ - 2):
            if a & 3:
                continue
            o = a - TEXT_START
            if a != rs and TEXT[o - 1] != 0xCC:
                continue
            b2 = TEXT[o:o + 2]
            b3 = TEXT[o:o + 3]
            if (b3 == b"\x55\x8b\xec" or b3 == b"\x53\x56\x57"
                    or b2 == b"\x83\xec" or b2 == b"\x81\xec"):
                add_cand(a, "prologue")
                n += 1
    STATS["prologue_candidates"] = n


def scan_data_ptrs(pe):
    for sec in pe.sections:
        name = sec.Name.rstrip(b"\x00").decode("latin1")
        if name not in (".rdata", ".data"):
            continue
        data = sec.get_data()
        va = IMAGE_BASE + sec.VirtualAddress
        cnt = len(data) // 4
        arr = array.array("I")
        arr.frombytes(data[:cnt * 4])
        if sys.byteorder == "big":
            arr.byteswap()
        tag = "ptr_" + name.lstrip(".")
        hits = 0
        for i in range(cnt):
            v = arr[i]
            if TEXT_START <= v < TEXT_END and not is_covered(v):
                add_cand(v, "%s@%X" % (tag, va + 4 * i))
                hits += 1
        STATS["ptr_hits_" + name] = hits


def load_vtable_refs():
    try:
        with open(VTABLES, encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        STATS["vtable_load_error"] = repr(e)
        return 0
    hits = [0]

    def walk(o):
        if isinstance(o, bool) or o is None:
            return
        if isinstance(o, int):
            if TEXT_START <= o < TEXT_END and not is_covered(o):
                add_cand(o, "vt")
                hits[0] += 1
            return
        if isinstance(o, float):
            return
        if isinstance(o, str):
            for m in re.findall(r"0x[0-9A-Fa-f]{6,8}|\b[0-9A-Fa-f]{6,8}\b", o):
                if "0x" in m.lower():
                    v = int(m, 16)
                else:
                    if not re.search(r"[A-Fa-f]", m):
                        continue
                    v = int(m, 16)
                if TEXT_START <= v < TEXT_END and not is_covered(v):
                    add_cand(v, "vt")
                    hits[0] += 1
            return
        if isinstance(o, list):
            for x in o:
                walk(x)
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(k)
                walk(v)
    walk(obj)
    STATS["vtable_hits"] = hits[0]
    return hits[0]


# ---------------------------------------------------------------- tables
def accepted_ivs():
    return [(a, a + ACC[a]["size"]) for a in ACC]


def clipped_segments(rs, re_):
    segs = [(rs, re_)]
    for s, e in sorted(accepted_ivs()):
        if e <= rs or s >= re_:
            continue
        new = []
        for a, b in segs:
            if e <= a or s >= b:
                new.append((a, b))
                continue
            if a < s:
                new.append((a, s))
            if e < b:
                new.append((e, b))
        segs = new
    return segs


def scan_pointer_runs(a, b, out):
    i = a
    while i + 4 <= b:
        v = dword(i)
        if TEXT_START <= v < TEXT_END:
            j = i + 4
            while j + 4 <= b and TEXT_START <= dword(j) < TEXT_END:
                j += 4
            n = (j - i) // 4
            vals = [dword(i + 4 * k) for k in range(n)]
            mono = all(vals[k] <= vals[k + 1] for k in range(n - 1))
            tbl = getattr(sys.modules[__name__], "_TBL", set())
            refd = i in tbl
            if refd and n >= JT_REF_MIN:
                out.append((i, j, "jumptable_ref", n))
            elif n >= JT_MONO_MIN and mono:
                out.append((i, j, "ptr_table_mono", n))
            elif n >= JT_DENSE_MIN:
                out.append((i, j, "ptr_table_dense", n))
            i = j
        else:
            i += 4


def recompute_tables():
    global TAB
    raw = []
    for rs, re_ in zip(UNC_S, UNC_E):
        for a, b in clipped_segments(rs, re_):
            scan_pointer_runs(a, b, raw)
    raw.sort()
    merged = []
    for s, e, kind, n in raw:
        if merged and s < merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1][1] = e
                merged[-1][2] = kind
                merged[-1][3] = max(merged[-1][3], n)
            continue
        merged.append([s, e, kind, n])
    TAB = [(s, e, k, n) for s, e, k, n in merged]
    STATS["tables_final"] = len(TAB)
    STATS["table_bytes_final"] = sum(e - s for s, e, k, n in TAB)


def add_jt_refs():
    for s, e, kind, n in TAB:
        for a in range(s, e, 4):
            v = dword(a)
            if TEXT_START <= v < TEXT_END and not is_covered(v):
                add_cand(v, "jt@%X" % a)


# ---------------------------------------------------------------- validation
def tail_suspect(addr, ev, kinds):
    if kinds - set(XREF_KINDS):
        return False
    srcs = set()
    for e in ev:
        k, _, s = e.partition("@")
        if k in XREF_KINDS:
            try:
                srcs.add(int(s, 16))
            except ValueError:
                pass
    if len(srcs) != 1:
        return False
    s = next(iter(srcs))
    if not is_covered(s):
        return False
    i = bisect_right(COV_S, s) - 1
    if i < 0:
        return False
    fend = COV_E[i]
    r = run_of(addr)
    return r is not None and r[0] == addr and fend == r[0]


def validate(addr):
    if is_covered(addr):
        return ("REJECT", "inside_covered_function", 0, "-")
    tk = in_table(addr)
    if tk:
        return ("REJECT", "inside_" + tk, 0, "-")
    if in_accepted(addr):
        return ("REJECT", "inside_accepted_function", 0, "-")
    ok, reason, ln, ends = try_decode(addr)
    if not ok:
        return ("REJECT", reason, 0, "-")
    ev = CANDS[addr]["ev"]
    kinds = set(e.split("@", 1)[0] for e in ev)
    if tail_suspect(addr, ev, kinds):
        return ("REJECT", "likely_tail_of_prev_function", ln, ends)
    if kinds & set(STRONG_KINDS):
        return ("ACCEPT", reason, ln, ends)
    if "prologue" in kinds and ln >= WEAK_MIN_LEN:
        return ("ACCEPT_WEAK", "prologue_only_clean_decode", ln, ends)
    return ("REJECT", "no_strong_reference", ln, ends)


def accept(addr, size, weak, ends, wave, ev):
    ACC[addr] = {"size": size, "weak": weak, "ends": ends, "wave": wave,
                 "ev": sorted(ev)}
    if addr in ACC_S:
        i = ACC_S.index(addr)
        ACC_E[i] = addr + size
    else:
        insort(ACC_S, addr)
        j = bisect_right(ACC_S, addr)
        ACC_E.insert(j, addr + size)


def validate_pass(wave):
    n_strong = n_weak = 0
    for a in sorted(CANDS.keys()):
        c = CANDS[a]
        if c["verdict"] == "ACCEPT":
            continue
        if c["verdict"] == "ACCEPT_WEAK" and len(c["ev"]) == c["evlen"]:
            continue
        v, r, ln, ends = validate(a)
        c["verdict"], c["reason"], c["len"], c["ends"] = v, r, ln, ends
        c["wave"] = wave
        c["evlen"] = len(c["ev"])
        if v == "ACCEPT":
            accept(a, ln, False, ends, wave, c["ev"])
            n_strong += 1
        elif v == "ACCEPT_WEAK":
            accept(a, ln, True, ends, wave, c["ev"])
            n_weak += 1
    STATS.setdefault("accept_strong_per_wave", []).append(n_strong)
    STATS.setdefault("accept_weak_per_wave", []).append(n_weak)


def reconcile():
    """Final overlap resolution; tables win only when referenced."""
    dropped = 0
    for a in sorted(ACC.keys()):
        e = ACC[a]
        if e["weak"]:
            continue
        for s, en, kind, n in TAB:
            if kind == "jumptable_ref" and a < en and s < a + e["size"]:
                del ACC[a]
                CANDS[a].update(verdict="REJECT", reason="overlaps_final_jumptable@%X" % s,
                                len=0, ends="-")
                dropped += 1
                break
    strong = sorted((a, a + ACC[a]["size"]) for a in ACC if not ACC[a]["weak"])
    for a in sorted([a for a in ACC if ACC[a]["weak"]]):
        iv = (a, a + ACC[a]["size"])
        clash = False
        for s, e in strong:
            if iv[0] < e and s < iv[1]:
                clash = True
                break
        if not clash:
            for s, en, kind, n in TAB:
                if iv[0] < en and s < iv[1]:
                    clash = True
                    break
        if clash:
            del ACC[a]
            CANDS[a].update(verdict="REJECT", reason="dropped_final_overlap",
                            len=0, ends="-")
            dropped += 1
    STATS["reconcile_dropped"] = dropped
    refresh_acc()


# ---------------------------------------------------------------- byte classes
def classify_bytes():
    strong = sorted((a, a + ACC[a]["size"]) for a in ACC if not ACC[a]["weak"])
    weak = sorted((a, a + ACC[a]["size"]) for a in ACC if ACC[a]["weak"])
    taken = merge_intervals(strong + weak)
    taken_s = [a for a, b in taken]
    taken_e = [b for a, b in taken]

    def seg_minus_taken(a, b):
        segs = [(a, b)]
        for s, e in taken:
            if e <= a or s >= b:
                continue
            new = []
            for x, y in segs:
                if e <= x or s >= y:
                    new.append((x, y))
                    continue
                if x < s:
                    new.append((x, s))
                if e < y:
                    new.append((e, y))
            segs = new
        return segs

    tab_bytes = 0
    tab_ivs = []
    for s, e, kind, n in TAB:
        for x, y in seg_minus_taken(s, e):
            tab_ivs.append((x, y))
            tab_bytes += y - x

    pad_cc = pad00 = unexp = 0
    unexp_runs = []
    for rs, re_ in zip(UNC_S, UNC_E):
        for a, b in seg_minus_taken(rs, re_):
            cur = a
            while cur < b:
                # skip table spans
                tnext = None
                for x, y in tab_ivs:
                    if y <= cur:
                        continue
                    if x < b and y > cur:
                        tnext = (max(x, cur), min(y, b))
                    break
                if tnext:
                    cur = tnext[1]
                    continue
                o = cur - TEXT_START
                w = TEXT[o:o + 1]
                if w == b"\xcc" or w == b"\x90":
                    run_s = cur
                    while cur < b and TEXT[cur - TEXT_START] in (0xCC, 0x90):
                        cur += 1
                    pad_cc += cur - run_s
                    continue
                if w == b"\x00":
                    run_s = cur
                    while cur < b and TEXT[cur - TEXT_START] == 0x00:
                        cur += 1
                    pad00 += cur - run_s
                    continue
                run_s = cur
                while cur < b:
                    ch = TEXT[cur - TEXT_START]
                    if ch in (0xCC, 0x90, 0x00):
                        break
                    tn = None
                    for x, y in tab_ivs:
                        if y <= cur:
                            continue
                        if x < b and y > cur:
                            tn = max(x, cur)
                        break
                    if tn is not None:
                        break
                    cur += 1
                unexp += cur - run_s
                unexp_runs.append((run_s, cur))
    STATS["strong_fn_bytes"] = sum(e - s for s, e in strong)
    STATS["weak_fn_bytes"] = sum(e - s for s, e in weak)
    STATS["pad_cc90_bytes"] = pad_cc
    STATS["pad00_bytes"] = pad00
    STATS["table_bytes"] = tab_bytes
    STATS["unexplained_bytes"] = unexp
    return unexp_runs


# ---------------------------------------------------------------- io
def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(str(x) for x in row) + "\n")


def first_bytes(addr, n=16):
    o = addr - TEXT_START
    return TEXT[o:o + n].hex()


def main():
    STATS["exe_sha256"] = sha256_file(EXE)
    STATS["sha_matches"] = STATS["exe_sha256"] == EXPECT_SHA256

    pe = pefile.PE(EXE, fast_load=True)
    global IMAGE_BASE, TEXT
    IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
    tsec = None
    for s in pe.sections:
        if s.Name.rstrip(b"\x00").decode("latin1") == ".text":
            tsec = s
    assert tsec is not None
    tva = IMAGE_BASE + tsec.VirtualAddress
    tdata = tsec.get_data()
    assert tva <= TEXT_START
    TEXT = tdata[TEXT_START - tva:TEXT_END - tva]
    STATS["text_bytes_available"] = len(TEXT)

    # ---- atlas
    rows = []
    with open(ATLAS, encoding="utf-8", newline="") as f:
        f.readline()  # header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if not parts or not parts[0].strip():
                continue
            try:
                ent = int(parts[0], 16)
            except ValueError:
                continue
            try:
                size = int(parts[1], 16)
            except ValueError:
                try:
                    size = int(parts[1])
                except ValueError:
                    continue
            rows.append((ent, size))
    total = TEXT_END - TEXT_START
    cov_size = sum(min(b, TEXT_END) - a
                   for a, b in merge_intervals([(e, e + s) for e, s in rows]))
    mode = "size"
    if not (0.3 <= cov_size / total <= 1.0):
        rows2 = [(e, s - e) for e, s in rows]
        cov2 = sum(min(b, TEXT_END) - a
                   for a, b in merge_intervals([(e, e + s) for e, s in rows2]))
        if 0.3 <= cov2 / total <= 1.0:
            rows, cov_size, mode = rows2, cov2, "end"
    STATS["atlas_rows"] = len(rows)
    STATS["atlas_size_interpretation"] = mode

    in_text = [(e, s) for e, s in rows if TEXT_START <= e < TEXT_END]
    covered = merge_intervals([(e, min(e + s, TEXT_END)) for e, s in in_text])
    uncovered = []
    cur = TEXT_START
    for a, b in covered:
        if a > cur:
            uncovered.append((cur, a))
        cur = max(cur, b)
    if cur < TEXT_END:
        uncovered.append((cur, TEXT_END))
    refresh_cov(covered)
    refresh_unc(uncovered)

    covered_bytes = sum(b - a for a, b in covered)
    uncovered_bytes = total - covered_bytes
    STATS["total_text_bytes"] = total
    STATS["covered_bytes"] = covered_bytes
    STATS["uncovered_bytes"] = uncovered_bytes
    STATS["covered_pct"] = 100.0 * covered_bytes / total
    STATS["uncovered_runs"] = len(uncovered)

    # ---- wave 0 evidence
    for ent, size in in_text:
        collect_refs(ent, size)
    recompute_tables()
    add_jt_refs()
    scan_prologues()
    scan_data_ptrs(pe)
    load_vtable_refs()
    refresh_acc()
    validate_pass(0)

    # ---- waves 1..N-1 from accepted functions
    for wave in range(1, WAVES):
        prev = [a for a, e in ACC.items() if e["wave"] == wave - 1]
        for a in prev:
            collect_refs(a, ACC[a]["size"])
        recompute_tables()
        add_jt_refs()
        validate_pass(wave)

    reconcile()
    recompute_tables()          # final table set for byte accounting
    unexp_runs = classify_bytes()

    # ---- outputs
    os.makedirs(OUTDIR, exist_ok=True)
    write_tsv(os.path.join(OUTDIR, "uncovered_runs.tsv"),
              ["start", "end", "size"],
              [( "%X" % a, "%X" % b, b - a) for a, b in uncovered])

    cand_rows = []
    rej_hist = {}
    acc_ev_hist = {}
    for a in sorted(CANDS.keys()):
        c = CANDS[a]
        ev = ";".join(sorted(c["ev"])[:6])
        cand_rows.append(("%X" % a, ev, c["verdict"], c["reason"],
                          c["len"] if c["verdict"].startswith("ACCEPT") else 0,
                          c["ends"]))
        if c["verdict"] == "REJECT":
            rej_hist[c["reason"]] = rej_hist.get(c["reason"], 0) + 1
        elif c["verdict"].startswith("ACCEPT"):
            for k in set(e.split("@", 1)[0] for e in c["ev"]):
                acc_ev_hist[k] = acc_ev_hist.get(k, 0) + 1
    write_tsv(os.path.join(OUTDIR, "candidates.tsv"),
              ["addr", "source_of_evidence", "verdict", "reason", "decoded_len", "ends_with"],
              cand_rows)

    strong = sorted([a for a in ACC if not ACC[a]["weak"]])
    weak = sorted([a for a in ACC if ACC[a]["weak"]])
    nf_rows = []
    for a in strong:
        e = ACC[a]
        prio = ["call", "jmp", "jt", "vt", "ptr_rdata", "ptr_data", "imm", "abs", "jcc"]
        evs = sorted(e["ev"])
        evs.sort(key=lambda x: prio.index(x.split("@", 1)[0])
                 if x.split("@", 1)[0] in prio else 99)
        nf_rows.append(("%X" % a, e["size"], ";".join(evs[:3]), first_bytes(a)))
    write_tsv(os.path.join(OUTDIR, "new_functions.tsv"),
              ["entry", "size", "evidence", "first_bytes"], nf_rows)

    # unexplained runs with context
    unexp_runs.sort()
    merged_unexp = merge_intervals(unexp_runs)
    u_rows = []
    for a, b in merged_unexp:
        i = bisect_right(COV_S, a) - 1
        prev_end = COV_E[i] if i >= 0 else 0
        j = bisect_right(COV_S, b)
        next_start = COV_S[j] if j < len(COV_S) else 0
        u_rows.append(("%X" % a, "%X" % b, b - a, "%X" % prev_end,
                       "%X" % next_start, first_bytes(a)))
    write_tsv(os.path.join(OUTDIR, "unexplained_runs.tsv"),
              ["start", "end", "size", "prev_cov_end", "next_cov_start", "first_bytes"],
              u_rows)

    # ---- report
    hist_buckets = [(1, 15), (16, 63), (64, 255), (256, 1023), (1024, 4095),
                    (4096, 65535), (65536, 1 << 62)]
    run_hist = {k: 0 for k in [( "1-15") + "", "16-63", "64-255", "256-1K", "1K-4K", "4K-64K", ">64K"]}
    keys = ["1-15", "16-63", "64-255", "256-1K", "1K-4K", "4K-64K", ">64K"]
    run_hist = dict.fromkeys(keys, 0)
    for a, b in uncovered:
        sz = b - a
        for k, (lo, hi) in zip(keys, hist_buckets):
            if lo <= sz <= hi:
                run_hist[k] += 1
                break

    top_unexp = sorted(merged_unexp, key=lambda r: r[1] - r[0], reverse=True)[:20]

    def pct(x, d=total):
        return 100.0 * x / d

    strong_bytes = STATS["strong_fn_bytes"]
    weak_bytes = STATS["weak_fn_bytes"]
    new_cov = covered_bytes + strong_bytes
    new_cov_w = covered_bytes + strong_bytes + weak_bytes
    accounted = (strong_bytes + weak_bytes + STATS["pad_cc90_bytes"]
                 + STATS["pad00_bytes"] + STATS["table_bytes"] + STATS["unexplained_bytes"])

    L = []
    L.append("# T4 textcov -- gamemd.exe uncovered .text analysis\n")
    L.append("Binary SHA-256: `%s` (expected `%s`, match: %s) [已证]\n"
             % (STATS["exe_sha256"], EXPECT_SHA256, STATS["sha_matches"]))
    L.append("Atlas: `function_atlas.tsv`, %d rows, size column read as %s. "
             "vtables_canonical.json loaded.\n" % (STATS["atlas_rows"],
                                                   STATS["atlas_size_interpretation"]))
    L.append("## 1. Coverage recomputation\n")
    L.append("| metric | value |")
    L.append("|---|---|")
    L.append("| .text span | 0x401000..0x%X (%d bytes) |" % (TEXT_END, total))
    L.append("| atlas-covered bytes | %d (%.2f%%) |" % (covered_bytes, pct(covered_bytes)))
    L.append("| uncovered bytes | %d (%.2f%%) |" % (uncovered_bytes, pct(uncovered_bytes)))
    L.append("| claim 79.5%% covered | %s |"
             % ("RIGHT (recomputed %.2f%%)" % pct(covered_bytes)
                if abs(pct(covered_bytes) - 79.5) < 0.5 else
                "WRONG (recomputed %.2f%%)" % pct(covered_bytes)))
    L.append("")
    L.append("[已证] covered/uncovered computed from merged atlas intervals over "
             "0x401000..0x7E038D (see uncovered_runs.tsv).\n")
    L.append("## 2. Uncovered run distribution\n")
    L.append("runs: %d\n" % len(uncovered))
    L.append("| size bucket | runs |")
    L.append("|---|---|")
    for k in keys:
        L.append("| %s | %d |" % (k, run_hist[k]))
    L.append("")
    L.append("## 3. Candidate recovery (waves=%d, independent evidence then strict validation)\n" % WAVES)
    L.append("Evidence sources: direct call/jmp/jcc rel32 xrefs from atlas-decoded code; "
             "immediate & absolute-disp pointers in .text; pointer scan of .rdata/.data; "
             "vtable entries; jump-table entries; prologue-after-CC (weak only).\n")
    L.append("Strong evidence = {call, jmp, jt, vt, ptr_rdata, ptr_data}. A candidate is "
             "ACCEPTed only with strong evidence AND a clean linear decode from its entry "
             "to a ret/jmp terminator with no invalid byte, no int3, no overlap with "
             "covered/accepted/table ranges. Prologue-only candidates that decode cleanly "
             "and are >=16 bytes get ACCEPT_WEAK (reported separately).\n")
    L.append("| verdict | count |")
    L.append("|---|---|")
    vs = {}
    for c in CANDS.values():
        vs[c["verdict"]] = vs.get(c["verdict"], 0) + 1
    for k in sorted(vs):
        L.append("| %s | %d |" % (k, vs[k]))
    L.append("")
    L.append("Accept evidence kinds (a function may match several):\n")
    for k in sorted(acc_ev_hist):
        L.append("- %s: %d" % (k, acc_ev_hist[k]))
    L.append("")
    L.append("## 4. Reject reason histogram\n")
    L.append("| reason | count |")
    L.append("|---|---|")
    for k in sorted(rej_hist):
        L.append("| %s | %d |" % (k, rej_hist[k]))
    L.append("")
    L.append("## 5. Byte accounting of the uncovered %d bytes\n" % uncovered_bytes)
    L.append("| bucket | bytes | % of uncovered |")
    L.append("|---|---|---|")
    for name, val in (("accepted strong functions", strong_bytes),
                      ("accepted weak (prologue-only) functions", weak_bytes),
                      ("CC/90 padding", STATS["pad_cc90_bytes"]),
                      ("00 padding", STATS["pad00_bytes"]),
                      ("jump tables / pointer data", STATS["table_bytes"]),
                      ("still unexplained", STATS["unexplained_bytes"])):
        L.append("| %s | %d | %.2f%% |" % (name, val, 100.0 * val / uncovered_bytes))
    L.append("| **sum** | **%d** | (should equal uncovered) |" % accounted)
    L.append("")
    L.append("## 6. New coverage\n")
    L.append("- strong accepts: %d functions, %d bytes -> coverage %.2f%% -> %.2f%%\n"
             % (len(strong), strong_bytes, pct(covered_bytes), pct(new_cov)))
    L.append("- weak accepts: %d functions, %d bytes -> coverage with weak %.2f%%\n"
             % (len(weak), weak_bytes, pct(new_cov_w)))
    L.append("[已证] accepts decoded cleanly from an independently referenced entry; "
             "sizes = offset of terminating ret/jmp. [未证] that every accept is the "
             "compiler's true function boundary (linear decode cannot see fall-through "
             "into following code or data embedded after the last ret).\n")
    L.append("## 7. Largest still-unexplained runs (top 20)\n")
    L.append("| start | end | size | prev covered end | next covered start | first bytes |")
    L.append("|---|---|---|---|---|---|")
    for r in u_rows[:20]:
        L.append("| 0x%s | 0x%s | %s | 0x%s | 0x%s | %s |" % r)
    L.append("")
    L.append("Full list: unexplained_runs.tsv.\n")
    L.append("## 8. Method and limits (honest)\n")
    L.append("- Method: covered bitmap from atlas -> uncovered runs -> candidate entries "
             "from 4 independent evidence classes -> strict single-pass decode validation "
             "-> 2 more waves harvesting refs from accepted functions -> final overlap "
             "reconciliation (referenced jump tables veto accepts; speculative pattern "
             "tables yield to accepts).\n")
    L.append("- [未证] functions whose ONLY reference is an immediate (callback passed in "
             "a register chain) or a jcc are conservatively rejected (%d candidates).\n"
             % rej_hist.get("no_strong_reference", 0))
    L.append("- [未证] xrefs derive from linear decodes of atlas functions; atlas size "
             "errors can plant bogus refs. Validation mitigates but cannot eliminate this.\n")
    L.append("- [未证] tail extensions: runs beginning immediately after a covered "
             "function's claimed end whose only xrefs come from that same function are "
             "rejected as 'likely_tail_of_prev_function' (%d).\n"
             % rej_hist.get("likely_tail_of_prev_function", 0))
    L.append("- [未证] unaligned pointer arrays in .text and pointer arrays in other "
             "sections are not scanned.\n")
    L.append("- [未证] 'CC/90 padding' and '00 padding' buckets are byte-pattern guesses "
             "on non-function bytes; CC/90 inside real (unaccepted) code inflates padding.\n")
    L.append("- [未证] decoded length is the first terminator; trailing int3 alignment and "
             "post-ret data belong to padding/unexplained buckets.\n")
    L.append("- Validation decode cap is %d bytes; a >32 KiB truly-terminating function "
             "would be missed.\n" % MAX_FUNC_LEN)
    L.append("- The 79.5%% claim: see section 1.\n")
    L.append("## 9. Determinism\n")
    L.append("Script reruns must be byte-identical. Data-file SHA-256 (this run):\n")
    for fn in ("uncovered_runs.tsv", "candidates.tsv", "new_functions.tsv",
               "unexplained_runs.tsv"):
        p = os.path.join(OUTDIR, fn)
        L.append("- %s: `%s`\n" % (fn, sha256_file(p)))
    with open(os.path.join(OUTDIR, "report.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("\n".join(L) + "\n")

    # ---- stdout summary
    print("sha_ok=%s atlas_rows=%d" % (STATS["sha_matches"], STATS["atlas_rows"]))
    print("text=%d covered=%d (%.2f%%) uncovered=%d (%.2f%%) runs=%d"
          % (total, covered_bytes, pct(covered_bytes), uncovered_bytes,
             pct(uncovered_bytes), len(uncovered)))
    print("candidates=%d strong_accepts=%d(%dB) weak=%d(%dB)"
          % (len(CANDS), len(strong), strong_bytes, len(weak), weak_bytes))
    print("new_coverage=%.2f%% with_weak=%.2f%%" % (pct(new_cov), pct(new_cov_w)))
    print("pad_cc90=%d pad00=%d tables=%d(%dB) unexplained=%d sum=%d"
          % (STATS["pad_cc90_bytes"], STATS["pad00_bytes"], STATS["tables_final"],
             STATS["table_bytes"], STATS["unexplained_bytes"], accounted))
    print("rejects=%s" % json.dumps(rej_hist, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
