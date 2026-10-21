#!/usr/bin/env python3
"""
addr_probe.py -- instruction-level adjudication of crash VA 0x0084F2BA
                   in ra2youli/gamemd.exe, plus the 0x0054A56E `mov [esi+4],0`.

READ-ONLY. Never modifies the target, never executes it.

Run:  PYTHONDONTWRITEBYTECODE=1 python addr_probe.py [stage]
Stage (omit for pe+bytes):  scan | crash56e | all
  pe       : PE32 header + section table + locate 0x0084F2BA + page protection
  bytes    : 32-byte dump at 0x0084F2BA, decoded as float32 / uint32 + ramp context
  scan     : capstone linear sweep of .text -> imm32 / abs-disp / indexed-store leads
  crash56e : disassembly window around the 0x0054A56E `mov [esi+4],0`
  all      : everything
READ-ONLY: opens the exe with builtins.open('rb'); never writes or runs it.
"""
import struct, sys, re, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PAGE = 0x1000
TARGET = 0x0084F2BA
NEAR_LO, NEAR_HI = 0x0084F200, 0x0084F400

data = open(EXE, "rb").read()
print(f"file size = {len(data):,} B")
print("sha256    =", __import__("hashlib").sha256(data).hexdigest()[:16])

# ---------------------------------------------------------------- PE headers
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew+4] == b"PE\0\0", "bad PE sig"
coff = e_lfanew + 4
machine, nsec, ts, ptr_sym, nsym, sz_opt, chars = struct.unpack_from(
    "<HHIIIHH", data, coff)
print(f"\nPE sig @ 0x{e_lfanew:08X}  machine=0x{machine:04X} "
      f"sections={nsec} characteristics=0x{chars:04X}")

# PE32 (magic 0x10b) optional header. The optional header itself starts at
# coff+20 (4B "PE\0\0" signature is already in `coff`; the IMAGE_FILE_HEADER is
# 20 bytes). Offsets below are relative to `coff` = start of IMAGE_FILE_HEADER.
#   +16 SizeOfOptionalHeader   +18 Characteristics   +20 Magic
#   +24 SizeOfCode  +28 SizeOfInitData  +32 SizeOfUninitData  +36 AddressOfEP
#   +40 BaseOfCode  +44 BaseOfData[PE32]  +48 ImageBase  +52 SectionAlignment
#   +56 FileAlignment  +76 SizeOfImage  +80 SizeOfHeaders  +88 Subsystem
#   +90 DllCharacteristics
sig32  = struct.unpack_from("<H", data, coff+20)[0]
ep     = struct.unpack_from("<I", data, coff+36)[0]
image_base = struct.unpack_from("<I", data, coff+48)[0]
sec_align  = struct.unpack_from("<I", data, coff+52)[0]
file_align = struct.unpack_from("<I", data, coff+56)[0]
size_of_image   = struct.unpack_from("<I", data, coff+76)[0]
size_of_headers = struct.unpack_from("<I", data, coff+80)[0]
subsys    = struct.unpack_from("<H", data, coff+88)[0]
dll_chars = struct.unpack_from("<H", data, coff+90)[0]
print(f"PE32 sig=0x{sig32:04X} image_base=0x{image_base:08X} "
      f"sect_align=0x{sec_align:X} file_align=0x{file_align:X}")
print(f"SizeOfImage=0x{size_of_image:08X}  entry=0x{image_base+ep:08X} "
      f"subsystem={subsys}  DllCharacteristics=0x{dll_chars:04X}")
NX = 0x100  # IMAGE_DLLCHARACTERISTICS_NX_COMPAT
print(f"NX_COMPAT bit (0x0100) {'SET' if dll_chars & NX else 'CLEAR'} "
      "-> {'DEP enforced on data pages' if dll_chars & NX else 'no NX opt-in; under DEP OptIn the whole image (incl. .data) is EXECUTABLE'}")

# IMAGE_SCN_* -- https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
SCN = {0x00000020: "CNT_CODE", 0x00000040: "CNT_INITIALIZED_DATA",
       0x00000080: "CNT_UNINITIALIZED_DATA", 0x00000200: "LNK_INFO",
       0x00001000: "LNK_COMDAT", 0x00008000: "GPREL",
       0x02000000: "MEM_DISCARDABLE", 0x04000000: "MEM_NOT_CACHED",
       0x08000000: "MEM_NOT_PAGED", 0x10000000: "MEM_SHARED",
       0x20000000: "MEM_EXECUTE", 0x40000000: "MEM_READ",
       0x80000000: "MEM_WRITE"}
