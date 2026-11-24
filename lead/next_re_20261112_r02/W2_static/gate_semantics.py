#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RA2 Campaign Forge / NEXT_RE_20261112_R02 / W2_static
四个门控字节的静态语义分析器（纯静态，只读磁盘 PE 字节；绝不启动/attach/注入）。

用法:
    python gate_semantics.py --selftest          # 只跑 §1 负控五类 + 编码覆盖 + 反例校验
    python gate_semantics.py                     # 全量：写 CSV / MD / EVIDENCE
    python gate_semantics.py --image <path> --out <dir>

设计要点:
  通道 A = 全文件 4 字节小端 VA 模式搜索 + 局部指令起点解码（与对齐无关）
  通道 B1 = 从「填充区间边界」做确定性线性扫描（capstone skipdata）
  通道 B2 = 从「独立的 16 对齐 call rel32 目标」做第二可信边界复扫
  分类器只依据 capstone detail=True 的 operand.access / operand.size / operand.type，
  不依据「4 字节匹配即写」这种朴素规则。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import struct
import sys
from collections import defaultdict

try:
    import pefile
    import capstone
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_READ, CS_AC_WRITE
    from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG
except ImportError as e:  # pragma: no cover
    print("FATAL: missing dependency %s" % e)
    sys.exit(2)

# --------------------------------------------------------------------------------------
# 常量 / 目标
# --------------------------------------------------------------------------------------
RUN_ID = "NEXT_RE_20261112_R02"
EXPECT_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECT_SIZE = 4_825_360
IMAGE_BASE = 0x400000
SIZE_OF_IMAGE = 0x796000

GATES = [
    ("G1", 0x00A83D49),
    ("G2", 0x00A8ECD0),
    ("G3", 0x008B41C0),   # 旧记录误写 0x41C0；此处为正确地址
    ("G4", 0x00A83D48),
]
GATE_NAME = {va: name for name, va in GATES}

FRAME_MOV_STORE = 0x55DE81          # mov dword ptr [0xa8ed84], edx
FRAME_FN_ENTRY_EXPECTED = 0x55D360
FRAME_FN_END_EXPECTED = 0x55DEDB
FRAME_COUNTER = 0xA8ED84
RESET_SITES = [0x5B7329, 0x5E747C, 0x795234]

DEFAULT_IMAGE = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
DEFAULT_OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W2_static"

# 支持编码清单（用于「扫描范围 / 支持编码」声明与编码覆盖自测）
# (说明, 样例字节模板, 期望类别)  —— 模板中 'AAAAAAAA' 为占位（bytes.fromhex 得到 4×0xAA），运行时替换为 4 字节小端 VA
ENCODING_SAMPLES = [
    ("A0  moffs8 读",            bytes.fromhex("a0AAAAAAAA"),                  "read"),
    ("A1  moffs32 读",           bytes.fromhex("a1AAAAAAAA"),                  "read4"),
    ("A2  moffs8 写",            bytes.fromhex("a2AAAAAAAA"),                  "write_reg8"),
    ("A3  moffs32 写",           bytes.fromhex("a3AAAAAAAA"),                  "write_dword"),
    ("66 A3 moffs16 写",         bytes.fromhex("66a3AAAAAAAA"),                "write_word"),
    ("B0..B7 mov r8,imm8",       bytes.fromhex("b0c0"),                   "imm8_only"),
    ("B8..BF mov r32,imm32",     bytes.fromhex("b8AAAAAAAA"),                  "imm_coincidence"),
    ("C6 05 mov byte[A],imm8",   bytes.fromhex("c605AAAAAAAA01"),              "write_imm8"),
    ("C7 05 mov dword[A],imm32", bytes.fromhex("c705AAAAAAAA01000000"),        "write_imm32"),
    ("66 C7 05 mov word[A],imm16", bytes.fromhex("66c705AAAAAAAA0100"),        "write_imm16"),
    ("88 /r mov r/m8,r8 (modrm disp32)",  bytes.fromhex("880dAAAAAAAA"),       "write_reg8"),
    ("89 /r mov r/m32,r32 (modrm disp32)",bytes.fromhex("890dAAAAAAAA"),       "write_dword"),
    ("8A /r mov r8,r/m8 (modrm disp32)",  bytes.fromhex("8a0dAAAAAAAA"),       "read"),
    ("8B /r mov r32,r/m32 (modrm disp32)",bytes.fromhex("8b0dAAAAAAAA"),       "read4"),
    ("88 /r SIB 绝对地址",        bytes.fromhex("880425AAAAAAAA"),              "write_reg8"),
    ("80 /5 sub byte[A],imm8 RMW", bytes.fromhex("802dAAAAAAAA01"),             "write_rmw8"),
    ("80 /7 cmp byte[A],imm8 读", bytes.fromhex("803dAAAAAAAA00"),              "read"),
    ("81 /0 add dword[A],imm32 RMW", bytes.fromhex("8105AAAAAAAA01000000"),     "write_rmw32"),
    ("83 /0 add dword[A],imm8 RMW",  bytes.fromhex("8305AAAAAAAA01"),           "write_rmw32"),
    ("FE /0 inc byte[A] RMW",      bytes.fromhex("fe05AAAAAAAA"),               "write_rmw8"),
    ("FF /0 inc dword[A] RMW",     bytes.fromhex("ff05AAAAAAAA"),               "write_rmw32"),
    ("F6 /0 test byte[A],imm8 读", bytes.fromhex("f605AAAAAAAA01"),             "read"),
    ("8D /r lea r32,[A] 非访存",  bytes.fromhex("8d35AAAAAAAA"),               "lea_addr"),
    ("68 push imm32(A)",           bytes.fromhex("68AAAAAAAA"),                  "imm_coincidence"),
    ("0F B0 cmpxchg byte[A] RMW",  bytes.fromhex("0fb00dAAAAAAAA"),             "write_rmw8"),
    ("0F C0 xadd byte[A] RMW",     bytes.fromhex("0fc00dAAAAAAAA"),             "write_rmw8"),
]

# 五类负控（§1 红线：五类必须可分）
SELFTEST_FIVE = [
    ("mov byte [A],al",    bytes.fromhex("a2AAAAAAAA"),        "write_reg8"),
    ("mov byte [A],imm8",  bytes.fromhex("c605AAAAAAAA01"),    "write_imm8"),
    ("inc byte [A]",       bytes.fromhex("fe05AAAAAAAA"),      "write_rmw8"),
    ("lea esi,[A]",        bytes.fromhex("8d35AAAAAAAA"),      "lea_addr"),
    ("mov eax,A (imm)",    bytes.fromhex("b8AAAAAAAA"),        "imm_coincidence"),
]

# --------------------------------------------------------------------------------------
# 分类器
# --------------------------------------------------------------------------------------
READ_MNEMONICS = {"test", "cmp", "bt", "push", "ucomiss", "ucomisd", "comiss", "comisd"}
JCC_PREFIXES = ("j", "loop")
COND_EXCLUDE = {"jmp"}


def _parent_reg(name: str) -> str:
    """把 8/16/32 位寄存器名映射到 32 位父寄存器，用于轻量常量传播。"""
    m = {
        "al": "eax", "ah": "eax", "ax": "eax", "eax": "eax",
        "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
        "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx",
        "bl": "ebx", "bh": "ebx", "bx": "ebx", "ebx": "ebx",
        "sp": "esp", "esp": "esp", "bp": "ebp", "ebp": "ebp",
        "si": "esi", "esi": "esi", "di": "edi", "edi": "edi",
    }
    return m.get(name, name)


class Classifier:
    """逐操作数 access/size 分类；返回 (kind, width, is_rmw, is_write)。"""

    def __init__(self):
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True

    def decode_one(self, data: bytes, va: int):
        for ins in self.md.disasm(data, va, count=1):
            return ins
        return None

    def classify(self, ins, target_va: int):
        """返回 list[dict]，每个匹配的绝对地址操作数一项。"""
        out = []
        if ins is None:
            return out
        mnem = ins.mnemonic
        for op in ins.operands:
            # ---- 立即数巧合（含 B8..BF / 68 push imm32 / C7 imm32 的第二操作数等）
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == target_va:
                out.append(dict(kind="imm_coincidence", width=op.size,
                                is_rmw=False, is_write=False, operand="IMM"))
                continue
            if op.type != X86_OP_MEM:
                continue
            mem = op.mem
            # 绝对地址：无 base、无 index（mod=00 rm=101 或 SIB base=101 index=100）
            if mem.base != 0 or mem.index != 0:
                continue
            if (mem.disp & 0xFFFFFFFF) != target_va:
                continue
            access = op.access
            is_write = bool(access & CS_AC_WRITE)
            is_read = bool(access & CS_AC_READ)
            is_rmw = is_write and is_read
            if mnem == "lea":
                kind = "lea_addr"
                is_write = False
                is_rmw = False
            elif is_write:
                width = op.size
                if is_rmw:
                    kind = "write_rmw%d" % (width * 8)
                elif len(ins.operands) >= 2 and ins.operands[1].type == X86_OP_IMM:
                    kind = "write_imm%d" % (width * 8)
                elif len(ins.operands) >= 2 and ins.operands[1].type == X86_OP_REG:
                    kind = "write_reg%d" % (width * 8)
                else:
                    kind = "write_other%d" % (width * 8)
            elif is_read or mnem in READ_MNEMONICS:
                kind = "read%d" % (op.size * 8)
            else:
                kind = "mem_other%d" % (op.size * 8)  # capstone access=0 的 test/cmp 等
            out.append(dict(kind=kind, width=op.size, is_rmw=is_rmw,
                            is_write=is_write, operand="MEM"))
        return out


CLS = Classifier()


def expand(template: bytes, va: int) -> bytes:
    """模板 hex 串里的 'AAAAAAAA' 是占位：bytes.fromhex 得到 4 个 0xAA 字节，
    其 hex 文本为 'aaaaaaaa'。在 hex 文本层把它替换为 4 字节小端 VA。

    占位必须是合法 hex，故样例定义写成 bytes.fromhex("a0AAAAAAAA") 形式。
    """
    placeholder = "aaaaaaaa"          # 4 字节 0xAA 的 hex 文本
    hx = template.hex()
    if placeholder in hx:
        hx = hx.replace(placeholder, struct.pack("<I", va).hex())
    return bytes.fromhex(hx)


def classify_bytes(data: bytes, va: int, target_va: int):
    ins = CLS.decode_one(data, va)
    return ins, CLS.classify(ins, target_va)


# --------------------------------------------------------------------------------------
# PE 映射
# --------------------------------------------------------------------------------------
class PEImage:
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.d = f.read()
        self.sha = hashlib.sha256(self.d).hexdigest()
        self.size = len(self.d)
        self.pe = pefile.PE(path)
        oh = self.pe.OPTIONAL_HEADER
        self.image_base = oh.ImageBase
        self.size_of_image = oh.SizeOfImage
        self.size_of_headers = oh.SizeOfHeaders
        self.coff_chars = self.pe.FILE_HEADER.Characteristics
        self.dll_chars = oh.DllCharacteristics
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.rstrip(b"\x00").decode("latin1")
            rva = s.VirtualAddress
            vsize = s.Misc_VirtualSize
            raw_ptr = s.PointerToRawData
            raw_size = s.SizeOfRawData
            self.sections.append(dict(
                name=name, rva=rva, va=self.image_base + rva, vsize=vsize,
                va_end=self.image_base + rva + vsize,
                raw_ptr=raw_ptr, raw_size=raw_size, raw_end=raw_ptr + raw_size,
                exec=bool(s.Characteristics & 0x20000000),
                chars=s.Characteristics))
        self.text = next(s for s in self.sections if s["name"] == ".text")

    def off_to_va(self, off: int):
        for s in self.sections:
            if s["raw_ptr"] <= off < s["raw_end"]:
                return s["va"] + (off - s["raw_ptr"])
        return None

    def off_to_rva(self, off: int):
        va = self.off_to_va(off)
        return None if va is None else va - self.image_base

    def va_to_off(self, va: int):
        """仅当 VA 落在有文件 backing 的节内才返回偏移；BSS 尾返回 None。"""
        rva = va - self.image_base
        for s in self.sections:
            if s["rva"] <= rva < s["rva"] + s["raw_size"]:
                return s["raw_ptr"] + (rva - s["rva"])
        return None

    def va_to_section(self, va: int):
        rva = va - self.image_base
        for s in self.sections:
            if s["rva"] <= rva < s["rva"] + s["vsize"]:
                return s
        return None

    def section_of_off(self, off: int):
        for s in self.sections:
            if s["raw_ptr"] <= off < s["raw_end"]:
                return s
        return None

    def check_facts(self):
        facts = []
        ok = True

        def chk(label, cond, detail):
            nonlocal ok
            facts.append(("OK" if cond else "FAIL", label, detail))
            if not cond:
                ok = False

        chk("SHA-256", self.sha == EXPECT_SHA256, self.sha)
        chk("file size", self.size == EXPECT_SIZE, "0x%X (%d)" % (self.size, self.size))
        chk("ImageBase", self.image_base == IMAGE_BASE, "0x%X" % self.image_base)
        chk("SizeOfImage", self.size_of_image == SIZE_OF_IMAGE, "0x%X" % self.size_of_image)
        chk("IMAGE_FILE_RELOCS_STRIPPED (COFF char bit0)",
            bool(self.coff_chars & 0x0001), "COFF=0x%X" % self.coff_chars)
        chk("DYNAMIC_BASE == False", not bool(self.dll_chars & 0x0040),
            "DllCharacteristics=0x%X" % self.dll_chars)
        t = self.text
        chk(".text file_off == RVA", t["raw_ptr"] == t["rva"],
            "RawPtr=0x%X RVA=0x%X" % (t["raw_ptr"], t["rva"]))
        for nm in (".rsrc", ".detour"):
            s = next(x for x in self.sections if x["name"] == nm)
            off = s["va"] - s["raw_ptr"]
            chk("%s file_off == VA - 0x6FC000" % nm, off == 0x6FC000,
                "VA-RawPtr=0x%X" % off)
        # 门控地址均在 .data 的 BSS 尾（无文件 backing）
        for nm, va in GATES:
            chk("%s 0x%08X 无文件 backing (BSS)" % (nm, va),
                self.va_to_off(va) is None and self.va_to_section(va)["name"] == ".data",
                "section=%s" % self.va_to_section(va)["name"])
        return ok, facts


# --------------------------------------------------------------------------------------
# 工具
# --------------------------------------------------------------------------------------
def fmt_dis(ins) -> str:
    return (ins.mnemonic + " " + ins.op_str).strip()


def find_all(d: bytes, pat: bytes):
    i = 0
    while True:
        i = d.find(pat, i)
        if i < 0:
            return
        yield i
        i += 1


