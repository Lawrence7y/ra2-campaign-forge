"""Ring-4 per-row verification: host alloc/ctor/CoRegisterClassObject, factory vtable install, ㉓."""
import core, idx, json
from verify import factory_ctor_vt, hx

ENTS = ['006C1010','006C1190','006C1310','006C1490','006C1610','006C1790','006C1910','006C1A90',
        '006C1C10','006C1D90','006C1F10','006C2090','006C2210','006C2390','006C2510','006C2690',
        '006C2810','006C2990']
HOST = 0x006BB9A0

host = idx.body(HOST)
seqs = []
for k, x in enumerate(host):
    if x['t'] == 'push 8':
        item = {'alloc': '%08X' % x['a']}
        for j in range(k + 1, min(k + 4, len(host))):
            if host[j]['t'].startswith('call 0x'):
                item['new'] = '%08X' % host[j]['a']
                break
        for j in range(k + 2, min(k + 9, len(host))):
            t = host[j]['t']
            if t.startswith('call 0x') and t != 'call 0x7c8e17':
                item['ctor_site'] = '%08X' % host[j]['a']
                item['ctor'] = int(t.split('0x')[1], 16)
                break
        for j in range(k + 2, min(k + 18, len(host))):
            t = host[j]['t']
            if t.startswith('push 0x'):
                v = int(t.split('0x')[1], 16)
                if 0x7E0000 <= v < 0x800000:
                    item['clsid'] = '%08X' % v
                    for m in range(j + 1, min(j + 9, len(host))):
                        if host[m]['t'].startswith('call ') and '0x' not in host[m]['t']:
                            item['reg_site'] = '%08X' % host[m]['a']
                            item['reg'] = host[m]['t']
                    break
        seqs.append(item)
print('host 006BB9A0 range=%s n_insn=%d last=%s sequences=%d' % (
    ['%08X' % v for v in idx.func_range(HOST)], len(host), host[-1]['t'], len(seqs)))
print('callers of host:', ['%08X' % c for c in idx.callers(HOST)])
print('push-imm sites of host:', ['%08X' % c for c in idx.push_sites(HOST)])
print('atexit registration of host:', idx.atexit_registered(HOST))
w = idx.last_writer_of_reg(host, 'esi')
print('esi last writer in host: %08X %s' % (w['a'], w['t']))
print()

res = {}
for e in ENTS:
    E = int(e, 16)
    slot = None
    for sec, va in core.find_dword(E):
        vt, ix = core.vtable_containing(va)
        ri = core.rtti_of_vtable(vt)
        slot = {'slot': '%08X' % va, 'vt': '%08X' % vt, 'idx': ix, 'name': ri['name']}
        break
    V = int(slot['vt'], 16)
    match = None
    for s in seqs:
        if 'ctor' not in s:
            continue
        reg, w0, wN, cins = factory_ctor_vt(s['ctor'])
        inst = [v for a, m, v, b in w0]
        if V in inst:
            match = (s, reg, w0, cins)
            break
    rec = {'entry': e, 'slot': slot}
    if match:
        s, reg, w0, cins = match
        rec.update({'alloc': s.get('alloc'), 'new': s.get('new'), 'ctor': '%08X' % s['ctor'],
                    'ctor_site': s.get('ctor_site'), 'clsid': s.get('clsid'),
                    'reg_site': s.get('reg_site'), 'reg': s.get('reg'),
                    'ctor_this': reg,
                    'ctor_w0': [('%08X' % a, m, '%08X' % v) for a, m, v, b in w0],
                    'ctor_n_insn': len(cins), 'ctor_last': cins[-1]['t'],
                    'ctor_callers': ['%08X' % c for c in idx.callers(s['ctor'])],
                    'ctor_atexit': idx.atexit_registered(s['ctor']),
                    'ctor_range': ['%08X' % v for v in idx.func_range(s['ctor'])]})
        # slot3 check on the exact installed vtable
        rec['vt_slot3'] = '%08X' % core.u32(V + 12)
        rec['vt_slot3_ok'] = (core.u32(V + 12) == E)
        # does the ctor write OTHER vtables at [this] too? (chained base ctors)
        rec['all_installed'] = ['%08X' % v for v in [wm[2] for wm in w0]]
    res[e] = rec

for e in ENTS:
    r = res[e]
    print('%-9s slot=%s idx=%d vt=%s idx3ok=%s | alloc=%s ctor=%s@%s reg=%s clsid=%s | ctor_writes=%s | calls=%s | atexit=%s' % (
        e, r['slot']['slot'], r['slot']['idx'], r['slot']['vt'], r.get('vt_slot3_ok'),
        r.get('alloc'), r.get('ctor'), r.get('ctor_site'), r.get('reg_site'), r.get('clsid'),
        ','.join(x[2] for x in r.get('ctor_w0', [])), ','.join(r.get('ctor_callers', [])), r.get('ctor_atexit')))
json.dump(res, open('ring4b.json', 'w'), indent=1)
print()
print('distinct alloc:', len(set(r.get('alloc') for r in res.values())))
print('distinct ctor:', len(set(r.get('ctor') for r in res.values())))
print('distinct reg_site:', len(set(r.get('reg_site') for r in res.values())))
print('distinct clsid:', len(set(r.get('clsid') for r in res.values())))
