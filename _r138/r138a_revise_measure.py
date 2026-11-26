# -*- coding: utf-8 -*-
"""r138a_revise_measure.py —— R138 主会话独立复算：F23/F24/F35 正文修订所需的四项数字。

不复用任何子代理代码；四项各自带正反控。
断言失败即抛 AssertionError（非零退出），不许静默。

用法: timeout 300 python3 _r138/r138a_revise_measure.py
"""
import io, os, sys, json, math, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI = os.path.join(R14, 'R17_R104_FACTINDEX_V532', 'FACT_INDEX.tsv')
TIER = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
OUT = os.path.join(ROOT, '_r138', 'r138a_revise_measure.json')

N_PASS = N_FAIL = 0
FAILS = []


def chk(cond, label, extra=''):
    global N_PASS, N_FAIL
    if cond:
        N_PASS += 1
        print('  PASS ' + label)
    else:
        N_FAIL += 1
        FAILS.append(label + (' | ' + str(extra) if extra else ''))
        print('  FAIL ' + label + (' | ' + str(extra) if extra else ''))


def load_facts():
    d = {}
    hdr = []
    for ln in io.open(FI, encoding='utf-8'):
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 5 and c[0]:
            if re_id().match(c[0]):
                d[c[0]] = c
            else:
                hdr.append(c[0])
    return d, hdr


def re_id():
    import re
    return re.compile(r'^F\d{2}$')


def stat(p):
    try:
        return True, os.stat(p).st_size
    except OSError:
        return False, None


