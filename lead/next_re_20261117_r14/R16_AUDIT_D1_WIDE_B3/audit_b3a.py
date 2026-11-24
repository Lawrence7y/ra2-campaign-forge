#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B3 step A: INDEPENDENT re-derivation of the 18 B3 rows.

Independence contract
---------------------
* own PE32 parser (VirtualSize-aware virtual image; no pefile, no final.py)
* own RTTI resolver (COL -> TypeDescriptor -> decorated name)
* own global linear .text pass -> instruction index, call index, mov-imm index
* own function-boundary / host-identity / this-attribution logic
* does NOT import R16_D1_WIDE_B3/derive.py or verify_independent.py
* does NOT use R16_PROBE_4FINAL.final
* function_atlas.tsv used only as an EXTERNAL boundary cross-check (reported
  as host_atlas), never as the sole authority: when its range and my own
  clean-decode boundary disagree, both are recorded.

Read-only: gamemd.exe / coverage.tsv / sieve_all.tsv.
Writes only into lead/next_re_20261117_r14/R16_AUDIT_D1_WIDE_B3/.
"""
import os
import sys
import json
import re
import struct
import hashlib
import collections

sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
B3 = os.path.join(R14, "R16_D1_WIDE_B3")

EXE_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
DEL = 0x7C8B3D        # CRT operator delete used by MSVC scalar-deleting dtors


# --------------------------------------------------------------------- PE
class PE(object):
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        self.sha = hashlib.sha256(self.raw).hexdigest().upper()
        d = self.raw
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        if d[pe:pe + 4] != b"PE\0\0":
            raise SystemExit("not PE")
        nsec = struct.unpack_from("<H", d, pe + 6)[0]
        optsize = struct.unpack_from("<H", d, pe + 20)[0]
        opt = pe + 24
        if struct.unpack_from("<H", d, opt)[0] != 0x10B:
            raise SystemExit("not PE32")
        self.base = struct.unpack_from("<I", d, opt + 28)[0]
        st = opt + optsize
        self.secs = []
        for i in range(nsec):
            off = st + i * 40
            nm = d[off:off + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rsize, rptr = struct.unpack_from("<IIII", d, off + 8)
            ch = struct.unpack_from("<I", d, off + 36)[0]
            self.secs.append(dict(name=nm, va=self.base + va, vsize=vsize,
                                  rsize=rsize, rptr=rptr, ch=ch))
        end = max(s["va"] + max(s["vsize"], s["rsize"]) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        for s in self.secs:
            o = s["va"] - self.base
            n = min(s["rsize"], len(self.raw) - s["rptr"])
            if n > 0:
                self.buf[o:o + n] = self.raw[s["rptr"]:s["rptr"] + n]

    def in_image(self, va):
        return va is not None and 0 <= va - self.base < len(self.buf)

    def u8(self, va):
        o = va - self.base
        return self.buf[o] if 0 <= o < len(self.buf) else None

    def u16(self, va):
        o = va - self.base
        return struct.unpack_from("<H", self.buf, o)[0] if 0 <= o and o + 2 <= len(self.buf) else None

    def u32(self, va):
        o = va - self.base
        return struct.unpack_from("<I", self.buf, o)[0] if 0 <= o and o + 4 <= len(self.buf) else None

    def cstr(self, va, n=512):
        o = va - self.base
        if o < 0 or o >= len(self.buf):
            return None
        e = self.buf.find(b"\x00", o, min(o + n, len(self.buf)))
        return None if e < 0 else bytes(self.buf[o:e]).decode("latin-1", "replace")

    def sec_of(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                return s["name"]
        return None

    def code(self, va, n):
        o = va - self.base
        return b"" if o < 0 else bytes(self.buf[o:o + n])


pe = PE(EXE)
IB = pe.base
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

SEC = {s["name"]: s for s in pe.secs}
TEXT = SEC[".text"]
DATA = SEC[".data"]
DATA_LO = DATA["va"]
DATA_HI = DATA["va"] + max(DATA["vsize"], DATA["rsize"])

H = lambda v: "%08X" % v if v is not None else None


def norm(s):
    if s is None:
        return ""
    s = s.lower().replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\+\s*", " + ", s)
    return re.sub(r"\s+", " ", s).strip()


def rtti(vt):
    if vt is None or not pe.in_image(vt - 4):
        return None
    col = pe.u32(vt - 4)
    if not pe.in_image(col) or pe.u32(col) != 0:
        return None
    off = pe.u32(col + 4)
    td = pe.u32(col + 12)
    if not pe.in_image(td):
        return None
    nm = pe.cstr(td + 8)
    if nm is None or not nm.startswith(".?A"):
        return None
    return dict(col=col, offset=off, td=td, mangled=nm)


# --------------------------------------------------------- linear text pass
INSTR = {}
RETS = set()
CALLS = collections.defaultdict(list)      # target -> [site]
IMM_INDEX = collections.defaultdict(list)  # imm -> [dict(site,op,base,disp)]


def linear_pass():
    code = pe.code(TEXT["va"], TEXT["vsize"])
    n = 0
    for ins in md.disasm(code, TEXT["va"]):
        a = ins.address
        mn, os_ = ins.mnemonic, ins.op_str
        INSTR[a] = (ins.size, mn, os_)
        n += 1
        if mn in ("ret", "retf"):
            RETS.add(a)
        try:
            ops = ins.operands
        except Exception:
            continue
        if mn == "call" and len(ops) == 1 and ops[0].type == X.X86_OP_IMM:
            CALLS[ops[0].imm].append(a)
        if mn == "mov" and len(ops) == 2 and ops[0].type == X.X86_OP_MEM \
                and ops[1].type == X.X86_OP_IMM:
            m = ops[0].mem
            breg = ins.reg_name(m.base) if m.base else None
            ireg = ins.reg_name(m.index) if m.index else None
            IMM_INDEX[ops[1].imm].append(dict(site=a, op=os_, base=breg,
                                              index=ireg, disp=m.disp))
    return n


N_INSTR = linear_pass()
print("linear pass: %d instructions, %d rets, %d calls-targets, %d vts stored"
      % (N_INSTR, len(RETS), len(CALLS), len(IMM_INDEX)))

ATL = {}
with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2:
            try:
                ATL[int(p[0], 16)] = int(p[1])
            except ValueError:
                pass
print("atlas: %d functions" % len(ATL))
ATLAS_STARTS = sorted(ATL)
import bisect


def atlas_fn_of(va):
    """atlas function start containing va (atlas is size-based: va < a+size)."""
    i = bisect.bisect_right(ATLAS_STARTS, va)
    if i == 0:
        return None
    for j in range(i - 1, max(-1, i - 6), -1):
        a = ATLAS_STARTS[j]
        sz = ATL[a]
        if a <= va < a + sz:
            return a
    return None


# ---------------------------------------------------------- disassembly utils
def disasm_from(start, stop=None, maxn=4000):
    n = 0x200 if stop is None else max(16, stop - start + 16)
    out = []
    for ins in md.disasm(pe.code(start, n), start):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str))
        if len(out) >= maxn:
            break
        if stop is not None and ins.address >= stop:
            break
    return out


def lands_on(start, site, limit=0x1000):
    """clean (no .byte resync) linear decode from start hits site exactly."""
    if start > site or site - start > limit:
        return False
    for (a, sz, mn, os_) in disasm_from(start, site + 16):
        if a == site:
            return True
        if a > site or mn in ("ret", "retf"):
            return False
        if mn.startswith(".byte") or mn == "data":
            return False
    return False


def pad_candidates(site, back=0x600):
    out = []
    lo = max(TEXT["va"], site - back)
    for p in range(lo, site):
        if p in ATL:
            pass
        elif p > lo and pe.u8(p - 1) in (0xCC, 0x90, 0xC3):
            pass
        else:
            continue
        if lands_on(p, site):
            out.append(p)
    return out


_HOST_CACHE = {}


def host_of(site):
    """(host, method, my_own_start) — atlas authoritative when it contains site."""
    if site in _HOST_CACHE:
        return _HOST_CACHE[site]
    a = atlas_fn_of(site)
    own = pad_candidates(site)
    own_best = max(own) if own else None
    if a is not None and a < site:
        res = (a, "atlas", own_best)
    elif own_best is not None:
        res = (own_best, "pad+clean_decode", own_best)
    else:
        res = (None, "none", None)
    _HOST_CACHE[site] = res
    return res


def func_extent(start):
    """[start,end) — atlas size when available, else own decode to first ret."""
    if start is None:
        return (None, None, None, None)
    if start in ATL:
        end = start + ATL[start]
        ins = [x for x in disasm_from(start, end + 8) if x[0] < end]
        ret = None
        for (a, sz, mn, os_) in ins:
            if mn in ("ret", "retf"):
                ret = (a, os_)
        return (start, end, ret[0] if ret else None, ret[1] if ret else None)
    ins = disasm_from(start, None, 8000)
    last = start
    for (a, sz, mn, os_) in ins:
        last = a + sz
        if mn in ("ret", "retf"):
            return (start, last, a, os_)
    return (start, last, None, None)


def is_dtor_shaped_range(start, end):
    """MSVC scalar-deleting-dtor tail: test byte [esp+X],1 + call _delete + ret N"""
    if start is None:
        return dict(shaped=False)
    ins = [x for x in disasm_from(start, end + 8) if x[0] < end]
    tst = None
    dc = None
    ret = None
    for (a, sz, mn, os_) in ins:
        if mn == "test" and "byte ptr [esp" in os_ and re.search(r",\s*1$", os_):
            if tst is None:
                tst = (a, os_)
        if mn == "call" and re.search(r"\b0x%x\b" % DEL, os_):
            dc = (a, os_)
    if ins and ins[-1][2] in ("ret", "retf"):
        ret = (ins[-1][0], ins[-1][3])
    return dict(shaped=bool(tst and dc), test=tst, delcall=dc, ret=ret, n=len(ins))


def this_trace(start, site, reg):
    """nearest preceding definition of `reg` within [start, site)."""
    writes = []
    for (a, sz, mn, os_) in disasm_from(start, site + 16):
        if a >= site:
            break
        if mn in ("mov", "lea", "xor", "pop", "and", "or", "sub", "add", "inc", "dec"):
            dst = os_.split(",")[0].strip()
            if dst == reg:
                writes.append((a, mn, os_))
    if not writes:
        return dict(reg=reg, defsite=None, kind="undefined_in_host")
    a, mn, os_ = writes[-1]
    src = os_.split(",", 1)[1].strip() if "," in os_ else ""
    if mn == "mov" and src == "ecx":
        kind = "this"
    elif "[esp" in src:
        kind = "stack"
    elif mn == "xor" and src == reg:
        kind = "zeroed"
    elif src in ("eax", "ebx", "esi", "edi", "edx", "ecx"):
        kind = "reg_chain:" + src
    else:
        kind = "other"
    return dict(reg=reg, defsite=a, mnem=mn, ins=os_, kind=kind)


def install_points(vt, primary_only=True):
    """every `mov [mem], vt` store, classified."""
    out = []
    for d in IMM_INDEX.get(vt, []):
        if primary_only and d["disp"] != 0:
            continue
        out.append(d)
    out.sort(key=lambda d: d["site"])
    return out


def classify_ip(d, entry_va=None, deep=True):
    """classify one install point: abs/this/stack + host identity + dtor chain."""
    r = dict(site=d["site"], site_h=H(d["site"]), op=d["op"],
             base=d["base"], index=d["index"], disp=d["disp"])
    if d["base"] is None and d["index"] is None:
        r["target_kind"] = "abs"
        r["abs"] = d["disp"]
        r["abs_sec"] = pe.sec_of(d["disp"])
        r["abs_in_data"] = DATA_LO <= d["disp"] < DATA_HI
        r["form"] = "mov_abs" if r["abs_in_data"] else "mov_abs_out_of_data"
        host, method, own = host_of(d["site"])
        r["host"], r["host_method"], r["host_own"] = H(host), method, H(own)
        ex = func_extent(host)
        r["host_end"], r["host_atlas"] = H(ex[1]), ATL.get(host)
        r["host_prologue"] = ["%08X %s %s" % (a, mn, o)
                              for (a, sz, mn, o) in disasm_from(host, ex[1] + 8)[:8]] if host else []
        return r
    if d["base"] == "esp" or d["base"] == "ebp":
        r["target_kind"] = "stack"
        host, method, own = host_of(d["site"])
        r["host"], r["host_method"], r["host_own"] = H(host), method, H(own)
        ex = func_extent(host)
        r["host_end"], r["host_atlas"] = H(ex[1]), ATL.get(host)
        r["dtor"] = is_dtor_shaped_range(host, ex[1])
        r["form"] = "stack_temp"
        return r
    # register base
    host, method, own = host_of(d["site"])
    r["host"], r["host_method"], r["host_own"] = H(host), method, H(own)
    if host is None:
        r["target_kind"] = "reg"
        r["form"] = "other"
        return r
    ex = func_extent(host)
    r["host_end"], r["host_ret"], r["host_atlas"] = H(ex[1]), (H(ex[2]), ex[3]), ATL.get(host)
    tr = this_trace(host, d["site"], d["base"])
    r["this_trace"] = tr
    r["target_kind"] = "this" if tr["kind"] == "this" else tr["kind"]
    r["dtor_inline"] = is_dtor_shaped_range(host, ex[1])
    if deep:
        # is this host called by a scalar-deleting destructor wrapper?
        w = []
        for c in CALLS.get(host, []):
            wc, wm, _ = host_of(c)
            wex = func_extent(wc)
            sig = is_dtor_shaped_range(wc, wex[1])
            w.append(dict(call_site=H(c), call_site_va=c, wrapper=H(wc),
                          wrapper_atlas=ATL.get(wc), shaped=sig["shaped"],
                          sig_test=H(sig["test"][0]) if sig.get("test") else None,
                          sig_del=H(sig["delcall"][0]) if sig.get("delcall") else None,
                          sig_ret=sig.get("ret")))
        r["callers"] = w
        r["deleting_wrapper_of_host"] = [x for x in w if x["shaped"]]
        r["is_dtor"] = bool(r["dtor_inline"]["shaped"] or r["deleting_wrapper_of_host"])
        # ctor signals
        ins = [x for x in disasm_from(host, ex[1] + 8) if x[0] < ex[1]]
        r["host_prologue"] = ["%08X %s %s" % (a, mn, o) for (a, sz, mn, o) in ins[:10]]
        r["host_tail"] = ["%08X %s %s" % (a, mn, o) for (a, sz, mn, o) in ins[-8:]]
        r["calls_base_ctor_first"] = None
        for (a, sz, mn, os_) in ins[:6]:
            if mn == "call":
                r["calls_base_ctor_first"] = "%08X call %s" % (a, os_)
                break
        r["returns_this"] = any(mn == "mov" and re.match(r"^eax, esi$", os_) for
                                (a, sz, mn, os_) in ins)
        r["has_free_calls"] = [("%08X %s" % (a, os_)) for (a, sz, mn, os_)
                               in ins if mn == "call" and ("0x7c8b3d" in os_)]
    ok_this = (r["target_kind"] == "this") and d["disp"] == 0
    if ok_this and not r.get("is_dtor"):
        r["form"] = "ctor_body"
    elif ok_this and r.get("is_dtor"):
        r["form"] = "reg"
    elif r["target_kind"] in ("stack",):
        r["form"] = "stack_temp"
    else:
        r["form"] = "other"
    return r


# ------------------------------------------------------------------- inputs
def load_cov():
    d = open(COV, "rb").read()
    lines = d.decode("utf-8").split("\n")
    rows, order = {}, []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        p = ln.split("\t")
        if len(p) != 8:
            continue
        rows[p[0]] = p
        order.append(p[0])
    return dict(bytes=len(d), sha=hashlib.sha256(d).hexdigest().upper(),
                hdr=lines[0], rows=rows, order=order)


def load_tsv(path):
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            if line.strip():
                out.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    return hdr, out


COVD = load_cov()
print("coverage %d bytes sha=%s rows=%d" % (COVD["bytes"], COVD["sha"][:16], len(COVD["rows"])))
print("exe sha ok =", pe.sha == EXE_SHA)

SIEVE_HDR, SIEVE_ROWS = load_tsv(SIEVE)
DELTA_HDR, DELTA_ROWS = load_tsv(os.path.join(B3, "delta.tsv"))
FIELDS_HDR, FIELDS_ROWS = load_tsv(os.path.join(B3, "fields.tsv"))
SIEVE_BY = {r["entry"]: r for r in SIEVE_ROWS}
FIELDS_BY = {r["entry"]: r for r in FIELDS_ROWS}
DELTA_BY = {r["entry"]: r for r in DELTA_ROWS}


def tables_holding(entry_va, slot):
    pat = struct.pack("<I", entry_va)
    buf = bytes(pe.buf)
    out, seen = [], set()
    idx = buf.find(pat)
    while idx >= 0:
        vt = pe.base + idx - slot * 4
        if pe.in_image(vt - 4) and vt not in seen:
            r = rtti(vt)
            if r:
                out.append(dict(vt=vt, vt_h=H(vt), in_sec=pe.sec_of(vt), **r))
                seen.add(vt)
        idx = buf.find(pat, idx + 1)
    out.sort(key=lambda t: t["vt"])
    return out


# --------------------------------------------------------------- row facts
DEEP_VTS = set()      # vts whose every install point gets deep classification
ROWS = []

for d in DELTA_ROWS:
    e = d["entry"]
    ei = int(e, 16)
    fl = FIELDS_BY.get(e, {})
    sv = SIEVE_BY.get(e, {})
    vt = int(fl["vt"], 16) if fl.get("vt") else None
    slot = int(fl["slot"]) if fl.get("slot") else None
    site = int(fl["install_site"], 16) if fl.get("install_site") else None
    for x in re.findall(r"0x([0-9a-fA-F]{6,8})", fl.get("note", "")):
        pass
    rec = dict(entry=e, entry_va=ei, delta=d, fields=fl, sieve=sv,
               vt=vt, vt_h=H(vt), slot=slot, site=site, site_h=H(site))
    if vt is not None:
        rec["vt_sec"] = pe.sec_of(vt)
        rec["rtti"] = rtti(vt)
        rec["slot_val"] = pe.u32(vt + slot * 4)
        rec["chk1"] = rec["slot_val"] == ei
        rec["chk2"] = rec["rtti"] is not None and pe.u32(rec["rtti"]["col"]) == 0
        rec["chk3"] = rec["rtti"] is not None and rec["rtti"]["offset"] == 0
        rec["chk4"] = rec["rtti"] is not None and rec["rtti"]["mangled"].startswith(".?A")
        rec["tables"] = tables_holding(ei, slot)
        rec["vt_ip_all"] = install_points(vt, primary_only=False)
        rec["vt_ip_primary"] = install_points(vt, primary_only=True)
    ee = func_extent(ei)
    rec["entry_ext"] = dict(start=H(ee[0]), end=H(ee[1]), ret=H(ee[2]),
                            retop=ee[3], size=(ee[1] - ee[0]) if ee[1] else None,
                            atlas=ATL.get(ei))
    rec["entry_is_dtor"] = is_dtor_shaped_range(ei, ee[1])
    rec["chk6"] = vt is not None
    if site is not None:
        rec["chk5"] = not (ee[0] <= site < ee[1])
        ip = [x for x in rec.get("vt_ip_all", []) if x["site"] == site]
        rec["site_in_vt_index"] = bool(ip)
        d0 = ip[0] if ip else dict(site=site, op=(INSTR.get(site, (0, "?", ""))[1] + " " +
                                                 INSTR.get(site, (0, "", "?"))[2]),
                                   base=None, index=None, disp=None)
        rec["site_cls"] = classify_ip(d0, ei, deep=True)
        rec["site_bytes"] = pe.code(site, 16).hex()
    rec["cov"] = COVD["rows"].get(e)
    ROWS.append(rec)
    sc = rec.get("site_cls", {})
    print("%s vt=%s slot=%-2s site=%s form=%-11s host=%s dtor=%s" % (
        e, rec["vt_h"], slot, rec["site_h"], sc.get("form"),
        sc.get("host"), sc.get("is_dtor")))

# ------------------------------------------------- deep vts for fix auditing
FIX_VTS = {
    "005F4B10": [0x7E22A4, 0x7EF060, 0x7E3AD0],   # CLASS_FIX old(AircraftClass)/new/ObjectScope
    "00631CC0": [0x7E4D78, 0x7E4DA0],             # CLASS_FIX old(SHAPipe)/new(FilePipe)
    "0065CAC0": [0x7F0904], "0065CDD0": [0x7F0904],
    "0065CF00": [0x7F0904], "0065D0D0": [0x7F0904],
    "0065D150": [0x7E1668], "0065D190": [0x7E1668],
}
deep = {}
for k, vlist in FIX_VTS.items():
    for v in vlist:
        if v in deep:
            continue
        ips = install_points(v, primary_only=False)   # ALL stores, stack writes too
        cls = [classify_ip(x, deep=True) for x in ips[:150]]
        deep[H(v)] = dict(vt=H(v), rtti=rtti(v), n=len(ips),
                          truncated=len(ips) > 150, points=cls)
        print("deep vt %s rtti=%s install_points(all disp)=%d" % (
            H(v), (rtti(v) or {}).get("mangled"), len(ips)))

out = dict(exe=EXE, exe_sha=pe.sha, exe_sha_ok=pe.sha == EXE_SHA, n_instr=N_INSTR,
           sections=[dict(name=s["name"], va=H(s["va"]), vsize="%08X" % s["vsize"],
                          rsize="%08X" % s["rsize"],
                          end=H(s["va"] + max(s["vsize"], s["rsize"])))
                     for s in pe.secs],
           data_lo=H(DATA_LO), data_hi=H(DATA_HI),
           cov=dict(bytes=COVD["bytes"], sha=COVD["sha"], n=len(COVD["rows"])),
           rows=ROWS, deep=deep)

with open(os.path.join(HERE, "_facts.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)

# ------------------------------------------------------------ readable dump
with open(os.path.join(HERE, "_facts.txt"), "w", encoding="utf-8") as f:
    f.write("EXE %s\nsha %s ok=%s  instrs=%d\n" % (EXE, pe.sha, pe.sha == EXE_SHA, N_INSTR))
    for s in out["sections"]:
        f.write("SEC %-8s va=%s vsize=%s rsize=%s end=%s\n" %
                (s["name"], s["va"], s["vsize"], s["rsize"], s["end"]))
    f.write(".data value range %s .. %s\n\n" % (out["data_lo"], out["data_hi"]))
    for r in ROWS:
        f.write("=" * 104 + "\nENTRY %s  %s\n" % (r["entry"], r["delta"]["name"]))
        f.write(" vt=%s slot=%s slot_val=%s chk1=%s chk2=%s chk3=%s chk4=%s chk6=%s\n" % (
            r["vt_h"], r["slot"], H(r.get("slot_val")), r.get("chk1"), r.get("chk2"),
            r.get("chk3"), r.get("chk4"), r.get("chk6")))
        f.write(" rtti=%s\n" % (r.get("rtti")))
        f.write(" entry_ext=%s entry_is_dtor=%s\n" % (r["entry_ext"], r["entry_is_dtor"]))
        f.write(" chk5(site outside entry)=%s  site_in_vt_index=%s\n" % (
            r.get("chk5"), r.get("site_in_vt_index")))
        f.write(" site_bytes=%s\n" % r.get("site_bytes"))
        f.write(" SITE %s\n" % json.dumps(r.get("site_cls"), ensure_ascii=False, default=str))
        f.write(" tables holding (entry,slot): %s\n" %
                [t["vt_h"] + " " + t["mangled"] for t in r.get("tables", [])])
        f.write(" vt install points primary=%d all=%d\n" % (
            len(r.get("vt_ip_primary", [])), len(r.get("vt_ip_all", []))))
    f.write("\n\n#### DEEP VTS ####\n")
    for k, v in deep.items():
        f.write("=" * 104 + "\nVT %s rtti=%s n_points=%d\n" % (v["vt"], v["rtti"], v["n"]))
        for p in v["points"]:
            f.write("  %s %-11s host=%s dtor=%s op=%s\n" % (
                p["site_h"], p["form"], p.get("host"), p.get("is_dtor"), p["op"]))
print("wrote _facts.json / _facts.txt")
