#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ds audit: independent image/VA layer. Index 0 == ImageBase 0x400000."""
from __future__ import annotations
import hashlib
from pathlib import Path
import pefile

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
BASE = 0x400000
EXP_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

PE = pefile.PE(str(EXE), fast_load=True)
RAW = bytes(PE.__data__)
IMG = bytes(PE.get_memory_mapped_image())   # index 0 == ImageBase


class Sec:
    def __init__(self, s):
        self.name = s.Name.decode("latin1").rstrip("\x00")
        self.va = BASE + s.VirtualAddress
        self.vsize = s.Misc_VirtualSize
        self.raw = s.PointerToRawData
        self.rsize = s.SizeOfRawData
        self.ch = s.Characteristics
        self.exec = bool(self.ch & 0x20000000)
        self.wr = bool(self.ch & 0x80000000)
        self.vend = self.va + max(self.vsize, self.rsize)

    def __repr__(self):
        return (f"<{self.name} va=0x{self.va:08X} vsize=0x{self.vsize:X} "
                f"raw=0x{self.raw:X} rsize=0x{self.rsize:X} exec={self.exec}>")


SECS = [Sec(s) for s in PE.sections]


def sha_ok() -> bool:
    return hashlib.sha256(RAW).hexdigest().upper() == EXP_SHA


def sec_of(va: int):
    for s in SECS:
        if s.va <= va < s.vend:
            return s
    return None


def in_raw(va: int) -> bool:
    """True only if va has FILE BYTES (BSS / beyond-raw => False)."""
    s = sec_of(va)
    if s is None:
        return False
    return (va - s.va) < s.rsize and (va - s.va) < s.vsize


def is_exec(va: int) -> bool:
    s = sec_of(va)
    return bool(s and s.exec)


def u8(va):
    if not in_raw(va):
        return None
    return IMG[va - BASE]


def u32(va):
    if not in_raw(va) or not in_raw(va + 3):
        return None
    o = va - BASE
    return int.from_bytes(IMG[o:o + 4], "little")


def u16(va):
    if not in_raw(va) or not in_raw(va + 1):
        return None
    o = va - BASE
    return int.from_bytes(IMG[o:o + 2], "little")


def rd(va, n):
    o = va - BASE
    if o < 0 or o + n > len(IMG):
        return None
    return IMG[o:o + n]


def cstr(va, maxlen=200):
    if not in_raw(va):
        return None
    o = va - BASE
    e = IMG.find(b"\x00", o, o + maxlen)
    if e < 0:
        return None
    return IMG[o:e]


def secname(va):
    s = sec_of(va)
    if s is None:
        return "<unmapped>"
    if not in_raw(va):
        return s.name + ".bss"
    return s.name
