# -*- coding: utf-8 -*-
"""
t1_enumerate.py -- mechanical enumeration of every static VectorClass<T> /
DynamicVectorClass<T> *global object* in gamemd.exe (Red Alert 2: Yuri's Revenge).

Binary : D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe
         SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

Outputs (all inside this directory, nothing outside is touched):
    vector_globals.tsv         one row per object header of a vector-typed global
    unresolved_candidates.tsv  vector-typed globals that are NOT standalone vector objects
    _stats.txt                 counts + raw evidence lines quoted in report.md

WHY A PLAIN `C7 05 <dst> <vftable>` SCAN IS INSUFFICIENT
--------------------------------------------------------
1. MSVC encodes `global.vptr = &vftable` in three ways:
      C7 05 <abs> <imm32>   mov dword ptr [abs], imm32
      A3    <abs>           mov dword ptr [abs], eax      (eax already holds the imm)
      89 0D <abs>           mov dword ptr [abs], ecx      (similarly for 15/05 = edx/eax)
   The A3/89 forms are rare but real: 0x00889E08 (TechnoClass vector inside the
   TechnoClass type-registry block), 0x0089DE18, 0x00ABFDA0, 0x0087F778, 0x00A83D24
   are only reachable that way.
2. One global can carry several different `DynamicVectorClass<T>` vptr stores (e.g.
   0x00ABFDA0 is re-initialised with 0x007EED20 nine times) -- the *destinations* must
   be deduped, not the store sites.
3. Some vector-vtable dwords in .data are **not object headers**.  Example: 20 consecutive
   `.?AV?$VectorClass@PAVObjectClass@@@@` vptr stores at 0x008B4108..0x008B4180.  They
   belong to 0x008B41E0 (`DynamicVectorClass<BuildingClass*>`), whose ctor at 0x004E7BFD
   stores the *same* vptr seven times at 0x008B4108+0x0C*k.  Type identity alone cannot
   tell them apart, so a shape/usage rule is mandatory.

CLASSIFICATION RULE (what counts as a *global vector object*)
------------------------------------------------------------
R1 header+capacity  : a `mov dword ptr [B+0x14], 10` store exists (default
                      CapacityIncrement=10, the only value the engine ever uses), and
R2 runtime usage    : code reads the object through the VectorClass layout at B,
                      i.e. reads [B+0x04] (Items) and/or [B+0x10] (Count), and
R3 own ctor         : the vptr store at B is not owned by a *neighbouring* class ctor,
                      i.e. it is not a repeated store of `B`'s vptr performed inside the
                      initialiser of another global that starts at B-0x0C*k.

Rows failing R1/R2/R3 are listed in unresolved_candidates.tsv with the reason and,
where known, the global that owns them.

Deterministic: no dict-order dependence, no randomness.  Exit 0 on success.
"""
import hashlib
import os
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
IB = 0x400000
TEXT = (0x401000, 0x7E038D)
RDATA = (0x7E1000, 0x811074)
DATA = (0x812000, 0xB79BE4)
CAPINC_OFF = 0x14
CAPINC_DEFAULT = 10
ITEMS_OFF = 0x04
COUNT_OFF = 0x10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------------------------------------- image
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class Image(object):
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.img = self.pe.get_memory_mapped_image()
        self.n = len(self.img)

    def u32(self, va):
        o = va - IB
        if o < 0 or o + 4 > self.n:
            return None
        return struct.unpack_from("<I", self.img, o)[0]

    def cstr(self, va, maxlen=512):
        o = va - IB
        if o < 0 or o >= self.n:
            return None
        e = self.img.find(b"\x00", o, min(o + maxlen, self.n))
        if e < 0:
            return None
        try:
            return self.img[o:e].decode("ascii")
        except UnicodeDecodeError:
            return None


def rtti(im, vftable):
    """vftable -> (col, td, mangled); None when the dword is not a typed vftable."""
    col = im.u32(vftable - 4)
    if col is None or not (RDATA[0] <= col < DATA[1]):
        return None
    off = im.u32(col + 0x04)
    if off is None or off >= 0x10000:
        return None
    td = im.u32(col + 0x0C)
    if td is None:
        return None
    nm = im.cstr(td + 8)
    if nm is None or not (nm.startswith(".?AV") or nm.startswith(".?AU")):
        return None
    return col, td, nm


