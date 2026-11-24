#!/usr/bin/env python3
"""Q5: scan .text for `c7 05 <imm32 addr> <imm32 value>` (mov dword ptr [addr], imm32)
where addr is one of the 35 BSS object VAs from Q4.

Byte scan is O(n) over .text and streaming -- no objects accumulate beyond matches.

Control tests:
  (a) positive: a synthetic c7 05 sequence with a target addr must be found;
  (b) negative: `c7 45 08 <imm32>` (mov [ebp+8], imm) must NOT be treated as an
      absolute store, because the modrm is 0x45 (disp8), not 0x05;
  (c) negative: `c7 05 <other addr> <imm>` for an addr NOT in the target set must
      be ignored;
  (d) control: c7 05 requires 10 bytes; a truncated hit at end of .text is skipped.
"""
import json, struct, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q4 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q4.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q5.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
text = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
TV, TRP, TRS = text.VirtualAddress, text.PointerToRawData, text.SizeOfRawData
with open(EXE, "rb") as f:
    f.seek(TRP); tb = f.read(TRS)

q4 = json.load(open(Q4))
targets = sorted({r["obj_va"] for r in q4["rows"]})
tset = set(targets)

def scan(buf, base_rva, want):
    """Return list of (site_rva, addr, value) for c7 05 <addr> <value> with addr in want."""
    hits = []
    i = buf.find(b"\xc7\x05")
    while i != -1:
        if i + 10 <= len(buf):
            addr = struct.unpack_from("<I", buf, i + 2)[0]
            val = struct.unpack_from("<I", buf, i + 6)[0]
            if addr in want:
                hits.append((base_rva + i, addr, val))
        i = buf.find(b"\xc7\x05", i + 1)
    return hits

hits = scan(tb, TV, tset)

groups = {}
for site, addr, val in hits:
    groups.setdefault(addr, []).append({"site_rva": site, "site_va": IB + site,
                                        "value_va": val, "value_rva": val - IB})

# per-object: was each of the 35 written at least once?
written = {t: len(groups.get(t, [])) for t in targets}

# ---- controls ----
# (a) positive synthetic
synth = b"\xc7\x05" + struct.pack("<I", targets[0]) + b"\x11\x22\x33\x44"
pos_a = scan(synth, 0, tset) == [(0, targets[0], 0x44332211)]
# (b) negative: modrm 0x45 disp8 must not match
neg_b = scan(b"\xc7\x45\x08" + struct.pack("<I", targets[0]), 0, tset) == []
# (c) negative: c7 05 with a non-target address
neg_c = scan(b"\xc7\x05" + struct.pack("<I", 0xDEADBEEF) + b"\x00\x00\x00\x00", 0, tset) == []
# (d) truncated tail skipped
tail = b"\xc7\x05" + struct.pack("<I", targets[0])[:2]
neg_d = scan(tail, 0, tset) == []
# (e) every found site must re-read from the original buffer identically
ctl_e = all(tb[s - TV:s - TV + 2] == b"\xc7\x05" for s, _, _ in hits)
assert pos_a and neg_b and neg_c and neg_d and ctl_e, (pos_a, neg_b, neg_c, neg_d, ctl_e)

res = {
    "n_sites": len(hits),
    "n_targets_hit": len(groups),
    "n_targets_requested": len(targets),
    "targets_with_zero_writes": ["%#x" % t for t in targets if written[t] == 0],
    "n_sites_per_target": {"%#x" % t: written[t] for t in targets},
    "by_target": {"%#x" % a: sorted(v, key=lambda x: x["site_rva"]) for a, v in sorted(groups.items())},
    "sites": [{"site_rva": s, "site_va": IB + s, "target_va": a, "value_va": v,
               "value_rva": v - IB} for s, a, v in hits],
    "self_test": {"positive_synthetic_c705": pos_a, "negative_modrm_45_disp8": neg_b,
                  "negative_non_target_addr": neg_c, "negative_truncated_tail": neg_d,
                  "control_reread_from_buffer": ctl_e},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
print("c7 05 sites=%d hitting %d/%d targets; zero-write targets=%s"
      % (len(hits), len(groups), len(targets), res["targets_with_zero_writes"]))
print("per-target site counts:", res["n_sites_per_target"])
print("self_test:", res["self_test"])
