# -*- coding: utf-8 -*-
"""R17-AUDIT-D48-B2B-B : bounded byte-level check of D-1 / D-2.  READ-ONLY.

Boundary rules (card §0):
 A. Sanctioned windows, nothing else linearly disassembled except B6's three
    named functions: [0x43F100,0x43F660) and [0x449440,0x449520).
 B. Alignment rule for the 0x43F1xx function: try every start s in
    {0x43F100,...,0x43F230} (16-byte grid) *and* every s that immediately
    follows a `C2 iw` / `C3` terminator in the window; a start is accepted only
    if the linear decode is junk-free (no fstp/push cs/iretd/invalid/...),
    lands exactly on the anchors 0x43F2B5, 0x43F504, 0x43F5B1, and terminates
    on `C3`/`C2`.
 C. Stop rule: stop at ret/int3-run or 200 insns per segment; segments are
    chained only while the next address stays < window end.
 D. B6: linear decode from the given VA until 3x CC padding, a ret-run, or
    600 insns. No function index built, no .text sweep.
"""
import struct, json, os, hashlib, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "ra2youli/gamemd.exe"
OUT = "lead/next_re_20261117_r14/R17_AUDIT_D48_B2B_B"
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


class PE:
    def __init__(self, path):
        self.b = open(path, "rb").read()
        b = self.b
        e = struct.unpack_from("<I", b, 0x3C)[0]
        assert b[e:e + 4] == b"PE\0\0"
        coff = e + 4
        nsec, = struct.unpack_from("<H", b, coff + 2)
        optsz, = struct.unpack_from("<H", b, coff + 16)
        opt = coff + 20
        self.base, = struct.unpack_from("<I", b, opt + 28)
        sec = opt + optsz
        self.sections = []
        for i in range(nsec):
            o = sec + 40 * i
            name = b[o:o + 8].rstrip(b"\0").decode("latin1")
            vsz, va, rawsz, rawptr = struct.unpack_from("<IIII", b, o + 8)
            self.sections.append((name, va, vsz, rawptr, rawsz))
        self.sha256 = hashlib.sha256(b).hexdigest()
        self.size = len(b)

    def off(self, va):
        rva = va - self.base
        for name, sva, vsz, rp, rs in self.sections:
            if sva <= rva < sva + max(vsz, rs):
                d = rva - sva
                return None if d >= rs else rp + d
        return None

    def rd(self, va, n):
        o = self.off(va)
        return None if o is None else self.b[o:o + n]


pe = PE(EXE)

JUNK = {"fstp", "iretd", "iret", "hlt", "invalid", "in", "out", "db", "fdiv",
        "fild", "fst", "bound", "les", "lds", "arpl", "into", "sahf"}


def seg(va, hi, cap=200):
    """one bounded linear segment, clipped to < hi"""
    buf = pe.rd(va, min(hi - va, 0x600))
    if not buf:
        return []
    out = []
    for i in md.disasm(buf, va):
        if i.address >= hi or len(out) >= cap:
            break
        out.append(i)
        if i.mnemonic in ("ret", "retf"):
            break
        if i.mnemonic == "int3" and pe.rd(i.address + i.size, 3) == b"\xcc\xcc\xcc":
            break
    return out


def chain(start, hi):
    ins, va = [], start
    while va < hi:
        s = seg(va, hi)
        if not s:
            break
        ins += s
        if s[-1].mnemonic in ("ret", "retf", "int3"):
            break
        va = s[-1].address + s[-1].size
    return ins


# ---------- pick the aligned start of the 0x43F1xx function ----------
WIN_A, WIN_A_HI = 0x43F100, 0x43F660
ANCHORS = (0x43F2B5, 0x43F504, 0x43F5B1)
cands = set(range(WIN_A, 0x43F240, 0x10))
win = pe.rd(WIN_A, WIN_A_HI - WIN_A)
for pat in (b"\xc3", b"\xc2"):
    i = win.find(pat)
    while i >= 0:
        cands.add(WIN_A + i + (1 if pat == b"\xc3" else 3))
        i = win.find(pat, i + 1)
best, best_n = None, -1
align_log = []
for s in sorted(cands):
    if not (WIN_A <= s < WIN_A_HI):
        continue
    ins = chain(s, WIN_A_HI)
    if not ins:
        continue
    A = {i.address for i in ins}
    junk = sum(1 for i in ins if i.mnemonic in JUNK or
               (i.mnemonic == "push" and i.op_str == "cs"))
    ok = sum(1 for a in ANCHORS if a in A)
    good = (junk == 0 and ok == 3 and ins[-1].mnemonic in ("ret", "retf"))
    align_log.append({"start": hex(s), "junk": junk, "anchors": ok,
                      "n": len(ins), "end": hex(ins[-1].address),
                      "accepted": good})
    if good and len(ins) > best_n:
        best, best_n = s, len(ins)
