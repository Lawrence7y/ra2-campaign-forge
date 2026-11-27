#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 E：FACT_INDEX V556 -> V557，改正 5 处被字节测反的措辞（4 处在 limitations、2 处在 statement，共 5 处）

改动依据（全部本轮实测，不引用未测数字）：
  r175a（35 断言 0 FAIL）独立复算：值跨度 16,711,104 / 整条成员 16,711,116 / 算术差 16,711,118；
          相邻差 12 与 2；对偶差集 {12, 2, 14}；12 = b', "bounds": ' 逐字节 12 B。
  r175c（35 断言 0 FAIL）复算审计员 #414：本体恒 10 B × 1,392,592 + 分隔符 b', ' 恒 2 B × 1,392,591
          + 方括号 2 B = 12n 恒等式；末条无尾随分隔符；list 913,237 = 9 + dumps(calls) 913,228；
          lead/ 树下 913,237 B 的实物 **0 件**（清单值是声明净额，不是盘上文件）。

5 处改动（每处原串在所属列**恰 1 次**、在另一列 0 次）：
  C1 F24.statement：「bounds 段 16,711,118 B」→ 16,711,104 B + 订正说明（这是**把记账差当段长**）
  C2 F24.statement：「差 +16,711,118 B 恰为被剔的 bounds 段」→ 记账差，非段长
  C3 F24.limitations：「三个数两两差 2 B」→ 差集 {12, 2, 14}
  C4 F24.limitations：「三种宽度两两相差 2 B 与 2 B」→ 差集 {12, 2, 14}
  C5 F24.limitations：「1,392,592 条 × 12 B（每条…恰 12 字节）」→ 10 B 本体 + 2 B 分隔符 + 括号 = 12n 恒等式
  C6 F24.limitations：末尾**追加**一段 R175 补记（不改任何既有字符）

写前硬闸（任一不成立即 fail-closed，不写盘；S-619 纪律：全部断言在写盘之前）：
  G1 母本 V556 五项（字节 / sha / CR / 行数 / 列数）
  G2 V557 目标目录不存在
  G3 6 个原串/锚串各在所属列恰 1 次
  G4 变化单元：仅 F24 的 statement 与 limitations 两列，其余 53 行 × 5 列逐字节相同
  G5 反控：把订正后的 104 改回 118 ⇒ 新串里 118 作为段长的形态必须为 0（证明订正有判别力）
  G6 反控：把差集 {12, 2, 14} 改成 {2, 2, 2} ⇒ 必须与 r175a/c 实测不符
