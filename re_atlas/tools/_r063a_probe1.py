# -*- coding: utf-8 -*-
"""R-063a probe1: flag-writer closure for [0xA8ED80] write @0x7778CE (read-only).

Own engine (methodology aligned to _crev_engine.py, no import, no modification):
  A0  hash + PE parse (section table VA->file offset)
  A1  byte anchors re-read (write site / WndProc head / C block / spin loops)
  A2  aligned linear decode + pred graph + E8 head set
  T1  function boundary of 0x7778CE: backward reach & HEADS; fwd closure range;
      tail forms; neighbour-head leak check
  T2  write-point context: full listing 0x7775C0..end of WndProc with bytes
  T3  writers/readers census of 0xA8ED80 image-wide (aligned decode + raw abs32)
  T4  raw disp32 0xA8ED80 / 0xA8EDD8 census (data-pointer exclusion)
Prints only. Writes nothing.
"""
import hashlib
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
print("A0 sha256 %s %s" % (hashlib.sha256(raw).hexdigest(),
                           "OK" if hashlib.sha256(raw).hexdigest() == EXPECT_SHA else "FAIL"))

# ---- A0 PE parse ------------------------------------------------------------
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
ENTRY = IB + struct.unpack_from("<I", raw, opt + 16)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((name, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[2]   # virtual range (incl. BSS tail of .data separate)
print("A0 ImageBase=%08X ENTRY=%08X sections:" % (IB, ENTRY))
for nm, sva, vsz, rp, rsz in SEC:
    print("   %-10s VA=%08X vsz=%06X raw=%06X/%06X" % (nm, sva, vsz, rp, rsz))


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def vaof(off):
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= off < rp + rsz:
            return sva + (off - rp)
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


# ---- A1 anchors -------------------------------------------------------------
ANCHORS = [
    (0x7778CE, 5, "a280eda800", "mov [0xA8ED80],al  <- THE WRITE (a2 form)"),
    (0x7775C0, 16, None, "WndProc presumed head (prologue)"),
    (0x7775C8, 2, "33db", "xor ebx,ebx"),
    (0x7777F3, 6, "8b0d68738800", "C-block head mov ecx,[0x887368]"),
    (0x777818, 10, "c705d8eda80002000000", "C-block mov [0xA8EDD8],2"),
    (0x777828, 3, "c21000", "C-block ret 0x10"),
    (0x6BB9A0, 8, None, "host A head (SEH prologue)"),
    (0x6BDD08, 6, None, "A spin loop 1"),
    (0x6BDD2E, 6, None, "A spin loop 2"),
    (0x5D4D50, 5, "a15035b700", "pump head mov eax,[0xB73550]"),
    (0x7CD8EA, 5, None, "host A unique call site"),
]
print("\nA1 anchors:")
for va, n, exp, tag in ANCHORS:
    got = rd(va, n).hex()
    print("   %08X: %-20s %s %s" % (va, got, ("exp=" + exp if exp else "          "),
                                    "OK " + tag if (exp is None or got == exp) else "DIFF " + tag))

# ---- A2 linear decode -------------------------------------------------------
MD = Cs(CS_ARCH_X86, CS_MODE_32)
stream = []
idx = {}
cur = TLO
tb = TEXT[3]
text_bytes = raw[tb: tb + TEXT[4]]
while cur < TLO + TEXT[4]:
    got = None
    for ins in MD.disasm(text_bytes[cur - TLO: cur - TLO + 15], cur):
        got = ins
        break
    if got is None:
        cur += 1
        continue
    b = got.bytes
    mn, op = got.mnemonic, got.op_str
    tgt = None
    if mn in ("call", "jmp"):
        if len(b) == 5 and b[0] in (0xE8, 0xE9):
            tgt = cur + 5 + struct.unpack_from("<i", b, 1)[0]
        elif len(b) == 2 and b[0] == 0xEB:
            tgt = cur + 2 + struct.unpack_from("<b", b, 1)[0]
    elif mn.startswith("j"):
        if len(b) == 6 and b[0] == 0x0F and 0x80 <= b[1] <= 0x8F:
            tgt = cur + 6 + struct.unpack_from("<i", b, 2)[0]
        elif len(b) == 2 and 0x70 <= b[0] <= 0x7F:
            tgt = cur + 2 + struct.unpack_from("<b", b, 1)[0]
    stream.append((cur, got.size, b.hex(), mn, op, tgt))
    cur += got.size
for i, s in enumerate(stream):
    idx[s[0]] = i
print("\nA2 decoded %d aligned insns over .text" % len(stream))

callers = {}
pred = {}
for (a, sz, bs, mn, op, tgt) in stream:
    if mn == "call" and tgt is not None and TLO <= tgt < THI:
        callers.setdefault(tgt, []).append(a)
    if mn[0] == "j" and tgt is not None and TLO <= tgt < THI:
        pred.setdefault(tgt, []).append(a)
    if mn in ("ret", "retf", "hlt", "ud2") or mn == "jmp":
        continue
    nxt = a + sz
    if nxt < TLO + TEXT[4]:
        pred.setdefault(nxt, []).append(a)
HEADS = set(callers)
print("A2 E8 heads=%d aligned call sites=%d" % (len(HEADS), sum(len(v) for v in callers.values())))


def reach(site):
    seen = set()
    work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen:
                seen.add(p)
                work.append(p)
    return seen


def fwd(head):
    seen = set()
    work = [head]
    order = []
    while work:
        a = work.pop()
        k = idx.get(a)
        if k is None:
            continue
        order.append(a)
        a2, sz, bs, mn, op, tgt = stream[k]
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if tgt is not None and TLO <= tgt < THI and tgt not in seen and mn != "call":
            seen.add(tgt)
            work.append(tgt)
        nxt = a + sz
        if mn != "jmp" and nxt < TLO + TEXT[4] and nxt not in seen:
            seen.add(nxt)
            work.append(nxt)
    seen.add(head)
    return seen, order


# ---- T1 boundary ------------------------------------------------------------
WRITE = 0x7778CE
rs = reach(WRITE) & HEADS
print("\nT1 reach(0x7778CE) & HEADS = %s" % sorted(hex(x) for x in rs))
HEAD = 0x7775C0
clo, order = fwd(HEAD)
body = sorted(clo)
print("T1 fwd(%08X): %d insns, range=[%08X, %08X]" % (HEAD, len(clo), body[0], body[-1]))
# last insn end
last = body[-1]
last_end = last + stream[idx[last]][1]
print("T1 body byte range = [%08X, %08X)" % (HEAD, last_end))
# tail forms
rets = [(a, stream[idx[a]][2], stream[idx[a]][3] + " " + stream[idx[a]][4])
        for a in body if stream[idx[a]][3] in ("ret", "retf")]
print("T1 ret-family insns in closure: %d" % len(rets))
for a, bs, mn in sorted(rets):
    print("   %08X: %s %s" % (a, bs, mn))
# indirect jmps inside closure
ijmps = [(a, stream[idx[a]][2], stream[idx[a]][3] + " " + stream[idx[a]][4])
         for a in body if stream[idx[a]][3] == "jmp" and stream[idx[a]][5] is None]
print("T1 indirect/out jmps in closure: %d" % len(ijmps))
for a, bs, mn in sorted(ijmps):
    print("   %08X: %s %s" % (a, bs, mn))
# neighbour-head leak check
below = [x for x in HEADS if x < HEAD]
above = [x for x in HEADS if x > last_end]
nb = (max(below) if below else None, min(above) if above else None)
print("T1 neighbour heads: below=%s above=%s" % tuple(hex(x) if x else None for x in nb))
for nbh in nb:
    if nbh is None:
        continue
    c2, _ = fwd(nbh)
    print("T1 leak check: write-site in fwd(%08X)=%s" % (nbh, WRITE in c2))
# E8 direct callers of presumed head
print("T1 E8 direct callers of %08X: %s" % (HEAD, [hex(x) for x in callers.get(HEAD, [])]))
# jmp-edge (tail call / intra) into head
jmp_in = [a for (a, sz, bs, mn, op, tgt) in stream if mn == "jmp" and tgt == HEAD]
jcc_in = [a for (a, sz, bs, mn, op, tgt) in stream if mn.startswith("j") and mn != "jmp" and tgt == HEAD]
print("T1 jmp->head: %s ; jcc->head: %s" % ([hex(x) for x in jmp_in], [hex(x) for x in jcc_in]))

# ---- T2 listing of WndProc body ---------------------------------------------
print("\nT2 full listing %08X..%08X (fwd-closure instructions in order):" % (HEAD, last_end))
kset = clo
for a in sorted(kset):
    k = idx.get(a)
    if k is None:
        continue
    _, sz, bs, mn, op, tgt = stream[k]
    t = ("-> %08X" % tgt) if (tgt is not None and mn in ("call", "jmp")) else ""
    mark = " <<< WRITE" if a == WRITE else ""
    print("   %08X: %-22s %-8s %s %s%s" % (a, bs, mn, op, t, mark))

# ---- T3 writers/readers of 0xA8ED80 ----------------------------------------
print("\nT3 0xA8ED80 references via aligned decode:")
for (a, sz, bs, mn, op, tgt) in stream:
    if "0xa8ed80" in op:
        kind = "WRITE" if mn == "mov" and op.startswith(("byte ptr [0xa8ed80]", "dword ptr [0xa8ed80]")) and ", " in op and not op.startswith(("byte ptr [0xa8ed80], ",)) else "read?"
        print("   %08X: %-20s %s %s" % (a, bs, mn, op))

# ---- T4 raw abs32 census ----------------------------------------------------
for target, label in [(0xA8ED80, "0xA8ED80 flag"), (0xA8EDD8, "0xA8EDD8 exitstate"),
                      (0x7775C0, "0x7775C0 WndProc head")]:
    pat = struct.pack("<I", target)
    hits = []
    start = 0
    while True:
        j = raw.find(pat, start)
        if j < 0:
            break
        v = vaof(j)
        hits.append((j, v))
        start = j + 1
    insec = {}
    for off, v in hits:
        sn = "?"
        for nm, sva, vsz, rp, rsz in SEC:
            if rp <= off < rp + rsz:
                sn = nm
        insec[sn] = insec.get(sn, 0) + 1
    print("T4 raw abs32 hits for %s: total=%d per-section=%s" % (label, len(hits), insec))
    if target == 0x7775C0:
        for off, v in hits:
            sn = "?"
            for nm, sva, vsz, rp, rsz in SEC:
                if rp <= off < rp + rsz:
                    sn = nm
            # context bytes
            ctx = raw[max(0, off - 6): off + 6].hex()
            print("   file=%08X va=%s sec=%-8s ctx=%s" % (off, ("%08X" % v) if v else "None", sn, ctx))
    else:
        for off, v in hits:
            if v is not None and TLO <= v < TLO + TEXT[4]:
                ctx = raw[max(0, off - 6): off + 6].hex()
                print("   va=%08X ctx=%s" % (v, ctx))
print("\nDONE probe1")
