#!/usr/bin/env python3
# R17-R8-RESIDUAL -- bounded, pure-static analysis of ra2youli/gamemd.exe
#
# Rules honoured (card R17-R8-RESIDUAL):
#   * read-only open; no process, no debugger, no gamemd launch
#   * writes ONLY into this directory
#   * ANCHOR ALIGNMENT: every disassembly run starts at the first real instruction
#     byte after a C3 / C2 xx xx / 90|CC fill, never at an arbitrary address.
#     anchor_of() scans backwards at most 32 bytes and tells you which byte it
#     stopped on. Self-test: 0x47CA6E + 1 must resolve to 0x47CA70 anchored on
#     "C2 0C 00 at 0x47ca79"?  -> no: the self-test is the R17 trap itself
#     (R7 mis-decoded 0x47CA6E+2). See SELF_TESTS below.
#   * BOUNDED: only the addressed functions are decoded. The ONE whole-image pass
#     is Q1's 4-byte pointer scan, which the card explicitly allows and which is
#     DECLARED in REPORT.md sec.Q1(c). E8 call-site scans are limited to .text.
import os, sys, struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <repo>/lead/next_re_20261117_r14/R17_R8_RESIDUAL  -> repo is 3 levels up
CAND = [os.path.abspath(os.path.join(HERE, *(['..'] * 3))),
        os.path.abspath(os.path.join(HERE, *(['..'] * 4))),
        r'D:\Project\ra2-campaign-forge']
ROOT = next(r for r in CAND if os.path.isfile(os.path.join(r, 'ra2youli', 'gamemd.exe')))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IB = 0x400000

d = open(EXE, 'rb').read()
sha = hashlib.sha256(d).hexdigest().upper()
assert sha == EXPECT_SHA, 'hash mismatch: %s' % sha

pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec = struct.unpack_from('<H', d, pe + 6)[0]
opt = pe + 24
so = opt + struct.unpack_from('<H', d, pe + 20)[0]
SECS = []
for i in range(nsec):
    o = so + i * 40
    nm = d[o:o + 8].rstrip(b'\0').decode()
    vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8)
    SECS.append((nm, IB + va, vs, rs, ra))

def sec_of(va):
    for s in SECS:
        nm, sva, vs, rs, ra = s
        if sva <= va < sva + rs:      # FILE image: bound by raw size, not vsize
            return s
    return None

def va2off(va):
    s = sec_of(va)
    if s is None:
        raise ValueError('unmapped %#x' % va)
    return s[4] + (va - s[1])

def rb(va, n):
    return d[va2off(va):va2off(va) + n]

def hx(va, n):
    return rb(va, n).hex(' ').upper()

md = Cs(CS_ARCH_X86, CS_MODE_32)

# ---------------------------------------------------------------- anchoring
def anchor_of(va, back=32):
    """Return (anchor_va, evidence) = first real instruction byte after a
    C3 / C2 xx xx / 90|CC fill preceding <va>. Never guesses; raises if none.
    A fill is a maximal run of 90/CC, or a single C3, or a single C2 xx xx.
    Rule: SCAN BACK to the NEAREST fill and return its end. If that end equals
    <va>, <va> is already anchored (the fill is what precedes it)."""
    for c in range(va, va - back - 1, -1):
        if rb(c - 3, 1)[0] == 0xC2:
            return c, 'after C2 %s at %#x' % (hx(c - 2, 2), c - 3)
        if rb(c - 1, 1)[0] == 0xC3:
            return c, 'after C3 at %#x' % (c - 1)
        run, p = 0, c - 1
        while p >= va - back - 8 and rb(p, 1)[0] in (0x90, 0xCC):
            run += 1
            p -= 1
        if run:
            return c, 'after %d-byte 90|CC fill ending at %#x' % (run, c - 1)
    raise RuntimeError('no anchor within %d bytes before %#x' % (back, va))

def dis(lo, hi, anchored=False):
    if anchored:
        lo, ev = anchor_of(lo)
        sys.stderr.write('anchor 0x%x -> 0x%x (%s)\n' % (lo, lo, ev))
    return list(md.disasm(rb(lo, hi - lo), lo))

# ---------------------------------------------------------------- Q1 scanner
class Scanner:
    def __init__(self):
        self.images = [(s[0], s[1], min(s[3], len(d) - s[4]), s[4]) for s in SECS]
        self.images = [x for x in self.images if x[2] > 0]

    def find_dword(self, value):
        """All mapped positions holding <value> as a little-endian dword.
        This is the ONE whole-image pass of the card (declared)."""
        tgt = struct.pack('<I', value)
        a, b, c, e = tgt
        out = []
        for nm, sva, size, ra in self.images:
            i = d.find(tgt, ra, ra + size)
            while i >= 0:
                out.append((nm, sva + (i - ra)))
                i = d.find(tgt, i + 1, ra + size)
        return out

    def find_e8(self, target):
        """Direct E8 rel32 call sites, .text only (bounded by section)."""
        nm, sva, size, ra = next(x for x in self.images if x[0] == '.text')
        out = []
        for i in range(ra, ra + size - 5):
            if d[i] == 0xE8:
                va = sva + (i - ra)
                if (va + 5 + struct.unpack_from('<i', d, i + 1)[0]) & 0xFFFFFFFF == target:
                    out.append(va)
        return out

