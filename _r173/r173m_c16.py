#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 M：把 C16 逐节下界表补上 §2.178（171 → 172 节）。

fail-closed 顺序（S-582 纪律）：
 1) 备份 check_disc.py（wx），断言备份 sha256 == 现文件 sha256；
 2) 先解析现有 C16_FLOORS 表与 C16_FLOORS_SHA256，用**旧表**重算 sha 必须命中旧常量（硬闸）；
 3) 只插入 id 178 一行（floor = 实测字节的一半），其余 171 条逐条不变；
 4) 重算 sha、写盘、回读断言；
 5) 反控：副本上把 floor 调大 1 必须 FAIL；删掉 178 整行必须 FAIL（理由含 unpinned）。
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, time

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
CD = os.path.join(TIER, 'check_disc.py')
RC = os.path.join(TIER, 'R14_COMMON.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

src = io.open(CD, encoding='utf-8').read()
raw = src.encode('utf-8')

# ---- 2) 解析旧表 ----
m = re.search(r"^C16_FLOORS = \{\n(.*?)^\}", src, re.M | re.S)
ck('A1 找到 C16_FLOORS 表', m is not None, None)
body = m.group(1)
pairs = re.findall(r"^\s*(\d+):\s*(\d+),\s*$", body, re.M)
old_tbl = {int(k): int(v) for k, v in pairs}
ck('A2 旧表 171 条', len(old_tbl) == 171, len(old_tbl))
mpin = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src, re.M)
old_pin = mpin.group(1)
ck('A3 旧 pin == 84273ed6…', old_pin.startswith('84273ed6'), old_pin[:16])

def table_sha(tbl):
    return hashlib.sha256('\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl)).encode()).hexdigest()

ck('A4 用旧表按 check_disc 自身规范化重算 sha，命中旧 pin（硬闸，不命中不写盘）',
   table_sha(old_tbl) == old_pin, (table_sha(old_tbl)[:16], old_pin[:16]))

# ---- 3) 实测 §2.178 字节 ----
rc = io.open(RC, encoding='utf-8', newline='').read()
i = rc.rfind('## 2.178')
sec = rc[i:]
ck('B1 §2.178 定位到末尾段、且只出现 1 次', i > 0 and rc.count('## 2.178') == 1, i)
sec_bytes = len(sec.encode('utf-8'))
floor = sec_bytes // 2
print('   §2.178 实测 %d B ⇒ floor %d' % (sec_bytes, floor))
ck('B2 floor 为正且小于实测（下界语义）', 0 < floor < sec_bytes, (floor, sec_bytes))
ck('B3 178 不在旧表里', 178 not in old_tbl, 178 in old_tbl)

new_tbl = dict(old_tbl)
new_tbl[178] = floor
ck('B4 新表 172 条', len(new_tbl) == 172, len(new_tbl))
ck('B5 原 171 条逐条不变', all(new_tbl[k] == old_tbl[k] for k in old_tbl), True)
new_pin = table_sha(new_tbl)
print('   新 pin', new_pin[:16])

# ---- 4) 只插入一行 ----
lines = src.split('\n')
ins_at = None
for j, l in enumerate(lines):
    mm = re.match(r"^\s*(\d+):\s*(\d+),\s*$", l)
    if mm and int(mm.group(1)) == 177:
        ins_at = j + 1
        break
ck('C1 找到 177 那一行且 178 应插在其后', ins_at is not None, ins_at)
new_lines = lines[:ins_at] + ['    %d: %d,' % (178, floor)] + lines[ins_at:]
new_src = '\n'.join(new_lines)
ck('C2 只多了一行', len(new_lines) == len(lines) + 1, (len(lines), len(new_lines)))
ck('C3 新 pin 替换旧 pin 恰 1 处', new_src.count(old_pin) == 1, new_src.count(old_pin))
new_src = new_src.replace(old_pin, new_pin)
ck('C4 替换后旧 pin 0 次', new_src.count(old_pin) == 0, True)
# S-608：首版 C5 用 zip 逐行比 —— 插入一行会让后面全部错位，报 219 行变化（与 S-587 同族，
# 第三次复发）。改用 SequenceMatcher 拿真正的 opcode。
from difflib import SequenceMatcher as _SM
_ops = [o for o in _SM(None, lines, new_lines, autojunk=False).get_opcodes() if o[0] != 'equal']
ck('C5 行差分恰 1 个 opcode 且为 insert(178 那一行)',
   len(_ops) == 1 and _ops[0][0] == 'insert' and (_ops[0][4] - _ops[0][3]) == 1, _ops)
try:
    compile(new_src, CD, 'exec')
    ck('C6 改后语法合法', True)
except SyntaxError as e:
    ck('C6 改后语法合法', False, e)

# ---- 备份 ----
bak = os.path.join(BASE, 'check_disc.py.before_r173_c16_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('D1 备份 sha256 == 旧文件 sha', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
   os.path.basename(bak))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails)); sys.exit(1)

