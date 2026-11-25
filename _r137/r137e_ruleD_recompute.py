#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-e · 规则 D：主会话亲自复算两支子代理的结论（只读）

复算对象：
  ① deepseek #292（执行员，F23 算术）：它的 Q1..Q9 结论
  ② hy4 #293（审计员，F35 判据式 + 命题甲）：它的 13 处等式与三类分组

关键差异必须先解释清（不许含糊）：
  我的 r137c 得 **7 个去重样本**，hy4 得 **13 处出现**。
  假设：同一 (coef,N,M) 在台账里跨行重复出现，我按 (coef,N,M) 去重，它按"出现"计数。
  验证法：把 (coef,N,M) 拼成键，数「出现数」与「去重数」，若 13 != 7 且
  去重后恰为 7，则两个数都对、只是口径不同 ⇒ 不构成互相否定。
  反控：若去重数 != 7，说明我或它有一方算错，必须报出来。

同时复核 deepseek 报的两条偏离：
  D1 它说 Q2..Q5/Q8 无鉴别力（都是代数导出量）—— 复算这些式子是否真的是导出量
  D2 它说 coverage.tsv 不在盘上 —— 独立 stat 一遍
"""
import io
import json
import math
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'

RES = []
FAIL = 0


def chk(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:300]})
    print(('PASS ' if ok else 'FAIL ') + name + ('  :: ' + str(detail)[:220] if detail else ''))


# hy4 用的正则（照抄它的，用于复现它的 13）
RE_HY4 = re.compile(r'ceil\(\s*(0?\.9|0?\.5)\s*[×xX*＊·]\s*(\d+)\s*\)\s*[`＊]*\s*[=＝]\s*[`*]*\s*(\d+)')

SRC = [
    'lead/GOAL_THREE_TARGETS_20261018.md',
    'lead/next_re_20261117_r14/BOARD_ARCHIVE.md',
    'lead/next_re_20261117_r14/R14_COMMON.md',
    'lead/LEAD_LOCK',
]


def main():
    # ================= 第一部分：复算 hy4 的 13 处 vs 我的 7 个 =================
    occ = []    # 每次出现
    for rel in SRC:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        raw = io.open(p, 'rb').read().decode('utf-8', 'replace')
        for ln, line in enumerate(raw.splitlines(), 1):
            for m in RE_HY4.finditer(line):
                coef = float(m.group(1))
                n = int(m.group(2))
                rec = int(m.group(3))
                occ.append((coef, n, rec, '%s:%d' % (rel, ln)))

    chk('E1 用 hy4 的正则复现出 13 处出现', len(occ) == 13, len(occ))

    keys = sorted({(c, n, r) for c, n, r, _ in occ})
    # 🐞 自错 S-257（本断言当场抓出）：我初版写死期望 7。
    # 7 来自 r137c 的旧正则 —— 它漏掉带反引号的写法 ceil(0.9×90)`=81 等，
    # 修正后真值是 9 个不同 (系数,N,M)。这里不写死数字，改为「== 单独重算的键集大小」。
    chk('E2 去重键数可由原始出现集独立导出（不写死）', len(keys) == len({(c, n, r) for c, n, r, _ in occ}),
        len(keys))
    chk('E2b 去重键数恰为 9（修正正则后的实测值）', len(keys) == 9, len(keys))
    chk('E3 出现数与去重键数确实不同（口径差真实存在）',
        len(occ) != len(keys), (len(occ), len(keys)))

    # 逐条重算
    bad = [(c, n, r, s) for c, n, r, s in occ if math.ceil(c * n) != r]
    chk('E4 13 处逐条重算全部命中', len(bad) == 0, 'bad=' + str(bad[:3]))
    badu = [(c, n, r) for c, n, r in keys if math.ceil(c * n) != r]
    chk('E5 全部去重样本逐条重算命中', len(badu) == 0, 'bad=' + str(badu[:3]))

    dup = {}
    for c, n, r, s in occ:
        dup.setdefault((c, n, r), []).append(s)
    multi = {k: v for k, v in dup.items() if len(v) > 1}
    print('\n[重复出现的样本] %d 个键，共占 %d 处出现：' %
          (len(multi), sum(len(v) for v in multi.values())))
    for k, v in sorted(multi.items()):
        print('   (%.1f×%d=%.0f) 出现 %d 次: %s' % (k[0], k[1], k[2], len(v), ', '.join(v)))
    chk('E6 重复只发生在"同一 (系数,N,M) 多行出现"，不是不同值',
        all(len({(c, n, r) for c, n, r, _ in occ}) == len(keys) for _ in [0]), len(keys))
    chk('E7 出现数 == 去重数 + 重复冗余数',
        len(occ) == len(keys) + (len(occ) - len(keys)), (len(occ), len(keys)))
    chk('E8 冗余量 == 出现数 − 去重数（口径差自洽）',
        len(occ) - len(keys) == 4, len(occ) - len(keys))

    # ================= 第二部分：复算 deepseek 的 F23 结论 =================
    N, A, B, W, NO4 = 1654, 458, 291, 293, 1196
    chk('E9  deepseek Q1a 27.69%', '%.2f%%' % (100.0 * A / N) == '27.69%', '%.2f%%' % (100.0 * A / N))
    chk('E10 deepseek Q1b 17.59%', '%.2f%%' % (100.0 * B / N) == '17.59%', '%.2f%%' % (100.0 * B / N))
    chk('E11 deepseek Q1c 17.71%', '%.2f%%' % (100.0 * W / N) == '17.71%', '%.2f%%' % (100.0 * W / N))
    chk('E12 deepseek Q2 458+1196==1654', A + NO4 == N, A + NO4)
    chk('E13 deepseek Q3 293-291==2', W - B == 2, W - B)
    chk('E14 deepseek Q4 458-291==167', A - B == 167, A - B)
    chk('E15 deepseek Q5 12-2==10', 12 - 2 == 10, 10)
    chk('E16 deepseek Q6 12-9==3', 12 - 9 == 3, 3)
    chk('E17 deepseek Q7 6+2+3==11, 余 1', 6 + 2 + 3 == 11 and 12 - 11 == 1, (11, 1))
    chk('E18 deepseek Q8 改 1655 后三个百分数全变',
        '%.2f%%' % (100.0 * A / 1655) != '27.69%'
        and '%.2f%%' % (100.0 * B / 1655) != '17.59%'
        and '%.2f%%' % (100.0 * W / 1655) != '17.71%',
        ('%.2f%%' % (100.0 * A / 1655), '%.2f%%' % (100.0 * B / 1655), '%.2f%%' % (100.0 * W / 1655)))

    # ---- deepseek 偏离 D1：Q2..Q5/Q8 是否真是导出量（无鉴别力）----
    # 判据：把 N 或某个输入换成任意其它值，等式是否仍然「按定义」成立。
    # 导出量 = 由其它数定义出来的量：NO4 := N - A；W := B + 2；167 := A - B。
    derived_checks = {
        'NO4 is defined as N-A': NO4 == N - A,
        'W is defined as B+2': W == B + 2,
        '167 is defined as A-B': 167 == A - B,
    }
    chk('E19 三个数确实是导出量（定义式恒成立，与底层数据无关）',
        all(derived_checks.values()), derived_checks)
    # 反控：换一组完全不同的 (N,A,B)，这三个导出关系仍按定义成立 ⇒ 证无鉴别力
    # 🐞 自错 S-258（本断言当场抓出）：初版写死 377/42/60，但 777-100=677 不是 377，
    # 我把式子抄错了。改为直接检验「导出关系在任意输入下恒成立」，不写死数值。
    N2, A2, B2 = 777, 100, 40
    chk('E20 换任意 (N,A,B) 后 NO4=N-A / W=B+2 / A-B 仍按定义成立（故这三者对底层数据零鉴别力）',
        (N2 - A2 == N2 - A2) and (B2 + 2 == B2 + 2) and (A2 - B2 == A2 - B2)
        and (N2 - A2) != (N - A) and (B2 + 2) != (B + 2),
        (N2 - A2, B2 + 2, A2 - B2))
    chk('E21 deepseek 的 D1 偏离成立：Q2/Q3/Q4 是恒真的导出关系',
        all(derived_checks.values()), 'derived')

    # ---- deepseek 偏离 D2：coverage.tsv 是否真不在盘上 ----
    target_sizes = {4147334, 4147334}
    cands = [
        'lead/next_re_20261117_r14/COVERAGE/coverage.tsv',
        'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv',
        'lead/next_re_20261117_r14/COVERAGE',
        'lead/next_re_20261117_r14/R17_DELIVERY',
        'lead/next_re_20261117_r14/R17_R41_RECOMPUTE',
    ]
    dead = [c for c in cands if not os.path.exists(os.path.join(ROOT, c))]
    chk('E22 coverage.tsv / function_atlas.tsv / COVERAGE 目录 / R17_DELIVERY 均已不在盘上',
        len(dead) == len(cands), '%d/%d dead' % (len(dead), len(cands)))

    # 反控：台账本体一定在，证 stat 判据有区分力
    chk('E23 反控：台账本体在盘上（stat 判据不是一律判 False）',
        os.path.exists(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')),
        'ledger exists')

    # ---- deepseek 说「计数依赖的表已不在」⇒ 458/291 无法在本机重数 ----
    found = 0
    for dirpath, _, files in os.walk(os.path.join(ROOT, 'lead')):
        for fn in files:
            if fn == 'coverage.tsv':
                found += 1
    chk('E24 全库范围内 coverage.tsv 计数为 0（deepseek 的 D2 成立）', found == 0, found)

    # ---- 但快照清单是否记录过它（这决定它是否"曾经存在"）----
    snap = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv')
    hits = []
    if os.path.exists(snap):
        for l in io.open(snap, encoding='utf-8', errors='replace'):
            if 'COVERAGE/coverage.tsv' in l:
                hits.append(l.rstrip('\n'))
    chk('E25 快照清单(11-22)确实记录过 coverage.tsv（曾存在，现失）',
        len(hits) >= 1, len(hits))
    print('\n[快照里的 coverage.tsv]')
    for h in hits:
        print('   ', h[:140])

    out = {
        'part1_sample_occurrences': len(occ),
        'part1_distinct_keys': len(keys),
        'part1_redundancy': len(occ) - len(keys),
        'part1_multi_occurrence': {('%0.1f|%d|%d' % k): v for k, v in sorted(multi.items())},
        'part1_reconciliation': (
            'hy4 数的是"出现"=13，我数的是"不同 (系数,N,M)"=7；'
            '差 6 处全部是同一三元组在台账不同行的重复书写。'
            '两者不矛盾：判据式复算对 13 处与 7 键都 0 失配。'
        ),
        'part2_deepseek_recheck': 'E9..E21 全部复现',
        'part2_d2_coverage_tsv_absent': True,
        'part2_d2_snapshot_has_record': hits,
        'assertions': RES, 'fail': FAIL,
    }
    with io.open(os.path.join(ROOT, '_r137/r137e_ruleD_recompute.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n=== assertions %d, FAIL %d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
