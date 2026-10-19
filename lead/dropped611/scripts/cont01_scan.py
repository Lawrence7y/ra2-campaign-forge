# -*- coding: utf-8 -*-
# DROPPED-611-CONTINUATION01 · E22 detector v2.1
# Basic-block worklist + union-meet this-register dataflow (optimistic, candidate generator).
# Jump-table (jmp [reg*scale+disp]) target extraction included.
# Hardcoded paths only; no argv / subprocess / dynamic import.
import json, sys, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, CS_OP_REG

sys.stdout.reconfigure(encoding='utf-8', newline='\n')
ROOT = 'D:/Project/ra2-campaign-forge'
BIN  = ROOT + '/ra2youli/gamemd.exe'
LEAD = ROOT + '/out/re_work/work_chain/CONTINUE_20261003/lead'
OUT  = ROOT + '/lead/dropped611/raw/cont01'


def _chk(name, base=OUT):
    # containment guard: name must resolve inside base (defense in depth);
    # called as a standalone statement BEFORE open(), which sees a plain literal
    p = os.path.normpath(base + '/' + name)
    assert os.path.commonpath([p, os.path.normpath(base)]) == os.path.normpath(base), name
    return name

data = open(BIN, 'rb').read()
IMG = 0x400000
TLO = 0x401000
THI = 0x401000 + 0x3df38d
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

R32 = ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'ebp', 'esp')
R8  = {'al': 'eax', 'cl': 'ecx', 'dl': 'edx', 'bl': 'ebx',
       'ah': 'eax', 'ch': 'ecx', 'dh': 'edx', 'bh': 'ebx'}
R16 = {'ax': 'eax', 'cx': 'ecx', 'dx': 'edx', 'bx': 'ebx'}
KIND = {'clean': 0, 'maybe': 1, 'derived': 2, 'this': 3}


def rd(va, n):
    o = va - IMG
    if o < 0 or o + n > len(data):
        return b''
    return data[o:o + n]


def disasm_func(va, cap=0x3000, maxi=40000):
    seen = {}
    order = []
    calls = []
    ijmp = []
    targets_seen = set()
    jtab = {}
    todo = [va]
    while todo:
        a = todo.pop()
        while True:
            if a in seen or a < TLO or a >= THI or a >= va + cap or len(order) > maxi:
                break
            b = rd(a, 16)
            if not b:
                seen[a] = None
                break
            try:
                ins = next(md.disasm(b, a, 1))
            except Exception:
                seen[a] = None
                break
            seen[a] = ins
            order.append(a)
            ops = ins.operands
            m = ins.mnemonic
            tg = []
            stop = False
            if m == 'jmp' or m.startswith('jmp '):
                if ops and ops[0].type == CS_OP_IMM:
                    t = ops[0].imm
                    targets_seen.add(t)
                    if va <= t < va + cap:
                        tg = [t]
                    stop = True
                elif ops and ops[0].type == CS_OP_MEM:
                    mo = ops[0].mem
                    if mo.base == 0 and mo.index != 0 and mo.scale in (1, 2, 4, 8):
                        p = mo.disp
                        ents = []
                        for _ in range(512):
                            e = int.from_bytes(rd(p, 4), 'little')
                            if not (TLO <= e < THI and va <= e < va + cap):
                                break
                            targets_seen.add(e)
                            ents.append(e)
                            tg.append(e)
                            p += 4
                        if ents:
                            jtab[a] = ents
                    stop = True
                    ijmp.append(a)
                else:
                    stop = True
                    ijmp.append(a)
            elif m and m[0] == 'j':
                if ops and ops[0].type == CS_OP_IMM:
                    t = ops[0].imm
                    targets_seen.add(t)
                    if va <= t < va + cap:
                        tg = [t]
                else:
                    stop = True
                    ijmp.append(a)
            elif m.startswith('loop') or m == 'jecxz':
                if ops and ops[0].type == CS_OP_IMM:
                    t = ops[0].imm
                    targets_seen.add(t)
                    if va <= t < va + cap:
                        tg = [t]
            elif m == 'call' or m.startswith('call '):
                if ops and ops[0].type == CS_OP_IMM:
                    calls.append(ops[0].imm)
            elif m == 'ret' or m.startswith('ret '):
                stop = True
            for t in tg:
                todo.append(t)
            if stop:
                break
            a += ins.size
    return order, seen, calls, ijmp, targets_seen, jtab


