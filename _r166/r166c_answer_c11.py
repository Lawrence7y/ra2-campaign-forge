#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166c_answer_c11.py —— C11 那 5 条历史 FAIL（id 3, 4, 22, 27, 28）现在到底处于什么状态

背景（R68 起记了 98 轮）：门禁 C11 曾报 5 条 FAIL（id 3/4/22/27/28）。R86 把根因定位成
「窗口表整体错位一轮」并做内存重映射，`0 -> 5` 由 FAIL 变 PASS 的恰是这 5 条。但**改表还是
改行至今不可区分**（R71 §CY9 明写），且 R68/R86 都说明：本轮之前它们是 **fail 态**。

本轮不做裁定、只做一件事：把这 5 条**现盘**的每一条判据分量逐条量出来，并给出四条可失败断言：
  Q1  这 5 行的 col7 现值为「无」还是「有」？（决定它们走 claims-none 还是 claims-recheck 分支）
  Q2  它们的产物里有没有本纪律的自述行（DISC_RECHECK discipline=N）？（R128 判据）
  Q3  它们的校验式现盘是否真跑通过？（R129 判据）
  Q4  它们是否在冻结档 DISC_UNVERIFIABLE.tsv 里？（决定 C11 的冻结分支是否对它们生效）
  Q5  反控：把它们当「有」处理（强制走 verify_recheck_line）会得到什么结论 —— 若为 FAIL，
      则「现在门禁是绿的」这件事**不是**因为它们被修好了，而是因为它们声明不补。

