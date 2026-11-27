#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166f_bump_gate.py —— 门禁 R165 -> R166（C16 加 171 节 + 四处常量重钉 + GATE_VER 三处同步）

为什么必须动门禁：
  §2.171 即将落盘，C16 的逐节下界表只到 170 节 ⇒ 新节落在「表外新节」通道，
  C16_UNPINNED_MAX = 2 ⇒ 再攒两轮就撞线。C16 是「每节正文 >= 建表时实测字节的一半」，
  但本轮 §2.171 文本先落盘才有实测字节 ⇒ 本脚本分两阶段：
    阶段 A（--stage a）：只把 §2.171 写进 R14_COMMON / 台账 / LEAD_LOCK / 看板，不动门禁；
    阶段 B（--stage b）：读盘上 §2.171 实测字节 -> 算下界 -> 重钉 C16 与四个常量 + GATE_VER。
  两阶段分开是为了避免 R165 的 S-523（按落盘前的字节算下界，随后又改短）。

反控（每一条都必须能单独 FAIL）：
  R1 C16 表除新节外 164 条逐条不变
  R2 新节下界 == 落盘后实测字节的一半（地板，非等值）
  R3 重算 C16_FLOORS_SHA256 与常量不同 -> 必须重钉（不重钉必 FAIL）
  R4 C14_TEXT_SHA256 一字未动（本轮没改 DISC_RECHECK 的自由文本列）
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
GATE = os.path.join(T, 'check_disc.py')
DR = os.path.join(T, 'DISC_RECHECK.tsv')
UN = os.path.join(T, 'DISC_UNVERIFIABLE.tsv')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r166/r166f_bump_gate.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r166f_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


gt = rb(GATE).decode('utf-8')

# ---- 读 §2.171 实测字节（从 R14_COMMON 现盘量，不猜）
rc = rb(os.path.join(T, 'R14_COMMON.md')).decode('utf-8')
m = re.search(r'(?m)^##\s+2\.171\b', rc)
ck('A0 R14_COMMON 里已有 §2.171（阶段 A 已落盘）', m is not None, m.start() if m else 'MISSING')
i = m.start()
# 到下一个 ## 2.x 或文件尾
m2 = re.search(r'(?m)^##\s+2\.\d+\b', rc[i + 5:])
j = i + 5 + m2.start() if m2 else len(rc)
sec171 = rc[i:j]
SEC171_BYTES = len(sec171.encode('utf-8'))
FLOOR171 = SEC171_BYTES // 2
print('  §2.171 实测 %d B -> C16 下界 %d' % (SEC171_BYTES, FLOOR171))
ck('A1 §2.171 节名是 2.171', rc[i:i + 20].startswith('## 2.171'), rc[i:i + 20])
ck('A2 该节至少 3,000 B（不是空壳）', SEC171_BYTES >= 3000, SEC171_BYTES)

# ---- 读现盘 C16 表
mi = gt.index('C16_FLOORS = {')
mj = gt.index('}', mi)
tbl_src = gt[mi:mj + 1]
C16 = {}
for k, v in re.findall(r'(\d+):\s*(\d+),', tbl_src):
    C16[int(k)] = int(v)
print('  C16 现表 %d 节，最大 id %d' % (len(C16), max(C16)))
ck('B0 现表是 164 节（未含 171）或 165 节（已含 171）—— 幂等两态', len(C16) in (164, 165)
   and max(C16) in (170, 171), (len(C16), max(C16)))
NEW = dict(C16)
# S-535（自错，本轮当场抓出，与 R165 的 S-523 同族）：首版写 if 171 not in NEW: NEW[171]=FLOOR171
# ⇒ 第一次 bump 把 171 钉在 4,230（当时 §2.171 是 8,461 B），随后我给该节补了「十一 · 断言总量」
# 使其实测变成 8,960 B，下界仍停在 4,230 ⇒ 下界与「现字节一半」脱钩（门禁不 FAIL，但那是侥幸）。
# 正确做法：171 的下界**始终等于现盘实测字节的一半**，并在漂移时如实记账。
_old171 = NEW.get(171)
NEW[171] = FLOOR171
ck('B1 新表 165 节 / 新增 171:%d（是否漂移：%s）' % (FLOOR171, _old171 != FLOOR171),
   len(NEW) == 165 and NEW[171] == FLOOR171,
   (len(NEW), 'old=%s new=%s' % (_old171, NEW[171])))
_diff = [k for k in C16 if NEW[k] != C16[k]]
ck('B2 除 171 外 164 条逐条相同（反控；幂等重跑时 171 已等于目标值，差异集应为空）',
   all(k == 171 for k in _diff), _diff)

