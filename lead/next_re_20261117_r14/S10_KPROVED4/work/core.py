"""S10-KPROVED4 core: self-written PE/RTTI/call-sweep/CFG library.
No import from any other card's work/. Reads gamemd.exe read-only.
"""
import struct, re, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

IMAGE_BASE = 0x400000
_ROOT = None
_p = os.path.abspath(__file__)
for _ in range(8):
    _p = os.path.dirname(_p)
    if os.path.isdir(os.path.join(_p, 'ra2youli')):
        _ROOT = _p
        break
assert _ROOT, 'project root not found'
EXE = os.path.join(_ROOT, 'ra2youli', 'gamemd.exe')


class Bin:
    def __init__(self, path=EXE):
        self.path = path
        self.data = open(path, 'rb').read()
        self.pe = pefile.PE(path, fast_load=True)
        self.pe.parse_data_directories()
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.rstrip(b'\x00').decode('latin1')
            self.sections.append({
                'name': name,
                'va': IMAGE_BASE + s.VirtualAddress,
                'vsize': s.Misc_VirtualSize,
                'raw': s.PointerToRawData,
                'rawsize': s.SizeOfRawData,
            })
        self.text = self.sec('.text')
        self.rdata = self.sec('.rdata')

    def sec(self, name):
        for s in self.sections:
            if s['name'] == name:
                return s
        return None

    def in_sec_va(self, s, va):
        return s is not None and (s['va'] <= va < s['va'] + s['vsize'])

    def in_text(self, va):
        return self.in_sec_va(self.text, va)

    def in_rdata(self, va):
        return self.in_sec_va(self.rdata, va)

    def off(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + s['vsize']:
                d = va - s['va']
                if d < s['rawsize']:
                    return s['raw'] + d
        return None

    def u32(self, va):
        o = self.off(va)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from('<I', self.data, o)[0]

    def i32(self, va):
        v = self.u32(va)
        return None if v is None else struct.unpack('<i', struct.pack('<I', v))[0]

    def u8(self, va):
        o = self.off(va)
        if o is None or o >= len(self.data):
            return None
        return self.data[o]

    def u16(self, va):
        o = self.off(va)
        if o is None or o + 2 > len(self.data):
            return None
        return struct.unpack_from('<H', self.data, o)[0]

    def cstr(self, va, limit=128):
        o = self.off(va)
        if o is None:
            return None
        end = self.data.find(b'\x00', o, min(o + limit, len(self.data)))
        if end < 0:
            end = min(o + limit, len(self.data))
        return self.data[o:end]

    def text_bytes(self):
        s = self.text
        return self.data[s['raw']:s['raw'] + s['rawsize']], s['va']


_NAME_RE = re.compile(rb'^\.?\?A[UV]')


def parse_td_name(b, td):
    """TD+8 inline name string. fail-closed: must start .?AV/.?AU and end @@."""
    name = b.cstr(td + 8, 160)
    if not name:
        return None
    s = name
    if s.startswith(b'.'):
        s = s[1:]
    if not (s.startswith(b'?AV') or s.startswith(b'?AU')):
        return None
    # must be printable and reasonably terminated by @@ (allow trailing)
    if b'@@' not in s:
        return None
    try:
        txt = s.decode('ascii')
    except Exception:
        return None
    if not all(32 <= c < 127 for c in s):
        return None
    return name.decode('ascii')  # e.g. ".?AVFootClass@@"


def valid_col(b, col):
    """COL at col: TD = u32[col+0xC]; name=TD+8 (inline). TD lives in .data typically."""
    td = b.u32(col + 0xC)
    if td is None or not (b.in_rdata(td) or b.in_sec_va(b.sec('.data'), td)):
        return None
    nm = parse_td_name(b, td)
    if nm is None:
        return None
    return td, nm


def build_rtti(bin):
    """Enumerate COL structures, then vtables via dword pointers to COL.

    MSVC layout: dword[vt-4] = address of COL. COL+0xC = TD, TD+8 = inline name.
    We (1) find COL structures in .rdata/.data, (2) scan .rdata for pointers to
    those COLs => vt = ptr_pos+4, (3) read slots forward while in .text.
    """
    b = bin
    s = b.rdata
    lo = s['va']
    hi = s['va'] + s['vsize']
    # (1) COL structures: scan .rdata and .data 4-aligned
    cols = {}
    for secname in ('.rdata', '.data'):
        sc = b.sec(secname)
        clo = sc['va']
        chi = sc['va'] + sc['vsize']
        for a in range(clo & ~3, chi - 0x14, 4):
            r = valid_col(b, a)
            if not r:
                continue
            td, nm = r
            sig = b.u32(a)
            selfp = b.u32(a + 0x10)
            strength = 2 if selfp == a else (1 if sig in (0, 1) else 0)
            if strength == 0:
                continue
            cols[a] = {'col': a, 'td': td, 'name': nm, 'sig': sig, 'self': selfp, 'strength': strength}
    coladdrs = set(cols.keys())
    # (2) vtable anchors: .rdata dword == a COL address
    vtables = []
    seen_vt = set()
    for p in range(lo & ~3, hi - 4, 4):
        val = b.u32(p)
        if val is None or val not in coladdrs:
            continue
        v = p + 4
        if v in seen_vt:
            continue
        seen_vt.add(v)
        c = cols[val]
        slots = []
        off = 0
        for k in range(0, 700):
            x = b.u32(v + off)
            if x is None or not b.in_text(x):
                break
            slots.append(x)
            off += 4
        vtables.append({'vt': v, 'col': val, 'td': c['td'], 'name': c['name'],
                        'strength': c['strength'], 'slots': slots})
    return {'cols': cols, 'vtables': vtables}


def holding_tables(bin, rtti, entry):
    """All (vt, slot, class) where vt[slot]==entry, using validated vtables."""
    out = []
    for t in rtti['vtables']:
        for k, val in enumerate(t['slots']):
            if val == entry:
                out.append({'vt': t['vt'], 'slot': k, 'byte_off': k * 4,
                            'col': t['col'], 'td': t['td'], 'name': t['name'],
                            'strength': t['strength']})
    return out


# class hierarchy (most-derived -> base) for S10 relevance
_HIER = {
    'UnitClass': 'FootClass', 'InfantryClass': 'FootClass', 'AircraftClass': 'FootClass',
    'FootClass': 'TechnoClass', 'BuildingClass': 'TechnoClass',
    'TechnoClass': 'MissionClass', 'MissionClass': 'ObjectClass',
    'ObjectClass': 'AbstractClass',
}


def cls_short(name):
    if not name:
        return '?'
    m = re.search(r'\.?\?A[UV](\w+?)@@', name)
    return m.group(1) if m else name


def ancestors(cls):
    out = [cls]
    while cls in _HIER and _HIER[cls] not in out:
        cls = _HIER[cls]
        out.append(cls)
    return out


def attribute_base(holders):
    """M1/错源16: if 2+ tables hold same slot -> base-class level.
    The base class is the LEAST-derived class that holds the slot, i.e. the class
    that is an ANCESTOR of every other holder class (where the method was introduced).
    Return (attributed_class_short, note)."""
    if not holders:
        return None, 'no-holders'
    slots = set(h['slot'] for h in holders)
    classes = set(cls_short(h['name']) for h in holders)
    if len(holders) >= 2 and len(slots) == 1:
        slot = next(iter(slots))
        # base = the holder that is an ancestor of ALL other holders
        cands = [c for c in classes
                 if all(c in ancestors(o) for o in classes if o != c)]
        if cands:
            # if several (partial hierarchy), pick the one closest to root (longest chain)
            base = sorted(cands, key=lambda c: len(ancestors(c)), reverse=True)[0]
            return base, f'{len(holders)} tables same slot{slot} -> base class (rule16)'
        # fallback: least-derived by hierarchy depth
        base = sorted(classes, key=lambda c: len(ancestors(c)), reverse=True)[0]
        return base, f'{len(holders)} tables same slot{slot} -> base (approx)'
    if len(holders) == 1:
        return cls_short(holders[0]['name']), '1 table'
    return cls_short(holders[0]['name']), 'multi tables diff slot (manual)'


def sweep_calls(bin):
    """Full .text linear sweep with skipdata; return instruction boundaries and E8 calls."""
    data, base = bin.text_bytes()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    md.skipdata = True
    boundaries = set()
    calls = {}
    n_ins = 0
    for ins in md.disasm(data, base):
        boundaries.add(ins.address)
        n_ins += 1
        if len(ins.bytes) == 5 and ins.bytes[0] == 0xE8:
            rel = struct.unpack('<i', ins.bytes[1:5])[0]
            tgt = ins.address + 5 + rel
            calls[ins.address] = tgt
    return {'n_ins': n_ins, 'boundaries': boundaries, 'calls': calls,
            'n_e8': sum(1 for x in data if x == 0xE8)}


def verify_sites(sweeps, entry, site_list):
    """For each site: E8 at boundary + rel32==entry + outside function body."""
    out = []
    for s in site_list:
        site = int(s, 16) if isinstance(s, str) else s
        row = {'site': f'{site:08X}'}
        row['at_boundary'] = site in sweeps['boundaries']
        row['is_e8'] = sweeps.get('e8_map', {}).get(site, None)
        tgt = sweeps['calls'].get(site)
        row['target'] = f'{tgt:08X}' if tgt is not None else None
        row['target_ok'] = (tgt == entry)
        out.append(row)
    return out


class FuncMap:
    """Global function-start map: all E8 call targets + vtable slots + explicit entries.
    Function extent = [entry, next known start). Avoids disassembly bleeding into
    the next function (which 'stop after N rets' does)."""
    def __init__(self, bin, rtti, sweep):
        starts = set(sweep['calls'].values())           # all E8 direct targets
        for t in rtti['vtables']:
            for v in t['slots']:
                starts.add(v)
        self.starts = sorted(s for s in starts if bin.in_text(s))
        self.startset = set(self.starts)
        import bisect
        self.bisect = bisect

    def extent(self, entry, cap=0x8000):
        i = self.bisect.bisect_right(self.starts, entry)
        nxt = self.starts[i] if i < len(self.starts) else entry + cap
        if nxt - entry > cap:
            nxt = entry + cap
        return entry, nxt


def disasm_range(bin, start, end, detail=True):
    """Linear disassembly of [start,end) with skipdata."""
    o = bin.off(start)
    if o is None:
        return []
    n = end - start
    data = bin.data[o:o + n]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = detail
    md.skipdata = True
    return list(md.disasm(data, start))


def disasm_window(bin, entry, max_bytes=8192):
    """Legacy wrapper: stop after 3 ret (kept for backward compat)."""
    o = bin.off(entry)
    if o is None:
        return []
    data = bin.data[o:o + max_bytes]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    insns = []
    rets = 0
    for ins in md.disasm(data, entry):
        insns.append(ins)
        if ins.mnemonic == 'ret' or ins.mnemonic.startswith('retf'):
            rets += 1
            if rets >= 3 and len(insns) >= 16:
                break
    return insns