同时把同一套分量对全 31 行跑一遍，给出四桶计数，与门禁 NOTE 行对照。
只读；不修改任何文件。
"""
import io
import json
import os
import re
import subprocess
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
DR = os.path.join(T, 'DISC_RECHECK.tsv')
UN = os.path.join(T, 'DISC_UNVERIFIABLE.tsv')
OUT = os.path.join(R, '_r166/r166c_answer_c11.json')

FAIL = 0
RES = []


def ck(n, c, d=''):
    global FAIL
    ok = bool(c)
    if not ok:
        FAIL += 1
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:400]})
    print(('PASS ' if ok else 'FAIL ') + n + (('  :: ' + str(d)[:320]) if d else ''))


rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n') if l]
hdr, body = rows[0], rows[1:]
ck('C0 DISC_RECHECK 32 行（表头 + 31 数据行）、每行 7 列',
   len(rows) == 32 and all(len(r) == 7 for r in body), (len(rows), len(body)))

frozen = set()
for l in io.open(UN, encoding='utf-8').read().split('\n')[1:]:
    c = l.split('\t')
    if c and c[0].strip().isdigit():
        frozen.add(int(c[0]))

TARGET = [3, 4, 22, 27, 28]
byid = dict((int(r[0]), r) for r in body if r[0].strip().isdigit())

print('\n== 逐条分量（目标 5 条 + 反控 1 条已知「有」的行）==')
detail = {}
for n in TARGET + [1]:
    r = byid[n]
    later = r[6].strip()
    prod = os.path.join(R, r[4].strip().replace('\\', '/'))
    exists = os.path.isfile(prod)
    selflines = []
    if exists:
        try:
            t = io.open(prod, encoding='utf-8', errors='replace').read()
        except OSError:
            t = ''
        for ln in t.splitlines():
            if not ln.startswith('DISC_RECHECK '):
                continue
            m = re.search(r'\bdiscipline=(\d+)\b', ln)
            if m and int(m.group(1)) == n:
                selflines.append(ln[:120])
    detail[n] = {'col7': later, 'claims_yes': later.startswith('有'),
                 'product': r[4].strip(), 'exists': exists,
                 'selflines': len(selflines), 'sample': selflines[:1],
                 'frozen': n in frozen, 'expr': r[5].strip()}
    print('  id=%-3d col7=%-3s claims_yes=%-5s prod_exists=%-5s selflines=%-2d frozen=%-5s expr=%s'
          % (n, later[:2], detail[n]['claims_yes'], exists, len(selflines), n in frozen,
             r[5].strip()[:44]))

print('\n== Q1 这 5 条声明的是「无」还是「有」==')
ck('Q1 5 条全部声明「无」（即走 claims-none 分支，不要求自产出凭证）',
   all(not detail[n]['claims_yes'] for n in TARGET),
   [(n, detail[n]['col7'][:2]) for n in TARGET])
ck('Q1b 反控：id 1 声明「有」（对照组，说明字段解析方向正确）',
   detail[1]['claims_yes'], detail[1]['col7'][:2])

print('\n== Q2 自述行计数（R128 判据：claims-none 行产物里不得有本纪律自述行）==')
ck('Q2 5 条的产物里本纪律自述行全为 0（故 R128 判据对它们不触发）',
   all(detail[n]['selflines'] == 0 for n in TARGET),
   [(n, detail[n]['selflines']) for n in TARGET])

print('\n== Q3 校验式现盘是否真跑通过（R129 判据）==')
sys.path.insert(0, T)
import importlib.util

spec = importlib.util.spec_from_file_location('cd_mod', os.path.join(T, 'check_disc.py'))
# 不 import check_disc（它会跑整门并把 FAIL 打屏）；改为复用它的 run_expr 语义：
# 这里独立重写三支（grep= / grepcount= / rows=），与门禁实现同语义（只在 path/expr 上）。
def run_expr(path, expr):
    ap = os.path.join(R, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False, 'FILE_MISSING'
    head = expr.split(' ')[0]
    cache = {}

    def txt():
        if 'v' not in cache:
            cache['v'] = io.open(ap, encoding='utf-8', errors='replace').read()
        return cache['v']

    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            return len(re.findall(pat, txt(), re.M)) >= 1, 'grep'
        except re.error as e:
            return False, 'BAD_REGEX'
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0:
            return False, 'BAD_GREPCOUNT'
        try:
            return len(re.findall(m0.group(1), txt(), re.M)) == int(m0.group(2)), 'grepcount'
        except re.error:
            return False, 'BAD_REGEX'
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = 0
        hdr_seen = 0
        for ln in io.open(ap, encoding='utf-8', errors='replace'):
            s = ln.strip()
            if s.startswith('DISC_RECHECK '):
                continue
            if hdr_seen == 0:
                hdr_seen = 1
                continue
            n += 1
        return n == int(m3.group(1)), 'rows=%d' % n
    return False, 'OTHER'


for n in TARGET:
    ok, det = run_expr(byid[n][4].strip(), byid[n][5].strip())
    detail[n]['expr_ok'] = ok
    detail[n]['expr_detail'] = det
    print('  id=%-3d expr_ok=%-5s %s' % (n, ok, det))
ck('Q3 5 条的校验式现盘全部真跑通过（故 R129 判据也不触发）',
   all(detail[n]['expr_ok'] for n in TARGET), [(n, detail[n]['expr_detail']) for n in TARGET])

print('\n== Q4 是否在冻结档 ==')
ck('Q4 5 条**都不在**冻结档 DISC_UNVERIFIABLE.tsv（12 个 id 里没有它们）',
   all(n not in frozen for n in TARGET), sorted(frozen))

print('\n== Q5 反控：若把 5 条当「有」处理，verify_recheck_line 会判什么 ==')
sys.path.insert(0, T)
import recheck_verify as V
res5 = {}
for n in TARGET:
    r = list(byid[n])
    ok, det = V.verify_recheck_line(R, r)
    res5[n] = (ok, str(det)[:80])
    print('  id=%-3d verify_ok=%-5s %s' % (n, ok, str(det)[:70]))
ck('Q5 反控成立：把 5 条当「有」处理会全部 FAIL（理由含 line_count=0）'
   ' ⇒ 门禁现绿的原因是它们声明不补，不是它们被修好了',
   all(not v[0] for v in res5.values()) and
   all('line_count' in v[1] or 'no self' in v[1].lower() or 'R1' in v[1] for v in res5.values()),
   res5)

print('\n== 四桶全表对照（与门禁 NOTE 行 C11 col7 machine-check 比）==')
ok_n = none_n = frozen_n = fail_n = 0
for r in body:
    n = int(r[0])
    if r[6].strip().startswith('有'):
        ok_n += 1
    else:
        none_n += 1
frozen_n = len(frozen)
print('  claims-有=%d claims-none=%d frozen=%d' % (ok_n, none_n, frozen_n))
ck('F0 claims-有 == 12 / claims-none == 19 / frozen == 12（与门禁 NOTE 一致）',
   ok_n == 12 and none_n == 19 and frozen_n == 12, (ok_n, none_n, frozen_n))
_r = subprocess.run([sys.executable, os.path.join(T, 'check_disc.py')], cwd=T,
                    capture_output=True, text=True, timeout=600)
_note = [l for l in _r.stdout.splitlines() if 'C11 col7 machine-check' in l]
print('  门禁实跑 exit=%d ; NOTE 行: %s' % (_r.returncode, (_note[0].strip() if _note else 'MISSING')))
ck('F1 门禁实跑 exit 0 且其 C11 NOTE 行写 ok=0 fail=0 frozen-unverifiable=12 claims-none=19',
   _r.returncode == 0 and _note and
   'ok=0 fail=0 frozen-unverifiable=12 claims-none=19' in _note[0],
   (_r.returncode, _note[0].strip() if _note else 'MISSING'))

json.dump({'target': detail, 'frozen': sorted(frozen),
           'claims_yes': ok_n, 'claims_none': none_n,
           'q5_verify': {str(k): [v[0], v[1]] for k, v in res5.items()},
           'asserts': RES, 'fail': FAIL},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), FAIL, OUT))
sys.exit(1 if FAIL else 0)