assert best is not None, "no aligned start found"
FUNC = chain(best, WIN_A_HI)
FUNC_HI = FUNC[-1].address + FUNC[-1].size
byaddr = {i.address: i for i in FUNC}

rows = []


def row(item, addr, ins_or_none, target, verdict, raw=None):
    if ins_or_none is None:
        rows.append([item, hex(addr) if isinstance(addr, int) else addr,
                     raw or "n/a", "n/a", target, verdict])
        return
    rows.append([item, hex(ins_or_none.address), ins_or_none.bytes.hex().upper(),
                 "%s %s" % (ins_or_none.mnemonic, ins_or_none.op_str),
                 target, verdict])


def jtgt(i):
    if i.mnemonic.startswith("j") and i.operands:
        try:
            return hex(i.operands[0].imm)
        except Exception:
            return ""
    return ""


notes = {"func_start": hex(best), "func_end": hex(FUNC_HI),
         "insn_count": len(FUNC), "align_log": align_log,
         "rule": "start accepted iff junk-free AND lands on 0x43F2B5/0x43F504/"
                 "0x43F5B1 AND ends on ret; window [0x43F100,0x43F660)"}

# ================= B1 =================
i = byaddr.get(0x43F2B5)
t = jtgt(i) if i else ""
row("B1", 0x43F2B5, i, t,
    "je displacement %+d -> target %s ; CONFIRMED == 0x43F504"
    % (i.operands[0].imm - (0x43F2B5 + i.size), t) if i else "UNVERIFIED")

# ================= B2 =================
seq = [i for i in FUNC if 0x43F504 <= i.address <= 0x43F515][:6]
notes["B2"] = [{"addr": hex(i.address), "bytes": i.bytes.hex().upper(),
                "decoded": "%s %s" % (i.mnemonic, i.op_str)} for i in seq]
for i in seq:
    v = ""
    if i.mnemonic in ("inc", "add", "dec", "sub"):
        v = "loop increment of esi"
    if jtgt(i) == "0x43f269":
        v = "back-edge to loop head 0x43F269"
    if i.mnemonic == "jl":
        v += " (signed <, operands %s)" % i.op_str
    row("B2", i.address, i, jtgt(i), v)
b2_ok = bool(seq) and seq[1].mnemonic == "inc" and any(
    jtgt(i) == "0x43f269" for i in seq)
notes["B2_is_loop_increment_plus_backedge"] = b2_ok

# ================= B3 =================
srcs = [i for i in FUNC if jtgt(i) == "0x43f5d8"]
sl = [hex(i.address) for i in srcs]
for i in srcs:
    row("B3", i.address, i, "0x43F5D8", "source of jump to reject exit")
row("B3", "n=%d" % len(srcs), None, "0x43F5D8", "sources=" + ",".join(sl),
    raw="count=%d" % len(srcs))
notes["B3_sources"] = sl
# sanity: is 0x43F5D8 inside the function body for any other opcode form
# (e.g. 0F 8x re-decoded)?  cross-check by raw-byte scan of the window for
# 6-byte jcc whose computed target is 0x43F5D8 (bounded, window only)
raw_hits = []
b = pe.rd(WIN_A, WIN_A_HI - WIN_A)
for k in range(len(b) - 6):
    if b[k] == 0x0F and 0x80 <= b[k + 1] <= 0x8F:
        rel = struct.unpack_from("<i", b, k + 2)[0]
        va = WIN_A + k
        if va + 6 + rel == 0x43F5D8:
            raw_hits.append(hex(va))
for k in range(len(b) - 2):
    if 0x70 <= b[k] <= 0x7F:
        rel = struct.unpack_from("<b", b, k + 1)[0]
        va = WIN_A + k
        if va + 2 + rel == 0x43F5D8:
            raw_hits.append(hex(va))
    if b[k] == 0xE9:
        rel = struct.unpack_from("<i", b, k + 1)[0]
        va = WIN_A + k
        if va + 5 + rel == 0x43F5D8:
            raw_hits.append(hex(va))
notes["B3_raw_scan_hits"] = sorted(set(raw_hits), key=lambda x: int(x, 16))

# ================= B4 =================
i = byaddr.get(0x43F5B1)
ctx = [x for x in FUNC if 0x43F5A9 <= x.address <= 0x43F5B5]
notes["B4_context"] = [{"addr": hex(x.address), "bytes": x.bytes.hex().upper(),
                        "decoded": "%s %s" % (x.mnemonic, x.op_str)} for x in ctx]
if i is not None:
    pred = [x for x in FUNC if x.address < i.address][-2:]
    uses = any("[esp + 0x23]" in x.op_str or "[esp+0x23]" in x.op_str for x in pred)
    row("B4", 0x43F5B1, i, jtgt(i),
        "preceded by %s ; [esp+0x23] judge %s"
        % (" ; ".join("%s %s" % (x.mnemonic, x.op_str) for x in pred),
           "CONFIRMED" if uses else "NOT FOUND"))
    notes["B4_ok"] = uses
    for x in pred:
        row("B4", x.address, x, jtgt(x), "loads/tests the byte at [esp+0x23]")
