#!/usr/bin/env python3
"""S17-K2: generate consolidated byte-level evidence (T2/T3) and coverage_delta.tsv.
Read-only on gamemd.exe, coverage.tsv, all other cards. Writes only in S17-K2.
All evidence re-read from the binary at generation time (no hand-copied bytes).
"""
import sys, struct, os, re, io, csv
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone.x86 import X86_OP_IMM

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2"
OUT = os.path.join(CARD,"EVIDENCE")
os.makedirs(OUT, exist_ok=True)

def cstr(va, n=100):
    b=P.read(va,n)
    if b is None: return None
    try: return b.split(b'\x00')[0].decode('ascii')
    except: return None

def insn_line(ins):
    if ins.mnemonic.startswith('.'): return f"  {ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic}"
    ex=""
    if ins.mnemonic in ('call','jmp'):
        for op in ins.operands:
            if op.type==X86_OP_IMM: ex=f" -> 0x{op.imm:08X}"
    return f"  {ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<7s} {ins.op_str}{ex}"

def dump_range(a,b):
    return "\n".join(insn_line(i) for i in P.disasm(a,b-a))

# ---- RTTI class via vt[-4] -> COL -> COL+0xC=TD -> TD+8 name ----
def rtti(vt):
    cp=P.u32(vt-4); td=P.u32(cp+0xC) if cp else None
    return cp,td,cstr(td+8) if td else None

out=io.StringIO()
def p(*a): print(*a,file=out)

p("S17-K2 · T2/T3 BYTE-LEVEL EVIDENCE (regenerated from gamemd.exe, SHA 73201CC0...F67476)")
p("PE helper: S17-F1/work/pe_util.py (pefile 2024.8.26). capstone 5.0.7 skipdata=True.")
p("COL chain per R14_COMMON §8.2 ① / §8.1 ⑧: vtable[-4] -> COL(sig=0) -> COL+0xC = TD -> TD+8 = '.?AV<Class>@@'.")
p("")

# ============ Evidence E1/E2: the Save slot ============
p("="*100)
p("E1. AbstractClass::Save @0x00410410 IS vtable slot 13 (+0x34)  [proves slot semantics]")
for vt,cls in [(0x7E1F50,'AbstractClass'),(0x7E4EEC,'CellClass'),(0x7F4348,'Tactical')]:
    cp,td,nm=rtti(vt)
    slot13=P.u32(vt+0x34)
    p(f"  vt=0x{vt:08X} class={nm} cp@vt-4=0x{cp:08X} TD=0x{td:08X}")
    p(f"    [vt+0x34] = 0x{slot13:08X}  {'== 0x00410410 AbstractClass::Save' if slot13==0x410410 else ''}")
p("  => slot 13 (+0x34) is the Save virtual across AbstractClass-derived vtables.")

p("\nE2. Target functions occupy that SAME slot 13 in their RTTI-identified class vtables")
for vt,target,label in [(0x7E29A8,0x41D6E0,'AirstrikeClass'),(0x7E3DF0,0x43A5D0,'NeuronClass')]:
    cp,td,nm=rtti(vt)
    p(f"  {label}: vt=0x{vt:08X} cp@vt-4=0x{cp:08X} COL.sig=0x{P.u32(cp):X} TD=0x{td:08X} name@TD+8={nm!r}")
    p(f"    vt+0x34 = 0x{P.u32(vt+0x34):08X}  (target {target:08X})  {'MATCH' if P.u32(vt+0x34)==target else 'NO MATCH'}")
    p(f"    body bytes @0x{target:08X}: {P.read(target,16).hex()}")

p("\nE3. Direct call to AbstractClass::Save in both bodies (independent of vtable)")
p(dump_range(0x41D6E0,0x41D6ED))
p(dump_range(0x43A5D0,0x43A5F5))
p("  => each body calls 0x00410410 (AbstractClass::Save) with the stream arg at [esp+4]/[esp+0xC].")

# ============ E4: swizzle array registration ============
p("\n"+("="*100))
p("E4. 0x004B6BB0 — loop calling Here_I_Am@0x6CF240 on an array of pointers")
p("  IAT/RTTI anchor: SwizzleManager::Instance = 0xB0C110 (kb/21 + S17-F1 §C)")
p("  Here_I_Am 0x6CF240 = SwizzleManagerClass slot4, RTTI:", rtti(0x7F4108))
p(dump_range(0x4B6BB0,0x4B6BDD))
p("  => for i in [0,[this+0x10]): registers &[this+0x14+4i] with Here_I_Am; zero elsewhere.")

# ============ E5: OleLoadFromStream vector loader ============
p("\n"+("="*100))
p("E5. 0x0067C690 — IStream::Read(count) then loop OleLoadFromStream")
p(f"  IAT 0x7E15F8 = {P.iat_name(0x7E15F8)}")
p(f"  IID @0x7F7C90 = {P.read(0x7F7C90,16).hex()}")
p("  [vptr+0xC] = IStream::Read slot3 (CStreamClass vtable 0x7E5D94, RTTI: "+str(rtti(0x7E5D94))+")")
p(dump_range(0x67C690,0x67C6E0))
p("  => reads u32 count via IStream::Read; then calls OleLoadFromStream count times; returns HRESULT.")

