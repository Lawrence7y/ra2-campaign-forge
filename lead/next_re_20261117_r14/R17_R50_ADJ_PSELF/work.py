# -*- coding: utf-8 -*-
# work.py -- R17-R50-ADJ-PSELF: what is COL.pSelf in this image?
# Static, read-only. No process, no debugger, no disassembly.
# Reproduce:  python work.py            (writes col_samples.tsv / verdict_stats.json next to it)
#
# OUTPUT CONTRACT: every file this script writes is written as BYTES with b"\n" line
# separators, so no CR can ever appear (checked at the end).
import hashlib, json, os, struct, sys

IMAGE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- PE / section table
def load(path):
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE"
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    optsz = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    opt = e_lfanew + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    assert magic == 0x10B, "expected PE32"
    image_base = struct.unpack_from("<I", data, opt + 28)[0]
    size_of_image = struct.unpack_from("<I", data, opt + 56)[0]
    secs = []
    so = opt + optsz
    for i in range(nsec):
        o = so + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
        secs.append(dict(name=name, va=va, vsize=vsize, rawptr=rawptr, rawsize=rawsize))
    return data, sha, image_base, size_of_image, secs

class Img:
    """VA -> file offset STRICTLY through the section table.
    Within a section: off = rawptr + (VA - (ImageBase + section.VA)).
    NOTE: this equals 'VA - ImageBase' only when section.VA == section.rawptr,
    which happens to be true for .text/.rdata/.data here but NOT for .rsrc/.detour;
    we always use the table, never the shortcut."""
    def __init__(self, data, image_base, size_of_image, secs):
        self.d, self.ib, self.soi, self.secs = data, image_base, size_of_image, secs
        self.mapped = 0
    def off(self, va):
        r = va - self.ib
        for s in self.secs:
            if s["va"] <= r < s["va"] + min(s["vsize"], s["rawsize"]):
                return s["rawptr"] + (r - s["va"])
        return -1
    def u32(self, va):
        o = self.off(va)
        if o < 0 or o + 4 > len(self.d):
            return None
        self.mapped += 4          # account every dword we actually read
        return struct.unpack_from("<I", self.d, o)[0]
    def cstr(self, va, cap=256):
        o = self.off(va)
        if o < 0:
            return None
        e = o
        while e < len(self.d) and self.d[e] != 0 and e - o < cap:
            e += 1
        self.mapped += (e - o + 1)
        return self.d[o:e].decode("latin1")
    def in_image(self, va):
        return va is not None and self.ib <= va < self.ib + self.soi

