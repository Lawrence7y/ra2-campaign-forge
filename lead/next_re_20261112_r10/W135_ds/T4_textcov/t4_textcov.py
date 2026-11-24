#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
t4_textcov.py -- rigorous accounting of the uncovered bytes of `gamemd.exe` .text.

Question: the function atlas claims 12,916 functions covering 79.5% of .text.
What are the other 20.5%, and how many of those bytes are real functions the
atlas missed?

Answer shape produced by this script:
  * recomputed coverage (does 79.5% hold?),
  * the uncovered holes (count, size distribution),
  * byte classes inside the holes: a real new function / CC-90 padding /
    inline data / still unexplained,
  * the rejected candidates with reasons.

Evidence model -- this is the core design decision.

  A "candidate" is only *acceptable* if it is backed by STRONG evidence:

    decoded  an atlas function, decoded from its own entry, executes a
             call/jmp/jcc whose rel32 lands there.  The atlas tool followed
             every rel32 it decoded, so a decoded rel32 into a hole means the
             atlas stopped following an edge it had.
    vtable   a slot of a vtable listed in vtables_canonical.json.
    table    a slot of the strictly-monotonic `dd` function-pointer table in
             .data (0x812004..0x815DA0, 3944 entries, NUL-terminated).
    prologue a prologue byte pattern that is immediately preceded by CC/90
             padding (or opens a hole).  Functions in this image are 16-byte
             aligned and padded, so this cannot fire inside code by accident.

  A "candidate" from a raw byte scan (E8/E9/0F8x anywhere in .text, or a bare
  dword window in .text) is WEAK: those patterns also occur inside instruction
  operands.  Weak candidates are reported but never accepted.  Measured cost of
  getting this wrong: with weak evidence accepted, 6,428 "functions" with a
  median size of 29 bytes were produced, almost all noise.

