"""Compact per-row report for AUDIT6."""
import core, sys, struct
from check import body_analysis, find_main_vtable_of_ctor, is_vtval, QI, HOST, NEW

def hx(v):
    return '%08X' % v if v else '--------'

def row(E):
    out = []
    ins, r = body_analysis(E)
    out.append('== %08X  n_insn=%d skipdata=%d last=%s' % (E, r['n_insn'], r['skipdata'], r['last']))
    for a, imm, b in r['imms']:
        out.append('   imm  %08X  mov eax,%s   [%s]' % (a, imm, b))
    # QI-ish slot0 dispatch
    seen = set()
    for it in r['qi_sites']:
        if len(it) == 4:
            a, t, b, seq = it
            seen.add(a)
            out.append('   QI?  %08X  %-26s [%s]' % (a, t, b))
            out.append('        next: ' + ' | '.join(seq[1:4]))
    for it in r['qi_sites']:
        if len(it) == 3 and it[0] not in seen:
            a, t, b = it
            out.append('   disp %08X  %-26s [%s]' % (a, t, b))
    out.append('   rets ' + ' '.join('%08X:%s' % (a, t) for a, t, b in r['rets']))
    # B slots
    for sec, va in core.find_dword(E):
        vt, idx = core.vtable_containing(va)
        ri = core.rtti_of_vtable(vt)
        out.append('   SLOT %08X sec=%-7s vt=%08X idx=%d sig=%s COL=%s TD=%s name=%s vt0=%s'
                   % (va, sec, vt, idx, ri['sig'], hx(ri['col']), hx(ri['td']), ri['name'], hx(core.u32(vt))))
    # C object ctor: try every direct call target in .text, keep those that write a vtable to [this]
    for a, t, b in r['calls']:
        if not t.startswith('call 0x'):
            continue
        tgt = int(t.split('0x')[1], 16)
        if not core.in_text(tgt) or tgt == NEW:
            continue
        this_reg, w0, wN, _ = find_main_vtable_of_ctor(tgt)
        tag = 'OBJCTOR' if (w0 and core.u32(w0[-1][2]) == QI) else 'calltgt'
        out.append('   %s call @%08X -> %08X  this=%s' % (tag, a, tgt, this_reg))
        if w0:
            out.append('     writes[this+0]: %s' % (' ; '.join('%08X:%s=%08X' % (x[0], x[1], x[2]) for x in w0)))
        if wN:
            out.append('     writes[member]: %s' % (' ; '.join('%08X:%s=%08X' % (x[0], x[1], x[2]) for x in wN)))
        if w0:
            main = w0[-1][2]
            ri = core.rtti_of_vtable(main)
            out.append('     MAIN vt=%08X vt0=%s name=%s COL=%s sig=%s' % (main, hx(core.u32(main)), ri['name'], hx(ri['col']), ri['sig']))
            for x in wN:
                out.append('       member-tbl %08X vt0=%s name=%s' % (x[2], hx(core.u32(x[2])), core.rtti_of_vtable(x[2])['name']))
    return '\n'.join(out)

if __name__ == '__main__':
    for e in sys.argv[1:]:
        print(row(int(e, 16)))
        print()
