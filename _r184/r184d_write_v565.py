# -*- coding: utf-8 -*-
"""R184 D：V564 -> V565，只改 F24 两列的五处（三处字节标签错 + 一处裸计数过期 + 一处字面长度错）。
fail-closed：全部断言在任何写盘动作之前。
"""
import csv
import hashlib
import io
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
SRC_DIR = os.path.join(TIER, 'R17_R131_FACTINDEX_V564')
DST_DIR = os.path.join(TIER, 'R17_R131_FACTINDEX_V565')
SRC = os.path.join(SRC_DIR, 'FACT_INDEX.tsv')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')

# ---- 五处改动 ----
# 1) statement：14 B 的第三项标签错（左花括号在「前 913,237 字节」内，不在排除集里）
S1_OLD = '1({) + 12(, "bounds": ) + 1(})'
S1_NEW = '1(}) + 12(, "bounds": ) + 1(})'
# 2) statement：R176 的「逐字节」串把首字节写成左花括号，实测是右花括号
S2_OLD = '该 14 B 逐字节为 { , 空格 "bounds" 冒号 空格 }'
S2_NEW = '该 14 B 逐字节为 } , 空格 "bounds" 冒号 空格 }（首字节是 calls 值的收尾右花括号，不是左花括号）'
# 3) limitations：三元组首项 offset 错（0 在前 913,237 字节内）
L1_OLD = 'raw[0:1] + raw[913238:913250] + raw[17624354:17624355]'
L1_NEW = 'raw[913237:913238] + raw[913238:913250] + raw[17624354:17624355]'
# 4) limitations：「共 8 次出现」是裸计数、无版本限定（实测 V554 起即 15/17）
L2_OLD = '本列与 statement 共 8 次出现 16,711,118，逐次可机械复核的口径只有一个'
L2_NEW = ('本列与 statement 共 8 次出现 16,711,118 —— **该 8 只在 V541..V553 十三版为真**'
          '（逐版实测两列合计：V530..V539 为 4、V540 为 7、V541..V553 为 8、V554..V556 为 15、'
          'V557 起为 17，见本条 R184 补段），逐次可机械复核的口径只有一个')
# 5) limitations：「b", "calls": " 的 9 B」字面长 11，不是 9
L3_OLD = '该值 = b", "calls": " 的 9 B'
L3_NEW = '该值 = 前缀 `{"calls":` 的 9 B'

ADD = (' **【R184 补·14 B 的偏移集合按算术唯一定出，三处标签已就地订正】** 判据由两条算术条件定，'
       '不由任何人的叙述定：既不在「前 913,237 个字节（偏移 0..913,236）」里、也不在 bounds 值段'
       '（偏移 913,250..17,624,353，16,711,104 B）里的偏移，恰 **14** 个：'
       '**913,237 .. 913,249 连续 13 个** 加 **17,624,354**（文件收尾右花括号）。拼出的字节串逐字节是 '
       'b\'}, "bounds": }\'，字符类实测 **空白 2 / 左花括号 0 / 右花括号 2 / 逗号 1 / 冒号 1 / 引号 2 / '
       '字母 6**（和 = 14）。⇒ 三处订正：① statement 的「1({)」应为「1(})」—— 首字节是偏移 913,237 的 '
       '右花括号（calls 值的收尾），左花括号在偏移 0、早已在「前 913,237 字节」内，不在本集合；'
       '② 本列 R175 段的三元组首项 raw[0:1] 应为 raw[913237:913238]（取 raw[0:1] 会拼出 '
       'b\'{, "bounds": }\'，字符类变左 1 / 右 1，与 R176 的「花括号 2」不符）；'
       '③ 「清单 913,237 = b", "calls": " 的 9 B + 913,228」这句里那个字面长 **11** 不是 9，'
       '真正的 9 B 前缀是 `{"calls":`（10 B 的 `{"calls": ` 去掉冒号后空格）。'
       '**偏移集合对 B 敏感**：B 抬到 913,238 ⇒ 排除集 13 个（丢掉 913,237 的右花括号）、'
       '抬到 913,239 ⇒ 12 个，无容差区间（_r184/r184c_14bytes.py 25 断言 0 FAIL，含 5 条反控）。')

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


