# -*- coding: utf-8 -*-
"""r179f：四件套追加 + 指针升版（一次性，fail-closed）。

纪律（写入纪律）：每次修改前在 R17_LEAD_BASELINE/ 用 wx 模式独占创建唯一备份；
断言旧 sha256 与 CR；一次性写入；回读校验。
"""
import hashlib, io, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
NEW = os.path.join(TIER, '_r179', '_new')
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def sha(b): return hashlib.sha256(b).hexdigest()


def backup(path, tag):
    bp = os.path.join(BASE, tag)
    if os.path.exists(bp):
        ck('备份已存在且可复算 %s' % tag, sha(open(bp, 'rb').read()) == sha(open(path, 'rb').read()))
        return
    fd = os.open(bp, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('wx 独占创建备份 %s' % tag, sha(open(bp, 'rb').read()) == sha(open(path, 'rb').read()))


# ---- 0. 旧状态断言 ----
EXP = {
    RC: ('f7dfeb258daa583759f3cdd1d77e6e218686e13772a2806aa2d912d9b57b4db8', 1081, 1567113),
    LED: ('5c23a03160857eb4d1216dadbd3b300e14e5998a330945ef5f6613033fcf4cd8', 337, 5296864),
    LOCK: ('72ee396c440601db7f3f81b0a2f1fab65f4c86345f693818585cfc6af5be325a', 137, 1237725),
    BRD: ('b2139c8b0c13ca2163be417c16c4e05d26bfd211381b59cec1b7c56f840d0b80', 0, 49256),
}
for p, (sh, cr, nb) in EXP.items():
    raw = open(p, 'rb').read()
    ck('旧状态 %s sha' % os.path.basename(p), sha(raw) == sh, sha(raw)[:16])
    ck('旧状态 %s CR=%d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    ck('旧状态 %s bytes=%d' % (os.path.basename(p), nb), len(raw) == nb, len(raw))
ck('看板 231 行 < 260，本轮不归档', open(BRD, 'rb').read().count(b'\n') == 231)

seg_rc = open(os.path.join(NEW, 'c_2_184.md'), 'rb').read()
seg_led = open(os.path.join(NEW, 'ledger_1234.md'), 'rb').read()
seg_lock = open(os.path.join(NEW, 'lock_pj.md'), 'rb').read()
seg_brd = open(os.path.join(NEW, 'board_179.md'), 'rb').read()
for nm, b in (('c_2_184', seg_rc), ('ledger_1234', seg_led), ('lock_pj', seg_lock), ('board_179', seg_brd)):
    ck('新段 %s 无 CR' % nm, b.count(b'\r') == 0, b.count(b'\r'))
# S-659：原稿对四段统一要求「以换行开头」。实测三段（R14 / 台账 / 锁定）需要前导空行，
# 而看板是「## 标题直接接在上一节末尾空行之后」的体例，不能加前导空行 —— 统一要求是错的。
ck('R14 / 台账 / 锁定 三段以空行开头', all(b.startswith(b'\n') for b in (seg_rc, seg_led, seg_lock)))
ck('看板段直接以 ## 开头（不加前导空行，符合看板体例）', seg_brd.startswith('## '.encode()))
ck('四段拼接后行数账：看板 231 + %d = %d <= 300'
   % (seg_brd.count(b'\n'), 231 + seg_brd.count(b'\n')), 231 + seg_brd.count(b'\n') <= 300)
ck('R14 新段不引入新节号重复', '## 2.184 · R179' in seg_rc.decode('utf-8'))
ck('台账新段 = §1234', '## §1234 · R179' in seg_led.decode('utf-8'))
ck('锁定新段 = PJ', seg_lock.decode('utf-8').startswith('\n\nPJ · R17 第 179 轮'))

# ---- 1. 备份 ----
for p, t in ((RC, 'R179_R14_COMMON.before_r179.bak'), (LED, 'R179_LEDGER.before_r179.bak'),
             (LOCK, 'R179_LEAD_LOCK.before_r179.bak'), (BRD, 'R179_STATUS_BOARD.before_r179.bak'),
             (PTR, 'R179_FACT_INDEX_CURRENT.before_r179.bak')):
    backup(p, t)

# ---- 2. 构造并写盘 ----
def do_append(path, seg, exp_cr):
    old = open(path, 'rb').read()
    sh0 = sha(old)
    new = old + seg
    ck('%s 拼接后 CR 不变' % os.path.basename(path), new.count(b'\r') == exp_cr, new.count(b'\r'))
    ck('%s 拼接后 sha 变化' % os.path.basename(path), sha(new) != sh0)
    open(path, 'wb').write(new)
    rb = open(path, 'rb').read()
    ck('%s 回读一致' % os.path.basename(path), rb == new)
    ck('%s 回读 CR=%d' % (os.path.basename(path), exp_cr), rb.count(b'\r') == exp_cr)
    print('  %s: %d -> %d B (+%d)' % (os.path.basename(path), len(old), len(rb), len(rb) - len(old)))
    return rb


if FAIL:
    print('ABORT 未写盘'); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry 通过'); print('---- %d PASS / %d FAIL ----' % (PASS, FAIL)); sys.exit(0)

rb_rc = do_append(RC, seg_rc, 1081)
rb_led = do_append(LED, seg_led, 337)
rb_lock = do_append(LOCK, seg_lock, 137)
rb_brd = do_append(BRD, seg_brd, 0)
ck('看板仍 <= 300 行', rb_brd.count(b'\n') <= 300, rb_brd.count(b'\n'))

# ---- 3. 指针升版（先写新版本目录已完成，改指针在后）----
V562TSV = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
b = open(V562TSV, 'rb').read()
newsha = sha(b)
txt = io.open(PTR, encoding='utf-8', newline='').read()
t2 = txt.replace('R17_R129_FACTINDEX_V561', 'R17_R131_FACTINDEX_V563')
t2 = t2.replace('dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7', newsha)
t2 = t2.replace('| 字节数 | 133317 |', '| 字节数 | %d |' % len(b))
t2 = t2.replace('| 声明轮次 | R178 |', '| 声明轮次 | R179 |')
t2 = t2.replace('530..561 连续 32 份', '530..563 连续 34 份')
t2 = t2.replace('530..561 是 32 个', '530..563 是 34 个')
ck('指针改动生效（sha/字节/轮次/份数四处都变）',
   newsha in t2 and '| 字节数 | %d |' % len(b) in t2 and 'R179' in t2 and '530..563' in t2)
ck('指针不再指向 V561', 'V561' not in t2)
open(PTR, 'w', encoding='utf-8', newline='').write(t2)
ck('指针回读一致', io.open(PTR, encoding='utf-8', newline='').read() == t2)
ck('指针 CR=0', open(PTR, 'rb').read().count(b'\r') == 0)

print()
print('新状态：R14 %d B / LEDGER %d B / LOCK %d B / BOARD %d 行 %d B / PTR %d B'
      % (len(rb_rc), len(rb_led), len(rb_lock), rb_brd.count(b'\n'), len(rb_brd), len(t2.encode())))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