WRITE_BIT, READ_BIT, EXEC_BIT = 0x80000000, 0x40000000, 0x20000000

def scn_str(sc):
    return "|".join(v for k, v in sorted(SCN.items()) if sc & k) or "(none)"

sec_hdr = coff + 20 + sz_opt
sections = []
for i in range(nsec):
    o = sec_hdr + i*40
    name = data[o:o+8].rstrip(b"\0").decode("latin1")
    # IMAGE_SECTION_HEADER: 8B Name, then u32 VirtualSize, u32 VirtualAddress,
    # u32 SizeOfRawData, u32 PointerToRawData, u32 PointerToRelocations,
    # u16 PointerToLinenumbers, u16 NumberOfRelocations, u16 NumberOfLinenumbers,
    # u32 Characteristics
    vsize, va, rawsize, rawptr, ptr_reloc = struct.unpack_from("<IIIII", data, o+8)
    ptr_ln, nreloc, nln, sc = struct.unpack_from("<IHHI", data, o+28)
    sections.append(dict(name=name, va=va, vsize=vsize, rawsize=rawsize,
                         rawptr=rawptr, chars=sc))
    perm = ("W" if sc & WRITE_BIT else "-") + \
           ("R" if sc & READ_BIT else "-") + \
           ("E" if sc & EXEC_BIT else "-")
    print(f"  [{i}] {name:<8} VA=0x{image_base+va:08X} VS=0x{vsize:08X} "
          f"RS=0x{rawsize:08X} RAW=0x{rawptr:08X} char=0x{sc:08X} "
          f"({scn_str(sc)}) delta=0x{image_base+va-rawptr:08X} perm={perm}")

def sec_of(v):
    for s in sections:
        lo = image_base + s["va"]
        # PE section extent in VA is max(VirtualSize, SizeOfRawData) page-aligned
        hi = image_base + s["va"] + max(s["vsize"], s["rawsize"])
        if lo <= v < hi:
            return s, lo, hi
    return None, None, None

def file_off_of(v):
    # correct per-section delta: fileoff = (v - sectionVA) + PointerToRawData
    s, lo, hi = sec_of(v)
    return None if not s else (v - lo) + s["rawptr"]

def read_at(v, n):
    """bytes at VA, following the real per-section delta"""
    s, lo, hi = sec_of(v)
    if not s:
        return None
    off = (v - lo) + s["rawptr"]           # file offset
    if s["rawptr"] == 0 or off + n > s["rawptr"] + s["rawsize"]:
        return b"\0" * n   # uninitialized / zero-filled past raw extent
    return data[off:off+n]

print("\n== every section's Characteristics, decoded ==")
for s in sections:
    print(f"  {s['name']:<8} char=0x{s['chars']:08X} "
          f"WRITE=0x80000000:{'set' if s['chars']&0x80000000 else 'clear'} "
          f"EXECUTE=0x20000000:{'set' if s['chars']&0x20000000 else 'clear'} "
          f"READ  =0x40000000:{'set' if s['chars']&0x40000000 else 'clear'}")

print(f"\n== locate 0x{TARGET:08X} ==")
s, lo, hi = sec_of(TARGET)
if s:
    pg = TARGET & ~0xFFF
    print(f"  section={s['name']}  VA range 0x{lo:08X}-0x{hi:08X}")
    print(f"  VirtualSize=0x{s['vsize']:08X} SizeOfRawData=0x{s['rawsize']:08X}")
    print(f"  intra-section offset = 0x{TARGET-lo:08X}")
    print(f"  delta (VA - fileoff) = 0x{image_base + s['va'] - s['rawptr']:08X}")
    print(f"  file offset          = 0x{file_off_of(TARGET):08X}")
    print(f"  page                 = 0x{pg:08X} (0x{TARGET:08X} & ~0xFFF)")
    print(f"  page offset          = 0x{TARGET & 0xFFF:04X}")
    print(f"  Characteristics      = 0x{s['chars']:08X} -> "
          f"IMAGE_SCN_MEM_WRITE(0x80000000) "
          f"{'SET (writable)' if s['chars']&0x80000000 else 'CLEAR (read-only)'}")
    # is the page inside the *raw data* extent, or past it?
    raw_end = image_base + s["va"] - s["rawptr"] + s["rawptr"] + s["rawsize"]
    print(f"  section raw-data VA extent ends at 0x{raw_end:08X}")
    print(f"  target {'INSIDE' if TARGET < raw_end else 'PAST'} raw extent "
          f"({'file-backed' if TARGET < raw_end else 'zero-fill / uninit'})")
    # does the page also cross into another section's VA?
    for t in sections:
        a, b = image_base+t["va"], image_base+t["va"]+max(t["vsize"], t["rawsize"])
        if a <= pg < b or a < hi and b > lo and t is not s:
            print(f"  NOTE section {t['name']} VA 0x{a:08X}-0x{b:08X} overlaps this page")
