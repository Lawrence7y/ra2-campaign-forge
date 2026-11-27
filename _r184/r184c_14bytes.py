#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R184 C：F24 的「14 B」到底是哪 14 个偏移，以及正文写的那两组分解是否成立。

背景（S-184c1 / S-184c2 两次自错已写进注释）：
  正文 statement：「两者相差 14 B 全是 JSON 结构开销：1({) + 12(, "bounds": ) + 1(})」
  正文 limitations：「14 B 的逐字节形式：... raw[0:1] + raw[913238:913250] + raw[17624354:17624355]」
  正文 limitations 另写：「该值 = b", "calls": " 的 9 B + dumps(calls) 的 913,228 B」

判据（由算术定义，不由任何人的叙述定义）：
  P1 排除集由两条算术条件唯一定出：不在前 B 个字节（0..B−1）里、也不在 bounds 值段 [bs..be] 里
  P2 该集合拼出的字节串逐字节值
  P3 该串的字符类计数
  P4 正文 statement 的「1({)」是否与 P3 相符
  P5 正文 limitations 的三元组是否与 P1 的偏移集一致
  P6 正文 limitations 的「b", "calls": " 的 9 B」字面长度是否为 9
反控：改 B / 改 S / 换三元组 / 换字面，各让对应断言真红。
"""
import csv
import io
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
LED = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R131_FACTINDEX_V564/FACT_INDEX.tsv')
fails, n_ck = [], 0


def ck(name, cond, detail=''):
    global n_ck
    n_ck += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


raw = open(SRC, 'rb').read()
N = len(raw)
bi = raw.index(b'"bounds"')
bs = raw.index(b'[', bi)
be = N - 2
S = be - bs + 1
B = 913237


def excl_offsets(B_, bs_, be_, N_):
    return [i for i in range(N_) if not (i < B_ or bs_ <= i <= be_)]


print('== A · 三条算术量 ==')
cs = raw.index(b'{', raw.index(b'"calls"'))
ce = raw.rfind(b'}', 0, bi)
val = raw[cs:ce + 1]
ck('A0 N / S / B', (N, S, B) == (17624355, 16711104, 913237), (N, S, B))
ck('A1 D = N − B − S == 14', N - B - S == 14, N - B - S)
ck('A2 逐段重建 == 整文件', b'{"calls": ' + val + raw[ce + 1:bs] + raw[bs:be + 1] + b'}' == raw)

print('== B · 偏移集合（算术唯一定出，不由叙述定）==')
offs = excl_offsets(B, bs, be, N)
ck('B1 该集合恰 14 个偏移', len(offs) == 14, len(offs))
ck('B2 集合 = {913,237..913,249} ∪ {17,624,354}',
   offs == list(range(913237, 913250)) + [17624354], (offs[0], offs[-1], len(offs)))
seg = b''.join(raw[i:i + 1] for i in offs)
ck('B3 拼出的字节串 == b\'}, "bounds": }\'', seg == b'}, "bounds": }', seg)
ck('B4 首字节是右花括号（calls 值的收尾），不是左花括号', seg[0:1] == b'}', seg[0:1])
ck('B5 该右花括号就是 dumps(calls) 的末字节（偏移 913,237 == ce）', ce == 913237 and raw[ce:ce + 1] == b'}', ce)
ck('B6 末字节是文件收尾的右花括号', offs[-1] == N - 1 and raw[N - 1:] == b'}')

print('== C · 字符类计数（「14 B 的逐字节」）==')
cnt = {'space': seg.count(b' '), 'lbrace': seg.count(b'{'), 'rbrace': seg.count(b'}'),
       'comma': seg.count(b','), 'colon': seg.count(b':'), 'quote': seg.count(b'"'),
       'alpha': sum(1 for c in seg if chr(c).isalpha())}
print('   %r' % cnt)
ck('C1 空白 2（R176 的「空白实测 2」成立）', cnt['space'] == 2, cnt['space'])
ck('C2 左花括号 0 / 右花括号 2（R176 的「花括号 2」成立，但两个都是右花括号）',
   cnt['lbrace'] == 0 and cnt['rbrace'] == 2, (cnt['lbrace'], cnt['rbrace']))
ck('C3 逗号 1 / 冒号 1 / 引号 2 / 字母 6',
   (cnt['comma'], cnt['colon'], cnt['quote'], cnt['alpha']) == (1, 1, 2, 6), cnt)
ck('C4 计数和 == 14', sum(cnt.values()) == 14, sum(cnt.values()))

print('== D · 正文两组分解逐条判 ==')
rows = {r['fact_id']: r for r in csv.DictReader(io.open(LED, encoding='utf-8', newline=''), delimiter='\t')}
f24 = rows['F24']
st, lim = f24['statement'], f24['limitations']
ck('D1 statement 的「1({)」与 C2 矛盾（左花括号实测 0 个）',
   st.count('1({)') == 1 and cnt['lbrace'] == 0, st.count('1({)'))
ck('D2 statement 的「1(})」成立（右花括号 2 个，其中一个是末尾那位）',
   st.count('1(})') >= 1 and cnt['rbrace'] == 2)
ck('D3 三项正解应为 1(}) + 12(, "bounds": ) + 1(})，首项被写成左花括号',
   seg == b'}' + b', "bounds": ' + b'}')
ck('D4 limitations 的三元组在文中在场',
   'raw[0:1] + raw[913238:913250] + raw[17624354:17624355]' in lim)
tri_doc = raw[0:1] + raw[913238:913250] + raw[17624354:17624355]
ck('D5 该三元组拼出 b\'{, "bounds": }\'，与 B3 的 b\'}, "bounds": }\' 差首字节',
   tri_doc == b'{, "bounds": }' and tri_doc != seg, (tri_doc, seg))
ck('D6 首项 offset 应为 913,237 而非 0（0 在前 913,237 个字节内，不在排除集里）',
   raw[913237:913238] == seg[0:1] and 0 < B, raw[913237:913238])
ck('D7 limitations 的「b\', "calls": \' 的 9 B」字面长 11 ≠ 9（真 9 B 前缀是 b\'{"calls":\'）',
   ', "calls": ' in lim and len(', "calls": ') == 11
   and len('{"calls":') == 9 and raw[:9] == b'{"calls":',
   (len(', "calls": '), len('{"calls":')))

print('== E · 反控（必须真红）==')
ck('N1 B 改 913,238 ⇒ 排除集 13 个，D 从 14 变 13',
   len(excl_offsets(913238, bs, be, N)) == 13, len(excl_offsets(913238, bs, be, N)))
# S-184c3 自错：初版写首偏移 913,240，实测 913,239（把 B 抬到 913,239 后，913,239 本身也不在
# 「前 B 个字节」里了，故它进排除集；只有 0..B−1 与 [bs..be] 两段被排除）。
ck('N2 B 改 913,239 ⇒ 排除集 12 个，首偏移 913,239（calls 收尾花括号已进 B）',
   len(excl_offsets(913239, bs, be, N)) == 12 and excl_offsets(913239, bs, be, N)[0] == 913239,
   excl_offsets(913239, bs, be, N)[0])
ck('N3 S 改小 1 B（be 取 N−3）⇒ 排除集 15 个',
   len(excl_offsets(B, bs, N - 3, N)) == 15, len(excl_offsets(B, bs, N - 3, N)))
ck('N4 三元组首项改 913237 ⇒ 与 seg 逐字节相同（这正是本文建议的订正）',
   raw[913237:913238] + raw[913238:913250] + raw[17624354:17624355] == seg)
ck('N5 若首项取 raw[0:1]，字符类计数变左 1 / 右 1 / 空白 2 —— 与 R176「花括号 2」不符',
   (tri_doc.count(b'{'), tri_doc.count(b'}'), tri_doc.count(b' ')) == (1, 1, 2),
   (tri_doc.count(b'{'), tri_doc.count(b'}'), tri_doc.count(b' ')))

print()
print('断言 %d 条，FAIL %d 条' % (n_ck, len(fails)))
if fails:
    print('FAIL 列表:', fails)
sys.exit(1 if fails else 0)
