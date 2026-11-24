#!/usr/bin/env python3
"""Q3: for each call site into the twin range, determine how edx was set, using ONLY
real instruction boundaries from a forward linear sweep (streaming ring buffer).

Why the rewrite: a first attempt decoded a 16-byte window ending exactly at each
call site. That is unsound -- x86 decoding is self-synchronising, so a window can
end exactly at the site while starting mid-instruction. It produced "mov edx,
0xa83e30" whose value lies outside SizeOfImage (0x796000), which is impossible for
a real .data object address. The ring-buffer pass below cannot make that mistake.

Memory discipline: no instruction list is kept. Only the last 4 decoded
instructions are retained (ring buffer), so peak memory is O(1) in .text size.
"""
import json, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q2 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q2.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q3.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
text = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
TV, TRP, TRS = text.VirtualAddress, text.PointerToRawData, text.SizeOfRawData
SIZE_OF_IMAGE = pe.OPTIONAL_HEADER.SizeOfImage
data = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".data")
DATA_FILE = (data.VirtualAddress, data.VirtualAddress + data.SizeOfRawData)
DATA_ALL = (data.VirtualAddress, data.VirtualAddress + data.Misc_VirtualSize)
with open(EXE, "rb") as f:
    f.seek(TRP); tb = f.read(TRS)

q2 = json.load(open(Q2))
wanted = {s["site_rva"]: s for s in q2["pass2_resync_sweep"]["sites"]}

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

# Mnemonics whose FIRST operand is a true destination (i.e. the register is written).
# Whitelist, not blacklist: `push edx`/`call`/`cmp` etc. name edx as an operand but
# do NOT write it. A blacklist bug made `push edx` look like an edx write.
WRITES_DST = {
    "mov", "movzx", "movsx", "lea", "xor", "add", "sub", "and", "or", "adc", "sbb",
    "imul", "not", "neg", "shl", "shr", "sar", "rol", "ror", "pop", "inc", "dec",
    "xchg", "setne", "sete", "setl", "setg", "seta", "setb",
}

def classify_write(mn, ops):
    """If this instruction writes edx, return (kind, detail)."""
    parts = ops.split(",")
    dst = parts[0].strip()
    if dst != "edx":
        return None
    if mn == "cdq":                      # cdq sign-extends eax into edx
        return ("other", "cdq")
    if mn not in WRITES_DST:
        return None
    if len(parts) == 1:
        return ("other", "%s %s" % (mn, ops))
    src = parts[1].strip()
    if mn == "mov":
        try:
            v = int(src, 0)
            if src.startswith("0x") or src.lstrip("-").isdigit():
                return ("imm32", v)
        except ValueError:
            pass
        if src.startswith("["):
            return ("mem", src)
        return ("reg", src)
    if mn in ("xor", "sub") and src == "edx":
        return ("zero", 0)
    return ("other", "%s %s" % (mn, ops))

RING = []
MAXRING = 6
found = {}

off = 0
while off < len(tb):
    progressed = False
    for a, sz, mn, ops in md.disasm_lite(tb[off:], TV + off):
        progressed = True
        if a in wanted and a not in found:
            # snapshot the ring (predecessor instructions, real boundaries only)
            found[a] = {"preds": list(RING)}
        w = classify_write(mn, ops)
        RING.append({"rva": a, "hex": tb[a - TV:a - TV + sz].hex(),
                     "insn": "%s %s" % (mn, ops), "edx_write": w})
        if len(RING) > MAXRING:
            RING.pop(0)
        nxt = a + sz - TV
        if nxt <= off:
            break
        off = nxt
    if not progressed:
        off += 1
        RING.append({"rva": TV + off, "insn": "<resync +1>", "edx_write": None})

def edx_source(preds):
    for p in reversed(preds):
        if p.get("edx_write"):
            return p
    return None

rows = []
for site_rva, s in sorted(wanted.items()):
    snap = found.get(site_rva)
    preds = snap["preds"] if snap else []
    src = edx_source(preds)
    rows.append({
        "site_rva": site_rva, "site_va": IB + site_rva,
        "target_rva": s["target_rva"], "target_va": IB + s["target_rva"],
        "prev8_hex": tb[site_rva - TV - 8: site_rva - TV].hex(),
        "prev_insns": [{"rva": p["rva"], "hex": p.get("hex"), "insn": p["insn"]} for p in preds[-3:]],
        "edx_source": ({"insn": src["insn"], "hex": src["hex"], "at_rva": src["rva"],
                        "kind": src["edx_write"][0], "imm": src["edx_write"][1]}
                       if src else None),
        "reached_in_sweep": snap is not None,
    })

# ---- what do the imm values look like? ----
# IMPORTANT: the imm32 encodings are ABSOLUTE VAs (ImageBase 0x400000); section
# VirtualAddress fields are RVAs. A raw VA-vs-RVA comparison is an apples/oranges
# bug -- the first version of this script made exactly that mistake and wrongly
# reported "0 in .data". Convert to RVA first.
imms = [r["edx_source"]["imm"] for r in rows if r["edx_source"] and r["edx_source"]["kind"] == "imm32"]
uniq = sorted(set(imms))
in_image = [v for v in uniq if v - IB < SIZE_OF_IMAGE]
out_of_image = [v for v in uniq if v - IB >= SIZE_OF_IMAGE]
in_data_file = [v for v in uniq if DATA_FILE[0] <= v - IB < DATA_FILE[1]]
in_data_bss = [v for v in uniq if DATA_FILE[1] <= v - IB < DATA_ALL[1]]
# sanity: every imm must be a plausible absolute VA, i.e. >= ImageBase
below_base = [v for v in uniq if v < IB]

