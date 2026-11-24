"""Adversarial checks: factory slot0 is a real QI, COL offsets, tricky ctors."""
import core, idx, json

def col_fields(col):
    # RTTICompleteObjectLocator32: sig, offset, cdOffset, pTD, pCHD, pSelf
    return {'sig': core.u32(col), 'offset': core.u32(col + 4), 'cdOffset': core.u32(col + 8),
            'pTD': core.u32(col + 0xC), 'pCHD': core.u32(col + 0x10),
            'pSelf': core.u32(col + 0x14), 'self_ok': core.u32(col + 0x14) == col}

rows = json.load(open('rows_all.json'))
print('=== factory vtable slot0 sanity + COL fields ===')
for e, r in rows.items():
    vt = int(r['slots'][0]['vt'], 16)
    slot0 = core.u32(vt)
    col = core.u32(vt - 4)
    f = col_fields(col)
    # does slot0 look like QueryInterface? first insn reads a stack arg and compares with 16-byte GUID
    head = idx.dis_at(slot0, 6)
    is_qi = any('cmpsd' in h for h in idx.dis_at(slot0, 40)) and any('mov eax, dword ptr [esp' in h for h in head[:3])
    print('%s vt=%08X slot0=%08X qi_shape=%s COL=%08X sig=%d offset=%d cd=%d self_ok=%s' % (
        e, vt, slot0, is_qi, col, f['sig'], f['offset'], f['cdOffset'], f['self_ok']))

print()
print('=== object main vtable COL fields ===')
for e, r in rows.items():
    vt = int(r['obj_main']['vt'], 16)
    col = core.u32(vt - 4)
    f = col_fields(col)
    print('%s obj vt=%08X vt0=%08X COL=%08X sig=%d offset=%d cd=%d self_ok=%s name=%s' % (
        e, vt, core.u32(vt), col, f['sig'], f['offset'], f['cdOffset'], f['self_ok'], r['obj_main']['name']))

print()
print('=== row 12 ctor 006E5B60 (this=ebp?) ===')
for l in idx.dis_at(0x6E5B60, 16):
    print('  ', l)
print('  ... write site context:')
for l in idx.dis_at(0x6E5B80, 8):
    print('  ', l)
print()
print('=== row 18 ctor 0045DD90 tail writes around 0045E2C0 ===')
for l in idx.dis_at(0x45E2B5, 10):
    print('  ', l)
print()
print('=== QI 00410260: interface table it compares against ===')
for l in idx.dis_at(0x410260, 8):
    print('  ', l)
print('  IID target 007F7C90:', core.read(0x7F7C90, 16).hex())
print('  IID target 007E9AE0:', core.read(0x7E9AE0, 16).hex())
print()
print('=== slot4 of factory vtable (row1) 006C1090 ===')
for l in idx.dis_at(0x6C1090, 10):
    print('  ', l)
