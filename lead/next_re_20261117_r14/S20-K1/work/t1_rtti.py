"""T1: Build RTTI class-name + vtable table strictly from .rdata.

RTTI chain (x86/MSVC), fail-closed:
  COL+0x0 = signature (0), COL+0x4 = offset, COL+0x8 = cdOffset,
  COL+0xC = pTypeDescriptor (TD), COL+0x10 = pClassDescriptor (CHD).
  TD+0x0 = pVFTable, TD+0x4 = spare, TD+0x8 = mangled name (NUL term).
  vtable[-1] = COL  (the dword 4 bytes before first slot).

NEVER read COL[+8] as TD (that is cdOffset -> TD=0 / name='?' trap, ledger §965).
Slot count = contiguous dwords from vtable start that point into .text;
NO atlas filtering (ledger §960: TClassFactory slot4 missing from 77/77 tables).
"""
import struct
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, EVID, write_text, write_tsv, IMAGE_BASE

b = Bin()
RLO, RHI = b.sec_range(".rdata")
TLO, THI = b.sec_range(".text")
DLO, DHI = b.sec_range(".data")
rdata = b.section_bytes(".rdata")
data = b.section_bytes(".data")

# --- Step 1: find TypeDescriptors by mangled-name signature at TD+8 ---
# Names are in .data on this binary (e.g. TD 0x8177C8 -> name 0x8177D0).
TD = {}  # td_va -> name
i = 0
n = len(data)
while i < n:
    j = data.find(b".?A", i)
    if j < 0:
        break
    i = j + 1
    tail = data[j:j+96]
    if len(tail) < 12:
        continue
    z = tail.find(b"\x00")
    if z < 6:
        continue
    name = tail[:z]
    if not (name.startswith(b".?AV") or name.startswith(b".?AU")
            or name.startswith(b".?AW4")):
        continue
    td_va = DLO + j - 8
    if td_va < DLO or td_va + 8 > DHI:
        continue
    pvf = b.u32(td_va)
    spare = b.u32(td_va + 4)
    if not (0x400000 <= pvf < 0x900000):
        continue
    try:
        chk = b.read(td_va + 8, len(name))
    except Exception:
        continue
    if chk != name:
        continue
    try:
        sname = name.decode("ascii")
    except Exception:
        continue
    TD[td_va] = sname

# --- Step 2: find COLs (broad, reproduces audited 1214/14044) ---
# COL validity criteria: sig==0, TD in .data, CHD in .rdata.
# Do NOT cap obj_off/cd_off (MouseClass etc. have obj_off=0x5518).
# Do NOT require TD name to match a regex (long template names may exceed scan window).
COL = {}  # col_va -> dict
nr = len(rdata)
for off in range(0, nr - 0x14, 4):
    va = RLO + off
    sig = struct.unpack_from("<I", rdata, off)[0]
    if sig != 0:
        continue
    td = struct.unpack_from("<I", rdata, off + 0xC)[0]
    if not (DLO <= td < DHI):
        continue
    chd = struct.unpack_from("<I", rdata, off + 0x10)[0]
    if not (RLO <= chd < RHI):
        continue
    obj_off = struct.unpack_from("<I", rdata, off + 4)[0]
    cd_off = struct.unpack_from("<I", rdata, off + 8)[0]
    # read name directly from TD+8, fail-closed: must be ASCII .?A name
    try:
        raw = b.read(td + 8, 256)
        z = raw.find(b"\x00")
        sname = raw[:z].decode("ascii") if 0 <= z <= 255 else ""
    except Exception:
        sname = ""
    if not (sname.startswith(".?AV") or sname.startswith(".?AU")
            or sname.startswith(".?AW4")):
        sname = "?"  # fail-closed marker; do NOT infer name
    COL[va] = dict(sig=sig, obj_off=obj_off, cd_off=cd_off,
                   td=td, chd=chd, name=sname, name_ok=(sname != "?"))

# TD table: from COLs (authoritative), plus any standalone TDs found in step 1
for va, info in COL.items():
    TD[info["td"]] = info["name"]

# --- Step 3: find vtables: dword in .rdata whose value is a COL address ---
# vt[-1] at loc => vt = loc+4
COLADDR = set(COL.keys())
vt_starts = []  # (vt_va, col_va, loc)
for off in range(0, nr - 4, 4):
    va = RLO + off
    val = struct.unpack_from("<I", rdata, off)[0]
    if val in COLADDR:
        vt_starts.append((va + 4, val, va))

# also collect all COL-pointer locations sorted, for boundary cross-check
col_ptr_locs = sorted(v[2] for v in vt_starts)

# --- Step 4: slot count = contiguous .text pointers from vt ---
def slot_count(vt):
    cnt = 0
    a = vt
    while True:
        try:
            v = b.u32(a)
        except Exception:
            break
        if TLO <= v < THI:
            cnt += 1
            a += 4
        else:
            break
    return cnt, a  # a = first non-text dword (table end)


rows = []
for vt, col, loc in sorted(vt_starts):
    sc, end = slot_count(vt)
    info = COL[col]
    rows.append([
        "%08X" % vt, "%08X" % col, "%08X" % info["td"], info["name"],
        "0x%X" % info["obj_off"], "0x%X" % info["cd_off"],
        "%08X" % info["chd"], sc, "%08X" % end,
        "%08X" % loc,
    ])

write_tsv("T1_rtti_vtables.tsv",
          "vtable\tCOL\tTD\tname\tobj_off\tcd_off\tCHD\tslots\tend_va\tcol_ptr_loc",
          rows)

# raw dump of all COLs (including those without vtable ref) for audit
colrows = []
for va, info in sorted(COL.items()):
    colrows.append([
        "%08X" % va, "%08X" % info["td"], info["name"],
        "0x%X" % info["obj_off"], "0x%X" % info["cd_off"],
        "%08X" % info["chd"],
        "Y" if any(c == va for _, c, _ in vt_starts) else "N",
    ])
write_tsv("T1_rtti_cols.tsv",
          "COL\tTD\tname\tobj_off\tcd_off\tCHD\thas_vtable", colrows)

# td dump
tdrows = [["%08X" % k, v] for k, v in sorted(TD.items())]
write_tsv("T1_rtti_typedescriptors.tsv", "TD\tname", tdrows)

# summary
summary = []
summary.append("sections:")
for s in b.sections:
    summary.append("  %-8s va=%08X raw=%08X rawsize=%08X" %
                   (s["name"], s["va"], s["raw"], s["rawsize"]))
summary.append("TD count=%d COL count=%d COL-with-vtable=%d vtables=%d" %
               (len(TD), len(COL), len(set(c for _, c, _ in vt_starts)), len(vt_starts)))
summary.append("total slots=%d" % sum(r[7] for r in rows))
# name frequency for Anim/Particle families
keys = [r for r in rows if ("Anim" in r[3] or "Particle" in r[3])]
summary.append("Anim/Particle-named vtables=%d" % len(keys))
for r in keys:
    summary.append("  vt=%s col=%s slots=%d name=%s end=%s" %
                   (r[0], r[1], r[7], r[3], r[8]))
write_text("T1_rtti_summary.txt", "\n".join(summary) + "\n")

print("\n".join(summary[:12]))
print("... Anim/Particle vtables:", len(keys))
for r in keys:
    print("  ", r[0], r[3], "slots=", r[7])
