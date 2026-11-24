"""Ring-4 verification: host 006BB9A0 factory registration chain per row."""
import core, struct
from check import find_main_vtable_of_ctor, is_vtval, atexit_check, QI
from rowrep import hx

ENTS = ['006C1010','006C1190','006C1310','006C1490','006C1610','006C1790','006C1910','006C1A90',
        '006C1C10','006C1D90','006C1F10','006C2090','006C2210','006C2390','006C2510','006C2690',
        '006C2810','006C2990']

ins = core.func_body(0x006BB9A0)
print('host 006BB9A0: n_insn=%d last=%s' % (len(ins), ins[-1]['t']))
print('IAT[0x7E15D8] =', core.import_at(0x7E15D8))
print('IAT[0x7C8E17] = operator new? %s (in .text: %s)' % (core.import_at(0x7C8E17), core.in_text(0x7C8E17)))

# find all call sites in host to the factory ctors
seqs = []
for k, i in enumerate(ins):
    if i['t'] == 'push 8' and k + 2 < len(ins) and ins[k+1]['t'] == 'call 0x7c8e17':
        item = {'alloc': i['a'], 'newcall': ins[k+1]['a']}
        for j in range(k + 2, min(k + 9, len(ins))):
            t = ins[j]['t']
            if t.startswith('call 0x') and t != 'call 0x7c8e17':
                item['ctor_site'] = ins[j]['a']
                item['ctor'] = int(t.split('0x')[1], 16)
                break
        # registration: push <clsid 0x7E....>; push 1; push 1; push eax; call <reg>
        for j in range(k + 2, min(k + 18, len(ins))):
            t = ins[j]['t']
            if t.startswith('push 0x'):
                v = int(t.split('0x')[1], 16)
                if 0x7E0000 <= v < 0x800000:
                    item['clsid'] = v
                    item['clsid_site'] = ins[j]['a']
                    for m in range(j + 1, min(j + 9, len(ins))):
                        if ins[m]['t'].startswith('call ') and '0x' not in ins[m]['t']:
                            item['reg_site'] = ins[m]['a']
                            item['reg_call'] = ins[m]['t']
                    break
        seqs.append(item)

print('found %d alloc/ctor/register sequences' % len(seqs))
for s in seqs[:3]:
    print(' ', s)

# check the esi source (IAT load) inside host before first reg call
for k, i in enumerate(ins):
    if i['t'].startswith('mov esi, dword ptr [0x'):
        print('esi load %08X %s' % (i['a'], i['t']))
        break

print()
print('%-9s %-9s %-9s %-9s %-9s %-9s %-34s %s' % ('entry','alloc','newcall','ctor','ctorSite','regSite','clsid','ctor_installs_vt'))
rows = []
for e in ENTS:
    E = int(e, 16)
    # entry's own slot
    slot = None
    for sec, va in core.find_dword(E):
        vt, idx = core.vtable_containing(va)
        if core.sec_of(vt) in ('.rdata', '.data') and core.sec_of(vt - 4) in ('.rdata', '.data'):
            slot = (va, vt, idx)
    match = None
    for s in seqs:
        c = s.get('ctor')
        if c is None:
            continue
        this_reg, w0, wN, _ = find_main_vtable_of_ctor(c)
        installed = [x[2] for x in w0]
        if slot and slot[1] in installed:
            match = (s, installed, this_reg)
            break
    if match:
        s, installed, this_reg = match
        rows.append((e, s, installed, this_reg, slot))
        print('%-9s %08X %08X %08X %08X %08X   %08X                        %s' % (
            e, s['alloc'], s['newcall'], s['ctor'], s['ctor_site'], s.get('reg_site', 0),
            s.get('clsid', 0), ' '.join('%08X' % v for v in installed)))
    else:
        print('%-9s NO MATCH  slot=%s' % (e, slot))

print()
print('host atexit/callers check:')
hits, reg, direct = atexit_check(0x006BB9A0)
print(' dword hits of 006BB9A0:', [(sec, '%08X' % va) for sec, va in hits])
print(' atexit-style:', reg)
print(' direct refs:', [('%08X' % a, k) for a, k in direct])

import json
json.dump([{'entry': e, 'alloc': s['alloc'], 'newcall': s['newcall'], 'ctor': s['ctor'],
            'ctor_site': s['ctor_site'], 'reg_site': s.get('reg_site'), 'clsid': s.get('clsid'),
            'installed': installed, 'this_reg': this_reg,
            'slot_va': slot[0], 'vt': slot[1], 'idx': slot[2]} for e, s, installed, this_reg, slot in rows],
          open('ring4.json', 'w'), indent=1)