else:
    print("  0x%08X is NOT in any section" % TARGET)

print("\n== .text (or first CODE section) delta sanity ==")
txt = next((x for x in sections if x["chars"] & 0x20000000), sections[0])
print(f"  code section = {txt['name']} delta=0x{image_base+txt['va']-txt['rawptr']:08X} "
      f"(the assumed 0x00400000 holds: {image_base+txt['va']-txt['rawptr']==0x00400000})")

if "--bytes" in sys.argv or "bytes" in sys.argv or "all" in sys.argv or True:
    print(f"\n== 32 bytes at 0x{TARGET:08X} ==")
    b = read_at(TARGET, 32)
    print("  hex:", " ".join(f"{x:02X}" for x in b))
    print("  as 8 little-endian float32:")
    for i in range(0, 32, 4):
        f = struct.unpack_from("<f", b, i)[0]
        print(f"    [{i//4}] bytes {b[i:i+4].hex().upper()} -> {f:.9g}")
    print("  as 8 little-endian uint32:")
    for i in range(0, 32, 4):
        print(f"    [{i//4}] 0x{struct.unpack_from('<I', b, i)[0]:08X}")
    # wider context to see the arithmetic progression
    w = read_at(TARGET & ~0x3F, 0x400)
    off0 = (TARGET & ~0x3F) - image_base
    print(f"\n  float table context, 0x400 bytes from 0x{TARGET & ~0x3F:08X}:")
    vals = [struct.unpack_from("<f", w, i)[0] for i in range(0, len(w), 4)]
    tv = [v for v in vals]
    print("   first 12:", [f"{v:.6f}" for v in tv[:12]])
    print("   around target (idx of 0x%08X in window) - 32B before / after:" % TARGET)
    k = (TARGET - (TARGET & ~0x3F))//4
    print("   before:", [f"{v:.6f}" for v in tv[max(0,k-4):k]])
    print("   at    :", [f"{v:.6f}" for v in tv[k:k+8]])
    print("   deltas:", [f"{tv[i+1]-tv[i]:.7f}" for i in range(k, k+7)])

# ---------------------------------------------------------------- capstone
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
def disasm(v, n=256, start_off=None):
    buf = read_at(v, n)
    if buf is None: return []
    return list(md.disasm(buf, v))

if "pe" in sys.argv or len(sys.argv) == 1:
    pass

print(f"\n== disassembly OF the data at 0x{TARGET:08X} (what EIP actually decodes) ==")
for ins in disasm(TARGET, 48):
    print(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}")

print(f"\n== back-trace anchors: how the SAME bytes decode from different starts ==")
for anchor in (TARGET, TARGET-1, TARGET-2, TARGET-3, TARGET-4, TARGET-6, TARGET-7, TARGET-8):
    ins = disasm(anchor, 1)
    tag = "  <-- EIP" if anchor == TARGET else ""
    if ins:
        print(f"  @{anchor:08X}: {ins[0].bytes.hex():<8} {ins[0].mnemonic:<7} {ins[0].op_str}{tag}")
    else:
        print(f"  @{anchor:08X}: <undisassemblable>{tag}")

print(f"\n== alignment forensics on the faulting VA ==")
print(f"  0x{TARGET:08X} mod 4 = {TARGET%4}  mod 8 = {TARGET%8}  mod 16 = {TARGET%16}")
print("  -> a 4-byte float element in a 4-aligned table lives at VA%4==0.")
print(f"     0x{TARGET:08X} is 2 mod 4, so it is NOT an aligned float-element boundary;")
print("     a natural table store `mov [base+i*4],xmm` cannot land exactly here.")

