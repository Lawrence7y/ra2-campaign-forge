#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-RESIDUAL-2 common library — self-contained. Read-only on gamemd.exe.

- PE via pefile 2024.8.26 + self struct reads; capstone 5.0.7 skipdata=True everywhere.
- Full-.text linear sweep builds: starts[], sizes[], mns[], bytes[], endmap (end_va -> mn).
- Predecessor of T = instruction whose end == T (sweep start preferred, resync fallback).
- Site ownership uses interval containment (Atlas.owner), never entry_at_or_before.
- No vtables_v2.json; vtable/tables derived from raw section bytes.
"""
import os, struct, array, bisect, hashlib
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COVERAGE = os.path.join(R14, "COVERAGE", "coverage.tsv")
PROBE = os.path.join(R14, "COVERAGE", "probe_and_data_entries.tsv")
OUTSIDE = os.path.join(R14, "COVERAGE", "coverage_outside_atlas.tsv")
GATE = os.path.join(R14, "P0_GATE", "ENTRY_ADJUDICATION.tsv")
RESID = os.path.join(R14, "P0_RESIDUAL", "RESIDUAL_ADJUDICATION.tsv")

TERM = {"nop", "int3", "ret", "retf", "jmp"}
JCC = {"j" + s for s in ("a ae b be c cx e g ge l le nae na nb nbe nc ne ng nge nl nle "
                         "no np ns nz o p pe po s z").split()} | {"jecxz", "jcxz", "loop", "loope", "loopne"}
E8E9EB = (0xE8, 0xE9, 0xEB)


def sha256_file(path=EXE):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


class PE:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.IB = self.pe.OPTIONAL_HEADER.ImageBase
        self.data = self.pe.__data__
        self.secs = {}
        for s in self.pe.sections:
            nm = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.IB + s.VirtualAddress
            self.secs[nm] = dict(name=nm, va=va, vsize=s.Misc_VirtualSize,
                                 raw=s.PointerToRawData, rawsize=s.SizeOfRawData,
                                 chars=s.Characteristics)
        t = self.secs[".text"]
        self.tlo = t["va"]
        self.thi = t["va"] + t["vsize"]      # vsize (0x7E038D), matches prior cards

    def read(self, va, n):
        for nm, s in self.secs.items():
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.data[off:off + n]
        # allow crossing within .text raw contiguously as fallback
        raise ValueError("VA %08X+%d not in single section raw" % (va, n))

    def try_read(self, va, n):
        try:
            return self.read(va, n)
        except Exception:
            return b""

    def byte(self, va):
        for nm, s in self.secs.items():
            if s["va"] <= va < s["va"] + s["rawsize"]:
                return self.data[s["raw"] + (va - s["va"])]
        return None

    def u32(self, va):
        d = self.read(va, 4)
        return struct.unpack("<I", d)[0]

    def in_text(self, va):
        return self.tlo <= va < self.thi

    def text_bounds(self):
        return self.tlo, self.thi


def md32(skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = False
    m.skipdata = skipdata
    return m


class Sweep:
    def __init__(self, pe):
        t = pe.secs[".text"]
        buf = pe.data[t["raw"]:t["raw"] + t["rawsize"]]
        md = md32(True)
        starts = array.array("I"); sizes = array.array("H"); mns = []; bts = []
        endmap = {}
        nskip = 0
        for ins in md.disasm(buf, pe.tlo):
            starts.append(ins.address)
            sz = ins.size if ins.size < 65535 else 65535
            sizes.append(sz)
            mns.append(ins.mnemonic if ins.id else ".byte")
            bts.append(bytes(ins.bytes))
            if ins.id:
                endmap[ins.address + ins.size] = ins.mnemonic
            else:
                nskip += ins.size
        self.starts = starts; self.sizes = sizes; self.mns = mns; self.bts = bts
        self.n = len(starts); self.startset = set(starts); self.endmap = endmap
        self.nskip = nskip

    def index_of(self, va):
        i = bisect.bisect_left(self.starts, va)
        return i if i < self.n and self.starts[i] == va else -1

    def insn_at(self, pe, va, maxb=16):
        d = pe.try_read(va, maxb)
        if not d:
            return None
        for ins in md32(True).disasm(d, va):
            return ins
        return None

    def pred(self, pe, T):
        """Return (kind_mnemonic, end_va, via) for instruction ending exactly at T."""
        # prefer sweep start predecessor
        i = bisect.bisect_left(self.starts, T)
        if 0 < i <= self.n:
            s = self.starts[i - 1]
            if s + self.sizes[i - 1] == T:
                return (self.mns[i - 1], s, "sweep")
        # resync: try starts in [T-15,T)
        best = None
        for s in range(T - 15, T):
            if s < pe.tlo:
                continue
            d = pe.try_read(s, 16)
            if not d:
                continue
            for ins in md32(True).disasm(d, s):
                if ins.address + ins.size == T and ins.id:
                    cand = (0 if s in self.startset else 1, -ins.size, s, ins.mnemonic)
                    if best is None or cand < best:
                        best = cand
                break
        if best is None:
            return (None, None, "none")
        return (best[3], best[2], "resync")


class Atlas:
    """Atlas intervals; size column decimal."""
    def __init__(self, path=ATLAS):
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            h = f.readline().rstrip("\n").split("\t")
            hi = {k: i for i, k in enumerate(h)}
            for ln in f:
                if not ln.strip():
                    continue
                p = ln.rstrip("\n").split("\t")
                e = int(p[hi["entry"]], 16); sz = int(p[hi["size"]])
                rows.append((e, sz))
        self.rows = rows; self.n = len(rows)
        self.entries = sorted(e for e, _ in rows)
        self.d = dict(rows)
        merged = []
        for e, sz in sorted(rows):
            if merged and e <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e + sz)
            else:
                merged.append([e, e + sz])
        self.merged = [(a, b) for a, b in merged]
        self.mstarts = [a for a, _ in self.merged]

    def owner(self, va):
        i = bisect.bisect_right(self.entries, va) - 1
        if i >= 0 and self.entries[i] <= va < self.entries[i] + self.d[self.entries[i]]:
            return self.entries[i]
        return None

    def in_atlas(self, va):
        return self.owner(va) is not None

    def hole(self, va, lo, hi):
        i = bisect.bisect_right(self.mstarts, va) - 1
        if i >= 0 and self.mstarts[i] <= va < self.merged[i][1]:
            return None
        nxt = self.merged[i][1] if i >= 0 else lo
        prv = self.merged[i + 1][0] if i + 1 < len(self.merged) else hi
        a = max(nxt, lo); b = min(prv, hi)
        return (a, b) if a <= va < b else None


def load_set(path, col=0, has_header=True, filt=None):
    out = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        if has_header:
            f.readline()
        for ln in f:
            if not ln.strip():
                continue
            p = ln.rstrip("\n").split("\t")
            try:
                v = int(p[col], 16)
            except Exception:
                continue
            if filt and not filt(p):
                continue
            out.add(v)
    return out


def form_c4a(b):
    """c4a prologue predicate on raw bytes (from audit a13)."""
    if not b or len(b) < 3:
        return False
    if b[0] in (0x55, 0x68):
        return True
    if b[0] == 0x83 and b[1] == 0xEC:
        return True
    if b[0] == 0x81 and b[1] == 0xEC:
        return True
    if b[0] in (0x53, 0x56, 0x57):
        for k in range(1, 4):
            if k + 2 < len(b) and b[k] == 0x83 and b[k + 1] == 0xEC:
                return True
    return False


def leafpat(b):
    if not b or len(b) < 3:
        return False
    return ((b[0] == 0x8B and (b[1] & 0xF0) == 0x40 and b[2] == 0x24) or
            (b[0] == 0x8B and b[1] == 0x41) or b[0] in (0x57, 0x56, 0x53))