with open(CD, 'w', encoding='utf-8', newline='') as f:
    f.write(new_src)
back = io.open(CD, encoding='utf-8').read()
ck('E1 回读一致', back == new_src, len(back))

r = subprocess.run([sys.executable, CD], capture_output=True, text=True, timeout=400)
ck('E2 check_disc 实跑 exit 0', r.returncode == 0, r.returncode)
note = [l for l in r.stdout.split('\n') if 'C16 per-section floors' in l]
ck('E3 NOTE 逐字：172 sections measured (pinned 172) … unpinned 0',
   note and '172 sections measured (pinned 172)' in note[0] and 'unpinned 0' in note[0],
   note[0].strip() if note else None)
ck('E4 无行首 FAIL', not any(l.strip().startswith('FAIL') for l in r.stdout.split('\n')),
   [l for l in r.stdout.split('\n') if l.strip().startswith('FAIL')][:3])

# ---- 5) 反控（同深度副本，S-592 纪律）----
# S-609：首版把反控副本放进 TIER/_r173_ctl_<stamp>/ 子目录 —— check_disc 按本文件位置
# **反推三层**得 ROOT，多一层就反推到 .../lead，于是 F1/F3 都以 FileNotFoundError 收场
# （与 R172 S-592 完全同族，第二次复发）。改成与生产文件**同目录同深度**（TIER 直属），
# 并在跑之前先断言三层反推得同一 ROOT。
ctl = TIER
_probe = os.path.join(ctl, 'check_disc.py')
ck('F0 副本目录与生产同深度（三层反推得仓库根）',
   os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(_probe))))
   == os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(CD)))),
   (os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(_probe)))),))
cp_ok = os.path.join(ctl, '_r173_ctl_ok_check_disc.py')
open(cp_ok, 'w', encoding='utf-8', newline='').write(new_src)
r_ok = subprocess.run([sys.executable, cp_ok], capture_output=True, text=True, timeout=400)
ck('F1 反控：未改副本（与生产同深度）exit 0', r_ok.returncode == 0, r_ok.returncode)

tbl_bad = dict(new_tbl); tbl_bad[178] = floor + 1
bad_src = new_src.replace(new_pin, table_sha(tbl_bad))
cp_bad = os.path.join(ctl, '_r173_ctl_bad_floor.py')
open(cp_bad, 'w', encoding='utf-8', newline='').write(bad_src)
r_bad = subprocess.run([sys.executable, cp_bad], capture_output=True, text=True, timeout=400)
ck('F2 反控：floor 调大 1 必 FAIL', r_bad.returncode != 0,
   [l for l in r_bad.stdout.split('\n') if 'C16' in l and 'FAIL' in l][:2])

del_src = re.sub(r"^\s*178:\s*\d+,\n", '', new_src, count=1, flags=re.M)
tbl_del = dict(new_tbl); del tbl_del[178]
del_src = del_src.replace(new_pin, table_sha(tbl_del))
cp_del = os.path.join(ctl, '_r173_ctl_no178.py')
open(cp_del, 'w', encoding='utf-8', newline='').write(del_src)
r_del = subprocess.run([sys.executable, cp_del], capture_output=True, text=True, timeout=400)
ck('F3 反控：删掉 178 整行必 FAIL 且理由含 unpinned', r_del.returncode != 0
   and any('unpinned' in l for l in r_del.stdout.split('\n')),
   [l for l in r_del.stdout.split('\n') if 'unpinned' in l][:2])
for _p in (cp_ok, cp_bad, cp_del):
    try: os.remove(_p)
    except OSError: pass
ck('F4 三个反控副本已清理（不留孤儿）',
   not any(os.path.exists(_p) for _p in (cp_ok, cp_bad, cp_del)), (cp_ok, cp_bad, cp_del))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('check_disc: %d B / sha %s ; C16_FLOORS 171 -> 172 ; pin %s -> %s' % (
    len(back.encode()), hashlib.sha256(back.encode()).hexdigest()[:16], old_pin[:16], new_pin[:16]))
json.dump(dict(fails=fails, asserts=n, old_pin=old_pin, new_pin=new_pin,
               sec_bytes=sec_bytes, floor=floor, c16_rows=len(new_tbl),
               bytes_after=len(back.encode()), sha_after=hashlib.sha256(back.encode()).hexdigest()),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173m_c16.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
