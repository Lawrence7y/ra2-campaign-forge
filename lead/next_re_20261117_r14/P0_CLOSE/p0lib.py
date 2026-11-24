#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE 独立分析库（自写 PE 解析 / capstone 5.0.7 / RTTI 虚表定界）。

写域：本目录。全程只读受审 `ra2youli\\gamemd.exe`。
- 自写 struct PE 解析，不 import pefile。
- capstone 一律 skipdata=True（纪律）。
- 站点归属一律用「函数区间包含」（owner），不用 entry_at_or_before。
- 不读 vtables_v2.json；虚表由 .rdata 现场定界。
"""
import os
import struct
import array
import bisect

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

_r14 = os.path.join(r"D:\Project\ra2-campaign-forge\lead", "next_re_20261117_r14")

# 片边界：atlas 数据行区间。C01..C09 各 1292 行，C10 = 1288 行（与各片 VERDICT 自述一致）。
SLICES = {}
for _k in range(1, 10):
    SLICES["C%02d" % _k] = (1292 * (_k - 1), 1292 * _k)
SLICES["C10"] = (11628, 12916)


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

    # ---- 地址换算 ----
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
                break  # 越过 raw 数据（零填充尾巴）不读，避免伪造字节
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


# ---------------- capstone ----------------
def md_new():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    md.detail = False
    return md


class Sweep:
    """全 .text 线性扫（skipdata=True）。仅保留 starts/sizes/mn-code。"""

    def __init__(self, pe, lo, hi):
        s = pe.byname[".text"]
        self.lo = lo
        self.hi = hi
        data = pe.read(lo, hi - lo)
        md = md_new()
        codes = {}
        mn = array.array("H")
        starts = array.array("I")
        sizes = array.array("B")
        for ins in md.disasm(data, lo):
            m = ins.mnemonic
            c = codes.get(m)
            if c is None:
                c = len(codes)
                codes[m] = c
            starts.append(ins.address)
            sizes.append(ins.size)
            mn.append(c)
        self.starts = starts
        self.sizes = sizes
        self.mncode = mn
        self.codes = codes
        self.names = {v: k for k, v in codes.items()}
        self.n = len(starts)

    def mn(self, i):
        return self.names[self.mncode[i]]

    def index_of(self, va):
        i = bisect.bisect_left(self.starts, va)
        if i < self.n and self.starts[i] == va:
            return i
        return -1

    def covering(self, va):
        """包含 va 的线性扫指令下标（-1 = 无）。"""
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0 and self.starts[i] <= va < self.starts[i] + self.sizes[i]:
            return i
        return -1


# ---------------- atlas ----------------
class Atlas:
    def __init__(self, path=ATLAS):
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            h = f.readline().rstrip("\n").split("\t")
            for ln in f:
                if not ln.strip():
                    continue
                r = dict(zip(h, ln.rstrip("\n").split("\t")))
                rows.append((int(r["entry"], 16), int(r["size"])))
        self.rows = rows
        self.n = len(rows)
        self.entries = [e for e, _ in rows]
        # 合并区间（防止 entry+size 与下一 entry 交叠）
        merged = []
        for e, sz in rows:
            if merged and e <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e + sz)
            else:
                merged.append([e, e + sz])
        self.merged = [(a, b) for a, b in merged]
        self.mstarts = [a for a, _ in self.merged]
        self._overlaps = sum(1 for i in range(1, len(rows)) if rows[i - 1][0] + rows[i - 1][1] > rows[i][0])

    def owner(self, va):
        """函数区间包含判定。返回 entry 或 None。"""
        i = bisect.bisect_right(self.entries, va) - 1
        if i >= 0 and self.entries[i] <= va < self.entries[i] + self.rows[i][1]:
            return self.entries[i]
        return None

    def in_atlas(self, va):
        return self.owner(va) is not None

    def hole(self, va, lo, hi):
        """返回 va 所在的未覆盖区段 [a,b)；被覆盖或无洞返回 None。"""
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

    def slice_range(self, name):
        i0, i1 = SLICES[name]
        sl = self.rows[i0:i1]
        return min(e for e, _ in sl), max(e + s for e, s in sl)


# ---------------- 指令级取证 ----------------
JCC = {
    "ja", "jae", "jb", "jbe", "jc", "je", "jg", "jge", "jl", "jle", "jna", "jnae",
    "jnb", "jnbe", "jnc", "jne", "jng", "jnge", "jnl", "jnle", "jno", "jnp", "jns",
    "jnz", "jo", "jp", "jpe", "jpo", "js", "jz", "jcxz", "jecxz", "jrcxz",
    "loop", "loope", "loopne",
}
TERM_OK = {"nop", "ret", "retn", "retf", "jmp", "int3"}
PAD_BYTES = (0x90, 0xCC, 0xCC)


def disasm_at(pe, va, n=6, span=64):
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
    """T 之前紧邻的连续 0x90 / 0xCC 填充字节数。"""
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


def successor_stub():
    pass


def predecessor(pe, sw, T):
    """判定 T 的前驱指令。返回 dict。

    通路 1（优先）：全局线性扫 —— T 是扫出的指令起点，取前一条。
    通路 2（重同步）：T 不是扫起点时，在 [T-15, T) 内找一条「恰好以 T 结尾」的指令。
    """
    i = sw.index_of(T)
    if i >= 0:
        if i == 0:
            return dict(kind="none", desc="sweep-head", via="sweep", boundary=True, pad=0)
        p = i - 1
        m = sw.mn(p)
        desc = "%s @%08X+%d" % (m, sw.starts[p], sw.sizes[p])
        kind = m if m in TERM_OK else ("other" if m not in TERM_OK else m)
        if m == "nop":
            kind = "nop"
        elif m in ("ret", "retn", "retf"):
            kind = "ret"
        elif m == "jmp":
            kind = "jmp"
        elif m == "int3":
            kind = "int3"
        else:
            kind = "other"
        return dict(kind=kind, desc=desc, via="sweep", boundary=True, pad=0, mn=m)

    # 重同步
    md = md_new()
    best = None
    for s in range(T - 15, T):
        if s < sw.lo:
            continue
        d = pe.read(s, 16)
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
            d += " (sweep: inside %s @%08X+%d)" % (sw.mn(cov), sw.starts[cov], sw.sizes[cov])
        return dict(kind="other", desc=d, via="resync", boundary=False, pad=0, mn="?")
    _, negsz, s, m, sz = best
    if m in ("nop",):
        kind = "nop"
    elif m in ("ret", "retn", "retf"):
        kind = "ret"
    elif m == "jmp":
        kind = "jmp"
    elif m == "int3":
        kind = "int3"
    else:
        kind = "other"
    return dict(kind=kind, desc="%s @%08X+%d" % (m, s, sz), via="resync",
                boundary=False, pad=0, mn=m)


def apply_c5(rows, key_slice="slice", key_T="T", key_hole="hole", key_p4="p1234",
             within=0x100, accepted_of=None):
    """判据 (5)「T 不是同洞近距目标的后者」的正解实现。

    「已有入口」= **同判据下已成立的入口**，因此只被「通过 c1..c4 且已被接受」的更早候选压制。
    证据：按「任一更早候选均压制」的字面实现，14 个压制者里 13 个 T%16!=0（首指令是
    `pop edi`/`xor eax,eax`/`inc eax` 之类函数中部），本身不是入口 ⇒ 字面读法系统性假阴性。
    做法：同片按地址升序贪心：若同洞内已有「被接受」者且 |T−T'| < within ⇒ 本目标为后者。

    返回 None（原地写入 c5 / c5_sup），并返回被压制者明细。
    """
    out = {}
    by = {}
    for r in rows:
        by.setdefault(r[key_slice], []).append(r)
    for sl, rs in by.items():
        acc = []
        for r in sorted(rs, key=lambda x: x[key_T]):
            hole = r.get(key_hole)
            sup = None
            if hole is not None:
                for a in acc:
                    if a["_hole_id"] == (hole[0], hole[1]) and \
                            abs(r[key_T] - a[key_T]) < within:
                        if sup is None or a[key_T] > sup:
                            sup = a[key_T]
            r["c5"] = (sup is None)
            r["c5_sup"] = sup
            r["_hole_id"] = (hole[0], hole[1]) if hole else None
            if r[key_p4] and r["c5"]:
                acc.append(r)
            if sup is not None and r[key_p4]:
                out[r[key_T]] = sup
    for r in rows:
        r.pop("_hole_id", None)
    return out
