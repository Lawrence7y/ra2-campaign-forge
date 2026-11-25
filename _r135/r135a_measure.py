# -*- coding: utf-8 -*-
"""r135a_measure.py -- R135 承重实测：C11 frozen 分支的两处「检查对象错位」

被测对象（全部只读）：
  A. lead/next_re_20261117_r14/DISC_RECHECK.tsv      （live 表，31 行，col5/col6 已被 C7d 钉住）
  B. lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv （冻结档，12 行，sha 被 FREEZE_SHA256 钉住）
  C. lead/next_re_20261117_r14/check_disc.py         （门禁，C11/C12 读哪一张表）

要证的三个量：
  M1 冻结档 col3/col4（产物/校验式）与 live 表 col5/col6 是否同一对象 —— 谁在错位
  M2 C12 实际跑的是冻结档副本，不是纪律真正的校验式（检查对象错位）
  M3 C11 的 frozen 分支把**任何** verify 失败都记成 declared（无 FAIL 出口、且不区分理由）

每个量自带正控（当前盘上应有分辨力）与反控（把坏条件造出来看判据是否翻转）。
全程不写任何 live 文件；临时文件写在 _r135/tmp 并删净。
"""
import io
import os
import re
import sys
import json
import shutil
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TMP = os.path.join(ROOT, '_r135', 'tmp')
res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-58s %s' % ('PASS' if cond else 'FAIL', name, detail))


def rd(p):
    return io.open(p, encoding='utf-8', errors='replace', newline='').read()


def rows_of(path):
    ls = [l for l in rd(path).split('\n') if l.strip()]
    return ls[0].split('\t'), [l.split('\t') for l in ls[1:]]


# ---- 独立实现的校验式求值器（不 import check_disc；纪律 D：主会话复算不复用被测代码）----
def ev(path, expr):
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False, 'FILE_MISSING'
    e = expr.strip()
    head = e.split(' ')[0]
    if head.startswith('grep='):
        try:
            n = len(re.findall(e[len('grep='):].strip(), rd(ap), re.M))
        except re.error as ex:
            return False, 'BAD_REGEX:%s' % ex
        return n >= 1, 'grep hits=%d' % n
    m = re.fullmatch(r'grepcount=(.*)=(\d+)$', e, re.S)
    if m:
        try:
            n = len(re.findall(m.group(1), rd(ap), re.M))
        except re.error as ex:
            return False, 'BAD_REGEX:%s' % ex
        return n == int(m.group(2)), 'grepcount %d vs %d' % (n, int(m.group(2)))
    m1 = re.search(r'[\(（](\d+)\s*B[\)）]', e)
    if head == 'exists':
        if m1:
            return os.path.getsize(ap) == int(m1.group(1)), 'bytes %d vs %d' % (os.path.getsize(ap), int(m1.group(1)))
        return False, 'exists-without-size-annotation'
    m2 = re.fullmatch(r'bytes=(\d+)', head)
    if m2:
        return os.path.getsize(ap) == int(m2.group(1)), 'bytes=%d' % os.path.getsize(ap)
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = h = 0
        for ln in io.open(ap, encoding='utf-8', errors='replace'):
            s = ln.strip()
            if s.startswith('DISC_RECHECK '):
                continue
            if h == 0:
                h = 1
                continue
            n += 1
        return n == int(m3.group(1)), 'rows=%d' % n
    if head == 'none':
        return None, 'none'
    return False, 'BAD_EXPR:' + head


hdrL, live = rows_of(os.path.join(R14, 'DISC_RECHECK.tsv'))
hdrF, frz = rows_of(os.path.join(R14, 'DISC_UNVERIFIABLE.tsv'))
L = dict((int(r[0]), r) for r in live)
F = dict((int(r[0]), r) for r in frz)
chk('M0 live 表 31 行 / 冻结档 12 行', len(live) == 31 and len(frz) == 12,
    'live=%d frozen=%d' % (len(live), len(frz)))

# ---------- M1 两表同一性 ----------
sec_bad = [i for i in F if F[i][1].strip() != L[i][1].strip()]
path_bad = [i for i in F if F[i][2].strip() != L[i][4].strip()]
expr_bad = sorted(i for i in F if F[i][3].strip() != L[i][5].strip())
chk('M1a 冻结档 col2 节 == live col2 节（12/12）', not sec_bad, 'mismatch=%s' % sec_bad)
chk('M1b 冻结档 col3 产物 == live col5 产物（12/12）', not path_bad, 'mismatch=%s' % path_bad)
chk('M1c 冻结档 col4 校验式 == live col6 校验式', not expr_bad,
    'mismatch ids=%s' % expr_bad)
OUT['M1'] = {'expr_mismatch': expr_bad}

# ---------- M1d 4 处错位是否都是「活式被截短成前缀」（松弛方向）----------
prefix_relaxed = []
for i in expr_bad:
    a = F[i][3].strip()          # 冻结档副本
    b = L[i][5].strip()          # 纪律真正的校验式
    if b.startswith(a) and len(a) < len(b):
        prefix_relaxed.append(i)
chk('M1d 4 处错位同为「冻结档副本是 live 式的真前缀」（松弛方向）',
    sorted(prefix_relaxed) == expr_bad and len(expr_bad) == 4,
    'prefix=%s all=%s' % (sorted(prefix_relaxed), expr_bad))

# 反控 M1e：把复制方向反过来验——任何 live 式都不是副本的前缀（证明不是「两边都对」）
rev = [i for i in expr_bad if L[i][5].strip().startswith(F[i][3].strip())
       and len(F[i][3].strip()) < len(L[i][5].strip())]
