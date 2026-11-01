# -*- coding: utf-8 -*-
"""_crev_ (R-061/R-062 independent review) -- own engine, no gate import.

Independently re-derives, from gamemd.exe (sha256-pinned) with self-written
PE parse / linear decode / pred graph / backward closure / classifier:
  E1  .text bounds + full decode stats
  E2  six INI globals re-derived from vptr-stamp byte pattern (c7 05 imm32
      f4 1a 7e 00), image-wide
  E3  per-host aligned caller counts (13 hosts) and boundary containment:
      backward-reach(site) & E8-heads == {host}; cold head handled separately
  E4  forward-BFS cross-check (host reaches site; neighbour heads do not)
  E5  R-059 spill sites: bytes 8bf1, below head, NOT in site reach
  E6  own E-hist (global-direct) over 5 direct hosts, strict + gate-like
  E7  own classifier over 7 SMALL hosts' callers: verdict per row vs frozen
      CHAIN (88 rows), histogram, chain bytes vs raw image bytes
  E8  param-slot audit: slot writes + address-taken (lea/mov esp) in frames
  E9  stack-object/GenericList: 17 rows, lea adjacency, per-frame slot dword
      stores, vptr-store bytes at 3 pinned VAs, RTTI walk (.?AVGenericList@@
      + CCINIClass control)
  E10 P1F chain pins (F head/callers/edi writers/slot writers)
  E11 caller-self positive control over 5 direct hosts (expect 51, 0x528A10=31)
Writes nothing.
"""
import re
import struct
import sys
from collections import Counter, defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
import hashlib
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

HOST_OF = {0x527750: 0x5276D0, 0x5279BD: 0x527920, 0x527D5B: 0x527CC0,
           0x527FD1: 0x527F20, 0x5282A0: 0x528220, 0x528450: 0x5283D0,
           0x528AA7: 0x528A10, 0x528CB7: 0x528C00, 0x528F97: 0x528F00,
           0x5291F3: 0x529160, 0x5293E3: 0x529394, 0x52966E: 0x5295F0,
           0x52A7DE: 0x52A760}
EXPECT_CNT = {0x5276D0: 757, 0x527920: 2, 0x527CC0: 5, 0x527F20: 7,
              0x528220: 1, 0x5283D0: 306, 0x528A10: 650, 0x528C00: 67,
              0x528F00: 5, 0x529160: 3, 0x529394: 0, 0x5295F0: 651,
              0x52A760: 3}
DIRECT5 = [0x5276D0, 0x528A10, 0x5295F0, 0x5283D0, 0x528F00]
EXPECT_HIST = {0x5276D0: {0x887180: 119, 0x8870C0: 45},
               0x528A10: {0x887180: 80, 0x8870C0: 10},
               0x5295F0: {0x887180: 95, 0x8870C0: 23},
               0x5283D0: {0x8870C0: 3}, 0x528F00: {0x8870C0: 2}}
SMALL = [0x527920, 0x527CC0, 0x527F20, 0x528220, 0x528C00, 0x529160, 0x52A760]
SPILLS = [0x5275CC, 0x527B97, 0x528DF2, 0x52A623]
SAVED = ("ebx", "edi", "esi", "ebp")
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")

# ---- own PE parse -----------------------------------------------------------
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


def fo(va):
    """VA -> file offset via section table (any section)."""
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:          # full-VA compare (rva-vs-VA bug fixed)
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


print("E0 image sha256 OK; ImageBase=%08X ENTRY=%08X .text=[%08X,%08X) raw=(off=%X size=%X)"
      % (IB, ENTRY, TLO, THI, TEXT[3], TEXT[4]))

# ---- own linear decode ------------------------------------------------------
MD = Cs(CS_ARCH_X86, CS_MODE_32)
stream = []          # (va, size, hexbytes, mnemonic, op_str, tgt_or_None)
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
    if mn == "call" or mn == "jmp":
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
print("E1 decoded %d aligned insns over .text" % len(stream))

# ---- own pred graph + callers ----------------------------------------------
callers = defaultdict(list)   # tgt -> [call-site va]
pred = defaultdict(list)
for k, (a, sz, bs, mn, op, tgt) in enumerate(stream):
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
        continue  # out-of-image jmp or no-target: dead end, no fallthrough
    nxt = a + sz
    if nxt < THI:
        pred[nxt].append(a)
