"""Definitive per-row verification (boundary-limited) for S22_B2 18 rows."""
import core, idx, json, sys

QI = 0x410260
HOST = 0x006BB9A0
NEW = 0x7C8E17
CO_REG_IAT = 0x7E15D8


def hx(v):
    return '%08X' % v if v else '--------'


def is_vtval(v):
    return v is not None and 0x7C0000 <= v < 0x807000 and core.sec_of(v) in ('.rdata', '.data')


def imm_writes_to(insns, this_reg):
    """All `mov dword ptr [<mem>], imm` where imm looks like a vtable."""
    w0, wN = [], []
    for x in insns:
        t = x['t']
        if not t.startswith('mov dword ptr ['):
            continue
        try:
            mem, val = t[len('mov dword ptr '):].split(', ')
        except ValueError:
            continue
        if not val.startswith('0x'):
            continue
        v = int(val, 16)
        if not is_vtval(v):
            continue
        rec = (x['a'], mem, v, x['b'])
        if this_reg and mem == '[%s]' % this_reg:
            w0.append(rec)
        else:
            wN.append(rec)
    return w0, wN


def factory_ctor_vt(ctor):
    ins = idx.body(ctor)
    this_reg = None
    for x in ins[:14]:
        m = x['t']
        if m.startswith('mov ') and m.endswith(', ecx'):
            cand = m.split(' ')[1].split(',')[0]
            if cand in ('esi', 'edi', 'ebx', 'ebp', 'eax', 'edx'):
                this_reg = cand
                break
    w0, wN = imm_writes_to(ins, this_reg)
    return this_reg, w0, wN, ins


def analyze(E):
    r = {'entry': '%08X' % E}
    ins = core.func_body(E)
    r['n_insn'] = len(ins)
    r['skipdata'] = sum(1 for i in ins if i['skip'])
    r['last'] = ins[-1]['t'] if ins else None
    r['first'] = ins[0]['t'] if ins else None
    r['range'] = ['%08X' % x for x in idx.func_range(E)]
    r['callers'] = ['%08X' % c for c in idx.callers(E)]
    r['imms'] = [(('%08X' % a), t, b) for a, t, b in
                 [(i['a'], i['t'], i['b']) for i in ins if i['t'].startswith('mov eax, 0x')]]
    # dispatch sites
    r['disp'] = []
    for k, i in enumerate(ins):
        if i['t'].startswith('call dword ptr ['):
            seq = [ins[j]['t'] for j in range(k + 1, min(k + 5, len(ins)))]
            r['disp'].append(('%08X' % i['a'], i['t'], i['b'], seq))
    r['rets'] = [('%08X' % i['a'], i['t']) for i in ins if i['t'].startswith('ret')]
    # 2: factory slots
    r['slots'] = []
    for sec, va in core.find_dword(E):
        vt, index = core.vtable_containing(va)
        ri = core.rtti_of_vtable(vt)
        r['slots'].append({'slot': '%08X' % va, 'sec': sec, 'vt': '%08X' % vt, 'idx': index,
                           'sig': ri['sig'], 'col': hx(ri['col']), 'td': hx(ri['td']),
                           'name': ri['name'], 'vt0': hx(core.u32(vt))})
    # 3: object ctor
    ctor = None
    for i in ins:
        t = i['t']
        if t.startswith('call 0x'):
            tgt = int(t.split('0x')[1], 16)
            if core.in_text(tgt) and tgt != NEW:
                ctor = tgt
                r['obj_ctor_call'] = '%08X -> %08X' % (i['a'], tgt)
                break
    if ctor:
        reg, w0, wN, cins = factory_ctor_vt(ctor)
        r['obj_ctor'] = '%08X' % ctor
        r['obj_ctor_this'] = reg
        r['obj_ctor_w0'] = [('%08X' % a, m, '%08X' % v, b) for a, m, v, b in w0]
        r['obj_ctor_wN'] = [('%08X' % a, m, '%08X' % v) for a, m, v, b in wN]
        if w0:
            main = w0[-1][2]
            ri = core.rtti_of_vtable(main)
            r['obj_main'] = {'vt': '%08X' % main, 'vt0': hx(core.u32(main)),
                             'name': ri['name'], 'col': hx(ri['col']), 'sig': ri['sig']}
            r['obj_main_qi'] = (core.u32(main) == QI)
        r['member_vts'] = []
        seen = set()
        for a, m, v, b in wN:
            if v in seen:
                continue
            seen.add(v)
            ri = core.rtti_of_vtable(v)
            r['member_vts'].append({'vt': '%08X' % v, 'vt0': hx(core.u32(v)), 'name': ri['name']})
    return r


def host_rows():
    """Map each factory ctor called from HOST -> (alloc, ctor_site, reg_site, clsid, esi origin)."""
    ins = idx.body(HOST)
    out = []
    for k, i in enumerate(ins):
        if i['t'] == 'push 8':
            item = {'alloc': '%08X' % i['a']}
            for j in range(k + 1, min(k + 4, len(ins))):
                if ins[j]['t'].startswith('call 0x'):
                    item['new'] = '%08X' % ins[j]['a']
                    break
            for j in range(k + 2, min(k + 9, len(ins))):
                t = ins[j]['t']
                if t.startswith('call 0x') and t != 'call 0x7c8e17':
                    item['ctor_site'] = '%08X' % ins[j]['a']
                    item['ctor'] = '%08X' % int(t.split('0x')[1], 16)
                    break
            for j in range(k + 2, min(k + 18, len(ins))):
                t = ins[j]['t']
                if t.startswith('push 0x'):
                    v = int(t.split('0x')[1], 16)
                    if 0x7E0000 <= v < 0x800000:
                        item['clsid'] = '%08X' % v
                        for m in range(j + 1, min(j + 9, len(ins))):
                            if ins[m]['t'].startswith('call ') and '0x' not in ins[m]['t']:
                                item['reg_site'] = '%08X' % ins[m]['a']
                                item['reg_call'] = ins[m]['t']
                        break
            out.append(item)
    # esi origin before first reg call
    first_reg = None
    for item in out:
        if 'reg_site' in item:
            first_reg = int(item['reg_site'], 16)
            break
    if first_reg:
        w = idx.last_writer_of_reg(ins, 'esi', before=first_reg)
        if w:
            out_first = {'esi_last_writer_before_first_reg': '%08X %s' % (w['a'], w['t'])}
            if w['t'].startswith('mov esi, dword ptr [0x'):
                iat = int(w['t'].split('[')[1].rstrip(']'), 16)
                out_first['esi_iat'] = '%08X' % iat
                out_first['esi_iat_name'] = core.import_at(iat)
            return out, out_first
    return out, {}


if __name__ == '__main__':
    ents = sys.argv[1:] or ['006C1010']
    res = {}
    for e in ents:
        res[e] = analyze(int(e, 16))
    hr, esiinfo = host_rows()
    json.dump({'rows': res, 'host_seq': hr, 'esi': esiinfo}, open('rows.json', 'w'), indent=1)
    print('esi:', esiinfo)
    print('host seqs:', len(hr))
    print(json.dumps(res, indent=1))
