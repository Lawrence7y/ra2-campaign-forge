# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B1 independent audit of R16_D1_WIDE_B1 (18 rows).

Read-only: gamemd.exe opened via pefile/`open('rb')`; coverage.tsv / sieve_all.tsv
read only. Writes only files inside R16_AUDIT_D1_WIDE_B1/.

Checks
  A 原文保全   : delta col4 strictly prefixed by on-disk col4; cols 1/2/3/5/6/7/8
                 byte-identical; grade unchanged; on-disk row has no ④ (=> not SKIP-ALREADY)
  B 字节事实   : u32(vt+slot*4)==entry / u32(vt-4)==COL / u32(COL+4)==offset /
                 u32(COL+12)==TD / cstr(TD+8)==mangled / install site is `mov mem,imm32`
                 with imm32==vt / containing function != entry
  C 装配方式   : mov_abs  => mem operand is absolute (no base register) + static global in .data
                 ctor_body=> mem operand is [this_reg] style and containing function is a
                             constructor/factory (independent ctor test, NOT the executor's
                             "mem operand not absolute => ctor_body" shortcut)
  D 文本一致   : every address in ④ equals the measured value; class in ④升级句 matches
                 row-name class and TD+8 decoration; D-47 disclosure present and points to
                 §12.6 (any §12.4 => FAIL)
  E 反抄袭     : 18 ④ texts pairwise distinct, also after normalising 8-hex tokens
  F 清单一致   : these 18 entries == first 18 of sieve_all.tsv rows with
                 has_ring4_on_disk==否, sorted by entry ascending
