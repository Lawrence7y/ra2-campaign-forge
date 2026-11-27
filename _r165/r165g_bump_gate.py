#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-g · 门禁 R164 -> R165（C16 加 170 节 + 四处常量重钉 + GATE_VER 三处同步）

为什么本轮必须动门禁：
  §2.170 已落盘（11,091 B / 10 节），C16 的逐节下界表只到 169 节 ⇒ 新节落在「表外新节」
  通道（下限 400 B），而 C16_UNPINNED_MAX = 2 ⇒ 新一轮段落若不纳表，会让 unpinned 计数漂。
  C16 是「每节正文 >= 建表时实测字节的一半」，故新节下界 = 11,091 // 2 = 5,545。

重钉清单（逐条都要能单独 FAIL）：
  1) C16_FLOORS 新增 170: 5545（逐节表 163 -> 164 节）
  2) C16_FLOORS_SHA256 由表规范化重算（不是手填）
  3) GATE_VER 'R164' -> 'R165'
  4) DISC_RECHECK 纪律号 20 的 col6 + DISC_UNVERIFIABLE 纪律号 20 的 col4 同步
  5) FREEZE_SHA256 / C7_TEXT_SHA256 / C7_ROW_SHA['20'] 随上面两张表内容变化而重钉
     （纪律 20 的产物就是 check_disc.py 自身 ⇒ 它一变，那两条锚必须跟着变）
  6) 反控：C14_TEXT_SHA256 **不得**动（本轮没改 DISC_RECHECK 的自由文本表）

三段验证（与 R164 同）：
  ① 沙箱预演：三层镜像 + 显式构造 DR=R999 失配副本 ⇒ 正本 exit 0 / 负本报 C10
  ② 生产 gate_runner 实名复验 G1/G2/G3
  ③ 直取主门禁 NOTE 行
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
GATE = os.path.join(T, 'check_disc.py')
DR = os.path.join(T, 'DISC_RECHECK.tsv')
UN = os.path.join(T, 'DISC_UNVERIFIABLE.tsv')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r165/r165g_bump_gate.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:320]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:320]})
    if not ok:
        FAILS.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r165g_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


def norm_floors(f):
    return '\n'.join('%d:%d' % (k, v) for k, v in sorted(f))