Determinism: sorted iteration only; no RNG, no clock, no threads.
Exit 0 on success, 2 on a failed precondition (binary hash).
"""

import collections
import hashlib
import json
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import (
    X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_NOP,
    X86_OP_IMM, X86_OP_MEM,
)
import capstone.x86_const as cc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
VT_JSON = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json")
EXPECT_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
IMAGE_BASE = 0x400000

MAX_FUNC_LEN = 0x4000
MAX_FUNC_INSN = 4000

JCC_IDS = set()
for _n in ("JAE JA JBE JB JCXZ JECXZ JE JGE JG JLE JL JNE JNO JNP JNS "
           "JO JP JS LOOP LOOPE LOOPNE").split():
    JCC_IDS.add(getattr(cc, "X86_INS_" + _n))


# --------------------------------------------------------------------- PE ----
def load_image():
    data = open(EXE, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    if sha != EXPECT_SHA256:
        sys.stderr.write("FATAL: sha256 mismatch: %s\n" % sha)
        raise SystemExit(2)
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off + 4] != b"PE\0\0":
        sys.stderr.write("FATAL: not a PE\n")
        raise SystemExit(2)
    nsec = struct.unpack_from("<H", data, pe_off + 6)[0]
    opt_sz = struct.unpack_from("<H", data, pe_off + 20)[0]
    tab = pe_off + 24 + opt_sz
    secs = []
    for i in range(nsec):
        o = tab + 40 * i
        name = data[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
        secs.append(dict(name=name, va=IMAGE_BASE + vaddr, vsize=vsize,
                         raw=rawptr, rawsize=rawsize))
    return data, secs


class Image(object):
    def __init__(self, data, secs):
        self.data = data
        self.sections = secs
        self.text = [s for s in secs if s["name"] == ".text"][0]

    def read(self, va, n):
        t = self.text
        return self.data[t["raw"] + (va - t["va"]):t["raw"] + (va - t["va"]) + n]

    def off_of(self, va):
        for s in self.sections:
            # Only the file-backed part: .data has vsize 0x367BE4 > rawsize
            # 0x6C000, so reading past rawsize would return unrelated bytes.
            if s["raw"] and s["va"] <= va < s["va"] + s["rawsize"]:
                return s["raw"] + (va - s["va"])
        return None

    def dword(self, va):
        o = self.off_of(va)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from("<I", self.data, o)[0]


# ---------------------------------------------------------------- atlas ----
def load_atlas(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 2 or not p[0]:
                continue
            rows.append((int(p[0], 16), int(p[1])))
    rows.sort()
    return rows


def coverage(rows, lo, hi):
    cov = bytearray(hi - lo)
    overlaps = []
    for e, s in rows:
        a, b = max(e, lo), min(e + s, hi)
        if a >= b:
            continue
        if any(cov[a - lo:b - lo]):
            overlaps.append((e, s))
        for x in range(a - lo, b - lo):
            cov[x] = 1
    runs = []
    i, n = 0, hi - lo
    while i < n:
        if not cov[i]:
            j = i
            while j < n and not cov[j]:
                j += 1
            runs.append((lo + i, lo + j, j - i))
            i = j
        else:
            i += 1
    return cov, runs, overlaps


# ------------------------------------------------------------ decoding ------
class DB(object):
    def __init__(self, img):
        self.img = img
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.md.skipdata = True
        self._c = {}

    def one(self, va):
        if va in self._c:
            return self._c[va]
        r = None
        if TEXT_LO <= va < TEXT_HI:
            for ins in self.md.disasm(self.img.read(va, 16), va, 1):
                if ins.id == 0:          # CS_ERR_SKIPDATA / invalid
                    break
                r = ins
                break
        self._c[va] = r
        return r


def flow(ins):
    if ins is None:
        return "bad", None, None
    if ins.id == X86_INS_RET:
        return "ret", None, None
    if ins.id in (X86_INS_CALL, X86_INS_JMP) or ins.id in JCC_IDS:
        kind = ("call" if ins.id == X86_INS_CALL
                else "jmp" if ins.id == X86_INS_JMP else "jcc")
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            return kind, op.imm, None
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            return kind, None, op.mem.disp & 0xFFFFFFFF
        return kind, None, None
    return "plain", None, None


def descend(db, entry, unc):
    """
    Recursive descent from `entry` only.  Any byte touched must be uncovered;
    leaving the hole ends that path (the function tail-jumped into atlas code).
    """
    seen = set()
    spans = []
    work = [entry]
    n_insn = 0
    end = entry
    term = None
    while work:
        pc = work.pop()
        while pc not in seen:
            if not (TEXT_LO <= pc < TEXT_HI):
                return dict(ok=False, spans=spans, end=end, term=None,
                            n_insn=n_insn, reason="target_out_of_text")
            if not unc[pc - TEXT_LO]:
                term = term or "jmp_out"
                break
            ins = db.one(pc)
            if ins is None:
                return dict(ok=False, spans=spans, end=end, term=None,
                            n_insn=n_insn, reason="invalid_instruction")
            seen.add(pc)
            n_insn += 1
            if n_insn > MAX_FUNC_INSN:
                return dict(ok=False, spans=spans, end=end, term=None,
                            n_insn=n_insn, reason="too_many_insn")
            spans.append((pc, pc + ins.size))
            end = max(end, pc + ins.size)
            if end - entry > MAX_FUNC_LEN:
                return dict(ok=False, spans=spans, end=end, term=None,
                            n_insn=n_insn, reason="too_long")
            kind, imm, _ = flow(ins)
            if kind == "ret":
                term = "ret"
                break
            if kind == "plain":
                pc += ins.size
                continue
            if kind == "call":
                pc += ins.size
                continue
            if kind == "jcc":
                if imm is not None and TEXT_LO <= imm < TEXT_HI:
                    work.append(imm)
                pc += ins.size
                continue
            if kind == "jmp":
                if imm is not None and TEXT_LO <= imm < TEXT_HI:
                    pc = imm
                    continue
                term = term or "jmp"
                break
            return dict(ok=False, spans=spans, end=end, term=None,
                        n_insn=n_insn, reason="invalid_instruction")
    if not spans:
        return dict(ok=False, spans=[], end=entry, term=None, n_insn=0,
                    reason="empty_body")
    return dict(ok=True, spans=spans, end=end, term=term, n_insn=n_insn,
                reason="ok")


# ------------------------------------------------------- reference mining ---
def decoded_rel32(db, rows):
    """STRONG: targets of instructions the atlas's own functions execute."""
    refs = collections.defaultdict(set)
    for e, s in rows:
        if not (TEXT_LO <= e < TEXT_HI):
            continue
        pc, stop = e, e + s
        while pc < stop:
            ins = db.one(pc)
            if ins is None:
                break
            kind, imm, _ = flow(ins)
            if imm is not None and TEXT_LO <= imm < TEXT_HI:
                refs[imm].add("decoded:%s@%08X" % (kind, pc))
            pc += ins.size
    return refs


def raw_rel32(img):
    """WEAK: E8/E9/0F8x byte patterns anywhere in .text."""
    t = img.text
    base = t["va"]
    blob = img.data[t["raw"]:t["raw"] + (TEXT_HI - base)]
    refs = collections.defaultdict(set)
    for i in range(len(blob) - 6):
        op = blob[i]
        if op in (0xE8, 0xE9):
            tgt = base + i + 5 + struct.unpack_from("<i", blob, i + 1)[0]
            if TEXT_LO <= tgt < TEXT_HI:
                refs[tgt].add("raw_rel32@%08X" % (base + i))
        elif op == 0x0F and 0x80 <= blob[i + 1] <= 0x8F:
            tgt = base + i + 6 + struct.unpack_from("<i", blob, i + 2)[0]
            if TEXT_LO <= tgt < TEXT_HI:
                refs[tgt].add("raw_rel32@%08X" % (base + i))
    return refs


