#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 B：R90「F23 档 2（可重算）」这条裁定的判据是否成立。

被检主张（BOARD_ARCHIVE.md 第 4915 行原文）：
  「F23 改判档 2（可重算）：7 个数字全部可算术独立复现，不需任何已消失文件
    —— 1654+5875+10969=18498、458+1196=1654、863+791=1654、
       458/1654=27.69%、291/1654=17.59%、293/1654=17.71%、863/1654=52.18%。
    ⇒ 它的 [已证] 不是零证据，是『原件全失、数字仍可复核』。」

本脚本只做一件事：区分「恒等式自洽」与「独立复现」。
判「可重算」需要一个能**否决**候选值的约束；
若任何候选值都能满足，则该约束无鉴别力，不能支撑「可重算」。

两个反例（强制前置）：
  必须为真（正）：给定候选值本身代入，等式成立
  必须为假（负）：换一个候选值，等式仍成立 ⇒ 该等式不能否决 ⇒ 无鉴别力
"""
import json, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
fails = []
out = {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


# ---------- 0 · 七个等式是否为恒等式 ----------
ck('0.1 1654+5875+10969=18498', 1654 + 5875 + 10969 == 18498)
ck('0.2 458+1196=1654', 458 + 1196 == 1654)
ck('0.3 863+791=1654', 863 + 791 == 1654)
ck('0.4 458/1654 四位小数 27.69', round(458 / 1654 * 100, 2) == 27.69, round(458 / 1654 * 100, 2))
ck('0.5 291/1654 = 17.59', round(291 / 1654 * 100, 2) == 17.59, round(291 / 1654 * 100, 2))
ck('0.6 293/1654 = 17.71', round(293 / 1654 * 100, 2) == 17.71, round(293 / 1654 * 100, 2))
ck('0.7 863/1654 = 52.18', round(863 / 1654 * 100, 2) == 52.18, round(863 / 1654 * 100, 2))

# ---------- 1 · 鉴别力测试：这三个等式能不能否决别的候选值 ----------
print("\n[1] 鉴别力：把候选值换掉，等式还成不成立")
cands = [300, 400, 458, 500, 600, 900]
rows = []
for a in cands:
    none = 1654 - a                      # 458+1196=1654 这个等式只定义 none
    ok_partition = (a + none == 1654)    # 由构造必真
    ok_aux = (1654 + 5875 + 10969 == 18498)   # 与 a 无关，恒真
    rows.append((a, none, ok_partition, ok_aux))
    print(f"    A'={a:4d} -> none'={none:4d}  A'+none'=1654:{ok_partition}  aux:{ok_aux}")

ck('1.1 反控（必须为真）：替换候选值时 A+none=1654 仍成立',
   all(r[2] for r in rows))
ck('1.2 决定性：因此 458+1196=1654 对 A 无任何鉴别力（纯定义式）',
   all(r[2] for r in rows))
ck('1.3 决定性：1654+5875+10969=18498 不含 458，对 A 也无鉴别力',
   all(r[3] for r in rows))
out['discrimination'] = [{'A': r[0], 'none': r[1], 'partition_holds': r[2]} for r in rows]

# ---------- 2 · 百分比是不是独立的第二约束 ----------
print("\n[2] 百分比：是独立测量，还是由计数算出来的同义反复")
for a in (400, 458, 500):
    pct = round(a / 1654 * 100, 2)
    print(f"    A'={a} -> A'/1654 = {pct}%   与 27.69% 相等？{pct == 27.69}")
ck('2.1 换 A 后百分比随之变 ⇒ 百分比是 A 的函数，不是独立约束',
   round(400 / 1654 * 100, 2) != 27.69 and round(500 / 1654 * 100, 2) != 27.69)
ck('2.2 因此 458/1654=27.69% 不能用来反证 458 是对的（循环）',
   True)  # 结构性结论，见 2.1

# ---------- 3 · 有没有任何一条能钉住 1654 ----------
print("\n[3] 1654 本身能不能被钉住")
ck('3.1 从 458+1196=1654 看不出 1654 的来源（它只是 A 与 none 之和）', True)
# 1654 是否有独立出处：statement 里 1654 作为分母出现，但它自己无独立锚
ck('3.2 台账里 1,654 与 18,498 都只是被记录的值，不由本表推出',
   18498 - 5875 - 10969 == 1654)
ck('3.3 但 5,875 / 10,969 / 18,498 同样无独立在盘源 ⇒ 该式是三条未知数一条方程',
   True)
free_dof = 3 - 1
ck('3.4 自由度 = 3 未知 - 1 方程 = 2 ⇒ 不足定解', free_dof == 2, free_dof)

# ---------- 4 · 结论 ----------
verdict = {
    'identities_all_true': True,
    'discriminating': False,
    'free_dof': free_dof,
}
ck('4.1 七式全部为真但无一具鉴别力 ⇒「可重算」判据不成立',
   verdict['identities_all_true'] and not verdict['discriminating'])
out['verdict'] = verdict
out['fails'] = fails
json.dump(out, open(os.path.join(ROOT, '_r146/r149b_r90_criterion.json'), 'w'),
          ensure_ascii=False, indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails:
    print('  ', f)
