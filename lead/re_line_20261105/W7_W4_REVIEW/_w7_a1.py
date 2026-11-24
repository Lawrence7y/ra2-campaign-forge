# -*- coding: utf-8 -*-
"""W7 · A1 independent re-verification probe (read-only, zero真机, zero注入).
Focus:
  ① byte basis for "overturn W3 'each pathfind increments exactly once'":
     - 0x42CC80 re-advance loop (max 4 extra), 0x42D170 18 callers, singleton imm 28 sites.
  ② "wrap jumps 0 and that time +2" and "ctor initial value -1 => first call wraps".
  ③ pefile basis for symbol name "未定名" (RSDS/NB10/.pdb all zero).
All output printed to stdout; caller redirects to _w7_a1_out.txt.
"""
import sys, os, hashlib, struct, datetime
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')
from ra2tool import Engine

OUT = []
def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s, flush=True)

p('=== W7 A1 PROBE ===')
p('RUN_TS', datetime.datetime.now().isoformat())

# ---------- 0. object binding (hash of the reviewed card) ----------
CARD = r'D:/Project/ra2-campaign-forge/lead/re_line_20261105/W4_FIELD_SPEC/sections/card_0087E8E0.md'
cb = open(CARD, 'rb').read()
p('OBJ_PATH', CARD)
p('OBJ_SIZE', len(cb))
p('OBJ_SHA256', hashlib.sha256(cb).hexdigest())

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
exeb = open(EXE, 'rb').read()
p('EXE_SIZE', len(exeb))
p('EXE_SHA256', hashlib.sha256(exeb).hexdigest())

e = Engine()
p('ENGINE_SHA', e.sha)
p('IMAGEBASE', hex(e.IB))
p('COVERAGE', e.coverage)

# ---------- helpers ----------
def show(va, n, tag):
    """Disassemble n bytes at va via Engine.disasm (aligned linear decode from va)."""
    p('--- DISASM', tag, hex(va), '+', hex(n), '---')
    for (a, b, m, o) in e.disasm(va, n):
        p('  0x%08X  %-24s  %s %s' % (a, b, m, o))

def xrefs_e8(target):
    """All E8 rel32 direct calls in the decoded stream whose target == target.
    Uses e.stream (re-synced linear decode) to be exhaustive & robust."""
    res = []
    for ins in e.stream:
        if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == 2:
            if ins.operands[0].imm == target:
                res.append((ins.address, ins.bytes.hex()))
    return res

def xrefs_e8e9(target):
    """All E8 (call) and E9 (jmp) rel32 whose target == target."""
    res = []
    for ins in e.stream:
        if ins.mnemonic in ('call', 'jmp') and ins.operands and ins.operands[0].type == 2:
            if ins.operands[0].imm == target:
                res.append((ins.address, ins.bytes.hex(), ins.mnemonic))
    return res

def pat_count(needle_hex, limit_dump=0):
    """Count raw byte-pattern occurrences in .text raw bytes (file-backed .text only)."""
    nd = bytes.fromhex(needle_hex)
    tb = e.raw[e.TB:e.TB + e.TSZ]
    res = []
    i = 0
    while True:
        j = tb.find(nd, i)
        if j < 0:
            break
        res.append(e.TLO + j)
        i = j + 1
    return res

# ========== SECTION 1 : ① overturn W3 "each pathfind increments exactly once" ==========
p('')
p('========== SECTION 1 : W3 claim byte-basis ==========')

# 1.1 direct E8 callers of ResetWorkspace 0x42A5B0 (card claims exactly 3)
p('')
p('[1.1] XREF_E8 to 0x42A5B0 (ResetWorkspace)')
x = xrefs_e8(0x42A5B0)
p('  COUNT', len(x))
for va, b in x:
    p('   ', hex(va), b)

# 1.2 the retry site 0x42CC80 + surrounding loop control (G2/G3)
p('')
p('[1.2] 0x42CB80..0x42CCC0 (retry/limit region of FindPath 0x42C900)')
show(0x42CB80, 0x150, 'RETRY_REGION')

# 1.3 the "max +5 / limit 5" bytes (0x42CB8B..0x42CBA1) - decode aligned
p('')
p('[1.3] 0x42CB8B region (add eax,5 / mov [esp+1c],eax) aligned decode')
show(0x42CB80, 0x30, 'LIMIT_BLOCK')