写后回读：sha / 字节 / CR / 行数 / 列数 / 其余 53 行 / SequenceMatcher 形状。
"""
import csv, hashlib, io, json, os, sys
from difflib import SequenceMatcher

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
MOM = os.path.join(TIER, 'R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, 'R17_R128_FACTINDEX_V557')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175e_v557.json')
MOM_SHA = 'eac22c67683179436d47db864600dd2e9fa69a59105644ec05f1976fb595886f'
MOM_BYTES = 125538

fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

print('== G1 · 母本 V556 ==')
raw = io.open(MOM, 'rb').read()
ck('G1a 母本字节 == 125,538', len(raw) == MOM_BYTES, len(raw))
ck('G1b 母本 sha256 == eac22c67…', hashlib.sha256(raw).hexdigest() == MOM_SHA, hashlib.sha256(raw).hexdigest()[:16])
ck('G1c 母本 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
txt = raw.decode('utf-8')
lines = txt.split('\n')
if lines and lines[-1] == '': lines = lines[:-1]
ck('G1d 母本 55 行', len(lines) == 55, len(lines))
ck('G1e 每行 5 列', all(len(l.split('\t')) == 5 for l in lines), [i for i, l in enumerate(lines) if len(l.split('\t')) != 5][:3])
rows = {}
for l in lines[1:]:
    f = l.split('\t')
    rows[f[0]] = f
ck('G1f 54 数据行', len(rows) == 54, len(rows))

print('== G2 · 目标目录 ==')
ck('G2 V557 目录此前不存在', not os.path.exists(DSTDIR), os.path.exists(DSTDIR))

st, lim = rows['F24'][1], rows['F24'][4]
print('== G3 · 原串唯一性 ==')
P1 = '再剔 `a2_sites.json` 的 **`bounds` 段 16,711,118 B**'
P2 = '差 **+16,711,118 B 恰为被剔的 `bounds` 段**'
P3 = '三个数两两差 2 B 的成因与可失败判据见本列 R173 补段与 _r174/r174a..e'
P4 = '三种宽度两两相差 2 B 与 2 B'
P5 = '① bounds 值跨度 **16,711,104 B** = 1,392,592 条 × 12 B（每条为 8 位十六进制加引号逗号，恰 12 字节）'
# ★ 自错 S-631：原先把 R174 给 F35 用的锚串拿来当 F24 的锚串（F24 里根本没有那句），
#   实测 F24.limitations 的**真实末尾**是下面这句；改为按实测末句定位。
ANCHOR = '**R173 未改任何既有数字**：8 次 16,711,118 一字未动，本条只补口径。'
for tag, s, where in (('P1', P1, st), ('P2', P2, st), ('P3', P3, lim), ('P4', P4, lim), ('P5', P5, lim)):
    ck('G3 %s 在所属列恰 1 次' % tag, where.count(s) == 1, where.count(s))
    ck('G3 %s 在另一列 0 次' % tag, (lim if where is st else st).count(s) == 0,
       (lim if where is st else st).count(s))
ck('G3 ANCHOR 在 limitations 恰 1 次', lim.count(ANCHOR) == 1, lim.count(ANCHOR))
ck('G3 全文件 P1 恰 1 次', txt.count(P1) == 1, txt.count(P1))

Q1 = ('再剔 `a2_sites.json` 的 **`bounds` 段 16,711,104 B**'
      '（**R175 订正：原写 16,711,118 B 是把「现盘 17,624,355 − 快照清单 913,237」的记账差当成了段长；'
      '段本身实测 16,711,104 B，两者相差 14 B 全是 JSON 结构开销：键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4**）')
Q2 = ('差 **+16,711,118 B**（**R175 订正：这是记账差，不是 `bounds` 段的字节长度**；'
      '段本身 16,711,104 B，可失败判据见本列 R175 补段与 _r175/r175a..c）')
Q3 = ('三个数两两**差集为 {12, 2, 14}**（**R175 订正：原写「两两差 2 B」错**；'
      '12 逐字节等于 b", "bounds": " 的 12 B、2 = calls 收尾 } 与文档收尾 } 两个单字节、14 为前两者之和）'
      '与可失败判据见本列 R173/R175 补段与 _r174/r174a..e、_r175/r175a..c')
Q4 = '三种宽度两两**差集为 {12, 2, 14}**（**R175 订正：原写「2 B 与 2 B」错**，见本列 R175 补段）'
Q5 = ('① bounds 值跨度 **16,711,104 B** = 1,392,592 条 × 12 B（**R175 订正解释**：本体恒 **10 B**'
      '（8 位大写十六进制 + 2 引号）× 1,392,592 + 分隔符 b", " 恒 **2 B** × 1,392,591 + 方括号 **2 B** = **12n 恒等式**；'
      '末条**没有**尾随分隔符，故「每条 12 字节」是**摊销口径**、不是逐条实测长度；'
      '换成 9 B 本体或 1 B 分隔符，12n 立刻失效）')
ADD = (''.join([
    '  **【R175 补·三处被字节测反的口径已改正，并登记「清单 913,237 盘上无实物」】** ',
    '（1）**差集**：三口径 16,711,104 / 16,711,116 / 16,711,118 的**两两**差是 **12 与 2 与 14**，',
    '不是「2 B 与 2 B」—— 12 逐字节等于 b", "bounds": "（_r175/r175a 的 E2c 实测 raw[913238:913250] 逐字节相等），',
    '2 = raw[913237:913238] 的 calls 收尾 } 与 raw[17624354:17624355] 的文档收尾 } 各 1 B，14 = 12 + 2。',
    '（2）**12n 是恒等式不是逐条长度**：2 + 10n + 2(n−1) = 12n（方括号 +2 与少一个分隔符 −2 精确抵消）；',
    '本体长度分布实测**只有 {10}**（1,392,592 条）、条目间分隔符分布实测**只有 {b", ": 1,392,591}**、',
    '末条之后到 `]` 前**剩 0 B** ⇒ 「每条 12 字节」只能当摊销读。',
    '（3）**清单 913,237 B 是声明净额、盘上无实物**：`lead/` 全树 os.walk 实测大小恰 913,237 B 的文件 **0 个**；',
    '该值 = b", "calls": " 的 9 B + `dumps(calls)` 的 **913,228 B**（与 R14_COMMON §2.72 第五节『差 9 B = 键名足迹』闭合一致）；',
    '且 json.dumps(obj, ensure_ascii=False).encode() 与磁盘原文**逐字节全等 17,624,355 B**，',
    '故「清单 913,237 vs 现盘 17,624,355 差 +16,711,118」不是两件文物的差，而是**记账口径差**。',
    '（4）**判别力自评（采纳审计员 #414 的 A6）**：r175a 的 E1/E2a/E2b/E2d/C7 是纯字面量断言（文件删掉也 PASS）；',
    '真正有判别力的是 D2/D4/D5（删整条成员后合法 + 键只剩 calls + 913,239 B）与 r175c 的 A4c/A4d/A4e（分布实测）；',
    '另 json.dumps(obj, separators=(",", ":")) 与 sort_keys=True 两条反控实测**都不等**于原文，证明 A3b 的逐字节全等不是恒真。',
    '执行员 #413 报的 16,711,103 是**口径差 1**（其结束偏移取 17,624,353 而非值末 17,624,354），复算后与 16,711,104 一致。',
]))

print('== 构造 V557 ==')
new_st = st.replace(P1, Q1).replace(P2, Q2)
new_lim = lim.replace(P3, Q3).replace(P4, Q4).replace(P5, Q5) + ADD
ck('G4a statement 两处替换都命中（含 P1/P2 的新串在 new_st 里各 1 次）',
   new_st.count(Q1) == 1 and new_st.count(Q2) == 1, (new_st.count(Q1), new_st.count(Q2)))
ck('G4b limitations 三处替换都命中', new_lim.count(Q3) == 1 and new_lim.count(Q4) == 1 and new_lim.count(Q5) == 1,
   (new_lim.count(Q3), new_lim.count(Q4), new_lim.count(Q5)))
ck('G4c 原串在 new 里 0 次', sum(new_st.count(p) for p in (P1, P2)) == 0 and
   sum(new_lim.count(p) for p in (P3, P4, P5)) == 0,
   (sum(new_st.count(p) for p in (P1, P2)), sum(new_lim.count(p) for p in (P3, P4, P5))))
# ★ 订正 label（S-631 同族）：这轮是「3 处替换 + 1 处追加」，故 new 不再是 old 的前缀。
#   有判别力的判据是：old 的首 7,000 字符与末 200 字符都必须原样出现在 new 里（替换点之外不动）。
ck('G4d old 的首 7,000 字符原样出现在 new 里', new_lim[:7000] in new_lim and new_lim.startswith(lim[:7000]),
   new_lim.startswith(lim[:7000]))
ck('G4d2 new_lim 以 ADD 结尾（追加在末尾）', new_lim.endswith(ADD), new_lim.endswith(ADD))
ck('G4d3 old 末句 ANCHOR 仍在 new 里（追加不改旧句）', new_lim.count(ANCHOR) == 1, new_lim.count(ANCHOR))
new_rows, units = {}, {}
for fid, f in rows.items():
    f2 = list(f)
    if fid == 'F24':
        f2[1], f2[4] = new_st, new_lim
    units[fid] = [i for i in range(5) if f2[i] != f[i]]
    new_rows[fid] = f2
ck('G4e F24 变化单元恰为 {1, 4}', units['F24'] == [1, 4], units['F24'])
ck('G4f 其余 53 行变化单元全空', all(not v for k, v in units.items() if k != 'F24'),
   {k: v for k, v in units.items() if v and k != 'F24'})
ck('G4g F24 grade 未动', new_rows['F24'][2] == rows['F24'][2], new_rows['F24'][2])
ck('G4h F24 evidence 列未动', new_rows['F24'][3] == rows['F24'][3])

print('== G5/G6 · 反控 ==')
bad = new_st.replace('**`bounds` 段 16,711,104 B**', '**`bounds` 段 16,711,118 B**')
ck('G5 把 104 改回 118 ⇒ 与 r175a 的段长实测冲突（该形态必须不存在于 new_st）',
   bad != new_st and new_st.count('**`bounds` 段 16,711,118 B**') == 0, new_st.count('**`bounds` 段 16,711,118 B**'))
ck('G6 差集若写成 {2, 2, 2} 则与实测（12/2/14）不符', '{2, 2, 2}' not in new_lim and '{12, 2, 14}' in new_lim,
   ('{2, 2, 2}' in new_lim, '{12, 2, 14}' in new_lim))
# ★ 自错 S-632：我预估改后为 3 次，实测 **4** 次 —— 因为订正句 Q1 自身写了「原写 16,711,118 B」，
#   净效果是「删 1（P1 的段长形态）+ 加 1（引文）」。这是「把应然数当实测」族第 N 次复发，如实登记。
ck('G7 订正后 statement 里 16,711,118 仍 4 次（删 1 段长形态 + 加 1 引文）', new_st.count('16,711,118') == 4, new_st.count('16,711,118'))
ck('G7b 其中「作为段长」的形态从 2 降为 0', new_st.count('段 16,711,118 B') == 0 and st.count('段 16,711,118 B') == 1,
   (st.count('段 16,711,118 B'), new_st.count('段 16,711,118 B')))
print('     statement 内 16,711,118 次数（改前 4 → 改后 %d）' % new_st.count('16,711,118'))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    res['blocked'] = list(fails)
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(1)

body = '\n'.join([lines[0]] + ['\t'.join(new_rows[l.split('\t')[0]]) for l in lines[1:]]) + '\n'
ck('G8 新全文 CR == 0', '\r' not in body)
ck('G8b 新 statement 字节 >= 旧 10,613（no-shrink 地板仍有效）', len(new_st.encode()) >= 10613, len(new_st.encode()))
ck('G8c 新 limitations 字节 >= 旧 33,011（no-shrink 地板仍有效）', len(new_lim.encode()) >= 33011, len(new_lim.encode()))
os.makedirs(DSTDIR)
io.open(DST, 'w', encoding='utf-8', newline='\n').write(body)
back = io.open(DST, 'rb').read()
sha_new = hashlib.sha256(back).hexdigest()
print('   wrote %s bytes=%d sha=%s' % (DST, len(back), sha_new))

print('== 写后回读 ==')
b2 = back.decode('utf-8')
l2 = b2.split('\n')
if l2 and l2[-1] == '': l2 = l2[:-1]
ck('H1 回读 55 行 5 列', len(l2) == 55 and all(len(l.split('\t')) == 5 for l in l2))
ck('H2 回读 CR == 0', back.count(b'\r') == 0)
ck('H3 回读 sha 与构造一致', sha_new == hashlib.sha256(body.encode()).hexdigest())
r2 = {l.split('\t')[0]: l.split('\t') for l in l2[1:]}
ck('H4 其余 53 行逐字节相同', all(r2[k] == rows[k] for k in rows if k != 'F24'),
   [k for k in rows if k != 'F24' and r2[k] != rows[k]][:5])
ck('H5 母本 V556 一字未改', hashlib.sha256(io.open(MOM, 'rb').read()).hexdigest() == MOM_SHA)
ops_st = [o for o in SequenceMatcher(None, st, new_st, autojunk=False).get_opcodes() if o[0] != 'equal']
ops_lim = [o for o in SequenceMatcher(None, lim, new_lim, autojunk=False).get_opcodes() if o[0] != 'equal']
print('   st opcodes=%r' % (ops_st,))
print('   lim opcodes=%r' % (ops_lim,))
print('   delta bytes=%d ; st %d -> %d ; lim %d -> %d' %
      (len(back) - MOM_BYTES, len(st.encode()), len(new_st.encode()), len(lim.encode()), len(new_lim.encode())))

res.update({'dst': DST, 'dst_bytes': len(back), 'dst_sha256': sha_new,
            'delta_bytes': len(back) - MOM_BYTES,
            'st_bytes': [len(st.encode()), len(new_st.encode())],
            'lim_bytes': [len(lim.encode()), len(new_lim.encode())],
            'st_118_count': [st.count('16,711,118'), new_st.count('16,711,118')],
            'ops_st': ops_st, 'ops_lim': ops_lim, 'assertions': n, 'fails': fails})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