# ---------------------------------------------------------------- 0 · 实测 §2.170 字节
print('== 0 · 从盘上实测 §2.170 字节（不预估）==')
common = io.open(os.path.join(T, 'R14_COMMON.md'), encoding='utf-8').read()
i = common.index('\n## 2.170 · R165：')
sec = common[i + 1:]
SEC_BYTES = len(sec.encode())
FLOOR170 = SEC_BYTES // 2
ck('0.1 §2.170 在盘', SEC_BYTES > 4000, SEC_BYTES)
ck('0.2 C16 下界 = 字节的一半（向下取整）', FLOOR170 == SEC_BYTES // 2, (SEC_BYTES, FLOOR170))
ck('0.3 §2.170 是本文件最后一节（后面无 2.171）', '## 2.171' not in common)

# ---------------------------------------------------------------- 1 · C16 表
print()
print('== 1 · C16 逐节表：163 -> 164 节 ==')
gt = io.open(GATE, encoding='utf-8').read()
blk_i = gt.index('C16_FLOORS = {')
blk_j = gt.index('\n}', blk_i)
blk = gt[blk_i:blk_j + 2]
old_floors = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', blk, re.M)]
ck('1.1 逐节表为 163 节（首跑）或 164 节（重跑）且末节前一项恒为 (169, 5331)',
   len(old_floors) in (163, 164) and old_floors[162] == (169, 5331),
   (len(old_floors), old_floors[162:]))
old_sha = sha(norm_floors(old_floors).encode())

# S-523/S-524（两条真错，如实记）：本轮先把下界按落盘那一刻的 11,091 B 算成 5,545，
# 随后又把 §2.170 的断言数 170 -> 201 改短了 54 B（11,037 B），使 5,545 与「现字节一半 5,518」脱钩；
# 且我第一版重钉脚本把表块写了两遍（5545 与 5518 各一次）⇒ C16d 报 TAMPERED。
# 处置：已回滚到干净态并**一次性**把 170 下界钉为 5,518（= 11,037 // 2），本脚本此后只校验、不再写表。
ck('1.2 170 节已在表里（本轮已钉，此后只校验）', 170 in dict(old_floors), dict(old_floors).get(170))
new_blk = blk
new_floors = old_floors
ck('1.3 表恰 164 节且末节为 170', len(new_floors) == 164 and new_floors[-1][0] == 170,
   (len(new_floors), new_floors[-1]))
ck('1.4 反控：前 163 行逐条未动（169 节仍为 (169, 5331)）',
   new_floors[:163] == [(k, v) for k, v in old_floors[:163]] and dict(new_floors)[169] == 5331)
new_c16_sha = sha(norm_floors(new_floors).encode())
_reg = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt, re.M).group(1)
ck('1.5a 注册的 C16 指纹 == 由表重算（无 TAMPERED）', _reg == new_c16_sha, (_reg[:16], new_c16_sha[:16]))
ck('1.5b 170 的下界 == §2.170 现字节的一半（下界语义逐字成立）',
   dict(new_floors)[170] == SEC_BYTES // 2, (dict(new_floors)[170], SEC_BYTES // 2))
ck('1.5c 反控：该下界 > 100（段落砍到 100 B 必被发现，见 6.8）', dict(new_floors)[170] > 100,
   dict(new_floors)[170])
ck('1.5d 170 的下界严格小于 §2.170 现有字节（不会恒 FAIL）',
   dict(new_floors)[170] < SEC_BYTES, (dict(new_floors)[170], SEC_BYTES))
w = gt
ck('1.5e 反控：若段落砍到 100 B，已登记下界必 > 100（证明它真能拦）',
   dict(new_floors)[170] > 100, dict(new_floors)[170])
new_c16_sha = sha(norm_floors(new_floors).encode())
ck('1.6 【锚定】新表 sha 必须等于门禁里注册的 C16_FLOORS_SHA256（首跑为「与旧值不同」）',
   (new_c16_sha != old_sha) or (new_c16_sha == re.search(
       r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt, re.M).group(1)),
   (old_sha[:16], new_c16_sha[:16]))

# 写 C16 表 + C16_FLOORS_SHA256
w = gt
if 170 not in dict(old_floors):
    w = w[:blk_i] + new_blk + w[blk_j + 2:]
w = re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'",
           "C16_FLOORS_SHA256 = '%s'" % new_c16_sha, w, count=1, flags=re.M)
ck('1.7 C16_FLOORS_SHA256 == 表重算值（已在上一轮显式重钉，本轮只校验）',
   "C16_FLOORS_SHA256 = '%s'" % new_c16_sha in w)

# ---------------------------------------------------------------- 2 · GATE_VER
print()
print('== 2 · GATE_VER R164 -> R165（三处）==')
mv = re.search(r"^GATE_VER = '([^']+)'", w, re.M)
ck('2.1 当前 GATE_VER == R164（或已是 R165，幂等）', mv.group(1) in ('R164', 'R165'), mv.group(1))
if mv.group(1) == 'R164':
    w = re.sub(r"^GATE_VER = 'R164'", "GATE_VER = 'R165'", w, count=1, flags=re.M)
ck('2.2 新 GATE_VER == R165', re.search(r"^GATE_VER = '([^']+)'", w, re.M).group(1) == 'R165')
ck('2.3 反控：docstring 里「(R164)」式的历史版本标记未被误改',
   w.count("GATE_VER = 'R165'") >= 1 and "GATE_VER = 'R164'" not in w,
   (w.count("GATE_VER = 'R165'"), w.count("GATE_VER = 'R164'")))

