# -*- coding: utf-8 -*-
# T5 recon: verify hash/sections, byte-scan call sites, dump the six routines and claim regions.
import hashlib, os, sys
import pefile, capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TARGETS = [0x724730, 0x724580, 0x7241A0, 0x724520, 0x724530, 0x724540]
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

data = open(EXE, "rb").read()
sha = hashlib.sha256(data).hexdigest().upper()
print("SHA256:", sha)
print("HASH MATCH:", sha == EXPECT)
print("file size:", len(data))

pe = pefile.PE(data=data, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
ib = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase: 0x%08X" % ib)
secinfo = {}
order = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode(errors="replace")
    secinfo[name] = (ib + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
    order.append(name)
    print("%s va=0x%08X vsize=0x%06X raw=0x%08X rawsize=0x%06X" % (name, ib + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
    print("exports:")
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        print("   0x%08X %s" % (ib + exp.address, exp.name))

tva, tvs, tro, trs = secinfo[".text"]
tcode = data[tro:tro + min(trs, tvs)]
print(".text decoded bytes: 0x%X (va 0x%08X..0x%08X)" % (len(tcode), tva, tva + len(tcode)))

def off2va(off):
    for nm in order:
        va, vs, ro, rs = secinfo[nm]
        if ro <= off < ro + rs:
            return va + (off - ro)
    return None

# --- linear sweep with skipdata, detail off, collect call/jmp imm targets ---
mdS = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdS.skipdata = True

print("\n=== linear sweep (skipdata) ===")
call_targets = {}
n_ins = 0
for i in mdS.disasm(tcode, tva):
    if i.id == 0:
        continue
    n_ins += 1
    if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x"):
        t = int(i.op_str, 16)
        if tva <= t < tva + len(tcode):
            call_targets.setdefault(t, []).append((i.address, i.mnemonic))
print("instructions decoded:", n_ins)
print("unique in-text call/jmp targets:", len(call_targets))

# --- byte scan for E8/E9 rel32 to each target ---
def scan_rel(opcode):
    res = {}
    opb = bytes([opcode])
    for t in TARGETS:
        sites = []
        idx = 0
        n = len(tcode)
        while True:
            i = tcode.find(opb, idx)
            if i < 0 or i + 5 > n:
                break
            rel = int.from_bytes(tcode[i + 1:i + 5], "little", signed=True)
            site = tva + i
            if site + 5 + rel == t:
                sites.append(site)
            idx = i + 1
        res[t] = sites
    return res

e8 = scan_rel(0xE8)
e9 = scan_rel(0xE9)
print("\n=== byte scan E8 (call rel32) / E9 (jmp rel32) ===")
for t in TARGETS:
    print("target 0x%06X  E8 sites: %2d  %s" % (t, len(e8[t]), " ".join("0x%X" % s for s in e8[t])))
    print("              E9 sites: %2d  %s" % (t, len(e9[t]), " ".join("0x%X" % s for s in e9[t])))

# --- literal 4-byte scans of the whole file (pointer tables / mov imm) ---
print("\n=== literal 4-byte occurrences of targets across whole file ===")
for t in TARGETS:
    tb = t.to_bytes(4, "little")
    idx = 0
    hits = []
    while True:
        i = data.find(tb, idx)
        if i < 0:
            break
        va = off2va(i)
        hits.append((i, va))
        idx = i + 1
    print("target 0x%06X: %d literal hits" % (t, len(hits)))
    for off, va in hits:
        sec = "?"
        for nm in order:
            va0, vs, ro, rs = secinfo[nm]
            if va is not None and va0 <= va < va0 + vs:
                sec = nm
        print("   fileoff=0x%08X va=%s sec=%s" % (off, ("0x%08X" % va) if va else "unmapped", sec))

# --- strict decoder helpers ---
mdX = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def dis_strict(va, nbytes):
    off = va - tva
    b = tcode[off:off + nbytes]
    out = []
    v = va
    idx = 0
    while idx < len(b):
        got = False
        for i in mdX.disasm(b[idx:], v, count=1):
            out.append(i)
            v += i.size
            idx += i.size
            got = True
            break
        if not got:
            break
    return out

def show(va, nbytes, title):
    print("\n--- %s (0x%08X..0x%08X) ---" % (title, va, va + nbytes))
    for i in dis_strict(va, nbytes):
        off = i.address - tva
        print("0x%06X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

for t in TARGETS:
    show(t, 0x150, "routine 0x%06X head" % t)

show(0x6D1720, 0x50, "fall-through claim region 0x6D1744->0x6D1749")
show(0x6F3F40, 0x60, "function 0x6F3F40 head")
show(0x6F4080, 0x40, "site A claimed 0x6F409C")
show(0x6F4100, 0x50, "site B claimed 0x6F4124")
show(0x6F4160, 0x40, "site C claimed 0x6F4173")

print("\nDONE")
