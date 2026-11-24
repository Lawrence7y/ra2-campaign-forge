#!/usr/bin/env python3
"""Baseline + 停机核验 for S19-K2. Independent of card claims except expected constants."""
import os, struct
import pefile
from capstone import *
from capstone.x86 import *

ROOT = r'D:\Project\ra2-campaign-forge'
EXE = os.path.join(ROOT, r'ra2youli\gamemd.exe')
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
# .text section
text = None
for s in pe.sections:
    if s.Name.rstrip(b'\0') == b'.text':
        text = s
        break
TSTART = IB + text.VirtualAddress
TEND = TSTART + text.Misc_VirtualSize
data = open(EXE,'rb').read()
raw = pe.get_data(text.VirtualAddress, text.Misc_VirtualSize)
print(f'ImageBase=0x{IB:X} .text VA=[0x{TSTART:X},0x{TEND:X}) rawlen={len(raw)}')

# --- 停机核验 1: PlayGlobal 0x750920 call sites, byte-level E8 rel32 scan ---
TARGET = 0x750920
sites = []
for i in range(len(raw)-4):
    if raw[i] == 0xE8:
        rel = struct.unpack_from('<i', raw, i+1)[0]
        va = TSTART + i
        if va + 5 + rel == TARGET:
            sites.append(va)
print(f'[CHECK] PlayGlobal 0x750920 call sites (byte E8 rel32) = {len(sites)} (expect 116)')

# capstone sweep (skipdata=True) independent count
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
insn_count = 0
cs_sites = set()
for ins in md.disasm(raw, TSTART):
    insn_count += 1
    if ins.id == X86_INS_CALL:
        op = ins.op_str
        # capstone formats direct call target as '0x750920'
        if op.strip().lower().lstrip('0x') == '750920' or op.strip() == '0x750920':
            cs_sites.add(ins.address)
print(f'[CHECK] capstone total insns={insn_count} call sites to 0x750920={len(cs_sites)} (byte∩cap={len(cs_sites & set(sites))})')

# --- 停机核验 2: VocClass 0x148 ---
def rd(va, n):
    off = va - IB
    return data[off:off+n]
b = rd(0x4063F0, 16)
print(f'[CHECK] bytes @0x4063F0 = {b.hex()}  (expect push 0x148 = 68 48 01 00 00 near 0x4063F5)')
# search B8 48 01 00 00 C3 globally in .text
pat = bytes.fromhex('B848010000C3')
hits = []
i = 0
while True:
    j = raw.find(pat, i)
    if j < 0: break
    hits.append(TSTART+j); i = j+1
print(f'[CHECK] B8 48 01 00 00 C3 in .text = {len(hits)} @ {[hex(x) for x in hits]} (audio-family 0x74AB10 expected among them)')

# --- 停机核验 3: volume absolute addresses 0xA8EB98/9C/A0 ---
for va in (0xA8EB98,0xA8EB9C,0xA8EBA0):
    # find section
    sec = None
    for s in pe.sections:
        if IB+s.VirtualAddress <= va < IB+s.VirtualAddress+s.Misc_VirtualSize:
            sec = s.Name.rstrip(b'\0').decode(); break
    print(f'[CHECK] volume addr 0x{va:X} in section {sec}')

# --- baseline: morph patterns are NOT specific ---
# B8 imm32 C3 total
cnt_b8c3 = 0; cnt_b8 = 0
for ins in md.disasm(raw, TSTART):
    if ins.bytes[:1] == b'\xB8':
        cnt_b8 += 1
        if len(ins.bytes) == 6 and ins.bytes[5:6] == b'\xC3':
            cnt_b8c3 += 1
print(f'[BASELINE] B8 imm32 C3 (6B) count = {cnt_b8c3}; B8 imm32 (any tail) = {cnt_b8}')
# ret 0xC / other morphs
cnt_c3 = sum(1 for ins in md.disasm(raw,TSTART) if ins.bytes[:1]==b'\xC3')
print(f'[BASELINE] bare ret (C3) count = {cnt_c3}')
