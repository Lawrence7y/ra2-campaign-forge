#!/usr/bin/env python3
"""R132 independent cross-checks: second implementation of CFG walk, masked scan, call scan."""
import hashlib
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_SZ = min(t.Misc_VirtualSize, t.SizeOfRawData)
raw = open(EXE, "rb").read()
CODE = raw[t.PointerToRawData:t.PointerToRawData + TEXT_SZ]
TEXT_END = TEXT_VA + TEXT_SZ

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

# ---- cross-check 1: iterative worklist CFG using md.disasm_lite, different successor code
COND = set(b"o")  # placeholder


def is_cond(m):
    return m in ("jo","jno","js","jns","je","jz","jne","jnz","jb","jnae","jc","jnb","jae",
                 "jnc","jbe","jna","ja","jnbe","jl","jnge","jge","jnl","jle","jng","jg",
                 "jnle","jp","jpe","jnp","jpo","jcxz","jecxz","loop","loope","loopne")


def cfg(entry):
    visited = []          # (addr, mnem, ops, size)
    stack = [entry]
    done = set()
    hi = entry
    while stack:
        a = stack.pop()
        if a in done or not (TEXT_VA <= a < TEXT_END):
            continue
        done.add(a)
        for addr, size, mnem, ops in md.disasm_lite(bytes(CODE[a - TEXT_VA:a - TEXT_VA + 16]), a, 1):
            visited.append((addr, mnem, ops, size))
            break
        else:
            continue
        hi = max(hi, a + size)
        if mnem.startswith("ret"):
            continue
        if mnem in ("jmp", "ljmp"):
            try:
                stack.append(int(ops.split()[-1], 16))
            except ValueError:
                pass
            continue
        if is_cond(mnem):
            try:
                stack.append(int(ops.split()[-1], 16))
            except ValueError:
                pass
            stack.append(a + size)
            continue
        stack.append(a + size)
    return hi, visited


for name, va in (("A", 0x6BEDB0), ("B", 0x41C250)):
    hi, vis = cfg(va)
    lin = 0
    a = va
    while True:
        got = None
        for addr, size, mnem, ops in md.disasm_lite(bytes(CODE[a - TEXT_VA:a - TEXT_VA + 16]), a, 1):
            got = (size, mnem)
            break
        if got is None:
            break
        lin += got[0]
        a += got[0]
        if got[1].startswith("ret"):
            break
    print("xcheck CFG %s: cfg_len=%d first_ret_len=%d visited=%d max_end=%#x"
          % (name, hi - va, lin, len(vis), hi))

# ---- cross-check 2: masked scan by explicit byte compare (no regex)
A = 0x6BEDB0
L = 136
body = CODE[A - TEXT_VA:A - TEXT_VA + L]
MASKOFF = {34, 35, 36, 37, 78, 79, 80, 81, 112, 113, 114, 115}


def scan_masked(pat, maskoff):
    hits = []
    n = len(pat)
    fixed = [(i, pat[i]) for i in range(n) if i not in maskoff]
    for s in range(0, len(CODE) - n + 1):
        ok = True
        for i, b in fixed:
            if CODE[s + i] != b:
                ok = False
                break
        if ok:
            hits.append(TEXT_VA + s)
    return hits


h = scan_masked(body, MASKOFF)
print("xcheck masked hits (byte-compare impl):", [hex(x) for x in h])

pat1 = bytearray(body); pat1[5] = 0xFF
print("xcheck ctrl off5=0xff:", len(scan_masked(bytes(pat1), MASKOFF)))
pat2 = bytearray(body); pat2[34] ^= 0xFF
print("xcheck ctrl first-mask-flip:", [hex(x) for x in scan_masked(bytes(pat2), MASKOFF)])
print("xcheck plain:", [hex(x) for x in scan_masked(body, set())])

# ---- cross-check 3: call sites via capstone linear sweep of whole .text
targets = {0x6BEDB0, 0x41C250}
found = {t: [] for t in targets}
for ins in md.disasm(CODE, TEXT_VA):
    if ins.mnemonic in ("call", "jmp"):
        try:
            v = int(ins.op_str, 16)
        except ValueError:
            continue
        if ins.mnemonic == "call" and v in targets:
            found[v].append(hex(ins.address))
for k, v in found.items():
    print("xcheck capstone call-rel32 -> %#x: n=%d %s" % (k, len(v), v))

# capstone also catches call via 0xe8 only when linear sweep is aligned; count e8 bytes seen
print("xcheck done")