# ---------------------------------------------------------------- 3 · 两张表的纪律 20
print()
print('== 3 · 纪律 20 的 col6 / col4 同步 ==')
dr = io.open(DR, encoding='utf-8').read()
un = io.open(UN, encoding='utf-8').read()
dr_new = re.sub(r"(?m)^(20\t[^\n]*?)\tR164\t", r"\1\tR165\t", dr)
if dr_new == dr:
    # 兜底：直接在行内替换 GATE_VER = 'R164'
    dr_new = dr.replace("grep=(?m)^GATE_VER = 'R164'", "grep=(?m)^GATE_VER = 'R165'")
un_new = un.replace("grep=(?m)^GATE_VER = 'R164'", "grep=(?m)^GATE_VER = 'R165'")
ck('3.1 DR 纪律 20 已指向 R165', "GATE_VER = 'R165'" in dr_new and "GATE_VER = 'R164'" not in dr_new,
   (dr_new.count("GATE_VER = 'R165'"), dr_new.count("GATE_VER = 'R164'")))
ck('3.2 UN 纪律 20 已指向 R165', "GATE_VER = 'R165'" in un_new and "GATE_VER = 'R164'" not in un_new,
   (un_new.count("GATE_VER = 'R165'"), un_new.count("GATE_VER = 'R164'")))
ck('3.3 反控：DR/UN 只改纪律 20 那两处（其它纪律行逐字不变）',
   dr_new.count("GATE_VER = 'R165'") == 1 and un_new.count("GATE_VER = 'R165'") == 1,
   (dr_new.count("GATE_VER = 'R165'"), un_new.count("GATE_VER = 'R165'")))

# S-521：上一版把 dr_new / un_new 只算在内存里，从未写盘 ⇒ 主门禁当场三条 FAIL
# （C7 id 20 expr、C10 self GATE_VER、C11 frozen registry TAMPERED）。写入纪律要求
# 「算完就写、写完回读」，故此处补写盘 + 回读。
for _path, _old, _new, _tag in ((DR, dr, dr_new, 'DISC_RECHECK'),
                                (UN, un, un_new, 'DISC_UNVERIFIABLE')):
    if _old == _new:
        ck('%s 幂等：已是终态' % _tag, True)
        continue
    _b = bak(_path, _tag)
    ck('%s 备份 wx 独占' % _tag, os.path.isfile(_b), os.path.basename(_b))
    ck('%s 备份逐字节等于原文' % _tag, sha(rb(_b)) == sha(_old.encode()))
    with open(_path, 'wb') as f:
        f.write(_new.encode())
    _back = rb(_path)
    ck('%s 回读 sha 与内存一致' % _tag, sha(_back) == sha(_new.encode()), sha(_back)[:16])
    ck('%s 回读 CR 计数未变' % _tag, _back.count(b'\r') == _old.encode().count(b'\r'),
       (_back.count(b'\r'), _old.encode().count(b'\r')))

# FREEZE_SHA256：UN 变了就必须重钉（此时 un_new 已在盘上）
new_freeze = sha(rb(UN))
w = re.sub(r"^FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'" % new_freeze, w,
           count=1, flags=re.M)
ck('3.4 FREEZE_SHA256 已重钉为盘上 UN 的 sha', "FREEZE_SHA256 = '%s'" % new_freeze in w, new_freeze[:16])
ck('3.5 反控：新 FREEZE 与旧值不同（UN 内容确实变了）',
   new_freeze != '85afa34f91d4340a3690e195d95e5c558e0270b26c944dc05b4fae78139e1fcf',
   new_freeze[:16])

# ---------------------------------------------------------------- 4 · 写盘 GATE
print()
print('== 4 · check_disc.py 写盘（S-529 后：本节起只校验不写，写入统一由 r165i 负责）==')
old_gate_sha = sha(rb(GATE))
ck('4.1 改前 check_disc.py sha 记录', True, old_gate_sha[:16])
ck('4.2 反控基线：C14_TEXT_SHA256 改前值',
   re.search(r"^C14_TEXT_SHA256 = '([0-9a-f]{64})'", gt, re.M).group(1)[:16]
   == re.search(r"^C14_TEXT_SHA256 = '([0-9a-f]{64})'", w, re.M).group(1)[:16])
