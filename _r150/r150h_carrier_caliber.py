#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 H：审计员 #339 报「承载行 13 行」与我报「11 行」的差 —— 判「口径差」还是「真错」。
R14_COMMON §2.8 实例 D 要求：同族先判口径差与真错，再分别处置。
做法：把 7 种读法全部跑一遍，看哪一种能复现 13、哪一种能复现 11，并指出 2 行的差在哪个 token。
只读。
"""
import hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
LED=os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

L=open(LED,encoding='utf-8',errors='replace').read().split('\n')
def tok(p): return re.compile(r'(?<![0-9A-Fa-fx])'+p+r'(?![0-9A-Fa-f])')
# S-359：我最初把 1,196 的严格 token 只写成「带逗号的 1,196」，于是把台账里写成
# 「1196」（无逗号）的两行判成未命中，得 11 行；审计员报 13 行。实测「1196」无逗号是
# 完全合法的写法（负控：11196 / 0x1196 / 111,196 / 11960 都不命中），故正确读法应**两形并列**。
# 修正后严格 token 全四元组 = 13 行，与审计员一致 ⇒ 这是**我的口径缺陷**，不是它编数。
S={'458':tok('458'),'291':tok('291'),'293':tok('293'),
   '1196':re.compile(r'(?<![0-9A-Fa-fx])(?:1,196|1196)(?![0-9A-Fa-f])')}
def sub(p): return p
READINGS={
 'R1 严格token 全四元组': lambda ln: all(r.search(ln) for r in S.values()),
 'R2 严格token 全四元组 且同行有④': lambda ln: all(r.search(ln) for r in S.values()) and '④' in ln,
 'R3 子串 全四元组': lambda ln: all(k in ln for k in ('458','291','293','1,196')) or
                              ('458' in ln and '291' in ln and '293' in ln and '1196' in ln),
 'R4 严格token 458+291+1196（不含293）': lambda ln: S['458'].search(ln) and S['291'].search(ln) and S['1196'].search(ln),
 'R5 严格token 458+291+293（不含1196）': lambda ln: S['458'].search(ln) and S['291'].search(ln) and S['293'].search(ln),
 'R6 严格token 全四元组 且含「口径」': lambda ln: all(r.search(ln) for r in S.values()) and '口径' in ln,
 'R7 严格token 全四元组 且含「独立复算/自行复算」': lambda ln: all(r.search(ln) for r in S.values())
        and re.search(r'独立复算|自行复算|两套独立实现|实跑', ln),
}
got={}
for name,f in READINGS.items():
    idx=[i for i,ln in enumerate(L,1) if f(ln)]
    got[name]=idx
    print('  %-46s %2d  %s'%(name,len(idx),idx[:12]))

r1=got['R1 严格token 全四元组']
ck('1.1 修正后的严格口径 R1 复现 13 行（= 审计员报的数）', len(r1)==13, len(r1))
ck('1.1b 追加负控：1196 的两形并列不吃 11196/0x1196/111,196/11960',
   not S['1196'].search('11196') and not S['1196'].search('0x1196')
   and not S['1196'].search('111,196') and not S['1196'].search('11960'))
hit13=[k for k,v in got.items() if len(v)==13]
print('  能复现 13 的读法:',hit13)
ck('2.1 审计员的 13 行可用某个读法精确复现（⇒ 口径差，不是它编数）', len(hit13)>=1, hit13)
# 差集：修正前后到底差在哪（S-359 已定位为「1196 单形口径」，不是子串污染）
S_BAD={'458':tok('458'),'291':tok('291'),'293':tok('293'),'1196':tok(r'1,196')}
r_bad=[i for i,ln in enumerate(L,1) if all(rx.search(ln) for rx in S_BAD.values())]
print('  S-359 前的错误口径（1196 只认带逗号）得 %d 行：%s'%(len(r_bad), r_bad))
extra=sorted(set(r1)-set(r_bad)); print('  修正后多出的行：%s'%extra)
ck('2.2 修正前 11 行 / 修正后 13 行，多出恰 2 行', len(r_bad)==11 and len(extra)==2, (len(r_bad),extra))
for i in extra:
    ln=L[i-1]
    print('   L%d 的 1196 写法: %s'%(i, re.findall(r'(?<![0-9])1?,?196(?![0-9])', ln)[:3]))
ck('2.3 多出的 2 行里 1,196 都写成无逗号形态（是写法差，不是子串污染）',
   all('1,196' not in L[i-1] and '1196' in L[i-1] for i in extra))

# 反控：必须为真的与必须为假的
ck('3.1 必须为真：R1 的每一行都真含四个严格 token',
   all(all(rx.search(L[i-1]) for rx in S.values()) for i in r1))
def fake_reading(ln): return '458' in ln
ck('3.2 必须为假：换一个只查 458 子串的假读法，行数必然 >11（判据有分辨力）',
   len([i for i,ln in enumerate(L,1) if fake_reading(ln)])>11,
   len([i for i,ln in enumerate(L,1) if fake_reading(ln)]))
ck('3.3 必须为假：自造四元组 77,731/88,842 在该读法下 0 行',
   len([i for i,ln in enumerate(L,1) if '77,731' in ln and '88,842' in ln])==0)

out={'readings':{k:v for k,v in got.items()},'reproduce_13':hit13,
     'extra_lines':sorted(set(got[hit13[0]])-set(r1)) if hit13 else []}
json.dump(out,open(os.path.join(ROOT,'_r150','r150h_carrier_caliber.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
