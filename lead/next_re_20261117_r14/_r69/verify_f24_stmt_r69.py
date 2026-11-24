# -*- coding: utf-8 -*-
# R69 · F24 statement 正文内部一致性核验（算术闭合 + 步骤枚举是否覆盖被引值）
import os, re, sys, io

ROOT = '/home/t628/projects/ra2-campaign-forge'
RD   = os.path.join(ROOT, 'lead/next_re_20261117_r14')
TSV  = os.path.join(RD, 'R17_R102_FACTINDEX_V530/FACT_INDEX.tsv')

fails, log = [], []
def W(s=''):
    print(s); log.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

rows = {r[0]: r for r in (l.split('\t') for l in open(TSV, encoding='utf-8').read().split('\n') if l)}
S = rows['F24'][1]

def sumtsv(p):
    ls = [l for l in open(os.path.join(RD, p), encoding='utf-8').read().split('\n')[1:] if l.strip()]
    return len(ls), sum(int(l.split('\t')[1]) for l in ls)

W('=== 0 四份清单实测（不采信正文自述）===')
meas = {}
for p in ['R17_R96_TIER_FINAL_4413/tier_final_4413.tsv',
          'R17_R97_TIER_FINAL_4413B/tier_final_4413b.tsv',
          'R17_R99_TIER_FINAL_4416/tier_final_4416.tsv',
          'R17_R101_TIER_FINAL_4417/tier_final_4417.tsv']:
    n, s = sumtsv(p)
    meas[os.path.basename(p)] = (n, s)
    W('  %-22s 件=%-5d sum(bytes)=%d' % (os.path.basename(p), n, s))

W('')
W('=== 1 正文声称的四个中间值 vs 实测 ===')
claim = [('4,518', 4518, '4,518 件 / 724,479,859 B（R53 重判后）'),
         ('4,413 / 744,172,839', 744172839, 'tier_final_4413'),
         ('4,413 / 727,461,721', 727461721, 'tier_final_4413b（剔 bounds）'),
         ('4,416 / 736,151,921', 736151921, 'tier_final_4416'),
         ('4,417 / 737,517,286', 737517286, 'tier_final_4417（正文主引值）')]
for tag, val, desc in claim:
    W('  %-24s = %d  | %s' % (tag, val, desc))
ck('正控：正文主引值 737,517,286 == tier_final_4417 实测 sum', meas['tier_final_4417.tsv'][1] == 737517286,
   str(meas['tier_final_4417.tsv'][1]))
ck('正控：正文 4,417 == tier_final_4417 行数', meas['tier_final_4417.tsv'][0] == 4417)
ck('正控：727,461,721 == tier_final_4413b 实测', meas['tier_final_4413b.tsv'][1] == 727461721)
ck('正控：744,172,839 == tier_final_4413 实测', meas['tier_final_4413.tsv'][1] == 744172839)
ck('正控：736,151,921 == tier_final_4416 实测', meas['tier_final_4416.tsv'][1] == 736151921)

W('')
W('=== 2 逐步算术闭合 ===')
d_bounds = 744172839 - 727461721
W('  R60 剔 bounds: 744,172,839 - 727,461,721 = %d' % d_bounds)
ck('正文「剔 bounds 16,711,118」', d_bounds == 16711118, str(d_bounds))
ck('正文「该件 17,624,355 → 913,237」', 17624355 - 913237 == 16711118, str(17624355 - 913237))

d_3 = 736151921 - 727461721
W('  R62/R63 三件翻: 736,151,921 - 727,461,721 = %d' % d_3)
three = 5693169 + 1631944 + 1365087
ck('正控：三件字节和 = 8,690,200', three == 8690200, str(three))
ck('三件翻差额与三件字节和一致', d_3 == three, '%d vs %d' % (d_3, three))

d_4 = 737517286 - 736151921
W('  R64 第四件翻: 737,517,286 - 736,151,921 = %d' % d_4)
ck('第四件 scan_mine 1,365,365', d_4 == 1365365, str(d_4))

total4 = 5693169 + 1631944 + 1365087 + 1365365
W('  四件合计 = %d' % total4)
ck('正文「合计 +10,055,565 B」', total4 == 10055565, str(total4))
ck('闭环：727,461,721 + 10,055,565 = 737,517,286',
   727461721 + total4 == 737517286, str(727461721 + total4))
ck('件数闭环：4,413 + 4 = 4,417', 4413 + 4 == 4417)

W('')
W('=== 3 关键判定：正文「四步」枚举是否覆盖被引主值 ===')
ck('正控：正文确实写了「四步」字样', '四步' in S)
ck('正控：正文确实写了 R64 字样', 'R64' in S)
# 拆出「四步」那句话与紧随其后的溯源括号
m = re.search(r'本值经([^（]*)四步[^（]*（溯源：([^）]*)）', S)
ck('正控：能定位到「四步」+「溯源」句', m is not None)
if m:
    steps_txt, trace = m.group(1), m.group(2)
    W('  「四步」枚举原文: 本值经%s四步' % steps_txt)
    W('  溯源括号原文  : 溯源：%s' % trace)
    # 溯源括号里给出的终值
    nums = re.findall(r'\*\*([\d,]+) 件 / ([\d,]+) B\*\*', trace)
    W('  溯源括号内的加粗终值: %s' % (nums,))
    lastb = int(nums[-1][1].replace(',', '')) if nums else None
    W('  溯源终值 = %s' % lastb)
    named = re.findall(r'R\d+(?:/\s*R\d+)*', steps_txt)
    W('  枚举出的步骤代号: %s' % named)
    # —— 以下两项是「缺陷实测记录」，用 RECORD 输出，不作断言（断言只用于尺子自检）——
    W('  RECORD-1 溯源括号终值 = 727,461,721，主引值 = 737,517,286，差 %d'
      % (737517286 - lastb))
    W('  RECORD-2 四步枚举代号 = %s；R64 不在其中 = %s'
      % (named, 'R64' not in steps_txt))
    W('  RECORD-3 四步覆盖量 = 8,690,200 = 三件和；主引值−剔段值 = 10,055,565；'
      '缺的正是 R64 的 1,365,365')
    ck('反控（尺子自检）：上述三项若把「四步」当完整枚举，就必然对不上 —— 判别力存在',
       three == 8690200 and (737517286 - 727461721) - 8690200 == 1365365,
       '%d + %d = %d' % (8690200, 1365365, 737517286 - 727461721))

W('')
W('=== 4 反控：把「四步」改成「五步」应使该缺陷消失 ===')
S2 = S.replace('四步', '五步', 1)
ck('反控：修成「五步」后该串不再含「四步」', '四步' not in S2.split('五步')[0] if '五步' in S2 else False)
ck('反控：原文确实只有 1 处「四步」（改动可定位）', S.count('四步') == 1, str(S.count('四步')))

W('')
W('=== 5 另一处：正文称「R62/R63/R64 再翻四件」，与「四步」是否同一划分 ===')
ck('正控：正文有「再翻四件」表述', '再翻四件' in S)
ck('判定：四件文件在正文中被逐个列出（4 个文件名齐）',
   all(x in S for x in ['mesh_imm32.json', 'sweep.json', 'e8_sites_audit.json', 'scan_mine.json']))

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_f24_stmt_r69.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
sys.exit(0 if not fails else 1)