def is_vec(nm):
    return "?$VectorClass@" in nm or "?$DynamicVectorClass@" in nm


def is_dyn(nm):
    return "?$DynamicVectorClass@" in nm


# ------------------------------------------------------------------ store extraction
def c705_stores(im):
    """Every `C7 05 dst imm32`.  Yields (addr, dst, imm) and keeps all of them."""
    lo, hi = TEXT
    t = im.img[lo - IB: hi - IB]
    out = []
    for a in range(0, len(t) - 10):
        if t[a] == 0xC7 and t[a + 1] == 0x05:
            dst, imm = struct.unpack_from("<II", t, a + 2)
            out.append((lo + a, dst, imm))
    return out


def register_form_stores(im):
    """A3/89 05/89 0D/89 15 stores whose source register provably holds a vector vftable.

    Returns [(addr, dst, imm, col, td, mangled)].  The register's value is taken from the
    last `mov <reg>, imm32` in the same basic block (no intervening call/jump).
    """
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    lo, hi = TEXT
    insns = [i for i in md.disasm(im.img[lo - IB: hi - IB], lo) if i.id != 0]
    regs = {0: "eax", 1: "ecx", 2: "edx"}
    out = []
    for idx, ins in enumerate(insns):
        if ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        dst, src = ins.operands
        if dst.type != CS_OP_MEM or src.type != 1:
            continue
        if dst.mem.base != 0 or dst.mem.index != 0:
            continue
        d = dst.mem.disp & 0xFFFFFFFF
        if not (DATA[0] <= d < DATA[1]):
            continue
        reg = src.reg
        val = None
        for back in reversed(insns[max(0, idx - 12):idx]):
            if back.mnemonic in ("call", "jmp") or back.mnemonic.startswith("j") \
                    or back.mnemonic.startswith("ret"):
                break
            if back.mnemonic == "mov" and len(back.operands) == 2 \
                    and back.operands[0].type == 1 and back.operands[0].reg == reg \
                    and back.operands[1].type == CS_OP_IMM:
                val = back.operands[1].imm & 0xFFFFFFFF
                break
        if val is None:
            continue
        r = rtti(im, val) if (RDATA[0] <= val < DATA[1]) else None
        if r is None or not is_vec(r[2]):
            continue
        out.append((ins.address, d, val, r[0], r[1], r[2]))
    return out


# ------------------------------------------------------------------------- demangling
def element_text(mangled):
    i = mangled.find("Class@")
    if i < 0:
        return "<?>"
    arg = mangled[i + len("Class@"):]
    while arg.endswith("@"):
        arg = arg[:-1]
    if arg == "K":
        return "unsigned long"
    if arg == "PBD":
        return "bool*"
    const = False
    if arg.startswith("PB"):
        const, rest = True, arg[2:]
    elif arg.startswith("PA"):
        rest = arg[2:]
    elif arg.startswith("P"):
        rest = arg[1:]
    else:
        rest = arg
    if rest[:1] in ("V", "U"):
        rest = rest[1:]
    if rest.startswith("?$"):
        # nested template, e.g. V?$rc_ptr@VGameOption@WorldDominationTour@@@@
        j = rest.find("@")
        head = rest[:j].replace("?$", "")
        tail = rest[j + 1:].rstrip("@")
        return "%s<%s>" % (head, tail)
    if rest.startswith("U"):
        # a struct/union member of an enclosing class: SCREAM@CLASS
        if "@" in rest:
            member, owner = rest.split("@", 1)
            return "%s@%s" % (member, owner)
        return rest
    return ("const %s*" % rest) if const else ("%s*" % rest)


