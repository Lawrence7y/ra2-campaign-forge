# -*- coding: utf-8 -*-
"""R-063a probe2: cold-head root proof, registration caller, IAT/string/RTTI
anchors, pump dispatch landmark, reader clustering (read-only, prints only).
"""
import hashlib
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((name, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[2]


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


def cstr(va, n=80):
    o = fo(va)
    if o is None:
        return None
    end = raw.find(b"\0", o, o + n)
    if end < 0:
        end = o + n
    return raw[o:end].decode("latin1")


# ---- imports ----------------------------------------------------------------
print("B1 imports (IAT resolution):")
iats = {}
dirdva = struct.unpack_from("<I", raw, opt + 96 + 8)[0]  # data dir[1] = import
for d in range(64):
    rva, sz = struct.unpack_from("<II", raw, opt + 96 + d * 8)
    if d == 1:
        importdir = (IB + rva, sz)
o = fo(importdir[0])
while True:
    ent = raw[o:o + 20]
    if ent == b"\0" * 20:
        break
    oft, tds, fwd, namet, first = struct.unpack("<IIIII", ent)
    dll_o = fo(IB + namet)
    dll = raw[dll_o:raw.find(b"\0", dll_o)].decode("latin1")
    t = oft or first
    while True:
        thunk = struct.unpack_from("<I", raw, fo(IB + t))[0]
        if thunk == 0:
            break
        if not (thunk & 0x80000000):
            hn = fo(IB + thunk + 2)
            name = raw[hn:raw.find(b"\0", hn)].decode("latin1")
            iats[IB + first] = "%s!%s" % (dll, name)
        t += 4
        first += 4
    o += 20
for a in (0x7E1394, 0x7E1404, 0x7E11C4, 0x7E14AC, 0x7E1444, 0x7E1214):
    print("   [%08X] = %s" % (a, iats.get(a, "??")))

# ---- decode -----------------------------------------------------------------
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
    seen = {head}
    work = [head]
    while work:
        a = work.pop()
        k = idx.get(a)
        if k is None:
            continue
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
    return seen


WRITE = 0x7778CE
HEAD = 0x7775C0

# ---- B2 cold-head root proof -------------------------------------------------
rs = reach(WRITE)
roots = sorted(r for r in rs if not pred.get(r))
print("\nB2 backward-closure of write: %d nodes; roots(no-pred nodes)=%s"
      % (len(rs), [hex(x) for x in roots]))
print("B2 write in fwd(head)=%s ; head==sole root=%s" % (WRITE in fwd(HEAD), roots == [HEAD]))

# ---- B3 registration function ------------------------------------------------
REGSITE = 0x777C7D
r2 = reach(REGSITE) & HEADS
print("\nB3 containing head(s) of %08X: %s" % (REGSITE, [hex(x) for x in r2]))
# frame walk: dump insns around the WNDCLASS setup
lo = REGSITE - 0x120
k = idx.get(lo)
while k is not None and stream[k][0] < REGSITE + 0x160:
    a, sz, bs, mn, op, tgt = stream[k]
    if a >= REGSITE - 0x100:
        t = ("-> %08X" % tgt) if (tgt is not None and mn in ("call", "jmp")) else ""
        note = ""
        if "0x7775c0" in op:
            note = "  <<< WndProc ptr"
        if mn == "call" and tgt is None:
            m = None
            for frag in op.split("[")[1:]:
                try:
                    m = int(frag.split("]")[0].replace("0x", ""), 16)
                except Exception:
                    m = None
                if m:
                    break
            if m:
                note = "   ; [%08X]=%s" % (m, iats.get(m, "?"))
        print("   %08X: %-22s %-6s %s %s%s" % (a, bs, mn, op, t, note))
    k += 1

# ---- B4 strings & data anchors ------------------------------------------------
print("\nB4 strings:")
for va in (0x849E94, 0x849EF8, 0x849F08, 0x849E70, 0x849F14):
    print("   %08X: %r" % (va, cstr(va)))
print("   0x81C5E8 dword=%s 0x81C5F0 dword=%s"
      % (rd(0x81C5E8, 4).hex(), rd(0x81C5F0, 4).hex()))
d1 = int.from_bytes(rd(0x81C5E8, 4), "little")
d2 = int.from_bytes(rd(0x81C5F0, 4), "little")
print("   *0x81C5E8 -> %r ; *0x81C5F0 -> %r"
      % (cstr(d1) if 0x700000 <= d1 < 0xB80000 else None,
         cstr(d2) if 0x700000 <= d2 < 0xB80000 else None))
# jump/case tables of WndProc
tabj = [int.from_bytes(rd(0x777A80 + i * 4, 4), "little") for i in range(6)]
caseb = list(rd(0x777A98, 0x18))
print("B4 WndProc jump table 0x777A80 = %s" % [hex(x) for x in tabj])
print("B4 case-byte table 0x777A98 = %s (idx=uMsg-1)" % [hex(x) for x in caseb])

# ---- B5 RTTI of singletons ----------------------------------------------------
print("\nB5 vptr stamps / RTTI for singletons:")
pat_needles = {0x887628: b"\xc7\x05\x28\x76\x88\x00", 0x887640: b"\xc7\x05\x40\x76\x88\x00",
               0x87F770: b"\xc7\x05\x70\xf7\x87\x00", 0xB73550: b"\xc7\x05\x50\x35\xb7\x00",
               0xB73560: b"\xa2\x60\x35\xb7\x00", 0xB73561: b"\xc6\x05\x61\x35\xb7\x00",
               0x884D34: b"\x88\x1d\x34\x4d\x88\x00", 0x8A00A0: b"\xc6\x05\xa0\x00\x8a\x00\x01"}
for g, pat in pat_needles.items():
    hits = []
    start = 0
    while True:
        j = text_bytes.find(pat, start)
        if j < 0:
            break
        hits.append(TLO + j)
        start = j + 1
    print("   writer-pattern for %08X: %s" % (g, [hex(x) for x in hits[:8]]))
# RTTI walk for the class owning vptr stamped into 0x887628
# find stamp c7 05 28 76 88 00 <vptr4>
j = text_bytes.find(b"\xc7\x05\x28\x76\x88\x00")
if j >= 0:
    vptr = int.from_bytes(text_bytes[j + 6: j + 10], "little")
    col = int.from_bytes(rd(vptr - 4, 4), "little")
    td = int.from_bytes(rd(col + 0xC, 4), "little")
    nm = rd(td + 8, 64).split(b"\0")[0].decode("latin1")
    print("   [0x887628] stamp@%08X vptr=%08X COL=%08X TD=%08X name=%r"
          % (TLO + j, vptr, col, td, nm))
j = text_bytes.find(b"\xc7\x05\x40\x76\x88\x00")
if j >= 0:
    vptr = int.from_bytes(text_bytes[j + 6: j + 10], "little")
    col = int.from_bytes(rd(vptr - 4, 4), "little")
    td = int.from_bytes(rd(col + 0xC, 4), "little")
    nm = rd(td + 8, 64).split(b"\0")[0].decode("latin1")
    print("   [0x887640] stamp@%08X vptr=%08X COL=%08X TD=%08X name=%r"
          % (TLO + j, vptr, col, td, nm))

# ---- B6 pump dispatch landmark -------------------------------------------------
print("\nB6 pump 0x5D4D50 body (call sites + IAT):")
a = 0x5D4D50
end = 0x5D4E70
while a < end:
    k = idx.get(a)
    if k is None:
        a += 1
        continue
    _, sz, bs, mn, op, tgt = stream[k]
    note = ""
    if mn == "call" and tgt is None:
        m = None
        for frag in op.split("[")[1:]:
            try:
                m = int(frag.split("]")[0].replace("0x", ""), 16)
            except Exception:
                m = None
            if m:
                break
        if m:
            note = "   ; [%08X]=%s" % (m, iats.get(m, "?"))
    print("   %08X: %-22s %-6s %s %s" % (a, bs, mn, op, note))
    a += sz

# ---- B7 reader clustering -------------------------------------------------------
print("\nB7 containing-head clusters of the 45 read sites:")
READS = [0x432E80, 0x4333F0, 0x4BAD92, 0x4BAF4D, 0x4BB00D, 0x4BB208, 0x4BB689,
         0x4C3D8A, 0x4C46AA, 0x52BB43, 0x55D377, 0x55D3A7, 0x55D88E, 0x55E204,
         0x5D2469, 0x5D2530, 0x5D256A, 0x5D2592, 0x611137, 0x61119E, 0x6211D5,
         0x68FBC7, 0x68FBEC, 0x68FC05, 0x69024A, 0x69027A, 0x6902A7, 0x6902BC,
         0x6904C0, 0x6904E9, 0x690504, 0x6BDD08, 0x6BDD33, 0x759A83, 0x759AAB,
         0x759CE1, 0x759D02, 0x774D74, 0x7776C1, 0x77DE0C, 0x7B9EAA, 0x7B9F86,
         0x7BA1CB, 0x7BA234]


def host_of(site):
    rr = reach(site) & HEADS
    if rr:
        return rr
    below = [x for x in HEADS if x <= site]
    return {"cold~%08X" % max(below)} if below else {"??"}


cl = {}
for s in READS:
    h = host_of(s)
    key = sorted(h)[0] if len(h) == 1 else tuple(sorted(h))
    cl.setdefault(str(key), []).append(hex(s))
for k in sorted(cl):
    print("   host %s: %d reads %s" % (k, len(cl[k]), cl[k]))

# ---- B8 0x777420 (activation-path callee) --------------------------------------
print("\nB8 function 0x777420: head bytes=%s" % rd(0x777420, 16).hex())
print("   E8 direct callers: %s" % [hex(x) for x in callers.get(0x777420, [])])
print("   reach(0x777420)&HEADS=%s" % [hex(x) for x in reach(0x777420) & HEADS])
rr = reach(0x777420)
roots = sorted(r for r in rr if not pred.get(r))
print("   roots=%s" % [hex(x) for x in roots[:6]])
print("   body listing (first 40):")
a = 0x777420
n = 0
while n < 40:
    k = idx.get(a)
    if k is None:
        break
    _, sz, bs, mn, op, tgt = stream[k]
    print("   %08X: %-22s %-6s %s" % (a, bs, mn, op))
    a += sz
    n += 1

# ---- B9 registration fn callers + host A/startup linkage ------------------------
print("\nB9 linkage of registration function:")
if REGSITE in idx:
    pass
reg_roots = sorted(r for r in reach(REGSITE) if not pred.get(r))
print("   roots of reach(%08X)=%s" % (REGSITE, [hex(x) for x in reg_roots[:8]]))
for r in reg_roots:
    if r in HEADS:
        print("   root %08X is E8 head, callers=%s" % (r, [hex(x) for x in callers[r]]))
print("\nDONE probe2")
