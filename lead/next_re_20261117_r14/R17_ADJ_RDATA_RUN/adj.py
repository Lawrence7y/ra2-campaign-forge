#!/usr/bin/env python3
# R17-ADJ-RDATA-RUN / adj.py  -- read-only, PE-section-table measured.
# Question: maximal contiguous run of 4-byte LE slots in .rdata whose value lies in .text,
# containing BOTH 0x7E3FE0 and 0x7E4068.
import struct, sys, os

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = os.path.dirname(os.path.abspath(__file__))
A, B = 0x7E3FE0, 0x7E4068

data = open(EXE, "rb").read()          # read-only open, no process, no debugger

# ---- PE section table (measured, not copied) ----
pe = struct.unpack_from("<I", data, 0x3C)[0]
assert struct.unpack_from("<I", data, pe)[0] == 0x00004550, "not PE"
nsec, = struct.unpack_from("<H", data, pe + 6)
optsz, = struct.unpack_from("<H", data, pe + 20)
opt = pe + 24
magic, = struct.unpack_from("<H", data, opt)
imagebase = struct.unpack_from("<Q", data, opt + 24)[0] if magic == 0x20b else struct.unpack_from("<I", data, opt + 28)[0]
secs = {}
for i in range(nsec):
    o = opt + optsz + 40 * i
    name = data[o:o+8].rstrip(b"\0").decode("latin1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    chars, = struct.unpack_from("<I", data, o + 36)
    secs[name] = dict(vsize=vsize, vaddr=vaddr, rawsize=rawsize, rawptr=rawptr, chars=chars,
                      va=imagebase + vaddr, va_virt_end=imagebase + vaddr + vsize,
                      va_raw_end=imagebase + vaddr + rawsize)

T = secs[".text"]; R = secs[".rdata"]
assert T["chars"] & 0x20000000, ".text not executable"

def rd(va):                             # 4-byte LE read, RVA==file offset for both sections here
    return struct.unpack_from("<I", data, va - imagebase)[0]

# two hi conventions
LO = T["va"]
HIS = [("hi=section virtual end", T["va_virt_end"]),
       ("hi=0x7E1000 (raw/rounded end)", T["va_raw_end"])]

res = {}
for label, hi in HIS:
    def in_text(v): return LO <= v < hi
    runs, s = [], None
    for va in range(R["va"], R["va_virt_end"] - 3, 4):
        if in_text(rd(va)):
            if s is None: s = va
        else:
            if s is not None: runs.append((s, va - 4)); s = None
    if s is not None: runs.append((s, R["va_virt_end"] - 4))
    tgt = [r for r in runs if r[0] <= A and B <= r[1]]
    res[label] = (hi, runs, tgt)
    print(f"[{label}] .text=[0x{LO:X},0x{hi:X})  runs={len(runs)}  target="
          + (f"[0x{tgt[0][0]:X},0x{tgt[0][1]:X}] slots={(tgt[0][1]-tgt[0][0])//4+1}" if tgt else "NONE"))

if len(sys.argv) > 1 and sys.argv[1] == "--write":
    label, hi = HIS[0]
    hi_virt = 0x7E038D
    hi = T["va_virt_end"]
    S, E = res[HIS[0][0]][2][0]
    rows = ["idx\tva\tvalue\tin_text_hi%X\tin_text_hi%X\ttarget" % (T["va_virt_end"], T["va_raw_end"])]
    for i, va in enumerate(range(S, E + 1, 4)):
        v = rd(va); t = {A: "0x7E3FE0", B: "0x7E4068"}.get(va, "")
        rows.append(f"{i}\t0x{va:08X}\t0x{v:08X}\t{int(LO<=v<T['va_virt_end'])}\t{int(LO<=v<T['va_raw_end'])}\t{t}")
    open(os.path.join(OUT, "run.tsv"), "w", newline="\n").write("\n".join(rows) + "\n")
    nv = ["va\tvalue\tside\tverdict"]
    for va in range(0x7E3E98, 0x7E3EBC, 4):
        v = rd(va); nv.append(f"0x{va:08X}\t0x{v:08X}\tleft\t{'in .text' if LO<=v<hi else 'not in .text'}")
    for va in range(0x7E43C4, 0x7E4408, 4):
        v = rd(va); nv.append(f"0x{va:08X}\t0x{v:08X}\tright\t{'in .text' if LO<=v<hi else ('zero' if v==0 else 'not in .text')}")
    open(os.path.join(OUT, "neighbors.tsv"), "w", newline="\n").write("\n".join(nv) + "\n")
    print("wrote run.tsv / neighbors.tsv")