# ============================================================ TEXT SWEEP
def text_sweep():
    TXT = next(s for s in sections if s["name"] == ".text")
    t_va = image_base + TXT["va"]
    t_bytes = read_at(t_va, TXT["vsize"])
    print(f"\n== capstone linear sweep of .text  0x{t_va:08X} + 0x{TXT['vsize']:X} ==")
    m = Cs(CS_ARCH_X86, CS_MODE_32); m.detail = True
    m.skipdata = True                       # CRITICAL: keep decoding past bad bytes
    LO, HI = 0x0084F200, 0x0084F400          # lead (a): exact table neighborhood
    WLO, WHI = 0x0084E000, 0x00851000        # wider page-band for lead (b)
    n_dec = 0; last_va = t_va
    abs_hits = []                            # memory operands whose abs disp in band
    imm_hits = []                            # imm32 operands in band
    idx_store = []                           # base+idx*scale+disp writes near band
    X86_OP_MEM, X86_OP_IMM = 3, 2
    for ins in m.disasm(t_bytes, t_va):
        n_dec += 1; last_va = ins.address + ins.size
        if ins.mnemonic == "data":      # skipdata pseudo-entry: no operands
            continue
        try:
            ops = list(ins.operands)
        except Exception:
            continue
        # walk capstone's structured operands (authoritative, not regex)
        for op in ops:
            if op.type == X86_OP_MEM:
                mem = op.mem
                disp = mem.disp & 0xFFFFFFFF
                has_idx = mem.index != 0
                scale = mem.scale
                # [disp] absolute, no base/index  -> static data reference
                if not has_idx and mem.base == 0:
                    if LO <= disp <= HI:
                        abs_hits.append((ins.address, ins.mnemonic, ins.op_str, disp, "A"))
                    elif WLO <= disp <= WHI:
                        abs_hits.append((ins.address, ins.mnemonic, ins.op_str, disp, "W"))
                # base+index*scale+disp  (lead b) -- record disp + whether store
                elif has_idx and scale in (1,2,4,8) and 0x00800000 <= disp <= 0x00B80000:
                    is_write = ins.mnemonic in (
                        "mov","movaps","movups","movss","movsd","movlp","movhp",
                        "add","sub","and","or","xor","adc","sbb","xadd",
                        "fsts","fst","fstp","push") or ins.mnemonic.startswith("cmov")
                    base = ins.reg_name(mem.base) if mem.base else "(abs)"
                    idx  = ins.reg_name(mem.index) if mem.index else ""
                    idx_store.append((ins.address, ins.mnemonic, ins.op_str, disp,
                                      base, idx, scale, is_write))
                # [base+disp] with disp in band (could be a struct field write)
                if not has_idx and mem.base != 0 and (LO <= disp <= HI):
                    abs_hits.append((ins.address, ins.mnemonic, ins.op_str, disp,
                                     "B+D"))
            elif op.type == X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if LO <= v <= HI:
                    imm_hits.append((ins.address, ins.mnemonic, ins.op_str, v, "IMM"))
                elif WLO <= v <= WHI:
                    imm_hits.append((ins.address, ins.mnemonic, ins.op_str, v, "IMMW"))
    print(f"  decoded {n_dec:,} instr, reached 0x{last_va:08X} "
          f"({'FULL' if last_va>=t_va+TXT['vsize']-16 else 'TRUNC'})")
    print(f"\n  == lead(a) absolute operands in [0x{LO:08X},0x{HI:08X}] : {len(abs_hits)} ==")
    for a,mn,op,v,tag in abs_hits:
        if tag in ("A","B+D","W"):
            print(f"    [{tag}] @{a:08X}: {mn} {op}   (0x{v:08X})")
    print(f"\n  == lead(a) imm32 in [0x{LO:08X},0x{HI:08X}] : {len(imm_hits)} ==")
    for a,mn,op,v,tag in imm_hits[:120]:
        print(f"    [{tag}] @{a:08X}: {mn} {op}   (imm 0x{v:08X})")
    print(f"\n  == lead(b) base+idx*scale+disp stores, disp in .data band : {len(idx_store)} ==")
    near = [h for h in idx_store if LO <= h[3] <= HI or (0x0084F000 <= (h[3] & ~0xFFF) <= 0x00851000)]
    print(f"     (of which disp in [0x{LO:08X},0x{HI:08X}] page band: {len(near)})")
    for a,mn,op,dv,base,idx,sc,isw in idx_store:
        band = (0x0084E000 <= dv <= 0x00851000)
        flag = "WRITE" if isw else "read"
        if band:
            print(f"    @{a:08X}: [{flag}] {mn} {op}  base={base} idx={idx}*{sc} disp=0x{dv:08X}")
    # Summary count of ALL indexed stores to be sure the filter works
    allsw = sum(1 for h in idx_store if h[7])
    print(f"     (total indexed .data stores of any disp: {len(idx_store)}, writes: {allsw})")
    return abs_hits, imm_hits, idx_store