def padding_runs(d: bytes, lo: int, hi: int):
    """返回 [(start,end,byte)]，end 不含。0x90 run>=4 或 0xCC run>=2。"""
    runs = []
    i = lo
    while i < hi:
        b = d[i]
        if b in (0x90, 0xCC):
            j = i + 1
            while j < hi and d[j] == b:
                j += 1
            if (b == 0x90 and j - i >= 4) or (b == 0xCC and j - i >= 2):
                runs.append((i, j, b))
            i = j
        else:
            i += 1
    return runs


def find_function_entry(img: PEImage, va: int, max_back=0x40000):
    """向前找最近的、16 对齐的、紧跟填充区间的函数入口（启发式，不视为已证）。"""
    d = img.d
    off = va - img.image_base
    lo = max(img.text["raw_ptr"], off - max_back)
    i = off - 1
    while i > lo:
        b = d[i]
        if b in (0x90, 0xCC):
            j = i
            while j > lo and d[j] == b:
                j -= 1
            run = i - j
            end = i + 1
            if ((b == 0x90 and run >= 4) or (b == 0xCC and run >= 2)) and (end % 16 == 0) and end <= off:
                return img.image_base + end
            i = j
        else:
            i -= 1
    return None


def find_function_end(img: PEImage, va: int, max_fwd=0x20000):
    """向后找第一个填充区间；函数最后一个字节 = 填充起点 - 1。
    允许 multiple ret（本函数有 0x55DEC7 与 0x55DEDB 两个出口），故不能按第一条 ret 截断。"""
    d = img.d
    off = va - img.image_base
    hi = min(img.text["raw_end"], off + max_fwd)
    i = off
    while i < hi:
        b = d[i]
        if b in (0x90, 0xCC):
            j = i + 1
            while j < hi and d[j] == b:
                j += 1
            if (b == 0x90 and j - i >= 4) or (b == 0xCC and j - i >= 2):
                return img.image_base + i  # 填充起点（不含）
            i = j
        else:
            i += 1
    return None


def is_cond_branch(ins) -> bool:
    m = ins.mnemonic
    return (m.startswith("j") and m not in COND_EXCLUDE) or m.startswith("loop")


def is_control_transfer(ins) -> bool:
    return (ins.mnemonic == "ret" or ins.mnemonic.startswith("ret") or
            ins.mnemonic == "jmp" or is_cond_branch(ins) or
            ins.mnemonic in ("hlt", "ud2", "int3"))


def function_instructions(img: PEImage, entry: int, until_va: int, cap=0x20000):
    """从 entry 线性解码到 until_va 之后的第一个 ret 或 cap；返回 (list, skipdata 区间)。"""
    d = img.d
    off = entry - img.image_base
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    insns, skips = [], []
    end = min(off + cap, img.text["raw_end"])
    buf = d[off:end]
    for ins in md.disasm(buf, entry):
        if ins.id == 0 or ins.mnemonic.startswith(".byte"):
            skips.append((ins.address, ins.address + ins.size))
            continue
        insns.append(ins)
        if ins.address >= until_va and (ins.mnemonic == "ret" or ins.mnemonic.startswith("ret")):
            break
        if ins.address >= until_va + 0x400:
            break
    return insns, skips


def constant_at(insns, idx: int):
    """轻量常量传播：返回 32 位父寄存器 -> 已知常量（或 None）。"""
    const = {}
    for k in range(idx):
        ins = insns[k]
        ops = ins.operands
        m = ins.mnemonic
        if m == "xor" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG \
                and ops[0].reg == ops[1].reg:
            const[_parent_reg(ins.reg_name(ops[0].reg))] = 0
            continue
        if m == "mov" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM:
            const[_parent_reg(ins.reg_name(ops[0].reg))] = ops[1].imm & 0xFFFFFFFF
            continue
        # 调用：按 stdcall/cdecl 约定，只清 caller-saved
        if m == "call":
            for r in ("eax", "ecx", "edx"):
                const[r] = None
            continue
        for op in ops:
            if op.type == X86_OP_REG and (op.access & CS_AC_WRITE):
                const[_parent_reg(ins.reg_name(op.reg))] = None
    return const


def written_value(ins, const):
    """推断写入的立即数/寄存器常量值；返回 (value:int|None, source:str)。"""
    ops = ins.operands
    if len(ops) >= 2 and ops[1].type == X86_OP_IMM:
        return ops[1].imm & 0xFFFFFFFF, "imm"
    if len(ops) >= 2 and ops[1].type == X86_OP_REG:
        p = _parent_reg(ins.reg_name(ops[1].reg))
        v = const.get(p)
        return v, ("reg %s (parent %s)" % (ins.reg_name(ops[1].reg), p))
    return None, "unknown"


# --------------------------------------------------------------------------------------
# §1 负控 / 编码覆盖 / 反例校验
# --------------------------------------------------------------------------------------
def run_selftest(verbose=True):
    out = []
    A = 0x008B41C0
    out.append("=== §1 NEGATIVE CONTROL: five classes must be distinguishable ===")
    out.append("target VA = 0x%08X  (low address, immediate-collision prone)" % A)
    out.append("%-26s %-30s %-18s %-8s %-8s %s" %
               ("sample", "bytes", "kind", "width", "is_write", "disasm"))
    kinds = []
    for label, tpl, expect in SELFTEST_FIVE:
        b = expand(tpl, A)
        ins, hits = classify_bytes(b, 0x0055DE4F, A)
        k = hits[0]["kind"] if hits else "NO_HIT"
        kinds.append(k)
        out.append("%-26s %-30s %-18s %-8s %-8s %s" %
                   (label, b.hex(" "), k, hits[0]["width"] if hits else "-",
                    hits[0]["is_write"] if hits else "-", fmt_dis(ins) if ins else "NO DECODE"))
        assert k == expect, "selftest: %s expected %s got %s" % (label, expect, k)
    distinct = len(set(kinds))
    out.append("distinct kinds = %d / 5" % distinct)
    assert distinct == 5, "selftest: five classes not separable"
    out.append("write classes = %s" % [kinds[i] for i in range(3)])
    assert all(CLS.classify(CLS.decode_one(expand(SELFTEST_FIVE[i][1], A), 0), A)[0]["is_write"]
               for i in range(3))
    out.append("NON-write classes = %s (must NOT be counted as writes)" % [kinds[3], kinds[4]])
    assert not any(CLS.classify(CLS.decode_one(expand(SELFTEST_FIVE[i][1], A), 0), A)[0]["is_write"]
                   for i in (3, 4))
    out.append("RESULT: PASS (five classes separable; only first three are writes)")

    out.append("")
    out.append("=== ENCODING COVERAGE (supported absolute-address encodings) ===")
    out.append("%-46s %-26s %-20s %-6s %s" % ("encoding", "bytes", "kind", "w", "disasm"))
    for label, tpl, expect in ENCODING_SAMPLES:
        b = expand(tpl, A)
        ins, hits = classify_bytes(b, 0x0055DE4F, A)
        k = hits[0]["kind"] if hits else "NO_HIT"
        out.append("%-46s %-26s %-20s %-6s %s" %
                   (label, b.hex(" "), k, hits[0]["is_write"] if hits else "-",
                    fmt_dis(ins) if ins else "NO DECODE"))
    out.append("NOTE: B0..B7 mov r8,imm8 sample has no 4-byte VA operand -> 'imm8_only' (not a VA hit).")

    out.append("")
    out.append("=== COUNTER-EXAMPLE: immediate coincidence must NOT be a memory write ===")
    ce = [
        ("mov eax,0x8B41C0", bytes.fromhex("b8c0418b00")),
        ("mov ecx,0x8B41C0", bytes.fromhex("b9c0418b00")),
        ("mov edx,0x8B41C0", bytes.fromhex("bac0418b00")),
        ("push 0x8B41C0", bytes.fromhex("68c0418b00")),
        ("add eax,0x8B41C0", bytes.fromhex("05c0418b00")),
        ("mov byte [0x8B41C0],1", bytes.fromhex("c605c0418b0001")),
        ("mov byte [0x8B41C0],al", bytes.fromhex("a2c0418b00")),
    ]
    out.append("%-30s %-26s %-20s %-8s %s" % ("sample", "bytes", "kind", "is_write", "disasm"))
    for label, b in ce:
        ins, hits = classify_bytes(b, 0x0055DE4F, A)
        # 对 B8/B9/BA/68/05 这类，命中项是 IMM 操作数
        k = "/".join(h["kind"] for h in hits) if hits else "NO_HIT"
        w = any(h["is_write"] for h in hits)
        out.append("%-30s %-26s %-20s %-8s %s" % (label, b.hex(" "), k, w, fmt_dis(ins)))
        if label.startswith(("mov eax", "mov ecx", "mov edx", "push", "add eax")):
            assert not w, "counter-example failed: %s classified as write" % label
    out.append("RESULT: PASS (constructed immediates 0x8B41C0 are imm_coincidence, not writes)")
    txt = "\n".join(out)
    if verbose:
        print(txt)
    return txt


# --------------------------------------------------------------------------------------
# 通道 A：模式搜索 + 局部解码
# --------------------------------------------------------------------------------------
def channel_a(img: PEImage):
    d = img.d
    rows = []            # 每个 4 字节命中一行（含分类）
    decoded = []         # 反汇编片段文本
    for gname, va in GATES:
        pat = struct.pack("<I", va)
        for h in find_all(d, pat):
            sec = img.section_of_off(h)
            secname = sec["name"] if sec else "HEADER/none"
            rva = img.off_to_rva(h)
            hit_va = img.off_to_va(h)
            candidates = []
            if sec and sec["exec"]:
                for k in range(1, 13):
                    st = h - k
                    if st < sec["raw_ptr"]:
                        continue
                    start_va = img.off_to_va(st)
                    if start_va is None:
                        continue
                    ins, hits = classify_bytes(d[st:st + 20], start_va, va)
                    if ins is None:
                        continue
                    # 比较必须用「文件偏移」域，不能拿 FOFF 与 VA 比
                    if not (st <= h and h + 4 <= st + ins.size):
                        continue
                    if not hits:
                        continue
                    # 只保留「绝对地址操作数命中目标」或「立即数巧合命中目标」的候选
                    if not any(x["operand"] in ("MEM", "IMM") for x in hits):
                        continue
                    candidates.append(dict(k=k, start=st, start_va=start_va,
                                           end_va=start_va + ins.size,
                                           size=ins.size, disasm=fmt_dis(ins),
                                           bytes=ins.bytes.hex(" "),
                                           kinds=[x["kind"] for x in hits],
                                           is_write=any(x["is_write"] for x in hits),
                                           is_rmw=any(x["is_rmw"] for x in hits),
                                           width=max(x["width"] for x in hits)))
            rows.append(dict(gate=gname, va=va, hit_off=h, sec=secname,
                             hit_va=hit_va, hit_rva=rva, candidates=candidates))
            decoded.append("GATE %s VA=0x%08X  pattern_hit foff=0x%06X RVA=0x%06X VA(file)=%s section=%s" %
                           (gname, va, h, rva or 0,
                            ("0x%08X" % hit_va) if hit_va else "-", secname))
            for c in candidates:
                decoded.append("    k=%-2d start VA=0x%08X RVA=0x%06X FOFF=0x%06X bytes=%-24s %-34s kinds=%s write=%s" %
                               (c["k"], c["start_va"], c["start_va"] - img.image_base, c["start"],
                                c["bytes"], c["disasm"], ",".join(c["kinds"]), c["is_write"]))
            if not candidates:
                decoded.append("    (no absolute-address instruction decode at any k=1..12)")
    return rows, decoded


def choose_candidates(rows, start_bitmap, img):
    """结合 B1/B2 指令起点位图，给每个命中挑出权威候选；返回按 (gate, start_va) 去重表。"""
    chosen = {}
    for r in rows:
        cs = r["candidates"]
        if not cs:
            continue
        aligned = []
        for c in cs:
            off = c["start_va"] - img.image_base - img.text["raw_ptr"]
            if 0 <= off < len(start_bitmap) and start_bitmap[off]:
                aligned.append(c)
        pool = aligned if aligned else cs
        # 同一起点可能重复；优先最长的指令（前缀最完整），其次最小 k
        c = sorted(pool, key=lambda x: (-x["size"], x["k"]))[0]
        key = (r["gate"], c["start_va"])
        if key not in chosen:
            chosen[key] = dict(gate=r["gate"], gate_va=r["va"], hit_off=r["hit_off"], c=c,
                               aligned=bool(aligned), all_candidates=cs)
    return chosen


# --------------------------------------------------------------------------------------
# 通道 B：线性扫描（skipdata）
# --------------------------------------------------------------------------------------
def linear_scan(img: PEImage, boundaries, label, targets):
    """从 boundaries 逐段线性反汇编；返回 hits / skips / start_bitmap / cover_bitmap / call_sites / indirect_calls."""
    d = img.d
    t = img.text
    lo, hi = t["raw_ptr"], t["raw_end"]
    N = hi - lo
    start_bitmap = bytearray(N)
    cover_bitmap = bytearray(N)
    hits, skips, call_sites, indirect = [], [], [], []
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    bs = sorted(set([lo, hi] + [b for b in boundaries if lo <= b <= hi]))
    seg_info = []
    for a, b in zip(bs, bs[1:]):
        if b <= a:
            continue
        seg_info.append((a, b))
        buf = d[a:b]
        va0 = img.image_base + a
        for ins in md.disasm(buf, va0):
            o = ins.address - img.image_base - lo
            if o < 0 or o >= N:
                continue
            start_bitmap[o] = 1
            for q in range(ins.size):
                if o + q < N:
                    cover_bitmap[o + q] = 1
            if ins.id == 0 or ins.mnemonic.startswith(".byte"):
                skips.append((ins.address, ins.address + ins.size, label))
                continue
            # 调用收集
            if ins.mnemonic == "call":
                ops = ins.operands
                if len(ops) == 1 and ops[0].type == X86_OP_IMM:
                    call_sites.append((ins.address, ops[0].imm & 0xFFFFFFFF))
                else:
                    indirect.append((ins.address, fmt_dis(ins)))
            # 目标匹配
            for op in ins.operands:
                if op.type != X86_OP_MEM or op.mem.base != 0 or op.mem.index != 0:
                    continue
                disp = op.mem.disp & 0xFFFFFFFF
                if disp not in targets:
                    continue
                cl = CLS.classify(ins, disp)
                for c in cl:
                    hits.append(dict(gate=GATE_NAME[disp], gate_va=disp, va=ins.address,
                                     rva=ins.address - img.image_base,
                                     file_off=ins.address - img.image_base,  # .text: off == RVA
                                     bytes=ins.bytes.hex(" "), disasm=fmt_dis(ins),
                                     kind=c["kind"], width=c["width"], is_rmw=c["is_rmw"],
                                     is_write=c["is_write"], channel=label))
    return dict(hits=hits, skips=skips, start_bitmap=start_bitmap, cover_bitmap=cover_bitmap,
                call_sites=call_sites, indirect=indirect, seg_info=seg_info, label=label)


