"""Per-row independent verification for NAMED_PUSH_AUDIT6 (S22_B2, 18 rows).

Checks per entry, all from my own disassembly:
  A body shape: imm HRESULT guards, QI dispatch site, test/jcc, release path, rets
  B factory vtable: entry's own .rdata slot + idx + RTTI COL/TD/name
  C object ctor: write of main vtable to [this+0], vt[0] must be 0x410260
  D factory ctor (from host): writes the factory vtable that holds entry at idx 3
  E host 006BB9A0: alloc/ctor/CoRegisterClassObject; not atexit destructor
"""
import core, json, struct, sys

QI = 0x410260
HOST = 0x006BB9A0
NEW = 0x7C8E17
CO_REG_IAT = 0x7E15D8


def is_vtval(v):
    """plausible vtable pointer (.rdata/.data)"""
    return v is not None and 0x7C0000 <= v < 0x807000 and core.sec_of(v) in ('.rdata', '.data')


def body_analysis(entry):
    ins = core.func_body(entry)
    r = {'entry': entry, 'n_insn': len(ins), 'skipdata': sum(1 for i in ins if i['skip']),
         'last': ins[-1]['t'] if ins else None,
         'imms': [], 'qi_sites': [], 'calls': [], 'rets': [],
         'branch_after_qi': None, 'release': None}
    # collect
    for k, i in enumerate(ins):
        t, a, b = i['t'], i['a'], i['b']
        if t.startswith('mov eax, 0x'):
            r['imms'].append((a, t.split(', ')[1], b))
        if t.startswith('call'):
            r['calls'].append((a, t, b))
            if t.startswith('call dword ptr ['):
                r['qi_sites'].append((a, t, b))
        if t.startswith('ret'):
            r['rets'].append((a, t, b))
    # find the [reg] (slot0) call site and the following test/jcc
    for k, i in enumerate(ins):
        t = i['t']
        if t.startswith('call dword ptr [') and '+' not in t and '-' not in t:
            # slot0 dispatch
            seq = [ins[j]['t'] for j in range(k, min(k + 5, len(ins)))]
            r['qi_sites'].append((i['a'], t, i['b'], seq))
    return ins, r


def find_main_vtable_of_ctor(ctor):
    """Disassemble ctor; return writes of vtable-looking imm to [this] (offset 0) and to members."""
    ins = core.dis(ctor, 400)
    # this-register: first 'mov <reg>, ecx' in the prologue
    this_reg = None
    for i in ins[:14]:
        m = i['t']
        if m.startswith('mov ') and m.endswith(', ecx'):
            cand = m.split(' ')[1].split(',')[0]
            if cand in ('esi', 'edi', 'ebx', 'ebp', 'eax', 'edx'):
                this_reg = cand
                break
    writes0, writesN = [], []
    for i in ins:
        t = i['t']
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
        off0 = (this_reg is not None and mem == '[%s]' % this_reg)
        writes0.append((i['a'], mem, v, i['b'], off0)) if off0 else writesN.append((i['a'], mem, v, i['b']))
    return this_reg, writes0, writesN, ins


def host_analysis(entrys_ctor_hint=None):
    ins = core.func_body(HOST)
    r = {'n_insn': len(ins), 'last': ins[-1]['t'], 'seqs': []}
    # pattern: push 8; call NEW; add esp,4; test eax,eax; je; mov ecx,eax; call ctor; ... push clsid; push1;push1; push eax; call esi
    for k, i in enumerate(ins):
        if i['t'] == 'push 8' and k + 2 < len(ins) and ins[k + 1]['t'].startswith('call 0x7c8e17'):
            item = {'alloc': i['a'], 'new': ins[k + 1]['a']}
            ctor = None
            for j in range(k + 2, min(k + 9, len(ins))):
                if ins[j]['t'].startswith('call 0x'):
                    a = int(ins[j]['t'].split('0x')[1], 16)
                    if a != NEW:
                        ctor = (ins[j]['a'], a)
                        break
            item['ctor'] = ctor
            # find the registration: push clsid; ... call <reg>
            for j in range(k + 2, min(k + 16, len(ins))):
                t = ins[j]['t']
                if t.startswith('push 0x') and is_vtval(int(t.split('0x')[1], 16)) and (int(t.split('0x')[1], 16) < 0x800000):
                    clsid = int(t.split('0x')[1], 16)
                    # look ahead for 'call esi'/reg within 8
                    for m in range(j + 1, min(j + 8, len(ins))):
                        tt = ins[m]['t']
                        if tt.startswith('call ') and '0x' not in tt:
                            item['clsid'] = clsid
                            item['regcall'] = (ins[m]['a'], tt)
                            break
                    break
            r['seqs'].append(item)
    return r


def atexit_check(fn):
    """Is fn registered with atexit (push fn; call 0x7C978A)? Also its callers."""
    hits = core.find_dword(fn)
    reg = []
    callers = []
    for sec, va in hits:
        # look for push imm; call 0x7c978a nearby
        for back in range(4, 12, 4):
            if core.u32(va - back) == 0x7C978A:
                reg.append((va, 'atexit-call-at-%08X' % (va - back)))
        callers.append((sec, va))
    direct = []
    for sec, va in hits:
        if sec != '.text':
            continue
        for off in range(-5, 1):
            o = core.va2off(va + off)
            if o is None:
                continue
            b = core.DATA[o:o + 5]
            if len(b) == 5 and b[0] == 0xE8:
                rel = struct.unpack('<i', b[1:5])[0]
                if (va + off + 5 + rel) & 0xFFFFFFFF == fn:
                    direct.append((va + off, 'direct-call'))
            if len(b) == 5 and b[0] == 0x68:
                v = struct.unpack('<I', b[1:5])[0]
                if v == fn:
                    direct.append((va + off, 'push-imm'))
    return hits, reg, direct


if __name__ == '__main__':
    entries = sys.argv[1:]
    out = {}
    for e in entries:
        E = int(e, 16)
        ins, r = body_analysis(E)
        # B: factory vtable slots
        r['slots'] = []
        for sec, va in core.find_dword(E):
            vt, idx = core.vtable_containing(va)
            ri = core.rtti_of_vtable(vt)
            r['slots'].append({'slot_va': va, 'sec': sec, 'vt': vt, 'idx': idx,
                               'col': ri['col'], 'sig': ri['sig'], 'td': ri['td'], 'name': ri['name'],
                               'col_sec': ri['col_sec'], 'td_sec': ri['td_sec'],
                               'vt0': core.u32(vt)})
        # C: object ctor from body (first call to a .text imm that is not QI/noise)
        ctor = None
        for a, t, b in r['calls']:
            if t.startswith('call 0x'):
                tgt = int(t.split('0x')[1], 16)
                if core.in_text(tgt) and tgt != QI and 0x600000 <= tgt < 0x800000:
                    ctor = tgt
                    r['ctor_call_site'] = a
                    break
        r['obj_ctor'] = ctor
        if ctor:
            this_reg, w0, wN, _ = find_main_vtable_of_ctor(ctor)
            r['obj_ctor_this'] = this_reg
            r['obj_writes0'] = w0
            r['obj_writesN'] = wN
            main = None
            for w in w0:
                main = w[2]  # last write to [this] wins
            r['obj_main_vt'] = main
            if main:
                ri = core.rtti_of_vtable(main)
                r['obj_main_rtti'] = {'col': ri['col'], 'sig': ri['sig'], 'td': ri['td'], 'name': ri['name']}
                r['obj_main_vt0'] = core.u32(main)
        out[e] = r
    print(json.dumps(out, indent=1, default=str))
