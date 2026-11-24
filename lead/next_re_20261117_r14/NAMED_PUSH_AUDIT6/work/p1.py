import core, sys, json

def show(va, n=120, label=''):
    print('--- dis %s %s' % (hex(va), label))
    for i in core.dis(va, n):
        print('  %08X %-20s %s' % (i['a'], i['b'], i['t']))

if __name__ == '__main__':
    E = 0x006C1010
    body = core.func_body(E)
    # 2) vtable hits for entry
    print('dword hits of entry %08X:' % E)
    for sec, va in core.find_dword(E):
        vt, idx = core.vtable_containing(va)
        r = core.rtti_of_vtable(vt)
        print('  slot@%08X sec=%s vt=%08X idx=%d | COL=%s sig=%s TD=%s name=%s secs=%s/%s' % (
            va, sec, vt, idx, r['col'], r['sig'], r['td'], r['name'], r['col_sec'], r['td_sec']))
        print('     slots:', [('%08X' % a, '%08X' % v if v else None) for a, v in core.vt_first_slots(vt, 6)])
    # 3) QI callee
    print('\nQI callee 00410260 first insns:')
    show(0x410260, 40)
    print('\nctor 00629210:')
    show(0x629210, 90)
