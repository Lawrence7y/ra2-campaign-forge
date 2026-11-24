#!/usr/bin/env python3
"""Exploratory scan: all noinit_t lines in YRpp, with next-line context and JMP_THIS detection."""
import os, re

YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\N_FIX\EVIDENCE\scan_noinit_raw.txt"

files = []
for dp, dn, fn in os.walk(YRPP):
    # skip .git / .mimosa
    dn[:] = [d for d in dn if d not in ('.git','.mimosa')]
    for f in fn:
        if f.lower().endswith(('.h','.hpp','.cpp','.inl')):
            files.append(os.path.join(dp,f))
files.sort()

JMP_RE = re.compile(r'JMP_THIS\s*\(\s*0x([0-9A-Fa-f]+)\s*\)')
lines_out = []
total_noinit_lines = 0
total_jmp_next = 0

for path in files:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
    except Exception as e:
        lines_out.append(f"ERR {path}: {e}")
        continue
    for i, ln in enumerate(lines):
        if 'noinit_t' not in ln:
            continue
        total_noinit_lines += 1
        nxt = lines[i+1] if i+1 < len(lines) else ''
        m = JMP_RE.search(nxt)
        rel = os.path.relpath(path, YRPP)
        if m:
            total_jmp_next += 1
            lines_out.append(f"[JMP-NEXT] {rel}:{i+1}\n    L{i+1}: {ln.strip()}\n    L{i+2}: {nxt.strip()}   ADDR=0x{int(m.group(1),16):08X}")
        else:
            # find whether within next 3 lines there's JMP_THIS
            window = lines[i+1:i+4]
            wjmp = None
            for k,w in enumerate(window):
                mm = JMP_RE.search(w)
                if mm: wjmp=(k+1, int(mm.group(1),16)); break
            tag = f"  (near JMP +{wjmp[0]}=0x{wjmp[1]:08X})" if wjmp else ""
            lines_out.append(f"[no-JMP ] {rel}:{i+1}\n    L{i+1}: {ln.strip()}\n    L{i+2}: {nxt.strip()}{tag}")

header = f"# noinit_t raw scan\ntotal .h/.cpp/.inl files={len(files)}\ntotal noinit_t lines={total_noinit_lines}\nnoinit_t lines with JMP_THIS on immediate next line={total_jmp_next}\n\n"
with open(OUT,'w',encoding='utf-8') as fh:
    fh.write(header + "\n".join(lines_out) + "\n")
print(header)
print("wrote", OUT, "records", len(lines_out))
