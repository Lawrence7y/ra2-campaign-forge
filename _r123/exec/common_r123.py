#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R123 exec 公共底座（deepseek / work/cn:deepseek-v4.1-flash）

只读 ra2bench/gamemd.exe。所有数字均由本模块的代码从二进制字节自己算出，
不读 _r122 的任何计数（_r122/r122a_objs35.json 仅作为「站点地址对照」的正控基准）。

内存纪律：
  * .text（0x3e0000 字节）只做一次 capstone disasm_lite（detail=False），
    结果压进 4 个 array（addr u32 / size u8 / mnem u8 / imm i32），约 14 MB 常驻，
    不保存 139 万条 Python 元组（那会吃掉 300+ MB）。
  * 需要指令长度/操作数细节的少数函数才开 detail=True。
"""

import array
import hashlib
import os
import struct

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
OUTDIR = "/home/t628/projects/ra2-campaign-forge/_r123/exec"

IMAGE_BASE = 0x400000
# pefile 实测（每脚本入口都会复核一次，漂移即报错）
SECTIONS = [  # (name, va, ptr_raw, size_raw, vsize)
    (".text",   0x401000, 0x1000, 0x3E0000, 0x3DF38D),
    (".rdata",  0x7E1000, 0x3E1000, 0x31000,  0x30074),
    (".data",   0x812000, 0x412000, 0x6C000,  0x367BE4),
    (".rsrc",   0xB7A000, 0x47E000, 0x19000,  0x18128),
    (".detour", 0xB93000, 0x497000, 0x3000,   0x2718),
]
TEXT_VA = 0x401000
TEXT_SIZE = 0x3E0000
TEXT_END = TEXT_VA + TEXT_SIZE
RDATA_VA, RDATA_SIZE = 0x7E1000, 0x31000
DATA_VA, DATA_RAWSIZE, DATA_VSIZE = 0x812000, 0x6C000, 0x367BE4
DATA_INIT_LO = DATA_VA                       # .data 有文件字节的已初始化区
DATA_INIT_HI = DATA_VA + DATA_RAWSIZE        # 0x87e000 = BSS 起点
BSS_LO, BSS_HI = DATA_INIT_HI, DATA_VA + DATA_VSIZE

_DATA = None


def load():
    global _DATA
    if _DATA is None:
        with open(EXE, "rb") as f:
            _DATA = f.read()
    return _DATA


def sha256():
    return hashlib.sha256(load()).hexdigest()


def rd(va, n):
    """只返回落在同一节 raw（有文件字节）范围内的字节。"""
    d = load()
    for _nm, sva, praw, rs, _vs in SECTIONS:
        if sva <= va and va + n <= sva + rs:
            o = praw + (va - sva)
            return d[o:o + n]
    return None


def u32(va):
    b = rd(va, 4)
    if b is None or len(b) < 4:
        return None
    return struct.unpack("<I", b)[0]


def cstr(va, n=256):
    b = rd(va, n)
    if b is None:
        return None
    e = b.find(b"\x00")
    if e < 0:
        return None
    return b[:e].decode("latin-1")


def verify_pe():
    import pefile
    pe = pefile.PE(EXE, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    got = [(s.Name.rstrip(b"\x00").decode("latin-1"), ib + s.VirtualAddress,
            s.PointerToRawData, s.SizeOfRawData, s.Misc_VirtualSize) for s in pe.sections]
    pe.close()
    return ib, got


# ---------------------------------------------------------------- 指令流缓存

MNEMS = ["push", "call", "ret", "jmp", "mov", "other"]
MN_ID = {m: i for i, m in enumerate(MNEMS)}
M_PUSH, M_CALL, M_RET, M_JMP, M_MOV, M_OTHER = range(6)


def _mnem_id(m):
    if m == "push":
        return M_PUSH
    if m == "call":
        return M_CALL
    if m.startswith("ret"):
        return M_RET
    if m.startswith("j"):
        return M_JMP
    if m.startswith("mov") or m.startswith("c6") or m.startswith("c7"):
        return M_MOV
    return M_OTHER


CACHE = os.path.join(OUTDIR, "_insntext.bin")


def build_insns(skipdata=True, force=False):
    """返回 (addr array('I'), size array('B'), mn array('B'), imm array('i')).

    imm: 对 push 指令是立即数（[esp+disp] 之类不是 0x... 形态则记 -1）；
         对 call/jmp 是绝对目标；其余 -1。
    同时返回 (n_insn, last_end, stopped_early_reason)。
    """
    if not skipdata:
        # 反控专用：不落盘缓存
        return _disasm(skipdata=False)
    if os.path.exists(CACHE) and not force:
        with open(CACHE, "rb") as f:
            head = f.read(12)
            n, last_end, nser = struct.unpack("<III", head)
            a = array.array("I")
            a.fromfile(f, n)
            s = array.array("B")
            s.fromfile(f, n)
            m = array.array("B")
            m.fromfile(f, n)
            i = array.array("q")
            i.fromfile(f, n)
        return a, s, m, i, n, last_end, None
    a, s, m, i, n, last_end, why = _disasm(skipdata=True)
    with open(CACHE, "wb") as f:
        f.write(struct.pack("<III", n, last_end, 0))
        a.tofile(f)
        s.tofile(f)
        m.tofile(f)
        i.tofile(f)
    return a, s, m, i, n, last_end, why


def _disasm(skipdata):
    import capstone
    d = load()
    text = d[0x1000:0x1000 + TEXT_SIZE]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = bool(skipdata)
    A = array.array("I")
    S = array.array("B")
    M = array.array("B")
    I = array.array("q")
    why = None
    last_end = TEXT_VA
    try:
        for addr, size, mnem, opstr in md.disasm_lite(text, TEXT_VA):
            A.append(addr)
            S.append(size)
            M.append(_mnem_id(mnem))
            v = -1
            try:
                if mnem == "push" and opstr.startswith("0x"):
                    v = int(opstr, 16)
                elif mnem in ("call", "jmp") and opstr.startswith("0x"):
                    v = int(opstr, 16)
            except ValueError:
                v = -1
            I.append(v)
            last_end = addr + size
    except capstone.CsError as e:      # 无 skipdata 时必然走到这里
        why = "CsError@0x%08x:%s" % (last_end, e)
    if why is None and last_end < TEXT_END:
        why = "stop@0x%08x" % last_end
    return A, S, M, I, len(A), last_end, why


class Insns(object):
    def __init__(self, skipdata=True):
        (self.a, self.s, self.m, self.i,
         self.n, self.last_end, self.why) = build_insns(skipdata=skipdata)
        self.index = None

    def idx_of(self, va):
        """线性扫描建立 va -> 下标（只在需要时建，一次 ~0.5 s）。"""
        if self.index is None:
            self.index = {int(x): k for k, x in enumerate(self.a)}
        return self.index.get(va)

    def find_va(self, va):
        """二分找精确地址（不建全表，供少数桩用）。"""
        import bisect
        k = bisect.bisect_left(self.a, va)
        if k < self.n and self.a[k] == va:
            return k
        return None


# ---------------------------------------------------------------- 代码单元

def unit_starts(ins):
    """ret 之后第一个非填充指令（0x90 / 0xcc 单字节填充不算）为新单元起点。

    返回 array('I')，升序；首项为 0x401000。
    """
    d = load()
    base = 0x1000 + (TEXT_VA - TEXT_VA)
    starts = array.array("I", [TEXT_VA])
    armed = False
    for k in range(ins.n):
        addr = int(ins.a[k])
        size = int(ins.s[k])
        b = d[base + (addr - TEXT_VA): base + (addr - TEXT_VA) + size]
        pad = (b == b"\x90" * size) or (b == b"\xcc" * size)
        if ins.m[k] == M_RET:
            armed = True
            continue
        if armed and not pad:
            starts.append(addr)
            armed = False
    return starts


def unit_of(starts, va):
    import bisect
    k = bisect.bisect_right(starts, va) - 1
    if k < 0:
        return None
    return int(starts[k])


def unit_range(starts, idx):
    """单元 [start, next_start)。"""
    s = int(starts[idx])
    e = int(starts[idx + 1]) if idx + 1 < len(starts) else TEXT_END
    return s, e


# ---------------------------------------------------------------- RTTI

def rtti(vtable_va):
    """MSVC x86: [vtable-4] = CompleteObjectLocator(24B)
    +0 sig, +4 this-offset, +8 cdOffset, +12 pTypeDescriptor, +16 pClassDescriptor, +20 pSelf
    TypeDescriptor: +8 = mangled name。返回 dict 或 None。"""
    col = u32(vtable_va - 4)
    if not col:
        return None
    b = rd(col, 24)
    if b is None:
        return None
    sig, toff, cdoff, ptd, pcd, pself = struct.unpack("<6I", b)
    if sig != 0 or not ptd:
        return None
    nm = cstr(ptd + 8, 256)
    if not nm or not nm.startswith(".?AV"):
        return None
    out = dict(vtable=vtable_va, col=col, sig=sig, this_off=toff, cd_off=cdoff,
               ptd=ptd, pcd=pcd, pself=pself, name=nm)
    # ClassHierarchyDescriptor 基类数组（+12 = pBaseClassArray）
    hb = rd(pcd, 16) if pcd else None
    out["bases"] = []
    if hb is not None:
        csig, cattr, nb, pbca = struct.unpack("<4I", hb)
        out["chd"] = dict(sig=csig, attr=cattr, nbase=nb, pbca=pbca)
        if pbca and 0 < nb <= 64:
            for j in range(nb):
                p = u32(pbca + 4 * j)
                if not p:
                    continue
                bcd = rd(p, 24)
                if bcd is None:
                    continue
                ptd2, ncb, mdisp, pdisp, vdisp, attr2 = struct.unpack("<6I", bcd)
                nm2 = cstr(ptd2 + 8, 256) if ptd2 else None
                out["bases"].append(dict(bcd=p, ptd=ptd2, name=nm2,
                                         ncb=ncb, mdisp=mdisp, attr=attr2))
    else:
        out["chd"] = None
    return out


# ---------------------------------------------------------------- c7 05 站点

def scan_c705(ins):
    """基于指令边界（而非裸字节）的 c7 05 站点：10 字节指令，modrm==0x05。

    返回 [(site_va, target, imm)]。"""
    d = load()
    base = 0x1000
    out = []
    for k in range(ins.n):
        if ins.s[k] != 10:
            continue
        addr = int(ins.a[k])
        off = base + (addr - TEXT_VA)
        if d[off] != 0xC7 or d[off + 1] != 0x05:
            continue
        tgt = struct.unpack_from("<I", d, off + 2)[0]
        imm = struct.unpack_from("<I", d, off + 6)[0]
        out.append((addr, tgt, imm))
    return out


# ---------------------------------------------------------------- 自测记账

class Checks(object):
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail=""):
        self.rows.append({"name": name, "pass": bool(ok), "detail": str(detail)[:400]})
        return bool(ok)

    def summary(self):
        p = sum(1 for r in self.rows if r["pass"])
        return {"total": len(self.rows), "passed": p,
                "verdict": "PASS" if p == len(self.rows) else "FAIL"}


def preflight(ck):
    """每个脚本入口都跑：sha + ImageBase + 节表。"""
    ck.add("sha256 与卡面/前轮一致", sha256() == EXPECT_SHA, sha256())
    ib, got = verify_pe()
    ck.add("ImageBase == 0x400000", ib == IMAGE_BASE, hex(ib))
    ok = True
    for (nm, va, praw, rs, vs), g in zip(SECTIONS, got):
        if nm != g[0] or va != g[1] or praw != g[2] or rs != g[3] or vs != g[4]:
            ok = False
    ck.add("节表(va/raw/rawsize/vsize) 与常量一致", ok, str(got[:2]))
    return ib, got


# ---------------------------------------------------------------- 对象/站点派生

TWIN_LO, TWIN_HI = 0x67FDF0, 0x680F80


def twin_targets(ins):
    """独立重导「孪生站」：call rel32 目标落在 [0x67fdf0,0x680f80)，
    且站点前 7 字节是 ba <imm32> 8b ce（mov edx,imm32 ; mov ecx,esi）。
    返回 [(site_va, obj_va)]，按站点升序。"""
    d = load()
    out = []
    for k in range(ins.n):
        if ins.m[k] != M_CALL:
            continue
        t = int(ins.i[k])
        if not (TWIN_LO <= t < TWIN_HI):
            continue
        site = int(ins.a[k])
        off = 0x1000 + (site - TEXT_VA)
        pre = d[off - 7:off]
        if len(pre) == 7 and pre[0] == 0xBA and pre[5:7] == b"\x8b\xce":
            out.append((site, struct.unpack_from("<I", pre, 1)[0]))
    return out


def sites_by_target(ins):
    """{target: [(site, imm)]}，来自指令边界上的 c7 05（10 字节）。"""
    out = {}
    for site, tgt, imm in scan_c705(ins):
        out.setdefault(tgt, []).append((site, imm))
    return out


def raw_c705_hits(ins=None):
    """裸字节 c7 05 扫描（不判指令边界），返回 {target: [(site, imm)]}，用于交叉核对。"""
    d = load()
    text = d[0x1000:0x1000 + TEXT_SIZE]
    out = {}
    i = 0
    while True:
        j = text.find(b"\xc7\x05", i)
        if j < 0 or j + 10 > len(text):
            break
        tgt = struct.unpack_from("<I", text, j + 2)[0]
        imm = struct.unpack_from("<I", text, j + 6)[0]
        out.setdefault(tgt, []).append((TEXT_VA + j, imm))
        i = j + 1
    return out


def unit_index(starts, va):
    import bisect
    k = bisect.bisect_right(starts, va) - 1
    return k if k >= 0 else None


def abs_writes_in_unit(ins, starts, unit_start, base, win):
    """单元体内对 [base, base+win) 的绝对写：c7 05 (4B) / c6 05 (1B) / a3 (4B)。
    返回 {offset: [(kind, width, site)]}。"""
    import bisect
    d = load()
    k = unit_index(starts, unit_start)
    if k is None:
        return {}
    s, e = unit_range(starts, k)
    out = {}
    kk = bisect.bisect_left(ins.a, s)
    while kk < ins.n:
        a = int(ins.a[kk])
        if a >= e:
            break
        sz = int(ins.s[kk])
        off = 0x1000 + (a - TEXT_VA)
        b = d[off:off + sz]
        kind = None
        if sz == 10 and b[0] == 0xC7 and b[1] == 0x05:
            kind, w, toff = "c7 05", 4, 2
        elif sz == 7 and b[0] == 0xC6 and b[1] == 0x05:
            kind, w, toff = "c6 05", 1, 2
        elif sz == 5 and b[0] == 0xA3:
            kind, w, toff = "a3", 4, 1
        if kind is not None:
            tgt = struct.unpack_from("<I", b, toff)[0]
            if base <= tgt < base + win:
                out.setdefault(tgt - base, []).append((kind, w, a))
        kk += 1
    return out