def main():
    res = {}
    facts, hdr = load_facts()
    print('= 项 0 · FACT_INDEX 结构 =')
    chk(len(facts) == 54, 'F01..F54 共 54 条事实项（表头已排除）', len(facts))
    chk(hdr == ['fact_id'], '表头行恰 1 条且为 fact_id', hdr)
    chk(all(len(v) == 5 for v in facts.values()), '全部行 5 列',
        sorted({len(v) for v in facts.values()}))
    chk('F23' in facts and 'F35' in facts, 'F23/F35 均在表内')
    chk(sorted(facts) == ['F%02d' % i for i in range(1, 55)],
        'F01..F54 编号连续无缺')

    # ---------- 项 1 · F23 十二行分解 ----------
    print('= 项 1 · F23 十二行分解闭合性 =')
    lim23 = facts['F23'][4]
    stmt23 = facts['F23'][1]
    txt = lim23 + stmt23
    # 四个数字必须逐字出现在原文
    chk('12 行' in txt, '原文出现「12 行」')
    chk('6 行为否定式' in txt, '原文出现「6 行为否定式」')
    chk('2 行为 callers 计数' in txt, '原文出现「2 行为 callers 计数」')
    chk('3 行' in txt, '原文出现「3 行」')
    parts = (6, 2, 3)
    total = 12
    chk(sum(parts) == 11, '6+2+3 = 11（分项和）', sum(parts))
    gap = total - sum(parts)
    chk(gap == 1, '12 与 11 相差 1 行，该行在分解里无归属', gap)
    res['f23_decomp'] = {'parts': parts, 'sum': sum(parts), 'total': total, 'gap': gap}

    # ---------- 项 2 · coverage.tsv 在盘性 ----------
    print('= 项 2 · coverage.tsv 在盘性 =')
    hits = []
    for dp, dn, fn in os.walk(ROOT):
        if '.git' in dp.split(os.sep):
            continue
        for f in fn:
            if f == 'coverage.tsv':
                hits.append(os.path.join(dp, f))
    chk(len(hits) == 0, 'coverage.tsv 全库命中 0', hits[:3])
    dirs = {}
    for d in ('COVERAGE', 'R17_DELIVERY', 'R17_R41_RECOMPUTE'):
        p = os.path.join(R14, d)
        dirs[d] = os.path.isdir(p)
    chk(not any(dirs.values()), '三个依赖目录均不存在', dirs)
    # 正控：本脚本自己一定存在
    ok, sz = stat(os.path.abspath(__file__))
    chk(ok and sz > 0, '正控：本脚本存在且非空', sz)
    # 负控：确定不存在的路径
    ok2, _ = stat(os.path.join(ROOT, '__no_such_dir__', 'coverage.tsv'))
    chk(not ok2, '负控：构造的不存在路径判为不存在')
    res['coverage'] = {'hits': len(hits), 'dirs': dirs}

    # ---------- 项 3 · F24 清单现盘一致性 ----------
    print('= 项 3 · F24 清单现盘一致性 =')
    rows = [l.rstrip('\n').split('\t') for l in io.open(TIER, encoding='utf-8') if l.strip()]
    chk(rows[0] == ['rel', 'bytes', 'source', 'why_content'], '表头 4 列符合', rows[0])
    body = rows[1:]
    chk(len(body) == 4417, '清单 4,417 行', len(body))
    same = diff = gone = 0
    same_b = diff_b = gone_b = 0
    decl = 0
    diff_list = []
    for rel, by, src, why in body:
        n = int(by)
        decl += n
        p = rel.replace('\\', '/')
        p = p if p.startswith('lead/') else os.path.join('lead', p)
        ap = os.path.join(ROOT, p)
        ok, sz = stat(ap)
        if not ok:
            gone += 1
            gone_b += n
        elif sz == n:
            same += 1
            same_b += n
        else:
            diff += 1
            diff_b += n
            diff_list.append((p, n, sz, sz - n))
    chk(decl == 737517286, '声明总字节 737,517,286', decl)
    chk(same + diff + gone == 4417, '三桶件数之和 = 4,417', (same, diff, gone))
    chk(same_b + diff_b + gone_b == decl, '三桶字节之和 = 声明总字节',
        (same_b, diff_b, gone_b))
    chk(same == 64 and same_b == 26846620, '存在且同字节 64 件 / 26,846,620 B',
        (same, same_b))
    chk(diff == 1, '存在但字节不同 1 件', diff)
    chk(gone == 4352 and gone_b == 709757429, '不存在 4,352 件 / 709,757,429 B',
        (gone, gone_b))
    # 唯一差异件必须恰是被剔 bounds 段那件
    chk(len(diff_list) == 1 and diff_list[0][1] == 913237
        and diff_list[0][2] == 17624355 and diff_list[0][3] == 16711118,
        '唯一差异件 = a2_sites.json，清单 913,237 vs 盘 17,624,355，差 +16,711,118',
        diff_list)
    res['f24_manifest'] = {'decl': decl, 'same': same, 'same_b': same_b,
                            'diff': diff, 'diff_b': diff_b,
                            'gone': gone, 'gone_b': gone_b,
                            'live_total_b': same_b + diff_b,
                            'live_bytes_note': 'same_b + 盘上实际 a2_sites 字节'}
    live_b = same_b + sum(x[2] for x in diff_list)
    res['f24_manifest']['live_b'] = live_b
    chk(live_b == 26846620 + 17624355, '现盘可 stat 到的实际字节合计', live_b)

    # ---------- 项 4 · F35 证据路径条数 ----------
    print('= 项 4 · F35 证据路径与判据式 =')
    ev35 = facts['F35'][3]
    ents = [x for x in ev35.split(';') if x.strip()]
    chk(len(ents) == 1, 'F35 evidence_paths 只有 1 条', ents)
    chk('PANEL.md' in ents[0], '该 1 条即已失的 PANEL.md', ents[0])
    exists35 = [e for e in ents if os.path.exists(
        os.path.join(ROOT, e.split('(')[0].replace('\\', '/')))]
    chk(len(exists35) == 0, '该条在盘不存在', exists35)
    chk('proved_strict' in facts['F35'][1], '正文含 proved_strict 定义式')
    res['f35'] = {'entries': len(ents), 'on_disk': len(exists35)}

    # F35 判据式在台账里的显式等式复算
    # R138 发现：R137 把「假样本 ceil(0.9x100)=91 判不成立」的原话写进了三份台账，
    # 而 (0.9,100,91) 恰好命中本正则。故必须把「真实判据等式」与「假样本引用」分开统计，
    # 否则要么把假样本当失配（假 FAIL），要么把它删掉（抹掉 R137 的反控记录）。
    print('= 项 5 · F35 ceil 判据式复算 =')
    pat = re_ceil()
    FAKE_CTX = u'假样本'
    live, fake = [], []
    for path in [os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                 os.path.join(R14, 'BOARD_ARCHIVE.md'),
                 os.path.join(R14, 'R14_COMMON.md'),
                 os.path.join(ROOT, 'lead', 'LEAD_LOCK')]:
        t = io.open(path, encoding='utf-8', errors='replace').read()
        for m in pat.finditer(t):
            coef = float(m.group(1))
            n = int(m.group(2))
            stated = int(m.group(3))
            calc = int(math.ceil(coef * n))
            # 同一行内若出现「假样本」字样，该处是引用假样本而非引用真实判据
            ls = t.rfind(u'\n', 0, m.start()) + 1
            le = t.find(u'\n', m.end())
            line = t[ls:le if le >= 0 else len(t)]
            rec = (path.rsplit(os.sep, 1)[-1], coef, n, stated, calc)
            (fake if FAKE_CTX in line else live).append(rec)
    bad = [s for s in live if s[3] != s[4]]
    chk(len(live) >= 9, '真实判据等式（排除假样本引用）>= 9 处', len(live))
    chk(len(bad) == 0, '真实判据等式 math.ceil 复算 0 失配', bad)
    chk(len(fake) == 3, '假样本引用恰 3 处（三份台账各 1）', len(fake))
    chk(all(s[1:4] == (0.9, 100, 91) for s in fake),
        '3 处假样本均为 (0.9,100,91)', [s[1:4] for s in fake])
    chk(all(s[3] != s[4] for s in fake),
        '假样本按设计就不成立（91 != ceil(0.9x100)=90）—— 这是反控，不是失配',
        [(s[3], s[4]) for s in fake])
    keys = {(s[1], s[2], s[3]) for s in live}
    res['f35_ceil'] = {'live_occurrences': len(live), 'distinct_keys': len(keys),
                       'mismatch': len(bad), 'fake_sample_refs': len(fake),
                       'coefs': sorted({s[1] for s in live})}

    # 反控：ceil 改 ceil+1 命中归零（只在真实判据等式上测）
    bad2 = [s for s in live if s[3] != s[4] + 1]
    chk(len(bad2) == len(live), '反控：ceil+1 时真实判据等式全部失配', len(bad2))
    # 反控：floor 与 ceil 至少在若干样本上不同（取整规则不是等价写法）
    floordiff = [s for s in live if int(math.floor(s[1] * s[2])) != s[4]]
    chk(len(floordiff) > 0, '反控：floor 与 ceil 在若干样本给出不同值',
        (len(floordiff), len(live)))

    res['assertions'] = {'pass': N_PASS, 'fail': N_FAIL, 'fail_list': FAILS}
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True))
        f.write(u'\n')
    print('\n== 断言 %d PASS / %d FAIL ==' % (N_PASS, N_FAIL))
    return 0 if N_FAIL == 0 else 1


def re_ceil():
    import re
    # 允许等号左边带反引号/空白；乘号允许 x * × 乘
    return re.compile(u'ceil\\(\\s*(0\\.\\d+)\\s*[x×*乘]\\s*(\\d+)\\s*\\)'
                      u'[`\\s]*[=＝][`\\s]*(\\d+)')


if __name__ == '__main__':
    sys.exit(main())
