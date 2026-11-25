# -*- coding: utf-8 -*-
"""R129j：五条不可能行的裁定落盘 —— 走「降级」，三处常量同步重钉。

裁定：降级（第 7 列 有 -> 无）。理由三条，都由 r129i 实测支撑：
  路一「改行」在机制上不可行：只改 round 到路径轮次，五条 at 全落在 R55 窗口，
       离 R61/81/84/88 的窗口很远 ⇒ R4 必失败；要过就必须改 at，而 at 无外部时钟，
       改它就是编造时刻。不做。
  路二「撤回」会让 C11 立刻 FAIL（声称有却没有有效自述行），必须连第 7 列一起改 ⇒ 与路三同形。
  路三「降级」不需要编造任何时刻，且代价全部是**显式重钉**（可见、要写理由），故取此路。

三处同步重钉（缺一处门禁就红）：
  a DISC_RECHECK.tsv 第 7 列：id 3/4/22/27/28 由「有（后续轮回跑）」改成「无（R129 裁定：自述行时间上不可能，已撤回声称）」
  b C11B_PIN_GAP：7 个 id -> 12 个 id
  c C17_PIN / C17_PIN_SHA256：5 条 -> 空集

写入纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 一次性写入 -> 回读校验 -> 断言 CR 不变。
"""
import io, os, sys, hashlib, datetime, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
ck = []
def add(n, ok, d=''):
    ck.append((n, bool(ok), d))

def sha(b): return hashlib.sha256(b).hexdigest()

OLD_DR_SHA = None
old_dr = io.open(DR, 'rb').read()
add('J0 开工前 DISC_RECHECK.tsv CR 为 0', old_dr.count(b'\r') == 0, old_dr.count(b'\r'))
old_gate = io.open(GATE, 'rb').read()
add('J1 开工前 check_disc.py 含 GATE_VER = R129', b"GATE_VER = 'R129'" in old_gate)

# ---- a. 第 7 列 ----
t = old_dr.decode('utf-8')
lines = t.split('\n')
NEW_LATER = '无（R129 裁定：自述行时间上不可能，已撤回声称）'
cnt = 0
out = []
for l in lines:
    c = l.split('\t')
    if len(c) == 7 and c[0] in ('3', '4', '22', '27', '28') and c[6].strip().startswith('有'):
        c[6] = NEW_LATER
        cnt += 1
        out.append('\t'.join(c))
    else:
        out.append(l)
add('J2 恰好改到 5 行第 7 列', cnt == 5, cnt)
t2 = '\n'.join(out)
assert '\r' not in t2
for i in ('3', '4', '22', '27', '28'):
    row = [x for x in t2.split('\n') if x.split('\t')[0] == i and len(x.split('\t')) == 7]
    add('J3 id %s 第 7 列已降级且其余 6 列一字未动' % i,
        len(row) == 1 and row[0].split('\t')[6] == NEW_LATER
        and row[0].split('\t')[:6] == [x for x in t.split('\n') if x.split('\t')[0] == i and len(x.split('\t')) == 7][0].split('\t')[:6],
        row[0].split('\t')[6] if row else None)

# ---- b/c. 门禁常量 ----
g = old_gate.decode('utf-8')
assert g.count('C11B_PIN_GAP = [11, 12, 13, 14, 15, 17, 26]') == 1
g2 = g.replace('C11B_PIN_GAP = [11, 12, 13, 14, 15, 17, 26]',
               'C11B_PIN_GAP = [3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]')
add('J4 C11B_PIN_GAP 7 -> 12 个 id（幂等：按排序写死）', 'C11B_PIN_GAP = [3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]' in g2)
OLD_C17 = """C17_PIN = {
    (3, 55, '2026-11-22T17:39:19+08:00'),
    (4, 55, '2026-11-22T17:40:02+08:00'),
    (22, 55, '2026-11-22T17:39:19+08:00'),
    (27, 55, '2026-11-22T17:39:19+08:00'),
    (28, 55, '2026-11-22T17:39:19+08:00'),
}
C17_PIN_SHA256 = '642c9cd8b9176f4e8dffd0c744e651d26e5465186a79bcaace70cadbc7a59288'"""
NEW_C17 = """# R129 裁定（_r129/r129i_ruling_design.py 12/12 PASS）：这五条已从「声称有」降级成「无」，
# 自述行本身仍留在原产物里（不删别人的产物），但第 7 列不再声称它们回跑过 ⇒ C17 扫不到它们。
# 故集合由 5 条塌成 0 条。空集不是「关掉检查」：判据仍是「实测集合必须等于这个集合」，
# 只要有人再写一条时间上不可能的自述行并声称有，集合就 ≠ 空集 ⇒ FAIL。
C17_PIN = set()
C17_PIN_SHA256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'"""
assert g2.count(OLD_C17) == 1
g2 = g2.replace(OLD_C17, NEW_C17)
add('J5 C17_PIN 由 5 条改为空集并换摘要（空集的 sha256 = e3b0c442...，实测非手填）',
    "C17_PIN = set()" in g2 and hashlib.sha256(b'').hexdigest().startswith('e3b0c442'))
add('J6 空集摘要与 hashlib 对空串的实测值逐位相同',
    "C17_PIN_SHA256 = '%s'" % hashlib.sha256(b'').hexdigest() in g2)

# 回填 notes 措辞：pinned 由 len(C17_PIN) 给出，已自动变 0；不改。
# ---- 落盘 ----
def write(path, oldb, newtext, tag):
    dst = os.path.join(BK, 'r129_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try: os.write(fd, oldb)
    finally: os.close(fd)
    nb = newtext.encode('utf-8')
    assert nb.count(b'\r') == oldb.count(b'\r'), '%s CR 变了' % tag
    with io.open(path, 'wb') as f: f.write(nb)
    rb = io.open(path, 'rb').read()
    add('J7 %s 回读 == 写入 且 CR 不变' % tag, rb == nb and rb.count(b'\r') == oldb.count(b'\r'),
        (len(oldb), len(rb), rb.count(b'\r')))
    return dst

write(DR, old_dr, t2, 'disc_recheck_ruling')
write(GATE, old_gate, g2, 'check_disc_ruling')

bad = [c for c in ck if not c[1]]
for n, ok, d in ck:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d != '' else ''))
print('%d/%d PASS' % (len(ck) - len(bad), len(ck)))
sys.exit(1 if bad else 0)
