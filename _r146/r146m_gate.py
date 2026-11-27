#!/usr/bin/env python3
"""R146 M：门禁回归（两处核心 + 两处 TSV 同步），纪律照 r145k/r145l/r145m：
  ① 重钉前先用**现表**复现**旧钉**（方法可复现性正控）
  ② 新钉 != 旧钉，且长度必须恰 64（S-320 教训：断言要比形状，不只比值）
  ③ 一次性整常量正则替换（不做前缀拼接）
  ④ 每步回读
"""
import io, os, re, json, hashlib, time, sys
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
GATE = os.path.join(BASE, 'check_disc.py')
DR = os.path.join(BASE, 'DISC_RECHECK.tsv')
DU = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')
RC = os.path.join(BASE, 'R14_COMMON.md')

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: FAILS.append(n)
    return bool(c)
def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def backup(path, tag):
    src = open(path, 'rb').read()
    dst = os.path.join(BL, os.path.basename(path) + '.before_r146_' + tag + '_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
    io.open(dst, 'xb').write(src)
    ck('备份 wx 独占且逐字节相同 [' + tag + ']', open(dst, 'rb').read() == src, os.path.basename(dst))

# ---------- A. §2.151 字节数（C16 口径）----------
def sec_bytes(text, num):
    cur = None; acc = []
    for l in text.split('\n'):
        if re.match(r'^##\s+2\.' + str(num) + r'\b', l):
            cur = num; acc = [l]; continue
        if cur == num:
            if re.match(r'^##\s+', l): break
            acc.append(l)
    return len('\n'.join(acc).encode('utf-8'))
rc = rd(RC)
size151 = sec_bytes(rc, 151); floor151 = size151 - 21
ck('§2.151 字节数 > 8000', size151 > 8000, size151)
ck('§2.151 在 R14_COMMON 中只出现一次', len(re.findall(r'(?m)^## 2\.151', rc)) == 1)
print('  size151=%d floor151=%d' % (size151, floor151))

# ---------- B. check_disc.py：C16_FLOORS + GATE_VER ----------
g0 = rd(GATE)
ck('门禁 CR == 0', g0.count('\r') == 0, g0.count('\r'))
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', g0, re.S)
ck('找到 C16_FLOORS', m is not None)
fl = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]+)'", g0).group(1)
ck('旧钉长度为 64 hex', len(old_sha) == 64, len(old_sha))
ck('旧钉前缀 183a5d82（R145 钉）', old_sha.startswith('183a5d82'), old_sha[:16])
ck('表项 144 条（R145 状态）', len(fl) == 144, len(fl))
ck('表里尚无 151', 151 not in fl, 151 in fl)
norm = lambda dd: '\n'.join('%d:%d' % (k, dd[k]) for k in sorted(dd))
ck('用现表 + 旧归一法能复现旧钉（方法正控）', sha(norm(fl)) == old_sha, sha(norm(fl))[:16])
fl2 = dict(fl); fl2[151] = floor151
new_sha = sha(norm(fl2))
ck('新钉长度为 64', len(new_sha) == 64, len(new_sha))
ck('新钉 != 旧钉', new_sha != old_sha)
ck('新钉由 145 项算出', len(fl2) == 145, len(fl2))

g1 = g0.replace("C16_FLOORS_SHA256 = '%s'" % old_sha, "C16_FLOORS_SHA256 = '%s'" % new_sha)
ck('C16_FLOORS_SHA256 已整常量替换（不复用前缀拼接）', ("C16_FLOORS_SHA256 = '%s'" % new_sha) in g1)
# 插入 151 项：插在 150 项之后
m150 = re.search(r'(150:\s*\d+,)', g1)
ck('找到 150 项', m150 is not None, m150.group(1) if m150 else None)
g1 = g1.replace(m150.group(1), m150.group(1) + ' 151: %d,' % floor151)
ck('已插入 151 项且只插一次', g1.count('151: %d,' % floor151) == 1, g1.count('151: %d,' % floor151))
# GATE_VER
ck('GATE_VER 当前为 R145', "GATE_VER = 'R145'" in g1)
g1 = g1.replace("GATE_VER = 'R145'", "GATE_VER = 'R146'")
ck('GATE_VER 已改 R146', "GATE_VER = 'R146'" in g1 and "GATE_VER = 'R145'" not in g1)
ck('改动后 CR 仍 0', g1.count('\r') == 0)
ck('改动后内容确实变化', g1 != g0)
backup(GATE, 'gate')
io.open(GATE, 'w', encoding='utf-8', newline='').write(g1)
gb = rd(GATE)
ck('门禁回读含新钉与新版本', new_sha in gb and "GATE_VER = 'R146'" in gb)
ck('门禁回读 CR == 0', gb.count('\r') == 0, gb.count('\r'))

