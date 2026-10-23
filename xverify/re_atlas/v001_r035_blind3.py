#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V-001 part 3 (corrected): independent blind recompute of R-035.
Fixes vs part2: resync decoder; PROTO_RE byte-pattern bug (was ASCII);
string scan tolerant of trailing \\n; wider ret lookback; phantom-E8 audit.
Read-only. Independent of re_atlas/tools/*."""
import re, json, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_INS_JMP, X86_INS_PUSH, X86_OP_IMM

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
raw = open(EXE, 'rb').read()
assert hashlib.sha256(raw).hexdigest() == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
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

# ---- resync linear decode of .text ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
insn_at = {}
starts_by_off = bytearray(tex_rsz)  # 1 if aligned insn start
addr = tex_va
tb = raw[tex_off:tex_off+tex_rsz]
while addr < tex_end:
    off = addr - tex_va
    b = tb[off:off+15]
    if not b:
        break
    got = None
    for ins in md.disasm(b, addr):
        got = ins
        break
    if got is None:
        addr += 1
        continue
    insn_at[got.address] = got
    starts_by_off[got.address - tex_va] = 1
    addr += got.size
print("resync insns:", len(insn_at))

# aligned E8/E9 target sets
e8_t, e9_t = set(), set()
e8_sites, e9_sites = {}, {}
for a, ins in insn_at.items():
    bs = ins.bytes
    if ins.id == X86_INS_CALL and bs[0] == 0xE8 and len(bs) == 5:
        t = a + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
        e8_t.add(t); e8_sites.setdefault(t, []).append(a)
    elif ins.id == X86_INS_JMP and bs[0] == 0xE9 and len(bs) == 5:
        t = a + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
        e9_t.add(t); e9_sites.setdefault(t, []).append(a)
e8_t = {t for t in e8_t if tex_va <= t < tex_end}
e9_t = {t for t in e9_t if tex_va <= t < tex_end}

# naive scan sets
e8_n, e9_n = set(), set()
for m in re.finditer(b'\xe8', tb):
    i = m.start()
    if i + 5 <= tex_rsz:
        t = tex_va + i + 5 + int.from_bytes(tb[i+1:i+5], 'little', signed=True)
        if tex_va <= t < tex_end: e8_n.add(t)
for m in re.finditer(b'\xe9', tb):
    i = m.start()
    if i + 5 <= tex_rsz:
        t = tex_va + i + 5 + int.from_bytes(tb[i+1:i+5], 'little', signed=True)
        if tex_va <= t < tex_end: e9_n.add(t)
print("aligned E8/E9:", len(e8_t), len(e9_t), " naive:", len(e8_n), len(e9_n))
ph_e8 = e8_n - e8_t
ph_e9 = e9_n - e9_t
print("phantom E8 targets:", len(ph_e8), " phantom E9:", len(ph_e9))

# audit phantoms: are they targets produced by real E8 whose encoding is
# not 0xE8+rel32 (e.g. capstone mis-decode)? or purely operand bytes?
# For each phantom, check 2-byte before: does 0xE8 sit at an aligned insn start?
ph_site_is_start = 0
ph_site_operand = 0
ph_site_unaligned = 0
for t in ph_e8:
    found = False
    for m in re.finditer(b'\xe8', tb[t-tex_va-5 if t-tex_va>5 else 0 : ]):
        pass
    # simpler: iterate naive matches again for this target
# faster: recompute sites for phantoms
naive_sites = {}
for m in re.finditer(b'\xe8', tb):
    i = m.start()
    if i + 5 <= tex_rsz:
        t = tex_va + i + 5 + int.from_bytes(tb[i+1:i+5], 'little', signed=True)
        if tex_va <= t < tex_end and t in ph_e8:
            naive_sites.setdefault(t, []).append(i)
for t, sites in naive_sites.items():
    kinds = set()
    for i in sites:
        addr_of_match = tex_va + i
        # is the matching 0xE8 byte inside an aligned instruction (not its start)?
        ins = insn_at.get(addr_of_match)
        if ins is not None and ins.id == X86_INS_CALL:
            kinds.add('aligned-call-diff')
        elif addr_of_match in insn_at:
            kinds.add('start-not-call')
        else:
            # find containing instruction
            # walk back up to 15 bytes
            k = addr_of_match
            while k >= tex_va and starts_by_off[k - tex_va] == 0:
                k -= 1
            cont = insn_at.get(k)
            if cont is not None and k < addr_of_match < k + cont.size:
                kinds.add('operand-byte')
            else:
                kinds.add('undecoded-region')
    if 'operand-byte' in kinds and len(kinds) == 1:
        ph_site_operand += 1
    else:
        ph_site_unaligned += 1
print(f"phantom E8: pure operand-byte sites = {ph_site_operand}, other = {ph_site_unaligned}")

# ---- CFG walk ----
def make_roots(e8s, vt):
    return e8s | vt | {entry}

# vtable: runs >=4 consecutive .text dwords in .rdata
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
print("vt(.rdata run>=4):", len(vt_t))

for label, roots in (("naive", make_roots(e8_n, vt_t)), ("aligned", make_roots(e8_t, vt_t))):
    covered = set()
    new_entries = set()
    def body_of(head):
        stack = [head]
        while stack:
            cur = stack.pop()
            while True:
                if cur in covered:
                    break
                ins = insn_at.get(cur)
                if ins is None:
                    break
                covered.add(cur)
                m = ins.mnemonic
                bs = ins.bytes
                nxt = cur + ins.size
                if m in ('ret', 'retf'):
                    break
                if m == 'call':
                    if bs[0] == 0xE8 and len(bs) == 5:
                        t = cur + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
                        if tex_va <= t < tex_end and t not in roots:
                            new_entries.add(t)
                    cur = nxt
                    continue
                if m == 'jmp':
                    if bs[0] == 0xE9 and len(bs) == 5:
                        t = cur + 5 + int.from_bytes(bs[1:5], 'little', signed=True)
                        if tex_va <= t < tex_end:
                            stack.append(t)
                        break
                    if bs[0] == 0xEB:
                        stack.append(cur + 2 + int.from_bytes(bs[1:2], 'little', signed=True))
                        break
                    break
                if m[0] == 'j':
                    if ins.operands and ins.operands[0].type == X86_OP_IMM:
                        t = ins.operands[0].imm
                        if tex_va <= t < tex_end:
                            stack.append(t)
                    cur = nxt
                    continue
                if m in ('leave', 'int3', 'hlt'):
                    break
                cur = nxt
    real_roots = set(roots)
    for r in sorted(real_roots):
        body_of(r)
    print(f"[{label}] roots={len(roots)} covered={len(covered)} new_entries_via_call={len(new_entries)}")
    globals()[f'cov_{label}'] = covered

cov_naive = cov_naive
e9_in_cov_n = {t for t in e9_n if t in cov_naive}
e9_in_cov_a = {t for t in e9_t if t in cov_aligned}
print("E9-naive-in-cover(naive-walk):", len(e9_in_cov_n), " claim 1445")
print("E9-aligned-in-cover(aligned-walk):", len(e9_in_cov_a))

# ---- UPPER heads (fixed byte-pattern regex, wider lookback) ----
PRO_RE = re.compile(rb'^(?:\x55\x8b\xec|\x83\xec|\x81\xec|\x53|\x56|\x57|\x8b\xff|\x6a)')
def upper_heads(roots, covered):
    heads = set()
    shape_cand = set()
    for a in insn_at:
        if a in covered:
            continue
        hb = read_va(a, 4) or b''
        if not PRO_RE.match(hb):
            continue
        shape_cand.add(a)
        b16 = read_va(a - 16, 16) or b''
        k = len(b16) - 1
        fill = 0
        while k >= 0 and b16[k] in (0x90, 0xCC):
            fill += 1; k -= 1
        if fill >= 2 and k >= 0 and b16[k] == 0xC3:
            if a not in roots:
                heads.add(a)
    return shape_cand, heads

shape_n, heads_naive = upper_heads(set(make_roots(e8_n, vt_t)), cov_naive)
shape_a, heads_aligned = upper_heads(set(make_roots(e8_t, vt_t)), cov_aligned)
print("UPPER add (naive roots):", len(heads_naive), " claim 890")
print("UPPER add (aligned roots):", len(heads_aligned))
print("shape candidates not covered (naive):", len(shape_n))
print("anchor 0x403A80: in heads_naive:", 0x403A80 in heads_naive,
      " shape:", 0x403A80 in shape_n)
print("UPPER naive:", len(make_roots(e8_n, vt_t)) + len(heads_naive), " claim 14242")

# 4-way reference of anchor
def any_data_ptr_to(t):
    hits = []
    for nm in ('.rdata', '.data'):
        v2, z2b, o2, o2s = secs[nm]
        b2 = raw[o2:o2+o2s]
        for k in range(0, len(b2)-3, 4):
            if int.from_bytes(b2[k:k+4], 'little') == t:
                hits.append(hex(v2+k))
    return hits[:5]
print("anchor dword ptrs:", any_data_ptr_to(0x403A80))

# ---- strings, tolerant scan (allow trailing control bytes before NUL) ----
def strings_in(name):
    v2, z2b, o2, o2s = secs[name]
    b2 = raw[o2:o2+o2s]
    out = []
    i = 0
    n = len(b2)
    while i < n:
        if not (32 <= b2[i] < 127):
            i += 1; continue
        j = i
        while j < n and 32 <= b2[j] < 127:
            j += 1
        # allow trailing control chars (e.g. \n) then NUL
        k = j
        while k < n and b2[k] in (0x0A, 0x0D, 0x09):
            k += 1
        if k < n and b2[k] == 0:
            s = b2[i:j].decode('ascii')
            out.append((v2+i, s))
        i = k + 1
    return out

allstr = strings_in('.rdata') + strings_in('.data')
print("total strings:", len(allstr), " (claim: 9,863 printable starts)")
pure = [(va, s) for va, s in allstr if re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*$', s)]
loose = [(va, s) for va, s in allstr
         if re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*', s) and (va, s) not in pure]
print("pure:", len(pure), " claim 5")
for va, s in pure: print("   ", hex(va), repr(s))
print("loose:", len(loose), " claim 30")
methods = set()
for va, s in loose:
    m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*)', s)
    if m: methods.add(m.group(1))
print("distinct methods:", len(methods), " claim 21")

name_addr = {va for va, s in pure} | {va for va, s in loose}
push_sites = []
for a, ins in insn_at.items():
    bs = ins.bytes
    if ins.id == X86_INS_PUSH and bs[0] == 0x68 and len(bs) == 5:
        t = int.from_bytes(bs[1:5], 'little')
        if t in name_addr:
            push_sites.append((a, t))
print("push sites:", len(push_sites), " claim 35")