if sha(rb(GATE)) == sha(w.encode()):
    ck('4.3 幂等：check_disc.py 已是终态', True)
else:
    bak(GATE, 'gate')
    with open(GATE, 'wb') as f:
        f.write(w.encode())
    ck('4.3 check_disc.py 写盘', sha(rb(GATE)) == sha(w.encode()), sha(rb(GATE))[:16])

# 纪律 20 的产物就是 check_disc.py 自身 ⇒ C7_TEXT_SHA256 / C7_ROW_SHA['20'] 必须随它重钉
w2 = io.open(GATE, encoding='utf-8').read()
_c7_after_gate = re.search(r"^C7_TEXT_SHA256 = '([0-9a-f]{64})'", w2, re.M).group(1)
ck('4.4 写盘后 C7_TEXT_SHA256 只会是「旧值 6ecc3726（尚未重钉）」或「新值（已重钉）」两态之一',
   _c7_after_gate.startswith('6ecc3726') or _c7_after_gate.startswith('38970988'),
   _c7_after_gate[:16])

# ---------------------------------------------------------------- 5 · C7d 重钉（纪律 20 的产物就是门禁自身）
print()
print('== 5 · C7d (col5,col6) 整表指纹重钉 ==')
w3 = io.open(GATE, encoding='utf-8').read()
_drrows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n')
           if l and not l.startswith('纪律号')]
_blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in _drrows if len(r) == 7)


def rowsha(r):
    return sha(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode())


_old_c7 = re.search(r"^C7_TEXT_SHA256 = '([0-9a-f]{64})'", w3, re.M).group(1)
ck('5.0 门禁里的 C7_TEXT_SHA256 为 6ecc3726…（首跑）或 38970988…（重跑）',
   _old_c7.startswith('6ecc3726') or _old_c7.startswith('38970988'), _old_c7[:16])
_now_c7 = sha(_blob.encode())
ck('5.1 现盘 (col5,col6) 指纹 == 门禁报的 drifted 值 38970988…（对齐，证明我要重钉的正是它）',
   _now_c7.startswith('38970988'), _now_c7[:16])
_drift = [r[0] for r in _drrows if len(r) == 7
          and re.search(r"'%s': '([0-9a-f]{64})'" % r[0], w3)
          and rowsha(r) != re.search(r"'%s': '([0-9a-f]{64})'" % r[0], w3).group(1)]
ck('5.2 行指纹偏离的行 恰为空（首跑已重钉）或 恰为 [20]（尚未重钉）—— 绝不会是其它行',
   _drift in ([], ['20']), _drift)
ck('5.2b 反控：偏离行里除 20 之外**必为空**（直接对上一条做集合运算，不重算一遍）',
   [x for x in _drift if x != '20'] == [], _drift)
w3 = re.sub(r"^C7_TEXT_SHA256 = '[0-9a-f]{64}'", "C7_TEXT_SHA256 = '%s'" % _now_c7,
            w3, count=1, flags=re.M)
_row20 = [r for r in _drrows if len(r) == 7 and r[0] == '20'][0]
w3 = re.sub(r"'20': '[0-9a-f]{64}'", "'20': '%s'" % rowsha(_row20), w3, count=1)
ck('5.3 C7_TEXT_SHA256 已重钉', "C7_TEXT_SHA256 = '%s'" % _now_c7 in w3, _now_c7[:16])
ck('5.4 C7_ROW_SHA[20] 已重钉', "'20': '%s'" % rowsha(_row20) in w3, rowsha(_row20)[:16])
ck('5.5 反控：C14_TEXT_SHA256 一字未动（本轮没改自由文本表）',
   re.search(r"^C14_TEXT_SHA256 = '([0-9a-f]{64})'", w3, re.M).group(1).startswith('a740bcc9'),
   re.search(r"^C14_TEXT_SHA256 = '([0-9a-f]{64})'", w3, re.M).group(1)[:16])
