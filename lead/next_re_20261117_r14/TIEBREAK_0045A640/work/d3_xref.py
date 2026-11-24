"""d3_xref.py — atlas-free cross-reference channels for 0045A640's ring ④.

Channels (deliberately independent of function_atlas.tsv entry+size):
  A  raw-byte + backward-decode : locate every `mov [mem], imm32` whose imm is a
     given vtable VA, without consulting any function boundary table.
  B  full linear sweep          : decode .text from its first byte, collect every
     `mov [mem], imm32` with imm inside .rdata.  Independent second count.
  C  raw-byte rel32 arithmetic  : locate `E8 rel32` / `E9 rel32` to a target by
     pure arithmetic on every byte offset, then confirm by decoding at the site.

atexit set (R14_COMMON §8.1 ㉓): pairs `push <imm32>; call 0x7C978A`.  The call
uses a *rel32* operand, so the target VA never appears as a literal dword —
that mistake is why a naive dword search finds 0 pairs.

Function ownership: self-validating backward search — a candidate start is
accepted only if linear decoding from it lands exactly on the site address.
"""
import json
import os
import struct
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")

TARGET_FN = 0x0045A640
VT_DV = 0x007E44F4          # ?$DynamicVectorClass@PAVFoggedObjectClass@@
VT_V = 0x007E4514           # ?$VectorClass@PAVFoggedObjectClass@@
ATEXIT = 0x007C978A
GLOBAL_DV = 0x008B3D10
BASE_CTOR = 0x00488080      # VectorClass<FoggedObjectClass*> ctor (ret 8)