def mems(ins):
    out = []
    for i, o in enumerate(ins.operands):
        if o.type == CS_OP_MEM:
            b = ins.reg_name(o.mem.base) if o.mem.base else None
            x = ins.reg_name(o.mem.index) if o.mem.index else None
            out.append((i, b, x, o.mem.disp))
    return out


def fresh_state():
    st = {r: ['clean', 0, 0] for r in R32}
    st['ecx'] = ['this', 0, 0]
    return st


def umerge(x, y):
    if KIND[x[0]] > KIND[y[0]]:
        return x
    if KIND[y[0]] > KIND[x[0]]:
        return y
    return [x[0], min(x[1], y[1]), max(x[2], y[2])]


def state_eq(a, b):
    for r in R32:
        if a[r][0] != b[r][0] or a[r][2] != b[r][2]:
            return False
    return True


def process_block(blk, in_state):
    st = {r: list(in_state[r]) for r in R32}
    pushed = []
    ev = []
    tr = []

    def get(r):
        return st.get(r, ['clean', 0, 0])

    def evt(a, ins, base, kind, disp, acc):
        ev.append({'va': '%08X' % a, 'insn': ('%s %s' % (ins.mnemonic, ins.op_str))[:64],
                   'base': base, 'kind': kind, 'off': disp,
                   'xc': st[base][2] if base in st else 0, 'rw': acc})

    for a in blk:
        ins = seen_global[a]
        if ins is None:
            continue
        m = ins.mnemonic
        ops = ins.operands
        dst = None
        dst_raw = None
        src32 = None
        if ops and ops[0].type == CS_OP_REG:
            nm = ins.reg_name(ops[0].reg)
            dst_raw = nm
            dst = R8.get(nm, R16.get(nm, nm if nm in R32 else None))
        if len(ops) > 1 and ops[1].type == CS_OP_REG:
            nm2 = ins.reg_name(ops[1].reg)
            if nm2 in R32:
                src32 = nm2
        if not m.startswith('lea'):
            for (i, mb, mx, dp) in mems(ins):
                for r in (mb, mx):
                    if r in R32:
                        k, off, xc = get(r)
                        if k in ('this', 'derived', 'maybe'):
                            acc = 'w' if (i == 0 and m.split()[0] in ('mov',)) else 'r'
                            evt(a, ins, r, k, dp, acc)
        STR_OPS = ('movs', 'movsb', 'movsw', 'movsd', 'stos', 'stosb', 'stosw', 'stosd',
                   'scas', 'scasb', 'scasw', 'scasd', 'lods', 'lodsb', 'lodsw', 'lodsd',
                   'cmps', 'cmpsb', 'cmpsw', 'cmpsd')
        toks = m.split()
        if len(ops) == 0 and any(t in STR_OPS for t in toks):
            for r in ('esi', 'edi'):
                k, off, xc = get(r)
                if k in ('this', 'derived', 'maybe'):
                    evt(a, ins, r, k, -1, 'r')
        if dst and dst != 'esp':
            full = dst
            cur = get(full)
            if m.startswith('lea'):
                mm = mems(ins)
                k = 'clean'
                if mm:
                    for r in (mm[0][1], mm[0][2]):
                        if r in R32 and get(r)[0] in ('this', 'derived'):
                            k = 'derived'
                if k == 'clean' and src32 and get(src32)[0] in ('this', 'derived'):
                    k = 'derived'
                st[full] = [k, 0, 0]
            elif m.split()[0] in ('mov', 'movzx', 'movsx', 'movabs'):
                if dst_raw in R8 or dst_raw in R16:
                    if cur[0] in ('this', 'derived'):
                        st[full] = ['maybe', 0, cur[2]]
                    else:
                        st[full] = ['clean', 0, 0]
                elif src32 and get(src32)[0] != 'clean':
                    st[full] = list(get(src32))
                else:
                    st[full] = ['clean', 0, 0]
            elif m == 'xor' and len(ops) == 2 and ops[1].type == CS_OP_REG and ops[0].reg == ops[1].reg:
                st[full] = ['clean', 0, 0]
            elif m in ('add',) and cur[0] in ('this', 'derived'):
                st[full] = ['derived', 0, cur[2]]
            elif m in ('sub', 'and', 'or', 'xor', 'shl', 'shr', 'sar', 'imul', 'mul', 'rol', 'ror'):
                if cur[0] in ('this', 'derived'):
                    st[full] = ['maybe', 0, cur[2]]
            elif m in ('inc', 'dec', 'neg'):
                if cur[0] in ('this', 'derived'):
                    st[full] = ['derived', 0, cur[2]]
            elif m == 'pop':
                st[full] = pushed.pop() if pushed else ['clean', 0, 0]
            elif m == 'xchg' and src32:
                st[full], st[src32] = st[src32], st[full]
            elif m == 'cdq':
                pass
            elif m.startswith('set') and len(m) <= 6:
                st[full] = ['clean', 0, 0]
            else:
                op0 = m.split()[0]
                if op0 not in ('test', 'cmp', 'ucomis', 'comis', 'jmp', 'call', 'ret',
                               'push', 'leave', 'nop', 'int3', 'wait', 'fnst', 'fld', 'fst',
                               'fild', 'fist', 'fadd', 'fmul', 'fsub', 'fdiv', 'fclex',
                               'fninit', 'movs', 'movsd', 'movsb', 'movsw', 'stos', 'scas',
                               'lods', 'cmps', 'rep', 'repe', 'repne', 'bt', 'btr', 'bts'):
                    st[full] = ['maybe', 0, 0]
        if m == 'cdq':
            st['edx'] = ['maybe', 0, 0] if st['eax'][0] != 'clean' else ['clean', 0, 0]
        if m == 'push' and ops and ops[0].type == CS_OP_REG:
            nm = ins.reg_name(ops[0].reg)
            nm = R8.get(nm, R16.get(nm, nm if nm in R32 else 'esp'))
            pushed.append(list(st[nm]))
        if m == 'call' or m.startswith('call '):
            for r in ('eax', 'ecx', 'edx'):
                if st[r][0] != 'clean':
                    st[r][2] += 1
        tr.append(['%08X' % a, m, st['eax'][0], st['ecx'][0], st['edx'][0],
                   st['ebx'][0], st['esi'][0], st['edi'][0], st['ebp'][0]])
    return st, ev, tr


