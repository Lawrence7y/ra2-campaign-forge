
# -*- coding: utf-8 -*-
"""R17-AUDIT-R30 independent static auditor (read-only).

NO reuse of the executor's work.py. Fresh implementation from scratch.

Scope (bounded, declared):
  decode windows (bytes actually fed to the decoder):
    0x4493FC + 0x44   preceding-function tail + padding + entry anchor
    0x449440 + 0x75   the 117-byte body (exact-byte, ends on instruction boundary)
    0x4494B5 + 0x10   tail padding + next entry
  data reads (4 bytes each, not decoded):
    0x7E3FE0 (vtable slot #73), 0x7E4068 (vtable slot #107)
  control-only raw byte scan: whole .text (0x3E0000 B) for direct branches to
    0x449440 -- reported as NOT instruction-confirmed; used only to show no direct
    caller exists (consistent with R14_COMMON 2.9 排除表 #2).

Total bytes fed to the decoder: 0x44 + 0x75 + 0x10 = 0xC9 = 201.
No process is created. No file under R17_R30_SLOT107_BODY is written.
"""
import hashlib, struct, sys, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT = "73201CC0"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R30"

raw = open(IMG, "rb").read()
sha = hashlib.sha256(raw).hexdigest().upper()
if not sha.startswith(EXPECT):
    sys.exit("FATAL: image hash mismatch (got %s); audit VOID" % sha)

pe = struct.unpack_from("<I", raw, 0x3C)[0]
assert raw[pe:pe+4] == b"PE\0\0"
nsec = struct.unpack_from("<H", raw, pe + 6)[0]
optsz = struct.unpack_from("<H", raw, pe + 20)[0]
opt = pe + 24
magic = struct.unpack_from("<H", raw, opt)[0]
IMAGEBASE = struct.unpack_from("<I", raw, opt + 28)[0] if magic == 0x10b else struct.unpack_from("<Q", raw, opt + 24)[0]
secs = []
s0 = opt + optsz
for i in range(nsec):
    o = s0 + i * 40
    nm = raw[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, ra = struct.unpack_from("<IIII", raw, o + 8)
    secs.append((nm, va, vs, ra, rs))

def boa(va):
    r = va - IMAGEBASE
    for n, v, t, ra, rs in secs:
        if v <= r < v + max(t, rs):
            return ra + r - v
    raise ValueError("va 0x%X not mapped" % va)

def rd(va, n):
    o = boa(va)
    return raw[o:o + n]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

rows = []          # (addr, bytes, mnemonic, opstr, tag)
decode_bytes = 0

def dump(va, n, tag):
    global decode_bytes
    decode_bytes += n
    ins = list(md.disasm(rd(va, n), va))
    for i in ins:
        rows.append((i.address, i.bytes.hex(" "), i.mnemonic, i.op_str, tag))
    return ins

# ---------- A1 : boundary by instruction boundaries, not C3/C2 byte scan -----
pre = dump(0x4493FC, 0x44, "pre")
body = dump(0x449440, 0x75, "body")
post = dump(0x4494B5, 0x10, "post")

# the 117 bytes must end exactly on an instruction boundary
assert body[-1].address + body[-1].size == 0x4494B5, "body does not end on boundary"
assert body[0].address == 0x449440
rets = [i for i in body if i.mnemonic == "ret"]
body_end = body[-1].address + body[-1].size
length = body_end - 0x449440

# ---------- A2 : rel32 recomputation ---------------------------------------
def rel32(site):
    b = rd(site, 5)
    assert b[0] == 0xE8
    r = struct.unpack_from("<i", b, 1)[0]
    return (site + 5 + r) & 0xFFFFFFFF

t_449482 = rel32(0x449482)
t_43F2AE = rel32(0x43F2AE)

# ---------- A3 : two-path CFG ---------------------------------------------
by = {i.address: i for i in body}
JCC = {}
for i in body:
    if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
        JCC[i.address] = int(i.op_str, 16)

def succ(a):
    i = by[a]
    if i.mnemonic == "ret":
        return []
    nxt = a + i.size
    if a in JCC and i.mnemonic != "jmp":
        return [nxt, JCC[a]]
    if i.mnemonic == "jmp":
        return [JCC[a]]
    return [nxt]

paths = []
def walk(a, acc, d):
    if d > 40 or a not in by:
        return
    i = by[a]
    acc = acc + [i]
    if i.mnemonic == "ret":
        paths.append(acc)
        return
    for s in succ(a):
        walk(s, acc, d + 1)
walk(0x449440, [], 0)

def tail_sig(p):
    sig = []
    for i in p:
        if i.mnemonic in ("neg", "sbb", "and", "add") and i.address >= 0x449487:
            sig.append(i.bytes.hex(" "))
    return sig

# ---------- A4 : nature --------------------------------------------------
writes, nonstack = [], []
for i in body:
    if i.mnemonic in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec", "stos", "xchg"):
        dst = i.op_str.split(",")[0].strip()
        if dst.startswith(("byte ptr [", "word ptr [", "dword ptr [", "[", "qword ptr [")):
            rec = (i.address, i.bytes.hex(" "), "%s %s" % (i.mnemonic, i.op_str))
            writes.append(rec)
            if "esp" not in dst and "ebp" not in dst:
                nonstack.append(rec)
vt_install = [w for w in writes if w[2].startswith("mov dword ptr [e") is False and "offset" in w[2]]
delete_sig = [i for i in body if i.mnemonic in ("test", "or", "and")
              and i.operands and i.operands[-1].type == 2 and i.operands[-1].imm == 1
              and ("al" in i.op_str.split(",")[0] or "[" in i.op_str.split(",")[0])]

# ---------- output ------------------------------------------------------
with open(OUT + r"\body_bytes.tsv", "w", encoding="utf-8") as f:
    f.write("# image\t%s\n" % IMG)
    f.write("# sha256\t%s\n" % sha)
    f.write("# imagebase\t0x%X\n" % IMAGEBASE)
    f.write("# decode_bytes_total\t%d (0x%X)\n" % (decode_bytes, decode_bytes))
    f.write("addr\tbytes\tmnemonic\top_str\ttag\n")
    for a, b, m, o, t in rows:
        f.write("0x%08X\t%s\t%s\t%s\t%s\n" % (a, b, m, o, t))

slot73 = struct.unpack_from("<I", rd(0x7E3FE0, 4))[0]
slot107 = struct.unpack_from("<I", rd(0x7E4068, 4))[0]

summary = {
    "image": IMG, "sha256": sha, "size": len(raw), "imagebase": IMAGEBASE,
    "decode_bytes_total": decode_bytes,
    "body_entry": "0x449440", "body_end": hex(body_end), "body_len": length,
    "rets": [(hex(i.address), i.bytes.hex(" "), i.op_str) for i in rets],
    "rel32_0x449482": hex(t_449482), "rel32_0x43F2AE": hex(t_43F2AE),
    "same_target": t_449482 == t_43F2AE,
    "paths": [{"exit": hex(p[-1].address), "n": len(p),
               "calls": [(hex(i.address), i.op_str) for i in p if i.mnemonic == "call"],
               "tail": tail_sig(p)} for p in paths],
    "writes_total": len(writes), "nonstack_writes": len(nonstack),
    "delete_signature": len(delete_sig),
    "slot_0x7E3FE0": hex(slot73), "slot_0x7E4068": hex(slot107),
}
import json
print(json.dumps(summary, indent=1, ensure_ascii=False))
