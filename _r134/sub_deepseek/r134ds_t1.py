# -*- coding: utf-8 -*-
"""r134ds_t1.py -- T1 baseline, measured on explicitly paired (gate, table) snapshots.

The lead tree was being edited while this audit started (check_disc.py mtime moved
08:25:31 -> 08:26:27 and GATE_VER 'R133' -> 'R134' with new C7c/C7d blocks appearing).
So nothing is measured "live": each measurement names the exact sha256 of both inputs.

Pairs:
  P_R133 : gate = b99f20ef... (docstring says GATE_VER R133, has C7+C7b, no C7c/C7d)
           table = current table with row 20 col6 set back to GATE_VER = 'R133'
                   (the only cell that differs between the R133-era table and now)
  N_R134 : gate = 7d287890... (GATE_VER R134, C7c + C7d present, the on-disk state)
           table = on-disk table fbc57aa5...
"""
import io, json, os, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def make_table(src_tsv, dst_tsv, patch_row20_to=None):
    txt = io.open(src_tsv, encoding='utf-8', newline='').read()
    if patch_row20_to is not None:
        lines = txt.split('\n')
        for i, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == 7 and c[0] == '20':
                assert c[5].startswith('grep=(?m)^GATE_VER'), c[5]
                c[5] = "grep=(?m)^GATE_VER = '%s'" % patch_row20_to
                lines[i] = '\t'.join(c)
        txt = '\n'.join(lines)
    io.open(dst_tsv, 'w', encoding='utf-8', newline='').write(txt)
    return dst_tsv


def measure(tag, gate_src, tsv_src):
    r14 = L.build_sandbox('t1_' + tag, gate_src, tsv_src)
    rc, fails, notes, out = L.gate(r14)
    hdr, rows = L.read_rows(r14)
    txt = io.open(os.path.join(r14, L.TSV), encoding='utf-8', newline='').read()
    d = {
        'gate_sha256': sha(gate_src), 'gate_bytes': os.path.getsize(gate_src),
        'tsv_sha256': sha(tsv_src), 'tsv_bytes': os.path.getsize(tsv_src),
        'gate_ver_line': [l for l in io.open(gate_src, encoding='utf-8').read().split('\n')
                          if l.startswith('GATE_VER')],
        'has_C7c': 'C7c vacuity' in out, 'has_C7d': 'C7d product' in out,
        'exit': rc, 'fails': fails, 'n_fails': len(fails),
        'rows': len(rows), 'cr': txt.count('\r'), 'lf': txt.count('\n'),
        'lf_only': ('\r' not in txt),
        'shape_note': [n for n in notes if 'C7b shape census' in n],
        'c7c_note': [n for n in notes if 'C7c vacuity' in n],
        'c7d_note': [n for n in notes if 'C7d product' in n],
        'c7line': [l for l in out.split('\n') if l.startswith('C7 live-checks')],
        'all_c7_lines': [l for l in out.split('\n') if 'C7' in l],
    }
    print('== %-8s gate=%s(%dB) tsv=%s(%dB) exit=%s fails=%d rows=%d CR=%d LF=%d LFonly=%s C7c=%s C7d=%s'
          % (tag, d['gate_sha256'][:12], d['gate_bytes'], d['tsv_sha256'][:12], d['tsv_bytes'],
             rc, len(fails), len(rows), d['cr'], d['lf'], d['lf_only'],
             d['has_C7c'], d['has_C7d']))
    for f in fails:
        print('   ', f)
    for l in d['c7line'] + d['c7c_note'] + d['c7d_note']:
        print('   ', l)
    return d


S = L.SNAP
# R133-consistent table (only row 20 differs from the on-disk one)
t_p = make_table(os.path.join(S, 'DISC_RECHECK.R134.tsv'),
                 os.path.join(S, 'DISC_RECHECK.R133pair.tsv'), patch_row20_to='R133')
OUT['P_R133'] = measure('P_R133', os.path.join(S, 'check_disc.R133_prefix.py'), t_p)
OUT['N_R134'] = measure('N_R134', os.path.join(S, 'check_disc.R134_final.py'),
                        os.path.join(S, 'DISC_RECHECK.R134.tsv'))

hdr, rows = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows)
OUT['table'] = {'rows': len(rows), 'distinct_col5': len(paths), 'paths': paths,
                'col_widths_ok': all(len(r) == 7 for r in rows)}
print('rows=%d distinct_col5=%d all_7cols=%s' % (len(rows), len(paths), OUT['table']['col_widths_ok']))

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t1.json'), 'w'), ensure_ascii=False, indent=1)
print('wrote r134ds_t1.json')