# ---- twin body identity ----
BODY = 128
ref_t = 0x27FDF0
ref = tb[ref_t - TV: ref_t - TV + BODY]
firstdiff = {}
for t in sorted({r["target_rva"] for r in rows}):
    b = tb[t - TV: t - TV + BODY]
    if b != ref:
        for i, (x, y) in enumerate(zip(b, ref)):
            if x != y:
                firstdiff["%#x" % t] = i
                break
        else:
            firstdiff["%#x" % t] = "len"

# ---- self tests ----
# 1) positive: streaming ring recognises `mov edx,imm32`
R = []
for a, sz, mn, ops in md.disasm_lite(bytes.fromhex("ba78563412"), 0):
    R.append({"rva": a, "insn": "%s %s" % (mn, ops), "edx_write": classify_write(mn, ops)})
pos1 = bool(edx_source(R) and edx_source(R)["edx_write"] == ("imm32", 0x12345678))
# 2) negative: `mov ebx,imm32` must not count as an edx write
R2 = [{"rva": 0, "insn": "mov ebx, 0x12345678",
       "edx_write": classify_write("mov", "ebx, 0x12345678")}]
neg1 = edx_source(R2) is None
# 3) control: mid-instruction window start does NOT fool the ring buffer --
#    the sweep decodes `8b 0d <imm32>` (mov ecx,[abs]) as one insn, and the byte
#    `ba` inside its imm32 is never treated as a mov opcode.
R3 = []
for a, sz, mn, ops in md.disasm_lite(bytes.fromhex("8b0d303ea800"), 0):
    R3.append({"rva": a, "insn": "%s %s" % (mn, ops), "edx_write": classify_write(mn, ops)})
ctl1 = len(R3) == 1 and edx_source(R3) is None
# 4) control: the ring buffer must attribute the write to the nearest preceding writer
R4 = [{"rva": 0, "edx_write": ("imm32", 0x111111)},
      {"rva": 1, "edx_write": ("imm32", 0x222222)}]
ctl2 = edx_source(R4)["edx_write"][1] == 0x222222
# 4b) regression control: `push edx` must NOT count as an edx write (this exact bug
#     made the 0x27e62b site look like a writer of edx in an earlier version).
R5 = [{"rva": 0, "edx_write": classify_write("push", "edx")},
      {"rva": 1, "edx_write": classify_write("mov", "edx, 0x111111")}]
ctl2b = edx_source([{"rva": 0, "edx_write": classify_write("push", "edx")}]) is None and \
        edx_source(R5)["edx_write"][1] == 0x111111
assert ctl2b
# 5) control: VA->RVA conversion must place a known absolute VA in .data BSS and must
#    NOT place it there if we forget the subtract. Guards the RVA/VA bug above.
probe_va = IB + DATA_FILE[1] + 0x100          # a point just inside .data BSS
ctl3 = (DATA_FILE[1] <= probe_va - IB < DATA_ALL[1]) and not (DATA_FILE[1] <= probe_va < DATA_ALL[1])
assert pos1 and neg1 and ctl1 and ctl2 and ctl3, (pos1, neg1, ctl1, ctl2, ctl3)

res = {
    "n_sites": len(rows), "n_targets": len({r["target_rva"] for r in rows}),
    "method": "forward linear sweep, streaming 6-insn ring buffer, capstone detail=False",
    "size_of_image": SIZE_OF_IMAGE,
    "data_file_backed": ["%#x" % DATA_FILE[0], "%#x" % DATA_FILE[1]],
    "data_all": ["%#x" % DATA_ALL[0], "%#x" % DATA_ALL[1]],
    "sites": rows,
    "imm32": {
        "count": len(imms), "distinct": len(uniq),
        "all_distinct": len(imms) == len(uniq),
        "sorted": ["%#x" % v for v in uniq],
        "n_inside_image": len(in_image), "n_outside_image": len(out_of_image),
        "outside_image_values": ["%#x" % v for v in out_of_image],
        "n_in_data_file_backed": len(in_data_file),
        "n_in_data_bss": len(in_data_bss),
        "below_image_base": ["%#x" % v for v in below_base],
        "rva_form": ["%#x" % (v - IB) for v in uniq],
    },
    "twin_body": {"window_bytes": BODY, "ref": "%#x" % ref_t,
                  "n_identical": len({r["target_rva"] for r in rows}) - len(firstdiff),
                  "n_targets": len({r["target_rva"] for r in rows}),
                  "non_identical_first_diff": firstdiff},
    "self_test": {"positive_mov_edx_imm": pos1, "negative_mov_ebx_imm_ignored": neg1,
                  "control_imm_bytes_not_opcodes": ctl1, "control_nearest_writer": ctl2,
                  "control_va_rva_conversion": ctl3},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

kinds = {}
for r in rows:
    k = r["edx_source"]["kind"] if r["edx_source"] else "NONE"
    kinds[k] = kinds.get(k, 0) + 1
print("sites=%d targets=%d" % (len(rows), len({r['target_rva'] for r in rows})))
print("edx kinds:", kinds)
print("imm32: count=%d distinct=%d in_image=%d out_of_image=%d data_file=%d data_bss=%d"
      % (len(imms), len(uniq), len(in_image), len(out_of_image), len(in_data_file), len(in_data_bss)))
print("twin identical: %d/%d  non-identical=%s"
      % (res["twin_body"]["n_identical"], res["twin_body"]["n_targets"], firstdiff))
print("self_test:", res["self_test"])
for r in rows:
    print("%#x -> %#x prev8=%s  %s" % (r["site_rva"], r["target_rva"], r["prev8_hex"],
                                       r["edx_source"] and r["edx_source"]["insn"]))