# ---------- C. DISC_RECHECK.tsv 主键 20 行 ----------
dr0 = rd(DR)
lines = dr0.split('\n')
hdr = lines[0].split('\t')
ck('DR 表头 7 列', len(hdr) == 7, len(hdr))
tgt = None
for i, l in enumerate(lines):
    if not l.strip(): continue
    c = l.split('\t')
    if c[0] == '20':
        tgt = i; break
ck('找到主键 20 的行', tgt is not None, tgt)
row = lines[tgt].split('\t')
ck('该行第 6 列当前是 R145 校验式', row[5] == "grep=(?m)^GATE_VER = 'R145'", row[5])
row2 = list(row); row2[5] = "grep=(?m)^GATE_VER = 'R146'"
lines2 = list(lines); lines2[tgt] = '\t'.join(row2)
dr1 = '\n'.join(lines2)
ck('DR 行数不变', dr1.count('\n') == dr0.count('\n'), [dr0.count('\n'), dr1.count('\n')])
ck('DR 唯一改动是那一行', sum(1 for a, b in zip(lines, lines2) if a != b) == 1)
ck('DR CR 仍 0', dr1.count('\r') == 0)
backup(DR, 'dr')
io.open(DR, 'w', encoding='utf-8', newline='').write(dr1)
ck('DR 回读含新校验式', "grep=(?m)^GATE_VER = 'R146'" in rd(DR))

# ---------- D. DISC_UNVERIFIABLE.tsv 主键 20 行 ----------
du0 = rd(DU)
L = du0.split('\n')
ck('DU 表头 8 列', len(L[0].split('\t')) == 8, len(L[0].split('\t')))
t2 = None
for i, l in enumerate(L):
    if not l.strip(): continue
    if l.split('\t')[0] == '20':
        t2 = i; break
ck('找到 DU 主键 20 的行', t2 is not None, t2)
r = L[t2].split('\t')
ck('DU 该行校验式当前是 R145', r[3] == "grep=(?m)^GATE_VER = 'R145'", r[3])
r2 = list(r); r2[3] = "grep=(?m)^GATE_VER = 'R146'"
L2 = list(L); L2[t2] = '\t'.join(r2)
du1 = '\n'.join(L2)
ck('DU 行数不变', du1.count('\n') == du0.count('\n'))
ck('DU 唯一改动是那一行', sum(1 for a, b in zip(L, L2) if a != b) == 1)
backup(DU, 'du')
io.open(DU, 'w', encoding='utf-8', newline='').write(du1)
new_du_sha = hashlib.sha256(open(DU, 'rb').read()).hexdigest()
ck('DU 文件 sha 长度为 64', len(new_du_sha) == 64, len(new_du_sha))
# FREEZE_SHA256 同步（按字节算，不是按文本）
old_freeze = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gb).group(1)
ck('门禁 FREEZE_SHA256 长度为 64', len(old_freeze) == 64, len(old_freeze))
ck('门禁 FREEZE_SHA256 = 旧 DU 字节 sha（方法正控）', old_freeze == hashlib.sha256(du0.encode('utf-8')).hexdigest())
gb2 = gb.replace("FREEZE_SHA256 = '%s'" % old_freeze, "FREEZE_SHA256 = '%s'" % new_du_sha)
ck('FREEZE_SHA256 已整常量替换', ("FREEZE_SHA256 = '%s'" % new_du_sha) in gb2)
ck('FREEZE_SHA256 新值长度为 64', len(new_du_sha) == 64, len(new_du_sha))
ck('FREEZE_SHA256 新值 != 旧值', new_du_sha != old_freeze)
io.open(GATE, 'w', encoding='utf-8', newline='').write(gb2)
ck('门禁回读含新 FREEZE', new_du_sha in rd(GATE))

json.dump({'fails': FAILS, 'size151': size151, 'floor151': floor151,
           'c16_old': old_sha, 'c16_new': new_sha, 'freeze_new': new_du_sha},
          open('/home/t628/projects/ra2-campaign-forge/_r146/r146m_gate.json', 'w'), indent=1)
print('\n=== 门禁回归 FAILS %d ===' % len(FAILS)); print(FAILS)
sys.exit(1 if FAILS else 0)
