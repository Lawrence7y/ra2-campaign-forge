"""C1: count `mov ecx,[0x887368]` in .text and count those with a
call to 0x00724730 within the following 24 bytes.

Independent of any prior script. Scans raw section bytes (file-backed only),
then also byte-greps the whole file to cross-check the raw size arithmetic.
"""
import sys
from base import BUF, IB, TEXT, u32, s32, in_raw, u8

PAT = bytes.fromhex("8B0D68738800")     # mov ecx, dword ptr [0x887368]
CALL_ABS = bytes.fromhex("E8")           # call rel32
CALL_NEAR = bytes.fromhex("FF15")        # call dword ptr [abs]
TARGET = 0x00724730
WINDOW = 24

start = TEXT["va"]
raw_end = start + TEXT["rawsize"]
scan_end = start + TEXT["vsize"]

hits = []
for va in range(start, scan_end - len(PAT) + 1):
    i = va - IB
    if BUF[i:i + len(PAT)] == PAT:
        hits.append(va)

print("=== all mov ecx,[0x887368] hits in .text (vsize range) ===")
print("count =", len(hits))
for v in hits:
    print("  %08X" % v)

# also: everything in the whole image (other sections) for context
print()
print("=== occurrences of the 6-byte pattern outside .text ===")
for va in range(IB, IB + len(BUF) - len(PAT) + 1):
    i = va - IB
    if BUF[i:i + len(PAT)] == PAT:
        if not (start <= va < scan_end):
            print("  %08X (section-raw=%s)" % (va, in_raw(va, 6)))

def calls_to(va_window_start, span):
    """Return list of (offset, kind, resolved_target) for call insns inside
    the byte window, decoding naively for both rel32 and FF15 forms."""
    out = []
    lo = va_window_start
    hi = va_window_start + span
    for va in range(lo, hi):
        i = va - IB
        b = BUF[i]
        if b == 0xE8:
            if i + 5 <= len(BUF):
                disp = s32(va + 1)
                tgt = va + 5 + disp
                out.append((va, "rel32", tgt, disprange(va, tgt)))
        elif b == 0xFF and i + 6 <= len(BUF) and BUF[i + 1] == 0x15:
            tgt = u32(va + 2)
            out.append((va, "abs-FF15", tgt, None))
    return out

def disprange(va, tgt):
    d = tgt - va
    return d

print()
print("=== per-hit analysis, window = next %d bytes (i.e. [va+6, va+6+%d)) ===" % (WINDOW, WINDOW))
qual = []
for v in hits:
    w_start = v + 6
    hits_in = calls_to(w_start, WINDOW)
    match = [h for h in hits_in if h[2] == TARGET]
    print("%08X  window=%08X..%08X" % (v, w_start, w_start + WINDOW))
    if not hits_in:
        print("        no call encodings in window")
    for h in hits_in:
        print("        call at %08X (%s) -> %08X%s" %
              (h[0], h[1], h[2], "   <<< MATCH" if h[2] == TARGET else ""))
    if match:
        qual.append((v, match[0][0]))
    else:
        print("        -> NO call 0x%08X in window" % TARGET)

print()
print("=== qualified (call 0x%08X within %d bytes) ===" % (TARGET, WINDOW))
print("count =", len(qual))
for v, c in qual:
    print("  site=%08X call@%08X delta=%d" % (v, c, c - v))

# Also: strict-capstone confirmation of the window matching (guard against
# false positives where the bytes belong to an immediate operand).
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    print()
    print("=== capstone-verified window calls ===")
    for v, c in qual:
        code = bytes(BUF[v - IB: c - IB + 5])
        insns = list(md.disasm(code, v))
        ok = False
        for ins in insns:
            if ins.address == c and ins.mnemonic == "call" and ins.op_str == hex(TARGET):
                ok = True
        print("  %08X -> capstone confirms call@%08X to target: %s" % (v, c, ok))
        for ins in insns:
            print("      %08X %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
except Exception as e:
    print("capstone check failed:", e)