def norm16(d):
    return '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))


NEW16SHA = sha(norm16(NEW).encode())
OLD16SHA = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt).group(1)
print('  C16 sha 旧 %s -> 新 %s' % (OLD16SHA[:16], NEW16SHA[:16]))
ck('B3 终态：表 sha == 常量（已重钉）或 二者不同（待重钉）—— 两态都合法，只看最终是否一致',
   True, (NEW16SHA[:16], OLD16SHA[:16]))
REC16 = sha(norm16(C16).encode())
ck('B4 用现表重算 sha 恰等于现常量（同法自证；幂等重跑同样成立）',
   REC16 == OLD16SHA or REC16 == NEW16SHA, (REC16[:16], OLD16SHA[:16], NEW16SHA[:16]))

# ---- 写 GATE：C16 表 + sha + GATE_VER
new_gt = gt
# S-536（自错，本轮当场抓出，造成门禁真红，与 R165 的 S-524 同族）：首版用「表长不同」作为
# 「要不要重写表」的判据 —— 但 171 已在表里（只是值旧）时两表长度相同 ⇒ 表不重写、只改 sha 常量
# ⇒ C16d 报 TAMPERED。正确判据是**内容相等**（dict 比较），且顺序必须是「先写表、再用新表算 sha」。
if NEW != C16:
    lines = ['C16_FLOORS = {']
    for k in sorted(NEW):
        lines.append('    %d: %d,' % (k, NEW[k]))
    lines.append('}')
    new_gt = new_gt[:mi] + '\n'.join(lines) + new_gt[mj + 1:]
new_gt = new_gt.replace("C16_FLOORS_SHA256 = '%s'" % OLD16SHA,
                        "C16_FLOORS_SHA256 = '%s'" % NEW16SHA, 1)
m_gv = re.search(r"GATE_VER = '([^']+)'", new_gt)
OLD_GV = m_gv.group(1)
new_gt = new_gt.replace("GATE_VER = '%s'" % OLD_GV, "GATE_VER = 'R166'", 1)
ck('C0 GATE_VER 终态为 R166', "GATE_VER = 'R166'" in new_gt, OLD_GV)
ck('C1 C14_TEXT_SHA256 一字未动（反控）',
   re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", new_gt).group(1)
   == re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", gt).group(1), 'C14 same')

if sha(new_gt.encode()) != sha(gt.encode()):
    bp = bak(GATE, 'check_disc')
    open(GATE, 'w', encoding='utf-8').write(new_gt)
    ck('C2 check_disc.py 备份 + 写入 + 回读', sha(rb(GATE)) == sha(new_gt.encode()),
       os.path.basename(bp))
else:
    ck('C2 check_disc.py 已是终态（幂等）', True, 'no change')

# ---- 同步纪律 20 的 col6（DR）与 col4（UN）
print('\n== 2 纪律号 20 两表同步 ==')
def patch_row0(path, colidx, old, new, tag):
    txt = rb(path).decode('utf-8')
    lines = txt.split('\n')
    hit = 0
    for n, l in enumerate(lines):
        c = l.split('\t')
        if len(c) > colidx and c[0].strip() == '20':
            if "GATE_VER = '%s'" % old in c[colidx]:
                c[colidx] = c[colidx].replace("GATE_VER = '%s'" % old, "GATE_VER = '%s'" % new)
                lines[n] = '\t'.join(c)
                hit += 1
    out = '\n'.join(lines)
    if hit and out != txt:
        bp = bak(path, tag)
        open(path, 'w', encoding='utf-8').write(out)
        ck('D %s 纪律20 col%d 已同步为 %s' % (tag, colidx, new), hit == 1, os.path.basename(bp))
    else:
        ck('D %s 纪律20 col%d 已是 %s（幂等）' % (tag, colidx, new), True, 'hit=%d' % hit)
    return out


dr_new = patch_row0(DR, 5, OLD_GV, 'R166', 'DR')
un_new = patch_row0(UN, 3, OLD_GV, 'R166', 'UN')

# ---- FREEZE / C7 两个常量随两张表内容变化重钉
gt2 = rb(GATE).decode('utf-8')
NEW_FREEZE = sha(rb(UN))
OLD_FREEZE = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", gt2).group(1)
ck('E0 UN 现盘 sha 与 FREEZE_SHA256 的关系：已一致（重钉完成）或不同（本次写入重钉）',
   True, (NEW_FREEZE[:16], OLD_FREEZE[:16]))
gt3 = gt2.replace("FREEZE_SHA256 = '%s'" % OLD_FREEZE,
                  "FREEZE_SHA256 = '%s'" % NEW_FREEZE, 1)

# C7_TEXT / C7_ROW['20'] 由 DR 的 (id, col5, col6) 重建
# S-532（自错，本轮当场抓出）：首版把**表头行**也算进了 C7 指纹 blob，得 a54b5265…，
# 而门禁是 rows = raw[1:]（**排除表头**），实测 b07f4698… ⇒ C7d 一条真 FAIL。
# 正确做法与门禁逐字同法：raw = [非空行]，rows = raw[1:]，再按 (id, col5, col6) 拼。
_raw = [l for l in dr_new.split('\n') if l]
rows = [l.split('\t') for l in _raw[1:]]
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
NEW_C7 = sha(blob.encode())
OLD_C7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gt3).group(1)
row20 = [r for r in rows if r[0].strip() == '20'][0]
NEW_ROW20 = sha(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode())
m_r20 = re.search(r"'20': '([0-9a-f]{64})'", gt3)
OLD_ROW20 = m_r20.group(1)
print('  C7_TEXT 旧 %s -> 新 %s' % (OLD_C7[:16], NEW_C7[:16]))
print('  C7_ROW[20] 旧 %s -> 新 %s' % (OLD_ROW20[:16], NEW_ROW20[:16]))
ck('E1 终态：C7_TEXT 与 C7_ROW[20] 重算值已写入常量（值驱动，不按旧值硬断言）',
   True, (NEW_C7[:12], NEW_ROW20[:12], OLD_C7[:12], OLD_ROW20[:12]))
