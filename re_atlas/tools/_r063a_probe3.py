# -*- coding: utf-8 -*-
"""R-063a probe3: phantom-root adjudication, registration linkage, extra IAT,
strings, RTTI, sync-entry API census, pump callers, reader table (read-only).
"""
import hashlib
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

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


def cstr(va, n=100):
    o = fo(va)
    if o is None:
        return None
    end = raw.find(b"\0", o, o + n)
    if end < 0:
        end = o + n
    s = raw[o:end]
    return s.decode("latin1") if all(32 <= c < 127 or c in (9, 10, 13) for c in s) else None


iats = {}
for d in range(16):
    rva, sz = struct.unpack_from("<II", raw, opt + 96 + d * 8)
o = fo(IB + struct.unpack_from("<I", raw, opt + 96 + 8)[0])
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


def roots_of(site):
    rr = reach(site)
    return sorted(r for r in rr if not pred.get(r))


def dump(a0, a1, tag):
    print("   -- %s" % tag)
    a = a0
    while a < a1:
        k = idx.get(a)
        if k is None:
            print("   %08X: (undecoded) %s" % (a, rd(a, 1).hex()))
            a += 1
            continue
        _, sz, bs, mn, op, tgt = stream[k]
        note = ""
        if mn == "call" and tgt is None:
            for frag in op.split("[")[1:]:
                try:
                    m = int(frag.split("]")[0].replace("0x", ""), 16)
                    note = "  ; [%08X]=%s" % (m, iats.get(m, "?"))
                    break
                except Exception:
                    pass
        print("   %08X: %-22s %-6s %s %s" % (a, bs, mn, op, note))
        a += sz


print("C1 phantom roots adjudication:")
print("C1a raw bytes 0x7775B0..0x7775C0: %s" % rd(0x7775B0, 0x10).hex())
dump(0x7775B0, 0x7775C4, "aligned decode 0x7775B0..0x7775C4")
print("C1b raw bytes 0x77740C..0x777420: %s" % rd(0x77740C, 0x14).hex())
dump(0x77740C, 0x777424, "aligned decode 0x77740C..0x777424")

print("\nC2 registration linkage:")
rs = reach(0x777C79) & HEADS
print("   reach(0x777C79)&HEADS=%s" % [hex(x) for x in rs])
print("   roots of reach(0x777C79)=%s" % [hex(x) for x in roots_of(0x777C79)][:6])
print("   E8 callers of 0x777C30: %s" % [hex(x) for x in callers.get(0x777C30, [])])
fwdA = None
# is registration inside host A fwd closure?
def fwd(head):
    seen = {head}
    work = [head]
    while work:
        a = work.pop()
        k = idx.get(a)
        if k is None:
            continue
        _, sz, bs, mn, op, tgt = stream[k]
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


fwdA = fwd(0x6BB9A0)
for c in callers.get(0x777C30, []):
    print("   caller %08X in fwd(hostA 0x6BB9A0)=%s ; in reach(0x7CD80F-entry region)=%s"
          % (c, c in fwdA, 0x6BB9A0 in reach(c) | {c}))

print("\nC3 extra IAT:")
for a in (0x7E102C, 0x7E1424, 0x7E143C, 0x7E13EC, 0x7E14F4, 0x7E14F8, 0x7E14BC,
          0x7E14C0, 0x7E1510, 0x7E1498, 0x7E146C, 0x7E13CC, 0x7E1398, 0x7E1400,
          0x7E14B4, 0x7E14D4, 0x7E14D8, 0x7E1350, 0x7E135C, 0x7E1360, 0x7E1368,
          0x7E1370, 0x7E1380, 0x7E138C, 0x7E1398, 0x7E13B8, 0x7E13C4, 0x7E13C8,
          0x7E13D0, 0x7E13E0, 0x7E13E4, 0x7E13F4, 0x7E1408, 0x7E1418, 0x7E1428,
          0x7E1430, 0x7E1438, 0x7E1440, 0x7E1448, 0x7E1450, 0x7E1458, 0x7E1460,
          0x7E1470, 0x7E1474, 0x7E1484, 0x7E1488, 0x7E1494, 0x7E14A8, 0x7E14B0,
          0x7E14B8, 0x7E14C4, 0x7E14C8, 0x7E14CC, 0x7E14D0, 0x7E14E4, 0x7E14E8,
          0x7E14EC, 0x7E14F0, 0x7E14FC, 0x7E1500, 0x7E1504, 0x7E1508, 0x7E1514):
    v = iats.get(a)
    if v:
        print("   [%08X] = %s" % (a, v))

print("\nC4 strings:")
for va in (0x849F48, 0x849ECC, 0x849EA4, 0x849F40, 0x849F0C):
    print("   %08X: %r" % (va, cstr(va)))

print("\nC5 RTTI second attempt:")
for stamp in (0x685BBA, 0x686205):
    vptr = int.from_bytes(rd(stamp + 6, 4), "little")
    if vptr:
        col = int.from_bytes(rd(vptr - 4, 4), "little")
        td = int.from_bytes(rd(col + 0xC, 4), "little")
        nm = rd(td + 8, 64).split(b"\0")[0].decode("latin1")
        print("   [0x887628] stamp@%08X vptr=%08X COL=%08X TD=%08X name=%r"
              % (stamp, vptr, col, td, nm))