HEADS = set(callers)
print("E1b E8 aligned call targets (heads): %d; total aligned call sites: %d"
      % (len(HEADS), sum(len(v) for v in callers.values())))


def reach(site):
    """all insn vas with a branch-graph path INTO site (site excluded)."""
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
    """forward closure from head, call targets NOT traversed (calls return)."""
    seen = set()
    work = [head]
    while work:
        a = work.pop()
        k = idx.get(a)
        if k is None:
            continue
        a2, sz, bs, mn, op, tgt = stream[k]
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if tgt is not None and TLO <= tgt < THI and tgt not in seen:
            if mn == "call":
                pass          # do not follow callee
            else:
                seen.add(tgt)
                work.append(tgt)
        nxt = a + sz
        if mn != "jmp" and nxt < THI and nxt not in seen:
            seen.add(nxt)
            work.append(nxt)
    return seen


# ---- E2 six globals from vptr stamps ---------------------------------------
stamps = {}
pat = re.compile(rb"\xc7\x05(....)\xf4\x1a\x7e\x00", re.S)
for m in pat.finditer(text_bytes):
    va = TLO + m.start()
    stamps[int.from_bytes(m.group(1), "little")] = va
print("E2 vptr-0x7E1AF4 global stamps: %s" %
      {hex(g): hex(a) for g, a in sorted(stamps.items())})
GLOBALS = set(stamps)
print("E2 derived GLOBALS == gate-pinned six: %s" %
      (GLOBALS == {0x887180, 0x887208, 0x887128, 0x887058, 0x8870C0, 0x89F518}))

# ---- E3 boundary containment + caller counts --------------------------------
print("E3 per-host containment & caller counts:")
bad = 0
for s, h in sorted(HOST_OF.items()):
    rs = reach(s) & HEADS
    cnt = len(callers.get(h, []))
    okc = (rs == {h}) if s != 0x5293E3 else (len(rs) == 0)
    okn = cnt == EXPECT_CNT[h]
    bad += (not okc) + (not okn)
    print("  site %08X host %08X heads-in-reach=%s cnt=%d(exp %d) %s %s"
          % (s, h, sorted(hex(x) for x in rs)[:4], cnt, EXPECT_CNT[h],
             "CONTAIN-OK" if okc else "CONTAIN-FAIL", "CNT-OK" if okn else "CNT-FAIL"))
# cold-entry extra facts
print("E3c cold head 0x529394 bytes=%s (exp 33c03bf00f84); E9@0x52949C tgt=%s;"
      " 0x529394 in reach(0x5293E3)=%s; 0x5293E3 in reach(0x5291F3-site)=%s"
      % (rd(0x529394, 6).hex(), hex(stream[idx[0x52949C]][5]),
         0x529394 in reach(0x5293E3), 0x5293E3 in reach(0x5291F3)))
# E9 jumps targeting 0x529394 image-wide
e9_hits = [a for (a, sz, bs, mn, op, tgt) in stream
           if mn == "jmp" and tgt == 0x529394]
print("E3c jmp->0x529394 sites: %s" % [hex(x) for x in e9_hits])

# ---- E4 forward cross-check (3 audited hosts) -------------------------------
for s, h in [(0x528450, 0x5283D0), (0x527750, 0x5276D0), (0x5293E3, 0x529394)]:
    inf = s in fwd(h)
    # neighbour heads: nearest E8 heads below and above host head
    below = [x for x in HEADS if x < h]
    above = [x for x in HEADS if x > h]
    nb = (max(below) if below else None, min(above) if above else None)
    leaks = [nbh for nbh in nb if nbh is not None and s in fwd(nbh)]
    print("E4 site %08X: in fwd(%08X)=%s; neighbour-head leaks=%s"
          % (s, h, inf, [hex(x) for x in leaks]))

