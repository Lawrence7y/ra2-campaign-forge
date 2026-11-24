"""P0-METHOD 公共库（只读目标镜像；不依赖 atlas 的 entry+size 做任何判据）。

纪律对齐（R14_COMMON.md）：
- §6 纪律 1：双通道至少一条不依赖 function_atlas 的 entry+size —— 本库所有通道均自写，atlas 只在正对照里被当"已知入口清单"读一次。
- §6 纪律 2：capstone 必须 skipdata=True。
- §6 纪律 3：边界判定超限必须返回 unknown（None），不得返 False。
- §8.1 ②：jmp32 不当真入口 —— 通道 A 把 E8 与 E9 分开统计。
- §8.1 ⑥：边界判据不得"全 True / 零超限"混过去 —— 每个判据都报命中数与失败原因分桶。
- §8.1 ㉖：报告扫描规模必须给"覆盖 .text 的百分比"，且交付站点必须落在自报覆盖范围内。
- §8.1 ⑦：虚表定界必须从 .rdata 的 COL / vtable[-1] 做，不得用 atlas 函数边界反推。
- §8.2 ⑦ + §8.2.1 ⑧：COL 在 vt-4；TD+8 是内联 ASCII 名串（不是指针）。
"""
import hashlib
import os
import struct

import capstone
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = os.path.join(ROOT, "ra2youli", "gamemd.exe")
R14 = os.path.join(ROOT, "lead", "next_re_20261117_r14")
ENUM = os.path.join(R14, "P0_RESIDUAL_2", "ENUM.tsv")
COVERAGE = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RESIDUAL_ADJ = os.path.join(R14, "P0_RESIDUAL", "RESIDUAL_ADJUDICATION.tsv")
HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)
EVIDENCE = os.path.join(CARD, "EVIDENCE")

EXPECT_SHA_PRE = "73201CC0"
EXPECT_SHA_SUF = "F67476"


class Image:
    def __init__(self, path=TARGET):
        self.path = path
        with open(path, "rb") as f:
            self.blob = f.read()
        self.sha256 = hashlib.sha256(self.blob).hexdigest().upper()
        self.size = len(self.blob)
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.rstrip(b"\x00").decode("latin-1")
            self.sections.append(
                dict(
                    name=name,
                    va=self.image_base + s.VirtualAddress,
                    vsize=s.Misc_VirtualSize,
                    raw_off=s.PointerToRawData,
                    raw_size=s.SizeOfRawData,
                )
            )
        self.text = self.by_name(".text")
        self.rdata = self.by_name(".rdata")
        self.data = self.by_name(".data")
        self.text_start = self.text["va"]
        self.text_end = self.text["va"] + self.text["vsize"]

    def by_name(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def sec_of(self, va):
        for s in self.sections:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["raw_size"]):
                return s
        return None

    def off(self, va):
        s = self.sec_of(va)
        if s is None:
            return None
        d = va - s["va"]
        if d >= s["raw_size"]:
            return None  # 未初始化尾部（.bss 类）
        return s["raw_off"] + d

    def read(self, va, n):
        o = self.off(va)
        if o is None or o + n > len(self.blob):
            return None
        return self.blob[o:o + n]

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]

    def bytes_hex(self, va, n):
        b = self.read(va, n)
        if b is None:
            return ""
        return " ".join(f"{x:02X}" for x in b)

    def in_text(self, va):
        return self.text_start <= va < self.text_end


def load_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def norm_addr(s):
    s = s.strip().upper()
    if s.startswith("0X"):
        s = s[2:]
    s = s.lstrip("0") or "0"
    return s.rjust(8, "0")


def new_md():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    return md
