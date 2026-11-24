# -*- coding: utf-8 -*-
# _exw_n2detail.py —— [N2] 补充：边界并列组两个命中划分的五元组是否逐位相同
# （裁决「断序第二等价类」是数值第二成员还是同一成员的另一种诱导方式）
import json, os, statistics, itertools

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_exw_n2detail_out.txt')

TARGETS = [('t55k_20261020', 0), ('t55k_20261020', 2)]
TABLE = {
    ('t55k_20261020', 0): (28.9, 2.62, 35.2, 2.60, -0.013),
    ('t55k_20261020', 2): (29.6, 2.61, 34.8, 2.61, -0.000),
}

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def med(v):
    return statistics.median(v)

def f3(x):
    return ('+' if x >= 0 else '-') + ('%.4f' % abs(x))

def main():
    for key in TARGETS:
        trip, w = key
        with open(os.path.join(BASE, *CORPUS_REL, trip, 'measure_w%d.json' % w), 'rb') as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        dur, mg = {}, {}
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
            if i + 1 < len(fids):
                dur[fid] = et[i + 1] - et[i]
        fwd = {fids[i]: mg[fids[i + 1]] for i in range(len(fids) - 1)}
        fwd[fids[-1]] = mg[fids[-1]]
        ids = sorted([f for f in fids if f in dur and f in mg], key=lambda x: (dur[x], x))
        n = len(ids); k = n // 3

        def row_of(ids_):
            fd = med([dur[i] for i in ids_[:k]]) * 1000.0
            sd = med([dur[i] for i in ids_[n - k:]]) * 1000.0
            fg = med([fwd[i] for i in ids_[:k]]) * 1000.0
            sg = med([fwd[i] for i in ids_[n - k:]]) * 1000.0
            return fd, fg, sd, sg, sg - fg

        def hits5(row):
            td = TABLE[key]
            return (round(row[0], 1) == td[0] and round(row[1], 2) == td[1] and
                    round(row[2], 1) == td[2] and round(row[3], 2) == td[3] and
                    round(row[4], 3) == td[4])

        P('=== %s/w%d（n_ids=%d k=%d）===' % (trip, w, n, k))
        base_row = row_of(ids)
        P('  基准（默认序）五元组: fd=%.4f fg=%.4f sd=%.4f sg=%.4f diff=%s  hits5=%s'
          % (base_row[0], base_row[1], base_row[2], base_row[3], f3(base_row[4]), hits5(base_row)))
        for bname, (i1, i2) in (('快边界', (k - 1, k)), ('慢边界', (n - k - 1, n - k))):
            if dur[ids[i1]] != dur[ids[i2]]:
                continue
            lo, hi = i1, i2
            while lo - 1 >= 0 and dur[ids[lo - 1]] == dur[ids[i1]]:
                lo -= 1
            while hi + 1 < n and dur[ids[hi + 1]] == dur[ids[i2]]:
                hi += 1
            block = ids[lo:hi + 1]
            m = (k - lo) if bname == '快边界' else (hi - (n - k) + 1)
            side_first = (bname == '快边界')
            P('  %s 并列块 位 %d..%d 成员 fid=%s dur=%.9f g=%d m=%d'
              % (bname, lo, hi, block, dur[block[0]], len(block), m))
            for ci, combo in enumerate(itertools.combinations(block, m)):
                cs = set(combo)
                rest = [f for f in block if f not in cs]
                if side_first:
                    new_ids = ids[:lo] + list(combo) + rest + ids[hi + 1:]
                else:
                    new_ids = ids[:lo] + rest + list(combo) + ids[hi + 1:]
                r2 = row_of(new_ids)
                tag = '（默认划分）' if tuple(combo) == combo_default(ids, lo, m, side_first, hi) else '（非默认划分）'
                side = '快侧取' if side_first else '慢侧取'
                P('    划分#%d %s %s %s → fd=%.4f fg=%.4f sd=%.4f sg=%.4f diff=%s  hits5=%s  与基准逐位相同=%s'
                  % (ci, side, list(combo), tag, r2[0], r2[1], r2[2], r2[3], f3(r2[4]), hits5(r2), r2 == base_row))
        P('')

    P('[_exw_n2detail] END')
    with open(os.path.join(BASE, *OUT_REL), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

def combo_default(ids, lo, m, side_first, hi):
    return tuple(ids[lo:lo + m]) if side_first else tuple(ids[hi + 1 - m:hi + 1])

if __name__ == '__main__':
    main()