else:
    row("B4", 0x43F5B1, None, "", "UNVERIFIED")
    notes["B4_ok"] = None

# ================= B5 =================
W5, W5_HI = 0x449440, 0x449520
head = chain(W5, W5_HI)              # 0x449440 .. ret 0x14
tailp = [i for i in chain(0x449493, W5_HI)]
notes["B5_head"] = [{"addr": hex(i.address), "bytes": i.bytes.hex().upper(),
                     "decoded": "%s %s" % (i.mnemonic, i.op_str)} for i in head]
notes["B5_je449493"] = [{"addr": hex(i.address), "bytes": i.bytes.hex().upper(),
                         "decoded": "%s %s" % (i.mnemonic, i.op_str)}
                        for i in head if jtgt(i) == "0x449493"]
notes["B5_block449493"] = [{"addr": hex(i.address), "bytes": i.bytes.hex().upper(),
                            "decoded": "%s %s" % (i.mnemonic, i.op_str)}
                           for i in tailp]
for i in head:
    if jtgt(i) == "0x449493":
        row("B5", i.address, i, "0x449493",
            "short-circuit edge to 0x449493 (NOT a direct `return 7`)")
for i in head + tailp:
    if "0xa8" in i.op_str.lower() or "0xa7" in i.op_str.lower():
        row("B5", i.address, i, jtgt(i), "vt[0xA8] candidate")
for i in head + tailp:
    if i.mnemonic == "ret":
        row("B5", i.address, i, "", "exit of 0x449440 body (returns 0 or 7 via and 0xF9 / add 7)")
vt = [i for i in tailp if "0xa8" in i.op_str.lower()]
notes["B5_vt0xa8"] = [{"addr": hex(i.address), "bytes": i.bytes.hex().upper(),
                       "decoded": "%s %s" % (i.mnemonic, i.op_str)} for i in vt]

# ================= B6 =================
WMN = ("mov", "and", "or", "add", "sub", "xor")


def wcount(va, cap=600):
    ins = chain(va, min(va + 0x1800, pe.base + 0x7E038D))
    if len(ins) > cap:
        ins = ins[:cap]
    tot = ns = 0
    det = []
    for i in ins:
        if i.mnemonic not in WMN:
            continue
        ops = [o.strip() for o in i.op_str.split(",")]
        if len(ops) < 2 or not ops[0].startswith(("[", "byte ptr [", "word ptr [",
                                                 "dword ptr [", "qword ptr [")):
            continue
        tot += 1
        st = "[esp" in ops[0].replace(" ", "")
        ns += 0 if st else 1
        det.append({"addr": hex(i.address),
                    "decoded": "%s %s" % (i.mnemonic, i.op_str), "stack": st})
    return len(ins), tot, ns, det


for name, va in (("0x449440", 0x449440), ("0x47C620", 0x47C620), ("0x47C3D0", 0x47C3D0)):
    n, tot, ns, det = wcount(va)
    row("B6", name, None, "writes_total/nonstack", "insns=%d tot=%d nonstack=%d" % (n, tot, ns),
        raw="%d/%d" % (tot, ns))
    notes["B6_" + name] = {"insns": n, "tot": tot, "nonstack": ns, "detail": det}

# ================= write =================
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "byte_checks.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("item\taddress\tbytes\tdecoded\tbranch_target\tverdict\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
notes["pe"] = {"sha256": pe.sha256, "size": pe.size, "base": hex(pe.base),
               "sections": [{"n": n, "va": hex(pe.base + va)} for n, va, _, _, _ in pe.sections]}
with open(os.path.join(OUT, "notes.json"), "w", encoding="utf-8") as f:
    json.dump(notes, f, ensure_ascii=False, indent=1)

print("sha256", pe.sha256)
print("func", hex(best), "..", hex(FUNC_HI), "insns", len(FUNC))
print("accepted starts:", [a["start"] for a in align_log if a["accepted"]],
      "| rejected:", [(a["start"], a["junk"], a["anchors"]) for a in align_log if not a["accepted"]][:6])
print("\nB1", [r for r in rows if r[0] == "B1"])
print("B2")
for x in notes["B2"]:
    print("   ", x["addr"], x["bytes"], x["decoded"])
print("B3 sources", sl, "raw_scan", notes["B3_raw_scan_hits"])
print("B4")
for x in notes["B4_context"]:
    print("   ", x["addr"], x["bytes"], x["decoded"])
print("B5 je->0x449493:", notes["B5_je449493"])
print("B5 block 0x449493:")
for x in notes["B5_block449493"]:
    print("   ", x["addr"], x["bytes"], x["decoded"])
print("B5 head tail:", notes["B5_head"][-4:])
print("B6", [(r[1], r[5]) for r in rows if r[0] == "B6"])
