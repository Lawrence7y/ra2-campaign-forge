#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R208B x1: T-form thunk census (COL records, vftables, slot0 shapes).

Read-only evidence script for gamemd.exe.  Writes x1_tform.json next to self.
"""
import sys, os, json, struct, hashlib, collections
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_r185')))
from pe185 import RAW, dw, where, r2o, cstr, SECS

HERE = os.path.dirname(os.path.abspath(__file__))
EXE  = os.path.join(HERE, '..', 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(HERE, 'x1_tform.json')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def i32(x):
    return x - 0x100000000 if x & 0x80000000 else x


def secvirt(va):
    for s in SECS:
        if s['lo'] <= va < s['hi_virt']:
            return s['name']
    return None


def scan_cols():
    """5-dword COL records in .rdata and .data."""
    out = []
    for sn in ('.rdata', '.data'):
        s = next(x for x in SECS if x['name'] == sn)
        va = s['lo']
        while va + 20 <= s['hi_file']:
            w = [dw(va + 4 * k) for k in range(5)]
            if None not in w and w[0] in (0, 1, 2) and w[2] == 0 \
                    and where(w[3]) == '.data' and where(w[4]) == '.rdata':
                nm = cstr(w[3] + 8)
                if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
                    out.append({'addr': va, 'w': w, 'name': nm.decode('latin1')})
            va += 4
    return out


def build_refs(cols):
    """Single linear scan: value==COL addr at r, dw(r+4) in .text => vftable=r."""
    colset = {c['addr'] for c in cols}
    refs = collections.defaultdict(list)
    for sn in ('.rdata', '.data'):
        s = next(x for x in SECS if x['name'] == sn)
        va = s['lo']
        while va + 8 <= s['hi_file']:
            v = dw(va)
            if v in colset:
                nxt = dw(va + 4)
                if nxt is not None and where(nxt) == '.text':
                    refs[v].append(va)
            va += 4
    return refs


def bcd_list(pchd):
    """Return list of (bcd_addr, mdisp, name) for the CHD's base-class array."""
    chd = [dw(pchd + 4 * k) for k in range(4)]
    bca, nb = chd[3], chd[2]
    res = []
    if where(bca) == '.rdata':
        for i in range(min(nb, 64)):
            bp = dw(bca + 4 * i)
            if bp is None or where(bp) != '.rdata':
                continue
            ti = dw(bp)
            nm = cstr(ti + 8) if where(ti) == '.data' else b''
            res.append({'addr': bp, 'mdisp': i32(dw(bp + 8)),
                        'name': nm.decode('latin1', 'replace') if nm else None})
    return res


def classify(bs):
    if bs[0:4] == b'\x83\x6c\x24\x04' and bs[5:6] == b'\xe9':
        return 'A'
    if bs[0:4] == b'\x81\x6c\x24\x04' and bs[8:9] == b'\xe9':
        return 'B'
    if bs[0:3] == b'\xc2\x04\x00':
        return 'C'
    if bs[0:5] == b'\x32\xc0\xc2\x08\x00':
        return 'D'
    if bs[0:4] == b'\x8b\x44\x24\x04':
        return 'E'
    return 'F'


def slot_bytes(slot0, n=24):
    o = r2o(slot0)
    return RAW[o:o + n] if o is not None else b''


def decode_ab(bs, kind):
    if kind == 'A':
        imm = bs[4] - 256 if bs[4] > 127 else bs[4]
        rel = struct.unpack_from('<i', bs, 6)[0]
        return imm, slot0_base + 10 + rel
    imm = struct.unpack_from('<i', bs, 4)[0]
    rel = struct.unpack_from('<i', bs, 9)[0]
    return imm, slot0_base + 13 + rel