if "scan" in sys.argv or "all" in sys.argv:
    text_sweep()

# ============================================================ 0x0054A56E
def crash_56e():
    A = 0x0054A56E
    print(f"\n== 0x{A:08X} context (the 'mov [esi+4],0' crash) ==")
    s, lo, hi = sec_of(A)
    if s:
        print(f"  section {s['name']} char=0x{s['chars']:08X} "
              f"WRITE={'set' if s['chars']&WRITE_BIT else 'clear'} "
              f"EXEC={'set' if s['chars']&EXEC_BIT else 'clear'}")
    print(f"  page 0x{A & ~0xFFF:08X}")
    print("  disasm window 0x%08X-0x%08X:" % (A-40, A+8))
    for ins in disasm(A-40, 48):
        tag = "  <== EIP" if ins.address==A else ""
        print(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:<8} {ins.op_str}{tag}")
    # look back further for the free() call whose arg became the corrupted esi
    print("  disasm window 0x%08X-0x%08X (search the preceding call/push chain):" % (A-120, A-40))
    for ins in disasm(A-120, 80):
        tag=""
        if ins.mnemonic=="call" and "0x" in ins.op_str: tag=" <-- CALL"
        if "esi" in ins.op_str: tag+="  [esi]"
        print(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:<8} {ins.op_str}{tag}")

if "crash56e" in sys.argv or "all" in sys.argv:
    crash_56e()