# register-store writers of 0x887640
for patname, pat in (("a3 40768800 (mov [..],eax)", b"\xa3\x40\x76\x88\x00"),
                     ("89 15/0d/1d/25/35/3d ... disp32", None)):
    if pat:
        hits = []
        s0 = 0
        while True:
            j = text_bytes.find(pat, s0)
            if j < 0:
                break
            hits.append(TLO + j)
            s0 = j + 1
        print("   0x887640 %s: %s" % (patname, [hex(x) for x in hits]))
        for h in hits[:4]:
            print("      ctx %08X: %s" % (h, rd(h - 2, 9).hex()))
# generic mov r32,[0x887640] encodings 89 /r with disp32
hits = []
for k, (a, sz, bs, mn, op, tgt) in enumerate(stream):
    if mn == "mov" and op.endswith("[0x887640]") and op.startswith("dword ptr") and bs.startswith("89"):
        hits.append(a)
print("   0x887640 reg-store sites: %s" % [hex(x) for x in hits])

print("\nC6 sync-entry API call census (call [IAT] sites):")
SYNC = {}
for (a, sz, bs, mn, op, tgt) in stream:
    if mn == "call" and op.startswith("dword ptr [0x"):
        try:
            m = int(op.split("[")[1].split("]")[0], 16)
        except Exception:
            continue
        nm = iats.get(m, "")
        for api in ("SetFocus", "SetForegroundWindow", "SetActiveWindow",
                    "ShowWindow", "DestroyWindow", "SetWindowPos", "EnableWindow",
                    "CloseWindow", "SetCapture", "ReleaseCapture", "SetParent",
                    "SendMessageA", "SendMessageW", "PostMessageA", "DispatchMessageA",
                    "SetCursor", "ClipCursor", "SetMenu", "SetWindowLongA",
                    "SetWindowLongPtrA", "SetLayeredWindowAttributes",
                    "ChangeDisplaySettingsA", "DirectDrawCreate", "CoCreateInstance"):
            if nm.endswith("!" + api):
                SYNC.setdefault(api, []).append(a)
for api in sorted(SYNC):
    print("   %-24s %2d sites: %s" % (api, len(SYNC[api]),
                                      [hex(x) for x in SYNC[api][:14]]))

print("\nC7 pump callers:")
PUMP = 0x5D4D50
pc = callers.get(PUMP, [])
print("   E8 callers of 0x5D4D50: %d -> %s" % (len(pc), [hex(x) for x in pc]))

print("\nC8 pump counter [0xAA0430] writers:")
hits = []
for (a, sz, bs, mn, op, tgt) in stream:
    if "0xaa0430" in op:
        hits.append((hex(a), bs, mn + " " + op))
for h in hits:
    print("   %s: %s %s" % h)

print("\nC9 fullscreen gate [0x89F978] writers:")
hits = []
s0 = 0
while True:
    j = text_bytes.find(b"\xc6\x05\x78\xf9\x89\x00", s0)
    if j < 0:
        break
    hits.append(TLO + j)
    s0 = j + 1
print("   c605 stores: %s" % [hex(x) for x in hits])
for (a, sz, bs, mn, op, tgt) in stream:
    if "0x89f978" in op:
        print("   %08X: %s %s %s" % (a, bs, mn, op))

print("\nC10 WM_PAINT case block (0x7776B5..0x7776E0):")
dump(0x7776B5, 0x7776E0, "table case cb=3 (uMsg=0x0F WM_PAINT)")

print("\nC11 0x778030 (pre-dispatch handler) head:")
dump(0x778030, 0x778060, "head 0x778030")
print("   E8 callers of 0x778030: %s" % [hex(x) for x in callers.get(0x778030, [])])
print("   reach(0x778030)&HEADS: %s" % [hex(x) for x in reach(0x778030) & HEADS][:8])

print("\nC12 reader cluster hosts (hex) with loop-shape note:")
READS = [0x432E80, 0x4333F0, 0x4BAD92, 0x4BAF4D, 0x4BB00D, 0x4BB208, 0x4BB689,
         0x4C3D8A, 0x4C46AA, 0x52BB43, 0x55D377, 0x55D3A7, 0x55D88E, 0x55E204,
         0x5D2469, 0x5D2530, 0x5D256A, 0x5D2592, 0x611137, 0x61119E, 0x6211D5,
         0x68FBC7, 0x68FBEC, 0x68FC05, 0x69024A, 0x69027A, 0x6902A7, 0x6902BC,
         0x6904C0, 0x6904E9, 0x690504, 0x6BDD08, 0x6BDD33, 0x759A83, 0x759AAB,
         0x759CE1, 0x759D02, 0x774D74, 0x7776C1, 0x77DE0C, 0x7B9EAA, 0x7B9F86,
         0x7BA1CB, 0x7BA234]
for s in READS:
    rr = reach(s) & HEADS
    k = idx[s]
    # loop shape: is there call 0x5D4D50 within +-0x30 in stream order?
    lo = max(0, k - 12)
    hi = min(len(stream), k + 12)
    pump_near = any(stream[q][3] == "call" and stream[q][5] == PUMP for q in range(lo, hi))
    host = sorted(rr)[0] if rr else None
    print("   %08X: pump-near=%s host=%s" % (s, pump_near, ("%08X" % host) if host else "cold"))
print("\nDONE probe3")
