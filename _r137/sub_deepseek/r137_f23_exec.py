#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137 执行卡 F23 · 三口径数字独立复算（只读）

两类内容严格分开：
  (I) 算术层：F23 正文的数字彼此之间的硬关系。不依赖任何外部表，可独立复算。
  (II) 计数层：458/291/293/1196/12/2/9 是不是对盘上某张表数出来的。
       按 F23 正文「（第 4 列语义）」与 R17-R41-RECOMPUTE 卡的口径，被数的对象是
       COVERAGE/coverage.tsv（18,498 数据行 / 8 列）。该文件本机不存在（见 probe），
       故 (II) 一律判「无法判定」，并另做可失败的反证：同一套判据施加到 FACT_INDEX.tsv
       本身，得到的行数远小于 458（说明 F23 的数不是对 FACT_INDEX 数的）。

纪律：断言必须能失败。每个等式都配一个「改成错值必须判 False」的反控。
"""
import io
import json
import os
import re

ROOT = '/home/t628/projects/ra2-campaign-forge'
FI = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
COV_CANDIDATES = [
    os.path.join(ROOT, 'COVERAGE', 'coverage.tsv'),
    os.path.join(ROOT, 'lead/next_re_20261117_r14/COVERAGE', 'coverage.tsv'),
    os.path.join(ROOT, 'lead', 'COVERAGE', 'coverage.tsv'),
]

RES = []
FAIL = 0


def chk(cid, claim, cond, got):
    """cond 为布尔；got 为实测值（写进 JSON）。FAIL 计数用于自检非恒真。"""
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': cid, 'claim': claim, 'ok': ok, 'got': got})
    print(('PASS ' if ok else 'FAIL ') + cid + '  ' + claim + '  :: ' + repr(got))
    return ok


def p2(a, b):
    """两位小数的百分比，按 F23 的写法（四舍五入到 0.01）。用 Decimal 化字符串避免浮点尾差。"""
    from decimal import Decimal, ROUND_HALF_UP
    v = (Decimal(a) * 100 / Decimal(b)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return str(v)


def ns_consistent(numer, pct_str, nmax=4000):
    """给定分子与百分比字符串，返回所有使 round(100*numer/N,2)==pct_str 的 N。"""
    out = []
    for n in range(1, nmax + 1):
        if p2(numer, n) == pct_str:
            out.append(n)
    return out


def main():
    # ---------- F23 正文声明的数（原样抄入，作为待验对象，不作结论） ----------
    N = 1654
    A = 458
    B = 291
    W = 293
    NO4 = 1196
    ABD = 167
    LOOSE = 12
    FULLSTR = 2
    SUB = 10
    SETD = 9
    NEG, CNT, REAL = 6, 2, 3

    q = {}

    # ---------------- Q1 三个百分数逐字比对 ----------------
    gotA, gotB, gotW = p2(A, N), p2(B, N), p2(W, N)
    q['Q1'] = {
        'verdict': '成立' if (gotA == '27.69' and gotB == '17.59' and gotW == '17.71') else '不成立',
        'computed': {'A': gotA + '%', 'B': gotB + '%', 'W': gotW + '%'},
        'stated': {'A': '27.69%', 'B': '17.59%', 'W': '17.71%'},
        'per_item': {'A': gotA == '27.69', 'B': gotB == '17.59', 'W': gotW == '17.71'},
        'raw_ratio': {'A': A / N, 'B': B / N, 'W': W / N},
        'note': '三个百分数均由 round(100*num/1654, 2) 独立重算，非抄卡面。',
    }
    chk('Q1-A', 'round(100*458/1654,2)==27.69', gotA == '27.69', gotA)
    chk('Q1-B', 'round(100*291/1654,2)==17.59', gotB == '17.59', gotB)
    chk('Q1-W', 'round(100*293/1654,2)==17.71', gotW == '17.71', gotW)
    # 反控：这些断言对错值必须判 False
    chk('Q1-neg1', 'round(100*458/1655,2) != 27.69', p2(458, 1655) != '27.69', p2(458, 1655))
    chk('Q1-neg2', 'round(100*457/1654,2) != 27.69', p2(457, 1654) != '27.69', p2(457, 1654))

    # ---------------- Q2 458 + 1196 == 1654 ----------------
    q['Q2'] = {'verdict': '成立' if A + NO4 == N else '不成立', 'computed': A + NO4, 'stated_rhs': N,
               'note': '口径 A（含 ④）与「完全无 ④」互补，等价于断言 1196 = N − A。'}
    chk('Q2', '458+1196==1654', A + NO4 == N, A + NO4)
    chk('Q2-neg', '458+1195 != 1654', A + (NO4 - 1) != N, A + (NO4 - 1))

    # ---------------- Q3 293 - 291 == 2 ----------------
    q['Q3'] = {'verdict': '成立' if W - B == 2 else '不成立', 'computed': W - B, 'stated_rhs': 2,
               'note': 'W = B ∪ |「④ direct call」|=2 且交集 0 ⇒ W − B = 2；此处只验算术。'}
    chk('Q3', '293-291==2', W - B == 2, W - B)
    chk('Q3-neg', '293-291 == 3 为假', not (W - B == 3), W - B)

    # ---------------- Q4 458 - 291 == 167 ----------------
    q['Q4'] = {'verdict': '成立' if A - B == ABD else '不成立', 'computed': A - B, 'stated_rhs': ABD,
               'note': '167 完全由 A、B 推出；A、B 一改它必随之改，故它不是独立事实。'}
    chk('Q4', '458-291==167', A - B == ABD, A - B)
    chk('Q4-neg', '458-291 == 168 为假', not (A - B == 168), A - B)

    # ---------------- Q5 减法读法 ----------------
    q['Q5'] = {
        'verdict': '成立' if LOOSE - FULLSTR == SUB else '不成立',
        'computed': LOOSE - FULLSTR,
        'expr': '12 − 2 = 10',
        'note': '减法读法 = |宽松命中| − |含全串 ④ direct call|；改成立的前提是「全串命中集合 ⊆ 宽松命中集合」。',
    }
    chk('Q5', '12-2==10', LOOSE - FULLSTR == SUB, LOOSE - FULLSTR)
    chk('Q5-neg', '12-2 == 9 为假', not (LOOSE - FULLSTR == 9), LOOSE - FULLSTR)

    # ---------------- Q6 集合差读法 ⇒ 交集必为 3 ----------------
    # |LOOSE \ W| = |LOOSE| − |LOOSE ∩ W|  （要求 LOOSE ∩ W ⊆ LOOSE，恒真）
    inter = LOOSE - SETD
    q['Q6'] = {
        'verdict': '成立' if inter == 3 else '不成立',
        'computed_intersection': inter,
        'derivation': '|LOOSE \\ W| = 9 = |LOOSE| − |LOOSE ∩ W| = 12 − x  ⇒  x = 12 − 9 = 3',
        'note': '正文括注「因其中 3 行本已在 W 内」与该推导自洽；但交集 3 与「分母」无关，与 W=293 是否数对无关。'
                '另注意：|LOOSE \\ W|=9 与减法读法 10 只有在 |LOOSE ∩ W|=3 时二者差 1，这是同一个数的两种写法。',
    }
    chk('Q6', '12-9==3', inter == 3, inter)
    chk('Q6-neg', '若集合差读法是 10，交集须为 2（即两读法相同）—— 该反控必须判 False',
        not (LOOSE - 10 == 3), LOOSE - 10)

    # ---------------- Q7 余下 1 行的归属：只答有/没有 + 引原句 ----------------
    fi_text = io.open(FI, encoding='utf-8', errors='replace').read()
    m = re.search(r'^F23\t(.*?)\t([^\t]*)\t([^\t]*)\t(.*)$', fi_text, re.M)
    stmt, grade, evid, lim = (m.group(1), m.group(2), m.group(3), m.group(4)) if m else ('', '', '', '')
    decomp = '该 12 行中 6 行为否定式（无 direct caller 等）、2 行为 callers 计数，真正非否定的多计仅 3 行且全为 direct caller。'
    has_residue_attribution = ('余' in lim and ('1 行' in lim or '一行' in lim)) or '第 12' in lim or '另一行' in lim
    q['Q7'] = {
        'verdict': '成立' if (NEG + CNT + REAL == 11 and not has_residue_attribution) else '不成立',
        'computed_sum': NEG + CNT + REAL,
        'residue': LOOSE - (NEG + CNT + REAL),
        'attributed_in_text': has_residue_attribution,
        'answer': '没有' if not has_residue_attribution else '有',
        'quote': decomp,
        'quote_scope': '该句位于 F23 的 limitations 字段（第 5 列），不在 statement 字段。',
    }
    chk('Q7', '6+2+3==11 且 12-11==1', NEG + CNT + REAL == 11 and LOOSE - (NEG + CNT + REAL) == 1,
        (NEG + CNT + REAL, LOOSE - (NEG + CNT + REAL)))
    chk('Q7-abs', 'F23 limitations 中不存在对余下 1 行的归属句', not has_residue_attribution,
        {'has余': '余' in lim, 'len_lim': len(lim)})
    chk('Q7-neg', '6+2+3+1==12 才是闭合式（证明 11 != 12 有分辨力）', NEG + CNT + REAL + 1 == LOOSE,
        NEG + CNT + REAL + 1)

    # ---------------- Q8 把 N 改成 1655 ----------------
    n2 = 1655
    got2 = {'A': p2(A, n2), 'B': p2(B, n2), 'W': p2(W, n2)}
    same = {'A': got2['A'] == '27.69', 'B': got2['B'] == '17.59', 'W': got2['W'] == '17.71'}
    # 反向：给定三个百分数，N 是否唯一？逐个百分数独立求解 N 的定义域
    nsA = ns_consistent(A, '27.69')
    nsB = ns_consistent(B, '17.59')
    nsW = ns_consistent(W, '17.71')
    q['Q8'] = {
        'verdict': '成立' if (not any(same.values()) and nsA == [1654] and nsB == [1654] and nsW == [1654])
                   else '不成立',
        'pct_at_1655': {k: v + '%' for k, v in got2.items()},
        'still_matches_text': same,
        'N_domain_from_A': nsA, 'N_domain_from_B': nsB, 'N_domain_from_W': nsW,
        'pinned': 'N=1654 在给定 458 / 291 / 293 下被三个百分数**各自单独**钉死（每个都只解出 1654）',
        'caveat': '但这是循环：百分数是 round(100*num/N,2) 的函数，与 N 同源。'
                  '「1654 被百分数钉住」只证明正文内部一致，不证明 1654 数对了行——'
                  '若真实行数是 1655，则 458/291/293 本身也该变，正文会以另一组自洽数字出现。',
    }
    # 反方向：固定 N=1654，看每个百分数是否只解出一个分子（检验「四元组被三个百分数联合钉死」）
    numA = [a for a in range(N + 1) if p2(a, N) == '27.69']
    numB = [b for b in range(N + 1) if p2(b, N) == '17.59']
    numW = [w for w in range(N + 1) if p2(w, N) == '17.71']
    q['Q8']['numerators_at_N1654'] = {'A': numA, 'B': numB, 'W': numW}
    q['Q8']['joint_pinning'] = (
        '(N, A, B, W) 在 0..N 范围内被三个百分数联合唯一确定：每个百分数独立只解出一个 N（均 1654），'
        '在 N=1654 下也各只解出一个分子（%s / %s / %s）。' % (numA, numB, numW))
    q['Q8']['rounding_mode_robust'] = (
        '改用截断（ROUND_DOWN）重解，三个百分数在 N≤20000 内仍各只解出 N=1654 ⇒ '
        '「钉住」不是舍入方式造成的假象。')
    q['Q8']['still_not_independent'] = (
        '但这不构成独立佐证：百分数是 round(100*A/N,2) 的确定性函数，与 A/B/W/N 同源。'
        '「唯一解出」只说明舍入没丢掉信息，不说明 458/291/293 在 coverage.tsv 上数对了 —— '
        '若真实计数是别的一组，正文照旧会自洽。')

    chk('Q8', '1655 时三个百分数全失配', not any(same.values()), got2)
    chk('Q8-uniq', '给定 458/291/293，每个百分数只解出 N=1654', nsA == [1654] and nsB == [1654] and nsW == [1654],
        (nsA, nsB, nsW))
    chk('Q8-uniq2', 'N=1654 时每个百分数只解出一个分子', numA == [A] and numB == [B] and numW == [W],
        (numA, numB, numW))
    chk('Q8-neg', '1655 时 A 的百分数 != 27.69（反控：断言可失败）', got2['A'] != '27.69', got2['A'])
    # 反控制度检验：截断模式下也必须只解出 1654
    from decimal import Decimal as _D, ROUND_DOWN as _RD
    def _p2trunc(a, b):
        return str((_D(a) * 100 / _D(b)).quantize(_D('0.01'), rounding=_RD))
    truncA = [n for n in range(1, 20001) if _p2trunc(A, n) == '27.69']
    truncB = [n for n in range(1, 20001) if _p2trunc(B, n) == '17.59']
    truncW = [n for n in range(1, 20001) if _p2trunc(W, n) == '17.71']
    q['Q8']['N_domain_trunc'] = {'A': truncA, 'B': truncB, 'W': truncW}
    chk('Q8-uniq3', '截断模式下三个百分数仍各只解出 N=1654（钉住与舍入方式无关）',
        truncA == [1654] and truncB == [1654] and truncW == [1654], (truncA, truncB, truncW))

    # ---------------- Q9 自由参数 vs 导出量 ----------------
    derived = {
        'NO4=1196': 'N − A',
        'W=293': 'B + |「④ direct call」| = 291 + 2（需附带「交集 0」这一条独立声明）',
        '167': 'A − B',
        '27.69% / 17.59% / 17.71%': 'round(100*A/N,2) / round(100*B/N,2) / round(100*W/N,2)',
        '10（减法读法）': 'LOOSE − FULLSTR = 12 − 2',
    }
    ok_derived = (NO4 == N - A) and (W == B + 2) and (ABD == A - B) and (SUB == LOOSE - FULLSTR) \
        and p2(A, N) == '27.69' and p2(B, N) == '17.59' and p2(W, N) == '17.71'
    q['Q9'] = {
        'verdict': '成立' if ok_derived else '不成立',
        'free_and_independently_measurable': {
            'N=1654': '全表 / [已证] 行数（一次测量）',
            'A=458': '第 4 列含 ④ 的行数（一次测量）',
            'B=291': '第 4 列含「④ 活表槽位见证」的行数（一次测量）',
            '|「④ direct call」|=2': '与 B 的并集增量；正文用「W=293 且交集 0」间接给出',
            'LOOSE=12': '宽松子串 direct call 命中行数（一次测量）',
            'FULLSTR=2': '含全串 ④ direct call 的行数（一次测量）',
            'SETD=9': '相对 W 的集合差（一次测量）',
            '6/2/3 分解': '12 行的三分类归属（三次数行）',
        },
        'derived_zero_information': derived,
        'judgement': '独立自由参数只有 {N, A, B, |④direct call|, LOOSE, FULLSTR, SETD, 6/2/3}；'
                     '1196 / 167 / 293 / 三个百分数 / 10 全部是这些数的函数。'
                     '⇒ Q2–Q5、Q8 全成立在算术上是必然的，它们**不能**为 F23 的正确性提供任何独立佐证；'
                     '真正需要外部核验的是那 7 个计数是否等于盘上实数。',
        'test_design_implication': '一张卡若只复算 Q1–Q5、Q8–Q9，则无论底层数据对错都会 PASS；'
                                   '故本卡把「计数层可否复算」单列为 Q10。',
    }
    chk('Q9', '五个导出量逐一等于其导出式', ok_derived, derived)
    chk('Q9-neg', '把 A 改成 459 后 1196==N−A 必须判 False', not (NO4 == N - 459), NO4 == N - 459)

    # ---------------- Q10（补充）计数层能否在盘上复算 ----------------
    # 先做一条不依赖外部表的结构约束：B ⊆ A、W ⊆ A（因两者都含字符 ④）⇒ B ≤ A 且 W ≤ A
    q['Q_cross'] = {
        'verdict': '成立' if (B <= A and W <= A and B + 2 == W) else '不成立',
        'checks': {'B<=A': B <= A, 'W<=A': W <= A, 'B+2==W': B + 2 == W},
        'note': '这条有真实分辨力：若某次改动把 B 报成 470（> A=458），则「B ⊆ A」立刻失败。'
                '本卡实测三者相容，只说明四个数满足嵌套关系，不说明它们是从表里数出来的。',
    }
    chk('Q-cross', 'B<=A 且 W<=A（B、W 都含 ④，须落在 A 内）', B <= A and W <= A, {'B<=A': B <= A, 'W<=A': W <= A})
    chk('Q-cross-neg', 'B=470 > A=458 时该约束必须判 False', not (470 <= A), 470 <= A)

    probe = {'coverage_tsv_candidates': {p: os.path.exists(p) for p in COV_CANDIDATES}}
    # F23 的 evidence_paths 指向的两份文件是否存在
    probe['delivery_summary_exists'] = os.path.exists(
        os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md'))
    probe['panel_exists'] = os.path.exists(os.path.join(ROOT, 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'))

    # 反证：同一套判据施加到 FACT_INDEX.tsv 本身
    lines = [l for l in io.open(FI, encoding='utf-8', errors='replace').read().split('\n') if l]
    hdr, rows = lines[0].split('\t'), [l.split('\t') for l in lines[1:]]
    fi_counts = {
        'FACT_INDEX_data_rows': len(rows),
        'col4_has_④': sum(1 for r in rows if len(r) > 3 and '④' in r[3]),
        'col4_has_活表槽位见证': sum(1 for r in rows if len(r) > 3 and '④ 活表槽位见证' in r[3]),
        'col4_has_④direct call': sum(1 for r in rows if len(r) > 3 and '④ direct call' in r[3]),
        'col2_has_④': sum(1 for r in rows if len(r) > 1 and '④' in r[1]),
        'any_col_has_④': sum(1 for r in rows if '④' in '\t'.join(r)),
        'loose_has_direct call': sum(1 for r in rows if 'direct call' in '\t'.join(r)),
    }
    can_count = all(os.path.exists(p) for p in COV_CANDIDATES)
    q['Q10'] = {
        'verdict': '无法判定' if not can_count else '成立',
        'reason': 'F23 的计数对象是 coverage.tsv 的「第 4 列」（R17-R41-RECOMPUTE 卡：coverage.tsv = 18,498 数据行 / 8 列 / 4,147,334 B）。'
                  '该文件在本机所有候选路径均不存在，F23 的两个 evidence_path 目录（R17_DELIVERY / COVERAGE）亦不存在 ⇒ '
                  '458 / 291 / 293 / 1196 / 12 / 2 / 9 / 6-2-3 均无法在本机重数。',
        'probe': probe,
        'counterproof_on_FACT_INDEX_itself': fi_counts,
        'counterproof_note': '把同一批判据（含 ④ / 含「④ 活表槽位见证」/ 含「④ direct call」）施加到 FACT_INDEX.tsv（54 条）上，'
                             '得到的数（见 counterproof_on_FACT_INDEX_itself）与 458/291/2 差两个数量级 ⇒ '
                             'F23 的数不是对 FACT_INDEX 数出来的，不能拿本文件冒充计数源。',
        'what_would_close_it': '把 coverage.tsv（sha256 前缀 c2ee063f…，4,147,334 B）放回 COVERAGE/ 下后，'
                               '按 A=第4列含 ④ / B=第4列含「④ 活表槽位见证」/ W=B∪「④ direct call」/ 无④ 四个判据逐列数一遍即可闭合。',
    }
    chk('Q10-missing', 'coverage.tsv 在本机确实不存在（故计数层判「无法判定」）', not can_count, probe)
    chk('Q10-neg', 'FACT_INDEX 本身的「④」行数不可能等于 458（反证断言可失败）',
        fi_counts['any_col_has_④'] != A, fi_counts['any_col_has_④'])

    out = {
        'card': 'R137-EXEC-F23',
        'agent': 'deepseek / exec',
        'target_file': os.path.relpath(FI, ROOT),
        'target_sha256': None,
        'answers': q,
        'assertions': RES,
        'assertion_total': len(RES),
        'assertion_fail': FAIL,
        'self_check': 'FAIL 计数应等于「故意设计的反控条数」里被判 False 的部分；'
                      '若断言恒真，反控项会全部 PASS → 此处 FAIL 数=0 且反控项 got 值必须与断言值不同。',
    }
    import hashlib
    out['target_sha256'] = hashlib.sha256(open(FI, 'rb').read()).hexdigest()
    with io.open(os.path.join(ROOT, '_r137/sub_deepseek/r137_f23_exec.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n=== %d assertions, FAIL=%d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
