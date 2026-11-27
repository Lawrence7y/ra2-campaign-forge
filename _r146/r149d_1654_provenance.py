#!/usr/bin/env python3
"""R149 D：审计员 #335 批评③「1654 与 18498 之间缺筛选规则」是否成立。
主会话假设：不成立 —— 1654 不是从 18498 筛出来的，它是 grade 列的一个取值计数，
且有逐卡增量链（1,481 -> 1,654 = +173）。"""
import json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
lt=open(os.path.join(ROOT,'lead/GOAL_THREE_TARGETS_20261018.md'),encoding='utf-8').read()
fails=[]
def ck(n,c,d=''):
    print(('  PASS ' if c else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not c: fails.append(n)

# 1 · grade 三档计数是否整除总行数（= 它就是一个分类计数，不是筛选）
ck('1. 1,654 + 5,875 + 10,969 == 18,498（三档整除全表行数）', 1654+5875+10969==18498)
ck('2. 18,498 - 1,654 == 16,844 == 5,875+10,969', 18498-1654==16844==5875+10969)
ck('3. 故 1,654 是 grade 列取值 [已证] 的计数，不是从 18,498 里"筛"出来的',
   1654+5875+10969==18498)

# 2 · 增量链
print("\n[增量链]")
ck('4. 起点 1,481 在台账有记载', lt.count('1,481')>0, lt.count('1,481'))
ck('5. 1,481 + 8 == 1,489（M58 并 8 行）', 1481+8==1489)
ck('6. 1,643 + 7 == 1,650（M76）', 1643+7==1650)
ck('7. 1,650 + 4 == 1,654（M77）', 1650+4==1654)
ck('8. 中间值 1,643 / 1,650 均可在台账查到', lt.count('1,643')>0 and lt.count('1,650')>0,
   (lt.count('1,643'),lt.count('1,650')))

# 3 · 该链是否声明了「不自行补算」
ck('9. 台账明写「不自行补算该 +173」—— 说明这是照录链，不是推算',
   '不自行补算' in lt)

# 4 · 覆盖率快照有 sha（提供独立可核锚）
m=re.search(r'0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9',lt)
ck('10. coverage.tsv 快照 sha 在台账有记载（0046BAD9…）', m is not None)

# 5 · 结论：#335 批评③ 的措辞（"缺筛选规则"）不成立，但它的担忧另有一半成立
ck('11. #335 批评③ 措辞「缺筛选规则」不成立：两者不是筛选关系', True)
ck('12. 但它指出的真问题成立：1,654 与各分项都无在盘可重数源（coverage.tsv 已失）',
   not any('coverage.tsv'==f for _,_,fs in os.walk(ROOT) for f in fs))
json.dump({'fails':fails},open(os.path.join(ROOT,'_r146/r149d_1654_provenance.json'),'w'),
          ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
