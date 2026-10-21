# verify_glm_probe.py -- independent re-verification probe (GLM binary reviewer)
# READ-ONLY w.r.t. gamemd.exe and every report/master file. Writes nothing.
# Run: PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py <stage>
# stages: pe | bytes | disasm | scan | hash
import sys, struct, math, re

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

from capstone import *
import capstone

DATA = open(EXE, "rb").read()

def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]

# ---------- raw PE parse (my own struct walk, no pefile) ----------
e_lfanew  = u32(DATA, 0x3C)
machine   = u16(DATA, e_lfanew + 4)
nsec      = u16(DATA, e_lfanew + 6)
sizeopt   = u16(DATA, e_lfanew + 20)
coffchar  = u16(DATA, e_lfanew + 22)
opt       = e_lfanew + 24
magic     = u16(DATA, opt)
ep_rva    = u32(DATA, opt + 16)
imagebase = u32(DATA, opt + 28)
secalign  = u32(DATA, opt + 32)
filealign = u32(DATA, opt + 36)
sizeofimg = u32(DATA, opt + 56)
subsys    = u16(DATA, opt + 68)
dllchar   = u16(DATA, opt + 70)

SECS = []
_st = opt + sizeopt
for i in range(nsec):
    o = _st + i * 40
    name = DATA[o:o+8].rstrip(b"\x00").decode("latin-1")
    vs, rva, rs, pr = u32(DATA, o+8), u32(DATA, o+12), u32(DATA, o+16), u32(DATA, o+20)
    ch = u32(DATA, o + 36)
    SECS.append({"name": name, "vs": vs, "rva": rva, "rs": rs, "pr": pr, "ch": ch,
                 "vastart": imagebase + rva, "vaend": imagebase + rva + vs})

def va2sec(va):
    for s in SECS:
        if s["vastart"] <= va < s["vastart"] + max(s["vs"], s["rs"]):
            return s
    return None

def va2off(va):
    s = va2sec(va)
    if s is None:
        return None, None
    return (va - imagebase - s["rva"]) + s["pr"], s

def read_va(va, n):
    off, s = va2off(va)
    inraw = s["rs"] - (off - s["pr"])
    if n <= inraw:
        return DATA[off:off + n]
    return DATA[off:off + inraw] + b"\x00" * (n - inraw)

CRASH   = 0x0084F2BA
TBLBASE = 0x0084F084
TBLEND  = 0x00859088

def h32(v): return "0x%08X" % (v & 0xFFFFFFFF)

