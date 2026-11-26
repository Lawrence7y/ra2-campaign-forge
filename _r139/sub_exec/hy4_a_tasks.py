import os, re, hashlib, struct
from collections import Counter
import pefile

OUT = []
def p(s=''):
    OUT.append(str(s))

path = 'ra2bench/gamemd.exe'
data = open(path, 'rb').read()
p('=== A-TASKS COMMAND ===')
p('python3 /tmp/r139hy4/a_tasks.py')
p('=== SCRIPT SOURCE SHA256 ===')
p(hashlib.sha256(open(__file__, 'rb').read()).hexdigest())
p('=== BINARY ===')
p('path=' + path)
p('size=' + str(len(data)))
p('sha256=' + hashlib.sha256(data).hexdigest())

pe = pefile.PE(path)
IB = pe.OPTIONAL_HEADER.ImageBase
def cstr_at_off(off):
    end = data.find(b'\x00', off)
    return data[off:end].decode('latin1')

def cstr_at_rva(rva):
    return cstr_at_off(pe.get_offset_from_rva(rva))

sections = []
for s in pe.sections:
    name = s.Name.decode('latin1').rstrip('\x00')
    sections.append(dict(name=name, va=s.VirtualAddress, vsize=s.Misc_VirtualSize,
                         raw=s.PointerToRawData, rsize=s.SizeOfRawData))
p('=== SECTION TABLE (reprinted before any VA conversion) ===')
p('ImageBase=' + hex(IB))
for s in sections:
    p(f"{s['name']} VA={hex(s['va'])} VSize={hex(s['vsize'])} RawPtr={hex(s['raw'])} RawSize={hex(s['rsize'])}")

def sec_for_off(off, length=1):
    for s in sections:
        if s['raw'] <= off and off + length <= s['raw'] + s['rsize']:
            return s
    return None

def sec_for_va(va, length=1):
    rva = va - IB
    for s in sections:
        if s['va'] <= rva and rva + length <= s['va'] + s['vsize']:
            return s
    return None

# ---------------- A1 ----------------
p('')
p('=== A1 ===')
prefix = b'.?AV?$TClassFactory@'
rx = re.compile(re.escape(prefix) + rb'([ -~]{1,120}?)@@')
matches = list(rx.finditer(data))
p('regex=' + repr(rx.pattern))
p('total_matches=' + str(len(matches)))
xs = [m.group(1).decode('latin1') for m in matches]
cnt = Counter(xs)
p('unique_template_args=' + str(len(cnt)))
p('all_unique_count_1=' + str(all(v == 1 for v in cnt.values())))
p('per_arg_counts=' + repr(sorted(cnt.items())))
secdist = Counter()
for m in matches:
    s = sec_for_off(m.start(), m.end() - m.start())
    secdist[s['name'] if s else 'UNMAPPED'] += 1
p('section_distribution=' + repr(dict(secdist)))
p('sample_full_names=' + repr([m.group(0).decode('latin1') for m in matches[:5]]))
p('boundary_rule=A1 match attributed to a section only when the whole match lies inside that section raw range')

# ---------------- A2 ----------------
p('')
p('=== A2 ===')
pat2 = bytes.fromhex('B801000000C20400')
p('pattern_hex=' + pat2.hex().upper())
offs = []
start = 0
while True:
    i = data.find(pat2, start)
    if i < 0:
        break
    offs.append(i)
    start = i + 1
p('whole_file_count=' + str(len(offs)))
c_text = c_other = c_cross = 0
details = []
for o in offs:
    s = sec_for_off(o, len(pat2))
    if s is None:
        c_cross += 1
        lab = 'CROSS_OR_UNMAPPED'
    elif s['name'] == '.text':
        c_text += 1
        lab = '.text'
    else:
        c_other += 1
        lab = s['name']
    details.append((hex(o), lab))
p('in_text=' + str(c_text))
p('in_other_sections=' + str(c_other))
p('cross_section_or_unmapped=' + str(c_cross))
p('details=' + repr(details))
p('boundary_rule=only hits fully closed inside a single raw section are attributed to that section; otherwise counted as cross-boundary')

# ---------------- A3 ----------------
p('')
p('=== A3 ===')
pat3 = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
p('pattern_hex=' + pat3.hex().upper())
offs3 = []
start = 0
while True:
    i = data.find(pat3, start)
    if i < 0:
        break
    offs3.append(i)
    start = i + 1
p('count=' + str(len(offs3)))
for o in offs3:
    s = sec_for_off(o, len(pat3))
    va = IB + s['va'] + (o - s['raw']) if s else None
    p(f'offset={hex(o)} file_va={hex(va) if va is not None else "NA"} section={s["name"] if s else "UNMAPPED"}')
for va in (0x6C2AC0, 0x6C51C0):
    off = va - IB
    s = sec_for_va(va, len(pat3))
    raws = sec_for_off(off, len(pat3))
    seg = data[off:off + len(pat3)]
    p(f'check_va={hex(va)} mapped_off={hex(off)} section_by_va={s["name"] if s else "NA"} section_by_off={raws["name"] if raws else "NA"} bytes={seg.hex().upper()} equals_pattern={seg == pat3}')
p('compare_two_sites=' + str(data[0x6C2AC0-IB:0x6C2AC0-IB+len(pat3)] == data[0x6C51C0-IB:0x6C51C0-IB+len(pat3)]))
p('conversion_rule=for .text VA==RawPtr, so file_off = VA - ImageBase; VA = ImageBase + sectionVA + (file_off - RawPtr)')

# ---------------- A4 ----------------
p('')
p('=== A4 ===')
dd = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
p(f'import_dir_rva={hex(dd.VirtualAddress)} size={hex(dd.Size)}')
desc_off = pe.get_offset_from_rva(dd.VirtualAddress)
target = 0x7E11C8
found = None
g0 = 0
dll_count = 0
while True:
    vals = struct.unpack_from('<5I', data, desc_off)
    if vals == (0, 0, 0, 0, 0):
        break
    oft, ts, fc, name_rva, ft = vals
    dll = cstr_at_rva(name_rva)
    dll_count += 1
    ilt = oft if oft else ft
    idx = 0
    while True:
        thunk_rva = ilt + 4 * idx
        try:
            entry = struct.unpack_from('<I', data, pe.get_offset_from_rva(thunk_rva))[0]
        except Exception:
            break
        if entry == 0:
            break
        if entry & 0x80000000:
            hint = None
            fname = 'ORDINAL:%d' % (entry & 0xFFFF)
        else:
            hn_off = pe.get_offset_from_rva(entry)
            hint = struct.unpack_from('<H', data, hn_off)[0]
            fname = cstr_at_rva(entry + 2)
        iat_va = IB + ft + 4 * idx
        if iat_va == target:
            found = dict(dll=dll, func=fname, hint=hint, idx_in_dll=idx,
                         global0=g0, global1=g0 + 1,
                         thunk_rva=hex(thunk_rva), iat_rva=hex(ft + 4 * idx))
        idx += 1
        g0 += 1
    desc_off += 20
p('dll_descriptor_count=' + str(dll_count))
p('total_import_entries=' + str(g0))
p('target_iat_va=' + hex(target) + ' target_rva=' + hex(target - IB))
p('found=' + repr(found))
p('idx_dll_0based=' + (str(found['idx_in_dll']) if found else 'NA'))
p('idx_global_0based=' + (str(found['global0']) if found else 'NA'))
p('idx_global_1based=' + (str(found['global1']) if found else 'NA'))

p('')
p('=== OUTPUT_LINES ===')
p(str(len(OUT) + 1))
print('\n'.join(OUT))
