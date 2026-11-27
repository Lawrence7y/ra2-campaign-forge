#!/usr/bin/env python3
"""R147 N：GATE_VER 换轮后的三处锚点同步 + 重钉。

为什么必须改（不是可选项）：门禁 C7 id20 / C12 id20 的校验式就是
  grep=(?m)^GATE_VER = 'R146'
GATE_VER 一改成 R147，这条锚点自然 0 命中 ⇒ 门禁当场 3 条 FAIL。
这是门禁**正确行为**（锚点必须随版本走），不是门禁坏了。

要改的四处：
  1. DISC_RECHECK.tsv  主键 20 的 col6：R146 → R147
  2. DISC_UNVERIFIABLE.tsv 主键 20 的 校验式：R146 → R147
  3. check_disc.py 的 C7_TEXT_SHA256      （DISC_RECHECK 全文指纹，丢表头口径）
  4. check_disc.py 的 C7_ROW_SHA['20']     （该行 col5/col6 指纹）
  5. check_disc.py 的 FREEZE_SHA256        （DISC_UNVERIFIABLE 全文 sha）
  另需处理 R146 遗留的 C10 自述行版本号（GATE_VER 字段）。
"""
import io, os, re, json, time, hashlib, sys

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
GATE = os.path.join(BASE, 'check_disc.py')
RCH = os.path.join(BASE, 'DISC_RECHECK.tsv')
DUF = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)
    return bool(c)

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def wr(p, s):
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

def bak(p, tag):
    src = open(p, 'rb').read()
    dst = os.path.join(BL, os.path.basename(p) + '.before_r147_' + tag + '_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
    with io.open(dst, 'xb') as f:
        f.write(src)
    ck('备份 wx 独占且逐字节相同 [' + tag + ']', open(dst, 'rb').read() == src, os.path.basename(dst))

OLD = "grep=(?m)^GATE_VER = 'R146'"
NEW = "grep=(?m)^GATE_VER = 'R147'"

# ---------- 1 DISC_RECHECK 主键 20 ----------
r0 = rd(RCH)
ck('DR 前置 CR == 0', r0.count('\r') == 0, r0.count('\r'))
ck('DR 前置 R146 锚点恰 1 次', r0.count(OLD) == 1, r0.count(OLD))
ck('DR 前置 R147 锚点尚未出现（幂等）', NEW not in r0, NEW in r0)
if FAILS:
    print('abort'); sys.exit(2)
bak(RCH, 'dr')
r1 = r0.replace(OLD, NEW, 1)
wr(RCH, r1)
rb = rd(RCH)
ck('DR 回读 R147 锚点恰 1 次', rb.count(NEW) == 1, rb.count(NEW))
ck('DR 回读 R146 锚点 0 次', rb.count(OLD) == 0, rb.count(OLD))
ck('DR 回读 CR == 0', rb.count('\r') == 0, rb.count('\r'))
ck('DR 回读 行数 32（表头+31）', len([l for l in rb.split('\n') if l.strip()]) == 32,
   len([l for l in rb.split('\n') if l.strip()]))

# ---------- 2 DISC_UNVERIFIABLE 主键 20 ----------
d0 = rd(DUF)
ck('DU 前置 R146 锚点恰 1 次', d0.count(OLD) == 1, d0.count(OLD))
bak(DUF, 'du')
d1 = d0.replace(OLD, NEW, 1)
wr(DUF, d1)
db = rd(DUF)
ck('DU 回读 R147 锚点恰 1 次', db.count(NEW) == 1, db.count(NEW))
ck('DU 回读 R146 锚点 0 次', db.count(OLD) == 0, db.count(OLD))
ck('DU 回读 行数 13', len([l for l in db.split('\n') if l.strip()]) == 13,
   len([l for l in db.split('\n') if l.strip()]))

# ---------- 3 重钉 C7d / C7_ROW_SHA[20] ----------
def c7d(raw):
    lines = raw.split('\n')
    rows = [l.split('\t') for l in lines[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), rows

g0 = rd(GATE)
ck('门禁 前置 CR == 0', g0.count('\r') == 0, g0.count('\r'))
h_new, rows = c7d(rb)
pin_old = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g0).group(1)
ck('门禁 旧 C7d 钉 == 用旧 TSV 复现值（算法一致）',
   pin_old == hashlib.sha256('\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                                       for r in [l.split('\t') for l in r0.split('\n')[1:]] if len(r) == 7).encode()).hexdigest(),
   pin_old[:16])
ck('新 C7d != 旧 C7d（TSV 改动被指纹捕获）', h_new != pin_old, [pin_old[:16], h_new[:16]])
row20 = [r for r in rows if len(r) == 7 and r[0] == '20'][0]
h20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
old20 = re.search(r"'20': '([0-9a-f]{64})'", g0).group(1)
ck('新 row20 != 旧 row20', h20 != old20, [old20[:16], h20[:16]])
ck('反控：含表头重算得不同 C7d 值（证明丢表头口径敏感）',
   c7d('HEADER\n' + rb)[0] != h_new, True)

g1 = g0.replace("C7_TEXT_SHA256 = '%s'" % pin_old, "C7_TEXT_SHA256 = '%s'" % h_new)
ck('C7_TEXT_SHA256 已整常量替换', ("C7_TEXT_SHA256 = '%s'" % h_new) in g1)
g1 = g1.replace("'20': '%s'" % old20, "'20': '%s'" % h20)
ck("C7_ROW_SHA['20'] 已整常量替换", ("'20': '%s'" % h20) in g1)

# ---------- 4 FREEZE_SHA256 ----------
fr_old = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g1).group(1)
fr_new = hashlib.sha256(db.encode('utf-8')).hexdigest()
ck('FREEZE 旧钉 == 旧 DU 文件 sha（算法一致）',
   fr_old == hashlib.sha256(d0.encode('utf-8')).hexdigest(), fr_old[:16])
ck('FREEZE 新 != 旧', fr_new != fr_old, [fr_old[:16], fr_new[:16]])
g1 = g1.replace("FREEZE_SHA256 = '%s'" % fr_old, "FREEZE_SHA256 = '%s'" % fr_new)
ck('FREEZE_SHA256 已整常量替换', ("FREEZE_SHA256 = '%s'" % fr_new) in g1)

bak(GATE, 'repin')
wr(GATE, g1)
gb = rd(GATE)
ck('门禁 回读 三钉自洽',
   h_new in gb and h20 in gb and fr_new in gb)
ck('门禁 回读 CR == 0', gb.count('\r') == 0, gb.count('\r'))

json.dump({'fails': FAILS, 'c7d_old': pin_old, 'c7d_new': h_new,
           'row20_old': old20, 'row20_new': h20,
           'freeze_old': fr_old, 'freeze_new': fr_new},
          open('/home/t628/projects/ra2-campaign-forge/_r147/r147n_repin.json', 'w'), indent=1)
print('\n=== FAILS %d ===' % len(FAILS))
print(json.dumps({'fails': FAILS, 'c7d': [pin_old[:16], h_new[:16]],
                  'row20': [old20[:16], h20[:16]], 'freeze': [fr_old[:16], fr_new[:16]]}, indent=1))
sys.exit(1 if FAILS else 0)
