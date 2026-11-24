# -*- coding: utf-8 -*-
"""PATCH-D35 step2: independently recompute the alleged 63B int3 cave at VA 0x7DF781.
Read-only on the original exe. No writes outside PATCH_D35.
"""
import pefile

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS= r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
CAVE_VA = 0x7DF781
CAVE_LEN = 63
IMAGEBASE = 0x400000

def main():
    pe = pefile.PE(EXE, fast_load=True)
    data = open(EXE, "rb").read()
    print("ImageBase =", hex(pe.OPTIONAL_HEADER.ImageBase))
    print("FileSize  =", len(data))
    print("=== Section table ===")
    for s in pe.sections:
        name = s.Name.decode("latin1").rstrip("\x00")
        print(f"  {name:8s} VA={s.VirtualAddress:#010x} VSize={s.Misc_VirtualSize:#x} "
              f"RawSize={s.SizeOfRawData:#x} RawPtr={s.PointerToRawData:#x}")

    rva = CAVE_VA - IMAGEBASE
    sec = next((s for s in pe.sections
                if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData)), None)
    if sec is None:
        print("!! VA not in any section"); return
    off = sec.PointerToRawData + (rva - sec.VirtualAddress)
    print(f"=== VA {CAVE_VA:#x} -> RVA {rva:#x} -> section {sec.Name!r} -> file offset {off:#x} ===")

    lo_va, lo_off = CAVE_VA - 0x40, off - 0x40
    ctx = data[lo_off:lo_off+0xC0]
    print(f"=== context dump from VA {lo_va:#x} ===")
    for i in range(0, len(ctx), 16):
        va = lo_va + i
        hx = " ".join(f"{b:02X}" for b in ctx[i:i+16])
        mark = "  <== 0x7DF781" if va <= CAVE_VA < va+16 else ""
        print(f"  {va:#010x}: {hx}{mark}")

    cave = data[off:off+CAVE_LEN]
    ncc = sum(1 for b in cave if b == 0xCC)
    print(f"=== {CAVE_LEN}B @ VA {CAVE_VA:#x}: 0xCC count = {ncc}/{CAVE_LEN} ===")
    print("  bytes:", " ".join(f"{b:02X}" for b in cave))
    if ncc != CAVE_LEN:
        print("  non-CC offsets from cave start:",
              [i for i,b in enumerate(cave) if b != 0xCC])

    a = off
    while a > 0 and data[a-1] == 0xCC:
        a -= 1
    b = off
    while b < len(data) and data[b] == 0xCC:
        b += 1
    va_a = IMAGEBASE + (a - sec.PointerToRawData + sec.VirtualAddress)
    va_b = IMAGEBASE + (b - sec.PointerToRawData + sec.VirtualAddress)
    print(f"=== maximal 0xCC run containing target: file [{a:#x},{b:#x}) len={b-a} "
          f"VA [{va_a:#x},{va_b:#x}) ===")

    print("=== function-interval containment (atlas [entry, entry+size), size decimal) ===")
    containing, near = [], []
    with open(ATLAS) as f:
        f.readline()
        for line in f:
            p = line.split()
            if len(p) < 2: continue
            try:
                e, sz = int(p[0], 16), int(p[1], 10)
            except ValueError:
                continue
            if e <= CAVE_VA < e + sz:
                containing.append((e, sz))
            if abs(e - CAVE_VA) < 0x3000:
                near.append((e, sz))
    print("  containing functions:", [(hex(e), sz) for e,sz in containing]
          or "NONE (cave not inside any known atlas function body)")
    near.sort()
    print(f"  nearby functions within +/-0x3000 ({len(near)}):")
    for e, sz in near:
        end = e + sz
        rel = "CONTAINS" if e <= CAVE_VA < end else ("before" if end <= CAVE_VA else "after")
        print(f"    {e:#010x} +{sz:<5d} -> {end:#x}  [{rel}]")

if __name__ == "__main__":
    main()