def main():
    pe = open_pe()
    txt = next(s for s in pe.sections if s["name"] == ".text")
    text_va = pe.image_base + txt["vaddr"]
    text_end = text_va + txt["rawsize"]
    tb = pe.buf[txt["rawptr"]:txt["rawptr"] + txt["rawsize"]]
    rd = next(s for s in pe.sections if s["name"] == ".rdata")
    rdata_lo = pe.image_base + rd["vaddr"]
    rdata_hi = rdata_lo + rd["rawsize"]

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    def decode_at(va, n=1):
        off = va - text_va
        if off < 0 or off >= len(tb):
            return []
        return list(md.disasm(tb[off:off + 16], va, n))

    # ---------------- full linear sweep (Channel B) -------------------------
    insns = []          # (va, size, mnem, op_str, target_or_None, kind)
    call_sites = {}     # target -> [site,...]
    pc = text_va
    while pc < text_end:
        got = decode_at(pc)
        if not got:
            pc += 1
            continue
        ins = got[0]
        tgt = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM \
                and ins.mnemonic in ("call", "jmp", "jcc") or \
                (ins.operands and ins.operands[0].type == X86_OP_IMM and
                 ins.mnemonic.startswith("j")):
            tgt = ins.operands[0].imm
        if ins.mnemonic in ("call", "jmp") and tgt is not None:
            call_sites.setdefault(tgt, []).append((ins.address, ins.mnemonic))
        insns.append((ins.address, ins.size, ins.mnemonic, ins.op_str, tgt,
                      ins.operands[1].imm if (ins.mnemonic == "mov" and len(ins.operands) == 2
                                              and ins.operands[1].type == X86_OP_IMM) else None))
        pc += ins.size
    insn_size = {a: sz for (a, sz, mn, ops, t, imm) in insns}

    boundaries = {a for (a, sz, mn, ops, t, imm) in insns}

    # ---------------- atexit set -------------------------------------------
    # `push <dtor>; call 0x7C978A`.  The call operand is rel32, so the target VA
    # never appears as a literal dword in .text — scanning for the dword finds 0
    # pairs (a real trap; Channel C does the arithmetic instead).
    def raw_calls_to(target):
        out = []
        for i in range(len(tb) - 5):
            if tb[i] not in (0xE8, 0xE9):
                continue
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            site = text_va + i
            if (site + 5 + rel) & 0xFFFFFFFF != target:
                continue
            got = decode_at(site)
            if got and got[0].size == 5 and got[0].mnemonic == "call" \
                    and got[0].operands[0].imm == target:
                out.append(site)
        return out

    atexit_pairs = []
    for site in raw_calls_to(ATEXIT):
        # the `push <dtor>` is NOT necessarily adjacent: MSVC emits
        #   push <dtor>; <field init>; call __onexit; pop ecx; ret
        # so we scan backwards for the nearest `push imm32` that is an
        # instruction boundary and whose imm lands in .text.
        dtor = None
        for back in range(5, 0x180):
            cand = site - back
            if cand < text_va or cand not in boundaries:
                continue
            got = decode_at(cand)
            if not got or got[0].size != 5 or got[0].mnemonic != "push":
                continue
            if got[0].operands[0].type != X86_OP_IMM:
                continue
            imm = got[0].operands[0].imm
            if text_va <= imm < text_end:
                dtor = imm
                break
        atexit_pairs.append(dict(call_site=site, dtor=dtor))
    dtor_set = sorted({p["dtor"] for p in atexit_pairs if p["dtor"] is not None})

    # ---------------- function start recovery -------------------------------
    # Ownership is reported as the nearest preceding *verified* `ret`-family
    # instruction (a sweep boundary whose decode is ret/ret imm16), then padding
    # (90/CC) skipped.  We deliberately do NOT claim the true entry when the
    # function's first bytes are not a standard prologue; the EVIDENCE records
    # the anchor ret address so the claim is checkable.
    cache = {}

    def find_func_start(site, window=0x600):
        if site in cache:
            return cache[site]
        res = None
        lo = max(text_va, site - window)
        for cand in range(site - 1, lo - 1, -1):
            if cand not in boundaries:
                continue
            got = decode_at(cand)
            if not got or not got[0].mnemonic.startswith("ret"):
                continue
            end = cand + got[0].size
            p = end
            while p < site and tb[p - text_va] in (0x90, 0xCC):
                p += 1
            if p > site:
                continue
            # no further ret between p and site
            q = p
            ok = True
            for _ in range(3000):
                if q == site:
                    break
                if q not in boundaries:
                    ok = False
                    break
                g = decode_at(q)
                if not g:
                    ok = False
                    break
                if g[0].mnemonic.startswith("ret"):
                    ok = False
                    break
                q += g[0].size
            if ok and q == site:
                res = dict(start=p, anchor_ret=cand,
                           anchor_kind=f"{got[0].mnemonic} {got[0].op_str}".strip())
                break
        cache[site] = res
        return res

    # ---------------- Channel A: raw byte + backward decode -----------------
    def find_imm_sites(imm):
        pat = struct.pack("<I", imm)
        out = []
        i = -1
        while True:
            i = tb.find(pat, i + 1)
            if i < 0:
                break
            hit_va = text_va + i
            rec = None
            for back in range(2, 11):
                got = decode_at(hit_va - back)
                if not got:
                    continue
                ins = got[0]
                if ins.size != back + 4 or not ins.operands:
                    continue
                if ins.operands[-1].type != X86_OP_IMM or ins.operands[-1].imm != imm:
                    continue
                r = dict(site=ins.address, size=ins.size, mnemonic=ins.mnemonic,
                         op_str=ins.op_str, ok=True, dst_kind=None, dst=None,
                         raw_hit=hit_va)
                op = ins.operands[0]
                if op.type == X86_OP_MEM:
                    base = ins.reg_name(op.mem.base) or ""
                    idx = ins.reg_name(op.mem.index) or ""
                    if not base and not idx:
                        r["dst_kind"] = "global"
                        r["dst"] = op.mem.disp & 0xFFFFFFFF
                    else:
                        r["dst_kind"] = "field"
                        r["dst"] = f"[{base}{('+'+idx) if idx else ''}{op.mem.disp:+#x}]"
                else:
                    r["dst_kind"] = "register"
                    r["dst"] = ins.op_str
                rec = r
                break
            out.append(rec if rec else dict(raw_hit=hit_va, ok=False))
        return out

    sites_dv = find_imm_sites(VT_DV)
    sites_v = find_imm_sites(VT_V)
    for lst in (sites_dv, sites_v):
        for s in lst:
            if s.get("ok"):
                fs = find_func_start(s["site"])
                s["func_start"] = fs
                s["in_atexit_dtor"] = bool(fs and fs["start"] in set(dtor_set))

    # ---------------- Channel C: raw rel32 arithmetic for callers ----------
    def raw_callers(target):
        out = []
        for i in range(len(tb) - 5):
            op = tb[i]
            if op not in (0xE8, 0xE9):
                continue
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            site = text_va + i
            if (site + 5 + rel) & 0xFFFFFFFF != target:
                continue
            got = decode_at(site)
            if not got:
                continue
            ins = got[0]
            if ins.size == 5 and ins.mnemonic in ("call", "jmp") \
                    and ins.operands[0].type == X86_OP_IMM \
                    and ins.operands[0].imm == target:
                out.append(dict(site=ins.address, mnemonic=ins.mnemonic,
                                op_str=ins.op_str,
                                func_start=find_func_start(ins.address)))
        return out

    callers_target = raw_callers(TARGET_FN)
    callers_ctordv = raw_callers(0x00457BE2)
    callers_ctordv = callers_ctordv  # not used; kept for shape
    callers_base = raw_callers(BASE_CTOR)

    # ---------------- Channel B installs into .rdata ------------------------
    sweep_installs = [(a, mn, ops, imm) for (a, sz, mn, ops, t, imm) in insns
                      if mn == "mov" and imm is not None
                      and rdata_lo <= (imm & 0xFFFFFFFF) < rdata_hi
                      and "dword ptr [" in ops]
    glob_installs = [x for x in sweep_installs if "[0x8b3d10]" in x[2]]

    meta = dict(text_va=text_va, text_end=text_end, sweep_instructions=len(insns),
                sweep_rdata_installs=len(sweep_installs),
                atexit_pairs=len(atexit_pairs), atexit_distinct_dtors=len(dtor_set),
                channel_c_callers=len(callers_target),
                installs_vt44f4=sum(1 for s in sites_dv if s.get("ok")),
                installs_vt4514=sum(1 for s in sites_v if s.get("ok")),
                glob_8b3d10_installs=len(glob_installs))

    L = ["# xref channels (atlas-free) — 0045A640 ring ④", ""]
    L.append(f"# .text  {text_va:#010x}..{text_end:#010x}   Channel-B sweep instrs={len(insns)}")
    L.append(f"# .rdata {rdata_lo:#010x}..{rdata_hi:#010x} (used only as the 'this imm is a vtable' window)")
    L.append(f"# atexit `push <dtor> ... call 0x7C978A`: {len(atexit_pairs)} call sites, "
             f"{len(dtor_set)} distinct pushed dtors")
    L.append("")
    fs_txt = lambda fs: (f"{fs['start']:#010x} (>= block start; anchored at "
                         f"{fs['anchor_ret']:#010x} `{fs['anchor_kind']}`)") if fs else "None"
    for tag, sites in (("007E44F4  .?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@", sites_dv),
                       ("007E4514  .?AV?$VectorClass@PAVFoggedObjectClass@@@@", sites_v)):
        L.append(f"## 装表点 installs of {tag}   [Channel A: raw byte + backward decode]")
        for s in sites:
            if not s.get("ok"):
                L.append(f"  RAW HIT {s['raw_hit']:#010x}: no instruction ends on it "
                         f"(byte-level false positive, rejected)")
                continue
            L.append(f"  site {s['site']:#010x}  {s['mnemonic']} {s['op_str']:<30} "
                     f"dst={s['dst_kind']:<6} atexit_dtor={s['in_atexit_dtor']}")
            L.append(f"        containing: {fs_txt(s['func_start'])}")
        L.append("")
    L.append("## Channel B (independent linear sweep) — same instruction set")
    for a, mn, ops, imm in sweep_installs:
        if imm in (VT_DV, VT_V):
            L.append(f"  {a:#010x}  {mn} {ops}")
    L.append("")
    L.append(f"## Channel C: direct E8/E9 to {TARGET_FN:#010x} = {len(callers_target)}")
    for c in callers_target:
        L.append(f"  {c['site']:#010x} {c['mnemonic']} {c['op_str']} in={fs_txt(c['func_start'])}")
    L.append("")
    L.append(f"## Channel C: callers of VectorClass<FoggedObjectClass*> ctor {BASE_CTOR:#010x} "
             f"= {len(callers_base)}")
    for c in callers_base:
        L.append(f"  {c['site']:#010x} {c['mnemonic']} {c['op_str']} in={fs_txt(c['func_start'])}")
    L.append("")
    L.append(f"## absolute-global installs into [0x8B3D10] = {len(glob_installs)}")
    for a, mn, ops, imm in glob_installs:
        L.append(f"  {a:#010x}  {mn} {ops}  imm={imm:#010x}")
    L.append("")
    L.append("## is any install site inside an atexit-registered dtor?")
    any_hit = False
    for s in [x for x in sites_dv + sites_v if x.get("ok")]:
        if s["in_atexit_dtor"]:
            any_hit = True
            L.append(f"  YES {s['site']:#010x} -> registered dtor {s['func_start']['start']:#010x}")
    if not any_hit:
        L.append("  no")
    L.append("")
    L.append("## atexit-registered dtors that appear as an install-site owner")
    for s in [x for x in sites_dv + sites_v if x.get("ok")]:
        if s["func_start"] and s["func_start"]["start"] in set(dtor_set):
            L.append(f"  dtor {s['func_start']['start']:#010x} installs {s['site']:#010x} = {s['op_str']}")
    L.append("")
    L.append("## the 0x4D0750 static-init / 0x4D0790 dtor pair, as evidence")
    for p in atexit_pairs:
        if p["dtor"] in (0x004D0790,):
            L.append(f"  call 0x7C978A at {p['call_site']:#010x} registers dtor {p['dtor']:#010x}")

    out = "\n".join(L)
    with open(os.path.join(EV, "xref_installs.txt"), "w", encoding="utf-8") as f:
        f.write(out + "\n")
    with open(os.path.join(HERE, "xref.json"), "w", encoding="utf-8") as f:
        json.dump(dict(meta=meta, sites_dv=sites_dv, sites_v=sites_v,
                       callers_target=callers_target, callers_base=callers_base,
                       glob_installs=[list(x) for x in glob_installs],
                       atexit_dtors=dtor_set), f, indent=1, default=str)
    print(out)


if __name__ == "__main__":
    main()
