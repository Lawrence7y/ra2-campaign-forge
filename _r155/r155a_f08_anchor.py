#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R155 A：F08 第 ② 项证据锚点（R17_LEDGER_1064/SECTION.md 事项4）到底承载不承载 a–e。
一条命令输出全部证据 + 正反控。只判「锚点承载性」，不判事实真假。"""
import os, re, json, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
LED  = os.path.join(LEAD, 'GOAL_THREE_TARGETS_20261018.md')
RC   = os.path.join(LEAD, 'next_re_20261117_r14', 'R14_COMMON.md')
IDX  = os.path.join(LEAD, 'next_re_20261117_r14', 'R17_R114_FACTINDEX_V542', 'FACT_INDEX.tsv')

fails, out = [], {}
def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

led = open(LED, encoding='utf-8').read()
rc  = open(RC,  encoding='utf-8').read()

# ---------- 1 · §1064 节边界（用台账实际节头形态 §1064） ----------
h1064 = re.search(r'(?m)^## §1064 ·', led)
h1065 = re.search(r'(?m)^## §1065 ·', led)
ck('1.1 §1064 节头存在', bool(h1064))
ck('1.2 §1065 节头存在（右边界）', bool(h1065))
ck('1.3 §1064 左界 < 右界', h1064.start() < h1065.start(), (h1064.start(), h1065.start()))
sec = led[h1064.start():h1065.start()]
out['sec1064_chars'] = len(sec)
out['sec1064_bytes'] = len(sec.encode('utf-8'))
ck('1.4 §1064 节长在合理区间 2000..20000', 2000 < len(sec) < 20000, len(sec))

# ---------- 2 · 事项边界（节内 事项 N） ----------
marks = [(m.start(), int(m.group(1))) for m in re.finditer(r'事项\s*([1-6])', sec)]
nums = sorted(set(n for _, n in marks))
ck('2.1 节内出现事项号集合 = {1,2,3,4,5,6}', nums == [1,2,3,4,5,6], nums)

def slice_item(n):
    """事项 n 的切片：从节内第一处「事项 n」到下一事项号首次出现处（按位置序，允许编号回退时断开）。"""
    start = None
    for pos, num in marks:
        if num == n:
            start = pos; break
    if start is None: return ''
    end = len(sec)
    for pos, num in marks:
        if pos > start and num == n + 1:
            end = pos; break
    return sec[start:end]

it4 = slice_item(4)
out['item4_chars'] = len(it4)
ck('2.2 事项4 切片非空', len(it4) > 50, len(it4))
ck('2.3 事项4 切片起点在节内',
   0 <= sec.find(it4) < len(sec), sec.find(it4))

# ---------- 3 · token 承载矩阵 ----------
TOK = ['0x47C3D0', '0x6F322F', '0x6F2B40', '硬件读断点', '0x449440', '0x47C620', '(a′)', '(a)']
# 第 ① 项承载区：R14_COMMON §2.9 一 与 §2.10 一/二
def rc_slice():
    a = re.search(r'(?m)^## 2\.9\b', rc); b = re.search(r'(?m)^## 2\.10\b', rc)
    c = re.search(r'(?m)^## 2\.11\b', rc)
    return rc[a.start():c.start()] if (a and c) else ''
rslice = rc_slice()
# S-407: 并集切片不能支撑「§2.9 与 §2.10 各 >=1」这种措辞，必须逐节计数
_a = re.search(r'(?m)^## 2\.9\b', rc); _b = re.search(r'(?m)^## 2\.10\b', rc)
_c = re.search(r'(?m)^## 2\.11\b', rc)
sec29  = rc[_a.start():_b.start()]
sec210 = rc[_b.start():_c.start()]
out['sec29_chars'] = len(sec29); out['sec210_chars'] = len(sec210)
out['rc_29_210_chars'] = len(rslice)
ck('3.0 R14_COMMON §2.9..§2.10 切片取到', len(rslice) > 500, len(rslice))

mat = {}
for t in TOK:
    mat[t] = {'sec1064': sec.count(t), 'item4': it4.count(t),
              'rc_29_210': rslice.count(t), 'rc_29': sec29.count(t), 'rc_210': sec210.count(t)}
out['token_matrix'] = mat
print()
print('  %-12s %-10s %-8s %-8s %-8s' % ('token', '§1064全节', '事项4', '§2.9', '§2.10'))
for t in TOK:
    print('  %-12s %-10d %-8d %-8d %-8d' % (t, mat[t]['sec1064'], mat[t]['item4'],
                                              mat[t]['rc_29'], mat[t]['rc_210']))

# ---------- 4 · 主张：a–e 四个判别 token 在 §1064 全节 0 次 ----------
AE = ['0x47C3D0', '0x6F322F', '0x6F2B40', '硬件读断点']
ck('4.1 a–e 四 token 在 §1064 全节各 0 次',
   all(mat[t]['sec1064'] == 0 for t in AE),
   {t: mat[t]['sec1064'] for t in AE})
ck('4.2 a–e 四 token 在事项4 各 0 次',
   all(mat[t]['item4'] == 0 for t in AE),
   {t: mat[t]['item4'] for t in AE})
ck('4.3 a–e 四 token 在 R14_COMMON §2.9 ∪ §2.10 并集内各 >=1 次',
   all(mat[t]['rc_29_210'] >= 1 for t in AE),
   {t: mat[t]['rc_29_210'] for t in AE})
# S-407: 上一版把并集写成「§2.9 与 §2.10 各 >=1」，逐节看立刻不成立 —— 这里把它拆成两条硬断言
ck('4.4 a–e 四 token 全部由 §2.9 单独承载（各 >=1）',
   all(mat[t]['rc_29'] >= 1 for t in AE), {t: mat[t]['rc_29'] for t in AE})
ck('4.5 §2.10 对 a–e 四 token 各 0 次（不承载 a–e）',
   all(mat[t]['rc_210'] == 0 for t in AE), {t: mat[t]['rc_210'] for t in AE})
ck('4.6 §2.10 只承载 (a′) 且 >=1 次', mat['(a′)'][ 'rc_210'] >= 1, mat['(a′)']['rc_210'])
ck('4.7 §2.9 对 (a′) 0 次（(a′) 只在 §2.10）', mat['(a′)']['rc_29'] == 0, mat['(a′)']['rc_29'])

# ---------- 5 · 正反控（判据有分辨力，不是恒真/恒假） ----------
# 正控：把 §1064 全节拼上 R14_COMMON 切片后，同一判据必须翻转（0 -> >=1）
ctrl_pos = (sec + rslice)
ck('5.1 正控：拼接后 a–e 四 token 各 >=1（判据能翻转）',
   all(ctrl_pos.count(t) >= 1 for t in AE),
   {t: ctrl_pos.count(t) for t in AE})
# 反控：把 token 改一个字符，必须 0 命中（不是子串恒真）
for t in AE:
    mut = t.replace('0x', '0y') if t.startswith('0x') else t + 'X'
    ck('5.2 反控：变异 token %r 在 §1064 全节 0 次' % mut, sec.count(mut) == 0, sec.count(mut))
# 反控：正控切片若误取整份 R14_COMMON，则 §2.11 之后的内容不得混入（切片边界有效）
ck('5.3 反控：R14_COMMON 切片不含 §2.11 节头', '## 2.11' not in rslice, '## 2.11' in rslice)

# ---------- 6 · F08 行 evidence_paths 的两项逐个 stat ----------
rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
d = {r[0]: r for r in rows[1:]}
ck('6.1 数据行 54', len(rows) - 1 == 54, len(rows) - 1)
ck('6.2 F08 行存在', 'F08' in d)
ev = d['F08'][3]
items = [x.strip() for x in ev.split(';') if x.strip()]
out['f08_evidence_paths'] = ev
out['f08_items'] = items
ck('6.3 F08 证据项恰 2 项', len(items) == 2, len(items))
stat = {}
for it in items:
    p = re.split(r'[\(（]', it)[0].strip().replace('\\', '/')
    ap = os.path.join(ROOT, p)   # S-401: 路径自带 lead/ 前缀，拼 LEAD 会得 lead/lead
    stat[it] = {'path': p, 'exists': os.path.isfile(ap),
                'bytes': os.path.getsize(ap) if os.path.isfile(ap) else None}
    print('    %s -> %s %s' % (it, 'EXIST' if os.path.isfile(ap) else 'MISSING',
                               stat[it]['bytes']))
out['f08_item_stat'] = stat

# ---------- 7 · 台账 §1064 自己的定位句（它到底写了什么） ----------
# 事项4 首 300 字与含 0x449440 的行（R154 说那 1 行是节名行）
print()
print('  --- 事项4 首 300 字 ---')
print('  ' + it4[:300].replace('\n', '\n  '))
l449 = [l for l in sec.split('\n') if '0x449440' in l]
out['item4_has_449440_lines'] = len(l449)
print('  --- §1064 内含 0x449440 的行 %d 条 ---' % len(l449))
for l in l449:
    print('    ' + l[:200])
# S-402: R154 的主张是「事项4 提到 0x449440 的那 1 行是节名行」，不是「事项4 不含 0x449440」
_l4 = [l for l in it4.split('\n') if '0x449440' in l]
out['item4_449440_lines'] = _l4
ck('7.1 事项4 内 0x449440 恰 1 行', len(_l4) == 1, len(_l4))
# S-403: 该行前面有列表符号「-」，须先剥列表标记再判是不是节名行
_strip = lambda x: re.sub(r'^[\s\-\*\u2022]+', '', x)
ck('7.2 该 1 行是节名行（剥列表标记后以「节名：## 2.10」开头）',
   bool(_l4) and _strip(_l4[0]).startswith('节名：## 2.10'),
   _strip(_l4[0])[:60] if _l4 else '')

json.dump(out, open(os.path.join(ROOT, '_r155', 'r155a_f08_anchor.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('  FAILS = %d  %s' % (len(fails), fails))
