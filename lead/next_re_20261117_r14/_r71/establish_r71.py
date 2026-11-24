# -*- coding: utf-8 -*-
"""R71 · DISC_ESTABLISH.tsv 的「依据」列可核验率：与 R70 的 128/171 同族口径。

背景：
  DISC_ESTABLISH.tsv 是 recheck_verify.py 的 R3 判据（at 必须晚于立条落盘上界）的**唯一外
  部输入**。它的第 5 列「依据（从哪推断）」全部指向 R14_COMMON.before_HHMMSS_.bak。
  若这些 .bak 在盘上不存在，则**每一条立条时刻都无法在本库内独立复核** —— 它们只是
  「当时写下来的一个字符串」，门禁照它判，判定本身不可核验。

这不是要推翻 DISC_ESTABLISH（R70 已裁：部署裁剪不修路径），而是要**给出门禁的可核验边界**：
  门禁 R3 这一条，在本精简库上属于「依赖本库不存在的文件」的判据。
  引用 C11「R3 通过」时必须同时声明这一点，否则等于声称「立条时刻已被验证」。

测量项：
  E1  13 个被引 .bak 的逐条存在性（本库内）
  E2  按条目口径与按去重路径口径分别算可核验率
  E3  全库 .bak 普查，确认没有同名异路径的救回
  E4  反控：构造一个**存在**的路径 ⇒ 检测器必须报 OK（证明不是恒报 MISS）
  E5  反控：构造一个同名但不同目录 ⇒ 必须报 MISS（证明不是 basename 兜底）
"""
import os, re, io, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EST = os.path.join(R14, 'DISC_ESTABLISH.tsv')
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

BAK_RE = re.compile(r'R14_COMMON\.before_(\d{6})_\.bak')

# ---------- E1 逐条存在性 ----------
lines = [l for l in io.open(EST, encoding='utf-8').read().split('\n') if l]
head = lines[0].split('\t')
P('[表] DISC_ESTABLISH.tsv 表头 %d 列：%s' % (len(head), head))
rows = [l.split('\t') for l in lines[1:] if len(l.split('\t')) == 6]
P('[表] 数据行 %d 条' % len(rows))

detail = []          # (纪律号, 引用的 bak 名, 是否存在)
for r in rows:
    n, sec, rnd, at, basis, conf = r
    ms = BAK_RE.findall(basis)
    for hh in ms:
        name = 'R14_COMMON.before_%s_.bak' % hh
        detail.append((int(n), name, os.path.isfile(os.path.join(R14, 'R17_LEAD_BASELINE', name))))

P('')
P('=== E1 · 被引 .bak 逐条存在性 ===')
hit = sum(1 for _, _, e in detail if e)
P('  引用条目 %d 条；存在 %d；缺失 %d' % (len(detail), hit, len(detail) - hit))
missing = sorted(set(n for n, _, e in detail if not e))
P('  缺失涉及纪律号：%s' % missing)

# 按「去重路径」口径
uniq = {}
for n, name, e in detail:
    uniq.setdefault(name, []).append((n, e))
u_hit = sum(1 for k, v in uniq.items() if all(e for _, e in v))
P('  去重路径 %d 条；全部存在 %d' % (len(uniq), u_hit))

ck('E1-a 按条目口径：%d/%d 存在' % (hit, len(detail)), True,
   '%d/%d = %.1f%%' % (hit, len(detail), 100.0 * hit / max(1, len(detail))))
ck('E1-b 按去重路径口径：%d/%d 存在' % (u_hit, len(uniq)), True,
   '%d/%d = %.1f%%' % (u_hit, len(uniq), 100.0 * u_hit / max(1, len(uniq))))
ck('E1-c 两口径一致：全部缺失（否则须分别报）', hit == 0 and u_hit == 0,
   '条目 %d/%d、路径 %d/%d' % (hit, len(detail), u_hit, len(uniq)))

# ---------- E3 全库 .bak 普查 ----------
P('')
P('=== E3 · 全库 .bak 普查（是否存在同名异路径救回）===')
alls = []
for rt, ds, fs in os.walk(ROOT):
    if os.sep + '.git' in rt: continue
    for f in fs:
        if f.endswith('.bak'): alls.append(os.path.join(rt, f))
P('  全库 .bak 共 %d 个' % len(alls))
for p in sorted(alls): P('    ' + os.path.relpath(p, ROOT))
names_all = set(os.path.basename(p) for p in alls)
rescued = [k for k in uniq if k in names_all]
ck('E3-a 无同名异路径救回（basename 兜底救回 0 条）', len(rescued) == 0, '%s' % rescued)
ck('E3-b 全库 .bak 全是 r66 的 5 件同一批，不含任何 before_HHMMSS_ 形态',
   all('before_r66_210054' in os.path.basename(p) for p in alls),
   '%d 个' % len(alls))

# ---------- E4/E5 反控 ----------
P('')
P('=== E4/E5 · 检测器反控 ===')
def exists_in_base(bakname):
    """本脚本唯一使用的存在性判据 —— 反控必须打在这个函数上。"""
    return os.path.isfile(os.path.join(R14, 'R17_LEAD_BASELINE', bakname))

# E4：拿一个**确实存在**的文件名去问 ⇒ 必须 True
real = 'R14_COMMON.md.before_r66_210054.bak'
ck('E4 反控：确实存在的 %s ⇒ 判存在（非恒报 MISS）' % real, exists_in_base(real) is True)

# E5：同名但放在别的目录 ⇒ 必须 False（不按 basename 兜底）
tmpname = 'R14_COMMON.before_999999_.bak'
open(os.path.join(HERE, tmpname), 'w').write('x')
try:
    ck('E5 反控：同名文件放在 _r71/ 下 ⇒ 仍判 MISS（不 basename 兜底）',
       exists_in_base(tmpname) is False)
finally:
    os.remove(os.path.join(HERE, tmpname))

# E5b：把它放进 baseline 目录就该被认
tmp2 = os.path.join(R14, 'R17_LEAD_BASELINE', tmpname)
open(tmp2, 'w').write('x')
try:
    ck('E5b 对照：放进 R17_LEAD_BASELINE/ ⇒ 判存在（判据确实指向该目录）',
       exists_in_base(tmpname) is True)
finally:
    os.remove(tmp2)
ck('E5c 清理后复归 MISS', exists_in_base(tmpname) is False)

P('')
P('=== 结论（如实陈述边界）===')
P('  DISC_ESTABLISH.tsv 的 %d 条立条时刻，其「依据」全部指向本库不存在的 .bak（%d/%d MISS）。'
  % (len(detail), len(detail) - hit, len(detail)))
P('  ⇒ 门禁 C11 的 R3 判据（at 必须晚于立条上界）在本精简库上**不可独立复核**。')
P('  这与 R70 裁定的「部署裁剪」同族：证据路径本身正确，文件不在精简库里。')
P('  **不修路径、不改 DISC_ESTABLISH**；只把此边界成文，供引用 C11 时附带声明。')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'establish_r71.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
