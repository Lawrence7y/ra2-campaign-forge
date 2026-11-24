# -*- coding: utf-8 -*-
"""只读探针：把 ④ 文本里被显示层遮蔽的 token 以码点形式打印，判断它到底是什么形态
（十六进制函数起点？符号名？），不影响任何被审文件。"""
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
D = os.path.join(R14, 'R16_F1_B5')


def dump(tag, s, i, n=40):
    seg = s[i:i + n]
    print('%s @%d: %s' % (tag, i, ' '.join('%04X' % ord(c) for c in seg)))


with open(os.path.join(D, 'delta.tsv'), encoding='utf-8') as f:
    lines = f.read().split('\n')
for ln in lines[1:]:
    if not ln.strip():
        continue
    c = ln.split('\t')
    j = c[3].find('构造器')
    if j >= 0:
        print('--- entry', c[0])
        print('   chars:', c[3][j:j + 30])
        dump('   cp', c[3], j)

with open(os.path.join(D, 'diag.json'), encoding='utf-8') as f:
    diag = json.load(f)
for d in diag:
    print('diag %s func=%r len=%s' % (d['entry'], d.get('func'),
                                      len(d.get('func') or '')))
    if d.get('func'):
        dump('   cp', d['func'], 0, len(d['func']))

with open(os.path.join(D, 'fields.tsv'), encoding='utf-8') as f:
    fl = [x for x in f.read().split('\n') if x.strip()]
for ln in fl[1:]:
    c = ln.split('\t')
    print('fields %s install_func=%r' % (c[0], c[10]))
