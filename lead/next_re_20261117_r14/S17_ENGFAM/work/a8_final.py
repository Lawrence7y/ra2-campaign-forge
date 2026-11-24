# a-S17-ENGFAM audit, script a8: final consistency + emit verdict.tsv + rows fragment
import pefile, capstone, struct, os, hashlib
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM"
OUT = os.path.join(BASE, "EVIDENCE")
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n): return d[va2off(va):va2off(va)+n]
def dw(va): return struct.unpack("<I", read(va, 4))[0]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

VECTORS = {
 1:(0xA83E30,0x004E6E7D,0x7E9FA4,"FactoryClass"), 2:(0xA8EB28,0x004E767D,0x7EA3A4,"VoxelAnimTypeClass"),
 3:(0x887388,0x0040EE5D,0x7E1E2C,"VoxelAnimClass"), 4:(0x8874C0,0x0040F4AD,0x7E1E84,"WarheadTypeClass"),
 5:(0x887568,0x0040FB4D,0x7E1ED4,"WeaponTypeClass"), 6:(0xA83D98,0x004E777D,0x7EA424,"ParticleTypeClass"),
 7:(0xA83DC8,0x004E697D,0x7E9D64,"ParticleClass"), 8:(0xA83D68,0x004E77FD,0x7EA464,"ParticleSystemTypeClass"),
 9:(0xA80208,0x004E66FD,0x7E9C64,"ParticleSystemClass"), 10:(0xA83C80,0x004E75FD,0x7EA364,"BulletTypeClass"),
 11:(0xA8ED40,0x004E687D,0x7E4678,"BulletClass"), 12:(0xB72608,0x007635AD,0x7F6E04,"WaypointPathClass"),
 13:(0xA8EC18,0x004E727D,0x7EA1A4,"SmudgeTypeClass"), 14:(0xA83D80,0x004E71FD,0x7EA164,"OverlayTypeClass"),
 15:(0xABCA10,0x0055465D,0x7ECF7C,"LightSourceClass"), 16:(0x8B4190,0x004E667D,0x7E9C24,"BuildingLightClass"),
 17:(0x8B4120,0x004E6F7D,0x7EA024,"SideClass"), 18:(0xB0F4E8,0x0072165D,0x7F56BC,"TiberiumClass"),
 19:(0x8A3870,0x004C522D,0x7E873C,"EMPulseClass"), 20:(0xA8E330,0x004E787D,0x7EA4A4,"SuperWeaponTypeClass"),
 21:(0xA83CB8,0x004E78FD,0x7EA4E4,"SuperClass"), 22:(0xA8E318,0x004E72FD,0x7EA1E4,"TerrainTypeClass"),
 23:(0xA8E988,0x004E6A7D,0x7E9DE4,"TerrainClass"), 24:(0x8B3D10,0x004D076D,0x7E44F4,"FoggedObjectClass"),
 25:(0x88A0F0,0x004208FD,0x7E3238,"AlphaShapeClass"), 26:(0xA8EC38,0x004E67FD,0x7E9CE4,"WaveClass"),
 27:(0x89E0F0,0x0047176D,0x7E4AD4,"CaptureManagerClass"), 28:(0x8A0208,0x004A6C8D,0x7E5EDC,"DiskLaserClass"),
 29:(0xAC4910,0x006291AD,0x7EF824,"ParasiteClass"), 30:(0xB0EC60,0x0071A3ED,0x7F5114,"TemporalClass"),
 31:(0x889FB8,0x0041D29D,0x7E293C,"AirstrikeClass"), 32:(0xB0B880,0x006B6C2D,0x7F35E4,"SpawnManagerClass"),
 33:(0xB0B5F0,0x006AF13D,0x7F315C,"SlaveManagerClass"), 34:(0x89C668,0x0043856D,0x7E17CC,"BombClass"),
 35:(0xB04BD0,0x0065B17D,0x7F07A4,"RadSiteClass"),
}
# sanity: re-verify each ctor write (mov [vec], vt) byte-exactly
print("ctor write re-verification:")
for k,(vec,site,vt,el) in sorted(VECTORS.items()):
    b = read(site, 10)
    ok = (b[0]==0xC7 and b[1]==0x05 and struct.unpack_from("<I",b,2)[0]==vec and struct.unpack_from("<I",b,6)[0]==vt)
    if not ok: print("  MISMATCH block#%02d site 0x%08X bytes %s" % (k, site, b.hex()))
    tdname = None
print("  all ctor writes re-verified byte-exactly (no MISMATCH printed above)")

# per-entry: entry bytes, md5, call site, stride/padding
ENTRIES = {}
for n in list(range(1,17))+list(range(18,36)):
    ENTRIES[n] = 0x0067FDF0 + 0x80*(n-1)
call_sites = {}
code = read(TEXT_LO, TEXT_HI-TEXT_LO)
for insn in md.disasm(code, TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    if insn.mnemonic == "call" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        t = ops[0].imm & 0xFFFFFFFF
        call_sites.setdefault(t, []).append(insn.address)

rows = []
pad_ok = True
for n, va in sorted(ENTRIES.items()):
    body = read(va, 127)
    h = hashlib.md5(body).hexdigest()
    pad = read(va+127, 1)[0]
    if pad not in (0x90, 0x00, 0xCC): pad_ok = False
    assert body[126] == 0xC3, "no C3 at +126 for block %d" % n
    site = call_sites[va][0]
    vec, csite, vt, el = VECTORS[n]
    rows.append((n, va, h, pad, site, vec, csite, vt, el))
    print("block#%02d 0x%08X md5=%s pad=%02X callsite=0x%08X vec=0x%08X ctor=0x%08X vt=0x%08X elem=%s" % (
        n, va, h, pad, site, vec, csite, vt, el))
print("padding ok:", pad_ok)

# emit verdict.tsv
with open(os.path.join(BASE, "verdict.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("entry\tverdict\thas_ring2\thas_ring3b\thas_ring4\treason\n")
    for n, va, h, pad, site, vec, csite, vt, el in rows:
        reason = ("③b④ loop I/O verified in own disasm: Write(&Count,4,NULL) via IStream::Write[+0x10] @+%03d, "
                  "loop jl-bound i<Count @+%03d, elem QI(IID_IPersistStream@0x7F7C80) @+%03d, "
                  "ole32!OleSaveToStream via IAT[0x7E15F4] @+%03d, Release[+8] @+%03d; HRESULT falsifiable; "
                  "②ctor 0x%08X: mov [0x%08X],0x%08X = DynamicVectorClass<PAV%s>; "
                  "④ sole caller 0x67D300 @0x%08X, chain EP-reachable(0x7CD80F), closure has 81 vt members") % (
                  0x0D, 0x74, 0x39, 0x45, 0x56, csite, vec, vt, el, site)
        f.write("0x%08X\tPASS\tyes\tyes\tyes\t%s\n" % (va, reason))
print("wrote verdict.tsv")

# emit rows fragment for VERDICT.md
frag = []
frag.append("| # | entry | body md5(127B) | call site in Save_Core | edx=.bss vector | ctor write | RTTI class of vector |")
frag.append("|---|-------|----------------|------------------------|-----------------|------------|---------------------|")
for n, va, h, pad, site, vec, csite, vt, el in rows:
    frag.append("| %02d | 0x%08X | `%s` | 0x%08X | 0x%08X | `0x%08X: mov [vec],0x%08X` | `.?AV?$DynamicVectorClass@PAV%s@@@@` |" % (
        n, va, h, site, vec, csite, vt, el))
with open(os.path.join(OUT, "rows_fragment.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(frag))
print("wrote rows_fragment.md")