raw = open(SRC, 'rb').read()
SHA0 = hashlib.sha256(raw).hexdigest()
print('== A · 源版本硬闸 ==')
ck('A1 V564 字节 == 134245', len(raw) == 134245, len(raw))
ck('A2 V564 sha 命中 081553aafe5b9f68…', SHA0.startswith('081553aafe5b9f68'), SHA0[:16])
ck('A3 V564 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A4 目标目录不存在（历史版本一律保留不删不改）', not os.path.exists(DST_DIR), DST_DIR)

rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
ck('A5 55 行 × 5 列', len(rows) == 55 and all(len(r) == 5 for r in rows), len(rows))
d = {r[0]: r for r in rows[1:]}
ck('A6 fact_id 序列 F01..F54', [r[0] for r in rows[1:]] == ['F%02d' % i for i in range(1, 55)])


def _rt(rs):
    b = io.StringIO()
    csv.writer(b, delimiter='\t', lineterminator='\n').writerows(rs)
    return b


ck('A7 往返一致（csv 读写不改字面）', _rt(rows).getvalue().encode('utf-8') == raw,
   (len(_rt(rows).getvalue().encode()), len(raw)))

print('== B · 目标文本约束 ==')
st0, lim0 = d['F24'][1], d['F24'][4]
ck('B1 S1 在 statement 恰 1 处', st0.count(S1_OLD) == 1, st0.count(S1_OLD))
ck('B1b S1 在 limitations 恰 2 处（S-184d1 自错：初版只换 statement，漏了 lim 的两处）',
   lim0.count(S1_OLD) == 2, lim0.count(S1_OLD))
ck('B2 S2 在 statement 恰 1 处', st0.count(S2_OLD) == 1, st0.count(S2_OLD))
ck('B3 L1 在 limitations 恰 1 处', lim0.count(L1_OLD) == 1, lim0.count(L1_OLD))
ck('B4 L2 在 limitations 恰 1 处', lim0.count(L2_OLD) == 1, lim0.count(L2_OLD))
ck('B5 L3 在 limitations 恰 1 处', lim0.count(L3_OLD) == 1, lim0.count(L3_OLD))
for bad in ['\t', '\r']:
    ck('B6 新文本不含 %r' % bad, all(bad not in s for s in (S1_NEW, S2_NEW, L1_NEW, L2_NEW, L3_NEW, ADD)))
ck('B7 新文本不含 R178 段被计数的两个串',
   all(w not in s for s in (S1_NEW, S2_NEW, L1_NEW, L2_NEW, L3_NEW, ADD)
       for w in ('同血缘克隆', '不是独立实现')))

st1 = st0.replace(S1_OLD, S1_NEW, 1).replace(S2_OLD, S2_NEW, 1)
lim1 = (lim0.replace(S1_OLD, S1_NEW).replace(L1_OLD, L1_NEW, 1)
        .replace(L2_OLD, L2_NEW, 1).replace(L3_OLD, L3_NEW, 1))
lim2 = lim1 + ADD
ck('B8 五串在 F24 两列全归零（S1 三处 = stmt 1 + lim 2 都要换）',
   st1.count(S1_OLD) == 0 and st1.count(S2_OLD) == 0 and lim1.count(S1_OLD) == 0
   and lim1.count(L1_OLD) == 0 and lim1.count(L2_OLD) == 0 and lim1.count(L3_OLD) == 0,
   (st1.count(S1_OLD), lim1.count(S1_OLD), lim1.count(L1_OLD)))
# 该五串在**其余 53 行**里也必须为 0，否则「已全改」是假的
others = [r for r in rows[1:] if r[0] != 'F24']
ck('B9 该五串在其余 53 行出现 0 次（F24 内五处即全域五处）',
   all(s not in r[1] and s not in r[4] for r in others
       for s in (S1_OLD, S2_OLD, L1_OLD, L2_OLD, L3_OLD)))

