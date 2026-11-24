"""只读复算 coverage.tsv 的 ④ 口径（不改任何文件）。

coverage.tsv 现状：第 1 行是逗号表头（历史遗留，不是数据）；其后 18,498 行 TAB 分隔。
列：entry / subsystem / name / one_line_semantics / grade / evidence_path / n_sources / conflict
"""
import collections, sys, hashlib, os

sys.dont_write_bytecode = True
P = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
PROVED = '\u5df2\u8bc1'          # 已证
COL4 = '\u2463'                  # ④

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()

def load():
    rows = []
    with open(P, encoding='utf-8-sig') as f:
        for ln in f:
            c = ln.rstrip('\n').split('\t')
            if len(c) != 8:
                continue
            rows.append(dict(entry=c[0], sub=c[1], name=c[2], sem=c[3],
                             grade=c[4], ev=c[5], ns=c[6], conflict=c[7]))
    return rows

if __name__ == '__main__':
    print('path', P)
    print('sha256', sha(P), 'bytes', os.path.getsize(P))
    rows = load()
    print('data rows', len(rows), 'distinct', len(set(r['entry'] for r in rows)))
    print('grades', {k: v for k, v in collections.Counter(r['grade'] for r in rows).items()})
    proved = [r for r in rows if r['grade'] == '[' + PROVED + ']']
    print('proved', len(proved))
    A = [r for r in proved if COL4 in r['sem']]
    B = [r for r in proved if (COL4 + ' \u6d3b\u8868\u69fd\u4f4d\u89c1\u8bc1') in r['sem']]
    no4 = [r for r in proved if COL4 not in r['sem']]
    other = [r for r in proved if COL4 in r['sem'] and (COL4 + ' \u6d3b\u8868\u69fd\u4f4d\u89c1\u8bc1') not in r['sem']]
    print('A(含④)=%d  B(④活表槽位见证)=%d  其它含④=%d  无④=%d' % (len(A), len(B), len(other), len(no4)))
    ctx = collections.Counter()
    for r in A:
        s = r['sem']
        i = s.find(COL4)
        ctx[s[i:i + 14]] += 1
    for k, v in ctx.most_common(20):
        print('%5d  %s' % (v, k))