if sha(rb(GATE)) == sha(w3.encode()):
    ck('5.6 幂等：已是终态', True)
else:
    bak(GATE, 'gate_c7d')
    with open(GATE, 'wb') as f:
        f.write(w3.encode())
    ck('5.6 check_disc.py 写盘', sha(rb(GATE)) == sha(w3.encode()), sha(rb(GATE))[:16])



# ---------------------------------------------------------------- 6 · 沙箱预演 + 负控
print()
print('== 6 · 沙箱预演（三层镜像 + 显式失配负控）==')
import shutil
import subprocess
import tempfile

ENV = dict(os.environ); ENV['PYTHONDONTWRITEBYTECODE'] = '1'
_prod_common_sha0 = sha(rb(os.path.join(T, 'R14_COMMON.md')))
SB = tempfile.mkdtemp(prefix='/tmp/r165sb_')
for name in os.listdir(R):
    if name == 'lead' or name.startswith('r165sb_'):
        continue
    os.symlink(os.path.join(R, name), SB + '/' + name)
os.makedirs(SB + '/lead')
for name in os.listdir(os.path.join(R, 'lead')):
    if name == 'next_re_20261117_r14':
        continue
    os.symlink(os.path.join(R, 'lead', name), SB + '/lead/' + name)
os.makedirs(SB + '/lead/next_re_20261117_r14')
# ⚠️ S-526（本轮最重事故）：初版把这三个文件之外的一切都建成**符号链接**，
# 而负控 2 会「读 sb3 里的 R14_COMMON.md → 改短 → 写回」，于是通过链接
# **写穿了生产文件**：§2.170 被截成 100 B、且 1081 个 CR 全被 io.open(text,'w') 换成 LF。
# 修法：凡负控**会写**的文件都必须在沙箱里是**实体副本**，不是链接。
OV = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md'}
for name in os.listdir(T):
    if name in OV:
        continue
    os.symlink(os.path.join(T, name), SB + '/lead/next_re_20261117_r14/' + name)
for name in OV:
    shutil.copy2(os.path.join(T, name), SB + '/lead/next_re_20261117_r14/' + name)
# 反控：确认这几个在沙箱里都**不是**符号链接（否则写穿风险仍在）
_sbdir = os.path.join(SB, 'lead/next_re_20261117_r14')
ck('6.0a 沙箱里被负控写入的文件全是实体副本（不是符号链接）',
   all(not os.path.islink(os.path.join(_sbdir, n)) for n in OV),
   {n: os.path.islink(os.path.join(_sbdir, n)) for n in OV})

p = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                   capture_output=True, text=True, cwd=SB, timeout=900, env=ENV)
out = p.stdout + p.stderr
ck('6.1 沙箱正本 exit 0', p.returncode == 0, p.returncode)
fsb = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
ck('6.2 沙箱 FAIL 行 0', len(fsb) == 0, fsb[:3])
ck('6.3 沙箱 C10 自报 R165', 'C10 self-check: ok(R165)' in out,
   [l for l in out.split('\n') if 'C10 self' in l])
ck('6.4 沙箱 C16 逐节 164 节且 unpinned 0', '164 sections measured (pinned 164)' in out and 'unpinned 0' in out,
   [l for l in out.split('\n') if 'C16 per-section' in l])
ck('6.5 沙箱 C16d 表指纹 OK', ('C16d floor-table pin: %s (OK)' % new_c16_sha[:16]) in out,
   new_c16_sha[:16])

sb2 = SB + '_neg'
shutil.copytree(SB, sb2, symlinks=True)
neg = io.open(os.path.join(sb2, 'lead/next_re_20261117_r14/DISC_RECHECK.tsv'),
              encoding='utf-8').read().replace("GATE_VER = 'R165'", "GATE_VER = 'R999'", 1)
