# -*- coding: utf-8 -*-
"""W101 step8: LOCALMD/LOCAL mount sites disasm + loose INI check + install json."""
import json, os, struct, sys
import capstone, pefile

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"
data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def va2off(va):
    for name, vstart, vsz, raw, rsz in secs:
        if vstart <= va < vstart + max(vsz, rsz):
            o = raw + (va - vstart)
            if o < len(data): return o
    return None

strings = {}
for rec in json.load(open(os.path.join(OUTD, "step2_strings.json"), encoding="utf-8")):
    strings.setdefault(rec["va"], rec["s"])
short = {va: s for va, s in strings.items() if 2 <= len(s) <= 64}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
KNOWN_CALLS = {0x4739F0: "CCFileClass::ctor(name)", 0x5B3C20: "MixFileClass::ctor",
               0x4068E0: "DebugPrint stub(ret)", 0x5301A0: "main-mix loader",
               0x65CA80: "RawFileClass::ctor", 0x7C8EF4: "sprintf"}
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

def disasm(start, end, title):
    P("")
    P("=" * 100)
    P(f"## {title}   0x{start:08X} - 0x{end:08X}")
    P("=" * 100)
    off = va2off(start)
    for ins in md.disasm(data[off: off + (end - start)], start):
        ann = []
        for tok in ins.op_str.replace(",", " ").split():
            if tok.startswith("0x"):
                try: v = int(tok, 16)
                except ValueError: continue
                if v in short: ann.append(f'"{short[v]}"')
                elif v in KNOWN_CALLS: ann.append(KNOWN_CALLS[v])
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            if t in KNOWN_CALLS: ann.append("-> " + KNOWN_CALLS[t])
        P(f"0x{ins.address:08X}  {ins.bytes.hex():<18s} {ins.mnemonic} {ins.op_str}"
          + ("   ; " + " ".join(ann) if ann else ""))

disasm(0x5303B0, 0x530420, "main loader: CACHEMD/CACHE/LOCALMD/LOCAL mount sites")

P("")
P("== loose INI files in ra2youli root ==")
for f in sorted(os.listdir(GAME)):
    if f.lower().endswith(".ini"):
        p = os.path.join(GAME, f)
        head = open(p, "rb").read(400)
        txt = head.decode("ascii", "replace")
        first = txt.split("\n", 1)[0][:80]
        P(f"{f:22s} {os.path.getsize(p):>9d} B  first-line: {first!r}")

P("")
P("== loose art/rules candidates check ==")
for pat in ["artmd", "rulesmd", "art.", "rules.", "aimd", "langrule"]:
    hits = [f for f in os.listdir(GAME) if pat in f.lower()]
    P(f"{pat:10s}: {hits if hits else '(none)'}")

P("")
P("== ra2forge_install.json ==")
try:
    j = json.load(open(os.path.join(GAME, "ra2forge_install.json"), encoding="utf-8-sig"))
    P(json.dumps(j, ensure_ascii=False, indent=1)[:3000])
except Exception as e:
    P("read fail:", e)

P("")
P("== loose BATTLEMD.INI vs LOCALMD-submix copy ==")
a = open(os.path.join(GAME, "BATTLEMD.INI"), "rb").read()
P("loose BATTLEMD.INI sha256 =", hashlib.sha256(a).hexdigest(), len(a), "B")

open(os.path.join(OUTD, "step8_mount_loose.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step8_mount_loose.txt"))