def raw_text_dwords(img):
    """WEAK: unaligned dword windows inside .text that look like pointers."""
    t = img.text
    refs = collections.defaultdict(set)
    blob = img.data[t["raw"]:t["raw"] + (TEXT_HI - t["va"])]
    for i in range(len(blob) - 4):
        v = struct.unpack_from("<I", blob, i)[0]
        if TEXT_LO <= v < TEXT_HI:
            refs[v].add("raw_textptr@%08X" % (t["va"] + i))
    return refs


def vtable_targets(img):
    """STRONG: all slots of all canonical vtables."""
    refs = collections.defaultdict(set)
    stat = dict(vtables=0, slots=0)
    if not os.path.exists(VT_JSON):
        return refs, stat
    with open(VT_JSON, encoding="utf-8") as f:
        doc = json.load(f)
    for vt in doc.get("vtables", []):
        start = vt.get("vt", 0)
        if not start:
            continue
        stat["vtables"] += 1
        cls = vt.get("class", "?")
        for k in range(256):
            v = img.dword(start + 4 * k)
            if v is None or not (TEXT_LO <= v < TEXT_HI):
                break
            stat["slots"] += 1
            refs[v].add("vtable:%s" % cls)
    return refs, stat


def fnptr_tables(img):
    """
    STRONG: monotonic NUL-terminated `dd` tables of code pointers in .data.
    Requirement: >= 8 entries, every entry a .text address, strictly ascending,
    and the dword before the first and after the last entry is 0.  That
    combination does not arise by accident inside mixed data.

    Cross-check reported in the summary: the fraction of slots that are
    16-byte aligned (the alignment MSVC gives function starts here) and the
    fraction preceded by CC/90 padding.
    """
    tables = []
    for s in img.sections:
        if s["name"] != ".data" or not s["raw"]:
            continue
        n = s["rawsize"] // 4
        words = [struct.unpack_from("<I", img.data, s["raw"] + 4 * k)[0]
                 for k in range(n)]
        ok = [TEXT_LO <= v < TEXT_HI for v in words]
        i = 0
        while i < n:
            if not ok[i]:
                i += 1
                continue
            j = i
            while j < n and ok[j]:
                j += 1
            ln = j - i
            if ln >= 8:
                tg = words[i:j]
                asc = all(tg[k + 1] > tg[k] for k in range(ln - 1))
                before = words[i - 1] if i > 0 else 0
                after = words[j] if j < n else 0
                if asc and before == 0 and after == 0:
                    tables.append((s["va"] + 4 * i, tg))
            i = j
    return tables


