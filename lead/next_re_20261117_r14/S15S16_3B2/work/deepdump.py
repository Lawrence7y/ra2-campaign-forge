# -*- coding: utf-8 -*-
"""Deep-dump disassembly for the 12 P1P2P3 hits plus their callees."""
import json, os, pefile, csv
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
WORK = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

def norm(e):
    e = e.strip().upper()
    return e[2:] if e.startswith("0X") else e

atlas = {}
with open(ATLAS, encoding="utf-8") as f:
    rdr = csv.reader(f, delimiter="\t"); next(rdr)
    for row in rdr:
        if row and row[0].strip():
            try: atlas[norm(row[0])] = int(row[1])
            except: pass

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sections = [(s.Name.rstrip(b"\x00").decode("latin1"), IB + s.VirtualAddress,
             max(s.Misc_VirtualSize, s.SizeOfRawData), s.get_data()) for s in pe.sections]

def read_va(va, maxlen):
    for nm, va0, sz, data in sections:
        if va0 <= va < va0 + sz:
            off = va - va0
            return data[off:off + maxlen], nm
    return b"", None

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

res = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
hits = [r for r in res if r["p3_count"] > 0]

out = []
def w(s=""):
    out.append(s)

w(f"Total P1P2P3 hits: {len(hits)}")
for r in hits:
    ea = int(r["entry"], 16)
    size = r["atlas_size"] or 512
    code, sec = read_va(ea, size)
    insns = list(md.disasm(code, ea))
    w(f"\n{'='*80}")
    w(f"ENTRY {r['entry']} {r['subsystem']} {r['name']}  size={size} sec={sec}")
    w(f"semantics: {r['semantics']}")
    w(f"{'-'*80}")
    for ins in insns:
        if ins.id == 0:
            w(f"  {ins.address:08X}: .byte {ins.bytes.hex()}  [skipdata]")
            continue
        opstr = f" {ins.op_str}" if ins.op_str else ""
        w(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:<8}{opstr}")

# callees of interest
w(f"\n\n{'#'*80}\n# CALLEES OF INTEREST\n{'#'*80}")
for cal in (0x410320, 0x410380, 0x410000, 0x4101C0):
    size = atlas.get(norm(hex(cal)), 256)
    code, sec = read_va(cal, size)
    insns = list(md.disasm(code, cal))
    w(f"\n--- callee {cal:08X} size={size} sec={sec} ---")
    for ins in insns:
        if ins.id == 0: continue
        opstr = f" {ins.op_str}" if ins.op_str else ""
        w(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:<8}{opstr}")

open(os.path.join(WORK, "deepdump.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote deepdump.txt, lines:", len(out))