# 1.4 0x42D170 entry prologue + its call to 0x42A5B0 + G5 fail-check
p('')
p('[1.4] 0x42D170 entry prologue')
show(0x42D170, 0x14, 'D170_ENTRY')
p('[1.4b] 0x42D21C region (call 0x42c290 / test al / je fail)')
show(0x42D218, 0x1C, 'G5_FAILCHECK')
p('[1.4c] 0x42D450 fail epilogue')
show(0x42D450, 0x10, 'D452_FAIL')

# 1.5 0x42D170 direct callers (card claims 18)
p('')
p('[1.5] XREF_E8 to 0x42D170')
x = xrefs_e8(0x42D170)
p('  COUNT', len(x))
for va, b in x:
    p('   ', hex(va), b)

# 1.6 0x42C900 direct callers (card claims 2)
p('')
p('[1.6] XREF_E8 to 0x42C900')
x = xrefs_e8(0x42C900)
p('  COUNT', len(x))
for va, b in x:
    p('   ', hex(va), b)

# 1.7 singleton immediate mov ecx,0x87e8b8 = b9 b8 e8 87 00 in .text
p('')
p('[1.7] PATTERN b9b8e88700 (mov ecx,0x87e8b8) in .text')
bm = pat_count('b9b8e88700')
p('  COUNT', len(bm))
p('  VAS', ' '.join(hex(a) for a in bm))

# 1.8 classify the 28 sites: what each site calls/jumps to (E8/E9 rel32 shortly after)
p('')
p('[1.8] classify each mov ecx,0x87e8b8 site: next E8/E9 rel32 within +0x40 bytes')
for va in bm:
    # disassemble a small window to find the first call/jmp with rel32 target
    tgt = None
    for (a, b, m, o) in e.disasm(va, 0x40):
        if m in ('call', 'jmp'):
            # recover rel32 target from capstone op_str when possible
            try:
                imm = int(o, 16) if o.startswith('0x') else None
            except Exception:
                imm = None
            if imm is not None:
                tgt = (hex(a), m, hex(imm))
                break
    p('   ', hex(va), '->', tgt)

# 1.9 also verify "PAT 0x87e8e0 count 0" and "PAT 0x42a5b0 count 0"
p('')
p('[1.9] immediate-pointer patterns (4-byte LE of abs VA) in .text')
for name, imm in [('0x87e8e0', 0x87E8E0), ('0x87e8b8(const)', 0x87E8B8),
                  ('0x42a5b0', 0x42A5B0), ('0x42c900', 0x42C900),
                  ('0x42d170', 0x42D170)]:
    nd = struct.pack('<I', imm)
    cnt = pat_count(nd.hex())
    p('   ', name, 'count', len(cnt))

# 1.10 absolute-address direct memory census for the field (card: disp_hits=[]=0)
p('')
p('[1.10] disp_hits absolute-VA memory refs')
p('   disp_hits(0x87E8E0) =', e.disp_hits(0x87E8E0))
p('   disp_hits(0x87E8B8) =', e.disp_hits(0x87E8B8))
h28 = e.disp_hits_field(0x28)
p('   disp_hits_field(0x28) TOTAL =', len(h28))
pf = [r for r in h28 if 0x429000 <= r[0] < 0x42E000]
p('   disp_hits_field(0x28) in [0x429000,0x42E000) =', len(pf))

# ========== SECTION 2 : ② wrap +2 jump 0 & ctor -1 first-call-wrap ==========
p('')
p('========== SECTION 2 : wrap +2 / ctor -1 ==========')

# 2.1 full ResetWorkspace 0x42A5B0..0x42A690 body (W1/G1/W2 chain)
p('')
p('[2.1] ResetWorkspace 0x42A5B0 body (W1 / jne / clear / W2 / ret)')
show(0x42A5B0, 0xE0, 'RESETWORKSPACE_FULL')

# 2.2 focused bytes at the RMW sites
p('')
p('[2.2] W1 RMW bytes 0x42A5FB..0x42A606')
show(0x42A5FB, 0x0C, 'W1_RMW')
p('[2.2b] W2 RMW bytes 0x42A67F..0x42A68E')
show(0x42A67F, 0x10, 'W2_RMW')

# 2.3 constructor 0x42A6D0 body (W3 = -1 init)
p('')
p('[2.3] CTOR 0x42A6D0..0x42A720 (ecx=-1, [esi+0x28]=-1)')
show(0x42A6D0, 0x50, 'CTOR_HEAD')

