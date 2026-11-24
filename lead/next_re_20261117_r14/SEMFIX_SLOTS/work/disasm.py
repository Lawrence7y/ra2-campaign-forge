"""Reusable disassembler for SEMFIX-SLOTS.

Loads the canonical gamemd.exe (read-only), maps each target VA to a file
offset via pefile, disassembles a window with capstone (skipdata=True), and
trims at a run of int3 (0xCC) padding to approximate the function boundary.

Writes one EVIDENCE/disasm_<entry>.txt per row plus a combined index.
"""
import os
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_INT3

sys.stdout.reconfigure(encoding="utf-8")

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS"
EVDIR = os.path.join(BASE, "EVIDENCE")

WINDOW = 0x600          # max bytes to disassemble from entry
INT3_RUN = 4            # consecutive 0xCC -> likely function end


def load_rows():
    rows = []
    with open(COVERAGE, encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 8 and "槽语义未证" in p[3] and p[4] == "[已证]" and p[1] != "S22":
                rows.append({
                    "entry": p[0], "subsystem": p[1], "name": p[2],
                    "semantics": p[3], "grade": p[4], "evpath": p[5],
                })
    return rows


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True


def va_to_off(va):
    rva = va - IB
    return pe.get_offset_from_rva(rva)


def find_end(data, start_off):
    """Return byte index (into data) where a run of INT3 begins."""
    run = 0
    for i, b in enumerate(data):
        if b == 0xCC:
            run += 1
            if run >= INT3_RUN:
                return max(0, i - (INT3_RUN - 1))
        else:
            run = 0
    return len(data)


def disasm_row(row):
    va = int(row["entry"], 16)
    off = va_to_off(va)
    with open(EXE, "rb") as f:
        f.seek(off)
        data = f.read(WINDOW)
    end = find_end(data, off)
    body = data[:end]
    lines = []
    lines.append(f"entry   = {row['entry']} (VA 0x{va:08X}, file off 0x{off:X})")
    lines.append(f"subsys  = {row['subsystem']}")
    lines.append(f"name    = {row['name']}")
    lines.append(f"oldsem  = {row['semantics']}")
    lines.append(f"imgbase = 0x{IB:08X}   window={WINDOW}B   trimmed_at=0x{end:X}")
    lines.append("; " + "-" * 70)
    n = 0
    for ins in md.disasm(body, va):
        rel = ins.address - va
        lines.append(f"+0x{rel:04X}  0x{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}")
        n += 1
        if n > 400:
            lines.append("; [TRUNC 400 insns]")
            break
    lines.append("; " + "-" * 70)
    lines.append(f"instructions={n}")
    return "\n".join(lines)


def main():
    os.makedirs(EVDIR, exist_ok=True)
    rows = load_rows()
    index = []
    for r in rows:
        txt = disasm_row(r)
        fn = os.path.join(EVDIR, f"disasm_{r['entry']}.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
        # first instruction line after header
        first = ""
        for ln in txt.splitlines():
            if ln.startswith("+0x"):
                first = ln.strip()
                break
        index.append(f"{r['entry']}\t{r['subsystem']}\t{r['name']}\t{first}")
    with open(os.path.join(EVDIR, "INDEX.tsv"), "w", encoding="utf-8") as f:
        f.write("entry\tsubsys\tname\tfirst_insn\n")
        f.write("\n".join(index) + "\n")
    print(f"wrote {len(rows)} disasm files + INDEX.tsv to {EVDIR}")


if __name__ == "__main__":
    main()
