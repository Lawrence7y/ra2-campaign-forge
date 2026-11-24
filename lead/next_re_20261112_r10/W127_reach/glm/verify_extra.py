# verify_extra.py -- closing checks for the loads69 audit (read-only exe)
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TSV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W127_reach\glm\loads69.tsv"
BASE = 0x400000
TEXT_START = 0x401000
TEXT_END   = 0x7E038D      # inclusive
DEL = 0x724730
# del-call sites found outside the 64B windows of their load sites (verified by
# extended probes / gap disasm, see loads69_report.txt sections 15 and verify section 1):
#   0x4a8b75 <- load 0x4a8b18, guarded by cmp ecx,ebx / je 0x4a8b9b (ebx unproven)
#   0x640427 <- load 0x6403a8, guarded by xor eax,eax / cmp ecx,eax / je 0x64043d (proven)
PROBE_DEL_EXTRA = {0x4A8B75, 0x640427}

pe  = pefile.PE(EXE, fast_load=True)
img = pe.get_memory_mapped_image()

def rd(va, n):
    off = va - BASE
    return bytes(img[off:off + n])

tb = rd(TEXT_START, TEXT_END - TEXT_START + 1)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True

print("=== 1. gap disasm 0x6403fb..0x640443 (0x6403a8 guard block vs 0x640431 reload) ===")
for ins in md.disasm(rd(0x6403fb, 0x50), 0x6403fb):
    if ins.mnemonic in (".byte", "(bad)"):
        print("  %#x  DATA[%s]" % (ins.address, bytes(ins.bytes).hex(" ")))
        continue
    print("  %#x  %-6s %s" % (ins.address, ins.mnemonic, ins.op_str))

print("")
print("=== 2. TSV integrity + independent byte-level E8->0x724730 check for all A rows ===")
lines = open(TSV, encoding="utf-8").read().rstrip("\n").split("\n")
print("  total lines (incl header): %d (expect 70)" % len(lines))
assert len(lines) == 70, "TSV row count mismatch"
a_ok = 0
a_bad = []
call_addrs = set()
for ln in lines[1:]:
    va_s, cls, hx, ev, ct = ln.split("\t")
    va = int(va_s, 16)
    b = bytes.fromhex(hx)
    if cls != "A":
        continue
    hit = None
    for o in range(6, 44):
        if o + 5 <= len(b) and b[o] == 0xE8:
            rel = struct.unpack("<i", b[o + 1:o + 5])[0]
            tgt = (va + o + 5 + rel) & 0xFFFFFFFF
            if tgt == DEL:
                hit = va + o
                break
    if hit:
        a_ok += 1
        call_addrs.add(hit)
    else:
        a_bad.append(va_s)
print("  A rows byte-verified (raw E8 rel32 recomputed == 0x724730): %d/28 ; failures: %s"
      % (a_ok, a_bad if a_bad else "none"))

print("")
print("=== 3. census: every direct E8 call / E9 jmp to FUN_00724730 in .text ===")
direct = []
i = tb.find(b"\xE8")
while i != -1:
    if i + 5 <= len(tb):
        rel = struct.unpack("<i", tb[i + 1:i + 5])[0]
        if (TEXT_START + i + 5 + rel) & 0xFFFFFFFF == DEL:
            direct.append(TEXT_START + i)
    i = tb.find(b"\xE8", i + 1)
i = tb.find(b"\xE9")
while i != -1:
    if i + 5 <= len(tb):
        rel = struct.unpack("<i", tb[i + 1:i + 5])[0]
        if (TEXT_START + i + 5 + rel) & 0xFFFFFFFF == DEL:
            direct.append(TEXT_START + i)
    i = tb.find(b"\xE9", i + 1)
print("  direct call/jmp sites to 0x724730: %d" % len(direct))
unmatched = [a for a in direct if a not in call_addrs and a not in PROBE_DEL_EXTRA]
print("  accounted by audit (28 A rows + probe-found %s): %d ; UNMATCHED: %d"
      % (sorted(hex(x) for x in PROBE_DEL_EXTRA), len(direct) - len(unmatched), len(unmatched)))
loads_all = sorted(int(ln.split("\t")[0], 16) for ln in lines[1:])
for a in unmatched:
    prev = [v for v in loads_all if v < a]
    near = max(prev) if prev and (a - max(prev)) <= 0x100 else None
    note = ("likely consumes load site %#x at distance %#x (beyond its 64B window)"
            % (near, a - near)) if near else "no 0x887368-load within 0x100 bytes before the call"
    print("    UNMATCHED caller @ %#x ; %s" % (a, note))
    print("      preceding 32B: %s" % rd(a - 32, 32).hex(" "))

print("")
print("=== 4. supplementary backward hunt: guard register provably zeroed upstream? ===")
REG = {"ebx", "esi"}

def hunt(site, reg):
    lo = max(TEXT_START, site - 0x1000)
    starts = []
    j = 0
    while j < site - lo:
        if tb[j] in (0xC3, 0xCC):
            k = j + 1
            while k < site - lo and tb[k] in (0xC3, 0xCC, 0x90):
                k += 1
            if k < site - lo and tb[k] not in (0xC3, 0xCC):
                starts.append(lo + k)
            j = k
        else:
            j += 1
    verdicts = []
    for st in starts[-4:]:
        try:
            code = rd(st, site - st + 16)
        except AssertionError:
            continue
        z = False
        clean = True
        zero_at = None
        for ins in md.disasm(code, st):
            if ins.mnemonic in (".byte", "(bad)") or not ins.mnemonic:
                clean = False
                break
            if ins.address >= site:
                break
            m2, o2 = ins.mnemonic, ins.op_str
            dst = o2.split(",")[0].strip() if o2 else ""
            if m2 == "xor" and dst == reg and o2.replace(" ", "").startswith(reg + ","):
                z = True
                zero_at = ins.address
            elif m2 == "mov" and dst == reg and len(o2.split(",")) > 1 and o2.split(",")[1].strip() == "0":
                z = True
                zero_at = ins.address
            elif dst == reg and m2 not in ("cmp", "test"):
                z = False
                zero_at = None
        if clean:
            verdicts.append((st, z, zero_at))
    return verdicts

SITES = [(0x6a707f, "ebx"), (0x7777f3, "ebx"), (0x68639f, "esi"), (0x48ce4c, "ebx"),
         (0x52daf9, "ebx"), (0x55d0a0, "ebx"), (0x55d159, "ebx"), (0x55d1e7, "ebx"),
         (0x4a8b18, "ebx")]
for site, reg in SITES:
    v = hunt(site, reg)
    if not v:
        print("  %#x  reg=%s : no clean candidate function start found -> inconclusive" % (site, reg))
        continue
    st, z, za = v[-1]
    extra = " ; ".join("%#x(zeroed@%s)" % (s2, ("%#x" % z3) if z3 else "-") for s2, z3, _ in v)
    print("  %#x  reg=%s : linear walk from %#x -> %s (candidates: %s)"
          % (site, reg, st, ("reg==0 on this path (zeroed at %s)" % ("%#x" % za)) if z
             else "reg NOT provably zero on this path", extra))