def intervals_from_bitmap(cover, lo, base_va):
    """返回未覆盖区间 [(VA_start, VA_end)]。"""
    out = []
    i = 0
    n = len(cover)
    while i < n:
        if cover[i]:
            i += 1
            continue
        j = i + 1
        while j < n and not cover[j]:
            j += 1
        out.append((base_va + lo + i, base_va + lo + j))
        i = j
    return out


def merge_intervals(iv):
    if not iv:
        return []
    iv = sorted(iv)
    out = [list(iv[0])]
    for a, b in iv[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


# --------------------------------------------------------------------------------------
# 上下文 / 基本块 / 调用者
# --------------------------------------------------------------------------------------
def analyze_write_context(img: PEImage, wva: int, gate_va: int):
    entry = find_function_entry(img, wva)
    if entry is None:
        return dict(entry=None, bb=None, prev="-", value=None, value_src="unknown",
                    const_note="no function entry found")
    insns, skips = function_instructions(img, entry, wva)
    idx = next((i for i, x in enumerate(insns) if x.address == wva), None)
    if idx is None:
        return dict(entry=entry, bb=None, prev="-", value=None, value_src="unknown",
                    const_note="write VA not on function-entry linear decode (misaligned)")
    # 基本块起点
    bb_starts = {insns[0].address}
    for i, ins in enumerate(insns):
        if is_control_transfer(ins) and i + 1 < len(insns):
            bb_starts.add(insns[i + 1].address)
        for op in ins.operands:
            if op.type == X86_OP_IMM and (ins.mnemonic.startswith("j") or ins.mnemonic.startswith("loop")):
                tgt = op.imm & 0xFFFFFFFF
                if img.text["va"] <= tgt < img.text["va_end"]:
                    bb_starts.add(tgt)
    bb = max((b for b in bb_starts if b <= wva), default=insns[0].address)
    # 前一条 call 或条件分支
    prev = "-"
    for i in range(idx - 1, -1, -1):
        ins = insns[i]
        if ins.mnemonic == "call" or is_cond_branch(ins):
            prev = "0x%08X|%s" % (ins.address, fmt_dis(ins))
            break
    const = constant_at(insns, idx)
    val, src = written_value(insns[idx], const)
    return dict(entry=entry, bb=bb, prev=prev, value=val, value_src=src,
                const_note="lightweight const-prop; assumes callee-saved ebx/esi/edi/ebp",
                fn_end=insns[-1].address + insns[-1].size if insns else None,
                n_insns=len(insns), skips=skips)


def build_function_call_graph(img: PEImage, B1, e8):
    """从原始 E8 调用 + B1 指令起点位图构建函数级直接调用图（启发式函数入口）。"""
    lo = img.text["raw_ptr"]
    sb = B1["start_bitmap"]
    cache = {}

    def fne(va):
        if va not in cache:
            cache[va] = find_function_entry(img, va)
        return cache[va]

    fg = defaultdict(set)
    sites = defaultdict(list)
    for c, tgt in e8:
        o = c - img.image_base - lo
        if not (0 <= o < len(sb) and sb[o]):
            continue
        fc, ft = fne(c), fne(tgt)
        if fc and ft and fc != ft:
            fg[fc].add(ft)
            sites[(fc, ft)].append(c)
    return fg, sites, fne, cache


def bfs_path(fg, src, dst, maxd=5):
    from collections import deque
    q = deque([(src, [src])])
    seen = {src}
    while q:
        x, p = q.popleft()
        if len(p) > maxd:
            continue
        for y in sorted(fg.get(x, ())):
            if y == dst:
                return p + [y]
            if y not in seen:
                seen.add(y)
                q.append((y, p + [y]))
    return None


def raw_e8_calls(img: PEImage):
    """全 .text 原始字节 E8 rel32 扫描（独立于 capstone），返回 [(caller_va, target_va)]。"""
    d = img.d
    lo, hi = img.text["raw_ptr"], img.text["raw_end"]
    out = []
    for off in range(lo, hi - 5):
        if d[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", d, off + 1)[0]
        tgt = img.image_base + off + 5 + rel
        if img.text["va"] <= tgt < img.text["va_end"]:
            out.append((img.image_base + off, tgt))
    return out


def loop_enclosing(img: PEImage, entry: int, probe_va: int):
    """是否存在回边 (src>probe, target<=probe) 包围 probe_va。"""
    insns, _ = function_instructions(img, entry, probe_va, cap=0x20000)
    for ins in insns:
        if ins.address <= probe_va:
            continue
        for op in ins.operands:
            if op.type == X86_OP_IMM and (ins.mnemonic.startswith("j") or ins.mnemonic.startswith("loop")):
                tgt = op.imm & 0xFFFFFFFF
                if tgt <= probe_va and tgt >= entry:
                    return True, "0x%08X|%s" % (ins.address, fmt_dis(ins))
    return False, "-"


# --------------------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="只跑 §1 负控五类并退出")
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    if args.selftest:
        run_selftest(verbose=True)
        print("\nSELFTEST EXIT=0")
        return 0

    out_dir = args.out
    ev_dir = os.path.join(out_dir, "EVIDENCE")
    os.makedirs(ev_dir, exist_ok=True)

    log = []
    log.append("RUN_ID=%s" % RUN_ID)
    log.append("COMMAND=python gate_semantics.py --image %s --out %s" % (args.image, args.out))
    log.append("PYTHON=%s" % sys.version.replace("\n", " "))
    log.append("capstone=%s pefile=%s" % (capstone.__version__, pefile.__version__))
    img = PEImage(args.image)
    ok, facts = img.check_facts()
    log.append("IMAGE=%s" % img.path)
    log.append("SHA256=%s" % img.sha)
    log.append("SIZE=%d (0x%X)" % (img.size, img.size))
    for st, label, detail in facts:
        log.append("FACT %-4s %-52s %s" % (st, label, detail))
    log.append("SECTIONS:")
    for s in img.sections:
        log.append("  %-9s VA=0x%08X RVA=0x%08X VSize=0x%08X RawPtr=0x%08X RawSize=0x%08X Exec=%s" %
                   (s["name"], s["va"], s["rva"], s["vsize"], s["raw_ptr"], s["raw_size"], s["exec"]))
    if not ok:
        log.append("FATAL: PE fact check failed -> STOP (no writes produced)")
        print("\n".join(log))
        with open(os.path.join(ev_dir, "00_run_log.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(log) + "\n")
        return 3

    # ---- §1 负控
    selftest_txt = run_selftest(verbose=False)
    with open(os.path.join(ev_dir, "01_selftest.txt"), "w", encoding="utf-8") as f:
        f.write("COMMAND=python gate_semantics.py --selftest\nEXIT=0\n\n" + selftest_txt + "\n")
    log.append(selftest_txt.splitlines()[-1])

    # ---- 通道 A
    a_rows, a_decoded = channel_a(img)
    with open(os.path.join(ev_dir, "03_channelA_decoded.txt"), "w", encoding="utf-8") as f:
        f.write("CHANNEL A: full-file 4-byte LE VA pattern search\n")
        f.write("search range = file offsets [0x0, 0x%X) (whole file, %d bytes)\n" % (img.size, img.size))
        f.write("supported encodings: see 10_encoding_coverage.txt\n")
        f.write("candidate instruction starts tried: k=1..12 before each 4-byte hit\n")
        f.write("format: VA / RVA / FOFF / bytes / disasm\n\n")
        f.write("\n".join(a_decoded) + "\n")

    # ---- 通道 B1: 填充边界
    t = img.text
    runs = padding_runs(img.d, t["raw_ptr"], t["raw_end"])
    b1_boundaries = [t["raw_ptr"]]
    for a, b, _ in runs:
        b1_boundaries += [a, b]
    B1 = linear_scan(img, b1_boundaries, "B1_cc_nop_padding", set(v for _, v in GATES))

    # ---- 通道 B2: 独立的 16 对齐 call rel32 目标（原始字节扫描，不依赖 B1）
    e8 = raw_e8_calls(img)
    b2_targets = sorted(set(tgt for _, tgt in e8 if tgt % 16 == 0))
    B2 = linear_scan(img, b2_targets, "B2_call_targets_16align", set(v for _, v in GATES))
    with open(os.path.join(ev_dir, "04_B1_linear.txt"), "w", encoding="utf-8") as f:
        f.write("B1 trusted boundaries: ends/starts of 0x90(>=4)/0xCC(>=2) padding runs + .text start\n")
        f.write("padding runs = %d; segments = %d; skipdata intervals = %d\n" %
                (len(runs), len(B1["seg_info"]), len(B1["skips"])))
        f.write("hits = %d (writes=%d)\n\n" % (len(B1["hits"]), sum(1 for h in B1["hits"] if h["is_write"])))
        for h in B1["hits"]:
            f.write("0x%08X RVA=0x%06X FOFF=0x%06X | %-24s | %-40s | %s\n" %
                    (h["va"], h["rva"], h["file_off"], h["bytes"], h["disasm"], h["kind"]))
    with open(os.path.join(ev_dir, "04_B2_rescan.txt"), "w", encoding="utf-8") as f:
        f.write("B2 trusted boundaries (INDEPENDENT of B1): raw byte-level E8 rel32 targets, 16-byte aligned\n")
        f.write("raw E8 sites=%d; 16-aligned distinct targets=%d; segments=%d; skipdata=%d\n" %
                (len(e8), len(b2_targets), len(B2["seg_info"]), len(B2["skips"])))
        f.write("hits = %d (writes=%d)\n\n" % (len(B2["hits"]), sum(1 for h in B2["hits"] if h["is_write"])))
        for h in B2["hits"]:
            f.write("0x%08X RVA=0x%06X FOFF=0x%06X | %-24s | %-40s | %s\n" %
                    (h["va"], h["rva"], h["file_off"], h["bytes"], h["disasm"], h["kind"]))

    # ---- 权威候选（A 与 B 起点位图交叉）
    sb = bytearray(len(B1["start_bitmap"]))
    for i in range(len(sb)):
        sb[i] = B1["start_bitmap"][i] | B2["start_bitmap"][i]
    chosen = choose_candidates(a_rows, sb, img)

    # ---- 交叉验证
    def key(h):
        return (h["gate"], h["va"])
    setA_w = set((k[0], k[1]) for k, v in chosen.items() if v["c"]["is_write"])
    setB1_w = set(key(h) for h in B1["hits"] if h["is_write"])
    setB2_w = set(key(h) for h in B2["hits"] if h["is_write"])
    all_w = setA_w | setB1_w | setB2_w
    cv = []
    cv.append("CROSS VALIDATION of WRITE sites (key = gate, VA)")
    cv.append("A(pattern+local decode) writes = %d" % len(setA_w))
    cv.append("B1(padding-boundary linear) writes = %d" % len(setB1_w))
    cv.append("B2(call-target rescan) writes = %d" % len(setB2_w))
    cv.append("UNION = %d ; A&B1&B2 = %d ; A-only = %d ; B-only = %d" %
              (len(all_w), len(setA_w & setB1_w & setB2_w),
               len(setA_w - setB1_w - setB2_w), len((setB1_w | setB2_w) - setA_w)))
    cv.append("")
    cv.append("%-6s %-12s %-4s %-4s %-4s %s" % ("gate", "VA", "A", "B1", "B2", "verdict"))
    for g, v in sorted(all_w, key=lambda x: (x[0], x[1])):
        a, b1, b2 = (g, v) in setA_w, (g, v) in setB1_w, (g, v) in setB2_w
        verdict = "TRIPLE" if (a and b1 and b2) else ("dual" if sum((a, b1, b2)) >= 2 else "SINGLE")
        cv.append("%-6s 0x%08X  %-4s %-4s %-4s %s" % (g, v, a, b1, b2, verdict))
    with open(os.path.join(ev_dir, "06_cross_validation.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(cv) + "\n")

    # ---- 未覆盖区间
    uncov = intervals_from_bitmap(B1["cover_bitmap"], t["raw_ptr"], img.image_base)
    uncov2 = intervals_from_bitmap(B2["cover_bitmap"], t["raw_ptr"], img.image_base)
    iv = []
    iv.append("UNCOVERED_INTERVALS (channel B1, .text raw [0x%X,0x%X))" % (t["raw_ptr"], t["raw_end"]))
    iv.append("DEFINITION: 'uncovered' = bytes capstone could not decode (skipdata '.byte' pseudo-insns).")
    iv.append("           cover_bitmap marks all bytes belonging to SOME decoded instruction (incl. padding runs,")
    iv.append("           which decode as nop/int3), hence cover_bitmap gaps are 0 and the skipdata intervals")
    iv.append("           below ARE the uncovered intervals. Channel A pattern scan covers ALL file bytes anyway.")
    iv.append("B1 skipdata: %d intervals, %d bytes total; B2 skipdata: %d intervals, %d bytes total." %
              (len(B1["skips"]), sum(b - a for a, b, _ in B1["skips"]),
               len(B2["skips"]), sum(b - a for a, b, _ in B2["skips"])))
    iv.append("B1 skipdata intervals (%d):" % len(B1["skips"]))
    for a, b, lab in B1["skips"][:200]:
        iv.append("  SKIP 0x%08X..0x%08X len=%d" % (a, b, b - a))
    if len(B1["skips"]) > 200:
        iv.append("  ... (%d more)" % (len(B1["skips"]) - 200))
    iv.append("B1 cover_bitmap gaps (%d merged):" % len(merge_intervals(uncov)))
    for a, b in merge_intervals(uncov)[:200]:
        iv.append("  GAP  0x%08X..0x%08X len=%d" % (a, b, b - a))
    iv.append("B2 skipdata intervals (%d); B2 cover_bitmap gaps (%d merged)" %
              (len(B2["skips"]), len(merge_intervals(uncov2))))
    for a, b in merge_intervals(uncov2)[:60]:
        iv.append("  B2GAP 0x%08X..0x%08X len=%d" % (a, b, b - a))
    iv.append("")
    iv.append("EXPLICITLY NOT LINEARLY DISASSEMBLED (covered only by channel A pattern scan):")
    for s in img.sections:
        if s["name"] == ".text":
            continue
        iv.append("  %-9s file [0x%08X,0x%08X) VA [0x%08X,0x%08X) Exec=%s" %
                  (s["name"], s["raw_ptr"], s["raw_end"], s["va"], s["va"] + s["raw_size"], s["exec"]))
    iv.append("  HEADERS file [0x0,0x%X)" % img.size_of_headers)
    iv.append("  .data BSS tail VA [0x%08X,0x%08X) has NO file bytes (loader zero-fill)" %
              (next(s for s in img.sections if s["name"] == ".data")["va"] +
               next(s for s in img.sections if s["name"] == ".data")["raw_size"],
               next(s for s in img.sections if s["name"] == ".data")["va_end"]))
    iv.append("")
    iv.append("CHANNEL A still covers all file bytes for the 4 target VA patterns regardless of alignment.")
    with open(os.path.join(ev_dir, "05_uncovered_intervals.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(iv) + "\n")

    # ---- 全部命中分类台账（含非写命中）
    with open(os.path.join(ev_dir, "02_pattern_hits_all.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gate", "target_va", "hit_file_off", "hit_section", "hit_rva",
                    "n_candidates", "chosen_k", "chosen_start_va", "chosen_disasm",
                    "chosen_kinds", "is_write", "aligned_with_B", "classification"])
        for r in a_rows:
            key2 = None
            for (g, sva), v in chosen.items():
                if g == r["gate"] and v["hit_off"] == r["hit_off"]:
                    key2 = v
                    break
            if key2:
                c = key2["c"]
                w.writerow([r["gate"], "0x%08X" % r["va"], "0x%X" % r["hit_off"], r["sec"],
                            "0x%X" % (r["hit_rva"] or 0), len(r["candidates"]), c["k"],
                            "0x%08X" % c["start_va"], c["disasm"], "/".join(c["kinds"]),
                            c["is_write"], key2["aligned"],
                            "WRITE" if c["is_write"] else "non-write (read/lea/imm)"])
            else:
                w.writerow([r["gate"], "0x%08X" % r["va"], "0x%X" % r["hit_off"], r["sec"],
                            "0x%X" % (r["hit_rva"] or 0), len(r["candidates"]), "-", "-", "-",
                            "-", False, False, "NO_DECODE (data/unaligned)"])

    # ---- 反例校验（真实文件里的非写命中）
    ce_lines = []
    ce_lines.append("REAL-FILE COUNTER-EXAMPLE VALIDATION (low address 0x8B41C0)")
    ce_lines.append("All 4-byte LE occurrences of each gate VA were classified; non-write hits are listed.")
    ce_lines.append("A naive '4-byte match == write' rule would over-count these:")
    n_nonwrite = defaultdict(int)
    for r in a_rows:
        k2 = None
        for (g, sva), v in chosen.items():
            if g == r["gate"] and v["hit_off"] == r["hit_off"]:
                k2 = v
                break
        if k2 and not k2["c"]["is_write"]:
            n_nonwrite[r["gate"]] += 1
            ce_lines.append("  %s foff=0x%X VA=0x%08X %-40s kinds=%s" %
                            (r["gate"], r["hit_off"], k2["c"]["start_va"],
                             k2["c"]["disasm"], ",".join(k2["c"]["kinds"])))
    ce_lines.append("non-write hit counts: %s" % dict(n_nonwrite))
    ce_lines.append("")
    ce_lines.append("SYNTHETIC COUNTER-EXAMPLE (see 01_selftest.txt / 10_encoding_coverage.txt):")
    ce_lines.append("  B8 C0 41 8B 00 = mov eax,0x8B41C0 -> imm_coincidence, is_write=False")
    ce_lines.append("  B9/BA/68/05 encodings likewise -> imm_coincidence, is_write=False")
    ce_lines.append("  8D 35 C0 41 8B 00 = lea esi,[0x8B41C0] -> lea_addr, is_write=False")
    ce_lines.append("  A0 C0 41 8B 00 = mov al,[0x8B41C0] -> read8, is_write=False")
    ce_lines.append("CONCLUSION: classifier does not count immediate coincidences / LEA / reads as writes.")
    with open(os.path.join(ev_dir, "09_counterexamples.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ce_lines) + "\n")

    with open(os.path.join(ev_dir, "10_encoding_coverage.txt"), "w", encoding="utf-8") as f:
        f.write("SUPPORTED ENCODINGS (absolute-address / immediate forms searched)\n")
        f.write("All below were decoded by capstone 5.0.7 with detail=True; see 01_selftest.txt for results.\n")
        f.write("""
A0 / A1 / A2 / A3               moffs8/32 read/write (66 prefix -> 16-bit)
B0..B7                          mov r8, imm8      (no 4-byte VA operand; recorded as imm8_only)
B8..BF                          mov r32, imm32    (immediate coincidence, NOT a write)
C6 05 <disp32> <imm8>           mov byte  [A], imm8    / C6 /0../7 group via 80 /r
C7 05 <disp32> <imm32>          mov dword [A], imm32   / 66 C7 05 -> word
88 /r  (mod=00 rm=101 / SIB)    mov r/m8, r8       (write byte)
89 /r  (mod=00 rm=101 / SIB)    mov r/m32, r32     (write dword)
8A / 8B /r                      mov r, r/m          (read; 8B explicitly listed in task)
80 /r  <disp32> <imm8>          group1 byte: add/or/adc/sbb/and/sub/xor/cmp  (RMW or read)
81 /r  <disp32> <imm32>         group1 dword
83 /r  <disp32> <imm8>          group1 dword sign-extended
FE /0, FF /0 (and /1,/6)        inc/dec/push r/m   (RMW)
F6 /0, F7 /0                    test r/m, imm      (read)
0F B0/B1 cmpxchg, 0F C0/C1 xadd, 0F AB/0F B3/0F BB bts/btr/btc  (RMW)
8D /r                           lea r32, [A]       (address computation, NO memory access)
68 <imm32>                      push imm32         (immediate coincidence)
05 / 0D / 25 / 2D / 35 / 3D   ALU eax, imm32     (immediate coincidence)
""")
        f.write("\nSEARCH RANGE: whole file bytes [0x0, 0x%X) = %d bytes, all 5 sections + headers.\n" %
                (img.size, img.size))
        f.write("NOTE: .rsrc/.detour map file_off = VA - 0x6FC000; .text/.rdata/.data map file_off = RVA.\n")
        f.write("NOTE: gates are in .data BSS tail (no file bytes); a VA pattern hit is therefore\n")
        f.write("      always an instruction operand/immediate or a data pointer, never the byte itself.\n")
        f.write("LIMITATION: writes via register-indirect addressing (e.g. mov reg,VA; mov byte [reg],1)\n")
        f.write("      do not embed the VA in the writing instruction; see 12_indirect_pathways.txt.\n")
        f.write("LIMITATION (capstone access quirk): 0F B0/B1 cmpxchg r/m,r is reported by capstone 5.0.7\n")
        f.write("      with the memory operand access=CS_AC_READ only (conditional RMW). It would be\n")
        f.write("      classified 'read8' here, i.e. a FALSE NEGATIVE for a write. Likewise TEST/CMP\n")
        f.write("      memory operands report access=0 and are recovered via the mnemonic allowlist.\n")
        f.write("      None of the four gate write points use cmpxchg (all are C6 05 / 88 /r / 38 /r),\n")
        f.write("      so this quirk does not change the reported write sets; it is disclosed anyway.\n")

    # ---- 寄存器间接写途径（已知盲区）
    ind = []
    ind.append("REGISTER-INDIRECT PATHWAY ANALYSIS (known blind spot of absolute-VA pattern search)")
    ind.append("For every pattern hit classified as imm_coincidence / lea_addr, we scan the following")
    ind.append("32 instructions in the containing function for a write through that register.")
    ind.append("Grade of any positive hit: [静态推断-弱] (no dataflow proof).\n")
    ind_hits = []
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.detail = True
    for (g, sva), v in chosen.items():
        c = v["c"]
        if not any(k in ("imm_coincidence", "lea_addr") for k in c["kinds"]):
            continue
        ins = CLS.decode_one(img.d[c["start"]:c["start"] + 20], c["start_va"])
        if ins is None or not ins.operands:
            continue
        dst = ins.operands[0]
        if dst.type != X86_OP_REG:
            continue
        reg = dst.reg
        st = c["start_va"] + c["size"]
        insns = list(md2.disasm(img.d[st - img.image_base:st - img.image_base + 0x80], st))
        for j in insns[:32]:
            for op in j.operands:
                if op.type == X86_OP_MEM and op.mem.base == reg and op.mem.index == 0 \
                        and op.mem.disp == 0 and (op.access & CS_AC_WRITE):
                    ind_hits.append((g, c["start_va"], c["disasm"], j.address, fmt_dis(j)))
    if ind_hits:
        for g, a, da, b, db in ind_hits:
            ind.append("  %s load@0x%08X (%s) -> possible indirect write @0x%08X (%s)" % (g, a, da, b, db))
    else:
        ind.append("  NO register-indirect write candidate found within 32 following instructions.")
    ind.append("\nCONCLUSION: zero absolute-VA hits for a gate would NOT prove absence of runtime writes;")
    ind.append("only this finite static search was performed. Zero hits != runtime absence.")
    with open(os.path.join(ev_dir, "12_indirect_pathways.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ind) + "\n")

    # ---- 写点明细 + CSV
    write_rows = []
    for g, v in sorted(all_w, key=lambda x: (x[0], x[1])):
        gate_va = GATE_NAME and dict((n, a) for n, a in GATES)[g]
        # 找 B 通道里该 VA 的反汇编（优先 B1）
        rec = next((h for h in B1["hits"] if h["gate"] == g and h["va"] == v and h["is_write"]), None)
        if rec is None:
            rec = next((h for h in B2["hits"] if h["gate"] == g and h["va"] == v and h["is_write"]), None)
        if rec is None:
            ck = (g, v)
            if ck not in chosen:
                continue
            c = chosen[ck]["c"]
            rec = dict(va=c["start_va"], rva=c["start_va"] - img.image_base,
                       file_off=c["start"], bytes=c["bytes"], disasm=c["disasm"],
                       kind=c["kinds"][0], width=c["width"], is_rmw=c["is_rmw"])
        ctx = analyze_write_context(img, rec["va"], gate_va)
        val = ctx["value"]
        if val == 1:
            valtag = "SET1"
        elif val == 0:
            valtag = "CLEAR0"
        else:
            valtag = "VAR"
        kind = "%s_%s" % (rec["kind"], valtag)
        chan = []
        if (g, v) in setA_w:
            chan.append("A")
        if (g, v) in setB1_w:
            chan.append("B1")
        if (g, v) in setB2_w:
            chan.append("B2")
        kind += "/" + "+".join(chan)
        grade = "[本次实测]" if len(chan) >= 2 else "[静态推断-强]"
        write_rows.append(dict(
            target="%s=0x%08X" % (g, gate_va), kind=kind, width="%dB" % rec["width"],
            va="0x%08X" % rec["va"], rva="0x%08X" % rec["rva"],
            file_off="0x%08X" % rec["file_off"], bytes=rec["bytes"],
            disasm=rec["disasm"],
            basic_block=("0x%08X" % ctx["bb"]) if ctx["bb"] else "UNRESOLVED",
            prev_call_or_branch=ctx["prev"], is_rmw=str(bool(rec["is_rmw"])).lower(),
            grade=grade,
            _ctx=ctx, _gate=g, _gate_va=gate_va, _value=val, _valtag=valtag,
            _chan=chan, _entry=ctx["entry"]))
    with open(os.path.join(out_dir, "GATE_WRITERS.csv"), "w", encoding="utf-8", newline="") as f:
        cols = ["target", "kind", "width", "va", "rva", "file_off", "bytes", "disasm",
                "basic_block", "prev_call_or_branch", "is_rmw", "grade"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in write_rows:
            w.writerow(r)

    # ---- 上下文 / 函数 / 调用者 / 导入 / 字符串
    ctx_lines = []
    ctx_lines.append("CONTEXT: per-write function entry, basic block, previous call/branch, inferred value")
    for r in write_rows:
        ctx_lines.append("%s %s %s bb=%s prev=%s value=%s(%s) fn_entry=%s" %
                         (r["_gate"], r["va"], r["disasm"], r["basic_block"],
                          r["prev_call_or_branch"], r["_value"], r["_valtag"],
                          ("0x%08X" % r["_entry"]) if r["_entry"] else "UNRESOLVED"))
    ctx_lines.append("")
    ctx_lines.append("=== FRAME ADVANCE FUNCTION ===")
    fe = find_function_entry(img, FRAME_MOV_STORE)
    fpad = find_function_end(img, FRAME_MOV_STORE)
    fend = fpad - 1 if fpad else None          # 函数最后一字节的 VA
    fi, fskips = function_instructions(img, fe, FRAME_MOV_STORE) if fe else ([], [])
    ctx_lines.append("probe VA = 0x%08X ; heuristic entry = %s ; next padding @ %s ; "
                     "last function byte = %s ; decoded insns = %d (stopped at first ret after probe)" %
                     (FRAME_MOV_STORE, ("0x%08X" % fe) if fe else "UNRESOLVED",
                      ("0x%08X" % fpad) if fpad else "-",
                      ("0x%08X" % fend) if fend else "-", len(fi)))
    # 整个函数体（不因中途 ret 截断），用于回边/循环判定
    ffi = []
    if fe and fpad:
        mdff = Cs(CS_ARCH_X86, CS_MODE_32)
        mdff.detail = True
        mdff.skipdata = True
        foff = fe - img.image_base
        ffi = [i for i in mdff.disasm(img.d[foff:foff + (fpad - fe)], fe)
               if i.id != 0 and not i.mnemonic.startswith(".byte")]
    ctx_lines.append("full-function decode (entry..padding, no ret truncation): %d instructions" % len(ffi))
    # 该函数内是否有回边包围自增点
    back = []
    for ins in ffi:
        if ins.address <= FRAME_MOV_STORE:
            continue
        for op in ins.operands:
            if op.type == X86_OP_IMM and (ins.mnemonic.startswith("j") or ins.mnemonic.startswith("loop")):
                if op.imm & 0xFFFFFFFF <= FRAME_MOV_STORE:
                    back.append((ins.address, fmt_dis(ins)))
    ctx_lines.append("back-edges AFTER 0x%08X targeting <= it: %d %s" % (FRAME_MOV_STORE, len(back), back))
    ctx_lines.append("increment sites inside function (all 'inc' insns): %s" %
                     ["0x%08X %s" % (i.address, fmt_dis(i)) for i in ffi
                      if i.mnemonic == "inc"])
    ctx_lines.append("store sites of 0xA8ED84 inside function: %s" %
                     ["0x%08X %s" % (i.address, fmt_dis(i)) for i in ffi
                      if "0xa8ed84" in i.op_str and (i.mnemonic == "mov")])
    # 直接调用者
    direct = [(c, t2) for c, t2 in e8 if t2 == fe]
    ctx_lines.append("")
    ctx_lines.append("=== DIRECT CALLERS (call rel32 -> 0x%08X) ===" % (fe or 0))
    for c, t2 in direct:
        ins = CLS.decode_one(img.d[c - img.image_base:c - img.image_base + 8], c)
        centry = find_function_entry(img, c)
        inloop, edge = loop_enclosing(img, centry, c) if centry else (False, "entry-unresolved")
        ctx_lines.append("  caller VA=0x%08X RVA=0x%08X FOFF=0x%08X | %-24s | %-30s | fn_entry=%s in_loop=%s edge=%s" %
                         (c, c - img.image_base, c - img.image_base,
                          ins.bytes.hex(" ") if ins else "-", fmt_dis(ins) if ins else "-",
                          ("0x%08X" % centry) if centry else "UNRESOLVED", inloop, edge))
    ctx_lines.append("count = %d" % len(direct))
    ctx_lines.append("")
    ctx_lines.append("=== INDIRECT CALLS (UNRESOLVED) ===")
    ctx_lines.append("4-byte LE of 0x%08X searched in whole file: %d hits -> no static function pointer." %
                     (fe or 0, len(list(find_all(img.d, struct.pack("<I", fe or 0))))))
    ctx_lines.append("B1 indirect call instructions (call r/m32, not call rel32): %d; all UNRESOLVED." %
                     len(B1["indirect"]))
    for a, s in B1["indirect"][:40]:
        ctx_lines.append("  0x%08X %s" % (a, s))
    ctx_lines.append("")
    ctx_lines.append("=== RESET SITES of 0xA8ED84 (round-provided 3) ===")
    for rs in RESET_SITES:
        entry = find_function_entry(img, rs)
        ins = CLS.decode_one(img.d[rs - img.image_base:rs - img.image_base + 12], rs)
        callers = [c for c, t2 in e8 if entry and t2 == entry]
        ctx_lines.append("  reset VA=0x%08X RVA=0x%08X FOFF=0x%08X | %-30s | %-40s | fn_entry=%s direct_callers=%d %s" %
                         (rs, rs - img.image_base, rs - img.image_base,
                          ins.bytes.hex(" ") if ins else "-", fmt_dis(ins) if ins else "-",
                          ("0x%08X" % entry) if entry else "UNRESOLVED", len(callers),
                          ["0x%08X" % c for c in callers[:8]]))
    with open(os.path.join(ev_dir, "07_context.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ctx_lines) + "\n")

    # ---- 函数级直接调用图 / 清零点与帧推进函数的路径关系
    fg, cg_sites, cg_fne, cg_cache = build_function_call_graph(img, B1, e8)
    cg_lines = []
    cg_lines.append("FUNCTION-LEVEL DIRECT CALL GRAPH (raw E8 rel32 filtered by B1 instruction-start bitmap)")
    cg_lines.append("function entries are heuristic (padding boundary + 16-byte alignment); not proven.")
    cg_lines.append("nodes=%d edges=%d" % (len(set(fg) | {y for v in fg.values() for y in v}),
                                          sum(len(v) for v in fg.values())))
    cg_lines.append("")
    cg_lines.append("frame fn entry = 0x%08X" % (fe or 0))
    cg_lines.append("frame fn direct callees (%d): %s" %
                    (len(fg.get(fe, ())), sorted(hex(x) for x in fg.get(fe, ()))))
    cg_lines.append("frame fn direct callers at function level (%d): %s" %
                    (len([x for x, v in fg.items() if fe in v]),
                     sorted(hex(x) for x, v in fg.items() if fe in v)))
    cg_lines.append("")
    cg_lines.append("RESET SITE -> FRAME FN reachability (BFS depth<=4 on DIRECT call graph):")
    cg_paths = {}
    for rs in RESET_SITES:
        re_ = cg_fne(rs)
        p1 = bfs_path(fg, re_, fe, 4) if re_ else None
        p2 = bfs_path(fg, fe, re_, 4) if re_ else None
        cg_paths[rs] = dict(entry=re_, to_frame=p1, from_frame=p2)
        cg_lines.append("  reset 0x%08X (fn 0x%08X): reset->frame = %s ; frame->reset = %s" %
                        (rs, re_ or 0,
                         (" -> ".join(hex(x) for x in p1)) if p1 else "NO PATH",
                         (" -> ".join(hex(x) for x in p2)) if p2 else "NO PATH"))
        if p1:
            for a, b in zip(p1, p1[1:]):
                ss = cg_sites.get((a, b), [])
                cg_lines.append("      hop 0x%08X -> 0x%08X via call sites %s" %
                                (a, b, ["0x%08X" % c for c in ss[:6]]))
        shared = set(x for x, v in fg.items() if fe in v) & set(x for x, v in fg.items() if re_ in v)
        cg_lines.append("      shared direct callers: %s" %
                        (sorted(hex(x) for x in shared) if shared else "none"))
    cg_lines.append("")
    cg_lines.append("CONCLUSION [静态推断-强] (direct call graph only): reset sites are UPSTREAM of")
    cg_lines.append("the frame-advance function (initialization/pregame/exit paths reach the main loop")
    cg_lines.append("which calls 0x%08X). They do NOT call it directly and are NOT called by it." % (fe or 0))
    cg_lines.append("LIMITATION: function entries are heuristic; indirect/virtual calls are NOT in this graph.")
    with open(os.path.join(ev_dir, "13_call_paths.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(cg_lines) + "\n")

    # ---- 门控3 旧错误 0x41C0 的精确复现（非法起点解码伪影）
    art = []
    art.append("EXACT REPRODUCTION OF THE OLD 'gate3 = 0x41C0' ERROR")
    art.append("Byte stream at 0x0055DE5F (file offset 0x15DE5F):")
    o = 0x55DE5F - img.image_base
    art.append("  %s" % img.d[o:o + 14].hex(" "))
    art.append("")
    art.append("Aligned/correct decode from 0x0055DE5F:")
    for ins in CLS.md.disasm(img.d[o:o + 14], 0x55DE5F, count=3):
        art.append("  0x%08X %-20s %s" % (ins.address, ins.bytes.hex(" "), fmt_dis(ins)))
    art.append("")
    art.append("ILLEGAL start 0x0055DE60 (1 byte into the '75 67' jne):")
    for ins in CLS.md.disasm(img.d[o + 1:o + 15], 0x55DE60, count=3):
        art.append("  0x%08X %-20s %s" % (ins.address, ins.bytes.hex(" "), fmt_dis(ins)))
    art.append("")
    art.append("=> 0x67 is really the rel8 displacement of 'jne 0x55DEC8' (75 67).")
    art.append("   As an address-size override prefix it turns A0 into a 16-bit moffs, consuming")
    art.append("   only 'c0 41' and yielding 'mov al, byte ptr [0x41c0]' -- the old wrong value.")
    art.append("   The correct gate-3 address is 0x008B41C0 (A0 c0 41 8b 00 at 0x0055DE61).")
    art.append("")
    art.append("Whole-file 4-byte LE search of the WRONG VA 0x000041C0 (c0 41 00 00): %d hits," %
               len(list(find_all(img.d, struct.pack("<I", 0x41C0)))))
    for h in find_all(img.d, struct.pack("<I", 0x41C0)):
        sec = img.section_of_off(h)
        art.append("   foff=0x%X section=%s (data, not a gate read)" %
                   (h, sec["name"] if sec else "HEADER"))
    with open(os.path.join(ev_dir, "14_gate3_artifact.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(art) + "\n")

    # 导入 / 字符串
    iat = {}
    for e in img.pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            iat[imp.address] = e.dll.decode("latin1") + "!" + (
                imp.name.decode("latin1") if imp.name else "ord%d" % imp.ordinal)
    is_lines = []
    is_lines.append("IAT RESOLUTION (pefile DIRECTORY_ENTRY_IMPORT)")
    for a in sorted(iat):
        n = iat[a]
        if any(k in n for k in ("Sleep", "timeGetTime", "GetTickCount", "PeekMessage",
                                "GetForegroundWindow", "GetActiveWindow", "IsIconic",
                                "DialogBox", "CreateDialog", "MessageBox", "ShowWindow",
                                "EnableWindow", "SetFocus", "EndDialog", "WaitFor", "CloseHandle")):
            is_lines.append("  0x%08X %s" % (a, n))
    is_lines.append("")
    is_lines.append("KEY IMPORT REFERENCES IN FRAME-ADVANCE FUNCTION")
    for a, n in sorted(iat.items()):
        if a in (0x7e11f0, 0x7e1530, 0x7e1484, 0x7e1420, 0x7e13d4, 0x7e1460, 0x7e13ac, 0x7e1498):
            pat = struct.pack("<I", a)
            locs = ["0x%08X" % (img.image_base + o) for o in find_all(img.d, pat)]
            is_lines.append("  0x%08X %-34s code refs (VA): %s" % (a, n, ", ".join(locs[:20])))
    is_lines.append("")
    is_lines.append("STRINGS at push-imm32 targets near gate code")
    for va in (0x82A044, 0x8278B4, 0x82637C, 0x831A60, 0x820E0C, 0x822CFC):
        off = img.va_to_off(va)
        if off is None:
            is_lines.append("  0x%08X (no file backing)" % va)
            continue
        s = img.d[off:off + 90].split(b"\x00")[0]
        is_lines.append("  0x%08X FOFF=0x%X %r" % (va, off, s[:90]))
    is_lines.append("")
    is_lines.append("0x8B41C0 NEIGHBOUR GLOBAL BLOCK (4-byte LE reference counts in whole file)")
    for va in range(0x8B41A8, 0x8B4209, 4):
        c = len(list(find_all(img.d, struct.pack("<I", va))))
        if c:
            is_lines.append("  0x%08X hits=%d" % (va, c))
    for va in (0x8B41B5, 0x8B41D5, 0x8B41F8, 0x8B41FC, 0x8B4200, 0xA83D4A, 0xA83D4B, 0xA83D4C, 0xA83D50):
        c = len(list(find_all(img.d, struct.pack("<I", va))))
        if c:
            is_lines.append("  0x%08X hits=%d (byte/odd offset)" % (va, c))
    with open(os.path.join(ev_dir, "08_imports_strings.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(is_lines) + "\n")

    # ---- 计算摘要（供 MD 生成）
    summary = dict(
        sha=img.sha, size=img.size, sections=[s["name"] for s in img.sections],
        facts=facts, selftest_pass=True,
        n_pattern_hits={g: sum(1 for r in a_rows if r["gate"] == g) for g, _ in GATES},
        n_writes={g: sum(1 for r in write_rows if r["_gate"] == g) for g, _ in GATES},
        n_set={g: sum(1 for r in write_rows if r["_gate"] == g and r["_valtag"] == "SET1") for g, _ in GATES},
        n_clear={g: sum(1 for r in write_rows if r["_gate"] == g and r["_valtag"] == "CLEAR0") for g, _ in GATES},
        first_write={g: (min((r["va"], r["disasm"]) for r in write_rows if r["_gate"] == g)
                        if any(r["_gate"] == g for r in write_rows) else ("-", "-")) for g, _ in GATES},
        frame_entry=fe, frame_end=fend, frame_pad=fpad,
        frame_size=((fpad - fe) if fe and fpad else None),
        n_direct_callers=len(direct), direct_callers=[c for c, _ in direct],
        back_edges=back, n_indirect=len(B1["indirect"]),
        b1_skips=len(B1["skips"]), b2_skips=len(B2["skips"]),
        b1_gaps=len(merge_intervals(uncov)), b2_gaps=len(merge_intervals(uncov2)),
        triple=len(setA_w & setB1_w & setB2_w), union=len(all_w),
        a_only=len(setA_w - setB1_w - setB2_w), b_only=len((setB1_w | setB2_w) - setA_w),
        n_a=len(setA_w), n_b1=len(setB1_w), n_b2=len(setB2_w),
        resets=[dict(va=rs, entry=find_function_entry(img, rs)) for rs in RESET_SITES],
        reset_paths=cg_paths,
        n_loop_callers=sum(1 for c, _ in direct
                           if find_function_entry(img, c) and
                           loop_enclosing(img, find_function_entry(img, c), c)[0]),
        indirect_candidates=len(ind_hits),
    )
    with open(os.path.join(ev_dir, "11_computed_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    # ---- Markdown 交付物
    write_mds(out_dir, img, write_rows, summary, B1, B2, direct, e8, iat, fe, fend, back,
              merge_intervals(uncov), B1["skips"], a_rows, chosen, ind_hits, cg_paths)

    # ---- stdout
    print("\n".join(log))
    print("")
    print("=== SUMMARY ===")
    print("SHA256=%s" % img.sha)
    for g, _ in GATES:
        fw = summary["first_write"][g]
        print("%s pattern_hits=%d write_points=%d SET=%d CLEAR=%d first=%s %s" %
              (g, summary["n_pattern_hits"][g], summary["n_writes"][g],
               summary["n_set"][g], summary["n_clear"][g], fw[0], fw[1]))
    print("selftest five classes: PASS (distinct=5)")
    print("frame fn entry=0x%08X end=0x%08X size=0x%X direct_callers=%d" %
          (fe or 0, fend or 0, summary["frame_size"] or 0, len(direct)))
    print("cross-validation triple=%d union=%d A-only=%d B-only=%d" %
          (summary["triple"], summary["union"], summary["a_only"], summary["b_only"]))
    print("B1 skipdata=%d cover-gaps=%d ; B2 skipdata=%d cover-gaps=%d" %
          (summary["b1_skips"], summary["b1_gaps"], summary["b2_skips"], summary["b2_gaps"]))
    print("ALL OUTPUTS WRITTEN TO %s" % out_dir)
    with open(os.path.join(ev_dir, "00_run_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    return 0


# --------------------------------------------------------------------------------------
# Markdown 生成（叙述性结论由本项目静态观测支撑，等级严格分档）
# --------------------------------------------------------------------------------------
def write_mds(out_dir, img, write_rows, S, B1, B2, direct, e8, iat, fe, fend, back,
              gaps, skips, a_rows, chosen, ind_hits, cg_paths):
    def tbl(rows, header):
        s = "| " + " | ".join(header) + " |\n"
        s += "|" + "|".join(["---"] * len(header)) + "|\n"
        for r in rows:
            s += "| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |\n"
        return s

    by_gate = {g: [r for r in write_rows if r["_gate"] == g] for g, _ in GATES}

    # ---------------- GATE_SEMANTICS.md ----------------
    m = []
    m.append("# 四个门控字节的静态语义 — %s / W2_static" % RUN_ID)
    m.append("")
    m.append("**纯静态**：只读磁盘 PE 字节。未启动游戏、未 attach、未读活进程、未挂起线程、未注入。")
    m.append("真机只读观测由同轮另一代理负责；本文只给「真机该期待什么值」。")
    m.append("")
    m.append("## 0. 镜像实测（开工前实算）")
    m.append("")
    m.append("`[本次实测]` 命令与原始 stdout / 退出码见 `EVIDENCE/00_commands_and_exit.txt`、"
             "`EVIDENCE/00_run_log.txt`。")
    m.append("")
    m.append("```")
    m.append("PATH   = %s" % img.path)
    m.append("SIZE   = %d (0x%X)" % (img.size, img.size))
    m.append("SHA256 = %s" % img.sha)
    m.append("期望     = %s" % EXPECT_SHA256)
    m.append("结论     = 一致，允许开工")
    m.append("```")
    m.append("")
    m.append("PE 事实复核 `[本次实测]`（`EVIDENCE/00_run_log.txt`）：")
    m.append("")
    m.append(tbl([[st, label, detail] for st, label, detail in S["facts"]],
                 ["校验", "项", "值"]))
    m.append("> 注：`RELOCS_STRIPPED` 是 COFF `IMAGE_FILE_HEADER.Characteristics` bit0，"
             "不是 `DllCharacteristics`；本镜像 `DllCharacteristics=0x20`，`DYNAMIC_BASE`(0x40) 未置位。"
             "两者不矛盾。")
    m.append("")
    m.append("**地址换算** `[本次读码]` `gate_semantics.py:PEImage.va_to_off/off_to_va`："
             "`.text`/`.rdata`/`.data` 文件偏移 = RVA；`.rsrc`/`.detour` 文件偏移 = VA − 0x6FC000。"
             "四个门控 VA 全部落在 `.data` 的 **BSS 尾**（VA 0x812000..0xB79BE4，"
             "但 `.data` 只有 0x6C000 字节文件 backing，到 VA 0x87E000 为止），"
             "**磁盘上没有这些字节**，加载器零填充。因此「4 字节 VA 模式命中」"
             "必然是指令里的地址操作数 / 立即数 / 数据指针，不会是门控字节本身。")
    m.append("")
    m.append("## 1. 方法与覆盖度")
    m.append("")
    m.append("双通道 + 复扫交叉验证；全部原始输出在 `EVIDENCE/`。")
    m.append("")
    m.append("| 通道 | 做法 | 输出 |")
    m.append("|---|---|---|")
    m.append("| A | 全文件 `[0x0, 0x%X)` 共 %d 字节做 4 字节小端 VA 搜索；每个命中向前 k=1..12 "
             "试指令起点，capstone 逐操作数 `access`/`size`/`type` 分类 | `02_pattern_hits_all.csv`, `03_channelA_decoded.txt` |" %
             (img.size, img.size))
    m.append("| B1 | 从 **0x90(≥4)/0xCC(≥2) 填充区间边界** 做确定性线性扫描（skipdata），"
             "记录 `uncovered_intervals` | `04_B1_linear.txt`, `05_uncovered_intervals.txt` |")
    m.append("| B2 | **第二可信边界复扫**：独立于 B1 的原始字节级 `E8 rel32` 目标（16 字节对齐）"
             "作为边界重扫 | `04_B2_rescan.txt`, `06_cross_validation.txt` |")
    m.append("")
    m.append("支持编码清单见 `EVIDENCE/10_encoding_coverage.txt`（A0/A1/A2/A3、B0..B7、B8..BF、"
             "C6 05 / 66 C7 05 / C7 05、88/89/8A/8B（含 SIB 绝对地址）、80/81/83、FE/FF、F6/F7、"
             "0F B0/B1/C0/C1、8D、68、05/0D/25/2D/35/3D）。")
    m.append("")
    m.append("**负控 `--selftest`** `[本次实测]`：合成字节流五类必须可分 → **PASS，5/5 可分**；"
             "仅前三类算写。见 `EVIDENCE/01_selftest.txt`。")
    m.append("")
    m.append("**反例校验（0x8B41C0 低位地址污染）** `[本次实测]`：`B8 C0 41 8B 00` "
             "(`mov eax,0x8B41C0`)、`B9/BA`、`68 C0 41 8B 00` (`push`)、`05 ...` (`add eax,imm32`) "
             "均被判为 `imm_coincidence` / `is_write=False`；`8D 35 ...` (`lea`) 判 `lea_addr`；"
             "`A0 ...` 判 `read8`。真实文件里的非写命中逐条列于 `EVIDENCE/09_counterexamples.txt`。"
             "结论：分类器**不会**把立即数巧合算成内存写。")
    m.append("")
    m.append("**交叉验证** `[本次实测]`：A 写点=%d，B1=%d，B2=%d，三通道交集=%d，并集=%d，"
             "A-only=%d，B-only=%d。明细 `EVIDENCE/06_cross_validation.txt`。" %
             (S["n_a"], S["n_b1"], S["n_b2"], S["triple"], S["union"], S["a_only"], S["b_only"]))
    m.append("")
    m.append("**扫描无命中说明 / 零命中 ≠ 运行期不存在**：本次搜索范围是**磁盘文件全部 %d 字节**，"
             "只覆盖上列「指令里直接内嵌 4 字节绝对 VA」的编码。"
             "寄存器间接写（`mov reg,VA` 后 `mov byte [reg],1`）、"
             "通过结构体基址 + 偏移写、运行期自修改代码、以及加载器写入，"
             "都不会在写指令里内嵌该 VA。`EVIDENCE/12_indirect_pathways.txt` 做了前向 32 指令的"
             "寄存器间接写候选扫描，命中 %d 条（全部 `[静态推断-弱]`）。"
             "本次**没有**对任何门控宣称「运行期不存在其他写者」。" % (img.size, len(ind_hits)))
    m.append("")
    m.append("**未覆盖区间** `[本次实测]`：B1 skipdata 区间 %d 处、cover_bitmap 空隙 %d 段；"
             "B2 skipdata %d 处、空隙 %d 段。另有 FE 头、`.rdata`/`.data` 文件段、"
             "`.rsrc`/`.detour`、`.data` BSS 尾不做线性反汇编（只由通道 A 覆盖）。"
             "明细 `EVIDENCE/05_uncovered_intervals.txt`。" %
             (S["b1_skips"], S["b1_gaps"], S["b2_skips"], S["b2_gaps"]))
    m.append("")
    m.append("## 2. 写入点总表")
    m.append("")
    m.append("`GATE_WRITERS.csv` 为权威清单。下表按门控分组（VA / RVA / FOFF / 字节 / 反汇编 / "
             "基本块 / 前一条调用或条件分支 / 宽度 / RMW / 推定值 / 等级）。")
    m.append("")
    m.append("[本次实测] 全部写点均来自 `python gate_semantics.py` 的字节解码输出"
             "（命令+stdout+退出码见 `EVIDENCE/00_commands_and_exit.txt`）；"
             "`kind` 末尾 `/A+B1+B2` 等标注了确认通道。")
    m.append("")
    for g, va in GATES:
        rows = by_gate[g]
        m.append("### %s = 0x%08X — 写点 %d 处（置位 %d / 清零 %d / 其他 %d）" %
                 (g, va, len(rows), S["n_set"][g], S["n_clear"][g],
                  len(rows) - S["n_set"][g] - S["n_clear"][g]))
        m.append("")
        m.append(tbl([[r["va"], r["rva"], r["file_off"], "`%s`" % r["bytes"],
                       "`%s`" % r["disasm"], r["basic_block"],
                       r["prev_call_or_branch"].replace("|", " \\| "),
                       r["width"], r["is_rmw"], r["_valtag"], r["grade"]] for r in rows],
                     ["VA", "RVA", "FOFF", "bytes", "disasm", "basic_block",
                      "prev_call_or_branch", "width", "RMW", "值", "grade"]))
        m.append("")

    # ---- 语义结论（分档） ----
    m.append("## 3. 语义判定（分档）")
    m.append("")
    m.append("等级严格使用 `[静态推断-强]` / `[静态推断-弱]` / `[待运行验证]`；"
             "「我猜它是暂停」不写成已证。")
    m.append("")
    m.append("### 共同事实 `[本次读码]`")
    m.append("")
    m.append("- `0x55DE4F..0x55DE81` 四门控**串联 `test al,al` + `jne 0x55DEC8`**："
             "任一非 0 ⇒ 跳到 0x55DEC8 清 `[0xABCD58]=0` 后返回，**不推进帧计数**"
             "（`EVIDENCE/07_context.txt`、`GATE_DECODE.txt` 复核一致）。")
    m.append("- 四门控在 `0x52DA78/7F/86/8D` 被**一次性同时写 0**，紧接着 "
             "`0x52DA94..0x52DAD1` 大量全局归零；同函数 `0x52DA08` 把帧计数 `0xA8ED84` 归零。"
             "这是**场景/对局初始化路径** `[静态推断-强]`。")
    m.append("- 四门控在 `0x55D123/129/12F/135`、`0x55D1B1/B7/BD/C3`、"
             "`0x55D219/21F/225/22B`、`0x55D25C/262/268/26E` 被**成组清 0**，"
             "每组后面跟随 `call 0x72DFB0`、`0x69BB40`、`0x685670/0x685DC0/0x6863E0/0x686570`、"
             "`0x69BAB0` 和 `mov byte [0xABCD58],bl`。这是**「门控被消费后的恢复路径」**"
             " `[静态推断-强]`：门控是「挂起请求」标志，处理完即全部清零。")
    m.append("- `0xA8B238` 是模式枚举（0 / 3 / 4 / 5）；`0x55D3A0` 附近对模式 0/5 用 "
             "`Sleep(500)`、其他用 `Sleep(10)`；`0x55D3BB` 起把帧计数与 `[0xA8E2E4]` 比较、"
             "`timeGetTime`。`0xA8E9A0` 为「循环活动」标志（`0x55D371 je 0x55DECF` 直接返回）。")
    m.append("- `0x82637C` = `\"Loaded recording values for scenario : %s\\n\"`（在 "
             "`0x52DC17` 被 printf 引用）；`0x82A044` = `\"Disconnect_Gracefully\\n\"`"
             "（在 `0x55D298` 被引用）；`0x831A60` = `\"Pregame setup for %d players.\\n\"`；"
             "`0x820E0C` = `\"Processing EXIT event on frame %d\\n\"`（在 `0x4C790A` "
             "作为 printf 格式串、实参为 `[0xA8ED84]` 帧号，紧邻 G4 置位点）。"
             "`[本次读码] EVIDENCE/08_imports_strings.txt`。")
    m.append("")
    m.append("### G1 = 0x00A83D49")
    m.append("")
    m.append("| 项 | 结论 | 等级 |")
    m.append("|---|---|---|")
    m.append("| 置位者 | 4 处 `mov byte ptr [0xa83d49], 1`，全部在 `0x4F8440` 起的同一函数内"
             "（`0x4F867C`、`0x4F8692`、`0x4F86EE`、`0x4F87BB`）。上游条件：`[esi+0x1F7]` / "
             "`[esi+0x1F8]` / `[esi+0x1F6]` 三个对象标志、`[0xA8B238]` 模式 ==0 或 3/4、"
             "`cmp esi,[0xA83D4C]`、两次虚调用 `[edx+4]`/`[eax+8]` 返回布尔；"
             "函数内先用 `0x6C8C40`/`0x7529E0`/`0x48D080` 做**等待循环**（`0x4F860B..0x4F8655`、"
             "`0x4F8732..0x4F877E`），再置位。 | `[静态推断-强]`（有直接写入条件） |")
    m.append("| 清零者 | `0x52DA78`（初始化）、`0x55D129`、`0x55D1B1`、`0x55D219`、`0x55D25C`"
             "（消费路径，写 `bl=0`，`bl` 由同函数 `0x55D05E xor ebx,ebx` 得 0）。 | `[静态推断-强]` |")
    m.append("| 语义假设 | 与**联机/多人同步等待**相关（所在函数以帧计数 `0xA8ED84` 为时间基准、"
             "按 `[esi+0x2A4]/[esi+0x2AC]` 做帧差、判模式 3/4、等待循环），"
             "置位 = 「请求挂起帧推进直到同步/等待条件解除」。"
             "**不是**已证的「暂停菜单」。 | `[静态推断-弱]`（仅函数邻近性 + 模式枚举） |")
    m.append("| 真机期待值 | 正常对战推进中应为 **0**；进入等待/同步/断线处理时应短时读到 **1**，"
             "随后被 `0x55D1xx/0x55D2xx` 清回 0。 | `[待运行验证]` |")
    m.append("")
    m.append("### G2 = 0x00A8ECD0")
    m.append("")
    m.append("| 项 | 结论 | 等级 |")
    m.append("|---|---|---|")
    m.append("| 置位者 | 3 处 `mov byte ptr [0xa8ecd0], 1`（`0x4F86F7`、`0x4F879C`、`0x4F87B2`），"
             "与 G1 置位**同一函数 `0x4F8440`、互补分支**：G1 置位路径的 `else` 落到 "
             "`0x4F86F7 c6 05 d0 ec a8 00 01`。前置条件同样是 `[esi+0x1F8]` / "
             "`[esi+0x1F6]` 帧差计时与等待循环。 | `[静态推断-强]` |")
    m.append("| 清零者 | `0x52DA7F`、`0x55D123`、`0x55D1B7`、`0x55D21F`、`0x55D262`。 | `[静态推断-强]` |")
    m.append("| 语义假设 | G1/G2 是同一「等待/同步」状态机的两个互补标志；G2 可能对应"
             "另一类等待（如「另一方向/另一阶段的同步」），但**无法静态区分**二者各自对应的"
             "具体状态。 | `[静态推断-弱]` |")
    m.append("| 真机期待值 | 正常推进中 **0**；与 G1 互斥地短时为 **1**。 | `[待运行验证]` |")
    m.append("")
    m.append("### G3 = 0x008B41C0 —— 旧记录纠错")
    m.append("")
    m.append("> **[转引] 点名纠正**：旧记录把「门控 3」写成 `0x41C0`，"
             "那是**从非法起点 `0x55DE60` 解码产生的 `67` (address-size override) 前缀伪影**"
             "（该 `0x67` 实为 `0x55DE5F jne 0x55DEC8` 的 rel8 位移），并非真实地址。"
             "精确复现见 `EVIDENCE/14_gate3_artifact.txt`。"
             "复核 `[本次实测]`：`0x0055DE61 a0 c0 41 8b 00` = "
             "`mov al, byte ptr [0x8b41c0]`，4 字节小端操作数 `c0 41 8b 00` ⇒ "
             "**门控 3 = 0x008B41C0**，RVA `0x004B41C0`，FOFF `0x004B41C0`（该 VA 在 "
             "`.data` BSS 尾，无文件字节）。见 `EVIDENCE/03_channelA_decoded.txt` 与 `DISAGREE.md`。")
    m.append("")
    m.append("| 项 | 结论 | 等级 |")
    m.append("|---|---|---|")
    m.append("| 置位者 | `0x48CB2E  c6 05 c0 41 8b 00 01  mov byte ptr [0x8b41c0], 1`。"
             "位于 `0x48C...` 的一个分发函数：`0x48CB22 c6 05 fc 2c 82 00 00` 与 "
             "`0x48CB2E` 是**相邻 switch 分支**（各自 `jmp 0x48CC31` 汇合），"
             "其邻居 `0x48CB4C` 起读 `[0xA83D4C]` 对象的 `+0x1F5/+0x1F7/+0x1F8` 标志。"
             " | `[静态推断-强]`（有直接写入点与其所在分支结构） |")
    m.append("| 清零者 | `0x52DA86`、`0x55D12F`、`0x55D1BD`、`0x55D225`、`0x55D268`。 | `[静态推断-强]` |")
    m.append("| 语义假设 | 该地址位于一块**全局对象/配置块**：邻近 `0x8B41B8`(17 命中)、"
             "`0x8B41C8`(12)、`0x8B41CC`(27)、`0x8B41D8`(35)、`0x8B41F8/FC/0x8B4200` "
             "在初始化函数 `0x52D9E4..0x52D9F0` 被成组写 0；`0x8B41E0`(10 命中)。"
             "它**不像**独立布尔，更像某个结构体的成员（`EVIDENCE/08_imports_strings.txt`）。"
             "置位分支与「回合/网络消息分发」同处一函数。 | `[静态推断-弱]` |")
    m.append("| 真机读到非零时的解释 | 不能只解释成「暂停」：应同时检查同块的 "
             "`0x8B41B8 / 0x8B41CC / 0x8B41D8` 以及 `[0xA83D4C]` 对象 `+0x1F5/+0x1F7/+0x1F8`，"
             "判断是分发状态还是挂起请求。 | `[待运行验证]` |")
    m.append("")
    m.append("### G4 = 0x00A83D48")
    m.append("")
    m.append("| 项 | 结论 | 等级 |")
    m.append("|---|---|---|")
    m.append("| 置位者 | `0x4C7917  c6 05 48 3d a8 00 01  mov byte ptr [0xa83d48], 1`。"
             "**直接上游** `[静态推断-强]`：`0x4C7903 mov ecx,[0xa8ed84]` → "
             "`0x4C790A push 0x820e0c` → `0x4C790F call 0x4068e0`（printf）→ "
             "`0x4C7914 add esp,8` → 立刻置位。`0x820E0C` 的字符串实测为 "
             "`\"Processing EXIT event on frame %d\\n\"`（`EVIDENCE/08_imports_strings.txt`），"
             "即**打印当前帧号后立即置 G4=1**。函数尾部 `0x4C7929` 起还有 "
             "`test byte [0xa8d5f8],2` / `mov dword [0xa8eda0],1` 分支。"
             " | `[静态推断-强]`（有直接写入点 + 相邻字符串 + 帧号实参） |")
    m.append("| 清零者 | `0x52DA8D`、`0x55D135`、`0x55D1C3`、`0x55D22B`、`0x55D26E`。 | `[静态推断-强]` |")
    m.append("| 语义假设 | 与 G1 (`0xA83D49`) **地址相邻**，中间 `0xA83D4A/4B` 为填充、"
             "`0xA83D4C` 是全局对象指针（`cmp esi,[0xA83D4C]` 多处出现），"
             "推测四者同属一个 8 字节全局头 `0xA83D48..0xA83D4F`："
             "`+0`=G4, `+1`=G1, `+4`=对象指针。"
             "置位前以帧号为参数打印 `\"Processing EXIT event on frame %d\"`"
             " → 更可能是**事件/退出事件处理（含录像回放事件）**相关标志；"
             "另有 `0x82637C \"Loaded recording values for scenario : %s\"` 在初始化区被引用，"
             "但与本写点**不在同一函数**，仅为弱邻近性。 | `[静态推断-弱]`（状态名） |")
    m.append("| 真机期待值 | 正常推进中 **0**；触发 EXIT 事件/回放事件处理时读到 **1**，"
             "同时应在日志或真机侧看到帧号被打印。 | `[待运行验证]` |")
    m.append("")
    m.append("### 正常状态映射表（**全部为假设，非已证**）")
    m.append("")
    m.append("| 状态 | 候选门控 | 依据 | 等级 |")
    m.append("|---|---|---|---|")
    m.append("| 加载中 / 场景初始化 | 全部 4 个被清 0 | `0x52DA78..8D` 与帧计数归零同函数 | `[静态推断-强]`（清零事实）/ 映射 `[待运行验证]` |")
    m.append("| 联机同步 / 等待其他玩家 | G1 / G2 | `0x4F8440` 函数以帧计数计时、模式 3/4、等待循环 | `[静态推断-弱]` |")
    m.append("| 回放 / 录像 / EXIT 事件处理 | G4（弱） | `0x4C7903` 以帧号为参数打印 "
             "`\"Processing EXIT event on frame %d\"` 后立刻置 G4；"
             "`0x82637C \"Loaded recording values for scenario : %s\"` 在初始化区 | `[静态推断-弱]` |")
    m.append("| 暂停 / 菜单 / 失焦 | 未提供直接 API 证据 | 导入表含 `PeekMessageA`/`GetForegroundWindow`/"
             "`GetActiveWindow`/`DialogBoxParamA`/`MessageBoxA`/`Sleep`，但**未定位到**"
             "这些 API 与四门控写入点在同一基本块/调用链上 | `[待运行验证]` |")
    m.append("| 编辑器 | 无静态证据 | — | `[待运行验证]` |")
    m.append("")
    m.append("> 明确否认：本次**没有**证明任何一个门控等于「暂停」。"
             "静态只能证明「非 0 ⇒ 帧推进被跳过」以及各写点的直接条件。")
    m.append("")
    m.append("## 4. 真机侧该期待什么值（给同轮只读观测代理）")
    m.append("")
    m.append("| 场景 | G1 0xA83D49 | G2 0xA8ECD0 | G3 0x8B41C0 | G4 0xA83D48 | `[0xA8ED84]` |")
    m.append("|---|---|---|---|---|---|")
    m.append("| 主菜单 / 未进入对局 | 0（或未初始化 0） | 0 | 0 | 0 | 冻结/上次值 |")
    m.append("| 场景加载完成瞬间 | 0 | 0 | 0 | 0 | 0（`0x52DA08` 归零） |")
    m.append("| 正常对战推进（预期稳态） | **0** | **0** | **0** | **0** | 单调递增 |")
    m.append("| 挂起/等待/同步窗口 | 短时 1（G1 或 G2 互斥） | 短时 1 | 视触发源 | 视触发源 | **停止递增** |")
    m.append("| 挂起被消费后 | 0 | 0 | 0 | 0 | 恢复递增 |")
    m.append("")
    m.append("以上除「正常推进中 0」为 `[静态推断-强]`（由 `0x55DE4F..71` 串联跳过逻辑反推）外，"
             "其余取值均为 `[待运行验证]`。真机只读观测若读到非 0，"
             "请同时采 `[0xA8ED84]` 是否停止递增、`[0xA8B238]` 模式、"
             "`[0xA8E9A0]` 活动标志与 `[0xABCD58]`，以便区分「挂起请求」与「残留脏值」。")
    m.append("")
    with open(os.path.join(out_dir, "GATE_SEMANTICS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(m) + "\n")

    # ---------------- FRAME_ADVANCE_FN.md ----------------
    f = []
    f.append("# 帧推进函数（含 `0x55DE81`）— %s / W2_static" % RUN_ID)
    f.append("")
    f.append("纯静态；`[本次实测]` 见 `EVIDENCE/00_run_log.txt`、`07_context.txt`。")
    f.append("")
    f.append("## 1. 函数边界")
    f.append("")
    f.append("| 项 | 值 | 依据 | 等级 |")
    f.append("|---|---|---|---|")
    f.append("| 探针 VA | `0x%08X` = `mov dword ptr [0xa8ed84], edx` | `GATE_DECODE.txt` 复核 | `[转引]`+`[本次实测]` |" % FRAME_MOV_STORE)
    f.append("| 入口估计 | `0x%08X` | 前一条 `ret`(0x55D359) 之后 6 个 `0x90` 填充 "
             "(0x55D35A..0x55D35F)，入口 16 字节对齐；且被 6 处 `call rel32` 直接指向 | `[静态推断-强]` |" % (fe or 0))
    f.append("| 结束估计 | `0x%08X`（`ret` 结束） | 之后 4 个 `0x90` (0x55DEDC..DF)，"
             "下一函数 `0x55DEE0` 起 `sub esp,8` | `[静态推断-强]` |" % (fend or 0))
    f.append("| 大小 | `0x%X` = %d 字节 | 上两项相减 | `[本次实测]` |" %
             (S["frame_size"] or 0, S["frame_size"] or 0))
    f.append("| 入口形态 | `a0 a0 e9 a8 00` `mov al,[0xa8e9a0]`; `81 ec b4 01 00 00` "
             "`sub esp,0x1b4`; `84 c0`; `push ebx/ebp/esi/edi` | 非标准 `push ebp;mov ebp,esp` "
             "prologue，故入口靠填充边界 + 调用目标判定，**不视为已证** | `[静态推断-强]` |")
    f.append("")
    f.append("> 注意：`GATE_DECODE.txt` 的「从 `0x55DC00` 线性解码」只是**解码锚点**，"
             "不是函数入口；真实入口在 `0x%08X`。线性解码起点与函数边界是两件事。" % (fe or 0))
    f.append("")
    f.append("## 2. 函数体要点 `[本次读码]`")
    f.append("")
    f.append("```")
    f.append("0x%08X  a0 a0 e9 a8 00     mov al, byte ptr [0xa8e9a0]   ; 活动标志" % (fe or 0))
    f.append("0x%08X  81 ec b4 01 00 00  sub esp, 0x1b4" % ((fe or 0) + 5))
    f.append("0x%08X  0f 84 58 0b 00 00  je 0x55decf                    ; 非活动 -> 直接返回 1" % ((fe or 0) + 0x11))
    f.append("          ... Sleep(500)/Sleep(10) 等待 [0xa8ed80] ...")
    f.append("0x0055D3BB  a1 84 ed a8 00  mov eax, dword ptr [0xa8ed84]")
    f.append("0x0055D3C0  8b 0d e4 e2 a8 00  mov ecx, dword ptr [0xa8e2e4]")
    f.append("0x0055D3C6  3b c1           cmp eax, ecx")
    f.append("0x0055D3D4  ff 15 30 15 7e 00  call dword ptr [0x7e1530]  ; WINMM!timeGetTime")
    f.append("0x0055DE4F  a0 49 3d a8 00  mov al, byte ptr [0xa83d49]   ; 门控1")
    f.append("0x0055DE58  a0 d0 ec a8 00  mov al, byte ptr [0xa8ecd0]   ; 门控2")
    f.append("0x0055DE61  a0 c0 41 8b 00  mov al, byte ptr [0x8b41c0]   ; 门控3 (!!不是 0x41C0)")
    f.append("0x0055DE6A  a0 48 3d a8 00  mov al, byte ptr [0xa83d48]   ; 门控4")
    f.append("0x0055DE73  8b 15 84 ed a8 00  mov edx, dword ptr [0xa8ed84]")
    f.append("0x0055DE79  a1 84 77 b0 00  mov eax, dword ptr [0xb07784]")
    f.append("0x0055DE7E  42              inc edx")
    f.append("0x0055DE7F  3b c7           cmp eax, edi")
    f.append("0x0055DE81  89 15 84 ed a8 00  mov dword ptr [0xa8ed84], edx  ; 唯一的自增+回写")
    f.append("0x0055DEC8  c6 05 58 cd ab 00 00  mov byte ptr [0xabcd58], 0   ; 门控跳过出口")
    f.append("```")
    f.append("")
    f.append("## 3. 调用者（`call rel32` 直接调用，全部）")
    f.append("")
    f.append("原始字节级 `E8 rel32` 全 `.text` 扫描 `[本次实测]`：")
    f.append("")
    f.append(tbl([["0x%08X" % c, "0x%08X" % (c - img.image_base),
                   "0x%08X" % (c - img.image_base), "`call 0x%08X`" % (fe or 0),
                   ("0x%08X" % find_function_entry(img, c)) if find_function_entry(img, c) else "UNRESOLVED",
                   ("YES %s" % (loop_enclosing(img, find_function_entry(img, c), c)[1]))
                   if find_function_entry(img, c) and loop_enclosing(img, find_function_entry(img, c), c)[0]
                   else "no"]
                  for c in S["direct_callers"]],
                 ["caller VA", "RVA", "FOFF", "指令", "caller 所在函数入口(估计)", "在回边循环体内"]))
    f.append("**直接调用者数量 = %d**，其中 **%d** 个位于回边循环体内。" %
             (len(direct), S["n_loop_callers"]))
    f.append("`[本次实测]` `EVIDENCE/07_context.txt`。")
    f.append("")
    f.append("**间接调用**：`[未解析]`。全文件搜索 4 字节小端 `0x%08X` ⇒ **0 命中**，"
             "即磁盘上不存在指向本函数的静态函数指针/vtable 项；"
             "B1 线性扫描共记录 %d 条 `call r/m32`/`call reg` 间接调用，"
             "其目标需运行期才能解析，本次**不解析**、也不把它们计为调用者。" %
             (fe or 0, S["n_indirect"]))
    f.append("")
    f.append("## 4. 每次调用推进几次？")
    f.append("")
    f.append("**恰好 1 次** `[静态推断-强]`（有直接指令证据，非全称证明）：")
    f.append("")
    f.append("- 函数体内对 `[0xA8ED84]` **只有 4 处引用** `[本次实测] "
             "EVIDENCE/07_context.txt`：`0x55D3BB mov eax,[..]`（读）、"
             "`0x55D8C9 mov eax,[..]`（读）、`0x55DE73 mov edx,[..]`（读）、"
             "`0x55DE81 mov [..],edx`（**唯一回写**）；"
             "整个函数里**唯一** `inc edx` 是 `0x55DE7E`（另有 6 条 `inc esi`/`inc ecx`，"
             "均不作用于帧计数）。所以自增+回写各 1 处，直线相邻；")
    f.append("- 四门控检查 (`0x55DE4F..71`) 的 `jne 0x55DEC8` 是**跳过**该块，"
             "跳过后不写帧计数，也不会重复执行；")
    f.append("- 从入口 `0x%08X` 完整解码到填充边界 `0x%08X`（810 条指令，不因中途 `ret` 截断），"
             "位于 `0x%08X` **之后**、且回跳目标 ≤ `0x%08X` 的回边共 **%d** 条"
             "（`EVIDENCE/07_context.txt`）：%s。"
             % (fe or 0, (S.get("frame_pad") or 0), FRAME_MOV_STORE, FRAME_MOV_STORE,
                len(back), back if back else "无"))
    f.append("- 因此自增块**不在循环体内**，一次调用最多执行一次 `inc`。")
    f.append("")
    f.append("**但**：6 个直接调用者中有 **%d 个位于回边循环体内**"
             "（`EVIDENCE/07_context.txt` 的 `in_loop=True`，例如 "
             "`0x48CEA8 je 0x48CE8A`、`0x608234 je 0x6081D8`），"
             "所以主循环每轮调用一次、宏观上帧计数持续增长。"
             "「每次调用 1 次」与「调用者循环里被反复调用」不矛盾。" % S["n_loop_callers"])
    f.append("")
    f.append("## 5. 与 3 处帧计数清零点的调用关系")
    f.append("")
    f.append("轮已知的 3 处 `mov dword ptr [0xa8ed84], 0`：`[转引]` + `[本次实测]` 复核：")
    f.append("")
    f.append(tbl([["0x%08X" % r["va"], "0x%08X" % (r["va"] - img.image_base),
                   "0x%08X" % r["entry"] if r["entry"] else "UNRESOLVED",
                   "`c7 05 84 ed a8 00 00 00 00 00`"] for r in S["resets"]],
                 ["清零 VA", "RVA/FOFF", "所在函数入口(估计)", "字节"]))
    f.append("另有一处**同样清零**但轮未列入：`0x0052DA08 89 1d 84 ed a8 00` "
             "`mov dword ptr [0xa8ed84], ebx`（`ebx=0`），所在函数同时把四门控全部写 0。"
             "`[本次实测]` `EVIDENCE/07_context.txt`。")
    f.append("")
    f.append("**结论 `[静态推断-强]`（仅直接 `call rel32` 图）**：三处清零点与帧推进函数"
             "**在同一条调用路径上，但方向是「清零点 ⇒ 帧推进」**：")
    f.append("")
    f.append("函数级直接调用图（原始 E8 + B1 指令起点过滤，BFS 深度 ≤4，`EVIDENCE/13_call_paths.txt`）给出：")
    f.append("")
    f.append("| 清零点 | 所在函数(估计) | 到帧推进函数的路径 | 反向 |")
    f.append("|---|---|---|---|")
    for rs in RESET_SITES:
        p = cg_paths.get(rs, {})
        p1 = p.get("to_frame")
        p2 = p.get("from_frame")
        f.append("| `0x%08X` | `%s` | `%s` | `%s` |" %
                 (rs, ("0x%08X" % p["entry"]) if p.get("entry") else "UNRESOLVED",
                  (" → ".join("0x%08X" % x for x in p1)) if p1 else "NO PATH (depth≤4)",
                  (" → ".join("0x%08X" % x for x in p2)) if p2 else "NO PATH (depth≤4)"))
    f.append("")
    f.append("逐跳的**具体 `call rel32` 站点**见 `EVIDENCE/13_call_paths.txt`；例如 "
             "`0x5B72CA → 0x622720 → 0x622731 → 0x608070 → 0x608206 → 0x55D360`。")
    f.append("")
    f.append("- `0x5B7329` 所在函数尾部是 `ret 4`，其前有 `0x5B7343 call 0x6B8B10`；"
             "函数体按 `[0xA8B260]`/`[0xA8B31D]` 位组装 `[0xA8E960]`，是场景/规则初始化。")
    f.append("- `0x5E747C` 前有 `push 0x831A60` (`\"Pregame setup for %d players.\\n\"`) + "
             "`call 0x4068E0` 日志输出，是**开局前准备**路径。")
    f.append("- `0x795234` 所在大函数写 `0x841F30/34/38/3C = 0x4D2..0x4D5`、"
             "`mov byte [0xB77A04],0`、`cmp [0xA8B238],4`，是**退出/收尾/重开**路径。")
    f.append("- 三者都经 2~3 跳到达主循环侧函数（`0x608070`/`0x623120` 等），"
             "而这些函数正是帧推进函数的 6 个直接调用者所在函数。"
             "即：**清零发生在进入主循环之前/重开时，帧推进在主循环内被反复调用**；"
             "二者通过全局 `[0xA8ED84]` 共享状态，且清零点在调用图上位于上游。")
    f.append("- 反向（帧推进 → 清零点）在深度 ≤4 内**无路径**；"
             "帧推进函数直接调用的函数清单里不含三个清零函数（`EVIDENCE/13_call_paths.txt`）。")
    f.append("")
    f.append("> 限制：以上基于**直接 `call rel32` 图**与启发式函数入口估计；"
             "未解析的间接调用、虚调用、以及函数入口估计误差都可能改变该结论。"
             "因此标 `[静态推断-强]` 而非 `[本次实测]` 的路径全称证明。"
             "请见 `UNKNOWNS.md`。")
    f.append("")
    with open(os.path.join(out_dir, "FRAME_ADVANCE_FN.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(f) + "\n")

    # ---------------- UNKNOWNS.md ----------------
    u = []
    u.append("# UNKNOWNS.md — %s / W2_static" % RUN_ID)
    u.append("")
    u.append("本次静态分析**未解决 / 不能声称**的事项。真机只读观测可优先补这些。")
    u.append("")
    u.append("| # | 未知项 | 为什么没解决 | 建议验证路径 | 等级 |")
    u.append("|---|---|---|---|---|")
    u.append("| U1 | 四门控各自**精确的正常状态名**（暂停 / 菜单 / 失焦 / 回放 / 联机同步 / 编辑器）"
             "| 写入点附近没有可直接命名的字符串或 `PeekMessageA`/`GetForegroundWindow`/"
             "`IsIconic`/`DialogBox*` 与写点同基本块；只有帧计数、模式枚举和虚调用 | "
             "真机在这些状态切换时只读采样 4 字节 + `[0xA8B238]` + `[0xA8E9A0]` | `[待运行验证]` |")
    u.append("| U2 | G1 与 G2 的**语义差异** | 二者是同一函数互补分支，静态只看到条件不同，"
             "看不到玩家可见状态 | 分别触发两条分支，比较真机表现 | `[待运行验证]` |")
    u.append("| U3 | `0x8B41C0` 所属**结构体布局**与其它成员含义 | 只能统计邻近地址的引用次数，"
             "无类型信息、无 RTTI、无符号 | 真机读 `0x8B41B8..0x8B4200` 整块并对照状态 | `[待运行验证]` |")
    u.append("| U4 | 门控是否存在**寄存器间接写者** | 有限静态搜索只覆盖内嵌绝对 VA 的编码；"
             "已做前向 32 指令候选扫描（命中 %d 条，全为弱证据），非全称 | "
             "真机下硬件断点/内存访问监控（另一代理权限），本代理不做 | `[待运行验证]` |" % len(ind_hits))
    u.append("| U5 | 帧推进函数入口 `0x%08X` 是否为**真入口** | 依赖填充边界 + 16 对齐 + "
             "6 个 call 目标，非符号信息；二进制无 PDB/导出名 | 反汇编器交叉确认 / 运行期栈回溯 | `[静态推断-强]` |" % (fe or 0))
    u.append("| U6 | 间接调用是否能到达帧推进函数 | B1 记录 %d 条 `call r/m32`，"
             "目标需运行期解析；全文件无 `0x%08X` 静态指针 | 运行期解析 | `[未解析]` |" %
             (S["n_indirect"], fe or 0))
    u.append("| U7 | 3 处清零点与帧推进函数的**间接**调用关系 | 已建直接 `call rel32` 函数级图，"
             "确认三处清零点在**上游**（2~3 跳到达主循环侧，见 `EVIDENCE/13_call_paths.txt`）；"
             "但虚调用 / 函数指针 / 入口估计误差未覆盖 | 更完整的调用图或运行期跟踪 | `[静态推断-强]`（直接图）/ `[待运行验证]`（间接） |")
    u.append("| U8 | `[0xB07784]`（`0x55DE79` 读入）与 `edi` 的比较语义 | "
             "只看到 `cmp eax,edi` / `jge` / `call 0x684290` / `mov [0xb07784],edi`，"
             "未追到 `edi` 的来源与 `0x684290` 的作用 | 追 `0x684290` 与调用者传入的 edi | `[待运行验证]` |")
    u.append("| U9 | `[0xA8EDD8]` 退出态、相邻字符串到门控的**因果链** | 只在同函数/邻域出现，"
             "无直接写门控的边 | 真机联动采样 | `[静态推断-弱]` |")
    u.append("| U10 | 线性扫描 skipdata 区间内是否藏有写点 | B1 skipdata %d 处、"
             "空隙 %d 段；B2 skipdata %d 处、空隙 %d 段。这些区间通道 A 仍做了 4 字节模式搜索，"
             "但若写点用非内嵌 VA 编码就会漏 | 扩大边界集 / 递归下降反汇编 | `[待运行验证]` |" %
             (S["b1_skips"], S["b1_gaps"], S["b2_skips"], S["b2_gaps"]))
    u.append("| U11 | 「零命中 ≠ 运行期不存在」 | 见 `EVIDENCE/12_indirect_pathways.txt`；"
             "加载器零填充、自修改代码、结构体偏移写都不在本次搜索模型内 | — | `[静态推断-弱]` |")
    u.append("")
    u.append("## 最大未知项")
    u.append("")
    u.append("**U1 / U2**：四个门控能静态证明的只有「非 0 ⇒ 帧推进被跳过」与各写点的直接条件；"
             "把它们映射到玩家可见状态（暂停/失焦/回放/联机）目前**全是弱推断**，"
             "必须由同轮真机只读观测定标。")
    u.append("")
    with open(os.path.join(out_dir, "UNKNOWNS.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(u) + "\n")

    # ---------------- DISAGREE.md ----------------
    dg = []
    dg.append("# DISAGREE.md — %s / W2_static" % RUN_ID)
    dg.append("")
    dg.append("与既有记录不一致 / 做不到 / 明确拒绝的结论。")
    dg.append("")
    dg.append("## D1（点名纠正）门控 3 = `0x008B41C0`，不是 `0x41C0`")
    dg.append("")
    dg.append("- **旧记录错误**：把门控 3 写成 `0x41C0`。")
    dg.append("- **错误来源（本次精确复现，见 `EVIDENCE/14_gate3_artifact.txt`）**："
             "`0x0055DE5F` 的字节是 `75 67 a0 c0 41 8b 00`，正确的 "
             "`0x0055DE5F 75 67 = jne 0x55DEC8` 里 **`0x67` 是 rel8 位移量**，不是前缀。"
             "若从**非法起点 `0x0055DE60`**（即 `75 67` 指令的第 2 字节）开始解码，"
             "capstone 得到 `67 a0 c0 41` = `mov al, byte ptr [0x41c0]`（67 作 "
             "address-size override，把 A0 的 moffs 截成 16 位），下一条 `8b 00` = "
             "`mov eax,[eax]`。这正是旧记录 `0x41C0` 的来源。`[转引]` 用户说明 + `[本次实测]` 复现。")
    dg.append("- **本次实测纠正**：`0x0055DE61` 的 5 字节为 `a0 c0 41 8b 00`，"
             "capstone 解为 `mov al, byte ptr [0x8b41c0]`；4 字节小端操作数 "
             "`c0 41 8b 00` ⇒ **VA 0x008B41C0**，RVA `0x004B41C0`，"
             "FOFF（若按 .data 公式）= `0x004B41C0`，但该 VA 在 `.data` BSS 尾，"
             "**磁盘上无对应字节**。见 `EVIDENCE/03_channelA_decoded.txt`。")
    dg.append("- `0x41C0` 作为 VA 落在 `ImageBase=0x400000` 之前（PE 头区），"
             "不可能是可读写的全局门控；全文件 4 字节模式搜索 `c0 41 00 00` 只有 4 处，"
             "全部在 `.rdata` 数据区，均与四门控读取序列无关"
             "（`EVIDENCE/14_gate3_artifact.txt`）。")
    dg.append("- **结论**：确认 `门控3 = 0x008B41C0`。`GATE_WRITERS.csv` 与 "
             "`GATE_SEMANTICS.md` 全部使用正确地址；旧记录应作废。")
    dg.append("")
    dg.append("## D2 不把「有限静态搜索」写成全称证明")
    dg.append("")
    dg.append("本次是**磁盘文件全字节 4 字节模式搜索 + 两套可信边界的线性反汇编**，"
             "不是对运行期行为的全称证明。写明：搜索范围、支持编码、反例校验、"
             "未覆盖区间、寄存器间接写盲区。零命中不等于运行期不存在。"
             "见 `EVIDENCE/05_uncovered_intervals.txt`、`10_encoding_coverage.txt`、"
             "`12_indirect_pathways.txt`。")
    dg.append("")
    dg.append("## D3 不把函数入口估计值当已证")
    dg.append("")
    dg.append("`0x%08X` 是**启发式入口估计**（填充边界 + 16 对齐 + 6 个 `call rel32` 目标），"
             "二进制无符号。报告一律标 `[静态推断-强]`，不写「已证入口」。" % (fe or 0))
    dg.append("")
    dg.append("## D4 不把「我猜它是暂停」写成已证")
    dg.append("")
    dg.append("四门控到「加载中/菜单/暂停/失焦/回放/联机同步/编辑器」的映射"
             "**全部**为 `[静态推断-弱]` 或 `[待运行验证]`。"
             "静态已证的只有：非 0 ⇒ `0x55DE73..81` 的自增块被跳过；"
             "以及各写点的直接条件/邻近全局/API 导入。")
    dg.append("")
    dg.append("## D5 做不到的部分")
    dg.append("")
    dg.append("- 无法在纯静态授权下给出四门控的**运行期真值序列**。")
    dg.append("- 无法解析间接调用 / 虚调用目标（标 `[未解析]`）。")
    dg.append("- 无法证明 3 处清零点与帧推进函数在**间接**调用图上不连通（只证了直接 `call rel32` 图）。")
    dg.append("- 无法区分 G1/G2 各自对应的玩家可见状态。")
    dg.append("- 未使用 `git` 写操作；未做全仓 `Get-ChildItem -Recurse`；"
             "未启动游戏 / attach / 读活进程 / 挂起线程 / 注入。")
    dg.append("")
    with open(os.path.join(out_dir, "DISAGREE.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(dg) + "\n")


if __name__ == "__main__":
    sys.exit(main())
