# -*- coding: utf-8 -*-
"""_e4w_ E4 writer-closure (host B write @0x6BEC72) -- read-only static analysis.

Methodology aligned with R-061/R-062 (as instantiated by C-line
re_atlas/tools/_crev_engine.py, which is NOT imported/modified here):
self-written PE parse, linear aligned decode of .text, pred graph,
backward closure & E8-head intersection for function boundaries,
forward closure for intra-function extent, import-table parse for
IAT call naming, raw-bytes abs32 sweep for data/table references.

Writes nothing. Sections selectable via argv (default: all).
"""
import struct
import sys
import hashlib
from collections import defaultdict, Counter

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

SITE_A_WRITE = 0x6BE0B6   # mov [exitstate],edi(=1)  host A
SITE_A_CMP = 0x6BE0E1     # cmp [exitstate],edi      host A gate (BAIL_SITE)
SITE_A_LOOP = 0x6BE0DC    # call PUMP                host A loop head
SITE_A_EXIT = 0x6BE0E9    # xor esi,esi              host A loop exit (clean img)
SITE_B_WRITE = 0x6BEC72   # mov [exitstate],esi(=1)  host B
SITE_B_CMP = 0x6BEC8C     # cmp [exitstate],esi      host B gate
SITE_B_LOOP = 0x6BEC87    # call PUMP                host B loop head
SITE_B_EXIT = 0x6BEC9D    # loop-exit fallthrough    host B
PUMP = 0x5D4D50
WNDBLOCK = 0x7777F3       # WM_DESTROY block (X3)

KNOWN_G = {0xB73550: "hwnd", 0xA8EDD8: "exitstate", 0x887368: "singleton"}

raw = open(EXE, "rb").read()
SHA = hashlib.sha256(raw).hexdigest()
print("A0 sha256=%s match=%s" % (SHA, SHA == EXPECT_SHA))

# ---- PE parse ---------------------------------------------------------------
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
TLO, THI = TEXT[1], TEXT[1] + TEXT[4]
print("A0 ImageBase=%08X ENTRY=%08X .text=[%08X,%08X)" % (IB, ENTRY, TLO, THI))
for nm, sva, vsz, rp, rsz in SEC:
    print("A0   sec %-8s va=%08X vsz=%X raw=%X/%X" % (nm, sva, vsz, rp, rsz))


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