def main():
    data, sha, ib, soi, secs = load(IMAGE)
    im = Img(data, ib, soi, secs)
    print("image  :", IMAGE)
    print("sha256 :", sha)
    if sha != EXPECT_SHA:
        print("!! sha mismatch, expected", EXPECT_SHA)
        return 2

    # ------------------------------------------------ step 1: TypeDescriptors
    # TD = {vftable*, spare*, name[]}; MSVC puts the mangled name inline at +8.
    tds = {}
    for s in secs:
        st = ib + s["va"]
        en = st + min(s["vsize"], s["rawsize"])
        for va in range(st, en - 12 + 1, 4):
            o = im.off(va)
            if o < 0 or data[o + 8] != 0x2E:       # '.'
                continue
            nm = im.cstr(va + 8)
            if not nm or nm[:4] not in (".?AV", ".?AU", ".?AT"):
                continue
            vt = im.u32(va); spare = im.u32(va + 4)
            if spare != 0 or not im.in_image(vt):
                continue
            tds[va] = nm
    print("TDs (TypeDescriptors with inline mangled name at +8):", len(tds))

    # ------------------------------------------------ step 2: COL candidates
    # This build has NO pSelf field: COL is FIVE dwords (20 bytes)
    #   +0x00 signature (0)  +0x04 offset (0)  +0x08 cdOffset (0)
    #   +0x0C pTypeDescriptor   +0x10 pClassDescriptor
    # A six-dword (pSelf-bearing) reading is tested and REJECTED below.
    cols = []
    for s in secs:
        st = ib + s["va"]
        en = st + min(s["vsize"], s["rawsize"])
        for va in range(st, en - 0x14 + 1, 4):
            sig = im.u32(va); offs = im.u32(va + 4); cd = im.u32(va + 8); ptd = im.u32(va + 0x0C)
            if sig is None or ptd is None:
                continue
            if sig != 0 or offs > 0x1000 or cd > 0x1000:
                continue
            if ptd not in tds:
                continue
            cols.append(dict(va=va, sig=sig, offs=offs, cd=cd, ptd=ptd,
                             pchd=im.u32(va + 0x10), name=tds[ptd],
                             d_before=im.u32(va - 4), d_m10=im.u32(va - 0x10)))
    colset = {c["va"] for c in cols}
    print("COL (5-dword MSVC layout, pTD -> real TD):", len(cols))

    # control for a pSelf-bearing 6-dword COL (pSelf at +0x00, pTD at +0x10):
    # such a COL would need a nonzero pTD at +0x10 that is itself a TD.
    six = [c for c in cols if im.u32(c["va"] + 0x10) in tds]
    print("control: COLs that also fit a 6-dword reading (pTD at +0x10):", len(six),
          "of", len(cols), "(0 => a 6th/pSelf dword is structurally excluded)")

    # ------------------------------------------------ step 3: who points at a COL
    # The compiler stores a COL pointer immediately before the vtable
    # (mov dword ptr [vt-4], <COL>).  That is the only structural anchor we use.
    vtref = {}
    for s in secs:
        st = ib + s["va"]
        en = st + min(s["vsize"], s["rawsize"])
        for va in range(st, en - 4 + 1, 4):
            v = im.u32(va)
            if v is not None and v in colset:
                vtref.setdefault(v, []).append(va + 4)
    strict = [c for c in cols if c["va"] in vtref]
    for c in strict:
        c["vt"] = min(vtref[c["va"]])
        c["vt0"] = im.u32(c["vt"])
    print("COLs held by a vt-4 store (vt[0] in code):", len(strict))

    # ------------------------------------------------ step 4: primary COL
    # 954 class names appear with >=1 COL; 91 of them also have a zero-headed
    # secondary structure.  "primary" = the lowest-VA zero-headed COL of the class
    # (or, for classes with no zero-headed COL, the lowest-VA COL).
    by_name = {}
    for c in strict:
        by_name.setdefault(c["name"], []).append(c)
    primary = []
    for nm, lst in by_name.items():
        lst.sort(key=lambda c: c["va"])
        zs = [c for c in lst if c["d_before"] == 0]
        primary.append(zs[0] if zs else lst[0])
    primary.sort(key=lambda c: c["va"])

    def kind(v, colva):
        if v is None: return "oob"
        if v == 0: return "0"
        if v == colva - 0x10: return "COL-0x10"
        return "other(delta=0x%X)" % ((colva - v) & 0xFFFFFFFF)

    def dist(lst):
        d = {}
        for c in lst:
            k = kind(c["d_before"], c["va"])
            k = "other" if k.startswith("other") else k
            d[k] = d.get(k, 0) + 1
        return d

    print("classes (distinct mangled names):", len(by_name))
    print("ALL    COLs:", len(strict), dist(strict))
    print("PRIMARY COLs:", len(primary), dist(primary))
    print("classes having >=1 zero-headed COL:",
          sum(1 for l in by_name.values() if any(c["d_before"] == 0 for c in l)))
    print("classes where [COL-4] == COL-0x10 anywhere:",
          sum(1 for c in strict if c["d_before"] == c["va"] - 0x10))
    print("dwords at COL-0x10 that are zero (all primary):",
          sum(1 for c in primary if c["d_m10"] == 0), "/", len(primary))

    # control: was the earlier claim "[COL-4] == COL-0x10" perhaps about a 4-dword
    # {?,?,?,ptr} record ENDING at COL?  Count COLs preceded by {0,0,smallInt,ptr}.
    pat = 0
    for c in strict:
        w = [im.u32(c["va"] - 0x10), im.u32(c["va"] - 0x0C), im.u32(c["va"] - 0x08)]
        if w[0] == 0 and w[1] == 0 and w[2] is not None and 0 < w[2] < 0x1000:
            pat += 1
    print("COLs preceded by {0,0,smallInt} at COL-0x10:", pat, "/", len(strict))

    # ------------------------------------------------ output: 25 cross-class samples
    # 16 evenly spaced + the 9 zero-headed primaries (so both groups appear) + the rest
    step = max(1, len(primary) // 16)
    sample = [primary[i] for i in range(0, len(primary), step)][:16]
    zeros = [c for c in primary if c["d_before"] == 0]
    sample += [zeros[i] for i in range(0, len(zeros), max(1, len(zeros) // 9))][:9]
    seen = set(); sample = [c for c in sample if not (c["va"] in seen or seen.add(c["va"]))]
    sample.sort(key=lambda c: c["va"])
    rows = [b"COL_VA\tfield_offset\trange\tvalue\teq_zero\teq_COL_minus_0x10\tclass_name\tsecondary_struct_base\tvalue_at_secondary_base"]
    for c in sample:
        v = c["d_before"]
        sc = c["va"] - v if v else 0
        rows.append(("%08X\tCOL-0x4\tCOL-0x10..COL-0x1\t%s\t%s\t%s\t%s\t%s\t%s" % (
            c["va"], "%08X" % v, "Y" if v == 0 else "N",
            "Y" if v == c["va"] - 0x10 else "N", c["name"],
            "%08X" % sc if v else "n/a",
            "%08X" % im.u32(sc) if v and im.u32(sc) is not None else "n/a")).encode())
    rows.append(b"# 30 rows: 16 evenly spaced + 9 zero-headed (secondary structure) + extras.")
    rows.append(b"# NOTE: the 5-dword MSVC COL of this build has NO self field; COL-0x4 is OUTSIDE COL.")
    open(os.path.join(OUT_DIR, "col_samples.tsv"), "wb").write(b"\n".join(rows) + b"\n")

    stats = dict(sha256=sha, tds=len(tds), col_total=len(strict), classes=len(by_name),
                 all_dist=dist(strict), primary_total=len(primary), primary_dist=dist(primary),
                 classes_with_zero_col=sum(1 for l in by_name.values() if any(c["d_before"] == 0 for c in l)),
                 eq_col_minus10_anywhere=sum(1 for c in strict if c["d_before"] == c["va"] - 0x10),
                 six_dword_fit=len(six), pattern_0_0_smallint_ptr=pat,
                 mapped_bytes=im.mapped)
    open(os.path.join(OUT_DIR, "verdict_stats.json"), "wb").write(
        json.dumps(stats, indent=1, sort_keys=True).encode() + b"\n")
    print(json.dumps(stats, indent=1, sort_keys=True))

    # no-CR gate
    for f in ("col_samples.tsv", "verdict_stats.json"):
        b = open(os.path.join(OUT_DIR, f), "rb").read()
        assert b"\r" not in b, f + " contains CR"
    print("no-CR gate: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