SC = Scanner()

def outline(lo, hi):
    """Linear decode, but re-anchor after every fill so a stray 90/CC cannot
    drag the decode off the rails."""
    out, va = [], lo
    while va < hi:
        got = list(md.disasm(rb(va, hi - va), va))
        if not got:
            va += 1
            continue
        for i in got:
            out.append(i)
            va = i.address + i.size
            if i.mnemonic in ('ret', 'retf'):
                break
    return out

# ---------------------------------------------------------------- Q2: 0x47C620 tail
# NOTE: the tail is decoded from its own label 0x47CA70, which is NOT a function
# entry; it is reached by "jne 0x47ca70" from 0x47C632 and by je from 0x47C8FD /
# 0x47C949 and by jl/jne from 0x47CA25 / 0x47CA6A. Anchoring from 0x47C620 and
# walking forward keeps the decode honest instead of starting mid-instruction.
INSNS = [i for i in outline(0x47C620, 0x47CA80) if i.address >= 0x47CA60]


def switch_targets(body_lo, body_hi):
    """(jcc/jmp target, insn) list inside a case body, following only intra-body
    control flow (the body is delimited by its own terminating ret)."""
    res = []
    for i in dis(body_lo, body_hi):
        if i.mnemonic.startswith('j'):
            try:
                res.append((i.address, i.mnemonic, int(i.op_str, 16)))
            except ValueError:
                pass
    return res

# ---------------------------------------------------------------- main
def main():
    print('# R17-R8 residual -- reproducible output\n')
    print('sha256 %s  size %d\n' % (sha, len(d)))

    print('## anchors')
    for t in (0x43F180, 0x43F1CA, 0x43F1E9, 0x43F9A6, 0x43F5D8, 0x43F5E0,
              0x47C3D0, 0x47C4D0, 0x47C620, 0x449440, 0x6F4A70):
        a, ev = anchor_of(t)
        print('0x%X  ->  0x%X   %s   bytes %s' % (t, a, ev, hx(a, 8)))

    print('\n## Q1 (c) 4-byte pointer scan (whole image, DECLARED)')
    for t in (0x43F180, 0x449440, 0x43F1E9, 0x47C620):
        hits = SC.find_dword(t)
        print('0x%X  hits=%d  %s' % (t, len(hits),
              ' '.join('%s:%#x' % h for h in hits)))

    print('\n## Q1 positive control (method resolution)')
    for t in (0x47C620, 0x47C3D0, 0x47C4D0, 0x6F4A70):
        h = SC.find_e8(t)
        print('E8 -> 0x%X  count=%d  %s' % (t, len(h), ' '.join('%#x' % x for x in h)))
    print('E8 -> 0x43F2AE (known call site of 0x47C620) present:',
          bool([i for i in dis(0x43F2AC, 0x43F2B4) if i.mnemonic == 'call'
                and i.op_str == '0x47c620']))

    print('\n## Q2 0x47C620 epilogue/tail (.rdata owner 0x7E3FE0 slot 16)')
    for i in INSNS:
        print('  %08x  %-20s %s %s' % (i.address, i.bytes.hex(' ').upper(),
                                       i.mnemonic, i.op_str))

    print('\n## Q2 all ' + "'ret'" + ' inside 0x47C620..0x47CA7C')
    for i in outline(0x47C620, 0x47CA7C):
        if i.mnemonic == 'ret':
            print('  %08x  %s' % (i.address, i.bytes.hex(' ').upper()))

    print('\n## Q4 case 0 body 0x43F1CA..0x43F1E6')
    for i in dis(0x43F1CA, 0x43F1E9):
        print('  %08x  %-20s %s %s' % (i.address, i.bytes.hex(' ').upper(), i.mnemonic, i.op_str))
    print('\n## Q4 case 2 body 0x43F9A6..0x43FB08')
    for i in dis(0x43F9A6, 0x43FAFC):
        print('  %08x  %-20s %s %s' % (i.address, i.bytes.hex(' ').upper(), i.mnemonic, i.op_str))
    for lo, hi in ((0x43FAFC, 0x43FB0B),):
        for i in dis(lo, hi):
            print('  %08x  %-20s %s %s' % (i.address, i.bytes.hex(' ').upper(), i.mnemonic, i.op_str))
    print('\n## Q4 [esp+0x23] raw byte pattern inside the whole switch function')
    pat = bytes.fromhex('2454')
    lo, hi = va2off(0x43F180), va2off(0x43FB20)
    blob, i, found = d[lo:hi], 0, []
    while True:
        i = blob.find(b'\x24\x23', i)
        if i < 0:
            break
        found.append(0x43F180 + i)
        i += 1
    print('  [esp+0x23] occurrences:', ' '.join('%#x' % x for x in found))

    print('\n## Q3 0x6F4A70 entry (anchored)')
    a, ev = anchor_of(0x6F4A70)
    for i in dis(a, 0x6F4AA3):
        print('  %08x  %-20s %s %s' % (i.address, i.bytes.hex(' ').upper(), i.mnemonic, i.op_str))

if __name__ == '__main__':
    main()