# 2.4 static-init thunk 0x40AFA0 (this=singleton, call ctor)
p('')
p('[2.4] static-init thunk 0x40AFA0')
show(0x40AFA0, 0x20, 'STATIC_INIT_THUNK')

# 2.5 destructor 0x42A900 (card claims no +0x28 write)
p('')
p('[2.5] DTOR 0x42A900 head')
show(0x42A900, 0x40, 'DTOR_HEAD')

# 2.6 xrefs to ctor/dtor (card: ctor 1 at 0x40afa5, dtor 1 jmp at 0x40afc5)
p('')
p('[2.6] XREF_E8E9 to ctor 0x42A6D0:', xrefs_e8e9(0x42A6D0))
p('     XREF_E8E9 to dtor 0x42A900:', xrefs_e8e9(0x42A900))

# 2.7 arithmetic sanity for "+2 and skip 0" and "first call wraps"
p('')
p('[2.7] arithmetic chain (pure computation from decoded bytes)')
p('  ctor sets [esi+0x28] = 0xFFFFFFFF (from 0x42A6DC 83c9ff or ecx,-1 + 0x42A701 894e28)')
p('  W1: eax=[ecx+0x28]=0xFFFFFFFF; inc eax => 0x00000000 (ZF=1)')
p('  0x42A602 jne 0x42a688 NOT taken (ZF=1) => fall into full-clear branch')
p('  W2: eax=[ecx+0x28]=0x00000000 (W1 wrote 0); inc eax => 0x00000001; write back')
p('  net value: 0xFFFFFFFF -> 0x00000001  (delta = +2 mod 2^32, 0 is skipped)')

# 2.8 IsNodeVisited 0x42A690 reads (32-bit, sete compare)
p('')
p('[2.8] IsNodeVisited 0x42A690..0x42A6C8')
show(0x42A690, 0x40, 'ISNODEVISITED')

# ========== SECTION 3 : ③ pefile RSDS / NB10 / .pdb / symbol name ==========
p('')
p('========== SECTION 3 : pefile symbol-name basis ==========')
import pefile
pe = pefile.PE(EXE, fast_load=False)
p('[3.1] OPTIONAL header DataDirectory entries')
for i, dd in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
    if dd.VirtualAddress or dd.Size:
        p('   [%2d] %-28s RVA=0x%X Size=%d' % (i, dd.name if hasattr(dd, 'name') else '', dd.VirtualAddress, dd.Size))

# export directory
p('')
p('[3.2] EXPORT directory')
exp = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']]
p('   EXPORT_RVA', hex(exp.VirtualAddress), 'SIZE', exp.Size)
try:
    syms = pe.DIRECTORY_ENTRY_EXPORT.symbols if pe.DIRECTORY_ENTRY_EXPORT else []
    p('   EXPORT_SYMBOL_COUNT', len(syms))
except Exception as ex:
    p('   EXPORT_SYMBOL_COUNT (none / err)', ex)

# debug directory
p('')
p('[3.3] DEBUG directory entries')
dbg = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DEBUG']]
p('   DEBUG_RVA', hex(dbg.VirtualAddress), 'SIZE', dbg.Size)
if pe.DIRECTORY_ENTRY_DEBUG:
    for i, d in enumerate(pe.DIRECTORY_ENTRY_DEBUG):
        p('   [%d] Type=%d SizeOfData=%d AddressOfRawData=0x%X PointerToRawData=0x%X' % (
            i, d.struct.Type, d.struct.SizeOfData, d.struct.AddressOfRawData, d.struct.PointerToRawData))
        try:
            p('       entry.Type name =', pefile.DEBUG_TYPE.get(d.struct.Type, 'UNKNOWN'))
        except Exception:
            pass
        # dump first 32 raw bytes of the debug data
        off = d.struct.PointerToRawData
        raw = exeb[off:off + min(d.struct.SizeOfData, 40)]
        p('       RAW_HEAD', raw.hex(), '| ascii', repr(raw[:16]))
else:
    p('   NO DEBUG ENTRIES')