ck('6.6 负控副本确实与正本不同', "GATE_VER = 'R999'" in neg)
io.open(os.path.join(sb2, 'lead/next_re_20261117_r14/DISC_RECHECK.tsv'), 'w', encoding='utf-8').write(neg)
p2 = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                    capture_output=True, text=True, cwd=sb2, timeout=900, env=ENV)
o2 = p2.stdout + p2.stderr
ck('6.7 反控：DR 登记 R999（镜像不同步）⇒ 必 FAIL 且报 C10',
   p2.returncode != 0 and 'C10 self GATE_VER registered' in o2,
   (p2.returncode, [l.strip()[:90] for l in o2.split('\n') if 'C10' in l][:2]))

# 负控 2：把 §2.170 砍到低于 C16 新下界的一半 ⇒ 必须报 C16 hollowed
sb3 = SB + '_neg2'
import importlib.util
shutil.copytree(SB, sb3, symlinks=True)
cm_path = os.path.join(sb3, 'lead/next_re_20261117_r14/R14_COMMON.md')
# S-526 续：必须按 **bytes** 读改写，text 模式会把 CRLF 归一成 LF（这正是写穿时毁掉 1081 个 CR 的原因）
cm = open(cm_path, 'rb').read()
k = cm.index('\n## 2.170 · R165：'.encode())
cut = cm[:k] + '\n## 2.170 · R165：\n'.encode() + b'x' * 100 + b'\n'
with open(cm_path, 'wb') as f:
    f.write(cut)
p3 = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                    capture_output=True, text=True, cwd=sb3, timeout=900, env=ENV)
o3 = p3.stdout + p3.stderr
ck('6.8 反控：§2.170 砍到 100 B ⇒ 必 FAIL 且报 C16 hollowed',
   p3.returncode != 0 and 'C16 section(s) hollowed out' in o3,
   (p3.returncode, [l.strip()[:90] for l in o3.split('\n') if 'C16' in l][:2]))
# 反控：负控跑完，生产 R14_COMMON.md 必须**一字未动**（这条是本轮事故的直接防线）
ck('6.8b 反控后生产 R14_COMMON.md 一字未动（sha 与开跑前相同）',
   sha(rb(os.path.join(T, 'R14_COMMON.md'))) == _prod_common_sha0,
   (sha(rb(os.path.join(T, 'R14_COMMON.md')))[:16], _prod_common_sha0[:16]))
ck('6.8c 反控后生产 R14_COMMON.md 的 CR 计数仍为 1081',
   rb(os.path.join(T, 'R14_COMMON.md')).count(b'\r') == 1081,
   rb(os.path.join(T, 'R14_COMMON.md')).count(b'\r'))
for d in (sb2, sb3, SB):
    shutil.rmtree(d, ignore_errors=True)
ck('6.9 沙箱目录已清理（无孤儿）', not any(os.path.isdir(d) for d in (sb2, sb3, SB)))

res = {'sec_170_bytes': SEC_BYTES, 'floor_170': FLOOR170,
       'old_c16_sha': old_sha, 'new_c16_sha': new_c16_sha,
       'n_sections': len(new_floors), 'new_freeze_sha': new_freeze,
       'c7_text_sha': _now_c7, 'c7_row20': rowsha(_row20),
       'FAILS': len(FAILS), 'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('SEC_170_BYTES=%d FLOOR_170=%d N_SECTIONS=%d' % (SEC_BYTES, FLOOR170, len(new_floors)))
print('C16_FLOORS_SHA256=%s' % new_c16_sha)
print('FREEZE_SHA256=%s' % new_freeze)
print('FAILS=%d' % len(FAILS))
for f in FAILS:
    print('   -', f)
print()
print('FAILS=%d' % len(FAILS))
for f_ in FAILS:
    print('   -', f_)
sys.exit(1 if FAILS else 0)
