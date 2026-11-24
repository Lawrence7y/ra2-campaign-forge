#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B4 / 项 B+C 独立复算。

独立性声明
----------
* 自写 PE32 解析（按 VirtualSize 铺满虚拟镜像），不 import pefile
* 自写 RTTI 解析（COL -> TD -> 装饰名）
* 自写 .text 单遍线性反汇编，自建 `mov [mem], imm32` 索引（含栈写/寄存器写/绝对写）
* 自写函数边界：atlas 尺寸优先；非 atlas 用「前邻填充 + 禁 skipdata 的 clean 解码恰好落在点位」
* 自写宿主身份判定：析构签名要求 `test byte [esp+X],1` -> `call 0x7C8B3D` -> `ret N` 同函数尾段同构，
  另加「被该形态包装器调用」检验；不用执行器 derive.py / raw_dump.json / verify_tricky.py 的任何结论
* 不采用执行器 fields.tsv 给出的 install_host 作为输入 —— 宿主由本脚本独立求，再与执行器对比

只读：gamemd.exe / coverage.tsv / sieve_all.tsv / final.tsv。
只写：lead/next_re_20261117_r14/R16_AUDIT_D1_WIDE_B4/。
"""
import os, sys, io, re, json, struct, hashlib, bisect, collections

sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
B4 = os.path.join(R14, "R16_D1_WIDE_B4")
DEL = 0x7C8B3D
EXE_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
H = lambda v: ("%08X" % (v & 0xFFFFFFFF)) if v is not None else None


class PE(object):
    def __init__(self, path):
        self.raw = open(path, "rb").read()
        self.sha = hashlib.sha256(self.raw).hexdigest().upper()
        d = self.raw
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[pe:pe + 4] == b"PE\0\0"
        nsec = struct.unpack_from("<H", d, pe + 6)[0]
        optsize = struct.unpack_from("<H", d, pe + 20)[0]
        opt = pe + 24
        assert struct.unpack_from("<H", d, opt)[0] == 0x10B, "not PE32"
        self.base = struct.unpack_from("<I", d, opt + 28)[0]
        st = opt + optsize
        self.secs = []
        for i in range(nsec):
            o = st + i * 40
            nm = d[o:o + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
            self.secs.append(dict(name=nm, va=self.base + va, vsize=vsize,
                                  rsize=rsize, rptr=rptr))
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

    def u32(self, va):
        o = va - self.base
        return struct.unpack_from("<I", self.buf, o)[0] if 0 <= o and o + 4 <= len(self.buf) else None

    def cstr(self, va, n=400):
        o = va - self.base
        if o < 0 or o >= len(self.buf):
            return None
        e = self.buf.find(b"\0", o, min(o + n, len(self.buf)))
        return None if e < 0 else bytes(self.buf[o:e]).decode("latin-1", "replace")

    def code(self, va, n):
        o = va - self.base
        return b"" if o < 0 else bytes(self.buf[o:o + n])

    def sec_of(self, va):
        if va is None:
            return None
        for s in self.secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                return s["name"]
        return None

    def sec_vsize_of(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + s["vsize"]:
                return s["name"]
        return None


pe = PE(EXE)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
# clean 解码器：禁 skipdata，遇不可解即停（用于函数边界判定）
mdc = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdc.detail = True
mdc.skipdata = False

SEC = {s["name"]: s for s in pe.secs}
TEXT = SEC[".text"]
DATA = SEC[".data"]
DATA_LO = DATA["va"]
DATA_HI = DATA["va"] + DATA["vsize"]            # 按 VirtualSize
DATA_HI_RSIZE = DATA["va"] + DATA["rsize"]


# ------------------------------------------------------------------ 基座索引
INSTR = {}                                   # addr -> (size, mnem, op_str, text)
IMM_ANY = collections.defaultdict(list)      # imm -> [(addr, text)]
STORE_IMM = []                               # mov [mem], imm
CALLS = collections.defaultdict(list)
RETS = []


def linear_pass():
    code = pe.code(TEXT["va"], TEXT["vsize"])
    n = 0
    for ins in md.disasm(code, TEXT["va"]):
        a = ins.address
        txt = "%s %s" % (ins.mnemonic, ins.op_str)
        INSTR[a] = (ins.size, ins.mnemonic, ins.op_str, txt)
        n += 1
        if ins.mnemonic in ("ret", "retf"):
            RETS.append((a, ins.op_str))
        if ins.mnemonic.startswith(".") or ins.id == 0:
            continue
        try:
            ops = ins.operands
        except Exception:
            continue
        for op in ops:
            if op.type == X.X86_OP_IMM:
                IMM_ANY[op.imm & 0xFFFFFFFF].append((a, txt, ins.mnemonic))
        if ins.mnemonic == "call" and len(ops) == 1 and ops[0].type == X.X86_OP_IMM:
            CALLS[ops[0].imm & 0xFFFFFFFF].append(a)
        if ins.mnemonic == "mov" and len(ops) == 2 and ops[0].type == X.X86_OP_MEM \
                and ops[1].type == X.X86_OP_IMM:
            m = ops[0].mem
            STORE_IMM.append(dict(site=a,
                                  base=ins.reg_name(m.base) if m.base else None,
                                  index=ins.reg_name(m.index) if m.index else None,
                                  disp=m.disp & 0xFFFFFFFF,
                                  imm=ops[1].imm & 0xFFFFFFFF,
                                  scale=m.scale, text=txt))
    return n


N_INSTR = linear_pass()
print("linear pass: %d instrs, %d stores, %d call-targets" % (N_INSTR, len(STORE_IMM), len(CALLS)))

# --------------------------------------------------------------------- atlas
ATL = {}
with io.open(ATLAS, "r", encoding="utf-8-sig") as f:
    f.readline()
    for ln in f:
        p = ln.rstrip("\r\n").split("\t")
        if len(p) >= 2:
            try:
                ATL[int(p[0].strip(), 16)] = int(p[1])
            except ValueError:
                pass
ATL_STARTS = sorted(ATL)
STARTS_ALL = sorted(set(ATL_STARTS))
print("atlas: %d funcs" % len(ATL))


def atlas_fn_of(va):
    i = bisect.bisect_right(ATL_STARTS, va)
    for j in range(i - 1, max(-1, i - 4), -1):
        a = ATL_STARTS[j]
        if a <= va < a + ATL[a]:
            return a
    return None


def clean_lands_on(start, site, limit=0x2000):
    """禁 skipdata 的 clean 解码从 start 出发恰好落在 site（不跨重同步）"""
    if start > site or site - start > limit:
        return False
    for ins in mdc.disasm(pe.code(start, min(site - start + 16, limit + 16)), start):
        if ins.address == site:
            return True
        if ins.address > site:
            return False
        if ins.size == 0:
            return False
    return False


def own_start_of(site, back=0x800):
    """装表点所属函数的自求起点：前邻为填充/ret 且 clean 解码恰好落在 site。"""
    lo = max(TEXT["va"] + 1, site - back)
    cands = []
    for p in range(lo, site):
        if pe.u8(p - 1) in (0xCC, 0x90, 0xC3):
            if clean_lands_on(p, site):
                cands.append(p)
    return cands


def dis(start, stop=None, maxn=6000, clean=False):
    n = 0x300 if stop is None else max(16, stop - start + 32)
    eng = mdc if clean else md
    out = []
    for ins in eng.disasm(pe.code(start, n), start):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str))
        if len(out) >= maxn:
            break
        if stop is not None and ins.address >= stop:
            break
    return out


def extent(start):
    """[start, end) + 末 ret。atlas 优先，否则解码到首个 ret。"""
    if start is None:
        return dict(start=None, end=None, ret=None, retop=None, method=None, atlas=None)
    if start in ATL:
        end = start + ATL[start]
        ins = [x for x in dis(start, end + 8) if x[0] < end]
        ret = None
        for (a, sz, mn, os_) in ins:
            if mn in ("ret", "retf"):
                ret = (a, os_)
        return dict(start=start, end=end, ret=ret[0] if ret else None,
                    retop=ret[1] if ret else None, method="atlas", atlas=ATL[start],
                    n=len(ins))
    ins = dis(start, None, 8000)
    last = start
    for (a, sz, mn, os_) in ins:
        last = a + sz
        if mn in ("ret", "retf"):
            return dict(start=start, end=last, ret=a, retop=os_, method="own-decode",
                        atlas=None, n=len(ins))
    return dict(start=start, end=last, ret=None, retop=None, method="own-decode",
                atlas=None, n=len(ins))


def dtor_signature(start, end):
    """MSVC scalar deleting destructor: test byte [esp+X],1 -> call 0x7C8B3D -> ret N（同函数内、ret 在尾）"""
    if start is None or end is None:
        return dict(shaped=False)
    ins = [x for x in dis(start, end + 8) if x[0] < end]
    tst = None
    for i, (a, sz, mn, os_) in enumerate(ins):
        if mn == "test" and re.search(r"byte ptr \[esp\s*\+\s*(0x[0-9a-f]+|\d+)\]", os_) \
                and re.search(r",\s*1$", os_.strip()):
            tst = (i, a, os_)
            break
    dc = None
    if tst is not None:
        for i in range(tst[0], min(len(ins), tst[0] + 8)):
            a, sz, mn, os_ = ins[i]
            if mn == "call" and os_.strip().lower() in ("0x%x" % DEL, "0x7c8b3d"):
                dc = (i, a, os_)
                break
    ret = None
    if ins and ins[-1][2] in ("ret", "retf"):
        ret = (len(ins) - 1, ins[-1][0], ins[-1][3])
    shaped = bool(tst and dc and ret and ret[0] > dc[0] and ret[0] - dc[0] <= 6
                  and re.match(r"^0x[0-9a-f]+$", (ret[2] or "").strip()))
    return dict(shaped=shaped,
                test=dict(at=H(tst[1]), ins=tst[2]) if tst else None,
                delcall=dict(at=H(dc[1]), ins=dc[2]) if dc else None,
                ret=dict(at=H(ret[1]), ins=ret[2]) if ret else None,
                n=len(ins))


# ---------------------------------------------------------------- this 归属
_WRITE_MN = ("mov", "lea", "xor", "pop", "and", "or", "sub", "add", "inc", "dec",
             "imul", "shl", "shr")


def reg_defs(start, site):
    """[start, site) 内每条指令的目标寄存器 -> (addr, mnem, op_str, src_text)"""
    defs = collections.defaultdict(list)
    body = dis(start, site + 16)
    for (a, sz, mn, os_) in body:
        if a >= site:
            break
        head = os_.split(",")[0].strip()
        if not re.match(r"^[a-z]{2,4}$", head):
            continue
        if mn in _WRITE_MN or mn.startswith("mov"):
            src = os_.split(",", 1)[1].strip() if "," in os_ else ""
            defs[head].append((a, mn, os_, src))
    return defs, body


def resolve_reg(host, site, reg, depth=0, seen=None):
    """回溯 reg 在 [host,site) 内最近一次定义，判定 this / stack / arg / other。"""
    if seen is None:
        seen = set()
    if depth > 4 or reg in seen or host is None:
        return dict(kind="unresolved", chain=[])
    seen.add(reg)
    defs, _ = reg_defs(host, site)
    lst = defs.get(reg)
    if not lst:
        return dict(kind="undefined_in_host", chain=[], reg=reg)
    a, mn, os_, src = lst[-1]
    rec = dict(reg=reg, defsite=H(a), mnem=mn, ins=os_, src=src, chain=[])
    if mn == "lea":
        m = re.match(r"^\[?\s*([a-z]{2,4})(\s*\+\s*0x([0-9a-f]+))?\s*\]?$", src)
        if m:
            base = m.group(1)
            off = int(m.group(3), 16) if m.group(3) else 0
            sub = resolve_reg(host, a, base, depth + 1, seen)
            rec["chain"] = [sub]
            if sub["kind"] == "this":
                rec["kind"] = "this"
                rec["offset"] = sub.get("offset", 0) + off
                return rec
        rec["kind"] = "other"
        return rec
    if src == "ecx":
        rec["kind"] = "this"
        rec["offset"] = 0
        return rec
    if "[esp" in src or "[ebp" in src:
        rec["kind"] = "stack"
        rec["offset"] = None
        return rec
    if re.match(r"^[a-z]{2,4}$", src):
        sub = resolve_reg(host, a, src, depth + 1, seen)
        rec["chain"] = [sub]
        rec["kind"] = sub["kind"] if sub["kind"] in ("this", "stack", "arg") else "reg_chain:" + sub["kind"]
        rec["offset"] = sub.get("offset")
        return rec
    if mn == "xor" and src == reg:
        rec["kind"] = "zeroed"
        return rec
    rec["kind"] = "other"
    return rec


def classify_store(st, derive_host=True):
    """分类一个 mov [mem], imm 装表点（形态 + 宿主 + 身份）。"""
    r = dict(site=st["site"], site_h=H(st["site"]), ins=st["text"],
             base=st["base"], index=st["index"], disp=H(st["disp"]) if st["disp"] else "0",
             imm=H(st["imm"]))
    site = st["site"]
    # --- 目标形态
    if st["base"] is None and st["index"] is None:
        r["target_kind"] = "abs"
        r["abs"] = st["disp"]
        r["abs_sec_vsize"] = pe.sec_vsize_of(st["disp"])
        r["abs_sec_rsize"] = pe.sec_of(st["disp"])
        r["abs_in_data_vsize"] = DATA_LO <= st["disp"] < DATA_HI
        r["abs_in_data_rsize"] = DATA_LO <= st["disp"] < DATA_HI_RSIZE
    elif st["base"] in ("esp", "ebp"):
        r["target_kind"] = "stack"
    else:
        r["target_kind"] = "reg"
    # --- 宿主（独立求，不采用执行器值）
    if derive_host:
        at = atlas_fn_of(site)
        own = own_start_of(site)
        own_max = max(own) if own else None
        if at is not None:
            host, method = at, "atlas"
        elif own_max is not None:
            host, method = own_max, "own:pad+clean"
        else:
            host, method = None, "none"
        r["host"], r["host_method"] = H(host), method
        r["host_own_candidates"] = [H(x) for x in own]
        r["host_atlas"] = H(at)
        ex = extent(host)
        r["host_extent"] = dict(start=H(ex["start"]), end=H(ex["end"]),
                                ret=H(ex["ret"]), retop=ex["retop"],
                                method=ex["method"], atlas=ex["atlas"])
        r["site_inside_host"] = bool(host is not None and ex["end"] is not None
                                     and host <= site < ex["end"])
        r["host_is_function_start"] = bool(
            host is not None and (host in ATL or pe.u8(host - 1) in (0xCC, 0x90, 0xC3)))
        r["dtor"] = dtor_signature(host, ex["end"])
        if host is not None:
            body = [x for x in dis(host, ex["end"] + 8) if x[0] < ex["end"]]
            r["prologue"] = ["%08X %s %s" % (a, mn, o) for (a, sz, mn, o) in body[:8]]
            r["tail"] = ["%08X %s %s" % (a, mn, o) for (a, sz, mn, o) in body[-6:]]
            r["returns_this"] = any(mn == "mov" and re.match(r"^eax,\s*(esi|ecx|edi)$", o)
                                    for (a, sz, mn, o) in body)
            r["calls"] = [("%08X call %s" % (a, o)) for (a, sz, mn, o) in body if mn == "call"]
            r["first_calls"] = r["calls"][:3]
        if st["base"] and st["base"] not in ("esp", "ebp") and host is not None:
            tr = resolve_reg(host, site, st["base"])
            r["this_trace"] = tr
            r["target_kind"] = ("this" if tr["kind"] == "this" and (tr.get("offset") or 0) == 0
                                else ("this_disp" if tr["kind"] == "this" else tr["kind"]))
    return r


def wrappers_of(host):
    out = []
    for c in CALLS.get(host, []):
        wh = atlas_fn_of(c)
        if wh is None:
            own = own_start_of(c)
            wh = max(own) if own else None
        if wh is None:
            out.append(dict(call_site=H(c), wrapper=None, shaped=None))
            continue
        wex = extent(wh)
        sig = dtor_signature(wh, wex["end"])
        out.append(dict(call_site=H(c), wrapper=H(wh), wrapper_atlas=H(ATL.get(wh)),
                        wrapper_retop=wex["retop"], shaped=bool(sig["shaped"]),
                        sig=sig))
    return out


def tables_holding(entry_va, slot):
    pat = struct.pack("<I", entry_va)
    buf = bytes(pe.buf)
    out, seen = [], set()
    idx = buf.find(pat)
    while idx >= 0:
        vt = pe.base + idx - slot * 4
        if pe.in_image(vt - 4) and vt not in seen:
            col = pe.u32(vt - 4)
            if pe.in_image(col) and pe.u32(col) == 0:
                td = pe.u32(col + 12)
                mg = pe.cstr(td + 8) if pe.in_image(td) else None
                if mg and mg.startswith(".?A"):
                    out.append(dict(vt=vt, vt_h=H(vt), sec=pe.sec_of(vt), col=H(col),
                                    offset=pe.u32(col + 4), td=H(td), mangled=mg))
                    seen.add(vt)
        idx = buf.find(pat, idx + 1)
    out.sort(key=lambda t: t["vt"])
    return out


def rtti(vt):
    if vt is None or not pe.in_image(vt - 4):
        return None
    col = pe.u32(vt - 4)
    if not pe.in_image(col) or pe.u32(col) != 0:
        return None
    td = pe.u32(col + 12)
    mg = pe.cstr(td + 8) if pe.in_image(td) else None
    if not mg or not mg.startswith(".?A"):
        return None
    return dict(col=col, offset=pe.u32(col + 4), td=td, mangled=mg)


def load_tsv(p):
    with io.open(p, "r", encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l.strip()], raw


def same_class(mangled, row_name):
    cls = row_name.split("::")[0]
    return mangled == ".?AV%s@@" % cls


FH, FROWS, _ = load_tsv(os.path.join(B4, "fields.tsv"))
DH, DROWS, _ = load_tsv(os.path.join(B4, "delta.tsv"))
FN_H, FN_ROWS, _ = load_tsv(FINAL)
FINAL_BY = {r["entry"]: r for r in FN_ROWS}

FACTS = []
for fr in FROWS:
    e = fr["entry"]
    ei = int(e, 16)
    vt = int(fr["vt"], 16)
    slot = int(fr["slot"])
    site = int(fr["install_site"], 16)
    rec = dict(entry=e, vt=H(vt), slot=slot, site=H(site),
               claimed_form=fr["install_form(ctor_body|mov_abs|reg|other)"],
               claimed_host=fr["install_host"], status=fr["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"],
               name=fr["name"], note=fr["note"])
    # --- B: 六项
    rec["vt_sec"] = pe.sec_of(vt)
    rr = rtti(vt)
    rec["rtti"] = rr
    rec["slot_val"] = H(pe.u32(vt + slot * 4))
    rec["chk1_slot_val_eq_entry"] = pe.u32(vt + slot * 4) == ei
    rec["chk2_col_sig0"] = rr is not None and pe.u32(rr["col"]) == 0
    rec["chk3_col_offset0"] = rr is not None and rr["offset"] == 0
    rec["chk4_td_mangled"] = rr is not None and rr["mangled"].startswith(".?A")
    rec["chk6_vt_obtained"] = vt is not None and pe.in_image(vt)
    eex = extent(ei)
    rec["entry_extent"] = dict(start=H(eex["start"]), end=H(eex["end"]),
                               ret=H(eex["ret"]), retop=eex["retop"],
                               method=eex["method"], atlas=H(eex["atlas"]),
                               in_atlas=eex["atlas"] is not None)
    rec["chk5_site_outside_entry"] = bool(not (eex["start"] <= site < eex["end"]))
    rec["entry_is_dtor"] = dtor_signature(ei, eex["end"])
    # --- 装表指令
    same = [st for st in STORE_IMM if st["site"] == site]
    rec["store_found"] = len(same)
    if same:
        st = same[0]
        rec["store_imm_eq_vt"] = st["imm"] == vt
        rec["site_cls"] = classify_store(st)
        cls = rec["site_cls"]
        rec["host_ne_entry"] = bool(cls["host"] is not None and int(cls["host"], 16) != ei)
        if cls.get("host"):
            rec["wrappers"] = wrappers_of(int(cls["host"], 16))
            rec["host_is_dtor_by_wrapper"] = any(w.get("shaped") for w in rec["wrappers"])
        # 与执行器声明的宿主对比
        rec["host_matches_claim"] = (cls.get("host") == fr["install_host"].upper())
        # 形态复判（本审计口径）
        f = None
        if cls["target_kind"] == "abs":
            f = "mov_abs" if cls["abs_in_data_vsize"] else "mov_abs_out_of_data"
        elif cls["target_kind"] == "this":
            f = "ctor_body" if not (cls["dtor"]["shaped"] or rec.get("host_is_dtor_by_wrapper")) else "reg"
        elif cls["target_kind"] == "stack":
            f = "stack_temp"
        else:
            f = "other"
        rec["form_audit"] = f
        rec["form_claim_ok"] = (f == fr["install_form(ctor_body|mov_abs|reg|other)"])
    rec["tables_holding"] = tables_holding(ei, slot)
    rec["n_tables_holding"] = len(rec["tables_holding"])
    # --- final.tsv 原表
    fv = FINAL_BY.get(e)
    if fv:
        rec["final"] = dict(vt=fv["vt"], slot=fv["slot"], install_site=fv["install_site"],
                            direct_sites=fv.get("direct_sites"), note=fv.get("note"))
        ofvt = int(fv["vt"], 16)
        orr = rtti(ofvt)
        rec["final_rtti"] = orr
        rec["final_slot_val"] = H(pe.u32(ofvt + int(fv["slot"]) * 4))
        rec["class_fix_needed"] = bool(orr and not same_class(orr["mangled"], fr["name"]))
    FACTS.append(rec)
    print("%s vt=%s slot=%-3d site=%s form=%-11s host=%s inside=%s dtor=%s wrapperDtor=%s" % (
        e, H(vt), slot, H(site), rec.get("form_audit"), rec["site_cls"].get("host") if rec.get("site_cls") else None,
        rec["site_cls"].get("site_inside_host") if rec.get("site_cls") else None,
        rec["site_cls"].get("dtor", {}).get("shaped") if rec.get("site_cls") else None,
        rec.get("host_is_dtor_by_wrapper")))


out = dict(exe=EXE, exe_sha=pe.sha, exe_sha_ok=pe.sha == EXE_SHA, n_instr=N_INSTR,
           sections=[dict(name=s["name"], va=H(s["va"]), vsize=H(s["vsize"]),
                          rsize=H(s["rsize"]),
                          end_vsize=H(s["va"] + s["vsize"]),
                          end_rsize=H(s["va"] + s["rsize"])) for s in pe.secs],
           data=dict(lo=H(DATA_LO), hi_vsize=H(DATA_HI), hi_rsize=H(DATA_HI_RSIZE)),
           rows=FACTS)
with io.open(os.path.join(HERE, "_facts.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)

# 缓存索引，供后续定向核查脚本复用（同一套自建索引，不是执行器产物）
import pickle
with open(os.path.join(HERE, "_index.pkl"), "wb") as f:
    pickle.dump(dict(stores=STORE_IMM,
                     imm_any={k: v for k, v in IMM_ANY.items()},
                     calls=dict(CALLS), atlas=ATL, rets=RETS,
                     text=dict(va=TEXT["va"], vsize=TEXT["vsize"]),
                     data=dict(lo=DATA_LO, hi=DATA_HI, hi_r=DATA_HI_RSIZE)), f)
print("wrote _facts.json / _index.pkl")