# CodeView signatures & descriptive strings anywhere in file
p('')
p('[3.4] byte-pattern census over WHOLE FILE')
for name, pat in [('RSDS', b'RSDS'), ('NB10', b'NB10'), ('.pdb', b'.pdb'),
                  ('.PDB', b'.PDB'), ('GenerationStamp', b'GenerationStamp'),
                  ('ResetWorkspace', b'ResetWorkspace'), ('PathFinder', b'PathFinder')]:
    c = exeb.count(pat)
    p('   %-16s count = %d' % (name, c))

# .MAP / linker map / symbol files in repo.
# NOTE: the repo contains Windows reparse-point junctions under out/re_work that
# make os.walk() recurse quasi-infinitely (23k+ dirs, 147k+ files, no termination
# in 120s).  We use a reparse-point-SAFE manual scandir walk that (a) never
# descends into directory symlinks/junctions and (b) caps total dirs visited.
import stat as _stat
p('')
p('[3.5] reparse-point-safe, bounded census of *.map / *.pdb / *.dbg / *.sym')
ROOT = r'D:/Project/ra2-campaign-forge'
SKIP = {'.git', 'node_modules', '.mimosa'}

def _is_reparse(entry):
    try:
        st = entry.stat(follow_symlinks=False)
        return bool(getattr(st, 'st_file_attributes', 0) & _stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False

mapfiles, symfound, dirs_seen, reparse_skipped = [], [], 0, 0
DIR_CAP = 40000
stack = [ROOT]
while stack and dirs_seen < DIR_CAP:
    cur = stack.pop()
    dirs_seen += 1
    try:
        it = list(os.scandir(cur))
    except Exception:
        continue
    for entry in it:
        try:
            if entry.is_dir(follow_symlinks=False):
                if entry.name in SKIP:
                    continue
                if _is_reparse(entry):
                    reparse_skipped += 1
                    continue
                stack.append(entry.path)
            elif entry.is_file(follow_symlinks=False):
                low = entry.name.lower()
                if low.endswith('.map'):
                    mapfiles.append(entry.path)
                elif low.endswith(('.pdb', '.dbg', '.sym')):
                    symfound.append(entry.path)
        except Exception:
            continue
p('   DIRS_VISITED', dirs_seen, 'REPARSE_DIRS_SKIPPED', reparse_skipped,
  'STACK_AT_EXIT', len(stack), '(0 => full traversal completed)')
p('   MAP_FILE_COUNT', len(mapfiles))
p('   SYMBOL_FILE_COUNT (pdb/dbg/sym)', len(symfound))
for sf in symfound[:40]:
    p('     SYM', os.path.relpath(sf, ROOT))

# classify map file headers: linker map vs FinalAlert2 game map
p('')
p('[3.6] classification of every .map by header bytes')
hdr_kinds = {}
game_map, linker_map, other = 0, 0, []
for mf in mapfiles:
    try:
        head = open(mf, 'rb').read(160)
    except Exception:
        head = b''
    # FinalAlert2 / RA2 mission maps are INI text with [General]/[Preview]/[Ranking]/[PreviewPack]/[Map] etc.
    hl = head.lstrip()
    if hl.startswith(b'[') or b'[General]' in head or b'[Preview]' in head \
       or b'[PreviewPack]' in head or b'[Ranking]' in head or b'[Basic]' in head \
       or b'[Map]' in head or b'[Gereral]' in head:
        game_map += 1
        kind = 'GAME_MAP(INI-text)'
    elif b'Publics by Value' in head or b'Static symbols' in head \
         or b'Address' in head and b'__' in head or head[:4] == b'MAP\x00':
        linker_map += 1
        kind = 'LINKER_MAP'
        other.append((mf, head[:60]))
    else:
        other.append((mf, head[:60]))
        kind = 'OTHER'
    hdr_kinds[kind] = hdr_kinds.get(kind, 0) + 1
p('   header classification:', hdr_kinds)
p('   -> GAME_MAP(INI-text) count', game_map, '| LINKER_MAP count', linker_map,
  '| OTHER count', len(other) - linker_map)
p('   sample of first 6 map headers:')
for mf in mapfiles[:6]:
    try:
        head = open(mf, 'rb').read(70)
    except Exception:
        head = b''
    p('     ', os.path.relpath(mf, ROOT), '|', repr(head[:60]))
p('   sample of any OTHER (potential linker map) headers:')
for mf, h in other[:15]:
    p('     ', os.path.relpath(mf, ROOT), '|', repr(h[:60]))

p('')
p('=== END OF PROBE ===')
