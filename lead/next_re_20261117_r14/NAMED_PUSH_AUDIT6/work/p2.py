import core

def vtinfo(vt, label=''):
    r = core.rtti_of_vtable(vt)
    print('%-10s vt=%08X COL=%08X sig=%s TD=%08X name=%r secs=%s/%s' % (
        label, vt, r['col'] or 0, r['sig'], r['td'] or 0, r['name'], r['col_sec'], r['td_sec']))
    print('           slots:', ' '.join('%08X:%08X' % (a, v or 0) for a, v in core.vt_first_slots(vt, 10)))
    return r

print('=== factory vtable (row1) ===')
vtinfo(0x007F3978, 'FACTORY')
print()
print('=== new-object main vtable ===')
vtinfo(0x007EF890, 'OBJ-MAIN')
print('  member tables written by ctor:')
for v in (0x007EF874, 0x007EF86C, 0x007EF864):
    print('   %08X ->' % v, ' '.join('%08X' % (core.u32(v + 4 * i) or 0) for i in range(8)),
          '| name=', core.rtti_of_vtable(v)['name'])
print()
print('=== QI 00410260 tail: all ret + mov eax,imm ===')
for i in core.dis(0x410260, 200, stop_at_ret=False):
    t = i['t']
    if t.startswith('ret') or (t.startswith('mov eax, 0x') ) or t.startswith('xor eax'):
        print('  %08X %-16s %s' % (i['a'], i['b'], t))
