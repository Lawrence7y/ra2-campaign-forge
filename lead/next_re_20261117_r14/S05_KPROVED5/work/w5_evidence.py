# -*- coding: utf-8 -*-
"""w5: 从已核验的 JSON 生成 7 张 ③a 行的 EVIDENCE 文本（③b① 候选 00709A40 已单独手写）。"""
import os,json
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED5"
s=json.load(open(os.path.join(BASE,'EVIDENCE','ROW_SUMMARY.json'),encoding='utf-8'))
for r in s['rows']:
    if r['entry']=='00709A40': continue
    txt="ROW %s  name=%s  ③b档=③a  delta=NO\n"%(r['entry'],r['name'])
    txt+="="*72+"\n"
    txt+="[① 入口形态] %s\n"%r['ring1']
    txt+="[② 全部持有表] %s\n"%r['ring2']
    txt+="[③b 档位与明细] %s\n"%r['ring3']
    txt+="[④ 直接调用站点] %s\n"%r['ring4']
    txt+="[四环综述] ①✓ ②✓ ④✓ ③仅③a ⇒ 三环齐全但缺环③b，不进 delta。理由入 UNKNOWNS.md。\n"
    open(os.path.join(BASE,'EVIDENCE','ROW_%s.txt'%r['entry']),'w',encoding='utf-8').write(txt)
    print("wrote ROW_%s.txt"%r['entry'])