# ---------- stage pe ----------
def stage_pe():
    print("== stage pe (raw struct parse) ==")
    print("file size            =", len(DATA))
    print("e_lfanew             =", h32(e_lfanew))
    print("machine              =", h32(machine), "(0x014C=i386)")
    print("NumberOfSections     =", nsec)
    print("COFF Characteristics =", h32(coffchar))
    print("OptionalMagic        =", h32(magic), "(0x010B=PE32)")
    print("AddressOfEntryPoint  =", h32(imagebase + ep_rva), "(RVA %s)" % h32(ep_rva))
    print("ImageBase            =", h32(imagebase))
    print("SectionAlignment     =", h32(secalign), " FileAlignment =", h32(filealign))
    print("SizeOfImage          =", h32(sizeofimg), "=> mapped [%s, %s)" % (h32(imagebase), h32(imagebase + sizeofimg)))
    print("Subsystem            =", subsys)
    print("DllCharacteristics   =", h32(dllchar), " NX_COMPAT(0x0100) set?", bool(dllchar & 0x0100))
    print()
    print("idx name      VA range                 VirtSize  RawPtr    RawSize   Char       delta      perm")
    for i, s in enumerate(SECS):
        delta = (imagebase + s["rva"]) - s["pr"]
        perm = ("R" if s["ch"] & 0x40000000 else "-") + \
               ("W" if s["ch"] & 0x80000000 else "-") + \
               ("X" if s["ch"] & 0x20000000 else "-")
        print("%2d  %-8s  %s-%s  %08X  %08X  %08X  %08X  %s  %s"
              % (i, s["name"], h32(s["vastart"]), h32(s["vaend"]), s["vs"], s["pr"], s["rs"], s["ch"], h32(delta), perm))
    print()
    s = va2sec(CRASH)
    off = (CRASH - imagebase - s["rva"]) + s["pr"]
    delta = CRASH - off
    print("crash VA            =", h32(CRASH))
    print("section             =", s["name"])
    print("intra-section off   =", h32(CRASH - s["vastart"]))
    print("file offset         =", h32(off), " delta(VA-off) =", h32(delta))
    print("mod 4               =", CRASH % 4, " mod 8 =", CRASH % 8)
    print("page                =", h32(CRASH & ~0xFFF), " page offset =", h32(CRASH & 0xFFF))
    print("section char        =", h32(s["ch"]),
          " MEM_WRITE", bool(s["ch"] & 0x80000000),
          "MEM_READ", bool(s["ch"] & 0x40000000),
          "MEM_EXEC", bool(s["ch"] & 0x20000000),
          "CNT_INIT_DATA", bool(s["ch"] & 0x40))
    rawvaend = s["vastart"] + s["rs"]
    print("file-backed extent  = [%s, %s)  page inside? %s" % (h32(s["vastart"]), h32(rawvaend),
          s["vastart"] <= (CRASH & ~0xFFF) < rawvaend))
    print("table base/end      =", h32(TBLBASE), h32(TBLEND), " base%4 =", TBLBASE % 4, " end%4 =", TBLEND % 4,
          " slots =", (TBLEND - TBLBASE) // 4, " rem =", (TBLEND - TBLBASE) % 4)
    print("crash home slot idx =", (0x0084F2B8 - TBLBASE) // 4, "(for VA 0x0084F2B8)")

# ---------- stage bytes ----------
def stage_bytes():
    print("== stage bytes ==")
    off, _ = va2off(CRASH)
    b = DATA[off:off + 32]
    print("file offset", h32(off))
    print("bytes:", " ".join("%02X" % x for x in b))
    expect = bytes.fromhex("DD3DC39CDE3D7D2CE03D2EBCE13DD64BE33D75DBE43D0C6BE63D99FAE73D1E8A")
    print("match report bytes :", b == expect)
    print("uint32 @CRASH      =", h32(struct.unpack_from("<I", b, 0)[0]))
    print("float  @CRASH      =", struct.unpack_from("<f", b, 0)[0])
    print()
    for va in (0x0084F2B0, 0x0084F2B4, 0x0084F2B8, 0x0084F2BC, 0x0084F2C0, 0x0084F2C4):
        o = va2off(va)[0]
        v = struct.unpack_from("<f", DATA, o)[0]
        idx = (va - TBLBASE) // 4
        print("float @%s (slot %d) = %.7f   uint32=%s" % (h32(va), idx, v, h32(struct.unpack_from("<I", DATA, o)[0])))
    print()
    c = 2 * math.pi / 8192
    print("2*pi/8192           = %.10f" % c)
    for k in (0, 1, 2, 3, 112, 140, 141, 142, 143, 189, 1000, 1024, 2047, 2048, 2049, 4096, 6144, 8191, 8192, 8193, 10240):
        va = TBLBASE + 4 * k
        t = struct.unpack("<f", read_va(va, 4))[0]
        print("t[%5d] @%s = %+.7f   sin(k*2pi/8192)=%+.7f   k*c=%+.7f"
              % (k, h32(va), t, math.sin(k * c), k * c))
    t140 = struct.unpack("<f", read_va(TBLBASE + 4 * 140, 4))[0]
    t141 = struct.unpack("<f", read_va(TBLBASE + 4 * 141, 4))[0]
    t142 = struct.unpack("<f", read_va(TBLBASE + 4 * 142, 4))[0]
    print()
    print("t141-t140 = %.10f   t142-t141 = %.10f   (2pi/8192 = %.10f)" % (t141 - t140, t142 - t141, c))
    print()
    for va, fmt in ((0x007E8988, "<d"), (0x008223B0, "<f"), (0x007E8970, "<d")):
        raw = read_va(va, struct.calcsize(fmt))
        v = struct.unpack(fmt, raw)[0]
        print("value @%s (%s) = %.10f  (raw %s)" % (h32(va), fmt, v, raw.hex()))
    print("8192/pi = %.10f   2048/pi = %.10f   2*pi/8192 = %.10f" % (8192 / math.pi, 2048 / math.pi, c))

# ---------- stage disasm ----------
_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def dis(va, nbytes, label=""):
    print("-- %s @%s --" % (label, h32(va)))
    off, _ = va2off(va)
    code = DATA[off:off + nbytes]
    for ins in _md.disasm(code, va):
        print("0x%08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

def stage_disasm():
    print("== stage disasm (capstone %s, skipdata=True) ==" % capstone.__version__)
    dis(0x0084F2BA, 16, "crash VA decoded from disk bytes")
    print()
    dis(0x004CB080, 0x4CB160 - 0x4CB080, "LUT generator / consumer cluster A")
    print()
    dis(0x004CB160, 0x4CB200 - 0x4CB160, "consumer cluster B")
    print()
    dis(0x004CACD0, 0x4CAD60 - 0x4CACD0, "consumer cluster C")
    print()
    dis(0x007C5F00, 0x60, "round-helper 0x007C5F00")
    print()
    dis(0x0054A4E0, 0x54A590 - 0x0054A4E0, "crash2 enclosing routine")
    print()
    dis(0x007C8B3D, 0x10, "thunk 0x007C8B3D")
    print()
    dis(0x007C93E8, 0x20, "thunk 0x007C93E8")
    print()
    dis(0x007CF7BD, 0x90, "SBH free core 0x007CF7BD")
    print()
    dis(0x007CFC80, 0x40, "RC-1 guard 0x007CFC9B region")
    print()
    dis(0x007C8E17, 0x10, "malloc thunk 0x007C8E17")
    print()
    dis(0x007C9442, 0x20, "malloc 0x007C9442")
    print()
    dis(0x00B93000, 0x20, ".detour head (VA 0x00B93000)")

# ---------- stage scan ----------
NARROW_LO, NARROW_HI = 0x0084F200, 0x0084F400
WIDER_LO,  WIDER_HI  = 0x0084E000, 0x00851000
DATA_LO,   DATA_HI   = 0x00812000, 0x00B79BE4
TBLDISPS = {0x0084F084, 0x0084F088, 0x00859088}

def stage_scan():
    print("== stage scan (full .text, capstone skipdata) ==")
    text = va2sec(0x00401000)
    tva, tlen = text["vastart"], text["vs"]
    code = DATA[text["pr"]:text["pr"] + tlen]
    n_ins = 0
    last_end = tva
    exact = []            # imm/disp == 0x84F2BA
    narrow = []           # any imm/disp in narrow band, or write-disp in band
    wider = {}            # (value, kind) -> [(va, mnem, op, is_write)]
    tbl = []              # disp/imm == table base/end
    b78 = []              # 0xB78B94/98 refs
    mask13 = []           # imm 0x80001FFF
    br_band = []          # jmp/call target in narrow band
    idx_stores = 0        # indexed stores to .data disp
    idx_store_tbl = []    # indexed stores with disp near table window
    for ins in _md.disasm(code, tva):
        n_ins += 1
        last_end = max(last_end, ins.address + ins.size)
        if ins.id == 0 or not ins.operands:
            continue
        if ins.group(CS_GRP_JUMP) or ins.group(CS_GRP_CALL):
            for op in ins.operands:
                if op.type == CS_OP_IMM and NARROW_LO <= (op.imm & 0xFFFFFFFF) <= NARROW_HI:
                    br_band.append((ins.address, ins.mnemonic, ins.op_str))
        for op in ins.operands:
            if op.type == CS_OP_IMM and (op.imm & 0xFFFFFFFF) == 0x80001FFF:
                mask13.append((ins.address, ins.mnemonic, ins.op_str))
        for op in ins.operands:
            v = None
            kind = None
            is_w = False
            has_idx = False
            if op.type == CS_OP_IMM:
                v, kind = op.imm & 0xFFFFFFFF, "imm"
            elif op.type == CS_OP_MEM:
                m = op.mem
                is_w = bool(op.access & CS_AC_WRITE)
                has_idx = (m.index != 0)
                if m.disp:
                    v, kind = m.disp & 0xFFFFFFFF, "disp"
                if is_w and has_idx and DATA_LO <= (m.disp & 0xFFFFFFFF) <= DATA_HI:
                    idx_stores += 1
                    if 0x0084E000 <= (m.disp & 0xFFFFFFFF) <= 0x0085A000:
                        idx_store_tbl.append((ins.address, ins.mnemonic, ins.op_str, m.disp & 0xFFFFFFFF))
                if is_w and NARROW_LO <= (m.disp & 0xFFFFFFFF) <= NARROW_HI:
                    narrow.append((ins.address, ins.mnemonic, ins.op_str, "WRITE disp-in-band", has_idx))
            if v is None:
                continue
            if v == 0x0084F2BA:
                exact.append((ins.address, ins.mnemonic, ins.op_str, kind))
            elif NARROW_LO <= v <= NARROW_HI:
                narrow.append((ins.address, ins.mnemonic, ins.op_str,
                               kind + "=" + h32(v) + (" WRITE" if is_w else ""), has_idx))
            elif WIDER_LO <= v <= WIDER_HI:
                wider.setdefault((v, kind), []).append((ins.address, ins.mnemonic, ins.op_str, is_w))
            if kind in ("disp", "imm") and v in TBLDISPS:
                tbl.append((ins.address, ins.mnemonic, ins.op_str))
            if v == 0x00B78B94 or v == 0x00B78B98:
                b78.append((ins.address, ins.mnemonic, ins.op_str))
    print("decoded instructions:", n_ins, " last end VA:", h32(last_end), "(.text virtual end %s)" % h32(tva + tlen))
    print()
    print("[exact 0x0084F2BA as imm/disp in .text]:", len(exact))
    for e in exact[:20]:
        print("   0x%08X %s %s (%s)" % e)
    print()
    print("[narrow band 0x0084F200-0x0084F400 hits]:", len(narrow))
    for e in narrow[:80]:
        print("   0x%08X %-8s %s   [%s idx=%s]" % (e[0], e[1], e[2], e[3], e[4]))
    print()
    print("[jmp/call targets into narrow band]:", len(br_band))
    for e in br_band[:20]:
        print("   0x%08X %s %s" % e)
    print()
    print("[wider band 0x0084E000-0x00851000 distinct (value,kind)]:", len(wider))
    for (v, kind), lst in sorted(wider.items()):
        vas = ", ".join("0x%08X" % x[0] for x in lst[:10])
        wr = any(x[3] for x in lst)
        print("   %s %s  n=%d write=%s  sites: %s" % (h32(v), kind, len(lst), wr, vas))
    print()
    print("[table disp/imm refs 0x0084F084/0x0084F088/0x00859088]:", len(tbl))
    for e in tbl[:60]:
        print("   0x%08X %-8s %s" % e)
    print()
    print("[0x00B78B94 / 0x00B78B98 refs in .text]:", len(b78))
    for e in b78[:30]:
        print("   0x%08X %-8s %s" % e)
    print()
    print("[imm 0x80001FFF sites]:", len(mask13))
    for e in mask13[:20]:
        print("   0x%08X %-8s %s" % e)
    print()
    print("[indexed stores to .data disp total]:", idx_stores)
    print("[indexed stores disp in 0x0084E000-0x0085A000]:", len(idx_store_tbl))
    for e in idx_store_tbl[:60]:
        print("   0x%08X %s %s (disp %s)" % e)
    print()
    print("[raw LE dword 0x0084F2BA (BA F2 84 00) in whole file]:", DATA.count(bytes.fromhex("BAF28400")))
    print("[raw LE dword 0xFE00FFFF (FF FF 00 FE) in whole file]:", DATA.count(bytes.fromhex("FFFF00FE")))
    print("[raw 0xFEFEFEFE]:", DATA.count(bytes.fromhex("FEFEFEFE")),
          " [CDCDCDCD]:", DATA.count(bytes.fromhex("CDCDCDCD")),
          " [DDDDDDDD]:", DATA.count(bytes.fromhex("DDDDDDDD")),
          " [BABABABA]:", DATA.count(bytes.fromhex("BABABABA")),
          " [F1F1F1F1]:", DATA.count(bytes.fromhex("F1F1F1F1")))
    pat = re.compile(b"|".join(re.escape(struct.pack("<I", v)) for v in range(NARROW_LO, NARROW_HI + 1)))
    hits = [m.start() for m in pat.finditer(DATA)]
    print("[raw LE dwords pointing into narrow band]:", len(hits))
    for o in hits[:40]:
        sec = "?"
        for s in SECS:
            if s["pr"] <= o < s["pr"] + s["rs"]:
                sec = s["name"]
        print("   file 0x%06X (%s) -> %s" % (o, sec, h32(struct.unpack_from("<I", DATA, o)[0])))
    print()
    det = va2sec(0x00B93000)
    dcode = DATA[det["pr"]:det["pr"] + det["vs"]]
    dhits = []
    dn = 0
    for ins in _md.disasm(dcode, det["vastart"]):
        dn += 1
        if ins.id == 0:
            continue
        for op in ins.operands:
            if op.type == CS_OP_IMM and NARROW_LO <= (op.imm & 0xFFFFFFFF) <= NARROW_HI:
                dhits.append((ins.address, ins.mnemonic, ins.op_str))
            if op.type == CS_OP_MEM and NARROW_LO <= (op.mem.disp & 0xFFFFFFFF) <= NARROW_HI:
                dhits.append((ins.address, ins.mnemonic, ins.op_str))
    print("[.detour instructions decoded]:", dn, " [.detour narrow-band refs]:", len(dhits))
    for e in dhits[:20]:
        print("   0x%08X %s %s" % e)

# ---------- stage hash ----------
def stage_hash():
    print("== stage hash ==")
    import hashlib, os
    print("main:", EXE)
    print("  sha256:", hashlib.sha256(DATA).hexdigest())
    print("  size  :", len(DATA))
    p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe"
    print("copy exists:", os.path.exists(p), "->", p)
    if os.path.exists(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        print("  copy sha256:", h.hexdigest())
        print("  copy size  :", os.path.getsize(p))

if __name__ == "__main__":
    {"pe": stage_pe, "bytes": stage_bytes, "disasm": stage_disasm,
     "scan": stage_scan, "hash": stage_hash}[sys.argv[1]]()
