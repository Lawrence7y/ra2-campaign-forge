"""Probe true function boundaries: scan a large window for 4x 0xCC padding."""
import pefile, sys
sys.stdout.reconfigure(encoding="utf-8")
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
BIG = 0x8000
with open(EXE, "rb") as f:
    blob = f.read()
def off(va): return pe.get_offset_from_rva(va - IB)
def endrun(data):
    run = 0
    for i, b in enumerate(data):
        if b == 0xCC:
            run += 1
            if run >= 4:
                return i - 3
        else:
            run = 0
    return None
with open(COVERAGE, encoding="utf-8") as f:
    f.readline()
    rows = [p for p in (l.rstrip("\n").split("\t") for l in f)
            if len(p) == 8 and "槽语义未证" in p[3] and p[4] == "[已证]" and p[1] != "S22"]
for p in rows:
    o = off(int(p[0], 16))
    data = blob[o:o+BIG]
    e = endrun(data)
    print(f"{p[0]} {p[1]:>3}  func_len=0x{e:X}" if e is not None else f"{p[0]} {p[1]:>3}  NO_INT3_WITHIN_0x8000")
