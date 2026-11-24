"""
W160 Q1 channel A: full-section byte-level census of call/indirect-call forms.

Discipline:
 - pefile section walking; .text read raw from disk (no atlas entry+size used).
 - raw signature scan for FF /2 (call r/m32) with modrm mod=01/10 and disp byte 5C,
   including SIB (modrm=0x54/0x94), plus FF /2 mod=00 with SIB base and 32-bit disp.
 - capstone with skipdata=True from known function entries linearly, and whole-section
   linear sweep, used to verify instruction boundaries and produce decoded-site census.
 - outputs JSON with all hits, boundary verdicts, mnemonic/operand text.
"""
import json, os, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_REG, X86_OP_MEM, X86_INS_CALL, X86_REG_ESP

ROOT = r"D:\Project\ra2-campaign-forge"
BIN = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OUT = os.path.join(ROOT, "lead", "next_re_20261116_r12", "W160_aidispatch", "EVIDENCE")
os.makedirs(OUT, exist_ok=True)
IMAGE_BASE = 0x400000

pe = pefile.PE(BIN, fast_load=True)
sections = []
for s in pe.sections:
    name = s.Name.rstrip(b"\0").decode("ascii", "replace")
    sections.append({
        "name": name,
        "va": IMAGE_BASE + s.VirtualAddress,
        "vsize": s.Misc_VirtualSize,
        "raw": s.PointerToRawData,
        "rawsize": s.SizeOfRawData,
        "chars": s.Characteristics,
    })
text = next(s for s in sections if s["name"] == ".text")
data = open(BIN, "rb").read()
blob = data[text["raw"]:text["raw"] + text["rawsize"]]
tva = text["va"]

def off(va):
    return va - tva

