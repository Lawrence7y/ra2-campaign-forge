#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-c · F35 判据式（ceil(0.9n) / ceil(0.5n)）的机械复算（只读）

F35 的判据式只有一行：
    达标 ⇔ named_S(R14) >= ceil(0.9n)  且  proved >= ceil(0.5n)      （n = 子系统 atlas 分母）

它的证据是已失的 COVERAGE/PANEL.md（M47 / M52）。本脚本不读 PANEL.md，
而是从**现盘仍在的台账 / 归档 / 看板 / LEAD_LOCK** 里抓台账正文自己写下的
**显式等式** `ceil(0.9×N)=M` 与 `ceil(0.5×N)=M`，逐条用 Python 的 ceil 重算。

为什么只认显式等式：
  上一版（本脚本初稿）用「门槛 NNN」配同行分母，抓到 n=848/门槛 424 一例 ——
  但 424 是 ceil(0.5×848) 即 **proved** 门槛，不是 named 门槛。形态混在一起 ⇒
  该法把两个判据混淆，作废（自错 S-255）。显式等式 `ceil(0.9×N)=M` 自带
  系数，不会歧义。

反控：
  N1 把判据式换成 ceil(0.9n)+1，所有样本必须失配
  N2 floor 与 ceil 在样本上确实给出不同值（证有区分度）
  N3 造一个假样本 ceil(0.9×100)=91 必须判不成立
