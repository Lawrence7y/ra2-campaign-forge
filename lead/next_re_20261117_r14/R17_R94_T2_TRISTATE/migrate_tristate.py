# -*- coding: utf-8 -*-
r"""migrate_tristate.py -- R55-T2 · 把 DISC_RECHECK.tsv 第 7 列「有」拆成三态。

只读原表 SRC，写新表 DST（DISC_RECHECK.tristate.tsv），**绝不覆盖 SRC**。
按卡要求：只交付本脚本，不执行迁移（调用 migrate() 才会落盘）。

用法:
    python migrate_tristate.py            # 执行迁移 + 写后自校验（本任务不运行）
    python migrate_tristate.py --check    # 只自校验已生成的新表，不写

判别式（REPORT Q1 逐字）:
    若 col7 以「无」开头                -> 第三态，col7 原样保留（无（仅立条当轮自带））
    否则（col7 以「有」开头）:
        expr = col6 按首个空格截断（与 check_disc.run_expr 一致，去 ✓(...) 注释）
        若 expr 匹配 ^(rows|bytes)=\\d+$ 或 ^grep=.*\\s\+\\d+$  -> 有·可核
        否则                                             -> 有·无自产出机制
"""
import io, os, re, sys
from collections import Counter

R14 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(R14, 'DISC_RECHECK.tsv')
DST = os.path.join(R14, 'DISC_RECHECK.tristate.tsv')

NEW_V = '有·可核'
NEW_N = '有·无自产出机制'

# 数值可重算校验式：rows=N / bytes=N（产物为脚本生成的结构化表/定长文件）
RE_ROWS = re.compile(r'^(rows|bytes)=\d+$')
# grep=...\s+<数字>：产物内含「可重算的数值断言行」（如 未核验 0 / 体例通过 15）
# 注意 TSV 里是字面反斜杠，故正则写 \\s；\s 用转义表达数值前的空白。
RE_GREP_NUM = re.compile(r'^grep=.*\\s\+\d+$')


def read_lines(p):
    with io.open(p, encoding='utf-8', newline='') as f:
        return f.read().split('\n')


def classify(row):
    """入参 7 列 list，返回第 7 列新值。纯函数、幂等（已是新值则原样返回）。"""
    c7 = row[6].strip()
    if c7 == NEW_V or c7 == NEW_N:
        return c7                                  # 已迁移 -> 原样（幂等）
    if not c7.startswith('有'):
        return c7                                  # 无（仅立条当轮自带）-> 原样保留
    expr = row[5].strip().split(' ')[0]           # 与 check_disc.py run_expr 同：去 ✓ 注释
    if RE_ROWS.match(expr) or RE_GREP_NUM.match(expr):
        return NEW_V
    return NEW_N


def build_output():
    """在内存中构造 (src_lines, dst_lines, changes)；不落盘。"""
    src_lines = read_lines(SRC)
    out, changes = [src_lines[0]], []
    for ln in src_lines[1:]:
        if ln == '':
            continue
        row = ln.split('\t')
        if len(row) != 7:
            raise ValueError('row cols != 7: %r' % ln[:80])
        new7 = classify(row)
        out.append('\t'.join(row[:6] + [new7]))
        if new7 != row[6]:
            changes.append((row[0], row[6], new7))
    return src_lines, out, changes


def migrate():
    """唯一落盘入口：写 DST，不碰 SRC。"""
    if os.path.abspath(SRC) == os.path.abspath(DST):
        raise RuntimeError('SRC == DST forbidden')
    _, out, changes = build_output()
    with io.open(DST, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(out))
    print('wrote %s : %d data rows, %d col7 changes (SRC untouched)'
          % (DST, len(out) - 1, len(changes)))
    return changes


def selfcheck():
    """写后自校验：28 行 × 7 列、其余 6 列逐字未变、无「有→无」、新值闭集合。"""
    s, d, _ = build_output()                       # 期望值（内存重算）
    s = [l for l in s if l != '']
    if os.path.isfile(DST):
        d_actual = [l for l in read_lines(DST) if l != '']
    else:
        d_actual = d                               # --check 前未落盘时，校验内存结果
    errs = []
    if len(s) != 29:
        errs.append('SRC lines %d != 29' % len(s))
    if len(d_actual) != 29:
        errs.append('DST lines %d != 29' % len(d_actual))
    if d_actual != d:
        errs.append('DST != freshly recomputed output (not idempotent / stale)')
    if s and d_actual and s[0] != d_actual[0]:
        errs.append('header changed')
    for i in range(1, min(len(s), len(d_actual))):
        a, b = s[i].split('\t'), d_actual[i].split('\t')
        if len(a) != 7 or len(b) != 7:
            errs.append('row %d cols %d/%d' % (i, len(a), len(b)))
            continue
        for k in range(6):
            if a[k] != b[k]:
                errs.append('row %s col%d changed' % (a[0], k + 1))
        if a[6].startswith('有') and b[6].startswith('无'):
            errs.append('row %s 有->无 FORBIDDEN' % a[0])
        if not (b[6].startswith('有') or b[6].startswith('无')):
            errs.append('row %s bad new col7 %r' % (a[0], b[6]))
    counts = Counter(d_actual[i].split('\t')[6].strip() for i in range(1, len(d_actual)))
    print('new col7 counts:', dict(counts))
    print('selfcheck:', 'PASS' if not errs else 'FAIL')
    for e in errs:
        print('  ERR', e)
    return not errs, counts


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--check' in args:
        sys.exit(0 if selfcheck()[0] else 1)
    migrate()
    sys.exit(0 if selfcheck()[0] else 1)
