#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r172b: 在 r172a 的分句/括号判据之上加「指称类型」判定，给出 F24 里真正需要逐次限定的次数。

指称类型（只看值之后的 0..2 个字符，机械可判）：
  BODY  值后紧跟「件」或「 件」      -> 语料体量（本条主引用值）
  ROWS  值后紧跟「行」或「 行」      -> 清单行数
  IDENT 值前是「=」或「+」（算术恒等式右端/加数）
  OTHER 其余
判据：需要逐次限定 ⇔ 类型 == BODY 且 r172a 的分句级在场判为不在场。

自测（正反控 8 条）：
  D1 正控 「4,417 件」-> BODY
  D2 正控 「4,417 行」-> ROWS
  D3 正控 「= 4,417」-> IDENT
  D4 反控 「4,417」裸数字 -> OTHER
  D5 边界 「4,417件」（无空格）-> BODY
  D6 反控 值前是「+」也算 IDENT
"""
import importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('a', os.path.join(HERE, 'r172a_f24_clause.py'))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
V = a.V

BODY_SUF = ('件', '文件', '个文件')
ROWS_SUF = ('行', '行清单')

def kind(s, pos):
    after = s[pos+len(V):pos+len(V)+4]
    before = s[max(0, pos-3):pos]
    tail = after.lstrip(' ')
    if any(tail.startswith(x) for x in BODY_SUF): return 'BODY'
    if any(tail.startswith(x) for x in ROWS_SUF): return 'ROWS'
    if before.rstrip().endswith('=') or before.rstrip().endswith('+'): return 'IDENT'
    return 'OTHER'

def selftest():
    T = []
    for txt, want, name in (
        ('语料 4,417 件在此', 'BODY', 'D1 正控 件=BODY'),
        ('清单 4,417 行', 'ROWS', 'D2 正控 行=ROWS'),
        ('65 + 4,352 = 4,417', 'IDENT', 'D3 正控 =号右端=IDENT'),
        ('见 4,417 一数', 'OTHER', 'D4 反控 裸数字=OTHER'),
        ('语料 4,417件', 'BODY', 'D5 边界 无空格=仍是BODY'),
        ('5 + 4,417', 'IDENT', 'D6 反控 +号=IDENT'),
        ('语料 4,417 文件 / 737,517,286 B', 'BODY', 'D7 正控 文件=BODY（第一版把 文件 判成 OTHER，是本脚本的真实缺陷）'),
        ('清单 4,417 行与 sum', 'ROWS', 'D8 正控 行清单=ROWS'),
    ):
        p = txt.index(V)
        T.append((name, kind(txt, p) == want, kind(txt, p)))
    return T

def main(path):
    rows = {}
    for line in open(path, encoding='utf-8'):
        c = line.rstrip('\n').split('\t'); rows[c[0]] = c
    f = rows['F24']
    print('%-6s %-5s %-6s %-8s %-22s %s' % ('列', '下标', '类型', '分句在场', '限定词', '分句区间'))
    need = []; body_n = 0; body_in = 0
    for col, name in ((1, 'ST'), (4, 'LIM')):
        s = f[col]
        for m in re.finditer(V, s):
            k = kind(s, m.start())
            hits, cl = a.present(s, m.start())
            inn = bool(hits)
            if k == 'BODY':
                body_n += 1
                if inn: body_in += 1
                else: need.append((name, m.start()))
            print('%-6s %-5d %-6s %-8s %-22s %s' % (name, m.start(), k, 'IN' if inn else 'OUT', str(sorted(set(x for x, _ in hits))), cl))
    print()
    print('BODY 型共 %d 次，其中逐次在场 %d 次' % (body_n, body_in))
    print('需要逐次限定（BODY 且在分句级不在场）:', need)
    return need

if __name__ == '__main__':
    T = selftest(); bad = [n for n, ok, _ in T if not ok]
    for n, ok, got in T: print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else ' got=' + got))
    if bad: print('SELFTEST FAIL:', bad); sys.exit(2)
    print('SELFTEST %d/%d PASS' % (len(T), len(T)))
    main(sys.argv[1] if len(sys.argv) > 1 else 'lead/next_re_20261117_r14/R17_R123_FACTINDEX_V551/FACT_INDEX.tsv')
