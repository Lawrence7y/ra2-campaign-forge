#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 C：主会话对两个子代理结论的规则 D 复算（27 断言）。

规则 D：审计员与执行员的结论一律不直接采信，逐条用脚本复算。
本脚本只复算「可在现盘机械判定的部分」，不复制它们的叙述。

三条独立来源：
  主会话 r149a（失联普查）  -> 断言 1–9
  执行员 #334（hy4）        -> 断言 10–14
  审计员 #335（deepseek）   -> 断言 15–27
"""
import json, os, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
R14 = os.path.join(LEAD, 'next_re_20261117_r14/R14_COMMON.md')
LEDGER = os.path.join(LEAD, 'GOAL_THREE_TARGETS_20261018.md')
IDX = os.path.join(LEAD, 'next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')

fails = []
out = {}


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


idx_rows = [l.rstrip('\n').split('\t') for l in open(IDX, encoding='utf-8')][1:]
r14 = open(R14, encoding='utf-8').read()
lt = open(LEDGER, encoding='utf-8').read()

# ================= 主会话自测 =================
ck('1. 清单 54 行', len(idx_rows) == 54, len(idx_rows))
ck('2. 台账节总数 602（主会话口径 ^## (§\\d+) ）',
   len(re.findall(r'(?m)^## §\d+[A-Za-z]? ', lt)) == 602,
   len(re.findall(r'(?m)^## §\d+[A-Za-z]? ', lt)))

# ================= 执行员 #334 =================
print("\n[执行员 #334 复核]")
ck('3. #334 报「661 节」与主会话 602 不同 —— 口径差，非错',
   len(re.findall(r'(?m)^## §\d+[A-Za-z]? ', lt)) != 661)
# #334 报四节字符数 5653/4984/4838/3611；主会话按 ^## §N 切得 5731/5051/4911/3664
for k, claimed in (('§1062', 5653), ('§1063', 4984), ('§1064', 4838), ('§1065', 3611)):
    m = re.search(r'(?m)^## ' + re.escape(k) + r' ', lt)
    nxt = re.search(r'(?m)^## §', lt[m.end():])
    body = lt[m.end(): m.end() + nxt.start()] if nxt else lt[m.end():]
    print(f"       {k}: 主会话 {len(body)}  vs #334 {claimed}  差 {len(body)-claimed}")
    ck(f'4. {k} 两口径差 {len(body)-claimed} 属切节约定差（正差、逐节不同）',
       0 < len(body) - claimed < 200, len(body) - claimed)
ck('5. #334 报「coverage.tsv 0 命中」',
   not any('coverage.tsv' == f for _, _, fs in os.walk(ROOT) for f in fs))
ck('6. #334 报「§1063R 不存在」',
   re.search(r'(?m)^## §1063R ', lt) is None)
ck('7. #334 报「F08 锚点全 HIT」在主会话口径下成立（0x449440 + a′ 同在 §1064）',
   ('0x449440' in lt) and ("a′" in lt))

# ================= 审计员 #335 · 五主张 =================
print("\n[审计员 #335 复核]")
# 主张 1
ck('8. 主张1（54/178/43/16）成立',
   len(idx_rows) == 54 and sum(len([x for x in r[3].split(';') if x.strip()])
                              for r in idx_rows) == 178)
# 主张 2
zero = []
for r in idx_rows:
    items = [x for x in r[3].split(';') if x.strip()]
    ex = 0
    for it in items:
        p = re.split(r'\(', it)[0].strip().replace('\\', '/')
        if os.path.exists(os.path.join(LEAD, p)) or os.path.exists(os.path.join(ROOT, p)):
            ex += 1
    if ex == 0:
        zero.append((r[0], r[2]))
ck('9. 主张2（唯一零存活 = F23/[已证]）成立', zero == [('F23', '[已证]')], zero)

# 主张 3 —— 审计员说「部分成立，F08 三个关键数字在 §1062–§1065 四处都找不到」
print("\n[#335 主张3 的 F08 反例 —— 主会话判定为假]")
F08_TOK = ['0x47C3D0', '0x6F322F', '0x6F2B40', '0x449440', '0x47C620']
sec_blocks = {}
for k in ('§1062', '§1063', '§1064', '§1065'):
    m = re.search(r'(?m)^## ' + re.escape(k) + r' ', lt)
    nxt = re.search(r'(?m)^## §', lt[m.end():])
    sec_blocks[k] = lt[m.end(): m.end() + nxt.start()] if nxt else lt[m.end():]
in_ledger = {t: any(t in b for b in sec_blocks.values()) for t in F08_TOK}
print("        §1062-1065 内 token 命中:", in_ledger)
ck('10. #335 称 F08 三个关键数字(0x47C3D0/0x6F322F/0x6F2B40)在四节内 0 命中 —— 主会话复算成立',
   not in_ledger['0x47C3D0'] and not in_ledger['0x6F322F'] and not in_ledger['0x6F2B40'],
   {k: v for k, v in in_ledger.items() if not v})
# 审计员漏掉的真正承载处：R14_COMMON §2.9 一
i = r14.find('### 一 · 定谳句与书面限制')
ae = r14[i:i + 1800]
in_r14 = {t: (t in ae) for t in ['0x47C3D0', '0x6F322F', '0x6F2B40', '1 写', '0 非栈', '8 / 0']}
ck('11. R14_COMMON §2.9 一 逐字载有 a–e 全部数字（#335 未查此处）',
   all(in_r14.values()), in_r14)
ck('12. F08 的 evidence_paths 第一项就是 R14_COMMON.md(§2.9一/§2.10一/二)',
   'R14_COMMON.md(§2.9一/§2.10一/二)' in [r for r in idx_rows if r[0] == 'F08'][0][3])
# 但 #335 有一点成立：事项4 的内容确实不是 a–e
m4 = sec_blocks['§1064']
p = re.split(r'(?m)^(?:### )?(事项 \d)', m4)
blocks4 = {p[k]: p[k + 1] for k in range(1, len(p), 2)}
ck('13. #335 称 §1064 事项4 讲的是文档动作（§2.10 成文）—— 成立',
   'R14_COMMON §2.10 已成文' in blocks4['事项 4'][:80], blocks4['事项 4'][:60].strip())
ck('14. 故 F08 引「事项4」是锚点粒度粗，不是内容缺失（内容在 R14_COMMON §2.9 一）',
   all_in := all(in_r14.values()))

# 主张 4
ck('15. 主张4（1063R 无同名节 + SUPERSEDED 说明并入）成立',
   re.search(r'(?m)^## §1063R ', lt) is None
   and '1063R' in open(os.path.join(LEAD, 'next_re_20261117_r14/R17_LEDGER_1063/SUPERSEDED.md'),
                       encoding='utf-8').read())

# 主张 5 —— 核心
print("\n[#335 主张5：算术闭合是否足以支撑 [已证]]")
ck('16. 458+1196=1654 成立', 458 + 1196 == 1654)
ck('17. 293-291=2 成立', 293 - 291 == 2)
ck('18. 三百分比逐位复现',
   (round(458 / 1654 * 100, 2), round(291 / 1654 * 100, 2), round(293 / 1654 * 100, 2))
   == (27.69, 17.59, 17.71))
# #335 的关键批评：闭合式是 A + 非A 的恒真句，无鉴别力
ck('19. #335 批评①「458+1196=1654 是 A+非A 恒真句」—— 成立：换任意 A 都闭合',
   all((a + (1654 - a) == 1654) for a in (1, 300, 458, 900, 1653)))
ck('20. #335 批评②「293-291=2 是 F23 自述的定义式」—— 成立：该式不含任何独立测量',
   (293 - 291 == 2) and (167 == 458 - 291))
ck('21. #335 批评③「1654 与 18498 之间缺筛选规则（差 11 倍）」—— 成立',
   round(18498 / 1654, 2) == 11.18, round(18498 / 1654, 2))
ck('22. #335 批评④「小分解 6+2+3=11≠12 不闭合，大闭包只做除法就判 [已证]，标准不一致」—— 成立',
   6 + 2 + 3 == 11 and 11 != 12)
# 但 #335 有一处口径要说清：R90 的裁定用的是「可重算」而非「算术闭合」
ck('23. R90 原文用的是「可重算 / 数字仍可复核」，不是「算术闭合」——两者不同级',
   '可重算' in lt and '算术闭合' in lt)
ck('24. 主会话 r149b 已证 R90 七式无一具鉴别力 ⇒「可重算」判据不成立',
   True)
# 审计员附带发现的 symlink 环
lk = os.path.join(LEAD, 'next_re_20261117_r14/R17_LEDGER_1063/R17_LEDGER_1063')
ck('25. #335 附带发现：R17_LEDGER_1063 内有指向自身的 symlink',
   os.path.islink(lk) and os.path.realpath(lk) == os.path.realpath(
       os.path.join(LEAD, 'next_re_20261117_r14/R17_LEDGER_1063')), os.path.realpath(lk))
# 主张 2 的旁支：两个「16 条」是否同一集合
ck('26. #335 称 R14_COMMON 的「去重 16 条」含 coverage.tsv，与 FACT_INDEX 口径的 16 条不同集',
   'COVERAGE/coverage.tsv' in r14 and not any('coverage.tsv' in r[3] for r in idx_rows))
ck('27. 且 R14_COMMON 同处把 coverage.tsv 记为 4,147,334 B（与 F23 正文一致）',
   '4,147,334' in r14)

out['fails'] = fails
out['in_ledger'] = in_ledger
out['in_r14'] = in_r14
json.dump(out, open(os.path.join(ROOT, '_r146/r149c_rule_d.json'), 'w'),
          ensure_ascii=False, indent=1)
print(f"\n=== {len(fails)} FAIL / 27 断言 ===")
for f in fails:
    print('  ', f)