# ============================================================ VERIFY (all report claims)
import math
def verify():
    print("\n\n############ VERIFICATION: every CRASH_ADDR_ANALYSIS.md claim ############")
    # (1) no branch/jmp/push target inside the neighborhood [0x84F200,0x84F400] in .text
    m = Cs(CS_ARCH_X86, CS_MODE_32); m.detail=True; m.skipdata=True
    tb = read_at(image_base + next(s for s in sections if s['name']=='.text')["va"],
                 next(s for s in sections if s['name']=='.text')["vsize"])
    tgt=[]; imm_exact=[]; disp_exact=[]; abs_store=[]
    for ins in m.disasm(tb, image_base+next(s for s in sections if s['name']=='.text')["va"]):
        if ins.mnemonic=="data": continue
        if ins.mnemonic in ("jmp","call") and ins.op_str.startswith("0x"):
            try: v=int(ins.op_str[2:],16)
            except: v=0
            if 0x84F200<=v<=0x84F400: tgt.append((ins.address,ins.mnemonic,hex(v)))
        try: ops=list(ins.operands)
        except: ops=[]
        for o in ops:
            if o.type==3 and (o.mem.disp&0xFFFFFFFF)==TARGET: disp_exact.append((ins.address,ins.mnemonic,ins.op_str))
            if o.type==2 and (o.imm&0xFFFFFFFF)==TARGET: imm_exact.append((ins.address,ins.mnemonic,ins.op_str))
            # absolute stores [abs],reg with abs==TARGET (the literal self-write reading)
            if o.type==3 and o.mem.base==0 and o.mem.index==0 and (o.mem.disp&0xFFFFFFFF)==TARGET \
               and ins.mnemonic in ("mov","fstp","add","sub","and","or","xor"):
                abs_store.append((ins.address,ins.mnemonic,ins.op_str))
    print(f" (1a) jmp/call targets in [0x84F200,0x84F400]: {len(tgt)} (expect 0)")
    print(f" (1b) imm32 == 0x0084F2BA in .text:            {len(imm_exact)} (expect 0)")
    print(f" (1c) disp32 == 0x0084F2BA (any mem op):       {len(disp_exact)} (expect 0)")
    print(f" (1d) literal self-store [0x84F2BA],reg:       {len(abs_store)} (expect 0)")
    raw_occ = len(re.findall(re.escape(struct.pack("<I",TARGET)), data))
    print(f" (1e) raw LE dword 0x0084F2BA anywhere in file: {raw_occ} (expect 0)")
    # (2) stores into the LUT base 0x84F084/088 grid: expect 0 (reads are fld)
    lut_st=0
    for ins in m.disasm(tb, image_base+next(s for s in sections if s['name']=='.text')["va"]):
        if ins.mnemonic=="data": continue
        try: ops=list(ins.operands)
        except: ops=[]
        for oi,o in enumerate(ops):
            if o.type==3 and 0x84F080<=(o.mem.disp&0xFFFFFFFF)<=0x84F08C and o.mem.index!=0 \
               and ins.mnemonic=="mov" and oi==0:
                lut_st+=1
    print(f" (2) mov-stores into [reg*4+0x84F084/088]: {lut_st} (expect 0; only fld reads + aligned fstp in init)")
    # (3) the LUT initializer exists and writes only 4-aligned
    init = [i for i in m.disasm(read_at(0x004CB0E0,0x70),0x004CB0E0)
            if i.mnemonic in ("fstp","cmp") and ("esi" in i.op_str)]
    print(" (3) LUT init stores (aligned, 4-byte step):")
    for i in init: print(f"      {i.address:08X}: {i.mnemonic} {i.op_str}")
    # (4) semantics constants  (.rdata delta is 0x00400000)
    RD=0x00400000
    print(" (4) phase-table constants:")
    print(f"      0x007E8988 = {struct.unpack_from('<d',data,0x007E8988-RD)[0]:.9f}  (expect 2*pi/8192={2*math.pi/8192:.9f})")
    print(f"      0x008223B0 = {struct.unpack_from('<f',data,0x008223B0-RD)[0]:.6f}  (expect 8192/pi={8192/math.pi:.6f})")
    print(f"      0x007E8970 = {struct.unpack_from('<d',data,0x007E8970-RD)[0]:.6f}  (expect 8192/(2pi)={8192/(2*math.pi):.6f})")
    print(f"      slot count [0x84F084,0x859088)/4 = {(0x859088-0x84F084)//4} ; idx of 0x84F2B8 = {(0x84F2B8-0x84F084)//4}")
    # (5) 0x54A56E: preceding free arg = [esi+4]; esi=ecx(this)
    print(" (5) preceding-free of 0x54A56E (expect mov eax,[esi+4]; push eax; call 0x7c8b3d):")
    for i in m.disasm(read_at(0x0054A562,0x20),0x0054A562):
        print(f"      {i.address:08X}: {i.mnemonic} {i.op_str}")
    # (6) SBH lineage: free chain + globals + RC-1 guard same cluster
    print(" (6) SBH lineage: free 0x007C8B3D -> 0x007C93E8 -> 0x007CF7BD ; RC-1 guard 0x007CFC9B ; "
          "shared SBH global [0x00B78B94]:")
    occ=sum(1 for addr in range(0x00401000,0x007E1000)
            if data[addr-RD]==0xA1 and struct.unpack_from("<I",data,addr-RD+1)[0]==0x00B78B94)
    print(f"        .text 'A1 [0x00B78B94]' refs = {occ} (expect 7)")
    # (7) page mapping of the decoded store target
    print(f" (7) pristine decode at EIP=0x84F2BA -> fnstsw store target 0x3DDE9CC3 ; "
          f"image=[0x00400000,0x00B96000) ; OUTSIDE image? {not (0x00400000<=0x3DDE9CC3<0x00400000+0x796000)} (expect True)")
    # (8) poison value & CRT flavour
    print(f" (8) 0xFE00FFFF raw LE dword in file: {len(re.findall(re.escape(struct.pack('<I',0xFE00FFFF)),data))} (expect 0 -> runtime value)")
    print("      debug-CRT fills present? " + ", ".join(
          f"{p}x4={data.count(bytes([int(p,16)])*4)}" for p in ("cd","dd","ba","f1"))
          + " (expect all 0 -> retail/non-debug CRT)")
    print("#### VERIFICATION DONE ####")

if "verify" in sys.argv or "all" in sys.argv:
    verify()
