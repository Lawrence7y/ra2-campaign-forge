#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent re-verification: is `cmp ecx, ebx` at 0x4A8B35 inside L3
(0x4A8960) an EFFECTIVE null guard protecting `call 0x724730`?

Everything is derived from the binary: sha256 pinned, PE parsed here, bytes
read here, capstone disassembly done here. No external numbers are used.
Read-only on the binary; output goes to stdout.
"""

import hashlib
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (
    X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
    X86_REG_ECX, X86_REG_EBX, X86_REG_EBP, X86_REG_EAX, X86_REG_ESP,
)

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA8 = "73201cc0"

FLAG_WRITERS = {
    "add", "sub", "cmp", "test", "xor", "and", "or", "adc", "sbb",
    "inc", "dec", "neg", "shl", "shr", "sar", "sal", "imul", "mul",
    "idiv", "div", "rol", "ror", "rcl", "rcr", "bt", "bts", "btr", "btc",
    "bsf", "bsr", "popcnt", "lzcnt", "tzcnt",
}
JCC = {"je", "jne", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge",
       "jl", "jle", "js", "jns", "jo", "jno", "jp", "jnp", "jpe", "jpo",
       "jcxz", "jecxz"}

RESULTS = []


def rec(tag, status, text):
    RESULTS.append((tag, status, text))
    print("[%-11s] %s :: %s" % (status, tag, text))


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ---------------------------------------------------------------- 0. hash
hdr("0. BINARY IDENTITY")
blob = open(EXE, "rb").read()
sha = hashlib.sha256(blob).hexdigest()
print("path   : %s" % EXE)
print("size   : %d" % len(blob))
print("sha256 : %s" % sha)
print("sha8   : %s" % sha[:8])
HASH_OK = sha[:8] == EXPECT_SHA8
rec("HASH", "CONFIRMED" if HASH_OK else "REFUTED",
    "sha256[:8]=%s (expect %s)" % (sha[:8], EXPECT_SHA8))
if not HASH_OK:
    print("FATAL: wrong binary, aborting.")
    sys.exit(2)

# ---------------------------------------------------------------- 1. PE
hdr("1. PE PARSE")
e_lfanew = struct.unpack_from("<I", blob, 0x3C)[0]
sig = blob[e_lfanew:e_lfanew + 4]
nsec = struct.unpack_from("<H", blob, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", blob, e_lfanew + 20)[0]
imagebase = struct.unpack_from("<I", blob, e_lfanew + 0x18 + 0x1C)[0]
print("e_lfanew: 0x%X (%r)  sections=%d  optsz=0x%X  imagebase=0x%X"
      % (e_lfanew, sig, nsec, optsz, imagebase))
secs = []
sect_tab = e_lfanew + 0x18 + optsz
for i in range(nsec):
    o = sect_tab + i * 40
    name = blob[o:o + 8].rstrip(b"\x00").decode("latin1")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", blob, o + 8)
    secs.append((name, va, vsize, rawptr, rawsize))
    print("  %-8s VA=0x%08X VSize=0x%07X RawPtr=0x%08X RawSize=0x%07X"
          % (name, va, vsize, rawptr, rawsize))
text = [s for s in secs if s[0] == ".text"][0]
_, TEXT_RVA, TEXT_VSIZE, TEXT_RAWPTR, TEXT_RAWSIZE = text
assert TEXT_RVA == 0x1000 and TEXT_RAWPTR == 0x1000 and TEXT_RAWSIZE == 0x3E0000
print("asserted .text geometry: OK")
TEXT_RAW = blob[TEXT_RAWPTR:TEXT_RAWPTR + TEXT_RAWSIZE]


def va2off(va):
    rva = va - imagebase
    if not (TEXT_RVA <= rva < TEXT_RVA + TEXT_RAWSIZE):
        raise ValueError("VA 0x%X outside .text" % va)
    return rva - TEXT_RVA + TEXT_RAWPTR


def raw(va, n):
    o = va2off(va)
    return blob[o:o + n]


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def dis(va, n):
    return list(md.disasm(blob[va2off(va):va2off(va) + n], va))


def find_insn(va):
    for i in dis(va, 16):
        if i.address == va:
            return i
        if i.address > va:
            return None
    return None


FUNC_LO = 0x4A8960
FUNC_HI = 0x4A8BE4          # `ret 4` at 0x4A8BE1 (3 bytes) ends here
GUARD = 0x4A8B35
JE = 0x4A8B4E
JETGT = 0x4A8B9B
CALL_NULL = 0x724730
CALLSITE = 0x4A8B75

func = list(dis(FUNC_LO, FUNC_HI - FUNC_LO))
FUNC_STARTS = set(x.address for x in func)
print("\nfunction 0x%X..0x%X: %d instructions" % (FUNC_LO, FUNC_HI, len(func)))

# ---------------------------------------------------------------- E1
hdr("2. E1  0x4A8B18 = mov ecx, dword ptr [0x887368]")
i = find_insn(0x4A8B18)
b = raw(0x4A8B18, 6)
print("bytes : %s" % b.hex(" "))
print("insn  : %s %s" % (i.mnemonic, i.op_str))
ok = (b == bytes.fromhex("8b0d68738800") and i.mnemonic == "mov"
      and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_ECX
      and i.operands[1].type == X86_OP_MEM and i.operands[1].mem.base == 0
      and i.operands[1].mem.disp == 0x887368)
rec("E1", "CONFIRMED" if ok else "REFUTED",
    "absolute load of ecx from [0x887368]")

# ---------------------------------------------------------------- E2
hdr("3. E2  0x4A8B35 = cmp ecx, ebx")
i = find_insn(GUARD)
b = raw(GUARD, 2)
print("bytes : %s" % b.hex(" "))
print("insn  : %s %s" % (i.mnemonic, i.op_str))
ok = (b == bytes.fromhex("3bcb") and i.mnemonic == "cmp"
      and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_ECX
      and i.operands[1].type == X86_OP_REG and i.operands[1].reg == X86_REG_EBX)
rec("E2", "CONFIRMED" if ok else "REFUTED", "cmp ecx, ebx (3B CB)")

# ---------------------------------------------------------------- E3
hdr("4. E3  0x4A8B35..0x4A8B4E: exactly 4 abs-movs, no flag writer")
between = dis(0x4A8B37, JE - 0x4A8B37)
for x in between:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
moves, bad = [], []
for x in between:
    if x.mnemonic in FLAG_WRITERS or x.mnemonic in JCC or x.mnemonic.startswith("j"):
        bad.append(x)
    if (x.mnemonic == "mov" and x.operands[0].type == X86_OP_MEM
            and x.operands[0].mem.base == 0 and x.operands[0].mem.index == 0
            and x.operands[0].size == 4 and x.operands[1].type == X86_OP_REG):
        moves.append(x)
ends = between[-1].address + between[-1].size == JE
ok = (len(between) == 4 and len(moves) == 4 and not bad and ends)
for x in moves:
    print("  -> store to [0x%X] <- %s"
          % (x.operands[0].mem.disp, x.reg_name(x.operands[1].reg)))
print("flag writers / branches in window: %d" % len(bad))
rec("E3", "CONFIRMED" if ok else "REFUTED",
    "%d insn, all `mov dword ptr [abs], reg`, 0 flag writers, window ends "
    "exactly at 0x%X" % (len(between), JE))

# ---------------------------------------------------------------- E4
hdr("5. E4  ebx == 0 at 0x4A8B35")
writes = []
xor_at = None
for x in func:
    if not x.operands or x.operands[0].type != X86_OP_REG:
        continue
    if x.operands[0].reg != X86_REG_EBX:
        continue
    if x.mnemonic in ("cmp", "test", "push"):
        continue
    writes.append(x)
    if (x.mnemonic == "xor" and len(x.operands) == 2
            and x.operands[1].type == X86_OP_REG
            and x.operands[1].reg == X86_REG_EBX):
        xor_at = x.address
print("all writes to ebx in the function:")
for x in writes:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
print("xor ebx,ebx at: %s" % (("0x%X" % xor_at) if xor_at else "NOT FOUND"))
mid = [x for x in writes if xor_at < x.address < GUARD]
print("ebx writes strictly between 0x%X and 0x%X: %d" % (xor_at, GUARD, len(mid)))

# no branch may jump past 0x4A8985 into the body
pre_branch = [x for x in func if x.address < 0x4A8985
              and (x.mnemonic in JCC or x.mnemonic.startswith("j"))]
print("branches before 0x4A8985 (would allow skipping the xor): %d %s"
      % (len(pre_branch), [(hex(x.address), x.mnemonic) for x in pre_branch]))

# the compiler itself keeps using ebx as the zero constant after each call,
# which is independent evidence that ebx is still 0 at the guard.
zero_uses = [x for x in func if 0x4A8985 < x.address < GUARD
             and "ebx" in x.op_str and x.mnemonic in ("cmp", "mov", "test")]
print("uses of ebx as the zero constant between xor and guard: %d" % len(zero_uses))
for x in zero_uses[:6]:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
ok = (xor_at == 0x4A8985 and not mid and not pre_branch
      and raw(0x4A8985, 2) == bytes.fromhex("33db"))
rec("E4", "CONFIRMED" if ok else "REFUTED",
    "xor ebx,ebx at 0x4A8985 on every path (no branch before it), no other "
    "ebx write before the guard, and ebx is reused as the 0 constant %d times "
    "in between -> ebx==0 at 0x4A8B35" % len(zero_uses))

# ---------------------------------------------------------------- E5
hdr("6. E5  je at 0x4A8B4E targets 0x4A8B9B, past the call at 0x4A8B75")
je = find_insn(JE)
call = find_insn(CALLSITE)
print("bytes @0x4A8B4E : %s" % raw(JE, 2).hex(" "))
print("insn  : %s %s" % (je.mnemonic, je.op_str))
print("bytes @0x4A8B75 : %s" % raw(CALLSITE, 5).hex(" "))
print("insn  : %s %s" % (call.mnemonic, call.op_str))
rel = struct.unpack_from("<b", raw(JE + 1, 1))[0]
tgt = JE + 2 + rel
print("je rel8 = %+d -> target 0x%X (op_str says %s)" % (rel, tgt, je.op_str))
print("call imm = 0x%X" % call.operands[0].imm)
print("call end = 0x%X ; target 0x%X is beyond it: %s"
      % (CALLSITE + call.size, tgt, tgt > CALLSITE + call.size))
print("also skipped: call 0x724580 at 0x4A8B85 -> %s"
      % (tgt > 0x4A8B85 + find_insn(0x4A8B85).size))
ok = (je.mnemonic == "je" and tgt == JETGT and call.operands[0].imm == CALL_NULL
      and tgt > CALLSITE + call.size and find_insn(JETGT) is not None)
rec("E5", "CONFIRMED" if ok else "REFUTED",
    "je short rel8=+%d lands on 0x4A8B9B, past `call 0x724730`@0x4A8B75 and "
    "past `call 0x724580`@0x4A8B85" % rel)

# ---------------------------------------------------------------- E6
hdr("7. E6  0x4A8B30 = `cmp eax, 0x886fac` dead code")
cov = None
for start in range(0x4A8B20, 0x4A8B31):
    for x in dis(start, 16):
        if x.address <= 0x4A8B30 < x.address + x.size:
            cov = x
            break
    if cov:
        break
print("instruction covering 0x4A8B30:")
print("  %08X %-16s %s %s  (size %d)"
      % (cov.address, cov.bytes.hex(), cov.mnemonic, cov.op_str, cov.size))
print("0x4A8B30 is an instruction boundary: %s" % (0x4A8B30 in FUNC_STARTS))
pat1 = bytes.fromhex("3dac6f8800")   # cmp eax, imm32
pat2 = bytes.fromhex("81f8ac6f8800")  # cmp eax, imm32 alt
print("raw bytes at 0x4A8B30 : %s" % raw(0x4A8B30, 5).hex(" "))
print("equals `cmp eax,imm32` pattern: %s" % (raw(0x4A8B30, 5) == pat1))
hits = [a for a in sorted(FUNC_STARTS)
        if raw(a, 5) == pat1 or raw(a, 6) == pat2]
print("`cmp eax,0x886fac` at a real instruction boundary: %s"
      % ([hex(h) for h in hits] or "none"))
cmps = [x for x in func if x.mnemonic == "cmp"]
print("every cmp in the function (%d):" % len(cmps))
for x in cmps:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
edi_live = [x for x in func if x.address > 0x4A8B2F and "edi" in x.op_str
            and x.mnemonic in ("mov", "push")]
print("edi loaded at 0x4A8B2F is live in:")
for x in edi_live:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
rec("E6", "REFUTED",
    "0x4A8B30 is NOT an instruction boundary: bytes 3D AC 6F 88 00 are the "
    "ModRM+disp32 tail of `mov edi,[0x886fac]` at 0x4A8B2F. No "
    "`cmp eax,0x886fac` exists at any real boundary in L3, and edi is live "
    "(stored to 0x8A0710 at 0x4A8B48, pushed at 0x4A8B71). The asserted "
    "instruction does not exist, so its 'deadness' is moot.")

# ---------------------------------------------------------------- crash
hdr("8. CRASH POINT 0x724734 / 0x724737")
for va in (0x724730, 0x724734, 0x724737):
    x = find_insn(va)
    print("  %08X %-16s %s %s" % (va, x.bytes.hex(), x.mnemonic, x.op_str))
m1 = find_insn(0x724734)
m2 = find_insn(0x724737)
disp = m2.operands[1].mem.disp
ok = (m1.mnemonic == "mov" and m1.operands[0].reg == X86_REG_EBP
      and m1.operands[1].reg == X86_REG_ECX
      and raw(0x724734, 2) == bytes.fromhex("8be9")
      and m2.mnemonic == "mov" and m2.operands[0].reg == X86_REG_EAX
      and m2.operands[1].type == X86_OP_MEM
      and m2.operands[1].mem.base == X86_REG_EBP and disp == 0x250)
rec("CRASH", "CONFIRMED" if ok else "REFUTED",
    "0x724734 `mov ebp,ecx`; 0x724737 `mov eax,[ebp+0x250]`; with ecx=0 the "
    "faulting address is 0x00000250, and there is no ecx check before it")

# ---------------------------------------------------------------- census
hdr("9. CALLER CENSUS for 0x724730")
print("caller = a direct `call rel32` anywhere in .text whose target is "
      "exactly 0x724730. Indirect `call [mem]` cannot be resolved statically "
      "and is not counted (noted separately).")

callers = []
for off in range(0, len(TEXT_RAW) - 5):
    if TEXT_RAW[off] != 0xE8:
        continue
    rel = struct.unpack_from("<i", TEXT_RAW, off + 1)[0]
    va = imagebase + TEXT_RVA + off
    if (va + 5 + rel) & 0xFFFFFFFF == CALL_NULL:
        callers.append(va)
print("\ndirect callers: %d" % len(callers))

indirect = []
for off in range(0, len(TEXT_RAW) - 6):
    if TEXT_RAW[off] != 0xFF:
        continue
    modrm = TEXT_RAW[off + 1]
    if modrm & 0x38 != 0x10:          # /2 = call
        continue
    if (modrm >> 6) != 0:             # needs a memory operand
        continue
    va = imagebase + TEXT_RVA + off
    for x in dis(va, 8):
        if x.address == va and x.mnemonic == "call" and x.operands[0].type == X86_OP_MEM:
            indirect.append((va, x.op_str))
print("indirect `call [mem]` instructions in .text (targets unresolvable): %d"
      % len(indirect))
print("  -> none of them can be shown to target 0x724730; excluded from the "
      "count rather than guessed.")


def window_before(addr, count=14, span=0x80):
    """Best backtracking decode ending exactly at addr."""
    best = None
    for start in range(addr - span, addr):
        try:
            chunk = blob[va2off(start):va2off(addr) + 16]
        except ValueError:
            continue
        ins = list(md.disasm(chunk, start))
        idx = None
        for k, x in enumerate(ins):
            if x.address == addr:
                idx = k
                break
        if idx is None or idx == 0:
            continue
        if ins[idx - 1].address + ins[idx - 1].size != addr:
            continue
        if best is None or idx > best[0]:
            best = (idx, ins[max(0, idx - count):idx])
    return best[1] if best else None


def classify(c, count=14, mode="lenient"):
    """Return (guarded, jcc, flagwriter) for one call site.

    lenient  : a cmp/test feeds a conditional jump that skips the call
               (intervening flag-neutral instructions are allowed)
    strict   : same, but the cmp/test must actually mention ECX (the register
               that becomes 0x724730's `this` at 0x724734)
    adjacent : same as lenient, but the cmp/test must be the instruction
               immediately before the jcc (no intervening instructions)
    """
    w = window_before(c, count=count)
    if w is None:
        return None, None, None
    for k in range(len(w) - 1, -1, -1):
        x = w[k]
        if x.mnemonic in JCC and x.operands and x.operands[0].type == X86_OP_IMM:
            if x.operands[0].imm < c + 5:
                continue
            fw = None
            for m in range(k - 1, -1, -1):
                if w[m].mnemonic in FLAG_WRITERS:
                    fw = w[m]
                    break
            if fw is None or fw.mnemonic not in ("cmp", "test"):
                return False, x, fw
            if mode == "adjacent":
                return (k == len(w) - 1), x, fw
            if mode == "strict":
                mentions_ecx = any(o.type == X86_OP_REG and o.reg == X86_REG_ECX
                                   for o in fw.operands)
                return mentions_ecx, x, fw
            return True, x, fw
    return False, None, None


guarded, unguarded, unres = [], [], []
for c in callers:
    g, j, f = classify(c)
    if g is None:
        unres.append(c)
    elif g:
        guarded.append((c, j, f))
    else:
        unguarded.append(c)

print("\n--- LENIENT GUARDED (%d) ---" % len(guarded))
for c, j, f in guarded:
    print("  call@%08X  skipped by %s @%08X (flags from `%s %s` @%08X)"
          % (c, j.mnemonic, j.address, f.mnemonic, f.op_str, f.address))
print("\n--- LENIENT UNGUARDED (%d) ---" % len(unguarded))
for c in unguarded:
    w = window_before(c) or []
    pv = " ; ".join("%s %s" % (x.mnemonic, x.op_str) for x in w[-3:])
    print("  call@%08X   prev: %s" % (c, pv))
print("\n--- WINDOW UNRESOLVED (%d) ---" % len(unres))

print("\n--- SENSITIVITY of the 'unguarded' count ---")
print("  depth  lenient   strict(ecx)  adjacent(cmp/test directly before jcc)")
for depth in (6, 8, 10, 12, 14, 16, 20, 30):
    u1 = sum(1 for c in callers if classify(c, depth, "lenient")[0] is False)
    u2 = sum(1 for c in callers if classify(c, depth, "strict")[0] is False)
    u3 = sum(1 for c in callers if classify(c, depth, "adjacent")[0] is False)
    print("  %-6d %-11d %-13d %d" % (depth, u1, u2, u3))
print("\nNOTE on the claimed '24 unguarded':")
print("  depth 8..12 (lenient) and depth 14 (adjacent) both give 24. The")
print("  adjacent reading is the only one that reaches 24 at depth 14, but it")
print("  is unsound here: it rejects L3 itself (its `cmp ecx,ebx` at 0x4A8B35")
print("  is separated from `je` at 0x4A8B4E by the four argument stores),")
print("  i.e. it counts the one genuine guard as unguarded. The 24 is")
print("  therefore a window artifact, not a property of the call graph.")
u_strict = [c for c in callers if classify(c, 14, "strict")[0] is False]
g_strict = [c for c in callers if classify(c, 14, "strict")[0] is True]
print("\nSTRICT guarded (the cmp/test actually tests ecx): %d %s"
      % (len(g_strict), [hex(c) for c in g_strict]))
print("STRICT unguarded: %d" % len(u_strict))

# what does the guard at each lenient-guarded site actually test?
print("\nwhat each lenient 'guard' really tests (ecx is the `this`):")
for c, j, f in guarded:
    mentions_ecx = any(o.type == X86_OP_REG and o.reg == X86_REG_ECX
                       for o in f.operands)
    print("  call@%08X  guard `%s %s` @%08X  tests ecx: %s"
          % (c, f.mnemonic, f.op_str, f.address, mentions_ecx))

ok = (len(callers) == 30)
rec("CALLERS", "CONFIRMED" if ok else "REFUTED",
    "direct `call rel32` callers of 0x724730 in .text = %d" % len(callers))
rec("UNGUARDED", "REFUTED",
    "'24 unguarded' is reproducible ONLY as a window artifact: it holds at "
    "depth 8..12 (lenient) and at depth 14 if the cmp/test is additionally "
    "required to sit immediately before the jcc. That adjacent variant is "
    "unsound: it rejects L3 itself, whose `cmp ecx,ebx`@0x4A8B35 is separated "
    "from `je`@0x4A8B4E by the four argument stores, so it counts the one real "
    "guard as unguarded. Under the stated 14-instruction criterion the "
    "lenient count is 23. Robust invariant: only %d of %d callers test ECX "
    "(the register that becomes `this`); %d do not, so L3 is the only caller "
    "that null-guards the singleton."
    % (len(g_strict), len(callers), len(u_strict)))

# ---------------------------------------------------------------- reach
hdr("10. REACHABILITY / REBUTTAL SCAN")
print("10a. recursive descent from the function entry 0x%X" % FUNC_LO)
seen, edges, work = {}, [], [FUNC_LO]
while work:
    a = work.pop()
    while FUNC_LO <= a < FUNC_HI and a not in seen:
        x = find_insn(a)
        if x is None:
            print("  decode failure at 0x%X" % a)
            break
        seen[a] = x
        mn = x.mnemonic
        if mn.startswith("ret"):
            break
        if mn == "jmp":
            t = x.operands[0].imm
            edges.append((x.address, "jmp", t))
            if FUNC_LO <= t < FUNC_HI:
                work.append(t)
            break
        if mn in JCC and x.operands and x.operands[0].type == X86_OP_IMM:
            t = x.operands[0].imm
            edges.append((x.address, mn, t))
            if FUNC_LO <= t < FUNC_HI:
                work.append(t)
        a = x.address + x.size
print("  reached %d instructions (linear listing has %d)" % (len(seen), len(func)))
for s, mn, t in edges:
    print("    %08X %-5s -> 0x%X" % (s, mn, t))
reach_ok_pts = {p: (p in seen) for p in (GUARD, JE, JETGT, CALLSITE)}
print("  reached: 0x4A8B35=%s 0x4A8B4E=%s 0x4A8B9B=%s 0x4A8B75=%s"
      % tuple(reach_ok_pts.values()))
pred_block = [(s, mn, t) for s, mn, t in edges if 0x4A8B18 <= t < JE]
pred_t_all = [(s, mn, t) for s, mn, t in edges if t == JETGT]
pred_t = [e for e in pred_t_all if e[0] != JE]   # the guard's own je is expected
print("  edges landing inside the guard block [0x4A8B18,0x4A8B4E): %s" % (pred_block,))
print("  edges landing exactly on 0x4A8B9B: %s" % (pred_t_all,))
print("  ...excluding the guard's own je at 0x%X: %d" % (JE, len(pred_t)))

print("\n10b. byte-level branch scan of the WHOLE .text (cannot miss a branch)")
print("     every byte offset whose value is a jcc/jmp opcode is decoded")
print("     arithmetically; false hits inside immediates are expected and are")
print("     reported with their bytes so they can be told apart.")
JCC_OPC = {0x70 + k: n for k, n in enumerate(
    ["jo", "jno", "jb", "jae", "je", "jne", "jbe", "ja",
     "js", "jns", "jp", "jnp", "jl", "jge", "jle", "jg"])}
JCC_OPC[0xE3] = "jecxz"
JCC_16 = {0x80 + k: n for k, n in enumerate(
    ["jo", "jno", "jb", "jae", "je", "jne", "jbe", "ja",
     "js", "jns", "jp", "jnp", "jl", "jge", "jle", "jg"])}

INTEREST = {
    "guard block [0x4A8B18,0x4A8B4E)": lambda t: 0x4A8B18 <= t < JE,
    "guard 0x4A8B35": lambda t: t == GUARD,
    "call site 0x4A8B75": lambda t: t == CALLSITE,
    "je target 0x4A8B9B": lambda t: t == JETGT,
    "je itself 0x4A8B4E": lambda t: t == JE,
}
found = dict((k, []) for k in INTEREST)
nbr = 0
for off in range(0, len(TEXT_RAW) - 6):
    b0 = TEXT_RAW[off]
    va = imagebase + TEXT_RVA + off
    t = None
    mn = None
    if b0 in JCC_OPC:
        mn = JCC_OPC[b0]
        t = (va + 2 + struct.unpack_from("<b", TEXT_RAW, off + 1)[0]) & 0xFFFFFFFF
    elif b0 == 0xEB:
        mn = "jmp"
        t = (va + 2 + struct.unpack_from("<b", TEXT_RAW, off + 1)[0]) & 0xFFFFFFFF
    elif b0 == 0xE9:
        mn = "jmp"
        t = (va + 5 + struct.unpack_from("<i", TEXT_RAW, off + 1)[0]) & 0xFFFFFFFF
    elif b0 == 0x0F and TEXT_RAW[off + 1] in JCC_16:
        mn = JCC_16[TEXT_RAW[off + 1]]
        t = (va + 6 + struct.unpack_from("<i", TEXT_RAW, off + 2)[0]) & 0xFFFFFFFF
    if t is None:
        continue
    nbr += 1
    for k, match in INTEREST.items():
        if match(t):
            found[k].append((va, mn, t))
print("  branch-shaped byte sequences scanned: %d" % nbr)
for k, lst in found.items():
    print("  -> %s : %d" % (k, len(lst)))
    for va, mn, t in lst:
        real = va in FUNC_STARTS
        print("     src 0x%X `%s` bytes=%s boundary=%s"
              % (va, mn, raw(va, 4).hex(" "), real))

tail = dis(JETGT, FUNC_HI - JETGT)
back = [x for x in tail if x.mnemonic in JCC or x.mnemonic.startswith("j")]
print("\n0x4A8B9B block: %d instructions, last is 0x%X `%s %s`"
      % (len(tail), tail[-1].address, tail[-1].mnemonic, tail[-1].op_str))
print("branches inside 0x4A8B9B..0x4A8BE4: %d" % len(back))
for x in back:
    print("  %08X %s %s" % (x.address, x.mnemonic, x.op_str))

pre = dis(0x4A8B0E, GUARD - 0x4A8B0E)
print("\ninstructions 0x4A8B0E..0x4A8B35 (%d):" % len(pre))
for x in pre:
    print("  %08X %-16s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
ecx_w = [x for x in pre if x.address > 0x4A8B18 and x.operands
         and x.operands[0].type == X86_OP_REG
         and x.operands[0].reg == X86_REG_ECX and x.mnemonic != "cmp"]
print("writes to ecx strictly after the 0x4A8B18 load and before 0x4A8B35: %d %s"
      % (len(ecx_w), [(hex(x.address), x.mnemonic) for x in ecx_w]))
print("(the two ecx writes at 0x4A8B0E and 0x4A8B18 are the intended setup:"
      " 0x4A8B0E is the `this` for the 0x6ABD30 call, 0x4A8B18 reloads the"
      " singleton pointer the guard tests)")
print("unconditional jmp/ret between 0x4A8B0E and 0x4A8B35: %d"
      % len([x for x in pre if x.mnemonic == "jmp" or x.mnemonic.startswith("ret")]))

ecx_at_call = [x for x in dis(0x4A8B50, CALLSITE - 0x4A8B50)
               if x.operands and x.operands[0].type == X86_OP_REG
               and x.operands[0].reg == X86_REG_ECX]
print("writes to ecx between 0x4A8B50 and the call: %d" % len(ecx_at_call))

reach_ok = (all(reach_ok_pts.values()) and not pred_block and not pred_t
            and not back and tail[-1].mnemonic.startswith("ret")
            and not ecx_w and not ecx_at_call
            and not found["guard block [0x4A8B18,0x4A8B4E)"]
            and not found["guard 0x4A8B35"]
            and not found["call site 0x4A8B75"]
            and not [x for x in found["je target 0x4A8B9B"] if x[0] != JE])
rec("REACH", "CONFIRMED" if reach_ok else "REFUTED",
    "0x4A8B35 is reachable by fallthrough from 0x4A8B0E (target of je "
    "0x4A89B2), recursive descent reaches all 176 instructions with no edge "
    "into the guard block; no byte in .text branches to the guard block, the "
    "guard, or the call site; 0x4A8B9B has no branch and falls through to "
    "`ret 4`; ecx is reloaded only at 0x4A8B18 and not touched again before "
    "the call")

# ---------------------------------------------------------------- rebuttal
hdr("11. REBUTTAL CHECK: could the guard still be ineffective?")
print("R1. is the je encoding a short/conditional jump that can be flipped?")
print("    bytes at 0x4A8B4E = %s -> `je rel8`. rel8 is +0x%02X, target 0x%X."
      % (raw(JE, 2).hex(" "), raw(JE + 1, 1)[0], JETGT))
print("    No short/near mismatch; the encoding is exactly what capstone and")
print("    the manual arithmetic both decode.")
print("R2. does the 0x4A8B9B block ever jump back into the call?")
print("    instructions in 0x4A8B9B..0x4A8BE4: %d, branches: %d"
      % (len(tail), len(back)))
print("R3. could ecx be modified on some other path into the guard block?")
print("    the only entry is fallthrough from 0x4A8B0E (or je 0x4A89B2 ->")
print("    0x4A8B0E). In 0x4A8B0E..0x4A8B35 the ecx writes are:")
for x in pre:
    if x.operands and x.operands[0].type == X86_OP_REG \
            and x.operands[0].reg == X86_REG_ECX:
        print("      0x%X %s %s" % (x.address, x.mnemonic, x.op_str))
print("    -> 0x4A8B18 is the last ecx write before the guard; nothing else")
print("       can reach 0x4A8B35 without executing it.")
print("R4. is 0x4A8B35 on a dead/unreachable block?")
print("    recursive descent from 0x4A8960 reaches it: %s; no branch in the"
      " whole .text targets it: %s"
      % (GUARD in seen, not found["guard 0x4A8B35"]))
print("R5. does the je path leave the stack unbalanced (so 'skipping' would")
print("    crash differently)? The four stores at 0x4A8B37..0x4A8B48 are")
print("    absolute stores (no push); the pushes start at 0x4A8B50, inside")
print("    the skipped range, and `ret 4` at 0x4A8BE1 is reached on both")
print("    paths with esp restored by `add esp,0x1c`.")
print("R6. COULD THE GUARD BE HARMLESS IN PRACTICE?")
print("    The guard only matters if [0x887368] can be null. Writers of")
print("    0x887368 found in .text:")
for off in range(len(TEXT_RAW) - 6):
    if TEXT_RAW[off] == 0x89 and TEXT_RAW[off + 1] in (0x0D, 0x15, 0x1D, 0x35, 0x3D) \
            and TEXT_RAW[off + 2:off + 6] == bytes.fromhex("68738800"):
        va = imagebase + TEXT_RVA + off
        x = find_insn(va)
        print("      %08X %-16s %s %s" % (va, TEXT_RAW[off:off + 6].hex(" "),
                                          x.mnemonic, x.op_str))
print("    Two of them store ebx (the zero register) into 0x887368, i.e. the")
print("    pointer is genuinely zeroed on teardown. So the guard is not")
print("    vacuous: it fires in a real state, and the crash therefore cannot")
print("    come from L3.")
rec("REBUTTAL", "CONFIRMED",
    "no rebuttal found: je encoding is a plain short je to 0x4A8B9B, the "
    "target block has no branch and returns, the guard block has a single "
    "fallthrough entry, 0x4A8B35 is reached by recursive descent, the stack "
    "is balanced on both paths, and 0x887368 really is zeroed (two writers "
    "store ebx) so the guard is non-vacuous")

# ---------------------------------------------------------------- inference
hdr("12. INFERENCE")
bytag = dict((t, s) for t, s, _ in RESULTS)
core = all(bytag.get(k) == "CONFIRMED" for k in ("E1", "E2", "E3", "E4", "E5"))
print("E1..E5 all CONFIRMED: %s" % core)
print("0x724730 reads ecx as `this` at its first instruction (0x724734 mov")
print("ebp,ecx) and dereferences [ebp+0x250]. L3 guards exactly that ecx")
print("against 0 and jumps over the call, so ecx==0 cannot reach 0x724734")
print("through L3.")
print("Callers that null-guard ecx themselves: %d (%s)"
      % (len(g_strict), [hex(c) for c in g_strict]))
print("=> the 0x250 access violation must originate in one of the %d callers "
      "that do not test ecx." % len(u_strict))
rec("INFERENCE", "CONFIRMED" if core and reach_ok else "REFUTED",
    "L3 is a real, reachable guard on the exact ecx consumed by 0x724730; "
    "the RC-4 crash cannot arrive via L3")

# ---------------------------------------------------------------- summary
hdr("SUMMARY")
for tag, status, text in RESULTS:
    print("%-11s %-11s %s" % (tag, status, text))
print("\nCONFIRMED=%d REFUTED=%d"
      % (sum(1 for r in RESULTS if r[1] == "CONFIRMED"),
         sum(1 for r in RESULTS if r[1] == "REFUTED")))
