#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R87 · C9 占位判据 v4（最终）。
演进与自错（全部由反控抓出，逐条记）：
  v1 「包含」扫长正文        -> 误伤 5 行（正文里正常出现「无」「—」）
  v2 「整格归一化 + <=6 前缀」-> 误伤 0，但漏抓 GARBAGE-CRITERION-OTHER
  v3 「ASCII 无界前缀 + CJK <=6 前缀」-> 报告值全绿；但我另构造 '无锚点'/'空表'/'略图'
     立刻误抓 5 例 —— 那个 6 是**我拍的阈值**，不是从数据来的（违反 R86 DM13）。
  v4 「整格等于任何占位词」+「ASCII 占位词无界前缀」，**删除 CJK 前缀规则**。
     理由：中文常用字（无/空/略/待）作正常值开头不可预测，任何前缀阈值都会误伤；
     ASCII 占位词作正常中文值开头几乎不可能。
本模块供门禁 import；自带 self_test()。"""
import re, unicodedata

TOK_ASCII = ('garbage', 'tbd', 'xxx', 'na', 'none', 'null', 'todo', 'fixme',
             'placeholder', 'dummy', 'foo', 'bar', 'lorem')
TOK_ANY   = TOK_ASCII + ('待定', '待补', '略', '同上', '无', '空', '占位', '占位符', '?', '-', '/')
_BRACES = re.compile(r'[（(][^）)]*[）)]')

def norm(s):
    v = _BRACES.sub('', s or '')
    return ''.join(ch for ch in v
                   if not unicodedata.category(ch).startswith('P') and not ch.isspace()).lower()

def is_placeholder(s):
    """(bool, why)。空/整格占位词/ASCII 占位词前缀 => 占位。"""
    v = norm(s)
    if v == '':
        return True, 'empty-after-norm'
    if v in TOK_ANY:
        return True, 'whole-cell %s' % v
    for t in TOK_ASCII:
        if v.startswith(t):
            return True, 'ascii-prefix %s' % t
    return False, ''

def self_test(rows3, rows4, verbose=True):
    """rows3/rows4: 现有表第3列/第4列取值列表。返回 FAIL 数。"""
    f = 0
    def ck(n, c, d=''):
        nonlocal f
        if verbose:
            print(('  PASS ' if c else '  FAIL ') + n + (('  | ' + str(d)) if d else ''))
        if not c: f += 1
    bad = [x for x in list(rows3) + list(rows4) if is_placeholder(x)[0]]
    ck('S1 现有表零误伤', not bad, bad[:4])
    ctl = ['GARBAGE-CRITERION-OTHER', 'TBD-', '无（占位）', 'xxx-yet', '—', 'N/A', '待定',
           '...', '  ', 'GARBAGE', '（无）', 'none', 'TODO', '占位符', '略', '同上', 'n/a',
           'placeholder', 'FIXME-later', 'dummy']
    miss = [c for c in ctl if not is_placeholder(c)[0]]
    ck('S2 构造占位全抓', not miss, miss)
    neg = ['v5.8 基线：人工核验类 0', '节号体例锚逐条列名', 'C3 双相反向注入',
           '三方混用量 339/339', '「无产物」时间顺序核查', '2×2 溯源表逐格复算',
           '零信息格（与 R72 的 W_only 同族', 'C′ 内备份副本 1,468 件 / 149,493,508 B',
           'FAIL 也留盘', '13 条 PARTIAL 全量复算（驳回 9）', '无产物时间顺序核查',
           '无锚点', '空表', '略图', '待定事项', '无效项', '安全边界', '无产物核查']
    fp = [n for n in neg if is_placeholder(n)[0]]
    ck('S3 正常值零误抓（含 v3 会误抓的 6 例）', not fp, fp)
    OLD = ('', '无', 'GARBAGE', 'TBD', 'xxx', 'XXX', '?', '-')
    lost = [c for c in ctl if c.strip() in OLD and not is_placeholder(c)[0]]
    ck('S4 无回归（老抓的新也抓）', not lost, lost)
    gain = sum(1 for c in ctl if c.strip() not in OLD and is_placeholder(c)[0])
    ck('S5 增益 > 0', gain > 0, 'gain=%d' % gain)
    return f

if __name__ == '__main__':
    import io
    SRC = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
    body = [l.split('\t') for l in io.open(SRC + '/DISC_RECHECK.tsv', encoding='utf-8').read().split('\n')[1:] if l.strip()]
    print('=== place_r87 self_test ===')
    n = self_test([r[2] for r in body], [r[3] for r in body])
    print('FAIL = %d' % n)
    raise SystemExit(1 if n else 0)
