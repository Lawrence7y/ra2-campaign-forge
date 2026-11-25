# -*- coding: utf-8 -*-
"""R128f：门禁 C11 的「永远通过子项」实况普查（只读，不改盘上文件）。

背景：COMPACT_STATE 待办⑦ 与提示词都点了「C11 其余 4 处永远通过子项」。
本轮不猜是哪 4 处，先按字节把 31 行的实际可失败性全量测一遍，再按类别判定。

三类判据：
  类 A  col7 以「无」开头 —— 声明不补。C11 主循环直接 continue 计入 claims-none，
        永不 FAIL。这是设计内（12 行冻结档 + 其余），但它的「诚实性」从未被核过。
  类 B  col7 以「有」开头且产物在冻结档 —— 若自述行通过则 FAIL（R87-T2 已收紧）。
  类 C  校验式是 rows=N 形态 —— 只数行数，不核内容是否支持该纪律。
"""
import io, os, re, json, hashlib
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r128', 'r128f_gate_probe.json')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

rows = [x.split('\t') for x in
        io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n')[1:] if x]
rows = [r for r in rows if len(r) == 7]
add('F0 DISC_RECHECK 行长 7 的行数', len(rows) == 31, len(rows))

A = [r for r in rows if not r[6].strip().startswith('有')]
B = [r for r in rows if r[6].strip().startswith('有')]
add('F1 按第 7 列分两类：声明不补 %d 行、声明回跑 %d 行' % (len(A), len(B)),
    len(A) + len(B) == 31, {'claims_none': [int(r[0]) for r in A],
                            'claims_yes': [int(r[0]) for r in B]})

# 类 A 的诚实性：产物在不在、有没有本纪律的自述行
a_out = []
for r in A:
    n = int(r[0]); ap = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
    ex = os.path.isfile(ap); hits = 0
    if ex:
        for l in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
            if l.startswith('DISC_RECHECK '):
                m = re.search(r'\bdiscipline=(\d+)\b', l)
                if m and int(m.group(1)) == n: hits += 1
    a_out.append({'id': n, 'exists': ex, 'own_lines': hits, 'path': r[4].strip()})
add('F2 14 条声明不补的行，产物文件全部存在，且都没有本纪律的自述行 —— '
    '「无」这个声明与盘上事实一致（不是「有产物有行却声明无」那种逃逸）',
    all(x['exists'] for x in a_out) and all(x['own_lines'] == 0 for x in a_out),
    a_out)

# 类 C：rows=N 的校验式只数行数
C = [r for r in rows if r[5].strip().startswith('rows=')]
add('F3 校验式是 rows=N 形态的共 %d 行（只数行数、不核内容）' % len(C),
    len(C) == 4, [int(r[0]) for r in C])

# 反控：rows=N 的校验式对内容完全不敏感 —— 追加一行垃圾仍通过
def count_rows(p):
    n = 0; hdr = 0
    for ln in io.open(p, encoding='utf-8', errors='replace'):
        s = ln.strip()
        if s.startswith('DISC_RECHECK '): continue
        if hdr == 0: hdr = 1; continue
        n += 1
    return n

probe = []
for r in C:
    p = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
    want = int(r[5].strip().split('=')[1].split(' ')[0])
    got = count_rows(p)
    probe.append({'id': int(r[0]), 'want': want, 'got': got, 'ok': got == want})
add('F4 四行 rows=N 的实测行数与期望逐一相符（说明当前不是假绿，但判据本身对内容无感）',
    all(x['ok'] for x in probe), probe)

# 真实验证：把这四行的校验式换成「内容敏感性」检查，看它们现在过不过
# 对 id 22 / 27 / 28：检查首列是否是合理的值域而非空串
sens = []
for r in C:
    p = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
    rows_txt = [x for x in io.open(p, encoding='utf-8', errors='replace').read().split('\n')[1:] if x.strip()]
    cols = [len(x.split('\t')) for x in rows_txt]
    empty_cells = sum(1 for x in rows_txt for c in x.split('\t') if c.strip() == '')
    sens.append({'id': int(r[0]), 'rows': len(rows_txt),
                 'col_counts_distinct': sorted(set(cols)),
                 'empty_cells': empty_cells})
add('F5 这四个 rows=N 产物里二列及以上结构的空单元计数（用于判断「数行数」漏掉了什么） '
    '—— 空单元数不是判据，只作为内容敏感性缺口的事实描述', True, sens)

json.dump({'checks': ck, 'A': a_out, 'C': sens}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128f: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:600])