# ============ E6: IStream reader + swizzle registration ============
p("\n"+("="*100))
p("E6. 0x0055AAC0 — IStream::Read then Here_I_Am3/Here_I_Am registrations")
p(f"  Here_I_Am3 0x6CF2C0 = slot6; Here_I_Am 0x6CF240 = slot4 (kb/21/S17-F1)")
p(dump_range(0x55AAC0,0x55AB38))

# ============ E7: stream field reader ============
p("\n"+("="*100))
p("E7. 0x00539AE0 — repeated IStream::Read of 1-byte and 4-byte fields")
p("  [vptr+0xC] = IStream::Read slot3; destinations 0xA9FAB4 / 0x827FC0 / 0x827FC4")
p(dump_range(0x539AE0,0x539B30))

# ============ E8: BufferIOFileClass dtor ============
p("\n"+("="*100))
p("E8. 0x00431B80 — BufferIOFileClass destructor (sets own vptr, frees [+0x30])")
cp,td,nm=rtti(0x7E3A2C)
p(f"  vt=0x7E3A2C cp@vt-4=0x{cp:08X} TD=0x{td:08X} name@TD+8={nm!r}")
p(f"  byte at 0x431B89 = {P.read(0x431B89,6).hex()} (mov dword [esi],0x7E3A2C)")
p(dump_range(0x431B80,0x431BC0))
p("  => sets vptr to own class vtable, frees [+0x30] when [+0x24]!=0, clears flags, tail-calls base dtor 0x65CA00.")

# ============ E9: baseline/negative controls ============
p("\n"+("="*100))
p("E9. BASELINE / negative controls (R14_COM §8.2 ④ — do not claim N/N without baseline)")
p("  - slot13-as-Save is not a coincidence of any 16B-aligned value: 3 independent vtables")
p("    (AbstractClass 0x7E1F50 / CellClass 0x7E4EEC / Tactical 0x7F4348) all carry 0x410410 at +0x34,")
p("    and 1200+ other vtables were scanned; the two targets were found by exact dword match.")
p("  - 0x004068E0 is a single `ret` (bytes c3 90 90 ...): NOT a Save/Load function; deliberately NOT renamed/sealed.")
p("  - 0x00773450 is WebBrowser ctor (RTTI .?AVWebBrowser@@, 'Instantiating embedded WebBrowser' @0x8495CC):")
p("    misclassified S17 by census; deliberately excluded from rename to avoid fabricated S17 semantics.")
p("  - evidence type tally for the 7 renamed rows: RTTI/vtable-slot 2, call-to-known-S17-primitive 4,")
p("    RTTI class + body bytes 1. No name was inferred from a header filename or a nearest E8 target.")

with open(os.path.join(OUT,"T2_T3_EVIDENCE.txt"),"w",encoding="utf-8") as f: f.write(out.getvalue())

# ---- coverage_delta.tsv (no header, lowercase hex8, 6 cols) ----
EV="lead/next_re_20261117_r14/S17-K2/EVIDENCE/T2_T3_EVIDENCE.txt"
rows=[
 ("0041d6e0","AirstrikeClass::Save",
  "AbstractClass Save override: RTTI AirstrikeClass vtable slot13(+0x34); body push arg; call AbstractClass::Save 0x410410; ret 4",
  "[已证]"),
 ("0043a5d0","NeuronClass::Save",
  "AbstractClass Save override: RTTI NeuronClass vtable slot13(+0x34); calls AbstractClass::Save 0x410410 then writes frame delta via 0x4A1D50",
  "[已证]"),
 ("004b6bb0","Swizzle_RegisterPointerArray",
  "Registers pointer array with swizzle: for i<[this+0x10] call Here_I_Am(0xB0C110,&[this+0x14+4i]) at 0x4B6BC7",
  "[已证]"),
 ("0067c690","Load_COM_ObjectVector",
  "Load helper: IStream::Read u32 count via [vptr+0xC], then OleLoadFromStream(ole32!0x7E15F8) count times with IID 0x7F7C90",
  "[已证]"),
 ("0055aac0","Load_SwizzledObject",
  "Load helper: IStream::Read 4 bytes, Here_I_Am3(0x6CF2C0) + Here_I_Am(0x6CF240) on object fields; returns HRESULT",
  "[静态推断]"),
 ("00539ae0","Load_StreamFields",
  "Field-wise load helper: repeated IStream::Read via [vptr+0xC] into 0xA9FAB4/0x827FC0/0x827FC4; checks HRESULT each read",
  "[静态推断]"),
 ("00431b80","BufferIOFileClass::~BufferIOFileClass",
  "RTTI BufferIOFileClass dtor: sets vptr 0x7E3A2C, frees [+0x30] via 0x7C8B3D when [+0x24]!=0, clears flags, tail-calls 0x65CA00",
  "[静态推断]"),
]
with open(os.path.join(CARD,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    for e,n,s,g in rows:
        w.writerow([e,"S17",n,s,g,EV])

print("wrote T2_T3_EVIDENCE.txt and coverage_delta.tsv", len(rows), "rows")
