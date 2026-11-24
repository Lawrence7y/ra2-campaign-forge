# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B2 : independent read-only re-derivation of all 18 B2 rows.

Independence notes
------------------
* Own PE parser (no pefile / no import of R16_PROBE_4FINAL.final).
* Own RTTI resolver, own install-site enumeration, own host-boundary scan.
* Executor's verify.py imported R16_PROBE_4FINAL.final and reused its atlas for
  check (5) and its Image for every byte read -> not independent. This does not.
Read-only: gamemd.exe opened rb. Writes only into this audit directory.
"""
import io, os, sys, json, re, struct, bisect, hashlib, collections

sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
ATLAS = os.path.join(os.path.dirname(os.path.dirname(R14)), "lead",
                     "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
EXE_SHA_EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

# ----------------------------------------------------------------- own PE reader
class PE(object):
    def __init__(self, path):
        self.raw = open(path, "rb").read()
        self.sha = hashlib.sha256(self.raw).hexdigest().upper()
        d = self.raw
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[pe:pe + 4] == b"PE\0\0", "not PE"
        nsec = struct.unpack_from("<H", d, pe + 6)[0]
        optsize = struct.unpack_from("<H", d, pe + 20)[0]
        opt = pe + 24
        magic = struct.unpack_from("<H", d, opt)[0]
        assert magic == 0x10B, "not PE32"
        self.base = struct.unpack_from("<I", d, opt + 28)[0]
        self.image_size = struct.unpack_from("<I", d, opt + 56)[0]
        st = opt + optsize
        self.secs = []
        for i in range(nsec):
            off = st + i * 40
            nm = d[off:off + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rsize, rptr = struct.unpack_from("<IIII", d, off + 8)
            ch = struct.unpack_from("<I", d, off + 36)[0]
            self.secs.append(dict(name=nm, va=self.base + va, vsize=vsize,
                                  rsize=rsize, rptr=rptr, ch=ch))
        # full virtual image buffer (VirtualSize aware: .bss style sections)
        end = max(s["va"] + max(s["vsize"], s["rsize"]) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        self.mapped = bytearray(len(self.buf))
        for s in self.secs:
            o = s["va"] - self.base
            n = min(s["rsize"], len(self.raw) - s["rptr"])
            if n > 0:
                self.buf[o:o + n] = self.raw[s["rptr"]:s["rptr"] + n]
            # virtual-only tail counts as mapped (zero fill) for .data/.bss
            m = max(s["vsize"], s["rsize"])
            self.mapped[o:o + m] = b"\x01" * m

    def in_image(self, va):
        if va is None:
            return False
        o = va - self.base
        return 0 <= o < len(self.buf)

    def u32(self, va):
        o = va - self.base
        if o < 0 or o + 4 > len(self.buf):
            return None
        return struct.unpack_from("<I", self.buf, o)[0]

    def cstr(self, va, n=256):
        o = va - self.base
        if o < 0 or o >= len(self.buf):
            return None
        e = self.buf.find(b"\x00", o, min(o + n, len(self.buf)))
        if e < 0:
            return None
        return bytes(self.buf[o:e]).decode("latin-1", "replace")

    def sec_of(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                return s["name"]
        return None

    def code(self, va, n):
        o = va - self.base
        if o < 0:
            return b""
        return bytes(self.buf[o:o + n])


pe = PE(EXE)
IB = pe.base
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

COL_RE = re.compile(r"^\.\?A")


def rtti(vt):
    """Independent: vt-4 must be a Complete Object Locator."""
    col = pe.u32(vt - 4)
    if not pe.in_image(col):
        return None
    sig = pe.u32(col)
    if sig != 0:
        return None
    off = pe.u32(col + 4)
    td = pe.u32(col + 12)
    if not pe.in_image(td):
        return None
    nm = pe.cstr(td + 8)
    if not nm or not COL_RE.match(nm):
        return None
    return dict(col=col, sig=sig, off=off, td=td, name=nm)


def tables():
    """Independent enumeration: every 4-aligned slot in .rdata/.data whose
    vt-4 resolves to a COL."""
    out = {}
    for s in pe.secs:
        if s["name"] not in (".rdata", ".data"):
            continue
        n = min(max(s["vsize"], s["rsize"]), s["rsize"] or s["vsize"])
        for k in range(n // 4):
            va = s["va"] + k * 4
            r = rtti(va)
            if r:
                out[va] = dict(vt=va, col=r["col"], cls=r["name"], sec=s["name"])
    return out


TABS = tables()

# ---------------------------------------------------------------- install sites
def build_store_index():
    """One linear sweep of .text: every `mov [mem], imm32` with imm in image space.
    Returns {imm: [ {site,text,bytes,mem} ] } in ascending site order."""
    t = next(s for s in pe.secs if s["name"] == ".text")
    code = bytes(pe.buf[t["va"] - IB: t["va"] - IB + max(t["vsize"], t["rsize"])])
    idx = collections.defaultdict(list)
    for insn in md.disasm(code, t["va"]):
        if insn.id == 0:
            continue
        if insn.mnemonic != "mov" or len(insn.operands) != 2:
            continue
        a, b = insn.operands
        if a.type != X.X86_OP_MEM or b.type != X.X86_OP_IMM:
            continue
        imm = b.imm & 0xFFFFFFFF
        if not (IB <= imm < IB + pe.image_size):
            continue
        idx[imm].append(dict(site=insn.address,
                             text="%s %s" % (insn.mnemonic, insn.op_str),
                             bytes=insn.bytes.hex(" "),
                             base=a.mem.base, index=a.mem.index, disp=a.mem.disp))
    for k in idx:
        idx[k].sort(key=lambda x: x["site"])
    return idx


STORE_IDX = build_store_index()


def find_stores(target_imm):
    return STORE_IDX.get(target_imm, [])


# ---------------------------------------------------------------- atlas / hosts
def load_atlas():
    d = {}
    if not os.path.isfile(ATLAS):
        return d
    with io.open(ATLAS, encoding="utf-8-sig") as f:
        f.readline()
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) < 2:
                continue
            try:
                d[int(c[0].strip(), 16)] = int(c[1])
            except ValueError:
                pass
    return d


ATLAS = load_atlas()
ASTARTS = sorted(ATLAS)
ASIZES = [ATLAS[a] for a in ASTARTS]


def atlas_func(va):
    i = bisect.bisect_right(ASTARTS, va) - 1
    if i >= 0 and ASTARTS[i] <= va < ASTARTS[i] + ASIZES[i]:
        return ASTARTS[i]
    return None


PAD = (0xCC, 0x90, 0x00, 0x66)


def own_func_start(site):
    """Own boundary scan (deliberately NOT the executor's 'last ret before site'):
    walk back over padding, then take the first byte after the padding run."""
    o = site - IB
    j = o
    while j > 8 and pe.buf[j - 1] in PAD:
        j -= 1
    if j < o:
        while j > 8 and pe.buf[j - 1] in PAD:
            j -= 1
        return IB + j
    return None


def func_extent(start, cap=0x3000):
    """Linear extent of the function starting at `start`: decode until padding or
    an unconditional terminator followed by padding; returns max end address."""
    insns = list(md.disasm(pe.code(start, cap), start))
    end = start
    for ins in insns:
        if ins.id == 0:
            break
        end = ins.address + ins.size
        if ins.mnemonic in ("ret", "retf") or (ins.mnemonic == "ret" and ins.op_str):
            # keep going only if next byte is not padding
            nx = ins.address + ins.size
            if pe.buf[nx - IB] in PAD:
                break
        if ins.mnemonic == "jmp" and ins.op_str.startswith("0x"):
            break
    return end


def window(va, before=22, after=8):
    """Instruction window [va-before*?, va+after] with correct instruction alignment:
    scan back up to 96 bytes for a decode that lands exactly on va."""
    for back in range(1, 96):
        lo = va - back
        insns = list(md.disasm(pe.code(lo, back + after * 8), lo))
        hit = None
        for i, ins in enumerate(insns):
            if ins.address == va:
                hit = i
                break
            if ins.address > va:
                break
        if hit is not None and hit >= min(before, 1):
            a = max(0, hit - before)
            return insns[a:hit + after + 1], hit - a
    insns = list(md.disasm(pe.code(va, after * 8), va))
    return insns, 0


def regs_written(insn):
    try:
        _r, w = insn.regs_access()
        return set(w)
    except Exception:
        return set()


def track_def(insns, idx, reg, max_back=40):
    """Backward: nearest preceding instruction writing `reg`."""
    for j in range(idx - 1, max(-1, idx - 1 - max_back), -1):
        if reg in regs_written(insns[j]):
            return j, insns[j]
    return None, None


def dtor_signature(start, end):
    """scalar deleting destructor tail: test byte ptr [esp+X],1 ; call 0x7c8b3d ; ret 4"""
    insns = list(md.disasm(pe.code(start, end - start), start))
    texts = ["%s %s" % (i.mnemonic, i.op_str) for i in insns]
    joined = "\n".join(texts)
    t = re.search(r"test byte ptr \[esp[^\]]*\], 1", joined)
    c = re.search(r"call 0x7c8b3d", joined)
    r = re.search(r"^ret 4$", joined, re.M)
    return dict(has_test=bool(t), has_del=bool(c), has_ret4=bool(r),
                triple=bool(t and c and r), n_insn=len(insns))


# ---------------------------------------------------------------- inputs
def read_cov():
    m = {}
    with io.open(COV, encoding="utf-8-sig") as f:
        f.readline()
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= 8:
                m[c[0].strip().upper()] = c
    return m


def read_delta():
    L = io.open(os.path.join(HERE, "..", "R16_D1_WIDE_B2", "delta.tsv"),
                encoding="utf-8").read().splitlines()
    return [ln.split("\t") for ln in L if ln.strip()]


def read_fields():
    L = io.open(os.path.join(HERE, "..", "R16_D1_WIDE_B2", "fields.tsv"),
                encoding="utf-8").read().splitlines()
    h = L[0].split("\t")
    return [dict(zip(h, ln.split("\t"))) for ln in L[1:] if ln.strip()]


def read_final():
    m = {}
    with io.open(FINAL, encoding="utf-8-sig") as f:
        h = f.readline().rstrip("\r\n").split("\t")
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= len(h):
                m[c[0]] = dict(zip(h, c))
    return m


def read_tsv(path):
    L = io.open(path, encoding="utf-8-sig").read().splitlines()
    h = L[0].split("\t")
    return [dict(zip(h, ln.split("\t"))) for ln in L[1:] if ln.strip()]


COVM = read_cov()
DELTA = read_delta()
FIELDS = read_fields()
FIN = read_final()
SIEVE_ROWS = read_tsv(SIEVE)
DH = DELTA[0]
DROWS = DELTA[1:]

# ---------------------------------------------------------------- per row
def analyze(entry):
    ei = int(entry, 16)
    fr = FIELDS and next((r for r in FIELDS if r["entry"] == entry), None)
    vt = int(fr["vt"], 16) if fr and fr["vt"] else None
    slot = int(fr["slot"]) if fr and fr["slot"] else None
    site = int(fr["install_site"], 16) if fr and fr["install_site"] else None
    rec = dict(entry=entry, vt=vt, slot=slot, site=site)
    r = rtti(vt) if vt else None
    rec["rtti"] = r
    rec["slot_val"] = pe.u32(vt + slot * 4) if vt is not None and slot is not None else None
    # chk1..6 independent
    chk = {}
    chk["1_slot_holds_entry"] = (rec["slot_val"] == ei)
    chk["2_col_sig0"] = bool(r and r["sig"] == 0)
    chk["3_col_off0"] = bool(r and r["off"] == 0)
    chk["4_td_mangled"] = bool(r and r["name"].startswith(".?A"))
    # 5: install site outside the ENTRY function body (own extent, + atlas cross-check)
    e_end_own = func_extent(ei)
    e_sz_atlas = ATLAS.get(ei)
    inside_own = ei <= site < e_end_own
    inside_atlas = bool(e_sz_atlas) and (ei <= site < ei + e_sz_atlas)
    chk["5_site_outside_entry"] = not inside_own and not inside_atlas
    chk["6_vt_obtained"] = vt is not None and r is not None
    rec["chk"] = chk
    rec["entry_extent_own"] = (ei, e_end_own)
    rec["entry_sz_atlas"] = e_sz_atlas
    rec["site_sec"] = pe.sec_of(site) if site else None

    # install instruction(s) for this vt
    stores = find_stores(vt) if vt else []
    rec["all_stores"] = ["%08X" % s["site"] for s in stores]
    st = next((s for s in stores if s["site"] == site), None)
    rec["site_insn"] = st
    # operand form + absolute target section
    insns, idx = window(site, before=22, after=6)
    rec["win"] = ["%08X: %s %s" % (i.address, i.mnemonic, i.op_str) for i in insns]
    rec["win_idx"] = idx
    cur = insns[idx] if idx < len(insns) else None
    mem = None
    if cur is not None and len(cur.operands) == 2 and cur.operands[0].type == X.X86_OP_MEM:
        mem = cur.operands[0].mem
    form = None
    tgt = None
    if mem is not None:
        has_base = mem.base != 0
        has_idx = mem.index != 0
        if not has_base and not has_idx:
            form = "mov_abs"
            tgt = mem.disp & 0xFFFFFFFF
            rec["abs_target"] = "%08X" % tgt
            rec["abs_target_sec"] = pe.sec_of(tgt)
            rec["abs_target_in_image"] = pe.in_image(tgt)
        else:
            form = "mov_reg"
            base = cur.reg_name(mem.base) if has_base else None
            rec["base_reg"] = base
            rec["disp"] = mem.disp
            rec["stack_target"] = (base in ("esp", "ebp"))
            # provenance of base register
            j, d = track_def(insns, idx, mem.base)
            rec["def_idx"] = j
            rec["def_insn"] = ("%08X: %s %s" % (d.address, d.mnemonic, d.op_str)) if d else None
            chain = []
            k, dj = j, d
            for _ in range(4):
                if dj is None or j is None:
                    break
                chain.append("%08X: %s %s" % (dj.address, dj.mnemonic, dj.op_str))
                src = None
                if len(dj.operands) == 2 and dj.operands[1].type == X.X86_OP_REG:
                    src = dj.operands[1].reg
                elif len(dj.operands) == 2 and dj.operands[1].type == X.X86_OP_MEM:
                    src = dj.operands[1].mem.base
                if src is None:
                    break
                k2, d2 = track_def(insns, j, src, max_back=30)
                j, dj = k2, d2
            rec["def_chain"] = chain
    rec["form_actual"] = form

    # host function
    host_atlas = atlas_func(site) if site else None
    rec["host_atlas"] = "%08X" % host_atlas if host_atlas else None
    rec["host_claimed"] = fr["install_host"] if fr else None
    hs = host_atlas or own_func_start(site)
    rec["host_own"] = "%08X" % hs if hs else None
    if hs:
        h_end = func_extent(hs)
        rec["host_extent"] = ("%08X" % hs, "%08X" % h_end)
        rec["host_contains_entry"] = (hs <= ei < h_end)
        rec["host_is_entry"] = (hs == ei)
        rec["host_dtor_sig"] = dtor_signature(hs, h_end)
    # entry itself: is it a scalar deleting dtor?
    rec["entry_dtor_sig"] = dtor_signature(ei, e_end_own)
    return rec


RECS = [analyze(d[0]) for d in DROWS]

out = dict(exe_sha=pe.sha, exe_sha_ok=(pe.sha == EXE_SHA_EXPECT),
           image_base="%08X" % IB, image_size=pe.image_size,
           sections=[(s["name"], "%08X" % s["va"], s["vsize"], s["rsize"]) for s in pe.secs],
           n_tables=len(TABS), n_fields=len(FIELDS), n_delta=len(DROWS),
           recs=[{k: v for k, v in r.items() if k != "win"} for r in RECS])

io.open(os.path.join(HERE, "_facts.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1, default=str))

# ---- text report
o = []
o.append("EXE sha=%s ok=%s  base=%08X size=%X  tables=%d" % (
    pe.sha, out["exe_sha_ok"], IB, pe.image_size, len(TABS)))
o.append("sections: " + " | ".join("%s va=%s vs=%X rs=%X" % t for t in out["sections"]))
for r in RECS:
    f = FIELDS and next(x for x in FIELDS if x["entry"] == r["entry"])
    o.append("")
    o.append("=" * 100)
    o.append("%s  name=%s  status=%s" % (r["entry"], COVM[r["entry"]][2],
                                         f["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"]))
    o.append("  vt=%08X slot=%d slot_val=%08X chk1=%s" % (
        r["vt"], r["slot"], r["slot_val"] or 0, r["chk"]["1_slot_holds_entry"]))
    rt = r["rtti"]
    o.append("  RTTI col=%08X sig=%s off=%s td=%08X name=%s" % (
        rt["col"], rt["sig"], rt["off"], rt["td"], rt["name"]) if rt else "  RTTI=NONE")
    o.append("  chk=%s  entry_extent=%08X..%08X (atlas sz=%s)" % (
        r["chk"], r["entry_extent_own"][0], r["entry_extent_own"][1], r["entry_sz_atlas"]))
    o.append("  site=%08X sec=%s insn=%s" % (
        r["site"], r["site_sec"], (r["site_insn"] or {}).get("text")))
    o.append("  all_stores(vt)=%s" % r["all_stores"])
    o.append("  form_actual=%s  claimed=%s" % (
        r["form_actual"], f["install_form(ctor_body|mov_abs|reg|other)"]))
    if r["form_actual"] == "mov_abs":
        o.append("    abs_target=%s sec=%s in_image=%s" % (
            r.get("abs_target"), r.get("abs_target_sec"), r.get("abs_target_in_image")))
    else:
        o.append("    base_reg=%s disp=%s stack_target=%s" % (
            r.get("base_reg"), r.get("disp"), r.get("stack_target")))
        o.append("    def=%s" % r.get("def_insn"))
        for c in r.get("def_chain") or []:
            o.append("      chain %s" % c)
    o.append("  host_atlas=%s host_own=%s claimed=%s extent=%s" % (
        r["host_atlas"], r["host_own"], r["host_claimed"], r.get("host_extent")))
    o.append("  host_is_entry=%s host_contains_entry=%s host_dtor=%s" % (
        r.get("host_is_entry"), r.get("host_contains_entry"), r.get("host_dtor_sig")))
    o.append("  entry_dtor=%s" % r.get("entry_dtor_sig"))
    o.append("  --- window ---")
    for i, t in enumerate(r["win"]):
        o.append("   %s%s" % (">>" if i == r["win_idx"] else "  ", t))

io.open(os.path.join(HERE, "_facts.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")
print("wrote _facts.json / _facts.txt  recs=%d" % len(RECS))