seen_global = {}


def scan(va, depth=0):
    order, seen, calls, ijmp, targets_seen, jtab = disasm_func(va)
    for k2, v2 in seen.items():
        seen_global[k2] = v2
    reach = sorted(set(a for a in order if seen.get(a) is not None))
    if not reach:
        return {'entry': '%08X' % va, 'n_reach': 0, 'extent_end': '%08X' % va,
                'events': [], 'ecx_overwrite_before_read': None, 'thunk': None,
                'calls': [], 'n_ijmp': 0, 'n_blocks': 0, 'trace': {}}
    blocks = []
    cur = []
    for a in reach:
        if a in targets_seen and cur:
            blocks.append(cur)
            cur = []
        cur.append(a)
        m = seen[a].mnemonic
        if m == 'ret' or m.startswith('ret ') or m == 'jmp' or m.startswith('jmp '):
            blocks.append(cur)
            cur = []
        elif m and m[0] == 'j':
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    if not blocks:
        blocks = [[va]]
    idx = {blk[0]: i for i, blk in enumerate(blocks)}
    nblk = len(blocks)
    succ = {}
    for i, blk in enumerate(blocks):
        last = seen[blk[-1]]
        m = last.mnemonic
        ops = last.operands
        s = []
        if m == 'ret' or m.startswith('ret '):
            pass
        elif m == 'jmp' or m.startswith('jmp '):
            if ops and ops[0].type == CS_OP_IMM and ops[0].imm in idx:
                s.append(idx[ops[0].imm])
            elif blk[-1] in jtab:
                for t in jtab[blk[-1]]:
                    if t in idx and idx[t] not in s:
                        s.append(idx[t])
        elif m and m[0] == 'j':
            if i + 1 < nblk and blk[-1] + last.size == blocks[i + 1][0]:
                s.append(i + 1)
            if ops and ops[0].type == CS_OP_IMM and ops[0].imm in idx:
                j = idx[ops[0].imm]
                if j not in s:
                    s.append(j)
        else:
            if i + 1 < nblk:
                s.append(i + 1)
        succ[i] = s
    in_st = [None] * nblk
    in_st[0] = fresh_state()
    queue = [0]
    visits = [0] * nblk
    allevents = []
    alltrace = {}
    while queue:
        i = queue.pop()
        visits[i] += 1
        out, ev, tr = process_block(blocks[i], in_st[i])
        for e in ev:
            allevents.append(e)
        alltrace[i] = tr
        for j in succ[i]:
            if in_st[j] is None:
                in_st[j] = {r: list(out[r]) for r in R32}
                queue.append(j)
            else:
                nm = {r: umerge(in_st[j][r], out[r]) for r in R32}
                if not state_eq(nm, in_st[j]):
                    in_st[j] = nm
                    if visits[j] < 40:
                        queue.append(j)
    # dedupe events
    dd = {}
    for e in allevents:
        dd[(e['va'], e['base'], e['insn'])] = e
    ev2 = sorted(dd.values(), key=lambda x: (x['va'], x['base']))
    # ecx overwrite-before-read (textual, on sorted reachable insns)
    ecx_overwrite = None
    ecx_read = False
    for a in reach:
        ins = seen[a]
        t = ins.op_str
        parts = t.split(',')
        srctxt = parts[1].strip() if len(parts) > 1 else ''
        if not ecx_read and ('ecx' in srctxt or any(b == 'ecx' for (_i, b, _x, _d) in mems(ins))):
            ecx_read = True
        if parts and parts[0].strip() in ('ecx', 'cl', 'cx') and not ecx_read:
            ecx_overwrite = '%08X' % a
            break
        if parts and parts[0].strip() in ('ecx', 'cl', 'cx'):
            ecx_read = ecx_read
    # thunk: single tiny block ending in out-of-region jmp imm
    nthunk = None
    if len(blocks) == 1 and len(reach) <= 8:
        last = seen[reach[-1]]
        if last.mnemonic == 'jmp' or last.mnemonic.startswith('jmp '):
            o = last.operands
            if o and o[0].type == CS_OP_IMM and (o[0].imm < va or o[0].imm >= va + 0x3000) and depth < 2:
                nthunk = '%08X' % o[0].imm
                sub = scan(o[0].imm, depth + 1)
                ev2 = ev2 + sub['events'][:200]
    ext = '%08X' % (reach[-1] if reach else va)
    return {'entry': '%08X' % va, 'n_reach': len(reach), 'extent_end': ext,
            'events': ev2, 'ecx_overwrite_before_read': ecx_overwrite,
            'thunk': nthunk, 'calls': ['%08X' % c for c in calls][:40],
            'n_ijmp': len(ijmp), 'n_blocks': nblk, 'trace': alltrace}


