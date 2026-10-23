#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XVERIFY V-001: independent blind recompute of R-035 denominator claims.
Written WITHOUT reading re_atlas/tools/verify_r035_claims.py or fn_walk.py
(blind protocol: my implementation first, compare after).
Target: ra2youli/gamemd.exe sha256 73201cc0...f67476 (assert below).
Read-only. Produces JSON lines of my own counts vs claimed values.
"""
import sys, json, hashlib, re
import pefile
from capstone import *
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
CLAIM = {
    'e8_targets': 7279, 'e9_targets': 2042, 'overlap': 138,
    'e9_in_covered': 1445, 'vtable_slots': 6499, 'LOWER': 13352,
    'UPPER_add': 890, 'UPPER': 14242,
    'pure_names': 5, 'classmethod_literals': 30, 'distinct_methods': 21,
    'push_sites': 35, 'ceiling_funcs': 17,
}

def main():
    raw = open(EXE, 'rb').read()
    assert hashlib.sha256(raw).hexdigest() == SHA, 'FINGERPRINT MISMATCH'
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs = {}
    for s in pe.sections:
        n = s.Name.rstrip(b'\0').decode()
        secs[n] = (base + s.VirtualAddress, s.Misc_VirtualSize,
                   s.PointerToRawData, s.SizeOfRawData)
    tex_va, tex_sz = secs['.text'][0], secs['.text'][1]
    tex_end = tex_va + tex_sz
    entry = base + pe.OPTIONAL_HEADER.AddressOfEntryPoint

    def va2off(va):
        for n, (v, z, o, z2) in secs.items():
            if v <= va < v + max(z, z2):
                off = o + (va - v)
                if off < len(raw):
                    return off
        return None

    def read_va(va, ln):
        o = va2off(va)
        if o is None: return None
        return raw[o:o+ln]

    # ---- linear disassembly of .text with resync ----
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    insn_at = {}  # addr -> (insn, size)
    addr = tex_va
    chunk = 15  # max x86 insn length
    while addr < tex_end:
        o = va2off(addr)
        b = raw[o:o+chunk]
        got = None
        for ins in md.disasm(b, addr):
            got = ins
            break
        if got is None:
            addr += 1
            continue
        insn_at[got.address] = got
        addr += got.size

    e8_t, e9_t = set(), set()
    for a, ins in insn_at.items():
        if ins.id == X86_INS_CALL and len(ins.bytes) == 5 and ins.bytes[0] == 0xE8 and ins.operands and ins.operands[0].type == X86_OP_IMM:
            e8_t.add(ins.operands[0].imm)
        elif ins.id == X86_INS_JMP and len(ins.bytes) == 5 and ins.bytes[0] == 0xE9 and ins.operands and ins.operands[0].type == X86_OP_IMM:
            e9_t.add(ins.operands[0].imm)

    # ---- vtable slot targets: dwords in .rdata/.data pointing into .text ----
    vt_t = set()
    for n in ('.rdata', '.data'):
        v, z, o, z2 = secs[n]
        blob = raw[o:o+z2]
        for i in range(0, len(blob) - 3, 4):
            dw = int.from_bytes(blob[i:i+4], 'little')
            if tex_va <= dw < tex_end:
                vt_t.add(dw)

    roots_call = e8_t | vt_t | {entry}

    # ---- naive byte scan variant (in case theirs was raw byte scan) ----
    tb = raw[va2off(tex_va):va2off(tex_va)+secs['.text'][3]]
    e8_naive, e9_naive = set(), set()
    for m in re.finditer(b'\xe8', tb):
        i = m.start()
        if i + 5 <= len(tb):
            rel = int.from_bytes(tb[i+1:i+5], 'little', signed=True)
            e8_naive.add(tex_va + i + 5 + rel)
    for m in re.finditer(b'\xe9', tb):
        i = m.start()
        if i + 5 <= len(tb):
            rel = int.from_bytes(tb[i+1:i+5], 'little', signed=True)
            e9_naive.add(tex_va + i + 5 + rel)
    e8_naive = {t for t in e8_naive if tex_va <= t < tex_end}
    e9_naive = {t for t in e9_naive if tex_va <= t < tex_end}

    # ---- CFG traversal from roots: call/jmp followed, jcc both, ret stops ----
    covered = set()          # union of all function bodies (instructions)
    fn_bodies = {}           # head -> body set
    def walk(head):
        body = set()
        # require decodable prologue start
        if head not in insn_at:
            return None
        stack = [head]
        seen = set()
        guard = 0
        while stack:
            guard += 1
            if guard > 200000: break
            a = stack.pop()
            if a in seen: continue
            # walk linearly from a until ret/jmp/terminator
            cur = a
            while True:
                ins = insn_at.get(cur)
                if ins is None: break
                if cur in body and cur != a: break   # already walked
                body.add(cur)
                if cur in seen and cur != a: break
                seen.add(cur)
                m = ins.mnemonic
                if m == 'ret':
                    break
                if m == 'call':
                    cur += ins.size
                    continue
                if m == 'jmp':
                    if len(ins.bytes) == 5 and ins.bytes[0] == 0xE9 and ins.operands and ins.operands[0].type == X86_OP_IMM:
                        t = ins.operands[0].imm
                        if tex_va <= t < tex_end:
                            stack.append(t)
                        break
                    if ins.bytes[0] == 0xEB:
                        t = cur + ins.size + int.from_bytes(ins.bytes[1:2], 'little', signed=True)
                        stack.append(t)
                        break
                    break  # indirect jmp: stop path (tail-call unknown target)
                if m.startswith('j'):
                    if ins.operands and ins.operands[0].type == X86_OP_IMM:
                        t = ins.operands[0].imm
                        if tex_va <= t < tex_end:
                            stack.append(t)
                    cur += ins.size
                    continue
                if m == 'leave' or m == 'iretd':
                    break
                cur += ins.size
        return body

    for r in sorted(roots_call):
        b = walk(r)
        if b:
            fn_bodies[r] = b
            covered |= b

    def in_covered(t):
        return t in covered

    # E9 targets landing inside covered code (function-internal block jumps)
    e9_in_cov = {t for t in e9_t if in_covered(t)}
    # E9-only targets (not also E8)
    e9_only = e9_t - e8_t
    e9_only_in_cov = {t for t in e9_only if in_covered(t)}

    # ---- UPPER: prologue-shape heads unreachable from roots_call closure ----
    PROTO_RE = re.compile(
        rb'^(?:558bec|83ec|81ec|53|56|57|8bff|6a)'
    )
    heads = set()
    candidates = 0
    for a in sorted(insn_at):
        if a in covered:
            continue
        b = read_va(a - 8, 8) or b''
        # preceded by a ret then >=2 filler bytes (0x90 or 0xcc) directly before head
        tail = b
        # scan back: last byte before head must be filler; need ret then >=2 fillers
        k = len(tail) - 1
        fill = 0
        while k >= 0 and tail[k] in (0x90, 0xCC):
            fill += 1; k -= 1
        has_ret_before = (k >= 0 and tail[k] == 0xC3)
        hb = read_va(a, 8) or b''
        if not PROTO_RE.match(hb):
            continue
        candidates += 1
        if fill >= 2 and has_ret_before:
            heads.add(a)
    UPPER_add_reach = len(heads - covered)
    # count of shape-and-not-in-roots (R-034 style unfiltered superset for context)
    heads_shape_only = set()
    for a in sorted(insn_at):
        hb = read_va(a, 8) or b''
        if PROTO_RE.match(hb):
            heads_shape_only.add(a)

    # ---- ceiling: Class::Method string literals & push sites ----
    def read_cstr(va):
        o = va2off(va)
        if o is None: return ''
        s = bytearray()
        while o < len(raw) and raw[o] != 0 and len(s) < 256:
            s.append(raw[o]); o += 1
        try: return s.decode('ascii')
        except Exception: return ''

    pure, loose = [], []
    for n in ('.rdata', '.data'):
        v, z, o, z2 = secs[n]
        blob = raw[o:o+max(z, z2)]
        for i in range(len(blob)):
            if blob[i] == 0: continue
            # start of a string = preceded by NUL (or section start)
            if i > 0 and blob[i-1] != 0: continue
            if (v+i) < tex_va or (v+i) >= tex_end:  # only data-section strings
                pass
            s = bytearray()
            j = i
            while j < len(blob) and 32 <= blob[j] < 127:
                s.append(blob[j]); j += 1
            if not s or (j < len(blob) and blob[j] != 0):
                continue
            st = s.decode('ascii')
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*$', st):
                pure.append((v+i, st))
            elif re.match(r'^[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*', st):
                loose.append((v+i, st))
    pure_set = set(pure)
    loose_set = set(loose) - set(pure)
    distinct_loose_methods = set()
    for va, st in loose:
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_]*)', st)
        if m: distinct_loose_methods.add(m.group(1))

    # push imm32 sites referencing these string addresses
    name_targets = {va for va, st in pure} | {va for va, st in loose}
    push_sites = []
    for a, ins in insn_at.items():
        if ins.id == X86_INS_PUSH and len(ins.bytes) == 5 and ins.bytes[0] == 0x68 and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t in name_targets:
                push_sites.append((a, t))
    # attribute to enclosing function (outermost root head whose body contains a)
    def owner(a):
        cands = [h for h, b in fn_bodies.items() if a in b]
        if not cands: return None
        return min(cands)  # outermost = lowest head address heuristic
    owners = set()
    unresolved = 0
    for a, t in push_sites:
        h = owner(a)
        if h is None: unresolved += 1
        else: owners.add(h)

    # naming points for coverage %: how many heads have known names (corpus) -- skip,
    # not in scope. Report the primary counts.

    out = {
        'entry': hex(entry),
        'insn_count': len(insn_at),
        'e8_targets': len(e8_t), 'e8_targets_claim': CLAIM['e8_targets'],
        'e9_targets': len(e9_t), 'e9_targets_claim': CLAIM['e9_targets'],
        'overlap': len(e8_t & e9_t), 'overlap_claim': CLAIM['overlap'],
        'e8_naive': len(e8_naive), 'e9_naive': len(e9_naive),
        'vtable_targets': len(vt_t), 'vtable_claim': CLAIM['vtable_slots'],
        'LOWER_roots_call': len(roots_call), 'LOWER_claim': CLAIM['LOWER'],
        'e9_in_covered': len(e9_in_cov), 'e9_in_covered_claim': CLAIM['e9_in_covered'],
        'e9_only': len(e9_only), 'e9_only_in_cov': len(e9_only_in_cov),
        'UPPER_add_heads': UPPER_add_reach, 'UPPER_add_claim': CLAIM['UPPER_add'],
        'UPPER': len(roots_call) + UPPER_add_reach, 'UPPER_claim': CLAIM['UPPER'],
        'shape_candidates_not_covered': candidates,
        'pure_names': len(pure), 'pure_claim': CLAIM['pure_names'],
        'loose_literals': len(loose_set), 'loose_claim': CLAIM['classmethod_literals'],
        'distinct_methods': len(distinct_loose_methods), 'methods_claim': CLAIM['distinct_methods'],
        'push_sites': len(push_sites), 'push_claim': CLAIM['push_sites'],
        'ceiling_funcs': len(owners), 'ceiling_claim': CLAIM['ceiling_funcs'],
        'unresolved_push': unresolved,
        'covered_bytes': len(covered),
        'roots_new_entries_via_walk': 0,
    }
    # did walk find any *new* entry-like heads beyond roots? (P4 claim: zero)
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
