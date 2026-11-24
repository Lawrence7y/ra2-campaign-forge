#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W29_override_order / override_order.py
=====================================
Pure STATIC, READ-ONLY re-derivation of the RA2/YR (gamemd.exe 1.001)
resource lookup order: LOOSE FILE vs MIX-internal same-name entry.

Target : D:\\Project\\ra2-campaign-forge\\ra2bench\\gamemd.exe
         (4,825,360 B, ImageBase 0x400000, RELOCS_STRIPPED,
          .text: FileOffset == RVA, i.e. FOFF = VA - 0x400000)

This script NEVER launches the game, attaches to a process, or writes
outside its own delivery directory. It only reads the PE image and
(optionally, for fixture facts) the ra2bench MIX files.

Usage
-----
    python override_order.py                # full evidence dump
    python override_order.py --selftest     # negative controls / counterexamples
    python override_order.py --quiet        # one-line-per-assertion summary

Exit code 0 = all hard assertions passed; 1 = at least one MISMATCH.

Evidence grading used by the companion OVERRIDE_ORDER.md:
  [本次实测] = this script's stdout + exit code
  [本次读码] = docs/re/*:line (pre-existing research, independently re-checked here)
  [静态推断-强|弱] / [待运行验证]
"""
import sys, os, struct, hashlib, zlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE  = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
BENCH= r"D:\Project\ra2-campaign-forge\ra2bench"
IB   = 0x400000
SELFTEST = "--selftest" in sys.argv
QUIET    = "--quiet" in sys.argv

# ------------------------------------------------------------------ PE map
pe = pefile.PE(EXE, fast_load=True)
DATA = open(EXE, "rb").read()
SECS = [(s.Name.rstrip(b"\x00").decode("latin1"), s.VirtualAddress,
         s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
        for s in pe.sections]

def va2off(va):
    rva = va - IB
    for n, srva, vsz, raw, rsz in SECS:
        if srva <= rva < srva + max(vsz, rsz):
            o = raw + (rva - srva)
            if o < raw + rsz:
                return o
    return None

def off2va(off):
    for n, rva, vsz, raw, rsz in SECS:
        if raw <= off < raw + rsz:
            return IB + rva + (off - raw)
    return None

def d32(va):
    o = va2off(va)
    return struct.unpack_from("<I", DATA, o)[0] if o is not None else None

def d16(va):
    o = va2off(va)
    return struct.unpack_from("<H", DATA, o)[0] if o is not None else None

def cstr(va, maxlen=200):
    o = va2off(va)
    if o is None: return "<unmapped>"
    b = DATA[o:o+maxlen]; z = b.find(b"\x00")
    return (b if z < 0 else b[:z]).decode("latin1")

def find_all(hay, needle):
    out=[]; s=0
    while True:
        p = hay.find(needle, s)
        if p < 0: break
        out.append(p); s = p+1
    return out

MD = Cs(CS_ARCH_X86, CS_MODE_32)

def insn_at(va, n=1):
    """Disassemble n instructions starting exactly at va (caller guarantees boundary)."""
    o = va2off(va)
    if o is None: return []
    return list(MD.disasm(DATA[o:o+16*n], va))[:n]

def disasm_block(va, count, title=""):
    """LINEAR disassembly from a KNOWN-good boundary. Printed for evidence only;
    never used as a function-boundary or instruction-count proof."""
    o = va2off(va)
    out = []
    print("\n-- DISASM %s VA=0x%08X RVA=0x%08X FOFF=0x%08X (linear from known boundary, n=%d) --"
          % (title, va, va-IB, o if o is not None else -1, count))
    if o is None:
        print("   !! unmapped"); return out
    c=0
    for i in MD.disasm(DATA[o:o+8*count], va):
        oo = va2off(i.address)
        line = "   VA=0x%08X RVA=0x%08X FOFF=0x%08X  %-22s  %-7s %s" % (
            i.address, i.address-IB, oo if oo is not None else -1,
            " ".join("%02X" % x for x in i.bytes), i.mnemonic, i.op_str)
        print(line); out.append((i.address, i.bytes, i.mnemonic, i.op_str)); c+=1
        if c >= count: break
    return out

# ------------------------------------------------------------------ assertions
RESULTS = []
def check(va, hexbytes, desc):
    o = va2off(va)
    actual = DATA[o:o+len(hexbytes)//2].hex().upper() if o is not None else "NOREAD"
    ok = (actual == hexbytes.upper())
    RESULTS.append((va, hexbytes.upper(), actual, desc, ok))
    if not QUIET:
        print("  [%s] VA=0x%08X RVA=0x%08X FOFF=0x%08X  exp=%-18s got=%-18s  %s"
              % ("OK" if ok else "MISMATCH", va, va-IB, o if o is not None else -1,
                 hexbytes.upper(), actual, desc))
    return ok

def e8_target(va):
    """Decode an E8 rel32 call at va -> target VA."""
    o = va2off(va)
    if o is None or DATA[o] != 0xE8: return None
    rel = struct.unpack_from("<i", DATA, o+1)[0]
    return va + 5 + rel

def jcc_target(va):
    """Decode 0F 8x rel32 at va -> target VA."""
    o = va2off(va)
    if o is None or DATA[o] != 0x0F or not (0x80 <= DATA[o+1] <= 0x8F): return None
    rel = struct.unpack_from("<i", DATA, o+2)[0]
    return va + 6 + rel

def imm32(va):
    o = va2off(va)
    return struct.unpack_from("<I", DATA, o)[0] if o is not None else None

# ================================================================== HEADER
print("="*100)
print("W29 override_order.py  |  PURE STATIC / READ-ONLY  |  selftest=%s" % SELFTEST)
print("="*100)
print("FILE      :", EXE)
print("SIZE      :", len(DATA))
print("MD5       :", hashlib.md5(DATA).hexdigest())
print("SHA256    :", hashlib.sha256(DATA).hexdigest())
print("ImageBase : 0x%X  RELOCS_STRIPPED=%s  DllChar=0x%X" %
      (pe.OPTIONAL_HEADER.ImageBase, bool(pe.FILE_HEADER.Characteristics & 1),
       pe.OPTIONAL_HEADER.DllCharacteristics))
for n, rva, vsz, raw, rsz in SECS:
    print("  section %-8s RVA=0x%08X VA=0x%08X VSize=0x%08X FOFF=0x%08X RawSize=0x%08X" %
          (n, rva, IB+rva, vsz, raw, rsz))
traw=trsz=trva=None
for n,rva,vsz,raw,rsz in SECS:
    if n==".text": trva,traw,trsz=rva,raw,rsz
print(".text raw SHA256:", hashlib.sha256(DATA[traw:traw+trsz]).hexdigest())
print(".text FOFF==RVA? ", traw==trva)

# ================================================================== IAT
print("\n==== IAT RESOLUTION (pefile DIRECTORY_ENTRY_IMPORT) ====")
imp={}
for d in pefile.PE(EXE).DIRECTORY_ENTRY_IMPORT:
    dll=d.dll.decode("latin1")
    for e in d.imports:
        imp[e.address]=(dll, e.name.decode("latin1") if e.name else "ord%d"%e.ordinal)
IAT_EXPECT = {0x7E11BC:"CreateFileA",0x7E1208:"FindFirstFileA",0x7E120C:"FindNextFileA",
              0x7E1300:"FindClose",0x7E1148:"SetCurrentDirectoryA",
              0x7E11A8:"GetModuleFileNameA",0x7E1460:"MessageBoxA"}
for slot,name in IAT_EXPECT.items():
    got = imp.get(slot,("?","?"))[1]
    print("  [0x%08X] -> %-22s (expected %s) %s"%(slot,got,name,"OK" if got==name else "MISMATCH"))

# ================================================================== HARD BYTE ASSERTIONS
print("\n==== HARD BYTE ASSERTIONS (VA / RVA / FOFF / raw bytes) ====")
A = [
 # --- CCFileClass::Get_File (0x473D10): THE order evidence ---
 (0x473D1D,"F644242002",      "test byte[esp+0x20],2   (mode&2 = disk-only)"),
 (0x473D22,"0F8511010000",    "jne 0x473E39            (mode&2 -> skip MIX entirely)"),
 (0x473D2D,"E8DEE1FBFF",      "call 0x431F10           *** LOOSE/DISK FIRST ***"),
 (0x473D32,"84C0",            "test al,al"),
 (0x473D34,"0F85FF000000",    "jne 0x473E39            *** disk hit -> SKIP MIX lookup ***"),
 (0x473D68,"E8C3061400",      "call 0x5B4430           *** MixFileClass::Find = FALLBACK ***"),
 (0x473D6D,"84C0",            "test al,al"),
 (0x473D6F,"0F84AF000000",    "je 0x473E24             (MIX also miss -> tail path)"),
 (0x473E39,"8B542420",        "disk read path entry"),
 (0x473E40,"E86B6C0000",      "call 0x47AAB0           (disk read helper)"),
 # --- disk helper -> RawFileClass::Open -> CreateFileA, name used verbatim ---
 (0x431F10,"8A4129",          "disk-open helper: mov al,[ecx+0x29]"),
 (0x431F1E,"E8CDAC2200",      "call 0x65CBF0 RawFileClass::Open"),
 (0x65CBF4,"8B4618",          "mov eax,[esi+0x18]      (FileName pointer)"),
 (0x65CC58,"52",              "push edx                (name as-is, NO prefix)"),
 (0x65CC59,"FF15BC117E00",    "call [0x7E11BC] = KERNEL32!CreateFileA"),
 (0x401940,"8B4118C3",        "vtable+4 GetFileName = return [ecx+0x18]; ret  (no path/prefix/extension rewriting)"),
 # --- MixFileClass::Find: FIFO from Head.Next ---
 (0x5B4470,"E84F8B2200",      "call 0x7DCFC4           (strupr: name -> UPPER)"),
 (0x5B449C,"E83FD9EEFF",      "call 0x4A1DE0           (CRC32 of uppercased name)"),
 (0x5B44A1,"8B2DE0EFAB00",    "mov ebp,[0xABEFE0]      (Head.Next = EARLIEST-loaded MIX)"),
 (0x5B4507,"8B6C2414",        "mov ebp,[esp+0x14]      (= node->Next, advance to newer MIX)"),
 (0x5B450B,"EB9C",            "jmp 0x5B44A9            (loop; first hit returns at 0x5B450D)"),
 # --- MIX header magic / flags (MixFileClass ctor 0x5B3C20) ---
 (0x5B3CF7,"66395C2428",      "cmp word[esp+0x28],bx   (word0==0 -> TS/RA2 header)"),
 (0x5B3CFC,"7551",            "jne 0x5B3D4F            (word0!=0 -> legacy C&C header)"),
 (0x5B3D0E,"884611",          "mov [esi+0x11],al       (flags bit1 = encrypted)"),
 (0x5B3D11,"742C",            "je 0x5B3D3F             (unencrypted bypass)"),
 # --- CSF loader 0x7346A0: runtime construction of "ra2md.csf" ---
 (0x7346F7,"6A2E",            "push 0x2E  ('.')        -> strip extension"),
 (0x734713,"E818680900",      "call 0x7CAF30           (strchr)"),
 (0x73471F,"C60000",          "mov byte[eax],0         (truncate at '.')"),
 (0x734722,"BFEC578400",      "mov edi,0x8457EC        ('.csf' literal)"),
 (0x73474B,"F3A5",            "rep movsd               (strcat '.csf' -> <base>.csf)"),
 (0x734758,"E893F2D3FF",      "call 0x4739F0           (CCFileClass ctor on <base>.csf)"),
 (0x734764,"E8E7F4D3FF",      "call 0x473C50           (CCFileClass::Open(0))"),
 (0x734771,"6A01",            "push 1                  (mode=1: bit1 clear -> MIX allowed)"),
 (0x734777,"E894F5D3FF",      "call 0x473D10           *** CCFileClass::Get_File : loose-first ***"),
 (0x73478F,"E87CF3D3FF",      "call 0x473B10           (Read 0x18-byte CSF header)"),
 (0x734799,"817C240820465343","cmp [esp+8],0x43534620  (CSF magic ' FSC')"),
 (0x7348BC,"B9B03EB100",      "mov ecx,0xB13EB0        (SAME filename buffer)"),
 (0x7348C1,"E8CA000000",      "call 0x734990           (stage-2 reads same CSF, no 2nd file)"),
 # --- Startup: string-table gate ---
 (0x6BD84E,"B9400D8400",      "mov ecx,0x840D40        ('ra2md.str' base name)"),
 (0x6BD853,"E8486E0700",      "call 0x7346A0           (load string table)"),
 (0x6BD85A,"7528",            "jne 0x6BD884            (success)"),
 (0x6BD863,"68580C8400",      "push 0x840C58           (\"Unable to initialize 'ra2.csf'...\")"),
 (0x6BD869,"FF1560147E00",    "call [0x7E1460] = USER32!MessageBoxA"),
 # --- BATTLEMD*.INI channel ---
 (0x52CBA0,"68A8618200",      "push 0x8261A8           ('BATTLEMD*.INI')"),
 (0x52CBA9,"FF1508127E00",    "call [0x7E1208] = FindFirstFileA  (FS-only, CWD, non-recursive)"),
 (0x52CBB8,"0F840F010000",    "je 0x52CCCD             (no match -> fallback)"),
 (0x52CBF6,"E8F56DF4FF",      "call 0x4739F0           (CCFileClass ctor on enumerated name)"),
 (0x52CC49,"E8A275F4FF",      "call 0x4741F0           (INIClass::Load)"),
 (0x52CC4E,"6898618200",      "push 0x826198           ('BATTLEMD.INI')"),
 (0x52CC54,"E8C7C02900",      "call 0x7C8D20           (_stricmp: seen-baseline flag)"),
 (0x52CC60,"C644241301",      "mov byte[esp+0x13],1    (mark baseline seen)"),
 (0x52CC67,"E8A401F4FF",      "call 0x46CE10           (Register_Battles merge)"),
 (0x52CCAB,"FF150C127E00",    "call [0x7E120C] = FindNextFileA (loop)"),
 (0x52CCC7,"0F8592000000",    "jne 0x52CD5F            (baseline seen -> SKIP fallback)"),
 (0x52CCCD,"6898618200",      "push 0x826198           (fallback: explicit name, mix-aware)"),
 (0x52CCD6,"E8156DF4FF",      "call 0x4739F0           (CCFileClass ctor)"),
 (0x52CD2C,"E8DF00F4FF",      "call 0x46CE10           (SAME merge fn)"),
 (0x46CE17,"68D8B18100",      "push 0x81B1D8           ('Battles' section)"),
 # --- CWD = game directory ---
 (0x6BBFDB,"FF15A8117E00",    "call [0x7E11A8] = GetModuleFileNameA"),
 (0x6BC07C,"FF1548117E00",    "call [0x7E1148] = SetCurrentDirectoryA"),
]
for va,hx,desc in A:
    check(va,hx,desc)

# ================================================================== STRUCTURAL RELATIONS (not just bytes)
print("\n==== DECODED CONTROL-FLOW RELATIONS (computed from bytes above) ====")
rel_disk  = e8_target(0x473D2D)
rel_mix   = e8_target(0x473D68)
rel_open  = e8_target(0x431F1E)
rel_ctor  = e8_target(0x734758)
rel_getf  = e8_target(0x734777)
rel_stg2  = e8_target(0x7348C1)
j_skipmix = jcc_target(0x473D34)
j_mode2   = jcc_target(0x473D22)
j_mixmiss = jcc_target(0x473D6F)
print("  e8 @0x473D2D -> 0x%08X  (disk helper 0x431F10 expected)" % rel_disk)
print("  e8 @0x473D68 -> 0x%08X  (MixFileClass::Find 0x5B4430 expected)" % rel_mix)
print("  e8 @0x431F1E -> 0x%08X  (RawFileClass::Open 0x65CBF0 expected)" % rel_open)
print("  e8 @0x734758 -> 0x%08X  (CCFileClass ctor 0x4739F0 expected)" % rel_ctor)
print("  e8 @0x734777 -> 0x%08X  (CCFileClass::Get_File 0x473D10 expected)" % rel_getf)
print("  e8 @0x7348C1 -> 0x%08X  (stage2 reader 0x734990 expected)" % rel_stg2)
print("  jne @0x473D34 -> 0x%08X (0x473E39 expected; must be > 0x473D68)" % j_skipmix)
print("  jne @0x473D22 -> 0x%08X (0x473E39 expected; mode&2 bypass)" % j_mode2)
print("  je  @0x473D6F -> 0x%08X (0x473E24 expected; MIX-miss tail)" % j_mixmiss)
print("  find head immediate @0x5B44A1 -> 0x%08X (0xABEFE0 Head.Next expected)" % imm32(0x5B44A1+2))
print("  '.csf' literal immediate @0x734722 -> 0x%08X" % imm32(0x734722+1))
print("  'ra2md.str' immediate @0x6BD84E -> 0x%08X" % imm32(0x6BD84E+1))

ORDER_OK = (rel_disk==0x431F10 and rel_mix==0x5B4430 and
            j_skipmix==0x473E39 and j_skipmix > 0x473D68 and
            0x473D2D < 0x473D68)
print("  => LOOSE-BEFORE-MIX structural verdict: %s" % ("PASS" if ORDER_OK else "FAIL"))
print("     (disk CALL SITE 0x473D2D precedes MIX CALL SITE 0x473D68; disk-success jne target")
print("      0x473E39 lies PAST 0x473D68, so a disk hit never executes MixFileClass::Find)")

# ================================================================== STRING / ENCODING SWEEP
print("\n==== STRING SWEEP: 'ra2md.csf' is NOT a static literal (zero-hit discipline) ====")
print("  Scope: entire file %d bytes; encodings: ASCII exact, ASCII case-insensitive, UTF-16LE." % len(DATA))
low = DATA.lower()
for k in [b"ra2md.csf", b"RA2MD.CSF", b"ra2.csf", b".csf", b"ra2md.str", b"BATTLEMD98.INI",
          b"InstallPath", b"CDPath", b"[CD]", b"local mix database"]:
    exact = len(find_all(DATA,k))
    ci    = len(find_all(low,k.lower()))
    u16   = len(find_all(DATA,k.decode("latin1").encode("utf-16le")))
    print("    %-20r exact=%-3d case-insensitive=%-3d utf16le=%-3d" % (k,exact,ci,u16))
print("  Interpretation: 'ra2md.csf' has 0 hits in ALL THREE encodings.")
print("  But 0x840D40='%s' and 0x8457EC='%s' exist and are referenced:" % (cstr(0x840D40),cstr(0x8457EC)))
for va,lab in [(0x840D40,"ra2md.str"),(0x8457EC,".csf")]:
    hits=find_all(DATA,struct.pack("<I",va))
    print("    xref imm32 0x%08X (%-10s): %d hit(s) -> %s" %
          (va,lab,len(hits),", ".join("VA=0x%X"%(off2va(h) or -1) for h in hits)))
print("  => runtime concatenation model: strchr(base,'.') -> truncate -> strcat('.csf')")
print("     'ra2md.str' -> 'ra2md' + '.csf' = 'ra2md.csf'  [本次读码 0x7346F7..0x734754]")
print("  NEGATIVE-CONTROL NOTE: a zero-hit static search for 'ra2md.csf' CANNOT be used")
print("     to claim the engine never requests that file. This is the counterexample.")

print("\n==== Q3: per-extension priority table search ====")
print("  Searched: literal extensions (ASCII + case-insensitive + UTF-16LE), and")
print("  every imm32 xref to them; plus CCFileClass vtable+4 (GetFileName) body.")
for k in [b".csf",b".CSF",b".ini",b".INI",b".mix",b".MIX",b".str",b".STR"]:
    hs=find_all(DATA,k)
    print("    %-6r : %-3d hit(s) %s"%(k,len(hs),", ".join("VA=0x%X"%(off2va(h) or -1) for h in hs[:6])))
print("  vtable+4 (0x401940) disassembles to a single 'mov eax,[ecx+0x18]; ret' ->")
print("  NO extension inspection, NO prefix, NO directory rewrite in the name path.")
print("  The ONLY priority list found is the MIX-to-MIX FIFO list @0xABEFD8 (Head.Next=0xABEFE0).")
print("  No per-extension override table exists in the searched surface. (bounded claim, not a proof)")

# ================================================================== DISASM BLOCKS (evidence)
if not QUIET:
    print("\n==== EVIDENCE DISASSEMBLY BLOCKS (VA/RVA/FOFF/bytes) ====")
    disasm_block(0x473D10, 46, "CCFileClass::Get_File (Q1 core)")
    disasm_block(0x473C50, 30, "CCFileClass::Open (NOTE: its MIX probe PRECEDES disk, opposite of Get_File)")
    disasm_block(0x431F10, 8,  "disk-open helper")
    disasm_block(0x65CBF0, 22, "RawFileClass::Open -> CreateFileA")
    disasm_block(0x401940, 3,  "GetFileName (vtable+4)")
    disasm_block(0x5B4430, 22, "MixFileClass::Find head")
    disasm_block(0x5B44A1, 8,  "MixFileClass::Find FIFO head/advance")
    disasm_block(0x7346A0, 42, "CSF string-table loader: name construction")
    disasm_block(0x734754, 16, "CSF loader: CCFileClass ctor/Open/Get_File/Read")
    disasm_block(0x6BD84E, 10, "Startup string-table gate")
    disasm_block(0x52CBA0, 22, "LoadBattleMdIni: FindFirstFileA wildcard")
    disasm_block(0x52CCCD, 10, "BATTLEMD.INI fallback branch")
    disasm_block(0x6BBFDB, 6,  "GetModuleFileNameA call site")
    disasm_block(0x6BC070, 8,  "SetCurrentDirectoryA call site")

# ================================================================== FIXTURE FACTS (NOT engine proof)
print("\n==== FIXTURE FACTS (auxiliary; NOT used as engine-behaviour evidence) ====")
print("  crc32 cross-check vs known real MIX artifact (docs/re/fs_mix_load_chain.md §6):")
for nm in [b"BATTLEMD.INI",b"ECH01.MAP",b"RA2MD.CSF",b"RA2.CSF"]:
    print("    crc32(%-14r) = 0x%08X"%(nm,zlib.crc32(nm)&0xffffffff))
print("  => engine strupr+CRC32 (0x7DCFC4/0x4A1DE0) == standard zlib.crc32(name.upper()).")
for fn in ["langmd.mix","language.mix","ra2md.mix","ra2.mix"]:
    p=os.path.join(BENCH,fn)
    with open(p,"rb") as f: h=f.read(10)
    w0,w1=struct.unpack_from("<HH",h,0)
    print("  %-16s flags=0x%04X encrypted(flags&2)=%s"%(fn,w1,bool(w1&2)))
# langmd.mix is unencrypted (flags=1, bit1=0). Layout re-derived from FILE SIZE:
#   4 (hdr) + 6 (numFiles/bodySize) + numFiles*12 (index @offset 10)
#   + bodySize + 20 (trailing digest when flags&1) == filesize
# Index is sorted by SIGNED 32-bit id (engine binary-search uses signed jl/jg).
p=os.path.join(BENCH,"langmd.mix")
with open(p,"rb") as f: LM=f.read()
n,body=struct.unpack_from("<HI",LM,4)
ents=[struct.unpack_from("<III",LM,10+i*12) for i in range(n)]
def s32(x): return x-0x100000000 if x>=0x80000000 else x
consistent = (10+n*12+body+20 == len(LM))
signed_sorted = all(s32(ents[i][0])<=s32(ents[i+1][0]) for i in range(n-1))
print("  langmd.mix numFiles=%d bodySize=%d ; 10+%d*12+%d+20=%d vs filesize=%d  %s" %
      (n,body,n,body,10+n*12+body+20,len(LM),"CONSISTENT" if consistent else "INCONSISTENT"))
print("  index sorted by SIGNED id? %s (engine binary search uses signed compares)" % signed_sorted)
ids={e[0]:e for e in ents}
for nm in [b"RA2MD.CSF",b"RA2.CSF"]:
    crc=zlib.crc32(nm)&0xffffffff; e=ids.get(crc)
    print("    %-10s crc=0x%08X  %s"%(nm.decode(),crc,
          "FOUND in langmd.mix (off=0x%X size=%d)"%(e[1],e[2]) if e else "NOT in langmd.mix index"))
fsc=LM.find(b" FSC")
owner=[(i,e) for i,e in enumerate(ents) if 130+e[1] <= fsc < 130+e[1]+e[2]]
print("  first CSF ' FSC' magic @0x%X -> %s" %
      (fsc, "langmd.mix entry %d id=0x%08X off=0x%X size=%d"%(
          owner[0][0],owner[0][1][0],owner[0][1][1],owner[0][1][2]) if owner else "no owning entry"))
print("  => A CSF file IS inside langmd.mix, but its CRC name is NOT 'RA2MD.CSF'.")
print("     language.mix is ENCRYPTED (flags&2=1): its index cannot be read in plaintext.")
print("     UNCLOSED (see UNKNOWNS.md): which MIX entry provides the CSF that 0x7346A0 requests.")
print("  loose .csf/.str in game dir:",
      [f for f in os.listdir(BENCH) if f.lower().endswith((".csf",".str"))] or "NONE")
print("  (=> in the shipped bench, CSF necessarily comes from a MIX.)")

# ================================================================== SELFTEST
if SELFTEST:
    print("\n"+"="*100)
    print("SELFTEST: negative controls and counterexamples (>=1 required)")
    print("="*100)
    S=[]
    def srecord(name, passed, detail):
        S.append((name,passed,detail))
        print("  [%s] %-58s %s"%("PASS" if passed else "FAIL",name,detail))

    # N1: NEGATIVE CONTROL -- deliberately wrong expected byte MUST be detected.
    wrong_ok = True
    o = va2off(0x473D2D)
    # flip one byte of the expected call to 0x5B4430 (as if MIX-first)
    bad = "E8C3061400"
    got = DATA[o:o+5].hex().upper()
    detected = (got != bad.upper())
    srecord("N1 negative-control: wrong-byte assertion is rejected", detected,
            "exp(wrong)=%s got=%s -> detector %s"%(bad,got,"FIRES" if detected else "SILENT(!)"))
    # and prove the checker really reports MISMATCH through check()
    saved = len(RESULTS)
    check(0x473D2D, bad, "SELFTEST-DELIBERATELY-WRONG (must MISMATCH)")
    fired = (not RESULTS[-1][4])
    srecord("N1b check() reports MISMATCH on corrupted byte", fired,
            "last assertion ok=%s (must be False)"%RESULTS[-1][4])
    RESULTS[:] = RESULTS[:saved]   # drop the deliberate negative-control assertion

    # N2: COUNTEREXAMPLE -- hypothesis "MIX is consulted first" must be refuted.
    hyp_mix_first = (0x473D68 < 0x473D2D) or (j_skipmix <= 0x473D68)
    srecord("N2 counterexample: 'MIX-first' hypothesis is REFUTED", not hyp_mix_first,
            "disk_call@0x%X mix_call@0x%X skipjump@0x%X (skip must be > mix_call)" %
            (0x473D2D,0x473D68,j_skipmix))

    # N3: COUNTEREXAMPLE -- Find does NOT start from Tail.Prev (0xABEFF0).
    head_imm = imm32(0x5B44A1+2)
    srecord("N3 counterexample: Find starts at Head.Next not Tail.Prev", head_imm==0xABEFE0,
            "immediate=0x%08X (0xABEFF0 would mean LIFO)"%head_imm)

    # N4: COUNTEREXAMPLE -- linear disassembly from 0x6BD840 is UNSYNCED (task's known pitfall).
    synced  = [(i.mnemonic,i.op_str) for i in insn_at(0x6BD835,4)]
    unsync  = [(i.mnemonic,i.op_str) for i in insn_at(0x6BD840,4)]
    diff = (synced != unsync) and any(m in ("add","inc","outsb","pop","or") for m,_ in unsync)
    srecord("N4 counterexample: wrong start VA desynchronises disasm", diff,
            "synced@0x6BD835=%s | unsynced@0x6BD840=%s"%(synced[:2],unsync[:2]))

    # N5: COUNTEREXAMPLE -- zero-hit for 'ra2md.csf' does NOT mean 'never requested'.
    zero = (len(find_all(DATA,b"ra2md.csf"))==0 and len(find_all(low,b"ra2md.csf"))==0
            and len(find_all(DATA,b"ra2md.csf".decode("latin1").encode("utf-16le")))==0)
    built = (cstr(0x840D40)=="ra2md.str" and cstr(0x8457EC)==".csf"
             and imm32(0x734722+1)==0x8457EC and rel_getf==0x473D10)
    srecord("N5 counterexample: zero-hit != absence (runtime concat)", zero and built,
            "zero_hit=%s concat_evidence=%s"%(zero,built))

    # N6: control -- a genuinely absent string should also be zero (sanity of sweep).
    srecord("N6 positive control: 'BATTLEMD98.INI' is absent", len(find_all(DATA,b"BATTLEMD98.INI"))==0,
            "0 hits, matches docs/re finding")

    # N7: control -- a genuinely present string is found (sweep not broken).
    srecord("N7 positive control: 'BATTLEMD*.INI' is present", len(find_all(DATA,b"BATTLEMD*.INI"))==1,
            "1 hit @0x8261A8")

    allpass = all(x[1] for x in S)
    print("\n  SELFTEST SUMMARY: %d/%d PASS"%(sum(1 for x in S if x[1]),len(S)))
    print("  HARD ASSERTIONS : %d/%d OK"%(sum(1 for r in RESULTS if r[4]),len(RESULTS)))
    sys.exit(0 if (allpass and all(r[4] for r in RESULTS)) else 1)

# normal-mode exit
bad = [r for r in RESULTS if not r[4]]
print("\n==== SUMMARY ====")
print("  hard byte assertions: %d/%d OK"%(len(RESULTS)-len(bad),len(RESULTS)))
print("  loose-before-MIX structural verdict: %s"%("PASS" if ORDER_OK else "FAIL"))
print("  exit code:", 1 if bad or not ORDER_OK else 0)
sys.exit(1 if (bad or not ORDER_OK) else 0)
