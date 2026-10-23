#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V-001 part 2: fixed CFG walk + phantom-E8 measurement + string rescan.
Independent of re_atlas/tools/*. Read-only."""
import re, json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_OP_IMM, X86_INS_PUSH

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
raw = open(EXE, 'rb').read()
pe = pefile.PE(data=raw)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    n = s.Name.rstrip(b'\0').decode()
    secs[n] = (base + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
tex_va, tex_sz, tex_off, tex_rsz = secs['.text']
tex_end = tex_va + tex_sz
entry = base + pe.OPTIONAL_HEADER.AddressOfEntryPoint

def va2off(va):
    for n, (v, z, o, z2) in secs.items():
        if v <= va < v + max(z, z2):
            return o + (va - v)
    return None

def read_va(va, ln):
    o = va2off(va)
    return raw[o:o+ln] if o is not None else None

# ---- full linear decode of .text ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
insn_at = {}
size_at = {}
addr = tex_va
tb = raw[tex_off:tex_off+tex_rsz]
# decode all at once in chunks via capstone disasm over the buffer
for ins in md.disasm(tb, tex_va):
    if ins.address >= tex_end:
        break
    insn_at[ins.address] = ins
    size_at[ins.address] = ins.size
print("aligned insns:", len(insn_at))

# E8/E9 from aligned decode
e8_t, e9_t = set(), set()
for a, ins in insn_at.items():
    bs = ins.bytes
    if ins.id == X86_INS_CALL and bs[0] == 0xE8 and len(bs) == 5:
        e8_t.add(a + 5 + int.from_bytes(bs[1:5], 'little', signed=True))
    elif ins.id == X86_INS_JMP and bs[0] == 0xE9 and len(bs) == 5:
        e9_t.add(a + 5 + int.from_bytes(bs[1:5], 'little', signed=True))

# naive scan (byte-level)
e8_n, e9_n = set(), set()
for m in re.finditer(b'\xe8', tb):
    i = m.start()
    t = tex_va + i + 5 + int.from_bytes(tb[i+1:i+5], 'little', signed=True)
    if tex_va <= t < tex_end: e8_n.add(t)
for m in re.finditer(b'\xe9', tb):
    i = m.start()
    t = tex_va + i + 5 + int.from_bytes(tb[i+1:i+5], 'little', signed=True)
    if tex_va <= t < tex_end: e9_n.add(t)
print("aligned E8/E9:", len(e8_t), len(e9_t), " naive:", len(e8_n), len(e9_n))
print("naive-only (phantom) E8:", len(e8_n - e8_t), " E9:", len(e9_n - e9_t))

# instruction-boundary coverage for phantom check
# mark aligned insn starts
starts = set(insn_at)
# phantom targets = in e8_n but not a decode start
ph = sorted(e8_n - e8_t)
not_start = sum(1 for t in ph if t not in starts)
print("phantom targets that are NOT aligned insn starts:", not_start, "/", len(ph))

# ---- .rdata vtable runs (>=4 consecutive dwords into .text), targets union
v, z, o, z2 = secs['.rdata']
rb = raw[o:o+z2]
vt_t = set()
i = 0
while i + 4 <= len(rb):
    dw = int.from_bytes(rb[i:i+4], 'little')
    if tex_va <= dw < tex_end:
        j = i
        while j + 4 <= len(rb) and tex_va <= int.from_bytes(rb[j:j+4], 'little') < tex_end:
            j += 4
        if (j - i) // 4 >= 4:
            k = i
            while k < j:
                vt_t.add(int.from_bytes(rb[k:k+4], 'little')); k += 4
        i = j
    else:
        i += 4
print("vtable(.rdata run>=4) targets:", len(vt_t))

roots_call = e8_n | vt_t | {entry}
print("LOWER (naive-roots union):", len(roots_call), " claim 13,352")

# ---- CFG walk with fixed logic ----
covered = set()
def is_covered(t): return t in covered
walked = set()
def body_of(head):
    if head in walked: return
    walked.add(head)
    stack = [head]
    seen = set()
    while stack:
        cur = stack.pop()
        while True:
            if cur in covered:
                break  # already assigned
            ins = insn_at.get(cur)
            if ins is None:
                break
            covered.add(cur)
            m = ins.mnemonic
            bs = ins.bytes
            nxt = cur + ins.size
            if m == 'ret' or m == 'retf':
                break
            if m == 'call':
                if bs[0] == 0xE8 and len(bs) == 5:
                    t = cur + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
                    if tex_va <= t < tex_end and t not in walked:
                        stack.append(t)
                cur = nxt; continue
            if m == 'jmp':
                if bs[0] == 0xE9 and len(bs) == 5:
                    t = cur + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
                    if tex_va <= t < tex_end: stack.append(t)
                    break
                if bs[0] == 0xEB:
                    t = cur + 2 + int.from_bytes(bs[1:2], 'little', signed=True)
                    stack.append(t); break
                break  # indirect jmp: stop
            if m[0] == 'j':
                if ins.operands and ins.operands[0].type == X86_OP_IMM:
                    t = ins.operands[0].imm
                    if tex_va <= t < tex_end: stack.append(t)
                cur = nxt; continue
            if m in ('leave', 'int3', 'hlt'):
                break
            cur = nxt
for r in sorted(roots_call):
    body_of(r)
print("covered:", len(covered), " claim fn_walk found 0 new entries:",
      "walked heads =", len(walked), " roots =", len(roots_call))
new_heads = walked - roots_call
print("new entry heads via walk (tailcall etc):", len(new_heads))

e9_in_cov = {t for t in e9_n if t in covered}
print("E9 naive targets in covered:", len(e9_in_cov), " claim 1,445")

# ---- UPPER heads: ret + >=2 fillers + prologue, not in covered, not in roots_call ----
PRO_RE = re.compile(rb'^(?:558bec|83ec|81ec|53|56|57|8bff|6a)')
heads = set()
for a in sorted(starts):
    if a in covered or a in roots_call:
        continue
    hb = read_va(a, 4) or b''
    if not PRO_RE.match(hb):
        continue
    b8 = read_va(a - 8, 8) or b''
    k = 7; fill = 0
    while k >= 0 and b8[k] in (0x90, 0xCC):
        fill += 1; k -= 1
    if fill >= 2 and k >= 0 and b8[k] == 0xC3:
        heads.add(a)
print("UPPER add (reachable-gated):", len(heads), " claim 890")
print("UPPER total:", len(roots_call) + len(heads), " claim 14,242")
# anchor check
print("anchor 0x403A80 in roots:", 0x403A80 in roots_call, " in covered:", 0x403A80 in covered, " in heads:", 0x403A80 in heads)
print("anchor bytes:", read_va(0x403A80, 8).hex())
print("anchor prev 8:", read_va(0x403A80-8, 8).hex())

# 4-way zero-reference recheck for anchor
def referenced(t, s):
    return t in s
print("anchor e8:", 0x403A80 in e8_n, " e9:", 0x403A80 in e9_n, " vt:", 0x403A80 in vt_t)
# data-pointer check
def any_data_ptr_to(t):
    for nm in ('.rdata', '.data'):
        v2, z2b, o2, o2s = secs[nm]
        b2 = raw[o2:o2+o2s]
        for k in range(0, len(b2)-3, 4):
            if int.from_bytes(b2[k:k+4], 'little') == t:
                return hex(v2 + k)
    return None
print("anchor dword ptr:", any_data_ptr_to(0x403A80))

# ---- strings with suffix tolerance ----
def strings_in(name):
    v2, z2b, o2, o2s = secs[name]
    b2 = raw[o2:o2+o2s]
    out = []
    i = 0
    n = len(b2)
    while i < n:
        if b2[i] == 0:
            i += 1; continue
        j = i
        while j < n and 32 <= b2[j] < 127:
            j += 1
        if j < n and b2[j] == 0:
            s = b2[i:j].decode('ascii')
            out.append((v2+i, s))
        i = j + 1
    return out

allstr = strings_in('.rdata') + strings_in('.data')
pure = [(va, s) for va, s in allstr if re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*$', s)]
loose = [(va, s) for va, s in allstr if re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*', s)
         and (va, s) not in pure]
print("pure Class::Method:", len(pure), " claim 5")
for va, s in pure: print("  ", hex(va), s)
print("loose (prefix):", len(loose), " claim 30")
methods = set()
for va, s in loose:
    m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*)', s)
    if m: methods.add(m.group(1))
print("distinct methods:", len(methods), " claim 21")

# push-imm32 sites referencing any of these
targets = {va for va, s in pure} | {va for va, s in loose}
push_sites = []
for a, ins in insn_at.items():
    bs = ins.bytes
    if ins.id == X86_INS_PUSH and bs[0] == 0x68 and len(bs) == 5:
        t = int.from_bytes(bs[1:5], 'little')
        if t in targets:
            push_sites.append((a, t))
print("push sites:", len(push_sites), " claim 35")
