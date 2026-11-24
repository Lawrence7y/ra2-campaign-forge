# -*- coding: utf-8 -*-
"""r55_recheck.py —— R55-T1-RERUN：纪律 3/4/22/27/28 的**只读**实测器

用途：本卡要求「真跑一遍」再把自描述行追加到产物末尾。本脚本只做**测量**，
      不写任何产物（追加由 append_line.py 单独负责），因此测量结果与门禁结果互相独立。

用法：
    python r55_recheck.py            # 打印实测值 + 建议的自描述行（含真算 sha256）
    python r55_recheck.py --json     # 同上，额外把结果写到 r55_recheck.json

三个口径（与 check_disc.py 的 C7 保持一致，避免「我的数」和「门的数」不同源）：
    rows : io.open(encoding='utf-8', errors='replace') 逐行计数，**减 1**（表头）
    sum  : 第 bytes 列全部必须为十进制整数，求和；出现非整数即记 bad 并判 UNKNOWN
    bytes: os.path.getsize

anchors（第 4 列锚）的 sha256 口径，逐字照抄 recheck_verify.py R5：
    'sha256:' + sha256(UTF-8(row[3])).hexdigest()   ← row[3] 原样、不 strip
"""
import hashlib
import io
import json
import os
import re
import sys

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
HERE = os.path.dirname(os.path.abspath(__file__))

TARGETS = [3, 4, 22, 27, 28]


def read_text(p):
    return io.open(p, encoding='utf-8', newline='').read()


def load_rows():
    txt = read_text(DR)
    raw = [l for l in txt.split('\n') if l]
    head = raw[0].split('\t')
    out = {}
    for ln in raw[1:]:
        c = ln.split('\t')
        if c[0].strip().isdigit():
            out[int(c[0])] = (c, head)
    return out


def anchor_hash(row):
    """逐字照 recheck_verify.py R5：对 row[3] 原样串做 sha256。"""
    return 'sha256:' + hashlib.sha256(row[3].encode('utf-8')).hexdigest()


def measure_table(path, bytes_col):
    """按 check_disc.py C7 的 rows 口径数行；并算 sum(bytes_col)。"""
    n = 0
    with io.open(path, encoding='utf-8', errors='replace') as f:
        for _ in f:
            n += 1
    data_rows = n - 1  # 减表头
    total = 0
    bad = []
    rows = read_text(path).split('\n')
    for i, ln in enumerate(rows[1:], start=2):
        if ln == '':
            continue
        c = ln.split('\t')
        if bytes_col >= len(c):
            bad.append((i, 'col_missing'))
            continue
        v = c[bytes_col].strip()
        if re.fullmatch(r'\d+', v):
            total += int(v)
        else:
            bad.append((i, v[:40]))
    return {'rows': data_rows, 'sum_bytes': total, 'nonnumeric': bad,
            'disk_bytes': os.path.getsize(path)}


def verdict_dist(path):
    rows = read_text(path).split('\n')
    dist = {}
    o = p = 0
    for ln in rows[1:]:
        if ln == '':
            continue
        c = ln.split('\t')
        v = c[1].strip()
        dist[v] = dist.get(v, 0) + 1
        o += int(c[2]) if c[2].strip().isdigit() else 0
        p += int(c[3]) if c[3].strip().isdigit() else 0
    return {'rows': sum(dist.values()), 'dist': dist, 'sum_O': o, 'sum_P': p}


def read_anchor_check(path):
    """解析 anchor_check.txt 的分类计数行。"""
    txt = read_text(path)
    out = {}

    def grab(label):
        m = re.search(r'(?m)^\s*' + re.escape(label) + r'\s+(\d+)', txt)
        return int(m.group(1)) if m else None

    for lab in (u'路径项', u'文件存在', u'带锚点', u'机械核验通过', u'节号体例通过',
                u'池未加载(未核验)', u'人工核验类(无节号)', u'目录即卡(可接受)',
                u'目录+锚(NG)', u'MISS'):
        out[lab] = grab(lab)
    m = re.search(r'(?m)^\[exit (\d+)\]', txt)
    out['exit'] = int(m.group(1)) if m else None
    return out


def main():
    rows = load_rows()
    res = {}

    # ---- 纪律 3 / 4：同一产物 anchor_check.txt ----
    for n in (3, 4):
        row = rows[n][0]
        rel = row[4].strip()
        p = os.path.join(ROOT, rel.replace('\\', '/'))
        rec = {'product': rel, 'exists': os.path.isfile(p),
               'anchor_col': row[3], 'anchors': anchor_hash(row),
               'checkexpr': row[5]}
        if rec['exists']:
            rec['disk_bytes'] = os.path.getsize(p)
            rec['parsed'] = read_anchor_check(p)
            # 与 DISC_RECHECK.tsv 第 6 列校验式对账
            rec['expr_hit'] = bool(re.search(row[5].split('=', 1)[1], read_text(p)))
        res[n] = rec

    # ---- 纪律 22 ----
    row22 = rows[22][0]
    p22 = os.path.join(ROOT, row22[4].strip().replace('\\', '/'))
    m22 = measure_table(p22, 1)
    m22.update({'product': row22[4].strip(), 'anchor_col': row22[3],
                'anchors': anchor_hash(row22)})
    res[22] = m22

    # ---- 纪律 27 ----
    row27 = rows[27][0]
    p27 = os.path.join(ROOT, row27[4].strip().replace('\\', '/'))
    d27 = verdict_dist(p27)
    d27.update({'product': row27[4].strip(), 'anchor_col': row27[3],
                'anchors': anchor_hash(row27),
                'disk_bytes': os.path.getsize(p27)})
    res[27] = d27

    # ---- 纪律 28 ----
    row28 = rows[28][0]
    p28 = os.path.join(ROOT, row28[4].strip().replace('\\', '/'))
    m28 = measure_table(p28, 1)
    m28.update({'product': row28[4].strip(), 'anchor_col': row28[3],
                'anchors': anchor_hash(row28)})
    res[28] = m28

    print(json.dumps({str(k): v for k, v in res.items()}, ensure_ascii=False, indent=2))
    if '--json' in sys.argv:
        with io.open(os.path.join(HERE, 'r55_recheck.json'), 'w',
                     encoding='utf-8', newline='') as f:
            f.write(json.dumps({str(k): v for k, v in res.items()},
                               ensure_ascii=False, indent=2) + '\n')
        print('\n[written] r55_recheck.json')
    return res


if __name__ == '__main__':
    main()
