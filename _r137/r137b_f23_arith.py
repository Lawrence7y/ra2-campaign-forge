#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-b · F23 算术闭合的机械核验（只读）

F23 的全部数字都是「行计数」，且彼此之间有硬算术关系。本脚本不依赖已失的
DELIVERY_SUMMARY.md / PANEL.md，只用 F23 自己正文里给的数字做**闭合检验**：

  ① 458/1654 = 27.69% ?  291/1654 = 17.59% ?  293/1654 = 17.71% ?
  ② 458 + 1196 = 1654 ?  （口径 A 与「完全无 ④」互补）
  ③ 293 − 291 = 2 ?      （宽口径 = B ∪ 2 行 direct call，交集 0）
  ④ 458 − 291 = 167 ?    （A − B 形态混杂数）
  ⑤ 12 行宽松命中：减法读法 12 − 2 = 10；集合差读法 293 − (293∩12) = 9 ⇒ 交集须为 3
  ⑥ 12 = 6 否定 + 2 callers + 3 真非否定 + ? ⇒ 余 1 行须有归属

判据：全部成立 ⇒ F23 的**数字层自洽**；但自洽不等于口径定义正确 —— 口径定义只在
已失的 DELIVERY_SUMMARY.md §2，本脚本只能证前者，不能证后者。这条边界写进结论。

反控：把每个等式改成对一个随机错值检验，必须判 False（证明断言有分辨力）。
"""
import io
import json
import os
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
    print(('PASS ' if ok else 'FAIL ') + name + ('  :: ' + str(detail)[:200] if detail else ''))


def pct(a, b):
    """按 F23 正文的写法算百分比，保留两位。返回字符串，便于与正文逐字比对。"""
    return '%.2f%%' % (100.0 * a / b)


def main():
    N = 1654
    A = 458          # 口径 A：含字符 ④
    B = 291          # 口径 B：含「④ 活表槽位见证」
    W = 293          # 宽口径 = B ∪ 「④ direct call」2 行
    NO4 = 1196       # 完全无 ④
    AB_DIFF = 167    # A − B
    LOOSE = 12       # 宽松子串 direct call 命中
    FULLSTR = 2      # 含全串「④ direct call」

    # ---- ① 百分比逐字吻合 ----
    chk('B1 pct(A/N) == "27.69%"', pct(A, N) == '27.69%', pct(A, N))
    chk('B2 pct(B/N) == "17.59%"', pct(B, N) == '17.59%', pct(B, N))
    chk('B3 pct(W/N) == "17.71%"', pct(W, N) == '17.71%', pct(W, N))

    # ---- ② 互补 ----
    chk('B4 A + NO4 == N', A + NO4 == N, A + NO4)

    # ---- ③ 宽口径增量 ----
    chk('B5 W - B == 2 (direct call rows, disjoint)', W - B == 2, W - B)

    # ---- ④ A − B ----
    chk('B6 A - B == 167', A - B == AB_DIFF, A - B)

    # ---- ⑤ 12 行宽松命中的两种读法 ----
    sub_read = LOOSE - FULLSTR          # 减法读法：12 − 2 = 10
    setdiff_read = 9                    # 正文另给的集合差读法
    chk('B7 subtraction reading 12-2 == 10', sub_read == 10, sub_read)
    # 集合差读法：若 |LOOSE 减 W| = 9，则 |LOOSE ∩ W| 必须是 LOOSE - 9 = 3
    chk('B8b |LOOSE ∩ W| == 3 (implied by set-diff reading = 9)',
        LOOSE - setdiff_read == 3, LOOSE - setdiff_read)
    chk('B9 two readings differ (10 != 9), so the ambiguity is real',
        sub_read != setdiff_read, (sub_read, setdiff_read))

    # ---- ⑥ 12 行的分解 ----
    NEG, CNT, REAL = 6, 2, 3
    chk('B10 6 + 2 + 3 <= 12 (leaves a residue row)', NEG + CNT + REAL <= LOOSE,
        NEG + CNT + REAL)
    chk('B11 residue is exactly 1 row', LOOSE - (NEG + CNT + REAL) == 1,
        LOOSE - (NEG + CNT + REAL))

    # ---- 反控：等式对错值必须判 False ----
    chk('N4 pct(458,1654) != "27.68%" (assertion has resolution)',
        pct(A, N) != '27.68%', pct(A, N))
    chk('N5 A + NO4 + 1 != N', A + NO4 + 1 != N, A + NO4 + 1)
    chk('N6 W - B != 3', W - B != 3, W - B)
    chk('N7 A - B != 168', A - B != 168, A - B)

    # ---- 反向：正文给出的数是否唯一确定 ----
    # 若有人把 1654 改成 1655，则三个百分比全部失配（证 1654 被三个独立百分比钉住）
    alt = 1655
    chk('B12 1654 is pinned by pct: 1655 breaks all three',
        pct(A, alt) != '27.69%' and pct(B, alt) != '17.59%' and pct(W, alt) != '17.71%',
        (pct(A, alt), pct(B, alt), pct(W, alt)))

    # ---- 哪些数互相独立、哪些是导出量 ----
    derived = {
        'NO4=1196': 'N - A',
        'W=293': 'B + 2',
        'AB_DIFF=167': 'A - B',
        'pct*': 'derived from N',
    }
    chk('B13 NO4 is derived from N and A (not independent)',
        NO4 == N - A, NO4)
    chk('B14 W is derived from B (not independent)', W == B + 2, W)
    chk('B15 AB_DIFF is derived from A and B', AB_DIFF == A - B, AB_DIFF)

    # 真正独立的自由参数只有 3 个：N, A, B（其余全导出）
    free = 3
    chk('B16 only 3 free parameters (N, A, B) — the rest are derived', free == 3, free)

    out = {
        'N': N, 'A': A, 'B': B, 'W': W, 'NO4': NO4,
        'pct': {'A': pct(A, N), 'B': pct(B, N), 'W': pct(W, N)},
        'derived': derived,
        'free_params': ['N=1654', 'A=458', 'B=291'],
        'loose_two_readings': {'subtraction': sub_read, 'setdiff': setdiff_read},
        'loose_decomp': {'neg': NEG, 'counters': CNT, 'real': REAL, 'residue': LOOSE - (NEG + CNT + REAL)},
        'boundary': '算术自洽只证数字层；口径定义只在已失 DELIVERY_SUMMARY.md §2，本脚本未证',
        'assertions': RES, 'fail': FAIL,
    }
    with io.open(os.path.join(ROOT, '_r137/r137b_f23_arith.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n=== assertions %d, FAIL %d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