# ---- A1 anchor byte read-back -----------------------------------------------
ANCHORS = [
    (0x6BE08C, "bf01000000", "mov edi,1 (A const)"),
    (0x6BE0B6, "893dd8eda800", "mov [exitstate],edi (A write)"),
    (0x6BE0E1, "393dd8eda800", "cmp [exitstate],edi (A gate)"),
    (0x6BE0E7, "74f3", "je 0x6be0dc (A back edge)"),
    (0x6BEC60, "a15035b700", "mov eax,[hwnd] (B block head)"),
    (0x6BEC6A, "be01000000", "mov esi,1 (B const)"),
    (0x6BEC72, "8935d8eda800", "mov [exitstate],esi (B write)"),
    (0x6BEC8C, "3935d8eda800", "cmp [exitstate],esi (B gate)"),
    (0x6BEC9B, "75ea", "jne 0x6bec87 (B back edge)"),
    (0x5D4D50, "a15035b700", "PUMP head mov eax,[hwnd]"),
    (0x777809, "a1d8eda800", "mov eax,[exitstate] (C block)"),
    (0x777818, "c705d8eda800", "mov [exitstate],2 (C block)"),
]
ok = 0
for va, exp, tag in ANCHORS:
    got = rd(va, len(exp) // 2).hex()
    ok += (got == exp)
    print("A1 %08X exp=%s got=%s %s ; %s" % (va, exp, got, "OK" if got == exp else "DIFF", tag))
print("A1 anchors %d/%d" % (ok, len(ANCHORS)))

# ---- A2 aligned linear decode + graphs --------------------------------------
MD = Cs(CS_ARCH_X86, CS_MODE_32)
stream = []
idx = {}
cur = TLO
tb = TEXT[3]
text_bytes = raw[tb: tb + TEXT[4]]
while cur < THI:
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
print("A2 decoded %d aligned insns over .text" % len(stream))

callers = defaultdict(list)
pred = defaultdict(list)
for a, sz, bs, mn, op, tgt in stream:
    if mn == "call" and tgt is not None and TLO <= tgt < THI:
        callers[tgt].append(a)
    if mn == "jmp" and tgt is not None and TLO <= tgt < THI:
        pred[tgt].append(a)
        continue
    if mn[0] == "j" and mn != "jmp" and tgt is not None and TLO <= tgt < THI:
        pred[tgt].append(a)
    if mn in ("ret", "retf", "hlt", "ud2"):
        continue
    if mn == "jmp":
        continue
    nxt = a + sz
    if nxt < THI:
        pred[nxt].append(a)
HEADS = set(callers)
print("A2 E8 heads=%d call sites=%d" % (len(HEADS), sum(len(v) for v in callers.values())))


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


def fwd(start, bound=None):
    seen = set()
    work = [start]
    while work:
        a = work.pop()
        if bound is not None and a not in bound:
            continue
        k = idx.get(a)
        if k is None:
            continue
        a2, sz, bs, mn, op, tgt = stream[k]
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if tgt is not None and TLO <= tgt < THI and tgt not in seen:
            if mn == "call":
                pass
            else:
                seen.add(tgt)
                work.append(tgt)
        nxt = a + sz
        if mn != "jmp" and nxt < THI and nxt not in seen:
            seen.add(nxt)
            work.append(nxt)
    return seen


# ---- A3 imports -------------------------------------------------------------
def parse_imports():
    dd = opt + 96
    imp_rva = struct.unpack_from("<I", raw, dd + 8)[0]
    iat = {}
    if not imp_rva:
        return iat
    d = 0
    while True:
        off = fo(IB + imp_rva + d * 20)
        if off is None:
            break
        oft, _ts, _fw, namerva, ft = struct.unpack_from("<IIIII", raw, off)
        if oft == 0 and ft == 0 and namerva == 0:
            break
        n = fo(IB + namerva)
        dll = raw[n:n + 64].split(b"\0")[0].decode("latin1", "replace") if n else "?"
        k = 0
        while True:
            toff = fo(IB + (oft or ft) + k * 4)
            if toff is None:
                break
            t = struct.unpack_from("<I", raw, toff)[0]
            if t == 0:
                break
            if t & 0x80000000:
                nm = "#ord%d" % (t & 0xFFFF)
            else:
                noff = fo(IB + t)
                nm = raw[noff + 2: noff + 2 + 96].split(b"\0")[0].decode("latin1", "replace") if noff else "?"
            iat[IB + ft + k * 4] = dll + "!" + nm
            k += 1
        d += 1
    return iat


IAT = parse_imports()
WANT = ("ExitProcess", "TerminateProcess", "PostQuitMessage", "PostMessage",
        "DestroyWindow", "Sleep", "WaitFor", "GetMessage", "PeekMessage",
        "SendMessage")
iat_by_name = {v: k for k, v in IAT.items()}
interesting = {v: k for k, v in IAT.items() if any(w.lower() in v.lower() for w in WANT)}
print("A3 imports=%d thunks; interesting: %s" % (len(IAT), {nm: hex(va) for nm, va in sorted(interesting.items(), key=lambda x: x[1])}))

# ---- helpers ----------------------------------------------------------------


def ann(s):
    for g, nm in KNOWN_G.items():
        if ("%x" % g) in s:
            return s + "  ; " + nm
    return s


def dump_range(lo, hi, title, mark=()):
    print("---- %s ----" % title)
    k = idx.get(lo)
    while k is None and lo < hi:
        lo += 1
        k = idx.get(lo)
    if k is None:
        print("   (no aligned insn in range)")
        return
    while k is not None and stream[k][0] < hi:
        a, sz, bs, mn, op, tgt = stream[k]
        mark_s = ""
        if tgt is not None and tgt <= a and mn[0] == "j":
            mark_s = "  ; <<< BACKEDGE -> %08X" % tgt
        if a in mark:
            mark_s += "  ; <<< SITE"
        t_s = ""
        if tgt is not None:
            t_s = "%08X" % tgt
        print("%08X: %-22s %-7s %-42s %s%s" % (a, bs, mn, ann(op), t_s, mark_s))
        k += 1


def find_head(site):
    hs = reach(site) & HEADS
    return hs


SECTIONS = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else {"all"}
ALL = SECTIONS == {"all"}


def want(s):
    return ALL or s in SECTIONS


# ---- B3 function boundaries -------------------------------------------------
if want("B3"):
    print("==== B3 function boundaries (reach(site) & E8-heads) ====")
    sites = [SITE_A_WRITE, SITE_A_CMP, SITE_A_LOOP, SITE_A_EXIT,
             SITE_B_WRITE, SITE_B_CMP, SITE_B_LOOP, SITE_B_EXIT, PUMP, WNDBLOCK]
    head_of = {}
    for s in sites:
        hs = find_head(s)
        h = max(hs) if hs else None
        head_of[s] = h
        print("B3 site %08X heads=%s -> chosen=%s  (n=%d)"
              % (s, sorted(hex(x) for x in hs), hex(h) if h else "None", len(hs)))
    # prologue bytes
    for s in sites:
        h = head_of.get(s)
        if h:
            print("B3 head %08X bytes[16]=%s  (for site %08X)"
                  % (h, rd(h, 16).hex(), s))
    # immediate preds of the two writes and the two loop exits
    for s in [SITE_A_WRITE, SITE_B_WRITE, SITE_A_EXIT, SITE_B_EXIT,
              SITE_A_LOOP, SITE_B_LOOP]:
        print("B3 imm preds of %08X: %s" % (s, sorted(hex(x) for x in pred.get(s, ()))))

    HEAD_A = head_of[SITE_A_WRITE]
    HEAD_B = head_of[SITE_B_WRITE]
    print("B3 HEAD_A=%s HEAD_B=%s same=%s" % (hex(HEAD_A), hex(HEAD_B), HEAD_A == HEAD_B))

# ---- B4 targeted function dumps ---------------------------------------------
if want("B4"):
    print("==== B4 targeted dumps ====")
    HEAD_A = max(find_head(SITE_A_WRITE)) if find_head(SITE_A_WRITE) else None
    HEAD_Bs = find_head(SITE_B_WRITE)
    HEAD_B = max(HEAD_Bs) if HEAD_Bs else None
    print("---- HOST_A head=%s extent-insns=%d fwdmin=%s fwdmax=%s ----"
          % (hex(HEAD_A) if HEAD_A else None, *( (len(fwd(HEAD_A)), hex(min(fwd(HEAD_A))), hex(max(fwd(HEAD_A))) ) if HEAD_A else (0, "-", "-"))))
    dump_range(0x6BDF40, 0x6BE160, "HOST_A exit-wait region (0x6BDF40..0x6BE160)",
               mark={SITE_A_WRITE, SITE_A_CMP, SITE_A_LOOP, SITE_A_EXIT})
    print("---- HOST_B heads=%s ----" % sorted(hex(x) for x in HEAD_Bs))
    dump_range(0x6BEB80, 0x6BED80, "HOST_B region (0x6BEB80..0x6BED80)",
               mark={SITE_B_WRITE, SITE_B_CMP, SITE_B_LOOP, SITE_B_EXIT})
    # walk back from A write to nearest branch boundary for gating context
    print("---- HOST_A gating walk-back from write 0x6BE0B6 ----")
    k = idx[SITE_A_WRITE]
    j = k
    n = 0
    start = k
    while j >= 0 and n < 70:
        mn = stream[j][3]
        if mn in ("ret", "retf") or mn[0] == "j" or mn == "call":
            start = j
            break
        j -= 1
        n += 1
    dump_range(stream[start][0], 0x6BE0DC, "HOST_A pre-write block (branch boundary .. write)")

# ---- B5 confluence ----------------------------------------------------------
if want("B5"):
    print("==== B5 control-flow confluence ====")
    HEAD_A = max(find_head(SITE_A_WRITE))
    HEAD_B = max(find_head(SITE_B_WRITE))
    fwdA = fwd(HEAD_A)
    fwdB = fwd(HEAD_B)
    inter = fwdA & fwdB
    print("B5 fwd(HEAD_A) n=%d [%08X..%08X]; fwd(HEAD_B) n=%d [%08X..%08X]"
          % (len(fwdA), min(fwdA), max(fwdA), len(fwdB), min(fwdB), max(fwdB)))
    print("B5 fwd overlap n=%d %s" % (len(inter), sorted(hex(x) for x in list(inter)[:20])))
    for tag, site in [("A_write", SITE_A_WRITE), ("A_cmp", SITE_A_CMP), ("A_loop", SITE_A_LOOP),
                      ("B_write", SITE_B_WRITE), ("B_cmp", SITE_B_CMP), ("B_loop", SITE_B_LOOP),
                      ("B_exit", SITE_B_EXIT), ("A_exit", SITE_A_EXIT)]:
        print("B5 %s(%08X): in fwdA=%s in fwdB=%s" % (tag, site, site in fwdA, site in fwdB))
    # cross edges (non-call) between the two closure sets
    cross = []
    for a in fwdB:
        k = idx.get(a)
        if k is None:
            continue
        a2, sz, bs, mn, op, tgt = stream[k]
        if mn == "call":
            continue
        if tgt is not None and tgt in fwdA:
            cross.append((a, mn, tgt))
    print("B5 cross edges fwdB->fwdA (non-call): %s" % [(hex(a), mn, hex(t)) for a, mn, t in cross])
    cross2 = []
    for a in fwdA:
        k = idx.get(a)
        if k is None:
            continue
        a2, sz, bs, mn, op, tgt = stream[k]
        if mn == "call":
            continue
        if tgt is not None and tgt in fwdB:
            cross2.append((a, mn, tgt))
    print("B5 cross edges fwdA->fwdB (non-call): %s" % [(hex(a), mn, hex(t)) for a, mn, t in cross2])
    # call edges between the two functions
    for tag, src, dst in [("B->A", fwdB, HEAD_A), ("A->B", fwdA, HEAD_B)]:
        sites = [a for a in src if stream[idx[a]][3] == "call" and stream[idx[a]][5] == dst]
        print("B5 call edges %s: %s" % (tag, [hex(x) for x in sites]))
    # indirect jmp/call inside each closure (static-visibility limits)
    for tag, S in [("A", fwdA), ("B", fwdB)]:
        ij = [hex(a) for a in S if stream[idx[a]][3] in ("jmp", "call") and stream[idx[a]][5] is None]
        print("B5 indirect/untargeted jmp|call inside fwd(%s): %s" % (tag, ij))

# ---- B6 loops ----------------------------------------------------------------
if want("B6"):
    print("==== B6 loop census (back edges inside each host) ====")
    for nm, site, hi_bound in [("HOST_A", SITE_A_WRITE, 0x6BE160), ("HOST_B", SITE_B_WRITE, 0x6BED80)]:
        hd = max(find_head(site))
        S = fwd(hd)
        bes = [(a, stream[idx[a]][3], stream[idx[a]][5]) for a in S
               if stream[idx[a]][3].startswith("j") and stream[idx[a]][5] is not None
               and hd <= stream[idx[a]][5] <= a and a <= hi_bound]
        print("B6 %s head=%08X back edges (a<=%08X): %s" % (nm, hd, hi_bound, [(hex(a), m, hex(t)) for a, m, t in bes]))
        # also any back edge anywhere in closure with target >= head (full extent scan)
        bes2 = [(a, stream[idx[a]][3], stream[idx[a]][5]) for a in S
                if stream[idx[a]][3].startswith("j") and stream[idx[a]][5] is not None
                and stream[idx[a]][5] <= a and stream[idx[a]][5] >= hd]
        print("B6 %s ALL back edges tgt>=head: n=%d %s" % (nm, len(bes2), [(hex(a), m, hex(t)) for a, m, t in bes2][:30]))

# ---- B7 caller census --------------------------------------------------------
def block_ctx(cva, back=28, fwd_n=6):
    k = idx[cva]
    j = k - 1
    n = 0
    while j >= 0 and n < back:
        mn = stream[j][3]
        if mn in ("ret", "retf") or mn == "jmp" or (mn[0] == "j" and mn != "jmp") or mn == "call":
            break
        j -= 1
        n += 1
    rows = stream[j + 1: k + 1 + fwd_n]
    return [(hex(a), bs, mn, ann(op)) for a, sz, bs, mn, op, tgt in rows]


if want("B7"):
    print("==== B7 caller census (E8 direct + jmp-tail + indirect/data refs) ====")
    HEAD_A = max(find_head(SITE_A_WRITE))
    HEAD_B = max(find_head(SITE_B_WRITE))
    for nm, hd in [("HOST_A", HEAD_A), ("HOST_B", HEAD_B)]:
        cs = callers.get(hd, [])
        print("B7 %s head=%08X direct E8 call sites=%d" % (nm, hd, len(cs)))
        # jmp-to-head (tail calls)
        jts = [a for (a, sz, bs, mn, op, tgt) in stream if mn == "jmp" and tgt == hd]
        print("B7 %s jmp-tail sites=%s" % (nm, [hex(x) for x in jts]))
        # any decoded insn referencing head address as operand (indirect)
        ind = [hex(a) for (a, sz, bs, mn, op, tgt) in stream
               if ("%x" % hd) in op and mn not in ("call", "jmp")]
        print("B7 %s other insns w/ head in operand: %s" % (nm, ind))
        # raw abs32 sweep over whole image
        pat = struct.pack("<I", hd)
        hits = []
        start = 0
        while True:
            p = raw.find(pat, start)
            if p < 0:
                break
            hits.append(p)
            start = p + 1
        hits_va = []
        for p in hits:
            # map file offset back to VA
            for snm, sva, vsz, rp, rsz in SEC:
                if rp <= p < rp + rsz:
                    hits_va.append((snm, sva + (p - rp)))
                    break
        print("B7 %s raw abs32 hits: %s" % (nm, [(s, hex(v)) for s, v in hits_va]))
        # per-call-site context
        by_enc = Counter()
        for c in cs:
            enc = find_head(c)
            ench = max(enc) if enc else None
            by_enc[ench] += 1
        print("B7 %s enclosing-head histogram: %s" % (nm, {hex(k) if k else "None": v for k, v in by_enc.items()}))
        for c in cs:
            enc = find_head(c)
            ench = max(enc) if enc else None
            print("B7 %s call site %08X enc=%s" % (nm, c, hex(ench) if ench else "None"))
            for row in block_ctx(c):
                print("     %s: %-20s %-7s %s" % row)

# ---- B8 ExitProcess / IAT calls reachable in hosts ---------------------------
if want("B8"):
    print("==== B8 IAT calls + direct callees inside host closures ====")
    HEAD_A = max(find_head(SITE_A_WRITE))
    HEAD_B = max(find_head(SITE_B_WRITE))
    for nm, hd in [("HOST_A", HEAD_A), ("HOST_B", HEAD_B)]:
        S = sorted(fwd(hd))
        iat_calls = []
        callees = Counter()
        for a in S:
            k = idx[a]
            a2, sz, bs, mn, op, tgt = stream[k]
            if mn == "call":
                if tgt is not None:
                    callees[tgt] += 1
                else:
                    m = op.replace(" ", "")
                    for t, name in IAT.items():
                        if "[%x]" % t in m or "[%X]" % t in m:
                            iat_calls.append((hex(a), name))
        print("B8 %s head=%08X IAT calls: %s" % (nm, hd, iat_calls))
        print("B8 %s direct callees: %s" % (nm, {hex(k): v for k, v in sorted(callees.items())}))

# ---- B9 who-calls-both + post-call path --------------------------------------
if want("B9"):
    print("==== B9 caller-level confluence ====")
    HEAD_A = max(find_head(SITE_A_WRITE))
    HEAD_B = max(find_head(SITE_B_WRITE))
    directA = set(callers.get(HEAD_A, []))
    directB = set(callers.get(HEAD_B, []))
    encA = {max(find_head(c)) if find_head(c) else None for c in directA}
    encB = {max(find_head(c)) if find_head(c) else None for c in directB}
    print("B9 enclosing fns of A callers: %s" % sorted(hex(x) for x in encA if x))
    print("B9 enclosing fns of B callers: %s" % sorted(hex(x) for x in encB if x))
    print("B9 common enclosing fns: %s" % sorted(hex(x) for x in (encA & encB) if x))
    # for each enclosing fn of B callers: does it also call A? and is A's call
    # reachable from after the B call site?
    for e in sorted(x for x in encB if x):
        S = fwd(e)
        callsA = [a for a in S if stream[idx[a]][3] == "call" and stream[idx[a]][5] == HEAD_A]
        callsB = [a for a in S if stream[idx[a]][3] == "call" and stream[idx[a]][5] == HEAD_B]
        print("B9 enc-fn %08X: callB sites=%s callA sites=%s" % (e, [hex(x) for x in callsB], [hex(x) for x in callsA]))
        for cb in callsB:
            after = stream[idx[cb]][0] + stream[idx[cb]][1]
            reachA = [a for a in fwd(after) if stream[idx[a]][3] == "call" and stream[idx[a]][5] == HEAD_A]
            print("B9   after callB@%08X (from %08X): callA reachable=%s"
                  % (cb, e, [hex(x) for x in reachA]))
    for e in sorted(x for x in encA if x):
        S = fwd(e)
        callsB = [a for a in S if stream[idx[a]][3] == "call" and stream[idx[a]][5] == HEAD_B]
        callsA = [a for a in S if stream[idx[a]][3] == "call" and stream[idx[a]][5] == HEAD_A]
        print("B9 enc-fn(A) %08X: callA sites=%s callB sites=%s" % (e, [hex(x) for x in callsA], [hex(x) for x in callsB]))

# ---- B10 upstream gating depth-2 ---------------------------------------------
if want("B10"):
    print("==== B10 upstream gating (2 levels) ====")
    HEAD_A = max(find_head(SITE_A_WRITE))
    HEAD_B = max(find_head(SITE_B_WRITE))
    for nm, hd in [("HOST_A", HEAD_A), ("HOST_B", HEAD_B)]:
        print("---- upstream of %s (%08X) ----" % (nm, hd))
        lv1 = callers.get(hd, [])
        seen_enc = {}
        for c in lv1:
            enc = max(find_head(c)) if find_head(c) else None
            seen_enc.setdefault(enc, []).append(c)
        for enc, sites in sorted(seen_enc.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
            if enc is None:
                print("B10 enc=None for sites %s" % [hex(x) for x in sites])
                continue
            lv2 = callers.get(enc, [])
            enc2 = Counter()
            for c2 in lv2:
                e2 = max(find_head(c2)) if find_head(c2) else None
                enc2[e2] += 1
            print("B10 enc %08X (calls to %s: %d) its callers=%d hist=%s"
                  % (enc, nm, len(sites), len(lv2),
                     {hex(k) if k else "None": v for k, v in enc2.items()}))

print("E4W DONE")

# ---- B11 tail blocks + specific IAT names -----------------------------------
if want("B11"):
    print("==== B11 tail blocks / specific thunks ====")
    for va in [0x7E11D0, 0x7E1384, 0x7E15DC, 0x7E15D0, 0x7E15CC, 0x7E1224,
               0x7E11E0, 0x7E1214, 0x7E1444, 0x7E14AC, 0x7E11B0, 0x7E11DC, 0x7E113C]:
        print("B11 IAT %08X = %s" % (va, IAT.get(va, "?")))
    HEAD_A = max(find_head(SITE_A_WRITE))
    fwdA = fwd(HEAD_A)
    print("B11 0x6BE1C0 in fwdA=%s is_head=%s its callers=%s"
          % (0x6BE1C0 in fwdA, 0x6BE1C0 in HEADS, [hex(x) for x in callers.get(0x6BE1C0, [])]))
    print("B11 0x7B86B0 in fwdA=%s; 0x7B86B0 is_head=%s callers=%s"
          % (0x7B86B0 in fwdA, 0x7B86B0 in HEADS, [hex(x) for x in callers.get(0x7B86B0, [])]))
    print("B11 0x7CBDDC bytes=%s" % rd(0x7CBDDC, 16).hex())
    dump_range(0x6BE15B, 0x6BE230, "HOST_A teardown continuation + 0x6BE1C0 head")
    dump_range(0x7B86A0, 0x7B8730, "shared tail block 0x7B86B0..")
    dump_range(0x6BDC90, 0x6BDF40, "HOST_A region around call-B site 0x6BDCFE",
               mark={0x6BDCFE})

# ---- B12 supplementary: reachability, gating context, flag writers -----------
if want("B12"):
    print("==== B12 supplementary ====")
    print("B12 0x7CBE21 bytes[16]=%s ; 0x7CBE18 bytes[12]=%s"
          % (rd(0x7CBE21, 16).hex(), rd(0x7CBE18, 12).hex()))
    print("B12 callers of 0x6BEC50 (exit stub): %s"
          % [hex(x) for x in callers.get(0x6BEC50, [])])
    print("B12 callers of 0x7CBDDC (exit impl) count=%d sites(first 20)=%s"
          % (len(callers.get(0x7CBDDC, [])), [hex(x) for x in callers.get(0x7CBDDC, [])][:20]))
    # pred chain backward from 0x54A8C0
    print("B12 pred-chain from 0x54A8C0:")
    cur = {0x54A8C0}
    seen = set()
    for depth in range(40):
        nxt = set()
        for a in cur:
            for p in pred.get(a, ()):
                if p not in seen:
                    seen.add(p)
                    nxt.add(p)
        if not nxt:
            break
        print("   depth %d: %s" % (depth + 1, sorted(hex(x) for x in nxt)))
        cur = nxt
    print("B12 E8 heads in pred-closure of 0x54A8C0: %s"
          % sorted(hex(x) for x in (seen & HEADS)))
    dump_range(0x54A860, 0x54A8E0, "0x54A8C0 site context")
    dump_range(0x5B3C20, 0x5B3C90, "fn 0x5B3C20 head + gating before callB 0x5B3C70",
               mark={0x5B3C70})
    dump_range(0x647260, 0x647385, "fn 0x647260 head + gating before callB 0x64736D",
               mark={0x64736D})
    print("B12 imm preds of 0x6BE08C: %s ; jmp-targets==0x6BE08C: %s"
          % (sorted(hex(x) for x in pred.get(0x6BE08C, ())),
             [hex(a) for (a, sz, bs, mn, op, tgt) in stream if tgt == 0x6BE08C]))
    # abs32 sweep: writers/readers of 0xa8ed80 (A-internal spin flag)
    tgtb = 0xA8ED80
    pat = struct.pack("<I", tgtb)
    print("B12 abs32 refs to 0xA8ED80 (decoded insns):")
    for (a, sz, bs, mn, op, t) in stream:
        if ("%x" % tgtb) in op:
            print("   %08X: %s %s" % (a, mn, op))
    print("B12 raw abs32 0xA8ED80 hits in file:")
    start = 0
    while True:
        p = raw.find(pat, start)
        if p < 0:
            break
        for snm, sva, vsz, rp, rsz in SEC:
            if rp <= p < rp + rsz:
                print("   sec=%s va=%08X bytes=%s" % (snm, sva + (p - rp), raw[p - 6:p + 8].hex()))
        start = p + 1
    # ExitProcess direct refs
    print("B12 decoded refs to IAT 0x7E1214 (ExitProcess):")
    for (a, sz, bs, mn, op, t) in stream:
        if "7e1214" in op.replace("0x", ""):
            print("   %08X: %s %s" % (a, mn, op))
    print("B12 raw ff15/ff25 14127e00 sites:")
    for sig in (b"\xff\x15\x14\x12\x7e\x00", b"\xff\x25\x14\x12\x7e\x00"):
        start = 0
        while True:
            p = raw.find(sig, start)
            if p < 0:
                break
            for snm, sva, vsz, rp, rsz in SEC:
                if rp <= p < rp + rsz:
                    print("   sig=%s sec=%s va=%08X" % (sig[:2].hex(), snm, sva + (p - rp)))
            start = p + 1
    # who calls 0x5B3C20 from within A + 0x55D360 context
    print("B12 call sites of 0x5B3C20 inside fwd(A): %s"
          % [hex(a) for a in fwd(max(find_head(SITE_A_WRITE)))
             if stream[idx[a]][3] == "call" and stream[idx[a]][5] == 0x5B3C20])
    print("B12 callers of 0x55D360: %s" % [hex(x) for x in callers.get(0x55D360, [])])

# ---- B13 final spot checks ---------------------------------------------------
if want("B13"):
    print("==== B13 spot checks ====")
    print("B13 callers of 0x54A8C0 (phantom site as head?): %s (in HEADS=%s)"
          % ([hex(x) for x in callers.get(0x54A8C0, [])], 0x54A8C0 in HEADS))
    print("B13 [0x7E4C30] data value=%08X ; [0x81C1D0] data value=%08X"
          % (int.from_bytes(rd(0x7E4C30, 4), "little"),
             int.from_bytes(rd(0x81C1D0, 4), "little")))
    print("B13 imm preds of 0x778B9: %s ; jmp-targets==0x778B9: %s"
          % (sorted(hex(x) for x in pred.get(0x778B9, ())),
             [hex(a) for (a, sz, bs, mn, op, t) in stream if t == 0x778B9]))
    print("B13 imm preds of 0x778CE: %s" % sorted(hex(x) for x in pred.get(0x778CE, ())))
    dump_range(0x778B0, 0x778E0, "WndProc block setting [0xa8ed80]")
    dump_range(0x6BD7C0, 0x6BD830, "A: two call sites of 0x5B3C20 context",
               mark={0x6BD7EF, 0x6BD81F})
    # 0x7CB302 = ? (called after phantom B call)
    print("B13 0x7CB302 bytes[8]=%s ; callers of 0x7CB302 count=%d"
          % (rd(0x7CB302, 8).hex(), len(callers.get(0x7CB302, []))))
    # 0x87BF90 = format string? read a bit
    print("B13 [0x87BF90] bytes=%s" % rd(0x87BF90, 48))
    # who reaches 0x5B3C70's block: preds of 0x5B3C70 beyond jne 0x5b3c7f fallthrough
    print("B13 imm preds of 0x5B3C70: %s" % sorted(hex(x) for x in pred.get(0x5B3C70, ())))
    print("B13 imm preds of 0x64736D: %s" % sorted(hex(x) for x in pred.get(0x64736D, ())))
    # is 0x5B3C20 reached during boot? its A call sites context (already dumping 0x6BD7C0)
    # E-heads reaching B write block, final containment statement:
    hb = find_head(SITE_B_WRITE)
    print("B13 containment B: reach(write)&HEADS=%s" % sorted(hex(x) for x in hb))
    ha = find_head(SITE_A_WRITE)
    print("B13 containment A: reach(write)&HEADS=%s" % sorted(hex(x) for x in ha))

# ---- B14 probe: 0x778B9 neighbors, .data init of 0xa8ed80, gate objects -------
if want("B14"):
    print("==== B14 probe ====")
    for va in (0x77880, 0x77890, 0x778A0, 0x778B0, 0x778B9, 0x778C0, 0x778CE, 0x778E0):
        print("B14 idx.get(%08X)=%s" % (va, idx.get(va)))
    k = idx.get(0x778B9)
    if k:
        for j in range(max(0, k - 8), min(len(stream), k + 10)):
            a, sz, bs, mn, op, t = stream[j]
            print("B14 stream[%d] %08X: %-18s %s %s %s" % (j, a, bs, mn, op, ("->%08X" % t) if t else ""))
        # walk back up to 30 insns listing all control instructions
        j = k - 1
        n = 0
        while j >= 0 and n < 40:
            a, sz, bs, mn, op, t = stream[j]
            if mn[0] == "j" or mn in ("ret", "retf", "call", "hlt", "ud2"):
                print("B14 nearest ctl-insn below: %08X: %s %s %s" % (a, bs, mn, op))
                break
            j -= 1
            n += 1
    # .data initial values
    for gva in (0xA8ED80, 0xA8EDD8, 0xB73550, 0x887368):
        o = fo(gva)
        print("B14 .data[%08X] file-off=%s raw=%s" % (gva, hex(o) if o else None,
              rd(gva, 8).hex()))
    print("B14 0x4790E0 bytes[24]=%s" % rd(0x4790E0, 24).hex())
    print("B14 0x4790B0 bytes[16]=%s ; 0x4BA770 bytes[16]=%s" % (rd(0x4790B0, 16).hex(), rd(0x4BA770, 16).hex()))
    print("B14 callers of 0x4790E0: n=%d %s" % (len(callers.get(0x4790E0, [])), [hex(x) for x in callers.get(0x4790E0, [])][:10]))
    # any indirect jmp with table base 0x777A80 beyond 6 entries? raw dump of dispatch tables
    print("B14 jumptable 0x777A80: %s" % rd(0x777A80, 24).hex())
    print("B14 casebyte 0x777A98: %s" % rd(0x777A98, 24).hex())
    # WndProc handlers: dump ranges around each target to find where 0x778B9 block lives
    for tva in (0x77778D, 0x7777CE, 0x7776B5, 0x777781):
        kk = idx.get(tva)
        if kk is not None:
            a, sz, bs, mn, op, t = stream[kk]
            print("B14 handler %08X first: %s %s" % (tva, mn, op))

# ---- B15 corrected: WndProc [0xa8ed80] writer block 0x7778CE -----------------
if want("B15"):
    print("==== B15 corrected writer-block ====")
    print("B15 imm preds of 0x7778B9: %s" % sorted(hex(x) for x in pred.get(0x7778B9, ())))
    print("B15 imm preds of 0x7778CE: %s" % sorted(hex(x) for x in pred.get(0x7778CE, ())))
    print("B15 jmp-targets==0x7778B9: %s"
          % [hex(a) for (a, sz, bs, mn, op, t) in stream if t == 0x7778B9])
    print("B15 idx(0x7778B9)=%s idx(0x7778CE)=%s" % (idx.get(0x7778B9), idx.get(0x7778CE)))
    dump_range(0x7778A0, 0x7778F0, "WndProc block 0x7778A0..0x7778F0 (sets [0xa8ed80])")
    # backward pred-chain from 0x7778CE up to a dispatch-table handler head
    seen = set()
    cur = {0x7778CE}
    chain = []
    for depth in range(60):
        nxt = set()
        for a in cur:
            for p in pred.get(a, ()):
                if p not in seen:
                    seen.add(p)
                    nxt.add(p)
        if not nxt:
            break
        hits = nxt & {0x77778D, 0x7777F3, 0x7777CE, 0x7776B5, 0x777781, 0x7779B9}
        if hits:
            chain.append(("HANDLER-HIT", sorted(hex(x) for x in hits)))
            break
        chain.append((depth + 1, sorted(hex(x) for x in list(nxt))[:6]))
        cur = nxt
    print("B15 pred-chain 0x7778CE upward: %s" % chain)
    print("B15 is 0x7778CE in reach of 0x7776B5? %s ; of 0x7779B9? %s"
          % (0x7778CE in reach(0x7778CE) | {0x7778CE}, 0x7779B9 in reach(0x7778CE)))
