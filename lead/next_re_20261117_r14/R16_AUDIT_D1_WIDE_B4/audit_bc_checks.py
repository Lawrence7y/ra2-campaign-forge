#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B4 / 项 B + C（含三处加严）独立复算。

自写：PE/RTTI/指令索引（由 audit_a_facts.py 建好的 _index.pkl，仍为本审计自建产物）+
结构化「真构造器 vs 析构器」判别 + 全 vt 装表点枚举 + 表多重性枚举。
不使用执行器 fields.tsv 的 install_host 作为输入。
"""
import os, sys, io, re, json, struct, hashlib, bisect, collections, pickle
sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")
B4 = os.path.join(R14, "R16_D1_WIDE_B4")
DEL = 0x7C8B3D
H = lambda v: ("%08X" % (v & 0xFFFFFFFF)) if v is not None else None

# ------------------------------------------------------------------ PE 基底
raw = open(EXE, "rb").read()
po = struct.unpack_from("<I", raw, 0x3C)[0]
ns = struct.unpack_from("<H", raw, po + 6)[0]
osz = struct.unpack_from("<H", raw, po + 20)[0]
opt = po + 24
BASE = struct.unpack_from("<I", raw, opt + 28)[0]
secs = []
for i in range(ns):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b"\0").decode("latin-1")
    vs, va, rs, rp = struct.unpack_from("<IIII", raw, o + 8)
    secs.append(dict(name=nm, va=BASE + va, vsize=vs, rsize=rs, rptr=rp))
BUF = bytearray(max(s["va"] + max(s["vsize"], s["rsize"]) for s in secs) - BASE + 16)
for s in secs:
    o = s["va"] - BASE
    n = min(s["rsize"], len(raw) - s["rptr"])
    BUF[o:o + n] = raw[s["rptr"]:s["rptr"] + n]
SEC = {s["name"]: s for s in secs}
TEXT = SEC[".text"]; DATA = SEC[".data"]
DATA_LO, DATA_HI = DATA["va"], DATA["va"] + DATA["vsize"]
DATA_HI_R = DATA["va"] + DATA["rsize"]

def code(va, n):
    o = va - BASE
    return bytes(BUF[o:o + n]) if o >= 0 else b""

def u8(va):
    o = va - BASE
    return BUF[o] if 0 <= o < len(BUF) else None

def u32(va):
    o = va - BASE
    return struct.unpack_from("<I", BUF, o)[0] if 0 <= o and o + 4 <= len(BUF) else None

def cstr(va, n=400):
    o = va - BASE
    if o < 0 or o >= len(BUF): return None
    e = BUF.find(b"\0", o, min(o + n, len(BUF)))
    return None if e < 0 else bytes(BUF[o:e]).decode("latin-1", "replace")

def sec_of(va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]): return s["name"]
    return None

def sec_of_vsize(va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["vsize"]: return s["name"]
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True; md.skipdata = True
mdc = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); mdc.detail = True

IDX = pickle.load(open(os.path.join(HERE, "_index.pkl"), "rb"))
STORES = IDX["stores"]; CALLS = IDX["calls"]; ATL = IDX["atlas"]
AS = sorted(ATL)

def fn_of(va):
    i = bisect.bisect_right(AS, va)
    for j in range(i - 1, max(-1, i - 4), -1):
        a = AS[j]
        if a <= va < a + ATL[a]: return a
    return None

def clean_lands_on(start, site, limit=0x2000):
    if start > site or site - start > limit: return False
    for ins in mdc.disasm(code(start, min(site - start + 16, limit + 16)), start):
        if ins.address == site: return True
        if ins.address > site or ins.size == 0: return False
    return False

def own_start(site, back=0x800):
    lo = max(TEXT["va"] + 1, site - back)
    return [p for p in range(lo, site) if u8(p - 1) in (0xCC, 0x90, 0xC3) and clean_lands_on(p, site)]

def dis(start, stop=None, maxn=8000):
    n = 0x300 if stop is None else max(16, stop - start + 32)
    out = []
    for ins in md.disasm(code(start, n), start):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str))
        if len(out) >= maxn: break
        if stop is not None and ins.address >= stop: break
    return out

def extent(start):
    if start is None: return dict(start=None, end=None, ret=None, retop=None, method=None, atlas=None, n=0)
    if start in ATL:
        end = start + ATL[start]
        ins = [x for x in dis(start, end + 8) if x[0] < end]
        rr = [x for x in ins if x[2] in ("ret", "retf")]
        return dict(start=start, end=end, ret=rr[-1][0] if rr else None,
                    retop=rr[-1][3] if rr else None, method="atlas", atlas=ATL[start], n=len(ins))
    ins = dis(start, None)
    last = start
    for (a, sz, mn, os_) in ins:
        last = a + sz
        if mn in ("ret", "retf"):
            return dict(start=start, end=last, ret=a, retop=os_, method="own-decode", atlas=None, n=len(ins))
    return dict(start=start, end=last, ret=None, retop=None, method="own-decode", atlas=None, n=len(ins))

def dtor_sig(start, end):
    if start is None or end is None: return dict(shaped=False)
    ins = [x for x in dis(start, end + 8) if x[0] < end]
    ti = None
    for i, (a, sz, mn, os_) in enumerate(ins):
        if mn == "test" and re.search(r"byte ptr \[esp\s*\+\s*(0x[0-9a-f]+|\d+)\]", os_) \
                and re.search(r",\s*1$", os_.strip()):
            ti = (i, a, os_); break
    di = None
    if ti:
        for i in range(ti[0], min(len(ins), ti[0] + 8)):
            a, sz, mn, os_ = ins[i]
            if mn == "call" and os_.strip().lower() in ("0x%x" % DEL, "0x7c8b3d"):
                di = (i, a, os_); break
    ri = None
    if ins and ins[-1][2] in ("ret", "retf"):
        ri = (len(ins) - 1, ins[-1][0], ins[-1][3])
    shaped = bool(ti and di and ri and ri[0] > di[0] and ri[0] - di[0] <= 10
                  and re.match(r"^(0x[0-9a-f]+|\d+)$", (ri[2] or "").strip()))
    return dict(shaped=shaped,
                test="%s %s @%s" % ("test", ti[2], H(ti[1])) if ti else None,
                delcall="call @%s" % H(di[1]) if di else None,
                ret="%s @%s" % (ri[2], H(ri[1])) if ri else None, n=len(ins))

def wrappers_of(host):
    out = []
    for c in CALLS.get(host, []):
        w = fn_of(c)
        if w is None:
            own = own_start(c); w = max(own) if own else None
        if w is None:
            out.append(dict(call_site=H(c), wrapper=None, shaped=None)); continue
        we = extent(w); sg = dtor_sig(w, we["end"])
        out.append(dict(call_site=H(c), wrapper=H(w), wrapper_atlas=H(ATL.get(w)),
                        wrapper_retop=we["retop"], shaped=bool(sg["shaped"]), sig=sg))
    return out

_W = ("mov", "lea", "xor", "pop", "and", "or", "sub", "add", "inc", "dec")

def this_trace(host, site, reg):
    body = [x for x in dis(host, site + 16) if x[0] < site]
    defs = collections.defaultdict(list)
    for (a, sz, mn, os_) in body:
        head = os_.split(",")[0].strip()
        if not re.match(r"^[a-z]{2,4}$", head): continue
        src = os_.split(",", 1)[1].strip() if "," in os_ else ""
        defs[head].append((a, mn, os_, src))
    seen = set()
    def res(r, depth=0):
        if depth > 4 or r in seen or r not in defs:
            return dict(kind="undefined" if r not in defs else "loop")
        seen.add(r)
        a, mn, os_, src = defs[r][-1]
        if mn == "lea":
            m = re.match(r"^\[?\s*([a-z]{2,4})(\s*\+\s*(?:0x[0-9a-f]+|\d+))?\s*\]?$", src)
            if m:
                sub = res(m.group(1), depth + 1)
                if sub["kind"] == "this":
                    return dict(kind="this", defsite=H(a), ins=os_,
                                offset=sub.get("offset", 0) + int(m.group(2).split("+")[-1].strip(), 0) if m.group(2) else sub.get("offset", 0))
                return dict(kind=sub["kind"], defsite=H(a), ins=os_, via=m.group(1))
            return dict(kind="other", defsite=H(a), ins=os_)
        if src == "ecx":
            return dict(kind="this", defsite=H(a), ins=os_, offset=0)
        if "[esp" in src or "[ebp" in src:
            return dict(kind="stack", defsite=H(a), ins=os_)
        if re.match(r"^[a-z]{2,4}$", src):
            sub = res(src, depth + 1)
            return dict(kind=sub["kind"], defsite=H(a), ins=os_, via=src, chain=sub)
        if mn == "xor" and src == r:
            return dict(kind="zeroed", defsite=H(a), ins=os_)
        return dict(kind="other", defsite=H(a), ins=os_)
    return res(reg)

def host_kind(host, end, site):
    """结构化判别：真构造器 / 析构器 / 其它。"""
    ins = [x for x in dis(host, end + 8) if x[0] < end]
    sg = dtor_sig(host, end)
    wr = wrappers_of(host)
    shaped_wr = [w for w in wr if w.get("shaped")]
    returns_this = None
    for (a, sz, mn, os_) in ins[-10:]:
        if mn == "mov" and re.match(r"^eax,\s*(esi|edi|ebx|ecx)$", os_):
            returns_this = "%08X mov %s" % (a, os_)
    calls = [("%08X call %s" % (a, o)) for (a, sz, mn, o) in ins if mn == "call"]
    first_call = calls[0] if calls else None
    last_call = calls[-1] if calls else None
    vptr_sites = [("%08X %s %s" % (a, mn, o)) for (a, sz, mn, o) in ins
                  if mn == "mov" and re.match(r"^dword ptr \[(esi|edi|ecx|eax|ebx)\], 0x7[0-9a-f]{6}$", o)]
    # 结构判据
    kind = "other"
    if sg["shaped"] or shaped_wr:
        kind = "scalar_deleting_dtor" if sg["shaped"] else "base_dtor(wrapper_called)"
    elif returns_this:
        # 构造器：返回 this，且首个 call 早于 vptr 写（基类构造器先于装表）
        pos_v = None
        for (a, sz, mn, o) in ins:
            if mn == "mov" and re.match(r"^dword ptr \[(esi|edi|ecx|eax|ebx)\], 0x7[0-9a-f]{6}$", o) and a == site:
                pos_v = a
        first_call_a = int(first_call.split()[0], 16) if first_call else None
        kind = "ctor" if (pos_v is None or first_call_a is None or first_call_a < pos_v) else "returns_this_late_vptr"
        if first_call is None:
            kind += "+no_call"
    elif not returns_this and last_call:
        kind = "dtor_like(no_returns_this)"
    return dict(kind=kind, dtor_sig=sg, shaped_wrappers=shaped_wr,
                all_callers=[dict(call_site=w["call_site"], wrapper=w["wrapper"], shaped=w["shaped"]) for w in wr],
                returns_this=returns_this, first_call=first_call, last_call=last_call,
                n_ins=len(ins), vptr_stores=vptr_sites[:12])

def tables_holding(entry, slot):
    pat = struct.pack("<I", entry); b = bytes(BUF)
    out, seen = [], set()
    i = b.find(pat)
    while i >= 0:
        vt = BASE + i - slot * 4
        if vt not in seen and 0 <= vt - BASE < len(BUF):
            col = u32(vt - 4)
            if col is not None and 0 <= col - BASE < len(BUF) and u32(col) == 0:
                td = u32(col + 12)
                mg = cstr(td + 8) if td is not None and 0 <= td - BASE < len(BUF) else None
                if mg and mg.startswith(".?A"):
                    out.append(dict(vt=H(vt), sec=sec_of(vt), col=H(col), offset=u32(col + 4),
                                    td=H(td), mangled=mg)); seen.add(vt)
        i = b.find(pat, i + 1)
    return sorted(out, key=lambda t: int(t["vt"], 16))

def stores_of_vt(vt):
    return [s for s in STORES if s["imm"] == vt]

def classify_store(st):
    r = dict(site=H(st["site"]), ins=st["text"], base=st["base"], disp=st["disp"],
             target=None, host=None, this=None, host_kind=None)
    if st["base"] is None and st["index"] is None:
        r["target"] = "abs"; r["abs_sec"] = sec_of_vsize(st["disp"])
        r["abs_in_data"] = DATA_LO <= st["disp"] < DATA_HI
        r["abs_in_data_rsize"] = DATA_LO <= st["disp"] < DATA_HI_R
    elif st["base"] in ("esp", "ebp"):
        r["target"] = "stack"
    else:
        r["target"] = "reg"
    h = fn_of(st["site"])
    if h is None:
        own = own_start(st["site"])
        h = max(own) if own else None
        r["host_method"] = "own:pad+clean"
    else:
        r["host_method"] = "atlas"
    r["host"] = H(h)
    ex = extent(h)
    r["host_extent"] = dict(start=H(ex["start"]), end=H(ex["end"]), ret=H(ex["ret"]), method=ex["method"])
    r["site_inside"] = bool(h is not None and ex["end"] and h <= st["site"] < ex["end"])
    r["host_is_fn_start"] = bool(h is not None and (h in ATL or u8(h - 1) in (0xCC, 0x90, 0xC3)))
    if st["base"] not in (None, "esp", "ebp") and h is not None:
        r["this"] = this_trace(h, st["site"], st["base"])
    if h is not None:
        r["host_kind"] = host_kind(h, ex["end"], st["site"])
    return r

FACTS = json.load(io.open(os.path.join(HERE, "_facts.json"), encoding="utf-8"))
FH = ["entry","subsystem","name","sieve_audit_file","sieve_audit_line","vt","slot","install_site",
      "install_form(ctor_body|mov_abs|reg|other)","install_host","pre_has_ring4(是/否)",
      "status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)","note"]
lines = io.open(os.path.join(B4, "fields.tsv"), encoding="utf-8-sig").read().split("\n")
if lines and lines[-1] == "": lines = lines[:-1]
FROWS = [dict(zip(FH, l.split("\t"))) for l in lines[1:] if l.strip()]

OUT = []
print("data .data range (VirtualSize) %s..%s   (rsize end %s)" % (H(DATA_LO), H(DATA_HI), H(DATA_HI_R)))
for fr, fx in zip(FROWS, FACTS["rows"]):
    e = fr["entry"]; ei = int(e, 16); vt = int(fr["vt"], 16); slot = int(fr["slot"]); site = int(fr["install_site"], 16)
    rec = dict(entry=e, name=fr["name"], claim_form=fr["install_form(ctor_body|mov_abs|reg|other)"],
               claim_host=fr["install_host"], status=fr["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"],
               vt=H(vt), slot=slot, site=H(site))
    # ---- B 六项
    col = u32(vt - 4); off = u32(col + 4) if col is not None else None
    td = u32(col + 12) if col is not None else None
    mg = cstr(td + 8) if td is not None else None
    ee = extent(ei)
    rec["b"] = dict(
        slot_val=H(u32(vt + slot * 4)), b1=u32(vt + slot * 4) == ei,
        col=H(col), b2=(col is not None and u32(col) == 0),
        offset=off, b3=(off == 0),
        td=H(td), mangled=mg, b4=bool(mg and mg.startswith(".?A")),
        entry_extent=dict(start=H(ee["start"]), end=H(ee["end"]), ret=H(ee["ret"]),
                          retop=ee["retop"], method=ee["method"], atlas=H(ee["atlas"])),
        b5=not (ee["start"] <= site < ee["end"]),
        b6=bool(vt and 0 <= vt - BASE < len(BUF)),
        entry_is_dtor=dtor_sig(ei, ee["end"]),
        site_minus_entry=site - ei)
    # ---- 装表点本身
    st = [s for s in STORES if s["site"] == site]
    cls = classify_store(st[0]) if st else None
    rec["site_cls"] = cls
    rec["b"]["store_imm_eq_vt"] = bool(st and st[0]["imm"] == vt)
    rec["b"]["host_ne_entry"] = bool(cls and cls["host"] and int(cls["host"], 16) != ei)
    rec["b"]["site_inside_host"] = bool(cls and cls["site_inside"])
    rec["b"]["host_is_fn_start"] = bool(cls and cls["host_is_fn_start"])
    rec["b"]["host_claim_match"] = bool(cls and cls["host"] == fr["install_host"].upper())
    # ---- C 形态复判
    hk = cls["host_kind"] if cls else None
    f = None
    if cls:
        if cls["target"] == "abs":
            f = "mov_abs" if cls["abs_in_data"] else "mov_abs_out_of_data"
        elif cls["target"] == "stack":
            f = "stack_temp"
        elif cls["target"] == "reg":
            this_ok = bool(cls["this"] and cls["this"]["kind"] == "this" and (cls["this"].get("offset") or 0) == 0)
            is_dtor = bool(hk and hk["kind"].startswith(("scalar_deleting_dtor", "base_dtor", "dtor_like")))
            if this_ok:
                f = "reg" if is_dtor else "ctor_body"
            else:
                f = "other:" + (cls["this"]["kind"] if cls["this"] else "no_trace")
    rec["form_audit"] = f
    rec["form_ok"] = (f == rec["claim_form"])
    # ---- 该 vt 全部装表点
    allst = stores_of_vt(vt)
    cls_all = [classify_store(s) for s in allst]
    rec["vt_stores"] = [dict(site=c["site"], ins=c["ins"], target=c["target"],
                             this_kind=(c["this"]["kind"] if c["this"] else None),
                             host=c["host"], host_kind=(c["host_kind"]["kind"] if c["host_kind"] else None))
                        for c in cls_all]
    rec["vt_n_stores"] = len(cls_all)
    rec["vt_this_writers"] = [c["site"] for c in cls_all
                              if c["target"] == "reg" and c["this"] and c["this"]["kind"] == "this"
                              and (c["this"].get("offset") or 0) == 0]
    rec["vt_lowest_site"] = min((int(c["site"], 16) for c in cls_all), default=None)
    rec["vt_lowest_site_h"] = H(rec["vt_lowest_site"]) if rec["vt_lowest_site"] else None
    # ---- 表归属
    tabs = tables_holding(ei, slot)
    rec["tables"] = tabs
    rec["n_tables"] = len(tabs)
    rowcls = fr["name"].split("::")[0]
    rec["row_class"] = rowcls
    rec["tables_of_rowclass"] = [t for t in tabs if t["mangled"] == ".?AV%s@@" % rowcls]
    rec["n_tables_of_rowclass"] = len(rec["tables_of_rowclass"])
    rec["rowclass_strict_eq"] = bool(mg == ".?AV%s@@" % rowcls)
    OUT.append(rec)
    print("\n%s %s  vt=%s slot=%d site=%s" % (e, fr["name"], H(vt), slot, H(site)))
    print("  B: " + " ".join("%s=%s" % (k, rec["b"][k]) for k in
          ("b1", "b2", "b3", "b4", "b5", "b6", "store_imm_eq_vt", "host_ne_entry", "site_inside_host", "host_is_fn_start")))
    print("  C: claim=%-10s audit=%-10s ok=%s  target=%s this=%s" % (
        rec["claim_form"], f, rec["form_ok"], cls["target"] if cls else None,
        (cls["this"] or {}).get("kind") if cls else None))
    print("     host=%s kind=%s claim_host=%s match=%s" % (
        cls["host"] if cls else None, hk["kind"] if hk else None, fr["install_host"], rec["b"]["host_claim_match"]))
    print("     vt stores=%d this-writers=%s lowest=%s" % (len(cls_all), rec["vt_this_writers"], rec["vt_lowest_site_h"]))
    print("     tables holding = %d ; of rowclass=%d %s" % (
        len(tabs), rec["n_tables_of_rowclass"], [t["mangled"] for t in tabs]))

json.dump(dict(data=dict(lo=H(DATA_LO), hi=H(DATA_HI), hi_rsize=H(DATA_HI_R)),
               sections=[dict(name=s["name"], va=H(s["va"]), vsize=H(s["vsize"]), rsize=H(s["rsize"])) for s in secs],
               rows=OUT), io.open(os.path.join(HERE, "_bc.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print("\nwrote _bc.json")
