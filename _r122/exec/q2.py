#!/usr/bin/env python3
"""Q2: scan .text for E8 rel32 whose target lands in the twin-function range.

Range interpretation: card gives [0x67fdf0,0x680f80]. That value exceeds the end of
.text as an RVA (.text RVA end = 0x3df38d+0x1000), so the card's numbers are
ABSOLUTE VAs, i.e. RVA [0x27fdf0, 0x280f80].

Two independent passes:
  P1 raw byte scan for 0xe8 (no big objects, streaming)
  P2 instruction-boundary sweep: capstone disasm_lite with explicit 1-byte resync
     so undecodable bytes do not truncate the sweep. detail stays off.
"""
import json, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q2.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
text = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
TV, TRP, TRS = text.VirtualAddress, text.PointerToRawData, text.SizeOfRawData
with open(EXE, "rb") as f:
    f.seek(TRP); tb = f.read(TRS)

LO_RVA, HI_RVA = 0x67FDF0 - IB, 0x680F80 - IB

# ---------- P1: raw byte scan ----------
raw = []
i = tb.find(b"\xe8")
while i != -1:
    if i + 5 <= len(tb):
        d = struct.unpack_from("<i", tb, i + 1)[0]
        tgt = (TV + i + 5 + d) & 0xFFFFFFFF
        if LO_RVA <= tgt <= HI_RVA:
            raw.append({"site_rva": TV + i, "site_va": IB + TV + i,
                        "rel32": d, "target_rva": tgt, "target_va": IB + tgt})
    i = tb.find(b"\xe8", i + 1)

# ---------- P2: resyncing linear sweep ----------
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
insn = []
off = 0
n_dec = 0
while off < len(tb):
    progressed = False
    for a, sz, mn, ops in md.disasm_lite(tb[off:], TV + off):
        n_dec += 1
        progressed = True
        nxt = a + sz - TV
        if mn == "call":
            try:
                tgt = int(ops, 0)
            except ValueError:
                tgt = None
            if tgt is not None and LO_RVA <= tgt <= HI_RVA:
                insn.append({"site_rva": a, "site_va": IB + a, "target_rva": tgt,
                             "target_va": IB + tgt, "len": sz})
        if nxt <= off:          # safety against zero-progress
            break
        off = nxt
    # capstone stopped; if it made no progress we are on an undecodable byte -> skip 1
    if not progressed:
        off += 1
    elif off < len(tb):
        # loop re-enters at off, which is already the first undecoded byte
        pass

def group(sites):
    g = {}
    for s in sites:
        g.setdefault(s["target_rva"], []).append(s)
    return {("%#x" % k): sorted(v, key=lambda x: x["site_rva"]) for k, v in sorted(g.items())}

# ---------- self tests ----------
probe = b"\xe8" + struct.pack("<i", LO_RVA - 5)
pos_ok = ((5 + struct.unpack_from("<i", probe, 1)[0]) & 0xFFFFFFFF) == LO_RVA
tg2 = (5 + struct.unpack_from("<i", (b"\xe8" + struct.pack("<i", LO_RVA - 6)), 1)[0]) & 0xFFFFFFFF
neg_ok = not (LO_RVA <= tg2 <= HI_RVA)
mono_ok = len(raw) >= len(insn)
p1 = {(s["site_rva"], s["target_rva"]) for s in raw}
sub_ok = all((s["site_rva"], s["target_rva"]) in p1 for s in insn)
assert pos_ok and neg_ok and mono_ok and sub_ok

res = {
    "image_base": IB,
    "range_as_absolute_va": ["0x67fdf0", "0x680f80"],
    "range_as_rva": ["%#x" % LO_RVA, "%#x" % HI_RVA],
    "why_absolute": "0x67fdf0 > .text RVA end %#x, so the card range is VA" % (TV + text.Misc_VirtualSize),
    "pass1_raw_bytescan": {"n_sites": len(raw), "n_targets": len({s['target_rva'] for s in raw}),
                           "sites": raw, "by_target": group(raw)},
    "pass2_resync_sweep": {"n_sites": len(insn), "n_targets": len({s['target_rva'] for s in insn}),
                           "n_decoded_insns": n_dec, "text_size": TRS,
                           "sites": insn, "by_target": group(insn)},
    "self_test": {"positive_exact_lower_bound": pos_ok, "negative_one_below_rejected": neg_ok,
                  "pass1_superset_of_pass2": mono_ok, "pass2_sites_subset_of_pass1": sub_ok},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

tg = sorted({s['target_rva'] for s in raw})
print("RVA range [%#x,%#x]" % (LO_RVA, HI_RVA))
print("P1 raw    : sites=%d targets=%d" % (len(raw), len(tg)))
print("P2 resync : sites=%d targets=%d  (decoded %d insns)"
      % (len(insn), len({s['target_rva'] for s in insn}), n_dec))
print("self_test:", res["self_test"])
print("target grid deltas:", sorted({tg[i+1]-tg[i] for i in range(len(tg)-1)}))
dup = {k: v for k, v in res["pass1_raw_bytescan"]["by_target"].items() if len(v) > 1}
print("targets with >1 site:", {k: [("%#x" % x['site_rva']) for x in v] for k, v in dup.items()})
