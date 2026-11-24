#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R122 exec2 公共底座（deepseek / work/cn:deepseek-v4.1-flash）

只读 ra2bench/gamemd.exe；所有数字均由本模块代码自己算出。
不读任何既有 _r122/*.json 的计数（symbols.json 只用作「类名族」旁证，不作计数来源；
主口径的类名一律由 .rdata 的 RTTI 链从二进制字节独立反解）。

内存红线：.text 只用 capstone disasm_lite（全程 detail=False），
边界集合用 bytearray 位图（4 MB）而不是 1.4M 个 Python int 的 set。
"""

import hashlib
import os
import struct

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

IMAGE_BASE = 0x400000

# PE 节表（pefile 实测，见下方 verify_pe()）
TEXT_VA = 0x401000
TEXT_RAW = 0x1000          # pefile PointerToRawData 实测
TEXT_SIZE = 0x3E0000       # .text SizeOfRawData
TEXT_END = TEXT_VA + TEXT_SIZE   # 0x7e1000

# 卡面写作 ".data VA 0x812000 raw 0x6c000 VirtualSize 0x367be4"
# 其中 "raw 0x6c000" 实为 SizeOfRawData（文件偏移是 0x412000），已实测确认。
DATA_VA = 0x812000
DATA_RAWSIZE = 0x6C000
DATA_VSIZE = 0x367BE4

BSS_LO = DATA_VA + DATA_RAWSIZE        # 0x87e000
BSS_HI = DATA_VA + DATA_VSIZE          # 0xb79be4

SECTIONS = [
    # (name, virtual_address, pointer_to_raw_data, size_of_raw_data)
    (".text",   0x401000, 0x1000, 0x3E0000),
    (".rdata",  0x7E1000, 0x3E1000, 0x31000),
    (".data",   0x812000, 0x412000, 0x6C000),
    (".rsrc",   0xB7A000, 0x47E000, 0x19000),
    (".detour", 0xB93000, 0x497000, 0x3000),
]

CALL_LO, CALL_HI = 0x67FDF0, 0x680F80
CALL_EXCLUDE = {0x67D193, 0x67E62B}


# ---------------------------------------------------------------- 基础读取

def load_file(path=EXE):
    with open(path, "rb") as f:
        return f.read()


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


class Image(object):
    """VA 读取器（只覆盖有文件字节的 raw 范围）。"""

    def __init__(self, data):
        self.data = data

    def rd(self, va, n):
        for _name, sva, raw, rsize in SECTIONS:
            if sva <= va and va + n <= sva + rsize:
                off = raw + (va - sva)
                return self.data[off:off + n]
        return None

    def u32(self, va):
        b = self.rd(va, 4)
        if b is None or len(b) < 4:
            return None
        return struct.unpack("<I", b)[0]

    # -------- RTTI：vtable -> COL -> TD -> 名字串
    def rtti_name(self, vtable_va):
        """按 [vt-4]=COL, COL+0xc=TD, TD+8=名字串 反解修饰名。"""
        col = self.u32(vtable_va - 4)
        if not col:
            return None
        td = self.u32(col + 12)
        if not td:
            return None
        b = self.rd(td + 8, 256)
        if not b:
            return None
        e = b.find(b"\x00")
        if e < 0:
            return None
        s = b[:e]
        try:
            t = s.decode("latin-1")
        except Exception:
            return None
        return t if t.startswith(".?AV") else None


def verify_pe(exe_data):
    """用 pefile 复核节表，防止硬编码漂移。"""
    import pefile
    pe = pefile.PE(data=exe_data, fast_load=True)
    rows = []
    for s in pe.sections:
        n = s.Name.rstrip(b"\x00").decode("latin-1")
        rows.append((n, IMAGE_BASE + s.VirtualAddress,
                     s.PointerToRawData, s.SizeOfRawData, s.Misc_VirtualSize))
    base = pe.OPTIONAL_HEADER.ImageBase
    pe.close()
    return base, rows


# ---------------------------------------------------------------- 文本装载

def load_text(exe_data):
    return exe_data[TEXT_RAW:TEXT_RAW + TEXT_SIZE]


# ---------------------------------------------------------------- c7 05 扫描

def scan_c705(text, va_base=TEXT_VA):
    """纯字节扫 c7 05，不判边界。返回 [(site_va, target, imm)]。

    c7 /0 id  =>  c7 05 <disp32> <imm32>  共 10 字节。
    要求 modrm 恰为 0x05（mod=00, reg=000(/0), rm=101 => disp32 绝对地址）。
    尾部不足 10 字节的残片不计（无法构成完整指令）。
    """
    out = []
    n = len(text)
    i = 0
    while True:
        j = text.find(b"\xc7\x05", i)
        if j < 0:
            break
        if j + 10 <= n:
            tgt = struct.unpack_from("<I", text, j + 2)[0]
            imm = struct.unpack_from("<I", text, j + 6)[0]
            out.append((va_base + j, tgt, imm))
        i = j + 1
    return out


def in_bss(va):
    return BSS_LO <= va < BSS_HI


def bss_writes(hits):
    return [h for h in hits if in_bss(h[1])]


# ---------------------------------------------------------------- 指令边界

def build_boundary_bitmap(text, va_base=TEXT_VA, skipdata=True):
    """全段一次 disasm_lite 扫完，返回 (bitmap, n_insn, n_byte, last_end)。

    bitmap[idx] == 1  <=>  va_base+idx 是一条**真实指令**的起始地址。
    .byte 伪指令不计入边界（skipdata 生成的 .byte 只占位、不置 1，
    但它占用长度，所以后续真实指令地址仍正确）。
    """
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = bool(skipdata)
    bm = bytearray(len(text))
    n_insn = 0
    n_byte = 0
    last_end = va_base
    for addr, size, mnem, _ops in md.disasm_lite(text, va_base):
        n_insn += 1
        off = addr - va_base
        if mnem == ".byte":
            n_byte += 1
        else:
            if 0 <= off < len(bm):
                bm[off] = 1
        last_end = addr + size
    del md
    return bm, n_insn, n_byte, last_end


def boundary_set_from_bitmap(bm, va_base=TEXT_VA):
    """调试/小规模用：把位图转 set。全段 1.39M 条时不建议调用。"""
    return {va_base + i for i, v in enumerate(bm) if v}


def filter_by_boundary(hits, bm, va_base=TEXT_VA):
    out = []
    for site, tgt, imm in hits:
        off = site - va_base
        if 0 <= off < len(bm) and bm[off]:
            out.append((site, tgt, imm))
    return out


# ---------------------------------------------------------------- 35 容器

def scan_call_rel32(text, va_base=TEXT_VA):
    """扫全段 call rel32（E8 cd），产出 (site, target)。"""
    out = []
    n = len(text)
    i = 0
    while True:
        j = text.find(b"\xe8", i)
        if j < 0:
            break
        if j + 5 <= n:
            rel = struct.unpack_from("<i", text, j + 1)[0]
            tgt = va_base + j + 5 + rel
            out.append((va_base + j, tgt))
        i = j + 1
    return out


def derive_35_containers(text, va_base=TEXT_VA):
    """自己重算 35 个容器地址，不复制任何既有清单。

    返回 dict：sites_in_range / excluded_present / kept / shape_ok / bad_shape / edx
    """
    calls = scan_call_rel32(text, va_base)
    in_range = [(s, t) for (s, t) in calls if CALL_LO <= t <= CALL_HI]
    excluded_present = [(s, t) for (s, t) in in_range if s in CALL_EXCLUDE]
    kept = [(s, t) for (s, t) in in_range if s not in CALL_EXCLUDE]
    edx = []
    bad = []
    for site, _t in kept:
        off = site - va_base - 7
        if off < 0:
            bad.append((site, None))
            continue
        pre = text[off:off + 7]
        if len(pre) == 7 and pre[0] == 0xBA and pre[5:7] == b"\x8b\xce":
            edx.append(struct.unpack_from("<I", pre, 1)[0])
        else:
            bad.append((site, pre.hex()))
    return {
        "calls_in_range": in_range,
        "excluded_present": excluded_present,
        "kept": kept,
        "shape_bad": bad,
        "edx": edx,
    }


# ---------------------------------------------------------------- 类名族

DVC_PREFIX = ".?AV?$DynamicVectorClass@"
VC_PREFIX = ".?AV?$VectorClass@"
VCURSOR_PREFIX = ".?AV?$VectorCursor@"


def family_of(name):
    """返回 'dvc' / 'vc' / 'vcursor' / None。"""
    if name is None:
        return None
    if name.startswith(DVC_PREFIX):
        return "dvc"
    if name.startswith(VC_PREFIX):
        return "vc"
    if name.startswith(VCURSOR_PREFIX):
        return "vcursor"
    return None


def elem_tail(name):
    """元素类型键：剥掉族前缀后剩下的 mangled 尾串。

    同一元素类型在 DynamicVectorClass 与 VectorClass 两个族里，
    前缀之后的尾串完全一致（实测 35/35 对齐），故直接比较尾串即可判定
    「元素类型相同」。返回 None 表示不是 VectorClass 族。
    """
    fam = family_of(name)
    if fam == "dvc":
        return name[len(DVC_PREFIX):]
    if fam == "vc":
        return name[len(VC_PREFIX):]
    return None


def has_vectorclass_substring(name):
    return name is not None and "VectorClass" in name


# ---------------------------------------------------------------- 写表

def build_write_table(sites, img):
    """sites: [(site, target, imm)] -> {target: [(site, imm, name), ...]}
    只对 BSS 目标建表；name 由 RTTI 独立反解。
    """
    tbl = {}
    for site, tgt, imm in sites:
        if not in_bss(tgt):
            continue
        tbl.setdefault(tgt, []).append((site, imm, img.rtti_name(imm)))
    for k in tbl:
        tbl[k].sort()
    return tbl


def dual_form_report(tbl, objs35, strict):
    """按严格/宽松两种定义挑出双形态对象。

    strict: 该对象全部写入恰 2 次，其中恰 1 个 DynamicVectorClass 名 +
            恰 1 个 VectorClass 名，且元素类型相同。
    loose : 该对象全部写入中至少 1 个 DynamicVectorClass 名 +
            至少 1 个 VectorClass 名，且元素类型相同。
    「元素类型相同」判定：该对象所有 VectorClass 族名字的 elem_tail 去重后恰 1 个。
    """
    res = {}
    for tgt, writes in tbl.items():
        dvc = [w for w in writes if family_of(w[2]) == "dvc"]
        vc = [w for w in writes if family_of(w[2]) == "vc"]
        tails = {elem_tail(w[2]) for w in writes
                 if family_of(w[2]) in ("dvc", "vc")}
        tails.discard(None)
        same_elem = (len(tails) == 1)
        if strict:
            ok = (len(writes) == 2 and len(dvc) == 1 and len(vc) == 1
                  and same_elem)
        else:
            ok = (len(dvc) >= 1 and len(vc) >= 1 and same_elem)
        if ok:
            res[tgt] = {
                "writes": len(writes),
                "n_dvc": len(dvc),
                "n_vc": len(vc),
                "elem": (sorted(tails)[0] if tails else None),
                "names": [w[2] for w in writes],
                "sites": [w[0] for w in writes],
            }
    return res


# ---------------------------------------------------------------- 自测

class Checks(object):
    def __init__(self):
        self.rows = []

    def check(self, name, cond, detail=""):
        cond = bool(cond)
        self.rows.append((name, cond, detail))
        print("[%s] %-46s %s" % ("PASS" if cond else "FAIL", name, detail))
        return cond

    def all_pass(self):
        return all(c for _n, c, _d in self.rows)

    def summary(self):
        n = len(self.rows)
        p = sum(1 for _n, c, _d in self.rows if c)
        print("\n自测汇总: %d/%d PASS  => %s" % (p, n, "PASS" if p == n else "FAIL"))
        return {"total": n, "passed": p, "verdict": "PASS" if p == n else "FAIL"}
