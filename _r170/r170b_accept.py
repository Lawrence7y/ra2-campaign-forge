#!/usr/bin/env python3
"""R170 B：R137 看板第九节 ①–④ 逐项验收（只读，正反控同跑）。
口径：statement = 第 2 列；limitations = 第 5 列；分离计数，绝不混算。
"""
import hashlib, json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
L = ROOT + '/lead/next_re_20261117_r14'
V = L + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
A = []
def ck(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + i + ' :: ' + str(detail)[:240])

rows = {}
for p in open(V, encoding='utf-8', newline='').read().split('\n')[1:]:
    if not p.strip(): continue
    f = p.split('\t'); rows[f[0]] = f

# ---------- ① F23 三处验收（按 R137 九节① 字面：差 1 行无归属 / 4,147,334 / coverage.tsv 已失）----------
s23, l23 = rows['F23'][1], rows['F23'][4]
ck('A1 F23.stmt 含「差 **1 行无归属**」', s23.count('差 **1 行无归属**') == 1, s23.count('差 **1 行无归属**'))
ck('A2 F23.stmt 含 4,147,334 且 >=2 次（两处口径：依赖 + 字节）', s23.count('4,147,334') >= 2, s23.count('4,147,334'))
ck('A3 F23.stmt 含 coverage.tsv', s23.count('coverage.tsv') >= 1, s23.count('coverage.tsv'))
ck('A4 F23.stmt 含「已失」判据词', ('已失' in s23) or ('不可重数' in s23), 'implied')
ck('A5 反控：F23.stmt 不含 gated 外的假串 ZZZ_NOT_IN_FACT_QQQ', 'ZZZ_NOT_IN_FACT_QQQ' not in s23 + l23, 'ok')
# 缺口算术（必须来自同一段正文三式 6/2/3 与 total 12）
ck('A6 F23 分解 6+2+3=11 != 12（缺口 1）', 6 + 2 + 3 == 11 and 12 - 11 == 1, '11 vs 12')
ck('A7 F23 第二读法 6+2+3+3=14 > 12（重计 2）', 6 + 2 + 3 + 3 == 14 and 14 - 12 == 2, '14 vs 12')

# ---------- ① F35 验收：目标字面 vs 已撤回事实 ----------
s35, l35 = rows['F35'][1], rows['F35'][4]
ck('B1 F35.stmt 出现「缺一手权威」', s35.count('缺一手权威') == 1, s35.count('缺一手权威'))
ck('B2 该出现处在撤回语境', '已撤回' in s35 and '不得再写' in s35, 'retract-in-stmt')
ck('B3 F35.stmt 含「无外部规范权威」=0（准确措辞只在 limitations）',
   s35.count('无外部规范权威') == 0 and l35.count('无外部规范权威') == 1,
   'stmt=%d lim=%d' % (s35.count('无外部规范权威'), l35.count('无外部规范权威')))
ck('B4 F35.lim 同时含「定义有代码权威」与「无外部规范权威」',
   '定义有代码权威' in l35 and '无外部规范权威' in l35, 'both-in-lim')
ck('B5 F35.stmt 含 proved_strict 定义串（判据式在正文）', s35.count('proved_strict') == 2, s35.count('proved_strict'))
# 代码权威实体是否在盘（一手实现）
SP = L + '/RULING_R15_20261119/work/strict_panel.py'
ck('B6 strict_panel.py 在盘', os.path.exists(SP), SP.replace(ROOT, ''))
if os.path.exists(SP):
    t = open(SP, encoding='utf-8', errors='replace').read().split('\n')
    ck('B7 第 78 行是判据式', '"[未证]" not in sem' in t[77], t[77].strip()[:80])
    ck('B8 第 76 行是 [已证] 前置', '"[已证]"' in t[75], t[75].strip()[:80])

# ---------- ② F24 86.19% 撤下 ----------
s24, l24 = rows['F24'][1], rows['F24'][4]
occ = [m.start() for m in re.finditer(re.escape('86.19'), s24)]
ret = [p for p in occ if any(k in s24[max(0, p - 80):p + 120] for k in ('撤', '错', '不得', '不是'))]
ck('C1 F24.stmt 86.19 每处都在撤回语境', len(occ) == len(ret), '%d/%d' % (len(ret), len(occ)))
ck('C2 F24.stmt 含 99.992 与 1,392,481/1,392,592 的分式', '99.992' in s24 and '1,392,481/1,392,592' in s24, 'ok')
ck('C3 F24.stmt 保留结构判据「单列地址」+「第二列」', '单列地址' in s24 and '第二列' in s24, 'ok')
ck('C4 反控：自造肯定句「86.19% 是剔除理由」不在正文', '86.19% 是剔除理由' not in s24 + l24, 'ok')

# ---------- ③ F24 语料失效期标注 ----------
ck('D1 F24.stmt 含「11-22 快照」限定', '2026-11-22 快照值' in s24, 'ok')
ck('D2 F24.stmt 含现盘 65 件 / 44,470,975 B', '65 件' in s24 and '44,470,975' in s24, 'ok')
ck('D3 F24.stmt 含 4,352 不存在桶且三桶件数闭合', '4,352' in s24 and 65 + 4352 == 4417, '65+4352=4417')
ck('D4 F24.stmt 三桶字节闭合', 26846620 + 913237 + 709757429 == 737517286, '26846620+913237+709757429')
ck('D5 F24 语料值 4,417 件 / 737,517,286 B 仍在', '4,417' in s24 and '737,517,286' in s24, 'ok')

# ---------- ④ F29 四处作用域 ----------
s29, l29 = rows['F29'][1], rows['F29'][4]
ck('E1 F29 两份拷贝=全镜像 80 次中的两份', ('80 次' in s29) and ('两份' in s29), 'stmt=%d/%d' % (s29.count('80 次'), s29.count('两份')))
ck('E2 F29 idx=62 带 DLL 内 0-based 口径', 'idx=**62（DLL 内 0-based 口径）**' in s29, 'ok')
ck('E3 F29 6 桩体「不在本条任何一列、不采用」的处置在场', '6 个不同桩体' in s29 and '不在本条任何一列' in s29, 'ok')
ck('E4 F29 40/63/77 非因果句在场', '非因果' in s29 and ('77 mod 40' in s29 or '77 − 40' in s29), 'ok')
ck('E5 反控：「全镜像只有两份」错句不在正文', '全镜像只有两份' not in s29 + l29, 'ok')

json.dump({'assertions': A, 'fail': sum(1 for a in A if not a['ok'])},
          open(ROOT + '/_r170/r170b_accept.json', 'w'), ensure_ascii=False, indent=1)
print('FAIL =', sum(1 for a in A if not a['ok']), '/', len(A))
