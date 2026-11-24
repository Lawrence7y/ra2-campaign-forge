# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B1 raw derive dump (read-only gamemd.exe / only writes this dir).
Method copied verbatim from R16_D1_FINAL/generate.py (authoritative D1 precedent).
"""
import io, os, sys, re, bisect, collections, hashlib, json

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
IB = 0x400000

import pefile
import capstone

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def read_tsv(p):
    L = io.open(p, encoding="utf-8-sig").read().splitlines()
    hdr = L[0].split("\t")
    rows = []
    for ln in L[1:]:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= len(hdr):
            rows.append(dict(zip(hdr, c)))
    return hdr, rows

# ---- PE image (read-only)
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    off = va - IB
    buf[off:off + len(d)] = d

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

def cstr(va, n=256):
    o = va - IB
    if o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

# ---- atlas
atlas = {}
for i, ln in enumerate(io.open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) < 2:
        continue
    try:
        atlas[int(c[0].strip(), 16)] = int(c[1])
    except ValueError:
        pass
starts = sorted(atlas)
sizes = [atlas[s] for s in starts]

def host_atlas(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and starts[i] <= va < starts[i] + sizes[i]:
        return starts[i], True
    return None, False

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def disasm_at(va, n=16):
    o = va - IB
    out = []
    for ins in md.disasm(bytes(buf[o:o + n]), va):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
    return out

def host_capstone(site):
    lo, hi = site - 0x100, site + 0x40
    insns = list(md.disasm(bytes(buf[lo - IB:hi - IB]), lo))
    prev = None
    for ins in insns:
        if ins.address < site and ins.mnemonic in ("ret", "retf"):
            prev = ins
    if prev:
        for ins in insns:
            if ins.address > prev.address and ins.mnemonic not in ("nop", "int3"):
                return ins.address, False
    return None, False

# ---- my 18 entries (B1)
TARGETS = ['0040B880','0040B930','0040F7C0','0040F870','0040FD90','0040FE40',
           '00410260','00413F80','0041C180','00431E80','00431F70','004322A0',
           '004324B0','004393D0','004393F0','00459EC0','0046B7E0','0046B890']

_, final_rows = read_tsv(FINAL)
fmap = {r["entry"]: r for r in final_rows}

recs = []
for e in TARGETS:
    fr = fmap.get(e)
    if not fr:
        recs.append(dict(entry=e, error="not_in_final"))
        continue
    vt = int(fr["vt"], 16)
    slot = int(fr["slot"])
    site = int(fr["install_site"], 16)
    col = u32(vt - 4)
    coff = u32(col + 4) if col else None
    td = u32(col + 12) if col else None
    mg = cstr(td + 8) if td else None
    h_atlas, in_atlas = host_atlas(site)
    h_cap, _ = host_capstone(site) if not in_atlas else (None, False)
    host = h_atlas if in_atlas else h_cap
    insns = disasm_at(site, 24)
    ins = insns[0] if insns else "?"
    om = re.search(r"\[([^\]]+)\]", ins)
    op = om.group(1).strip() if om else ""
    slot_val = u32(vt + slot * 4)
    # 6-point checks
    chk = [
        slot_val == int(e, 16),                          # 1 slot value == entry
        col is not None and u32(col) == 0,               # 2 COL sig == 0
        coff == 0,                                       # 3 COL offset == 0
        td is not None and (mg or "").startswith(".?A"), # 4 TD+8 mangled
        not (int(e, 16) <= site < int(e, 16) + atlas.get(int(e, 16), 0)), # 5 site outside entry
        vt is not None,                                  # 6 vt present
    ]
    recs.append(dict(
        entry=e, name=fr["name"], sub=fr["subsystem"], grade=fr["grade"],
        vt="%08X" % vt, slot=slot, site="%08X" % site,
        col=("%08X" % col) if col is not None else "未取得",
        coff=coff, td=("%08X" % td) if td is not None else "未取得",
        mg=mg or "未取得",
        host=("%08X" % host) if host else "未取得",
        in_atlas=in_atlas, ins=ins, insns=insns[:4], op=op,
        slot_val=("%08X" % slot_val) if slot_val is not None else "未取得",
        chk6=all(chk), chk=chk, note=fr.get("note", ""),
    ))

dump = dict(exe_sha=sha256(EXE), cov_sha=sha256(os.path.join(R14, "COVERAGE", "coverage.tsv")),
            cov_bytes=os.path.getsize(os.path.join(R14, "COVERAGE", "coverage.tsv")),
            recs=recs)
io.open(os.path.join(HERE, "raw_dump.json"), "w", encoding="utf-8").write(
    json.dumps(dump, ensure_ascii=False, indent=1))
print("wrote raw_dump.json")
for x in recs:
    if "error" in x:
        print(x["entry"], "ERROR", x["error"]); continue
    print("%s vt=%s slot=%d site=%s col=%s coff=%s td=%s mg=%s host=%s in_atlas=%s op=[%s] ins='%s' slotval=%s chk=%s note=%s" % (
        x["entry"], x["vt"], x["slot"], x["site"], x["col"], x["coff"], x["td"], x["mg"],
        x["host"], x["in_atlas"], x["op"], x["ins"], x["slot_val"], x["chk"], x["note"]))
