"""Collect automatic evidence for C01 slice (data rows 1..1292 of function_atlas.tsv).
Outputs:
  EVIDENCE/evidence_raw.json   full per-function evidence (not truncated)
  EVIDENCE/callgraph.json      global callees/callers by function entry
  EVIDENCE/import_map.json     IAT va -> DLL!Func
  EVIDENCE/string_xrefs.json   string va -> [sites]
All disassembly uses capstone skipdata=True. Function bodies use atlas entry+size.
"""
import os, re, json, struct
import pefile
import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
EVID = os.path.join(BASE, 'EVIDENCE')
os.makedirs(EVID, exist_ok=True)
ATLAS = os.path.join(PROJECT, 'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
EXE = os.path.join(PROJECT, 'ra2youli', 'gamemd.exe')
TAB = chr(9)

pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
# sections
secs = []
for s in pe.sections:
    name = s.Name.decode(errors='replace').rstrip('\x00')
    va = IB + s.VirtualAddress
    secs.append(dict(name=name, va=va, vsize=s.Misc_VirtualSize, raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
DATA = pe.__data__
TEXT = next(s for s in secs if s['name']=='.text')
RDATA = next(s for s in secs if s['name']=='.rdata')
DATASEC = next(s for s in secs if s['name']=='.data')

def in_sec(va, s):
    return s['va'] <= va < s['va'] + s['rawsize']

def readva(va, n):
    for s in secs:
        if s['va'] <= va and va+n <= s['va']+s['rawsize']:
            off = s['raw'] + (va - s['va'])
            return DATA[off:off+n]
    return b''

def u32(va):
    b = readva(va,4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None

# ---- IAT map ----
iat = {}
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode(errors='replace')
        for imp in entry.imports:
            if imp.address:
                iat[imp.address] = dll + '!' + (imp.name.decode(errors='replace') if imp.name else ('ord% d'%imp.ordinal))

# ---- atlas ----
with open(ATLAS, encoding='utf-8', errors='replace') as f:
    lines = f.read().splitlines()
hdr = lines[0].split(TAB)
all_rows = []
for ln in lines[1:]:
    p = ln.split(TAB)
    if len(p) < 9: continue
    try:
        e = int(p[0],16)
    except:
        continue
    all_rows.append(dict(entry=e, entryhex=p[0], size=int(p[1]), ninstr=int(p[2]),
                         ncallers=int(p[3]), ncallees=int(p[4]), isfnptr=int(p[5]),
                         first_import=p[6], nstrings=int(p[7] or 0), strings=p[8]))
by_entry = {r['entry']: r for r in all_rows}
slice_rows = all_rows[:1292]
slice_entries = set(r['entry'] for r in slice_rows)

# ---- capstone ----
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def is_ascii_str(va, minlen=3, maxlen=200):
    """If va points to a printable null-terminated ASCII string, return it."""
    if not (in_sec(va,RDATA) or in_sec(va,DATASEC)):
        return None
    b = readva(va, maxlen+1)
    if not b: return None
    z = b.find(b'\x00')
    if z < minlen: return None
    s = b[:z]
    if len(s) > maxlen: return None
    # allow tabs, newlines? keep printable ASCII + common
    if all((32 <= c < 127) or c in (9,10,13) for c in s):
        try: return s.decode('ascii')
        except: return None
    return None

CALL_RE = re.compile(r'^0x([0-9A-Fa-f]+)$')

def analyze_func(row, collect_strings=True):
    e = row['entry']; sz = row['size']
    code = readva(e, sz)
    callees = []
    imports = []
    strings = []
    str_sites = []
    imm_targets = []
    for insn in md.disasm(code, e):
        if insn.id == 0:  # skipdata .byte
            continue
        # direct call/jmp rel32
        if insn.mnemonic in ('call','jmp') and insn.op_str.startswith('0x'):
            tgt = int(insn.op_str,16)
            callees.append(dict(site=insn.address, mnem=insn.mnemonic, target=tgt))
        # indirect call via IAT: call dword ptr [imm]
        if insn.mnemonic == 'call':
            for op in insn.operands:
                if op.type == capstone.x86.X86_OP_MEM:
                    m = op.mem
                    if m.base==0 and m.index==0 and m.disp in iat:
                        imports.append(dict(site=insn.address, iat=m.disp, name=iat[m.disp]))
        # immediates that point to strings
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                val = op.imm & 0xFFFFFFFF
                s = is_ascii_str(val)
                if s:
                    strings.append(dict(site=insn.address, va=val, s=s))
                    str_sites.append(dict(site=insn.address, va=val))
    # dedup strings by (va,s)
    seen=set(); uniq=[]
    for x in strings:
        k=(x['va'],x['s'])
        if k not in seen: seen.add(k); uniq.append(x)
    return dict(callees=callees, imports=imports, strings=uniq, str_sites=str_sites)

def main():
    # Analyze all functions for global callgraph (needed for callers), but strings only for slice
    all_ev = {}
    for idx, row in enumerate(all_rows):
        ev = analyze_func(row, collect_strings=(row['entry'] in slice_entries))
        all_ev[str(row['entry'])] = ev
        if (idx+1) % 2000 == 0:
            print('analyzed', idx+1, '/', len(all_rows))
    # build callers map (only for call targets that are atlas entries)
    callers = {}
    for src, ev in all_ev.items():
        src_e = int(src)
        for c in ev['callees']:
            if c['mnem']=='call' and c['target'] in by_entry:
                callers.setdefault(c['target'], []).append(dict(src=src_e, site=c['site']))
    with open(os.path.join(EVID,'evidence_raw.json'),'w',encoding='utf-8') as f:
        json.dump(all_ev, f, ensure_ascii=False)
    with open(os.path.join(EVID,'callgraph.json'),'w',encoding='utf-8') as f:
        json.dump({str(k):v for k,v in callers.items()}, f, ensure_ascii=False)
    with open(os.path.join(EVID,'import_map.json'),'w',encoding='utf-8') as f:
        json.dump({str(k):v for k,v in iat.items()}, f, ensure_ascii=False, indent=0)
    # summary for slice
    print('slice functions:', len(slice_rows))
    nstr = sum(1 for r in slice_rows if all_ev[str(r['entry'])]['strings'])
    nimp = sum(1 for r in slice_rows if all_ev[str(r['entry'])]['imports'])
    ncall = sum(1 for r in slice_rows if callers.get(r['entry']))
    print('slice with extracted strings:', nstr, 'with imports:', nimp, 'with >=1 caller in image:', ncall)

if __name__ == '__main__':
    main()