"""
import io, os, sys, re, json, bisect
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
B1 = os.path.join(R14, "R16_D1_WIDE_B1")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
IB = 0x400000
import hashlib
import pefile, capstone

# ---------------------------------------------------------------- PE image (read-only)
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
SECTIONS = [(nm, va, vs) for nm, va, vs, _rs, _d in secs]
TEXT_VA = IB + pe.sections[0].VirtualAddress
TEXT_SZ = pe.sections[0].Misc_VirtualSize

def in_section(va):
    for nm, sva, svs in SECTIONS:
        if sva <= va < sva + svs:
            return nm
    return None

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

def cstr(va, n=300):
    o = va - IB
    if o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def dis1(va, n=16):
    o = va - IB
    return list(md.disasm(bytes(buf[o:o + n]), va))

# ---------------------------------------------------------------- function starts
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

_sj = os.path.join(HERE, "starts.json")
_targets = set()
if os.path.exists(_sj):
    _targets = set(json.load(io.open(_sj, encoding="utf-8"))["targets"])
ALL_STARTS = sorted(set(atlas) | _targets)

def fn_end(start):
    """end of function: atlas size when known, else next known start."""
    if start in atlas:
        return start + atlas[start]
    i = bisect.bisect_right(ALL_STARTS, start)
    if i < len(ALL_STARTS):
        return ALL_STARTS[i]
    return TEXT_VA + TEXT_SZ

def enclosing(va):
    """Largest candidate start <= va that (a) disassembles onto va exactly with no
    ret in between and (b) is a real function start: it is in the atlas, or is a
    direct call/jmp target, or sits right after a nop/int3 padding run that is
    itself preceded by a ret (`ret; nop..; func` alignment pattern)."""
    i = bisect.bisect_right(ALL_STARTS, va) - 1
    best = None
    for j in range(i, max(-1, i - 8), -1):
        s = ALL_STARTS[j]
        ins = dis1(s, va - s + 16)
        if not ins or not any(x.address == va for x in ins):
            continue
        if any(x.mnemonic in ("ret", "retf") for x in ins if x.address < va):
            continue
        best = (s, "atlas" if s in atlas else "call-target")
        break
    # padding pattern `ret; 90/CC..; start`  (static initialisers are not in the atlas)
    for back in range(1, 0x41):
        s = va - back
        if s < TEXT_VA + 1:
            break
        p = s - 1
        npad = 0
        while p > TEXT_VA and buf[p - IB] in (0x90, 0xCC):
            npad += 1
            p -= 1
        if npad == 0:
            continue
        # byte before the padding run must terminate a function
        if buf[p - IB] not in (0xC3, 0xC2, 0xCC):
            continue
        ins = dis1(s, va - s + 16)
        if not ins or not any(x.address == va for x in ins):
            continue
        if any(x.mnemonic in ("ret", "retf") for x in ins if x.address < va):
            continue
        if best is None or s > best[0]:
            best = (s, "padding")
        break
    if best:
        return best
    return None, "none"

# vptr store map (site -> (vt, base, disp, op_str))
_sv = os.path.join(HERE, "vptr_stores.tsv")
VPTR = []
if os.path.exists(_sv):
    for i, ln in enumerate(io.open(_sv, encoding="utf-8")):
        if i == 0:
            continue
        c = ln.rstrip("\r\n").split("\t")
        VPTR.append((int(c[0], 16), int(c[1], 16), c[2], int(c[3], 16), c[5]))

def vptr_stores_in(start, stop):
    return [v for v in VPTR if start <= v[0] < stop]

# ---------------------------------------------------------------- inputs
def read_tsv(p):
    L = io.open(p, encoding="utf-8-sig").read().splitlines()
    hdr = L[0].split("\t")
    rows = []
    for n, ln in enumerate(L[1:], start=2):
        c = ln.rstrip("\r\n").split("\t")
        rows.append((n, c))
    return hdr, rows

cov_hdr, cov_rows = read_tsv(COV)
COV_BY_ENTRY = {}
COV_DUP = {}
for n, c in cov_rows:
    if not c or not c[0]:
        continue
    COV_BY_ENTRY.setdefault(c[0], (n, c))
    COV_DUP[c[0]] = COV_DUP.get(c[0], 0) + 1
COV_LINES = io.open(COV, "rb").read().split(b"\r\n") if b"\r\n" in io.open(COV, "rb").read(2000) \
    else io.open(COV, "rb").read().split(b"\n")

delta_hdr, delta_rows = read_tsv(os.path.join(B1, "delta.tsv"))
fld_hdr, fld_rows = read_tsv(os.path.join(B1, "fields.tsv"))
FLD = {}
for n, c in fld_rows:
    if c and c[0]:
        FLD[c[0]] = (n, dict(zip(fld_hdr, c)))

sieve_hdr, sieve_rows = read_tsv(SIEVE)
SIEVE_ROWS = []
for n, c in sieve_rows:
    if len(c) >= len(sieve_hdr):
        SIEVE_ROWS.append(dict(zip(sieve_hdr, c)))

# ---------------------------------------------------------------- per-row audit
RING4 = "④ 活表槽位见证"
RES = []
for n, c in delta_rows:
    entry = c[0]
    r = dict(entry=entry, delta_line=n)
    row = dict(cols=c)

    # ---------- A 原文保全
    cov = COV_BY_ENTRY.get(entry)
    if not cov:
        r["A"] = "FAIL"
        r["A_why"] = "entry not found in on-disk coverage.tsv"
        RES.append(r)
        continue
    cov_line, cc = cov
    r["cov_line"] = cov_line
    if len(cc) != 8:
        r["A"] = "FAIL"; r["A_why"] = "on-disk row has %d cols (not 8)" % len(cc); RES.append(r); continue
    a_prefix = c[3].startswith(cc[3]) and len(c[3]) > len(cc[3])
    a_tail = c[3][len(cc[3]):] if a_prefix else ""
    diff_cols = []
    for idx in (0, 1, 2, 4, 5, 6, 7):
        if c[idx] != cc[idx]:
            diff_cols.append(idx + 1)
    a_cols = not diff_cols
    a_grade = c[4] == cc[4]
    a_no_ring4_before = RING4 not in cc[3]
    r.update(a_prefix=a_prefix, a_cols_ok=a_cols, a_diff_cols=diff_cols,
             a_grade_ok=a_grade, a_pre_no_ring4=a_no_ring4_before,
             A="PASS" if (a_prefix and a_cols and a_grade and a_no_ring4_before) else "FAIL",
             A_why="" if (a_prefix and a_cols and a_grade and a_no_ring4_before) else
                   "prefix=%s cols=%s grade=%s pre_no_ring4=%s" % (a_prefix, a_cols, a_grade, a_no_ring4_before))

    # ---------- fields.tsv claims
    f = FLD.get(entry)
    if not f:
        r["B"] = r["C"] = r["D"] = "FAIL"; r["B_why"] = "no fields.tsv row"; RES.append(r); continue
    fl, fd = f
    vt = int(fd["vt"], 16); slot = int(fd["slot"]); site = int(fd["install_site"], 16)
    claim_form = fd["install_form(ctor_body|mov_abs|reg|other)"]
    claim_host = int(fd["install_host"], 16)
    r.update(vt="%08X" % vt, slot=slot, site="%08X" % site,
             claim_form=claim_form, claim_host="%08X" % claim_host)

    # ---------- B 字节事实
    slotval = u32(vt + slot * 4)
    col = u32(vt - 4)
    col_sig = u32(col) if col is not None else None
    coff = u32(col + 4) if col is not None else None
    td = u32(col + 12) if col is not None else None
    mangled = cstr(td + 8) if td else None
    ins = dis1(site, 24)
    ins0 = ins[0] if ins else None
    imm = None; mem_base = None; mem_disp = None; nops = None
    if ins0 is not None and len(ins0.operands) == 2:
        a, b = ins0.operands
        if a.type == capstone.x86.X86_OP_MEM:
            mem_base = ins0.reg_name(a.mem.base) if a.mem.base else "ABS"
            mem_disp = a.mem.disp
        if b.type == capstone.x86.X86_OP_IMM:
            imm = b.imm & 0xFFFFFFFF
    insn_txt = "%s %s" % (ins0.mnemonic, ins0.op_str) if ins0 else "?"
    host, host_src = enclosing(site)
    host_end = fn_end(host) if host else None
    b = dict(
        b1_slot=slotval == int(entry, 16),
        b2_col=(col is not None and col_sig == 0),
        b3_off=(coff == 0),
        b4_mangled=(mangled or "").startswith(".?A"),
        b5_install=(ins0 is not None and ins0.mnemonic == "mov" and mem_base is not None and imm == vt),
        b6_outside=(host is not None and host != site and not (int(entry, 16) <= site < host_end)
                    and not (host <= int(entry, 16) < host_end)),
    )
    r.update(col="%08X" % col if col is not None else None, col_sig=col_sig, coff=coff,
             td="%08X" % td if td else None, mangled=mangled, slotval="%08X" % slotval if slotval else None,
             mem_base=mem_base, mem_disp=mem_disp, imm="%08X" % imm if imm is not None else None,
             insn=insn_txt, host="%08X" % host if host else None, host_src=host_src,
             host_end="%08X" % host_end if host_end else None, **b)
    r["B"] = "PASS" if all([b["b1_slot"], b["b2_col"], b["b3_off"], b["b4_mangled"],
                            b["b5_install"], b["b6_outside"]]) else "FAIL"
    r["B_why"] = ",".join(k for k, v in b.items() if not v)

    # ---------- C 装配方式（independent）
    in_text = "body"  # placeholder
    site_target_sec = in_section(mem_disp) if mem_base == "ABS" and mem_disp else None
    # this-register of the host function
    this_reg = None
    head = dis1(host, 64) if host else []
    for x in head[:14]:
        if x.mnemonic == "mov" and len(x.operands) == 2:
            d, s2 = x.operands
            if d.type == capstone.x86.X86_OP_REG and s2.type == capstone.x86.X86_OP_REG \
               and x.reg_name(s2.reg) == "ecx":
                this_reg = x.reg_name(d.reg)
                break
    stores = vptr_stores_in(host, host_end) if host else []
    on_this = [s for s in stores if this_reg and s[2] == this_reg]
    primary_on_this = [s for s in on_this if s[3] == 0]
    site_on_this = bool(this_reg and mem_base == this_reg)
    is_ctor = (len(primary_on_this) > 0)
    # deleting-destructor signature: `test byte [esp+X], 1` + call operator delete
    # 0x7C8B3D => the function is a dtor, so a vptr store in it is NOT a ctor body
    body = dis1(host, min(host_end - host + 16, 0x800)) if host else []
    bt = ["%s %s" % (x.mnemonic, x.op_str) for x in body]
    is_deleting_dtor = any(("test byte ptr [esp" in s and ", 1" in s) for s in bt) and \
                       any("0x7c8b3d" in s for s in bt)
    r.update(this_reg=this_reg, n_vptr_host=len(stores),
             vptr_on_this=",".join("%08X" % s[0] for s in on_this) or "-",
             site_on_this=site_on_this, is_ctor=is_ctor, is_deleting_dtor=is_deleting_dtor)

    if claim_form == "mov_abs":
        c_ok = (mem_base == "ABS" and site_target_sec == ".data")
        c_why = "" if c_ok else "not an absolute static-global store (base=%s sec=%s)" % (mem_base, site_target_sec)
    elif claim_form == "ctor_body":
        # a stack-slot store can be neither the enclosing function's ctor body nor a factory
        c_ok = site_on_this and is_ctor and not is_deleting_dtor
        if not c_ok:
            parts = []
            if mem_base == "esp":
                parts.append("store target is a stack slot [esp+disp], not `this`")
            if not is_ctor:
                parts.append("containing function has no vptr install on this=%s" % this_reg)
            if is_deleting_dtor:
                parts.append("containing function carries the scalar-deleting-destructor "
                             "signature (test byte [esp+X],1 + operator delete 0x7C8B3D)")
            c_why = "; ".join(parts) or "classification unsupported"
    else:
        c_ok = True; c_why = ""
    r["C"] = "PASS" if c_ok else "FAIL"
    r["C_why"] = c_why

    # ---------- D 文本一致
    t = c[3][len(cc[3]):]            # the appended ④ text only
    r["text_len"] = len(t)
    d_issues = []
    m = re.search(r"vt=([0-9A-F]{8})", t)
    d_issues += [] if (m and int(m.group(1), 16) == vt) else ["vt"]
    m = re.search(r"槽\s*(\d+)\s*值=([0-9A-F]{8})", t)
    d_issues += [] if (m and int(m.group(1)) == slot and int(m.group(2), 16) == (slotval or 0)) else ["slot/slotval"]
    m = re.search(r"COL=([0-9A-F]{8})\s*offset=(\d+)", t)
    d_issues += [] if (m and int(m.group(1), 16) == (col or 0) and int(m.group(2)) == (coff if coff is not None else -1)) else ["COL/offset"]
    m = re.search(r"RTTI=([0-9A-F]{8})→([^；，）]+)", t)
    d_issues += [] if (m and int(m.group(1), 16) == (td or 0) and m.group(2).strip() == (mangled or "")) else ["RTTI/TD"]
    m = re.search(r"装表点\s*([0-9A-F]{8})\s*位于\s*([0-9A-F]{8})\s*体内", t)
    d_issues += [] if (m and int(m.group(1), 16) == site and int(m.group(2), 16) == (host or 0)) else ["site/host"]
    m = re.search(r"装配方式=(\w+)（([^）]*)）", t)
    if not m:
        d_issues.append("form-decl")
    else:
        if m.group(1) != claim_form:
            d_issues.append("form-name-vs-fields")
        if insn_txt not in m.group(2):
            d_issues.append("insn-text")
        if "entry 体外" not in t:
            d_issues.append("outside-entry")
    # class in ④升级句
    m = re.search(r"④升级句：(.+?)::slot(\d+)（", t)
    cls4 = m.group(1) if m else None
    cls_slot = int(m.group(2)) if m else None
    if cls_slot is not None and cls_slot != slot:
        d_issues.append("upgrade-slot")
    row_name = cc[2]
    row_cls = row_name.rsplit("::", 1)[0] if "::" in row_name else row_name
    d_issues += [] if (cls4 is not None and (cls4 == row_cls or row_name.startswith(cls4 + "::"))) else ["class-vs-rowname"]
    # TD+8 decoration => class display
    def td_class(mg):
        if not mg:
            return None
        if mg.startswith(".?AV?$DynamicVectorClass@"):
            inner = mg[len(".?AV?$DynamicVectorClass@"):].split("@")[0]
            if inner.startswith("PAV"):
                return "DynamicVectorClass<%s*>" % inner[3:]
            return "DynamicVectorClass<%s>" % inner
        if mg.startswith(".?AV") and mg.endswith("@@"):
            return mg[len(".?AV"):-2]
        return None
    tdc = td_class(mangled)
    r.update(cls4=cls4, row_cls=row_cls, td_class=tdc)
    d_nits = []
    if tdc is not None and cls4 != tdc:
        # is cls4 a documented truncation of the decorated class? (row name is
        # immutable col-3 data, e.g. `?$DynamicVectorClass::PAVWar`)
        inner = cls4.split("::")[-1] if "::" in (cls4 or "") else None
        if cls4 == row_cls and inner and mangled and inner in mangled:
            d_nits.append("class-abbrev:%s <- %s" % (cls4, mangled))
        else:
            d_issues.append("class-vs-TD(mangled=%s)" % mangled)
    # every 8-hex address in the appended ④ must be one of the measured values
    allowed = {int(entry, 16), vt, col or 0, td or 0, site, host or 0, slotval or 0}
    stray = sorted({int(x, 16) for x in re.findall(r"\b[0-9A-F]{8}\b", t)} - allowed)
    r["stray_addr"] = ",".join("%08X" % x for x in stray) or "-"
    if stray:
        d_issues.append("stray-addr(%s)" % r["stray_addr"])
    # D-47 disclosure pointer
    has_d47 = "D-47" in t
    ptr_126 = "§12.6" in t
    bad_124 = "§12.4" in t
    has_panel = "PANEL" in t
    if not has_d47: d_issues.append("no-D-47")
    if not ptr_126: d_issues.append("no-12.6")
    if bad_124: d_issues.append("WRONG-12.4")
    if not has_panel: d_issues.append("no-PANEL")
    r.update(has_d47=has_d47, ptr_126=ptr_126, bad_124=bad_124, has_panel=has_panel,
             d_issues=d_issues, d_nits=d_nits)
    r["D"] = "PASS" if not d_issues else "FAIL"
    r["D_why"] = ";".join(d_issues)

    # ---------- F membership
    RES.append(r)

# ---------- E 反抄袭
def norm(s):
    return re.sub(r"\b[0-9A-Fa-f]{8}\b", "ENTRY", s)

# compare the appended ④ text (the part the executor wrote), not the inherited prefix
TXT = {}
FULLTXT = {}
for n, c in delta_rows:
    TXT[c[0]] = c[3]
    cov = COV_BY_ENTRY.get(c[0])
    FULLTXT[c[0]] = c[3][len(cov[1][3]):] if cov and c[3].startswith(cov[1][3]) else c[3]
app = [FULLTXT[r["entry"]] for r in RES]
full = [TXT[r["entry"]] for r in RES]
nfull, nfull_d = len(set(full)), len(full)
napp, napp_d = len(set(app)), len(app)
normd = [norm(x) for x in app]
nnorm = len(set(normd))
normfull = [norm(x) for x in full]
nnormfull = len(set(normfull))
dup_pairs = []
for i in range(len(app)):
    for j in range(i + 1, len(app)):
        if normd[i] == normd[j]:
            dup_pairs.append((RES[i]["entry"], RES[j]["entry"]))
E_PASS = (nnorm == napp_d and nnormfull == nfull_d)

# ---------- F 清单一致
def is_no(v):
    return v.strip() in ("否", "no", "No", "N", "0", "False", "false")

hdr_key = [h for h in sieve_hdr if h.startswith("has_ring4_on_disk")][0]
no_rows = [s for s in SIEVE_ROWS if is_no(s[hdr_key])]
yes_rows = [s for s in SIEVE_ROWS if not is_no(s[hdr_key])]
no_sorted = sorted(no_rows, key=lambda s: int(s["entry"].strip(), 16))
expect18 = [s["entry"].strip() for s in no_sorted[:18]]
got18 = [c[0] for n, c in delta_rows]
F_missing = [e for e in expect18 if e not in got18]
F_extra = [e for e in got18 if e not in expect18]
F_order_ok = (got18 == expect18)
F_PASS = (not F_missing and not F_extra and F_order_ok)

# ---------------------------------------------------------------- output
per_row_keys = ["entry", "A", "A_why", "B", "B_why", "C", "C_why", "D", "D_why",
                "claim_form", "claim_host", "host", "host_src", "host_end", "this_reg", "is_ctor",
                "is_deleting_dtor",
                "site_on_this", "mem_base", "insn", "vt", "slot", "col", "coff", "td",
                "mangled", "cls4", "row_cls", "td_class", "site", "delta_line", "cov_line",
                "stray_addr", "d_nits"]
lines = ["\t".join(per_row_keys)]
for r in RES:
    lines.append("\t".join(str(r.get(k, "")).replace("\t", " ") for k in per_row_keys))
lines.append("")
lines.append("# E\tappended_distinct=%d/%d\tappended_norm_distinct=%d/%d\tfull_col4_distinct=%d/%d\tfull_norm_distinct=%d/%d\tdup_pairs=%s\t%s" % (
    napp, napp_d, nnorm, napp_d, nfull, nfull_d, nnormfull, nfull_d, dup_pairs or "-",
    "PASS" if E_PASS else "FAIL"))
lines.append("# F\tsieve_rows=%d\tyes=%d\tno=%d\texpect18=%s" % (
    len(SIEVE_ROWS), len(yes_rows), len(no_rows), ",".join(expect18)))
lines.append("# F\tgot18=%s" % ",".join(got18))
lines.append("# F\tmissing=%s\textra=%s\torder_ok=%s\t%s" % (
    F_missing or "-", F_extra or "-", F_order_ok, "PASS" if F_PASS else "FAIL"))
io.open(os.path.join(HERE, "check.tsv"), "w", encoding="utf-8").write("\n".join(lines))

summary = dict(
    n_rows=len(RES),
    A_fail=[r["entry"] for r in RES if r["A"] != "PASS"],
    B_fail=[r["entry"] for r in RES if r["B"] != "PASS"],
    C_fail=[r["entry"] for r in RES if r["C"] != "PASS"],
    D_fail=[r["entry"] for r in RES if r["D"] != "PASS"],
    E=dict(norm_distinct=nnorm, n=napp_d, appended_distinct=napp,
           full_distinct=nfull, full_norm_distinct=nnormfull, pass_=E_PASS, dup=dup_pairs),
    F=dict(pass_=F_PASS, missing=F_missing, extra=F_extra, order_ok=F_order_ok,
           n_yes=len(yes_rows), n_no=len(no_rows), n_sieve=len(SIEVE_ROWS), expect18=expect18),
    forms={},
    hashes=dict(cov=sha256(COV), exe=sha256(EXE), cov_bytes=os.path.getsize(COV)),
    host_src={r["entry"]: r.get("host_src") for r in RES},
    text_len={r["entry"]: r.get("text_len") for r in RES},
    d_nits={r["entry"]: r.get("d_nits") for r in RES if r.get("d_nits")},
    # for a vtable whose chosen site is a stack temporary, are there install sites
    # that really write `this` (i.e. canonical constructor bodies)?
    canonical_sites_on_this={},
)
for vt in sorted({r["vt"] for r in RES}):
    v = int(vt, 16)
    on_this = [s[0] for s in VPTR if s[1] == v and s[2] != "ABS" and s[2] != "esp" and s[3] == 0]
    summary["canonical_sites_on_this"][vt] = dict(n=len(on_this),
                                                  examples=["%08X" % x for x in sorted(on_this)[:8]])
for r in RES:
    summary["forms"].setdefault(r["claim_form"], []).append(r["entry"])
io.open(os.path.join(HERE, "verify_summary.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=1))

print("rows:", len(RES))
for k in ("A", "B", "C", "D"):
    bad = [r["entry"] for r in RES if r[k] != "PASS"]
    print("  %s: PASS %d/%d   FAIL: %s" % (k, len(RES) - len(bad), len(RES), bad or "-"))
    for r in RES:
        if r[k] != "PASS":
            print("      %s  %s" % (r["entry"], r.get(k + "_why")))
print("  E: appended_distinct=%d/%d norm=%d/%d | full=%d/%d norm=%d/%d -> %s" % (
    napp, napp_d, nnorm, napp_d, nfull, nfull_d, nnormfull, nfull_d,
    "PASS" if E_PASS else "FAIL"))
print("  F: sieve=%d yes=%d no=%d  order_ok=%s missing=%s extra=%s -> %s" % (
    len(SIEVE_ROWS), len(yes_rows), len(no_rows), F_order_ok, F_missing or "-", F_extra or "-",
    "PASS" if F_PASS else "FAIL"))
print("  forms:", {k: len(v) for k, v in summary["forms"].items()})
print("  cov sha:", summary["hashes"]["cov"][:8], " exe sha:", summary["hashes"]["exe"][:8])