# ---- E5 spill sites ---------------------------------------------------------
for w in SPILLS:
    k = idx.get(w)
    host = min(h for h in HOST_OF.values() if h > w)
    s_of = min(s for s, h in HOST_OF.items() if h == host)
    print("E5 spill %08X bytes=%s mnem=%r below-head(%08X)=%s in-reach(%08X-site)=%s"
          % (w, stream[k][2], stream[k][3] + " " + stream[k][4], host,
             w < host, s_of, w in reach(s_of)))

# ---- E6/E7/E11 helpers ------------------------------------------------------
def frame_lo(cva):
    j = idx[cva] - 1
    while j >= 0 and stream[j][3] != "ret":
        j -= 1
    return stream[j + 1][0]


def nearest_writer(reg, from_va, lo, cross_calls):
    j = idx[from_va] - 1
    while j >= 0 and stream[j][0] >= lo:
        a, sz, bs, mn, op, tgt = stream[j]
        if (mn in ("mov", "lea")) and op.startswith(reg + ", "):
            return (a, bs, mn, op.split(", ", 1)[1])
        if mn == "call" and not (cross_calls and reg in SAVED):
            return None
        j -= 1
    return None


def slot_of(src):
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", src)
    if not m:
        return None
    t = m.group(1)
    return ("0x%x" % int(t, 16)) if t.startswith("0x") else ("0x%x" % int(t))


def slot_writers(slot, cva):
    lo = frame_lo(cva)
    out = []
    for q in range(idx[lo], idx[cva]):
        a, sz, bs, mn, op, tgt = stream[q]
        if mn == "mov" and re.match(r"^dword ptr \[esp \+ %s\], \S+"
                                    % re.escape(slot), op):
            out.append((a, bs, op))
    return out


def classify(cva):
    """own one-hop ecx-chain classifier -> (verdict, [(va, bytes)...])."""
    lo = frame_lo(cva)
    w = nearest_writer("ecx", cva, lo, cross_calls=False)
    if w is None:
        return "unknown-thunk", []
    chain = [(w[0], w[1])]
    src = w[3]
    if re.match(r"^0x[0-9a-f]+$", src):
        v = int(src, 16)
        return ("global-load" if v in GLOBALS else "imm"), chain
    if src.endswith("]") and "[" in src:
        slot = slot_of(src)
        if slot:
            if w[2] == "lea":
                return "stack-object", chain
            return ("local-slot" if slot_writers(slot, cva) else "param-slot"), chain
        return "other", chain
    if src in REGS and src != "ecx":
        w2 = nearest_writer(src, w[0], lo, cross_calls=True)
        if w2 is None:
            return "unknown-reg", chain
        chain.append((w2[0], w2[1]))
        src2 = w2[3]
        if re.match(r"^0x[0-9a-f]+$", src2):
            v = int(src2, 16)
            return ("global-load" if v in GLOBALS else "imm"), chain
        m = re.search(r"ebp \+ (0x[0-9a-f]+|\d+)", src2)
        if m and w2[2] == "mov":
            d = int(m.group(1), 16) if m.group(1).startswith("0x") else int(m.group(1))
            if d >= 8:
                return "param1-forward", chain
        slot = slot_of(src2)
        if slot:
            if w2[2] == "lea":
                return "stack-object", chain
            return ("local-slot" if slot_writers(slot, cva) else "param-slot"), chain
        if src2 == "ecx":
            clean = True
            for q in range(idx[lo], idx[w2[0]]):
                mn = stream[q][3]
                if mn == "call":
                    clean = False
                    break
                if mn in ("mov", "lea") and stream[q][4].startswith("ecx, "):
                    clean = False
                    break
            return ("caller-self" if clean else "unknown-reg"), chain
        return "unknown-reg", chain
    return "other", chain


# ---- E7 SMALL hosts classification vs frozen CHAIN --------------------------
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\re_atlas\tools")
import ast as _ast
_tree = _ast.parse(open(r"D:\Project\ra2-campaign-forge\re_atlas\tools\r062_upward_trace_contract.py",
                        encoding="utf-8").read())
CHAIN = None
for _n in _ast.walk(_tree):
    if isinstance(_n, _ast.Assign) and any(getattr(t, "id", "") == "CHAIN" for t in _n.targets):
        CHAIN = _ast.literal_eval(_n.value)
assert CHAIN and len(CHAIN) == 88