def main():
    global slot0_base
    cols = scan_cols()
    refmap = build_refs(cols)
    bychd = collections.defaultdict(list)
    for c in cols:
        bychd[c['w'][4]].append(c)
    extras = [c for pc, ls in bychd.items() for c in ls if c['addr'] != pc + 16]
    main_col = {pc: next(c['addr'] for c in ls if c['addr'] == pc + 16)
                for pc, ls in bychd.items()}

    shape_counts = collections.Counter()
    shape_f, ab_rows, b_rows = [], [], []
    mdisp_ok = mdisp_bad = jmp_ok = jmp_bad = 0
    mdisp_mismatch, jmp_fail = [], []

    for c in extras:
        va, w, nm = c['addr'], c['w'], c['name']
        rs = refmap.get(va, [])
        if len(rs) != 1:
            continue
        # 实测布局: r 处值=COL, r+4 处值=slot0(.text)。
        # 卡面"vftable 起点 = 引用位置+4"即 slot0 槽位地址。
        vt = rs[0] + 4
        slot0 = dw(vt)
        slot0_base = slot0
        bs = slot_bytes(slot0)
        kind = classify(bs)
        shape_counts[kind] += 1
        if kind == 'F':
            shape_f.append({'col': hex(va), 'name': nm, 'slot0': hex(slot0),
                            'hex8': bs[:8].hex()})
        if kind in ('A', 'B'):
            imm, jt = decode_ab(bs, kind)
            bcds = bcd_list(w[4])
            bcd_mdisps = [b['mdisp'] for b in bcds]
            col_off = i32(w[1])
            ok = (imm in bcd_mdisps) or (imm == col_off)
            if ok:
                mdisp_ok += 1
            else:
                mdisp_bad += 1
                mdisp_mismatch.append({'col': hex(va), 'name': nm,
                                       'mdisp': col_off, 'imm': imm})
            main_slot0 = dw(refmap[main_col[w[4]]][0] + 4)
            if jt == main_slot0:
                jmp_ok += 1
            else:
                jmp_bad += 1
                jmp_fail.append({'col': hex(va), 'name': nm,
                                 'jmp': hex(jt), 'main_slot0': hex(main_slot0)})
            row = {'shape': kind, 'col': hex(va), 'name': nm,
                   'mdisp': col_off, 'imm': imm, 'vftable': hex(vt),
                   'slot0': hex(slot0), 'bytes': bs[:16].hex(),
                   'jmp_target': hex(jt)}
            ab_rows.append(row)
            if kind == 'B':
                b_rows.append({**row, 'full_bytes': slot_bytes(slot0, 32).hex()})

    miss_only83 = [r for r in ab_rows if r['shape'] == 'B']

    result = {
        'source': {'exe': EXE, 'sha256': sha256(EXE)},
        'counts': {
            'col_total': len(cols),
            'chd_total': len(bychd),
            'vftable_unique': sum(1 for c in cols if len(refmap.get(c['addr'], [])) == 1),
            'extra_views': len(extras),
            'extra_with_vftable': sum(1 for c in extras if len(refmap.get(c['addr'], [])) == 1),
            'shape_counts': dict(shape_counts),
            'ab_total': len(ab_rows),
            'mdisp_ok': mdisp_ok, 'mdisp_bad': mdisp_bad,
            'jmp_ok': jmp_ok, 'jmp_bad': jmp_bad,
            'control_missed_by_83only': len(miss_only83),
        },
        'shape_F': shape_f,
        'shape_B_all': b_rows,
        'mdisp_mismatch': mdisp_mismatch,
        'jmp_fail': jmp_fail,
        'control_missed_names': [r['name'] for r in miss_only83],
        'all_ab': ab_rows,
    }
    with open(OUT, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    c = result['counts']
    print('sha256', result['source']['sha256'])
    print('COL_TOTAL', c['col_total'])
    print('VFTABLE_UNIQUE', c['vftable_unique'])
    print('EXTRA_VIEWS', c['extra_views'], 'WITH_VFTABLE', c['extra_with_vftable'])
    print('SHAPES', c['shape_counts'])
    print('A+B', c['ab_total'], 'MDISP_OK', c['mdisp_ok'], 'BAD', c['mdisp_bad'])
    print('JMP_OK', c['jmp_ok'], 'BAD', c['jmp_bad'])
    print('B_ENTRIES', json.dumps(b_rows, ensure_ascii=False))
    print('SHAPE_F', json.dumps(shape_f, ensure_ascii=False))
    print('CONTROL_83ONLY_MISS', c['control_missed_by_83only'],
          [r['name'] for r in miss_only83])
    print('ASSERT N / FAIL M')
    asserts = [
        ('COL_TOTAL', c['col_total'], 1214),
        ('VFTABLE_UNIQUE', c['vftable_unique'], 1214),
        ('EXTRA_VIEWS', c['extra_views'], 260),
        ('SHAPE_A', shape_counts['A'], 100),
        ('SHAPE_B', shape_counts['B'], 1),
        ('SHAPE_C', shape_counts['C'], 78),
        ('SHAPE_D', shape_counts['D'], 75),
        ('SHAPE_E', shape_counts['E'], 3),
        ('SHAPE_F', shape_counts['F'], 3),
        ('A+B_TOTAL', c['ab_total'], 101),
        ('MDISP_OK', c['mdisp_ok'], 101),
        ('MDISP_BAD', c['mdisp_bad'], 0),
        ('JMP_OK', c['jmp_ok'], 101),
        ('JMP_BAD', c['jmp_bad'], 0),
        ('CONTROL_MISS', c['control_missed_by_83only'], 1),
    ]
    fails = 0
    for name, got, want in asserts:
        status = 'FAIL' if got != want else 'N'
        if status == 'FAIL':
            fails += 1
        print(status, name, got, 'expected', want)
    print('ASSERT_COUNT', len(asserts), 'FAIL_COUNT', fails)
    print('JSON', OUT)


if __name__ == '__main__':
    main()