# --------------------------------------------------------------------------- analysis
def field_ref_census(im, bases):
    """For each base: {offset: n_refs} for .text operands whose disp is in [b, b+0x18)."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    lo, hi = TEXT
    out = {b: {} for b in bases}
    for ins in md.disasm(im.img[lo - IB: hi - IB], lo):
        if ins.id == 0:
            continue
        for op in ins.operands:
            if op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                d = op.mem.disp & 0xFFFFFFFF
                for b in bases:
                    if b <= d < b + 0x18:
                        k = d - b
                        out[b][k] = out[b].get(k, 0) + 1
    return out


def build(im):
    stores = c705_stores(im)
    vptr = {}        # dst -> [(addr, imm, col, td, mangled)]
    capinc = {}      # dst -> [(addr, imm)]
    zero_store = {}  # dst -> [(addr, 0)]

    for addr, dst, imm in stores:
        if not (DATA[0] <= dst < DATA[1]):
            continue
        r = rtti(im, imm) if (RDATA[0] <= imm < DATA[1]) else None
        if r is not None and is_vec(r[2]):
            vptr.setdefault(dst, []).append((addr, imm, r[0], r[1], r[2]))
        elif r is None and 0 < imm <= 0x10000:
            capinc.setdefault(dst, []).append((addr, imm))
        elif r is None and imm == 0:
            zero_store.setdefault(dst, []).append((addr, imm))

    reg_form = register_form_stores(im)
    for addr, dst, imm, col, td, nm in reg_form:
        vptr.setdefault(dst, [])
        if all(s[1] != imm for s in vptr[dst]):
            vptr[dst].append((addr, imm, col, td, nm))
        vptr[dst].sort(key=lambda s: s[0])

    bases = sorted(vptr)
    refs = field_ref_census(im, bases)

    records = {}
    for b in bases:
        recs = vptr[b]
        dyn = [r for r in recs if is_dyn(r[4])]
        bse = [r for r in recs if not is_dyn(r[4])]
        chosen = dyn[0] if dyn else bse[0]
        r = refs.get(b, {})
        records[b] = {
            "base": b,
            "stores": recs,
            "chosen": chosen,
            "has_dyn": bool(dyn),
            "has_base": bool(bse),
            "n_stores": len(recs),
            "mangled": chosen[4],
            "ref_items": r.get(ITEMS_OFF, 0),
            "ref_count": r.get(COUNT_OFF, 0),
            "ref_zero": r.get(0, 0),
            "n_refs": sum(r.values()),
            "refmap": r,
        }

    # ---- R1: default CapacityIncrement store.
    #      The MSVC ctor writes `mov dword ptr [B+0x14], 0x0A` -- see the TechnoClass
    #      vector ctor at 0x004E79FD:
    #          0x004E79FD  C7 05 78 EC A8 00 AC 17 7E 00   mov [0x00A8EC78], 0x007E17AC
    #          0x004E7A07  C7 05 8C EC A8 00 0A 00 00 00   mov [0x00A8EC8C], 0x0000000A
    #          0x004E7A11  A3 88 EC A8 00                  mov [0x00A8EC88], eax (Count=0)
    #      i.e. Items@+4, Capacity@+8, flags@+0x0C/+0x0D, Count@+0x10, CapInc@+0x14.
    for b in bases:
        rec = records[b]
        rec["capinc_ok"] = (b + CAPINC_OFF) in capinc
        rec["capinc_at"] = capinc[(b + CAPINC_OFF)][0][0] if rec["capinc_ok"] else None
        rec["zero_count_store"] = bool(zero_store.get(b + COUNT_OFF))

    # ---- R3: is the store at B owned by a neighbouring class ctor?  A class initialiser
    #      that starts at base W writes the vector header of W first and then repeats
    #      W's vptr at W+0x0C, W+0x18, ...  If the *only* vptr store at B lives inside a
    #      window whose first store is at W = B-0x0C*k (k>=1) and B carries no CapInc
    #      store of its own, B is an embedded sub-object of W, not a vector object.
    for b in bases:
        rec = records[b]
        owner = None
        if not rec["capinc_ok"]:
            for k in (1, 2, 3, 4, 5, 6, 7, 8):
                w = b - 0x0C * k
                if w in records and records[w]["capinc_ok"]:
                    span = [s[0] for s in records[w]["stores"]]
                    if span and span[0] <= rec["stores"][0][0] <= span[-1] + 0x40:
                        owner = w
                        break
        rec["owner"] = owner

    for b in bases:
        rec = records[b]
        reasons = []
        if not rec["capinc_ok"]:
            reasons.append("R1: no `mov [base+0x14],10` (default CapacityIncrement) store")
        if rec["ref_items"] == 0 and rec["ref_count"] == 0:
            reasons.append("R2: no code reads [base+0x04] (Items) or [base+0x10] (Count)")
        if rec["owner"] is not None:
            reasons.append("R3: vptr store belongs to the initialiser of 0x%08X"
                           % rec["owner"])
        rec["reasons"] = reasons
        rec["is_global_object"] = not reasons

    extra = [(b, records[b]["stores"]) for b in bases]
    return records, bases, reg_form


# ----------------------------------------------------------------------------- output
def main():
    sha = sha256_of(EXE)
    if sha != EXPECT_SHA:
        sys.stderr.write("SHA-256 mismatch: got %s\n" % sha)
        return 2
    im = Image(EXE)
    records, bases, reg_form = build(im)

    goods = [records[b] for b in bases if records[b]["is_global_object"]]
    bads = [records[b] for b in bases if not records[b]["is_global_object"]]

    with open(os.path.join(OUT_DIR, "vector_globals.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("element\tbase\titems\tcount\tvftable\tcol\ttd\tmangled\t"
                "has_dynamic_store\thas_base_store\tn_stores\n")
        for rec in goods:
            c = rec["chosen"]
            b = rec["base"]
            f.write("\t".join([
                element_text(c[4]),
                "0x%08X" % b,
                "0x%08X" % (b + ITEMS_OFF),
                "0x%08X" % (b + COUNT_OFF),
                "0x%08X" % c[1],
                "0x%08X" % c[2],
                "0x%08X" % c[3],
                c[4],
                "yes" if rec["has_dyn"] else "no",
                "yes" if rec["has_base"] else "no",
                str(rec["n_stores"]),
            ]) + "\n")

    with open(os.path.join(OUT_DIR, "unresolved_candidates.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("candidate_addr\tmangled\tvftable\tstore_addr\t"
                "owned_by\trefs_items\trefs_count\treason\n")
        for rec in bads:
            c = rec["chosen"]
            f.write("\t".join([
                "0x%08X" % rec["base"],
                c[4],
                "0x%08X" % c[1],
                "0x%08X" % c[0],
                ("0x%08X" % rec["owner"]) if rec["owner"] is not None else "-",
                str(rec["ref_items"]),
                str(rec["ref_count"]),
                "; ".join(rec["reasons"]),
            ]) + "\n")

    with open(os.path.join(OUT_DIR, "_stats.txt"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("sha256 %s\n" % sha)
        f.write("distinct_store_destinations_with_vector_vptr %d\n" % len(bases))
        f.write("global_vector_objects %d\n" % len(goods))
        f.write("rejected %d\n" % len(bads))
        f.write("regform_stores_found %d\n" % len(reg_form))
        for s in reg_form:
            f.write("  regform 0x%08X dst=0x%08X imm=0x%08X %s\n"
                    % (s[0], s[1], s[2], s[5]))
        f.write("\nrejected detail:\n")
        for rec in bads:
            f.write("  0x%08X %s stores=%d capinc_ok=%d ref_items=%d ref_count=%d "
                    "owner=%s\n"
                    % (rec["base"], rec["mangled"], rec["n_stores"],
                       rec["capinc_ok"], rec["ref_items"], rec["ref_count"],
                       ("0x%08X" % rec["owner"]) if rec["owner"] is not None else "-"))
            for a, imm, col, td, nm in rec["stores"]:
                f.write("        store 0x%08X -> vftable 0x%08X %s\n" % (a, imm, nm))
        f.write("\nper-object store list:\n")
        for rec in goods:
            f.write("  0x%08X %s\n" % (rec["base"], rec["mangled"]))
            for a, imm, col, td, nm in rec["stores"]:
                f.write("        store 0x%08X -> vftable 0x%08X col 0x%08X td 0x%08X %s\n"
                        % (a, imm, col, td, nm))
            f.write("        capinc_store=%s ref_items=%d ref_count=%d\n"
                    % (("0x%08X" % rec["capinc_at"]) if rec["capinc_at"] else "-",
                       rec["ref_items"], rec["ref_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