verdict_hist = Counter()
mismatch = []
rows_out = []
walked = {}
for host in SMALL:
    hs = sorted(callers.get(host, []))
    walked[host] = hs
    for c in hs:
        v, ch = classify(c)
        verdict_hist[v] += 1
        fv = CHAIN.get(c)
        my_chain_hex = ";".join(b for _, b in ch)
        if fv is None:
            mismatch.append((hex(c), "NOT-IN-CHAIN", v, my_chain_hex))
            continue
        if fv[0] != v or fv[1] != my_chain_hex:
            mismatch.append((hex(c), fv, v, my_chain_hex))
        # raw-image byte confirmation of chain addresses
        for a, b in ch:
            if rd(a, len(b) // 2).hex() != b:
                mismatch.append((hex(c), "RAWBYTE", hex(a), b))
rows_out.append(None)
print("E7 88-row classification: verdict hist=%s sum=%d"
      % (dict(verdict_hist), sum(verdict_hist.values())))
print("E7 frozen-CHAIN walked rows covered: %d/88; mismatches=%d"
      % (sum(1 for c in CHAIN if c in set(sum((walked[h] for h in SMALL), []))),
         len(mismatch)))
for m in mismatch[:20]:
    print("   !", m)
# walked-set vs CHAIN keys equality per host
CHAIN_HOSTS = {}
for host in SMALL:
    mine = set(walked[host])
    frozen_keys = {c for c in CHAIN}  # all keys
print("E7 walked total=%d CHAIN total=%d walked==CHAIN-keys: %s"
      % (sum(len(v) for v in walked.values()), len(CHAIN),
         set(sum((walked[h] for h in SMALL), [])) == set(CHAIN)))

# E7b: negative claim global-load==0 across SMALL; positive control on DIRECT5
gl_small = sum(1 for host in SMALL for c in callers.get(host, [])
               if classify(c)[0] == "global-load")
print("E7b global-load verdicts across 7 SMALL hosts = %d (claim 0)" % gl_small)
cs_total = 0
for h in DIRECT5:
    vs = Counter(classify(c)[0] for c in callers.get(h, []))
    cs_total += vs["caller-self"]
    print("E11 direct host %08X: global-load=%d (exp %d) caller-self=%d callers=%d"
          % (h, vs["global-load"], sum(EXPECT_HIST[h].values()),
             vs["caller-self"], len(callers[h])))

# ---- E6 hist: gate-like first-imm form AND strict any-ecx-write form --------
def hist(host, strict):
    hh = Counter()
    for c in callers.get(host, []):
        k = idx[c]
        j = k - 1
        while j >= 0 and stream[j][0] >= c - 40:
            _, _, _, mn, op, _t = stream[j]
            if mn in ("call", "ret") or mn[0] == "j":
                break
            if mn == "mov" and op.startswith("ecx, "):
                srcv = op.split(", ", 1)[1]
                if re.match(r"^0x[0-9a-f]+$", srcv):
                    v = int(srcv, 16)
                    if v in GLOBALS:
                        hh[v] += 1
                if strict:
                    break
            j -= 1
    return dict(hh)


for h in DIRECT5:
    a = hist(h, strict=False)
    b = hist(h, strict=True)
    print("E6 hist %08X first-imm=%s exp=%s %s | strict-anywrite=%s %s"
          % (h, a, EXPECT_HIST[h], "OK" if a == EXPECT_HIST[h] else "DIFF",
             b, "OK" if b == EXPECT_HIST[h] else "DIFF"))

# ---- E8 param-slot audit ----------------------------------------------------
lea_taken = 0
ps_rows = []
for host in SMALL:
    for c in callers.get(host, []):
        v, ch = classify(c)
        if v in ("param-slot", "local-slot"):
            lo = frame_lo(c)
            w1 = nearest_writer("ecx", c, lo, False)
            src = None
            if w1 and w1[3].startswith("[esp"):
                src = w1[3]
            elif w1 and w1[3] in REGS:
                w2 = nearest_writer(w1[3], w1[0], lo, True)
                if w2 and w2[3].startswith("[esp"):
                    src = w2[3]
            ps_rows.append((c, v, slot_of(src) if src else None))
print("E8 param/local-slot rows: %d" % len(ps_rows))
for c, v, slot in ps_rows:
    lo = frame_lo(c)
    hits = []
    for q in range(idx[lo], idx[c]):
        a, sz, bs, mn, op, tgt = stream[q]
        if slot and ("esp + %s]" % slot) in op:
            hits.append((hex(a), mn, op))
    if any(h[1] == "lea" for h in hits):
        lea_taken += 1
        if lea_taken <= 10:
            print("   ADDRESS-TAKEN(lea) %s %s slot=%s: %s"
                  % (hex(c), v, slot, [h for h in hits if h[1] == "lea"][:3]))
print("E8 rows with lea(address-taken) to the verdict slot: %d/%d"
      % (lea_taken, len(ps_rows)))

# ---- E9 GenericList ---------------------------------------------------------
stores = {0x7787C0: "c7442438041b7e00", 0x779BB3: "c7442424041b7e00",
          0x779E33: "c7442424041b7e00"}
for va, expb in stores.items():
    got = rd(va, 8).hex()
    print("E9 vptr-store %08X bytes=%s exp=%s %s" % (va, got, expb, "OK" if got == expb else "DIFF"))
vt = 0x7E1B04
col = int.from_bytes(rd(vt - 4, 4), "little")
td = int.from_bytes(rd(col + 0xC, 4), "little")
nm = rd(td + 8, 40).split(b"\0")[0].decode("latin1")
col2 = int.from_bytes(rd(0x8174C4, 4), "little")
td2 = int.from_bytes(rd(col2 + 0xC, 4), "little")
nm2 = rd(td2 + 8, 40).split(b"\0")[0].decode("latin1")
print("E9 RTTI GenericList: COL=%08X TD=%08X name=%r" % (col, td, nm))
print("E9 RTTI control 0x8174C8: vfp=%08X name=%r (exp vfp 0x7F9594, .?AVCCINIClass@@)"
      % (int.from_bytes(rd(0x8174C8, 4), "little"), nm2))
# per-frame slot store census over the 17 stack-object rows
so_rows = []
for host in SMALL:
    for c in callers.get(host, []):
        v, ch = classify(c)
        if v == "stack-object":
            so_rows.append((c, ch))
print("E9 stack-object rows: %d (claim 17)" % len(so_rows))
adj_bad = 0
constructed = []
bare = []
for c, ch in so_rows:
    k = idx[c]
    prev = stream[k - 1]
    if not (prev[3] == "lea" and prev[4].startswith("ecx, ")):
        adj_bad += 1
    slot = slot_of(prev[4])
    ws = slot_writers(slot, c)
    # c74424XX+imm8disp form: imm32 hex at chars [8:16]; c78424+disp32: [16:24]
    vptr_hits = [x for x in ws if x[1].startswith("c74424") and x[1][8:16] == "041b7e00"
                 or x[1].startswith("c78424") and x[1][16:24] == "041b7e00"]
    other = [x for x in ws if x not in vptr_hits]
    (constructed if vptr_hits else bare).append((hex(c), slot, [hex(x[0]) for x in vptr_hits], other))
print("E9 lea-adjacency violations: %d/17" % adj_bad)
print("E9 rows with in-frame vptr store: %d -> %s" % (len(constructed), constructed))
print("E9 bare rows (zero vptr store): %d; rows with ANY other slot dword write: %s"
      % (len(bare), [(c, o) for c, s, v, o in bare if o][:10]))

# ---- E10 P1F pins -----------------------------------------------------------
print("E10 bytes@0x689E9C=%s (exp 8b7d08); bytes@0x687744=%s (exp 8b7c2418)"
      % (rd(0x689E9C, 3).hex(), rd(0x687744, 4).hex()))
print("E10 callers of F=0x689E90: %s (exp [0x687853]); F head bytes=%s"
      % ([hex(x) for x in callers.get(0x689E90, [])], rd(0x689E90, 10).hex()))
print("E10 [esp+0x18] writers in frame of 0x687853: %d (exp 0); frame_lo=%08X"
      % (len(slot_writers("0x18", 0x687853)), frame_lo(0x687853)))
print("E10 DONE")