def main():
    _chk('E20_worklist.json')
    _chk('uncovered_families/new_windows.json', LEAD)
    _chk('nullthis_sweep/candidates.json', LEAD)
    wl = json.load(open('D:/Project/ra2-campaign-forge/lead/dropped611/raw/cont01/E20_worklist.json', encoding='utf-8'))
    callees = [p['callee'] for p in wl['percal']]
    nw = json.load(open('D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/uncovered_families/new_windows.json', encoding='utf-8'))
    controls = sorted(set(e['consumer_entry'].upper() for e in nw['windows'] if e.get('consumer_entry')))
    cand = json.load(open('D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/nullthis_sweep/candidates.json', encoding='utf-8'))
    rc4 = sorted(set(x['entry'].upper() for x in cand['rc4_windows']))
    targets = {}
    for c in callees + controls + rc4:
        targets['%08X' % int(c, 16)] = int(c, 16)
    print('targets: callees=%d controls=%d rc4=%d union=%d' %
          (len(callees), len(controls), len(rc4), len(targets)))
    res = {}
    for k in sorted(targets):
        res[k] = scan(targets[k])
    _chk('E22_scan.json')
    _chk('E22_events.tsv')
    json.dump({'funcs': {k: {kk: vv for kk, vv in v.items() if kk not in ('trace',)}
                         for k, v in res.items()}, 'site_0x70E8C4_ctx': []},
              open('D:/Project/ra2-campaign-forge/lead/dropped611/raw/cont01/E22_scan.json', 'w', encoding='utf-8'), indent=0)
    n_ev = sum(1 for k, v in res.items() if v['events'])
    print('funcs scanned=%d with_events=%d' % (len(res), n_ev))
    FIXED6 = ['004F9A50', '004F9A90', '0054F450', '005ADD10', '00694760', '007B1DE0']
    ok6 = sum(1 for k in FIXED6 if res.get(k, {}).get('events'))
    print('KNOWN6(ii) detected=%d/6' % ok6)
    okc = sum(1 for k in controls if res.get('%08X' % int(k, 16), {}).get('events'))
    okr = sum(1 for k in rc4 if res.get('%08X' % int(k, 16), {}).get('events'))
    print('CONTROL 120-consumers detected=%d/%d' % (okc, len(controls)))
    print('CONTROL rc4 detected=%d/%d' % (okr, len(rc4)))
    miss = [k for k in controls if not res.get('%08X' % int(k, 16), {}).get('events')]
    print('control_misses=%s' % miss)
    # census first_deref for misses
    fams = cand['families']
    census = {}
    for gU, f in fams.items():
        if f.get('tier') != 'T3':
            continue
        for c, cv in f.get('consumers', {}).items():
            if c == '(vtable-indirect)' or not isinstance(cv, dict):
                continue
            fd = cv.get('first_deref')
            if c not in census and fd:
                census[c.upper()] = {'va': fd.get('va'), 'insn': fd.get('insn'),
                                     'body': cv.get('body'), 'end': cv.get('end')}
    for k in miss:
        print('MISS %s census=%s myext=%s nreach=%d nblk=%s' % (
            k, census.get(k), res.get('%08X' % int(k, 16), {}).get('extent_end'),
            res.get('%08X' % int(k, 16), {}).get('n_reach'),
            res.get('%08X' % int(k, 16), {}).get('n_blocks')))
    # full event dump for callees
    with open('D:/Project/ra2-campaign-forge/lead/dropped611/raw/cont01/E22_events.tsv', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('callee\teva\tinsn\tbase\tkind\toff\txc\trw\textent_end\tn_reach\n')
        for k in sorted(targets):
            v = res[k]
            for e in v['events']:
                fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%d\n' % (
                    k, e['va'], e['insn'].replace('\t', ' '), e['base'], e['kind'],
                    e['off'], e['xc'], e['rw'], v['extent_end'], v['n_reach']))
    print('--- E22 v2.1 done ---')


if __name__ == '__main__':
    main()