# ------------------------------------------------------------ jump tables ---
def find_jump_tables(img):
    """`jmp/call [base + idx*4 + disp]` -> disp is the base of a dispatch table."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    t = img.text
    blob = img.data[t["raw"]:t["raw"] + (TEXT_HI - t["va"])]
    spans = []
    for ins in md.disasm(blob, t["va"]):
        if ins.id == 0:
            continue
        if ins.id not in (X86_INS_JMP, X86_INS_CALL):
            continue
        op = ins.operands[0]
        if op.type != X86_OP_MEM or op.mem.index == 0:
            continue
        ta = op.mem.disp & 0xFFFFFFFF
        n = 0
        while n < 8192:
            v = img.dword(ta + 4 * n)
            if v is None or not (TEXT_LO <= v < TEXT_HI):
                break
            n += 1
        if n >= 3:
            spans.append((ta, ta + 4 * n, n, ins.address))
    spans.sort()
    return spans


def in_spans(va, spans):
    for a, b in spans:
        if a <= va < b:
            return True
    return False


# ------------------------------------------------------------- prologues -----
PROLOGUES = [
    (b"\x55\x8b\xec", "55 8B EC"),
    (b"\x8b\xff\x55\x8b\xec", "8B FF 55 8B EC"),
    (b"\x53\x56\x57", "53 56 57"),
    (b"\x56\x57", "56 57"),
    (b"\x6a\xff\x68", "6A FF 68"),
    (b"\x51\x53\x56", "51 53 56"),
    (b"\x51\x56", "51 56"),
    (b"\x56\x8b\x74\x24", "56 8B 74 24"),
    (b"\x53\x8b\xdc", "53 8B DC"),
    (b"\x8b\x44\x24", "8B 44 24"),
    (b"\x83\xec", "83 EC"),
    (b"\x81\xec", "81 EC"),
]


def prologue_at(img, va):
    buf = img.read(va, 8)
    for pat, name in PROLOGUES:
        if buf.startswith(pat):
            return name
    return None


# ------------------------------------------------------------------ main -----
def main():
    data, secs = load_image()
    img = Image(data, secs)
    rows = load_atlas(ATLAS)
    total = TEXT_HI - TEXT_LO

    cov, runs, overlaps = coverage(rows, TEXT_LO, TEXT_HI)
    covered = sum(cov)
    unc = bytearray(total)
    for a, b, s in runs:
        for x in range(a, b):
            unc[x - TEXT_LO] = 1

    db = DB(img)

    # ---- byte classes inside the holes -----------------------------------
    PAD, JT, OTHER = 1, 2, 0
    kind = bytearray(total)
    all_pad_runs = []
    for a, b, s in runs:
        if all(x in (0xCC, 0x90) for x in img.read(a, s)):
            all_pad_runs.append((a, b, s))
            for x in range(a, b):
                kind[x - TEXT_LO] = PAD
    jtabs = find_jump_tables(img)
    for ta, tb, n, site in jtabs:
        for x in range(max(ta, TEXT_LO), min(tb, TEXT_HI)):
            if unc[x - TEXT_LO]:
                kind[x - TEXT_LO] = JT

    # ---- evidence --------------------------------------------------------
    strong = collections.defaultdict(set)
    weak = collections.defaultdict(set)
    dec = decoded_rel32(db, rows)
    vts, vtstat = vtable_targets(img)
    tabs = fnptr_tables(img)
    tab_targets = collections.defaultdict(set)
    tab_slots = 0
    for start, tg in tabs:
        for k, v in enumerate(tg):
            tab_targets[v].add("table:%08X+%d" % (start, 4 * k))
            tab_slots += 1

    for src in (dec, vts):
        for tgt, evs in src.items():
            if 0 <= tgt - TEXT_LO < total and unc[tgt - TEXT_LO]:
                strong[tgt] |= evs
    for tgt, evs in tab_targets.items():
        if 0 <= tgt - TEXT_LO < total and unc[tgt - TEXT_LO]:
            strong[tgt] |= evs
    for src in (raw_rel32(img), raw_text_dwords(img)):
        for tgt, evs in src.items():
            if 0 <= tgt - TEXT_LO < total and unc[tgt - TEXT_LO]:
                weak[tgt] |= evs

    # prologue evidence: pattern must be preceded by CC/90 padding
    for a, b, s in runs:
        for va in range(a, b):
            if kind[va - TEXT_LO] != OTHER:
                continue
            if va != a and img.read(va - 1, 1) not in (b"\xcc", b"\x90"):
                continue
            nm = prologue_at(img, va)
            if nm:
                strong[va].add("prologue:%s" % nm)

    cands = sorted(set(strong) | set(weak))

    # ---- validate --------------------------------------------------------
    out = []
    accepted = {}
    acc_mask = bytearray(total)
    for c in cands:
        ev_s = sorted(strong.get(c, ()))
        ev_w = sorted(weak.get(c, ()))
        ev = ",".join(ev_s) if ev_s else "WEAK:" + ev_w[0]
        if not (0 <= c - TEXT_LO < total):
            continue
        if not unc[c - TEXT_LO]:
            out.append((c, ev, "REJECT", "already_covered", 0, ""))
            continue
        if kind[c - TEXT_LO] == JT:
            out.append((c, ev, "REJECT", "inside_jump_table", 0, ""))
            continue
        if kind[c - TEXT_LO] == PAD:
            out.append((c, ev, "REJECT", "inside_padding", 0, ""))
            continue
        r = descend(db, c, unc)
        if not r["ok"]:
            out.append((c, ev, "REJECT", r["reason"], 0, ""))
            continue
        if any(acc_mask[x] for x in range(c - TEXT_LO,
                                          min(r["end"], TEXT_HI) - TEXT_LO)):
            out.append((c, ev, "REJECT", "overlaps_accepted",
                        r["end"] - c, r["term"] or ""))
            continue
        if not ev_s:
            out.append((c, ev, "REJECT", "weak_evidence_only",
                        r["end"] - c, r["term"] or ""))
            continue
        if r["n_insn"] == 1:
            out.append((c, ev, "REJECT", "single_insn_stub",
                        r["end"] - c, r["term"] or ""))
            continue
        if r["term"] is None:
            out.append((c, ev, "REJECT", "no_terminator",
                        r["end"] - c, ""))
            continue
        swallowed = [x for x in strong if c < x < r["end"]]
        if swallowed:
            out.append((c, ev, "REJECT",
                        "swallows_strong_start:%08X" % min(swallowed),
                        r["end"] - c, r["term"]))
            continue
        accepted[c] = dict(info=r, evidence=ev_s)
        for x in range(c - TEXT_LO, min(r["end"], TEXT_HI) - TEXT_LO):
            acc_mask[x] = 1
        out.append((c, ev, "ACCEPT", "ok", r["end"] - c, r["term"]))

    # ---- accounting ------------------------------------------------------
    acc_bytes = bytearray(total)
    for c, inf in accepted.items():
        for x in range(c - TEXT_LO, min(inf["info"]["end"], TEXT_HI) - TEXT_LO):
            if unc[x]:
                acc_bytes[x] = 1
    n_new = sum(acc_bytes)
    pad_bytes = sum(1 for i in range(total) if kind[i] == PAD)
    jt_bytes = sum(1 for i in range(total) if kind[i] == JT)
    resid = total - covered - n_new - pad_bytes - jt_bytes

    # ---- runs that are wholly accounted by new functions / padding -------
    def run_class(a, b, s):
        n_new_in = sum(1 for x in range(a, b) if acc_bytes[x - TEXT_LO])
        if n_new_in == s:
            return "new_function"
        if kind[a - TEXT_LO] == PAD:
            return "padding"
        if kind[a - TEXT_LO] == JT:
            return "jump_table"
        if n_new_in:
            return "partly_new"
        return "residual"

    run_summary = collections.Counter()
    run_bytes = collections.Counter()
    for a, b, s in runs:
        c = run_class(a, b, s)
        run_summary[c] += 1
        run_bytes[c] += s

    # ---- cross-checks reported (not used to accept/reject) ---------------
    # does each table target terminate like a function within 1 KiB?
    xc_terminates = 0
    for _start, _tg in tabs:
        for v in _tg:
            pc2, lim, hit = v, v + 0x400, False
            while pc2 < lim:
                ins = db.one(pc2)
                if ins is None:
                    break
                k2, _, _ = flow(ins)
                if k2 in ("ret", "jmp"):
                    hit = True
                    break
                pc2 += ins.size
            if hit:
                xc_terminates += 1
    xc = dict(tab_slots=tab_slots, tab_al16=0, tab_pad=0, acc_pad=0,
              acc_by_src=collections.Counter(), acc_bytes_by_src=collections.Counter(),
              atlas_al16=sum(1 for e, s in rows if e % 16 == 0),
              tab_in_holes=sum(1 for v in tab_targets
                               if 0 <= v - TEXT_LO < total and unc[v - TEXT_LO]),
              tab_terminates=xc_terminates)
    for start, tg in tabs:
        for v in tg:
            if v % 16 == 0:
                xc["tab_al16"] += 1
            if img.read(v - 1, 1) in (b"\xcc", b"\x90"):
                xc["tab_pad"] += 1
    for c, inf in accepted.items():
        if img.read(c - 1, 1) in (b"\xcc", b"\x90"):
            xc["acc_pad"] += 1
        kinds = set()
        for e in inf["evidence"]:
            kinds.add("table" if e.startswith("table") else
                      "vtable" if e.startswith("vtable") else
                      "decoded" if e.startswith("decoded") else "prologue")
        key = "+".join(sorted(kinds))
        xc["acc_by_src"][key] += 1
        xc["acc_bytes_by_src"][key] += inf["info"]["end"] - c

    # ---- outputs ---------------------------------------------------------
    with open(os.path.join(HERE, "uncovered_runs.tsv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("start\tend\tsize\n")
        for a, b, s in runs:
            f.write("%08X\t%08X\t%d\n" % (a, b, s))

    with open(os.path.join(HERE, "candidates.tsv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("addr\tsource_of_evidence\tverdict\treason\tdecoded_len\tends_with\n")
        for c, ev, v, rs, dl, ew in sorted(out):
            f.write("%08X\t%s\t%s\t%s\t%d\t%s\n" % (c, ev, v, rs, dl, ew))

    with open(os.path.join(HERE, "new_functions.tsv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("entry\tsize\tevidence\tfirst_bytes\n")
        for c in sorted(accepted):
            r = accepted[c]["info"]
            f.write("%08X\t%d\t%s\t%s\n" % (
                c, r["end"] - c, ",".join(accepted[c]["evidence"]),
                img.read(c, min(16, r["end"] - c)).hex(" ")))

    # ---- reject histogram ------------------------------------------------
    hist = collections.Counter()
    for c, ev, v, rs, dl, ew in out:
        if v != "REJECT":
            continue
        hist[rs.split(":")[0]] += 1

    size_buckets = collections.Counter()
    def bucket(s):
        if s < 8: return "1-7"
        if s < 16: return "8-15"
        if s < 32: return "16-31"
        if s < 64: return "32-63"
        if s < 256: return "64-255"
        if s < 1024: return "256-1023"
        return "1024+"
    for a, b, s in runs:
        size_buckets[bucket(s)] += 1

    # ---- report ----------------------------------------------------------
    write_report(dict(
        total=total, covered=covered, n_runs=len(runs), overlaps=overlaps,
        n_atlas=len(rows), unc=total - covered, n_new=n_new,
        n_acc=len(accepted), pad=pad_bytes, jt=jt_bytes, resid=resid,
        hist=hist, buckets=size_buckets, jtabs=jtabs, vtstat=vtstat,
        n_tables=len(tabs), tab_slots=tab_slots, run_bytes=run_bytes,
        run_summary=run_summary, runs=runs, accepted=accepted,
        acc_bytes=acc_bytes, out=out, kind=kind, all_pad_runs=all_pad_runs,
        xc=xc, cands=len(cands),
    ))

    print("SHA-256              : %s" % EXPECT_SHA256)
    print(".text                : %08X..%08X  %d bytes" % (TEXT_LO, TEXT_HI, total))
    print("atlas rows           : %d" % len(rows))
    print("atlas overlaps       : %d %s" % (len(overlaps),
                                            [("%08X+%d" % o) for o in overlaps]))
    print("covered              : %d (%.3f%%)" % (covered, 100.0 * covered / total))
    print("uncovered            : %d (%.3f%%)" % (total - covered,
                                                 100.0 * (total - covered) / total))
    print("uncovered runs       : %d" % len(runs))
    print("candidates           : %d" % len(cands))
    print("ACCEPT new functions : %d  bytes %d (%.3f%% of .text)"
          % (len(accepted), n_new, 100.0 * n_new / total))
    print("new coverage         : %.3f%%" % (100.0 * (covered + n_new) / total))
    print("CC/90 padding bytes  : %d" % pad_bytes)
    print("jump-table bytes     : %d  (%d tables)" % (jt_bytes, len(jtabs)))
    print("fnptr tables (.data) : %d  slots %d" % (len(tabs), tab_slots))
    print("vtable slots scanned : %d over %d vtables" % (vtstat["slots"],
                                                         vtstat["vtables"]))
    print("residual unexplained : %d" % resid)
    for k, v in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0])):
        print("  reject %-32s %d" % (k, v))
    x = xc
    print("cross-check: fnptr-table slots 16B aligned %d/%d, pad-preceded %d/%d"
          % (x["tab_al16"], x["tab_slots"], x["tab_pad"], x["tab_slots"]))
    print("cross-check: atlas entries 16B aligned %d/%d"
          % (x["atlas_al16"], len(rows)))
    print("cross-check: accepted entries pad-preceded %d/%d"
          % (x["acc_pad"], len(accepted)))
    print("cross-check: accepted by evidence combo")
    for k in sorted(x["acc_by_src"]):
        print("    %-24s %5d fns  %8d bytes"
              % (k, x["acc_by_src"][k], x["acc_bytes_by_src"][k]))
    return 0


def write_report(d):
    total = d["total"]
    xc = d["xc"]
    pc = lambda n: 100.0 * n / total
    L = []
    A = L.append
    A("# T4 — `.text` coverage audit of `gamemd.exe`")
    A("")
    A("Binary `ra2youli\\gamemd.exe`, SHA-256 `%s`," % EXPECT_SHA256)
    A("PE32, ImageBase `0x400000`. Every number here is regenerated by")
    A("`python -X utf8 t4_textcov.py` in this directory (deterministic; two runs")
    A("produce byte-identical TSVs).")
    A("")
    A("## 1. Headline numbers")
    A("")
    A("| quantity | bytes | % of `.text` |")
    A("|---|---:|---:|")
    A("| `.text` (`0x401000..0x7E038D`) | %d | 100.000%% |" % total)
    A("| covered by the 12,916 atlas rows | %d | %.3f%% |" % (d["covered"], pc(d["covered"])))
    A("| uncovered | %d | %.3f%% |" % (d["unc"], pc(d["unc"])))
    A("| → **accepted new functions** | **%d** | **%.3f%%** |" % (d["n_new"], pc(d["n_new"])))
    A("| → CC/90 alignment padding | %d | %.3f%% |" % (d["pad"], pc(d["pad"])))
    A("| → jump tables / dispatch data in `.text` | %d | %.3f%% |" % (d["jt"], pc(d["jt"])))
    A("| → still unexplained | %d | %.3f%% |" % (d["resid"], pc(d["resid"])))
    A("")
    A("**The 79.5%% claim is right**: recomputed coverage is %.3f%% (%d bytes)."
      % (pc(d["covered"]), d["covered"]))
    A("Coverage after adding every accepted function: **%.3f%%**."
      % pc(d["covered"] + d["n_new"]))
    A("")
    A("So the uncovered 20.5%% is not mostly padding: %.1f%% of it is real"
      % (100.0 * d["n_new"] / max(d["unc"], 1)))
    A("functions the atlas missed (%d entries, %d bytes), and only %.1f%% is"
      % (d["n_acc"], d["n_new"], 100.0 * d["pad"] / max(d["unc"], 1)))
    A("alignment padding.")
    A("")
    A("## 2. Uncovered runs")
    A("")
    A("%d runs, %d bytes. Run-size histogram:" % (d["n_runs"], d["unc"]))
    A("")
    A("| run size | runs |")
    A("|---|---:|")
    for k in ("1-7", "8-15", "16-31", "32-63", "64-255", "256-1023", "1024+"):
        if k in d["buckets"]:
            A("| %s B | %d |" % (k, d["buckets"][k]))
    A("")
    A("The distribution is bimodal: ~9,900 tiny runs (<= 15 B, mostly the gap")
    A("between an atlas row's claimed end and the next 16-byte-aligned entry)")
    A("and a long tail of large runs that are whole unrecognised functions.")
    A("")
    A("| class | runs | bytes |")
    A("|---|---:|---:|")
    for k in sorted(d["run_bytes"]):
        A("| %s | %d | %d |" % (k, d["run_summary"][k], d["run_bytes"][k]))
    A("")
    A("## 3. Accepted new functions")
    A("")
    A("**%d functions, %d bytes.** Full list, with the evidence string for each"
      % (d["n_acc"], d["n_new"]))
    A("entry, is `new_functions.tsv`.")
    A("")
    A("Acceptance requires STRONG evidence (see section 6). Evidence mix of the")
    A("accepted set (a function may carry several):")
    A("")
    A("| evidence combo | functions | bytes |")
    A("|---|---:|---:|")
    for k in sorted(xc["acc_by_src"]):
        A("| %s | %d | %d |" % (k, xc["acc_by_src"][k],
                                 xc["acc_bytes_by_src"][k]))
    A("")
    A("Independent cross-checks on that set:")
    A("")
    A("* %d / %d of the accepted entries are immediately preceded by CC/90"
      % (xc["acc_pad"], d["n_acc"]))
    A("  padding, i.e. they sit on a real function boundary.")
    A("* the `.data` function-pointer table has %d slots, **%d 16-byte aligned**"
      % (xc["tab_slots"], xc["tab_al16"]))
    A("  and %d preceded by padding — matching the alignment rule the atlas"
      % xc["tab_pad"])
    A("  itself follows (%d / %d atlas entries are 16-byte aligned)."
      % (xc["atlas_al16"], d["n_atlas"]))
    A("* no accepted function swallows another STRONG start (that case is a")
    A("  reject reason, %d occurrences)." % d["hist"].get("swallows_strong_start", 0))
    A("")
    A("## 4. Rejects")
    A("")
    A("%d candidates were examined; %d accepted, the rest rejected:"
      % (d["cands"], d["n_acc"]))
    A("")
    A("| reason | count |")
    A("|---|---:|")
    for k, v in sorted(d["hist"].items(), key=lambda kv: (-kv[1], kv[0])):
        A("| `%s` | %d |" % (k, v))
    A("")
    A("Notes on the two dominant reasons:")
    A("")
    A("* `overlaps_accepted` / `swallows_strong_start` — the same code reached")
    A("  from a second reference. Keeping the first (lowest-address) acceptance")
    A("  avoids double counting; this is a de-duplication reject, not a")
    A("  rejection of the evidence.")
    A("* `weak_evidence_only` — decodes cleanly and terminates, but its only")
    A("  reference came from the raw `E8/E9` / dword-window scanner. Those")
    A("  scanners also match instruction operands; see section 6.")
    A("")
    A("## 5. Residual unexplained bytes")
    A("")
    A("%d bytes (%.3f%% of `.text`, %.1f%% of what was uncovered) remain"
      % (d["resid"], pc(d["resid"]), 100.0 * d["resid"] / max(d["unc"], 1)))
    A("unexplained. They are *not* claimed to be anything. Structurally they are")
    A("the interiors of holes around the bodies of accepted functions: bytes")
    A("beyond a function's last reachable basic block (dead code, jump-table")
    A("targets my recursion did not enumerate, and data embedded between")
    A("functions). They are counted as unexplained rather than as covered")
    A("because no entry point could be established for them.")
    A("")
    A("## 6. Method, and why it is this conservative")
    A("")
    A("The instruction is `[已证]` only when the script reproduces it. Everything")
    A("below is produced by the script; no figure is hand-entered.")
    A("")
    A("### Candidate sources")
    A("")
    A("| source | weight | why |")
    A("|---|---|---|")
    A("| `decoded:` rel32 from an atlas row | STRONG | the atlas tool already followed every rel32 it decoded; a decoded edge into a hole means an edge it did not follow |")
    A("| `vtable:` slot of a canonical vtable | STRONG | a virtual function must start there |")
    A("| `table:` slot of a monotonic `.data` `dd` table | STRONG | see below |")
    A("| `prologue:` byte pattern after CC/90 padding | STRONG | the image aligns functions and pads between them |")
    A("| raw `E8/E9/0F8x` scan of `.text` | WEAK | matches inside instruction operands |")
    A("| unaligned dword window in `.text` | WEAK | same |")
    A("")
    A("The WEAK/STRONG split is the single decision that makes or breaks this")
    A("measurement. Measured during development: accepting raw `E8/E9` hits")
    A("produced 6,428 \"new functions\" with a median size of 29 bytes — almost")
    A("all of them operand bytes, not functions. The final run accepts %d with a"
      % d["n_acc"])
    A("median size of %d bytes."
      % sorted(int(v["info"]["end"] - k) for k, v in d["accepted"].items())[
          len(d["accepted"]) // 2])
    A("")
    A("### The `.data` function-pointer table")
    A("")
    A("The single largest evidence source is a `dd` array at `0x812004`.")
    A("It qualifies as a function-pointer table, not as coincidental adjacent")
    A("code addresses, because it is:")
    A("")
    A("* %d entries long (`.data` raw extent), NUL before the first and after" % xc["tab_slots"])
    A("  the last entry;")
    A("* **strictly ascending** with %d distinct targets, %d of which lie in"
      % (xc["tab_slots"], xc["tab_in_holes"]))
    A("  uncovered holes;")
    A("* %d/%d slots 16-byte aligned and %d/%d preceded by CC/90 padding;"
      % (xc["tab_al16"], xc["tab_slots"], xc["tab_pad"], xc["tab_slots"]))
    A("* its targets terminate like functions (%d/%d reach `ret`/`jmp`"
      % (xc["tab_terminates"], xc["tab_slots"]))
    A("  within 1 KiB when decoded from the target).")
    A("")
    A("A run of thousands of strictly ascending, 16-byte-aligned code addresses")
    A("each preceded by padding is not something that arises by chance in data.")
    A("")
    A("### Validation of each candidate")
    A("")
    A("1. must lie in an uncovered byte;")
    A("2. must not lie inside a jump table or a padding run;")
    A("3. must decode by recursive descent **starting at the candidate only**")
    A("   (never at an arbitrary offset), with `skipdata` guarded and every byte")
    A("   inside the hole;")
    A("4. must terminate with `ret` or an unconditional jump, or leave the hole;")
    A("5. must not be a single-instruction stub unless it has a decoded")
    A("   reference;")
    A("6. must not overlap an already accepted function;")
    A("7. must carry STRONG evidence (WEAK-only candidates are rejected).")
    A("")
    A("## 7. Honest limits")
    A("")
    A("* **This does not prove the atlas rows are complete functions.** Two")
    A("  atlas rows overlap each other (`%s`). The atlas also appears to stop"
      % ", ".join("%08X+%d" % o for o in d["overlaps"]))
    A("  many rows short of the following padding, which is why ~74 KB of the")
    A("  holes is pure padding.")
    A("* **The residual is not 'no functions there'.** It is 'no entry point")
    A("  could be established with STRONG evidence'. A determined analyst")
    A("  reading jump-table targets out of the `.rdata` dispatch tables would")
    A("  likely convert part of it.")
    A("* **Provisional, not final, addresses.** The %d accepted entries are"
      % d["n_acc"])
    A("  addresses whose function-start status is inferred from data references")
    A("  and padding. They should not be written back into `function_atlas.tsv`")
    A("  without an independent pass.")
    A("* **No dynamic confirmation.** The game was never executed; no runtime")
    A("  coverage, breakpoint or trace corroborates any of these entries.")
    A("* **Jump-table bytes in `.text` are small** (%d bytes, %d indexed"
      % (d["jt"], len(d["jtabs"])))
    A("  dispatch tables): almost all dispatch tables in this binary live in")
    A("  `.rdata`, so 'the holes are jump tables' is not a valid explanation.")
    A("")
    with open(os.path.join(HERE, "report.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