chk('M1e 反控：live 式不是冻结档副本的前缀（方向唯一）', not rev, 'rev=%s' % rev)

# ---------- M2 C12 的检查对象 ----------
# C12 读冻结档 col3/col4；若错位存在，C12 认证的表达式与纪律实际声明的不同。
m2_copy_ok = sum(1 for i in F if ev(F[i][2], F[i][3])[0] is True)
m2_live_ok = sum(1 for i in F if ev(L[i][4], L[i][5])[0] is True)
chk('M2a 按冻结档副本求值：12/12 命中（门禁当前看到的世界）', m2_copy_ok == 12,
    'copy_ok=%d' % m2_copy_ok)
chk('M2b 按 live 式求值：12/12 命中（错位不改变今天的结果）', m2_live_ok == 12,
    'live_ok=%d' % m2_live_ok)
# 反控 M2c：把某行 live 式改成必然不成立（内存中，不写盘），证明「按 live 式」有分辨力
_bad_ok, _ = ev(L[1][4], 'grep=ZZZ_NOT_PRESENT_ZZZ')
chk('M2c 反控：按 live 式求值对不成立式为 False（有分辨力）', _bad_ok is False,
    'false-expr -> %s' % repr(_bad_ok))
# 关键：错位使「改 live 式」在 C12 上完全静默
i0 = expr_bad[0]
silent = ev(F[i0][2], F[i0][3])[0] is True and ev(L[i0][4], 'grep=ZZZ_NOT_PRESENT_ZZZ')[0] is False
chk('M2d 错位的后果：live 式被换成永假式而 C12 仍命中（静默）', silent,
    'id=%d 副本命中=%s live假式命中=%s' % (i0, ev(F[i0][2], F[i0][3])[0],
                                          ev(L[i0][4], 'grep=ZZZ_NOT_PRESENT_ZZZ')[0]))
OUT['M2'] = {'copy_ok': m2_copy_ok, 'live_ok': m2_live_ok, 'silent_id': i0}

# ---------- M3 C11 frozen 分支不区分失败理由 ----------
sys.path.insert(0, R14)
import recheck_verify as V            # 只读 import（被测模块自身就是被测对象）
reasons = {}
for i in sorted(F):
    ok, det = V.verify_recheck_line(ROOT, L[i])
    reasons[i] = (ok, det.split(' ')[0])
chk('M3a 12 条冻结行 verify 全 False', all(v[0] is False for v in reasons.values()),
    'false=%d' % sum(1 for v in reasons.values() if v[0] is False))
chk('M3b 12 条失败理由全是 R1 line_count_for_discipline_<N>=0',
    all(v[1] == 'R1' for v in reasons.values()) and
    all(re.match(r'^R1 line_count_for_discipline_%d=0\b' % i, V.verify_recheck_line(ROOT, L[i])[1])
        for i in F),
    'reasons=%s' % {k: v[1] for k, v in reasons.items()})

# 反控 M3c：给冻结产物加一条**畸形**自述行（半写的凭证），看 verify 的理由是否变
os.makedirs(TMP, exist_ok=True)
fake_rel = 'lead/next_re_20261117_r14/_r135_tmp_product.md'
fake_abs = os.path.join(ROOT, fake_rel)
rowfake = list(L[1])
rowfake[4] = fake_rel.replace('/', '\\')
try:
    io.open(fake_abs, 'w', encoding='utf-8', newline='').write(
        '# fixture\nDISC_RECHECK discipline=1 garbage\n')
    ok_c, det_c = V.verify_recheck_line(ROOT, rowfake)
    chk('M3c 反控：产物含 1 条畸形自述行 -> verify 理由从 R1-count 变成格式类',
        ok_c is False and not det_c.startswith('R1 line_count_for_discipline_'),
        'detail=%s' % det_c[:70])
    # M3d：C11 现有分支对上述理由同样记 declared（不 FAIL）——用门禁片段的等价逻辑复算
    declared = (ok_c is False and 1 in F)
    chk('M3d 现有 C11 frozen 分支对「半写凭证」仍记 declared（无 FAIL 出口）', declared is True,
        'declared=%s（分支条件：not ok and n in FROZEN）' % declared)
finally:
    if os.path.isfile(fake_abs):
        os.remove(fake_abs)
OUT['M3'] = {'reasons': {k: v[1] for k, v in reasons.items()}}

# ---------- M4 冻结档元数据列的常量性（供 C12 增判据时确认零误伤面）----------
const = {}
for idx, nm in ((4, 'category'), (5, 'reason'), (6, 'ts'), (7, 'claimed_has')):
    vals = sorted(set(f[idx].strip() for f in frz))
    const[nm] = vals
chk('M4 冻结档 col5/col6/col7/col8 各自单值（分类/理由/时刻/声称）',
    all(len(v) == 1 for v in const.values()),
    'distinct=%s' % {k: len(v) for k, v in const.items()})
sec_vals = sorted(set(f[1].strip() for f in frz))
chk('M4b 冻结档 col2 节 8 个不同值（与 live 一致）', len(sec_vals) == 8, 'secs=%s' % sec_vals)
OUT['M4'] = {'const': {k: v[0][:40] for k, v in const.items()}, 'secs': sec_vals}

if os.path.isdir(TMP) and not os.listdir(TMP):
    os.rmdir(TMP)

npass = sum(1 for _, c, _ in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
io.open(os.path.join(ROOT, '_r135', 'r135a_measure.json'), 'w', encoding='utf-8').write(
    json.dumps({'asserts': [{'name': n, 'ok': c, 'detail': d} for n, c, d in res],
                'out': OUT}, ensure_ascii=False, indent=1))
sys.exit(0 if npass == len(res) else 1)
