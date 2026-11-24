"""S05-K1 master analysis: class-chain recovery, RTTI, GetSize, init points.
Read-only on gamemd.exe. Writes JSON results into ../EVIDENCE/.
All decoding uses capstone with skipdata=True (discipline #2).
"""
import pefile, struct, os, json, hashlib

ROOT = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge')
PE_PATH = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
OUT_DIR = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'S05-K1', 'EVIDENCE')
os.makedirs(OUT_DIR, exist_ok=True)

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True

pe = pefile.PE(PE_PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode('ascii', 'replace')
    SECS.append({'name': nm, 'va': s.VirtualAddress + IB, 'vs': s.Misc_VirtualSize,
                 'raw': s.PointerToRawData, 'rs': s.SizeOfRawData})
DATA = open(PE_PATH, 'rb').read()

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()

def off(va):
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vs'], s['rs']):
            d = va - s['va']
            if d < s['rs']:
                return s['raw'] + d
    return None

def sec_of(va):
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vs'], s['rs']):
            return s['name']
    return None

def rd(va):
    o = off(va)
    if o is None or o + 4 > len(DATA):
        return None
    return struct.unpack_from('<I', DATA, o)[0]

def rdstr(va, n=140):
    o = off(va)
    if o is None:
        return None
    return DATA[o:o+n].split(b'\0')[0].decode('ascii', 'replace')

def demangle(name):
    """Minimal demangle of .?AVClass@@ / .?AUName@@ -> Name (strip prefixes/suffix)."""
    if not name:
        return None
    if name.startswith('.?AV') or name.startswith('.?AU'):
        inner = name[4:]
        if inner.endswith('@@'):
            inner = inner[:-2]
        # template names like ?$X@Y@@ -> leave as-is for now
        return inner
    return name

TEXT_VA = next(s['va'] for s in SECS if s['name'] == '.text')
TEXT_END = TEXT_VA + next(s['vs'] for s in SECS if s['name'] == '.text')
RDATA_VA = next(s['va'] for s in SECS if s['name'] == '.rdata')
RDATA_END = RDATA_VA + next(s['vs'] for s in SECS if s['name'] == '.rdata')

def td_name(td):
    if not td:
        return None
    # sanity: TD+0 should be type_info vftable 0x7F9594 (KB), TD+8 name string
    vft = rd(td)
    nm = rdstr(td + 8)
    return nm

def col_to_td(col):
    """Return (td, name, ok, reason) with fail-closed."""
    if not col or sec_of(col) not in ('.rdata', '.data'):
        return None, None, False, 'col-not-in-rdata/data'
    td = rd(col + 0xC)
    if not td or sec_of(td) not in ('.rdata', '.data'):
        return td, None, False, 'td-ptr-invalid'
    nm = td_name(td)
    if not nm or not (nm.startswith('.?AV') or nm.startswith('.?AU')):
        return td, nm, False, 'td-name-invalid'
    return td, nm, True, ''

def parse_chd(col):
    chd = rd(col + 0x10)
    res = {'chd': chd, 'ok': False, 'bases': []}
    if not chd or sec_of(chd) not in ('.rdata', '.data'):
        res['reason'] = 'chd-ptr-invalid'; return res
    nbase, parr = rd(chd + 8), rd(chd + 0xC)
    res['nbase'], res['parr'] = nbase, parr
    if nbase is None or parr is None or not (0 <= nbase <= 64):
        res['reason'] = 'nbase-parr-invalid'; return res
    for i in range(nbase):
        bcd = rd(parr + 4*i)
        btd = rd(bcd) if bcd else None
        bnm = td_name(btd) if btd else None
        res['bases'].append({'bcd': bcd, 'btd': btd, 'name': bnm, 'short': demangle(bnm)})
    res['ok'] = True
    return res

def slot_count(vt, maxn=3000):
    n = 0; stop = None
    for i in range(maxn):
        val = rd(vt + 4*i)
        if val is None:
            stop = {'i': i, 'val': None, 'sec': None}; break
        s = sec_of(val)
        if s == '.text':
            n += 1
        else:
            stop = {'i': i, 'val': '%08X' % val, 'sec': s}
            break
    return n, stop

def decode_one(va, count=12):
    o = off(va)
    if o is None:
        return None
    buf = DATA[o:o+64]
    out = []
    for insn in MD.disasm(buf, va):
        out.append({'va': '%08X' % insn.address, 'bytes': insn.bytes.hex(),
                    'mn': insn.mnemonic, 'op': insn.op_str})
        if len(out) >= count:
            break
    return out

def get_imm_ret(va):
    """If function at va is B8 <imm32> C3, return imm; else None."""
    o = off(va)
    if o is None or o + 6 > len(DATA):
        return None
    b = DATA[o:o+6]
    if b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack_from('<I', b, 1)[0]
    return None

# ---- engine type-id name table at 0x816EE0: {char* name, u32 value} x74 ----
def read_type_table():
    tbl = {}
    base = 0x816EE0
    for i in range(74):
        np = rd(base + 8*i)
        val = rd(base + 8*i + 4)
        if np and val is not None:
            nm = rdstr(np)
            if nm:
                tbl[val] = nm
    return tbl

TYPE_TABLE = read_type_table()

TARGETS = [
    ('AbstractClass', 0x7E1F50), ('ObjectClass', 0x7EF060),
    ('MissionClass', 0x7EDCC0), ('RadioClass', 0x7F0508),
    ('TechnoClass', 0x7F4960), ('FootClass', 0x7E8C94),
    ('BuildingClass', 0x7E3EBC), ('UnitClass', 0x7F5C70),
    ('InfantryClass', 0x7EB058), ('AircraftClass', 0x7E22A4),
]

result = {
    'sha256': sha(PE_PATH), 'image_base': '0x%X' % IB,
    'sections': SECS,
    'type_table_count': len(TYPE_TABLE),
    'classes': [],
}

for name_hint, vt in TARGETS:
    col = rd(vt - 4)
    td, nm, ok, reason = col_to_td(col)
    chd = parse_chd(col) if col else None
    sc, stop = slot_count(vt)
    v11, v12 = rd(vt + 11*4), rd(vt + 12*4)
    imm11 = get_imm_ret(v11) if v11 else None
    imm12 = get_imm_ret(v12) if v12 else None
    entry = {
        'hint': name_hint, 'vtable': '0x%08X' % vt,
        'col': ('0x%08X' % col) if col else None,
        'td': ('0x%08X' % td) if td else None,
        'name_rtti': demangle(nm) if ok else ('?' if nm is None else demangle(nm)),
        'name_raw': nm, 'rtti_ok': ok, 'rtti_reason': reason,
        'slot_count': sc, 'slot_stop': stop,
        'v11': ('0x%08X' % v11) if v11 else None,
        'v12': ('0x%08X' % v12) if v12 else None,
        'whatami_id': imm11, 'whatami_name': TYPE_TABLE.get(imm11) if imm11 is not None else None,
        'getsize_imm': imm12,
        'chd': chd,
        'v12_code': decode_one(v12, 8) if v12 else None,
    }
    result['classes'].append(entry)
    print('%-14s %-16s slots=%-4d getsize=%-8s whatami=%-6s(%s) parent=%s' % (
        name_hint, entry['name_rtti'], sc,
        ('0x%X'%imm12) if imm12 is not None else ('STUB' if v12==0x4C9150 else 'NOIMM'),
        ('0x%X'%imm11) if imm11 is not None else '?',
        entry['whatami_name'],
        chd['bases'][1]['short'] if chd and chd['ok'] and len(chd['bases'])>1 else '?'))

outp = os.path.join(OUT_DIR, 'class_chain_core.json')
with open(outp, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
print('WROTE', outp)