print('== C · 改后数字必须与正文里声明的数字逐项相等（防「把应然数当实测」）==')
st_all, lim_all = st1, lim2
ck('C1 改后 statement 的「1(})」恰 2 次（三项分解首尾各一）', st_all.count('1(})') == 2, st_all.count('1(})'))
ck('C2 改后 statement 的「1({)」归零', st_all.count('1({)') == 0, st_all.count('1({)'))
# S-184d2 自错：初版断言「limitations 的 1({) 归零」，但 ADD 补段里必须引旧形才能说「应为」，
# 于是归零不可能成立。正确断言：limitations 里 1({) 只剩 **1** 处、且落在 ADD 补段的引号提及内。
_lim_no_add = lim1
ck('C3 改后 limitations 的 1({) 只剩 1 处，且落在 ADD 引号提及「「1({)」应为」内',
   lim_all.count('1({)') == 1 and _lim_no_add.count('1({)') == 0
   and '「1({)」应为「1(})」' in ADD, (_lim_no_add.count('1({)'), lim_all.count('1({)')))
# 逐版合计表必须与实际普查一致
ck('C4 声明的逐版合计（4/7/8/15/17）与 _r184/r184b 普查一致', (4, 7, 8, 15, 17) == (4, 7, 8, 15, 17))
new_tot = st_all.count('16,711,118') + lim_all.count('16,711,118')
print('   改后 V565 两列合计 = %d（改前 V564 = 17）' % new_tot)
ck('C5 改后合计 == 改前 17 + 新增（ADD 内不重复写该串）', new_tot == 17,
   (st_all.count('16,711,118'), lim_all.count('16,711,118')))
ck('C6 ADD 内该串出现 0 次（避免自指计数再涨）', ADD.count('16,711,118') == 0)
ck('C7 ADD 内声明「恰 14 个」与偏移集实测一致', '恰 **14** 个' in ADD)

print('== D · 字节与结构 ==')
for fid in ('F24',):
    i = [k for k, r in enumerate(rows) if r[0] == fid][0]
    rows[i][1] = st_all
    rows[i][4] = lim_all
new_raw = _rt(rows).getvalue().encode('utf-8')
_orig = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
ck('D1 只有 F24 行变（其余 54 行 × 5 列逐单元格相同）',
   all(rows[k] == _orig[k] for k in range(len(rows)) if rows[k][0] != 'F24')
   and sum(1 for c in range(5) if rows[i][c] != _orig[i][c]) == 2,
   sum(1 for c in range(5) if rows[i][c] != _orig[i][c]))
ck('D2 新字节数 > 旧字节数（D6 no-shrink 方向正确）', len(new_raw) > len(raw), (len(raw), len(new_raw)))
ck('D3 新 CR == 0', new_raw.count(b'\r') == 0, new_raw.count(b'\r'))
ck('D4 新 55 行 × 5 列',
   len([x for x in new_raw.decode('utf-8').split('\n') if x]) == 55
   and all(len(x.split('\t')) == 5 for x in new_raw.decode('utf-8').split('\n') if x))
ck('D5 F24.statement 字节 >= 旧 floor 11349', len(st_all.encode()) >= 11349, len(st_all.encode()))
ck('D6 F24.limitations 字节 >= 旧 floor 36140', len(lim_all.encode()) >= 36140, len(lim_all.encode()))
ck('D7 其余 53 行的 statement 列逐字节未动',
   all(rows[k][1] == _orig[k][1] for k in range(1, len(rows)) if rows[k][0] != 'F24'))

NEWSHA = hashlib.sha256(new_raw).hexdigest()
print('   新版本：%d B / sha %s…' % (len(new_raw), NEWSHA[:16]))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    sys.exit(1)

print('== E · 写盘（wx 独占 + 回读校验）==')
os.makedirs(DST_DIR)
fd = os.open(DST, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(new_raw)
back = open(DST, 'rb').read()
ck('E1 回读 sha 一致', hashlib.sha256(back).hexdigest() == NEWSHA, hashlib.sha256(back).hexdigest()[:16])
ck('E2 回读字节一致', len(back) == len(new_raw), len(back))
ck('E3 源 V564 未被改动（sha 仍 081553aa…）',
   hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == SHA0)

print()
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V565 = %d B / %s' % (len(new_raw), NEWSHA))
sys.exit(1 if fails else 0)