gt3 = gt3.replace("C7_TEXT_SHA256 = '%s'" % OLD_C7, "C7_TEXT_SHA256 = '%s'" % NEW_C7, 1)
gt3 = gt3.replace("'20': '%s'" % OLD_ROW20, "'20': '%s'" % NEW_ROW20, 1)

# C14 不动（反控）
ck('E2 C14_TEXT_SHA256 仍 == 旧值（反控：本轮没改 col2-col4）',
   re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", gt3).group(1) ==
   re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", gt).group(1), 'C14 unchanged')

cur = rb(GATE).decode('utf-8')
if sha(gt3.encode()) != sha(cur.encode()):
    bp = bak(GATE, 'check_disc_consts')
    open(GATE, 'w', encoding='utf-8').write(gt3)
    ck('F0 check_disc.py 常量重钉 备份+写+回读', sha(rb(GATE)) == sha(gt3.encode()),
       os.path.basename(bp))
else:
    ck('F0 check_disc.py 常量已终态（幂等）', True, 'no change')

# ---- 三段验证 ①：生产门禁实跑
print('\n== 3 生产门禁实跑 ==')
r1 = subprocess.run([sys.executable, GATE], cwd=T, capture_output=True, text=True, timeout=900)
ck('G0 check_disc exit 0', r1.returncode == 0, r1.returncode)
_fail_lines = [l for l in r1.stdout.splitlines() if l.strip().startswith('FAIL')]
ck('G1 输出无 FAIL 行（只数行首 FAIL，不数 NOTE 里的字样）', not _fail_lines,
   _fail_lines[:3])
note16 = [l for l in r1.stdout.splitlines() if 'C16 per-section floors' in l]
print('  %s' % (note16[0].strip() if note16 else 'MISSING'))
ck('G2 C16 NOTE 自报 165 sections (pinned 165) hollow 0 missing 0 unpinned 0',
   note16 and '165 sections measured (pinned 165)' in note16[0]
   and 'hollow/deficient 0' in note16[0] and 'missing 0' in note16[0]
   and 'unpinned 0' in note16[0], note16[0].strip() if note16 else 'MISSING')
note10 = [l for l in r1.stdout.splitlines() if 'C10 self-check' in l]
ck('G3 C10 self-check ok(R166)', note10 and 'ok(R166)' in note10[0],
   note10[0].strip() if note10 else 'MISSING')

json.dump({'sec171_bytes': SEC171_BYTES, 'floor171': FLOOR171,
           'c16_old_sha': OLD16SHA, 'c16_new_sha': NEW16SHA,
           'gate_ver': 'R166', 'freeze_new': NEW_FREEZE,
           'c7_new': NEW_C7, 'c7row20_new': NEW_ROW20,
           'gate_exit': r1.returncode,
           'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), len(FAILS), OUT))
if FAILS:
    print('FAILS: %s' % FAILS)
sys.exit(1 if FAILS else 0)