"""
import io
import json
import math
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = [
    'lead/GOAL_THREE_TARGETS_20261018.md',
    'lead/next_re_20261117_r14/BOARD_ARCHIVE.md',
    'lead/next_re_20261117_r14/STATUS_BOARD.md',
    'lead/LEAD_LOCK',
    'lead/next_re_20261117_r14/R14_COMMON.md',
]

RES = []
FAIL = 0


def chk(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:300]})
    print(('PASS ' if ok else 'FAIL ') + name + ('  :: ' + str(detail)[:220] if detail else ''))


# ceil(0.9×N)=M  /  ceil(0.9n)、  /  ceil(0.5×N)=M
# N 可以是十进制数（0.9×102）或记号 n（此时无 N 值，跳过）
#
# 🐞 自错 S-256（R137 复算 E2 当场抓出）：初版正则写
#     ceil\(\s*0\.([59])\s*[×x*]\s*(\d+)\s*\)\s*[=＝]\s*\*{0,2}\s*(\d+)
#   在闭括号与等号之间只允许空白，于是漏掉台账里带反引号的写法
#   ceil(0.9×90)`=81 与 ceil(0.9×240)`=216 —— 得 7 个样本。
#   实际台账用反引号包住表达式（Markdown 行内代码），正确写法必须容忍 ` 与 ＊
#   与全角等号。修正后与 hy4 #293 的 13 处出现 / 9 个去重键一致。
RE_EXPL = re.compile(
    r'ceil\(\s*0?\.([59])\s*[×xX*＊·]\s*(\d+)\s*\)\s*[`＊]*\s*[=＝]\s*[`*]*\s*(\d+)')


def main():
    samples = []   # (coef, n, recorded, src)
    for rel in SRC:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        for ln, line in enumerate(io.open(p, encoding='utf-8', errors='replace'), 1):
            for m in RE_EXPL.finditer(line):
                coef = 0.9 if m.group(1) == '9' else 0.5
                samples.append((coef, int(m.group(2)), int(m.group(3)),
                                '%s:%d' % (rel, ln)))

    # 去重
    seen = {}
    for coef, n, rec, src in samples:
        seen.setdefault((coef, n, rec), src)
    uniq = sorted((coef, n, rec, src) for (coef, n, rec), src in seen.items())

    print('抓到显式等式样本 %d 个（去重后）:' % len(uniq))
    ok_n = bad_n = 0
    for coef, n, rec, src in uniq:
        calc = math.ceil(coef * n)
        flag = 'OK ' if calc == rec else 'BAD'
        if calc == rec:
            ok_n += 1
        else:
            bad_n += 1
        print('   %s ceil(%.1f×%d) 台账=%-5d 实算=%-5d  %s' % (flag, coef, n, rec, calc, src))

    chk('C1 抓到 >=5 个显式 ceil 等式样本', len(uniq) >= 5, len(uniq))
    chk('C2 全部样本台账值 == 实算 ceil', bad_n == 0, 'ok=%d bad=%d' % (ok_n, bad_n))
    chk('C3 至少 3 个 0.9 系数样本（named 门槛）',
        sum(1 for c, _, _, _ in uniq if c == 0.9) >= 3,
        sum(1 for c, _, _, _ in uniq if c == 0.9))
    chk('C4 至少 1 个 0.5 系数样本（proved 门槛）',
        sum(1 for c, _, _, _ in uniq if c == 0.5) >= 1,
        sum(1 for c, _, _, _ in uniq if c == 0.5))

    # ---- 反控 ----
    p1 = sum(1 for coef, n, rec, _ in uniq if rec == math.ceil(coef * n) + 1)
    chk('N1 ceil+1 复现数必须为 0', p1 == 0, p1)

    flo = sum(1 for coef, n, rec, _ in uniq if rec == int(coef * n))
    diff = [(coef, n) for coef, n, _, _ in uniq if int(coef * n) != math.ceil(coef * n)]
    chk('N2 ceil 与 floor 在样本上确实不同（有区分度）', len(diff) > 0,
        'diff=%d floor-hits=%d' % (len(diff), flo))
    chk('N2b floor 复现数 < 全样本数（floor 不是等价写法）', flo < len(uniq),
        'floor-hits=%d/%d' % (flo, len(uniq)))

    chk('N3 假样本 ceil(0.9×100)=91 判不成立', 91 != math.ceil(0.9 * 100),
        '真值=%d' % math.ceil(0.9 * 100))

    # ---- 边界：判据式在整数 n 上并不总是「向上取整有实质作用」 ----
    same = [n for n in range(1, 2001) if math.ceil(0.9 * n) == int(0.9 * n)]
    print('\n[0.9n 时 ceil==floor 的 n] %d / 2000（这些 n 上向上取整不起作用）' % len(same))
    chk('C5 ceil 与 floor 不等价的 n 占多数（取整规则是真判据）',
        len(same) < 2000 - len(same), 'same=%d diff=%d' % (len(same), 2000 - len(same)))

    # ---- 两个门槛的相对位置 ----
    chk('C6 对全部样本 ceil(0.9n) > ceil(0.5n)（named 门槛恒严于 proved）',
        all(math.ceil(0.9 * n) > math.ceil(0.5 * n) for _, n, _, _ in uniq),
        'n 范围 %d..%d' % (min(n for _, n, _, _ in uniq), max(n for _, n, _, _ in uniq)))

    out = {
        'criterion': 'named_S >= ceil(0.9n) AND proved >= ceil(0.5n)',
        'samples_total': len(uniq),
        'samples_ok': ok_n,
        'samples_bad': bad_n,
        'samples': [{'coef': c, 'n': n, 'recorded': r, 'src': s,
                     'recomputed': math.ceil(c * n)} for c, n, r, s in uniq],
        'controls': {'plus1_hits': p1, 'floor_hits': flo,
                     'floor_differs_count': len(diff)},
        'boundary': ('算术层复算：判据式的两个门槛值在现盘台账里可逐条复现；'
                     'proved_strict 的定义（= atlas 内 [已证] 且语义栏不含 [未证]）'
                     '仍只在已失 PANEL.md M52，本脚本未证其定义，只证 ceil 两式'),
        'assertions': RES, 'fail': FAIL,
    }
    with io.open(os.path.join(ROOT, '_r137/r137c_f35_criterion.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n=== assertions %d, FAIL %d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