# ---- atlas entries: only used for verification helpers, not for the byte census ----
atlas = {}
with open(os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv"), encoding="utf-8") as f:
    next(f)
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 2:
            atlas[int(p[0], 16)] = int(p[1])  # size is DECIMAL per R11 common 3.2

# ---- raw FF /2 scan: mod=01/10, rm=100(SIB) or reg, disp8/32 == 0x5C ----
raw_hits = []
for i, b in enumerate(blob[:-2]):
    if b != 0xFF:
        continue
    modrm = blob[i+1]
    if (modrm & 0x38) != 0x10:  # /2 = call r/m32
        continue
    mod = modrm >> 6
    rm = modrm & 7
    if mod not in (1, 2):
        continue
    if rm == 4:  # SIB
        if i + 3 >= len(blob):
            continue
        sib = blob[i+2]
        if mod == 1:
            disp = blob[i+3]
            if disp != 0x5C:
                continue
            n = 4
        else:
            if i + 6 >= len(blob):
                continue
            disp = struct.unpack_from("<I", blob, i+3)[0]
            if disp != 0x5C:
                continue
            n = 7
        rec = {"va": hex(tva+i), "bytes": blob[i:i+n].hex(), "form": "SIB", "modrm": hex(modrm), "sib": hex(sib), "disp": "0x5C"}
    else:
        if mod == 1:
            if blob[i+2] != 0x5C:
                continue
            n = 3
        else:
            if i + 6 >= len(blob):
                continue
            if struct.unpack_from("<I", blob, i+2)[0] != 0x5C:
                continue
            n = 7
        rec = {"va": hex(tva+i), "bytes": blob[i:i+n].hex(), "form": "REG", "modrm": hex(modrm), "reg": rm, "disp": "0x5C"}
    raw_hits.append(rec)

# also: FF /2 mod=00 SIB with disp32 0x5C (no-base absolute-index form)
for i, b in enumerate(blob[:-7]):
    if b != 0xFF or blob[i+1] != 0x14 or struct.unpack_from("<I", blob, i+3)[0] != 0x5C:
        continue
    raw_hits.append({"va": hex(tva+i), "bytes": blob[i:i+7].hex(), "form": "SIB_NOBASE", "modrm": "0x14", "sib": hex(blob[i+2]), "disp": "0x5C"})

# ---- capstone decode from function entries (linear per entry), skipdata=True ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

insn_start = set()
entry_decoded = {}
for entry in sorted(atlas):
    if not (tva <= entry < tva + text["rawsize"]):
        continue
    size = atlas[entry]
    start = off(entry)
    end = min(start + size, len(blob))
    seq = []
    cursor = start
    for ins in md.disasm(blob[start:end], entry):
        insn_start.add(ins.address)
        seq.append((ins.address, ins.mnemonic, ins.op_str, ins))
    entry_decoded[hex(entry)] = seq

# ---- capstone whole-section linear sweep, skipdata=True (non-atlas channel) ----
whole_seq = []
whole_starts = set()
for ins in md.disasm(blob, tva):
    whole_starts.add(ins.address)
    whole_seq.append((ins.address, ins.mnemonic, ins.op_str, ins))

# persist a compact disassembly listing for cross-checks (no capstone object)
with open(os.path.join(OUT, "W160_whole_text_disasm.tsv"), "w", encoding="utf-8") as f:
    for a, mn, ops, ins in whole_seq:
        f.write(f"{a:08X}\t{mn}\t{ops}\t{ins.bytes.hex()}\n")

# ---- boundary-validated call-site census from whole-section linear sweep ----
# Record detail operands so we test the *decoded displacement* (0x5C), not an
# operand-string suffix (capstone prints -0xa4 for disp=0xffffff5c).
call_sites = []
for va, mn, ops, ins in whole_seq:
    if mn != "call" or not ins.operands:
        continue
    op0 = ins.operands[0]
    if op0.type != X86_OP_MEM:
        continue
    if (op0.mem.disp & 0xffffffff) != 0x5C:
        continue
    call_sites.append({"va": hex(va), "text": mn + " " + ops,
                       "base": op0.mem.base, "index": op0.mem.index,
                       "scale": op0.mem.scale, "disp": hex(op0.mem.disp & 0xffffffff)})

# which raw hits are instruction boundaries / which are call sites
for h in raw_hits:
    va = int(h["va"], 16)
    h["is_insn_start_whole"] = va in whole_starts
    h["is_insn_start_entry"] = va in insn_start
    h["is_call_5c_whole"] = any(x["va"] == h["va"] for x in call_sites)

# all call [..+0x5c] from whole sweep, with forms split
form_count = {"REG": 0, "SIB": 0, "SIB_NOBASE": 0, "OTHER": 0}
for cs in call_sites:
    va = int(cs["va"], 16)
    o = off(va)
    op = blob[o]
    modrm = blob[o+1]
    if op != 0xFF or (modrm & 0x38) != 0x10:
        form_count["OTHER"] += 1
        cs["form"] = "OTHER"
    elif (modrm & 7) == 4:
        form_count["SIB"] += 1
        cs["form"] = "SIB"
    else:
        form_count["REG"] += 1
        cs["form"] = "REG"

# add-reg-0x5C then call [reg] / call [reg+index*4] dispatch-table patterns
add5c = []
for a, mn, ops, ins in whole_seq:
    if mn == "add" and ("0x5c" in ops.lower()):
        add5c.append({"va": hex(a), "text": mn + " " + ops})
call_bracket = []
for a, mn, ops, ins in whole_seq:
    if mn == "call" and ops.startswith("dword ptr [") and (not ins.operands or (ins.operands[0].mem.disp & 0xffffffff) != 0x5C):
        call_bracket.append({"va": hex(a), "text": mn + " " + ops})

res = {
    "binary": BIN,
    "sha256": __import__("hashlib").sha256(open(BIN, "rb").read()).hexdigest().upper(),
    "sections": sections,
    "text": text,
    "atlas_entry_count": len(atlas),
    "raw_hits_total": len(raw_hits),
    "raw_hits": raw_hits,
    "whole_insn_count": len(whole_seq),
    "entry_insn_count": len(insn_start),
    "call_sites_total": len(call_sites),
    "call_sites": call_sites,
    "call_site_forms": form_count,
    "add_0x5c_instrs": add5c,
    "call_bracket_count": len(call_bracket),
}
with open(os.path.join(OUT, "W160_Q1_channelA.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1)
print(json.dumps({k: res[k] for k in ["raw_hits_total","whole_insn_count","entry_insn_count","call_sites_total","call_site_forms","call_bracket_count"]}, indent=2))
print("non-boundary raw hits:", [h for h in raw_hits if not h["is_insn_start_whole"]])
