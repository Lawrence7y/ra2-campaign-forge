#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-RESIDUAL 公共库：自写 PE 解析 / capstone 5.0.7 skipdata=True / atlas 区间包含。

写域仅 P0_RESIDUAL\work\。全程只读 gamemd.exe。
- 自写 struct PE 解析（不 import pefile）。
- capstone 一律 skipdata=True。
- 站点归属用「函数区间包含」(owner)，不用 entry_at_or_before。
- 不读 vtables_v2.json；虚表由 .rdata 现场定界。
"""
import os
import struct
import array
import bisect
import hashlib

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COVERAGE = os.path.join(R14, "COVERAGE", "coverage.tsv")
PROBE = os.path.join(R14, "COVERAGE", "probe_and_data_entries.tsv")
OUTSIDE = os.path.join(R14, "COVERAGE", "coverage_outside_atlas.tsv")


def sha256_file(path=EXE):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class RawPE:
    def __init__(self, path=EXE):
        with open(path, "rb") as f:
            self.buf = f.read()
        b = self.buf
        if b[:2] != b"MZ":
            raise ValueError("not MZ")
        e_lfanew = struct.unpack_from("<I", b, 0x3C)[0]
        if b[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise ValueError("not PE")
        coff = e_lfanew + 4
        nsec = struct.unpack_from("<H", b, coff + 2)[0]
        optsz = struct.unpack_from("<H", b, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from("<H", b, opt)[0]
        if magic != 0x10B:
            raise ValueError("not PE32: %04X" % magic)
        self.imagebase = struct.unpack_from("<I", b, opt + 28)[0]
        self.secalign = struct.unpack_from("<I", b, opt + 32)[0]
        self.filealign = struct.unpack_from("<I", b, opt + 36)[0]
        self.sizeofimage = struct.unpack_from("<I", b, opt + 56)[0]
        self.sizeofheaders = struct.unpack_from("<I", b, opt + 60)[0]
        secs = []
        p = opt + optsz
        for i in range(nsec):
            nm = b[p:p + 8].rstrip(b"\0").decode("latin1")
            vsize, va, rawsize, raw = struct.unpack_from("<IIII", b, p + 8)
            chars = struct.unpack_from("<I", b, p + 36)[0]
            secs.append(dict(name=nm, vsize=vsize, va=va, rawsize=rawsize,
                             raw=raw, chars=chars))
            p += 40
        self.secs = secs
        self.byname = {s["name"]: s for s in secs}

    def sec_of(self, va):
        rva = va - self.imagebase
        for s in self.secs:
            span = max(s["vsize"], s["rawsize"])
            if s["va"] <= rva < s["va"] + span:
                return s
        return None

    def read(self, va, n):
        out = bytearray()
        while n > 0:
            s = self.sec_of(va)
            if s is None:
                break
            rva = va - self.imagebase
            off_in_sec = rva - s["va"]
            if off_in_sec >= s["rawsize"]:
                break
            avail = min(n, s["rawsize"] - off_in_sec)
            fo = s["raw"] + off_in_sec
            out += self.buf[fo:fo + avail]
            va += avail
            n -= avail
        return bytes(out)

    def try_read(self, va, n):
        try:
            return self.read(va, n)
        except Exception:
            return b""

    def u32(self, va):
        d = self.read(va, 4)
        if len(d) < 4:
            raise ValueError("unreadable @%08X" % va)
        return struct.unpack("<I", d)[0]

    def in_text(self, va):
        s = self.byname.get(".text")
        if s is None:
            return False
        lo = self.imagebase + s["va"]
        hi = lo + s["vsize"]
        return lo <= va < hi


def md_new():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    md.detail = False
    return md


class Sweep:
    """全 .text 线性扫（skipdata=True）。保留 starts/sizes/mn/instr bytes。"""

    def __init__(self, pe, lo, hi):
        s = pe.byname[".text"]
        self.lo = lo
        self.hi = hi
        data = pe.read(lo, hi - lo)
        md = md_new()
        starts = array.array("I")
        sizes = array.array("B")
        bytes_list = []
        mns = []
        for ins in md.disasm(data, lo):
            starts.append(ins.address)
            sizes.append(ins.size if ins.size < 256 else 255)
            mns.append(ins.mnemonic)
            bytes_list.append(bytes(ins.bytes))
        self.starts = starts
        self.sizes = sizes
        self.mns = mns
        self.bytes_list = bytes_list
        self.n = len(starts)

    def index_of(self, va):
        i = bisect.bisect_left(self.starts, va)
        if i < self.n and self.starts[i] == va:
            return i
        return -1

    def covering(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0 and self.starts[i] <= va < self.starts[i] + self.sizes[i]:
            return i
        return -1


class Atlas:
    """atlas 函数区间。size 列按【十进制】读。"""

    def __init__(self, path=ATLAS):
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            h = f.readline().rstrip("\n").split("\t")
            hi = {k: i for i, k in enumerate(h)}
            for ln in f:
                if not ln.strip():
                    continue
                p = ln.rstrip("\n").split("\t")
                e = int(p[hi["entry"]], 16)
                sz = int(p[hi["size"]])   # 十进制
                rows.append((e, sz))
        self.rows = rows
        self.n = len(rows)
        self.entries = [e for e, _ in rows]
        merged = []
        for e, sz in rows:
            if merged and e <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e + sz)
            else:
                merged.append([e, e + sz])
        self.merged = [(a, b) for a, b in merged]
        self.mstarts = [a for a, _ in self.merged]
        self._overlaps = sum(1 for i in range(1, len(rows))
                             if rows[i - 1][0] + rows[i - 1][1] > rows[i][0])

    def owner(self, va):
        i = bisect.bisect_right(self.entries, va) - 1
        if i >= 0 and self.entries[i] <= va < self.entries[i] + self.rows[i][1]:
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
        a = max(nxt, lo)
        b = min(prv, hi)
        if a <= va < b:
            return (a, b)
        return None


JCC = {
    "ja", "jae", "jb", "jbe", "jc", "je", "jg", "jge", "jl", "jle", "jna", "jnae",
    "jnb", "jnbe", "jnc", "jne", "jng", "jnge", "jnl", "jnle", "jno", "jnp", "jns",
    "jnz", "jo", "jp", "jpe", "jpo", "js", "jz", "jcxz", "jecxz", "jrcxz",
    "loop", "loope", "loopne",
}
TERM_KINDS = ("nop", "ret", "jmp", "int3")


def classify_pred_kind(mn):
    if mn == "nop":
        return "nop"
    if mn in ("ret", "retn", "retf"):
        return "ret"
    if mn == "jmp":
        return "jmp"
    if mn == "int3":
        return "int3"
    return "other"


def predecessor(pe, sw, T):
    """判定 T 的前驱指令（与 P0-CLOSE p0lib.predecessor 同法）。"""
    i = sw.index_of(T)
    if i >= 0:
        if i == 0:
            return dict(kind="none", desc="sweep-head", via="sweep", boundary=True, mn="none")
        p = i - 1
        m = sw.mns[p]
        desc = "%s @%08X+%d" % (m, sw.starts[p], sw.sizes[p])
        return dict(kind=classify_pred_kind(m), desc=desc, via="sweep",
                    boundary=True, mn=m)
    # 重同步：在 [T-15, T) 找一条恰好以 T 结尾的指令
    md = md_new()
    best = None
    for s in range(T - 15, T):
        if s < sw.lo:
            continue
        d = pe.read(s, 16)
        if not d:
            continue
        for ins in md.disasm(d, s):
            if ins.id == 0:
                break
            if ins.address + ins.size == T:
                is_sw = sw.index_of(s) >= 0
                cand = (0 if is_sw else 1, -ins.size, s, ins.mnemonic, ins.size)
                if best is None or cand < best:
                    best = cand
            break
    cov = sw.covering(T)
    if best is None:
        d = "no-insn-ends-at-T"
        if cov >= 0:
            d += " (sweep: inside %s @%08X+%d)" % (sw.mns[cov], sw.starts[cov], sw.sizes[cov])
        return dict(kind="other", desc=d, via="resync", boundary=False, mn="?")
    _, negsz, s, m, sz = best
    return dict(kind=classify_pred_kind(m), desc="%s @%08X+%d" % (m, s, sz),
                via="resync", boundary=False, mn=m)


def disasm_at(pe, va, n=4, span=64):
    md = md_new()
    d = pe.read(va, span)
    out = []
    for ins in md.disasm(d, va):
        if ins.id == 0:
            out.append((".byte", "0x%02x" % ins.bytes[0], ins.address, ins.size))
        else:
            out.append((ins.mnemonic, ins.op_str, ins.address, ins.size))
        if len(out) >= n:
            break
    return out


def trailing_pad(pe, va, maxn=32):
    d = pe.read(max(0, va - maxn), min(maxn, 64))
    k = 0
    fill = None
    for c in reversed(d):
        if c not in (0x90, 0xCC):
            break
        if fill is None:
            fill = c
        elif c != fill:
            break
        k += 1
    return k, (hex(fill) if fill is not None else None)
