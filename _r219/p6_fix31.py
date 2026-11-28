# -*- coding: utf-8 -*-
"""R219 p6：订正已落盘的四件套中「三 offset 引用 31 条」=> 30 条（自错 E3）。

自错 E3 说明：m1 打印的是「对 +0x77c/+0x780/+0x784 的引用」与「0x87c488 派发表」两组的
**合计 31 条**，我误读成「三 offset 合计」，写进了 R14 §2.227 / GOAL §1277 / LEAD_LOCK QM /
STATUS_BOARD 第 219 轮。m13 A2 断言 FAIL 后由 m14 复算定稿：
  0x77c = 9 (call 2 + mov 7)
  0x780 = 9 (call 1 + fmul 2 + fstp 1 + mov 5)
  0x784 = 12 (call 1 + mov 11)
  三 offset 合计 = 30 ；imm32 写 .text 的写入端 = 12
  (另 0x788 = 30、0x87c488 = 1；全五 offset = 61)

本脚本只做**等长安全的字符串替换**，逐条断言旧串命中恰好 1 次，替换后 CR 不变、字节数只增不减，
并回读校验。
"""
import os, hashlib, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
BASE = ROOT + '/R17_LEAD_BASELINE'
fails = []
def ck(n, c, d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
def bak(path, tag):
    b = open(path, 'rb').read()
    dst = '%s/%s.before_r219fix_%s_20261128.bak' % (BASE, os.path.basename(path), tag)
    if os.path.exists(dst):
        assert open(dst, 'rb').read() == b, 'backup differs ' + tag
    else:
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f: f.write(b)
    return b

# ---- 替换对（旧串, 新串）----
PAIRS = [
    ('全 `.text` 对该三个 offset 的引用共 **31** 条，其中「`mov dword ptr [reg+off], imm32` 且 imm32 落 `.text`」的**写入端 12** 条（12/12 目标均在 `.text`），',
     '全 `.text` 对该三个 offset（`+0x77c`/`+0x780`/`+0x784`）的引用共 **30** 条（`0x77c` 9 / `0x780` 9 / `0x784` 12），其中「`mov dword ptr [reg+off], imm32` 且 imm32 落 `.text`」的**写入端 12** 条（12/12 目标均在 `.text`），'),
    ('全 `.text` 对 `+0x77c/+0x780/+0x784` 引用 **31** 条，其中 `mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），',
     '全 `.text` 对 `+0x77c/+0x780/+0x784` 引用 **30** 条（9/9/12），其中 `mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），'),
    ('全 `.text` 对 `+0x77c/+0x780/+0x784` 三个 offset 的引用共 **31** 条；',
     '全 `.text` 对 `+0x77c/+0x780/+0x784` 三个 offset 的引用共 **30** 条（9/9/12）；'),
    ('全 `.text` 对该三个 offset 引用 **31** 条，其中 `mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），',
     '全 `.text` 对该三个 offset 引用 **30** 条（9/9/12），其中 `mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），'),
    ('全 `.text` 对该三 offset 引用 **31** 条，`mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），',
     '全 `.text` 对该三 offset 引用 **30** 条（9/9/12），`mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），'),
]
FILES = [('R14_COMMON', TIER + '/R14_COMMON.md', 1081),
         ('GOAL', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
         ('LOCK', ROOT + '/lead/LEAD_LOCK', 137),
         ('BOARD', TIER + '/STATUS_BOARD.md', 0)]
pre = {}
for tag, p, cr in FILES:
    b0 = bak(p, tag)
    ck('%s 前置 CR=%d' % (tag, cr), b0.count(b'\r') == cr, b0.count(b'\r'))
    s = b0.decode('utf-8')
    n = 0
    for old, new in PAIRS:
        k = s.count(old)
        if k:
            ck('%s 旧串命中 %d 次 : %s…' % (tag, k, old[:28]), k == 1, k)
            s = s.replace(old, new); n += k
    if n == 0:
        print('  [%s] 无匹配串（可能该文件用的措辞不同），稍后单独检查' % tag)
    nb = s.encode('utf-8')
    pre[tag] = dict(before=len(b0), after=len(nb), replaced=n)
    if n:
        open(p, 'wb').write(nb)
        chk = open(p, 'rb').read()
        ck('%s 回读 CR=%d 且以旧内容为前缀' % (tag, cr), chk.count(b'\r') == cr and chk.startswith(b0[:len(b0) // 2]), chk.count(b'\r'))
        ck('%s 字节只增不减' % tag, len(chk) >= len(b0), (len(b0), len(chk)))
        print('  [%s] %d -> %d B (替换 %d 处)' % (tag, len(b0), len(chk), n))
    else:
        print('  [%s] 未改动 %d B' % (tag, len(b0)))
print('\n[汇总]', json.dumps(pre, ensure_ascii=False))
if fails:
    print('[FAILS]', fails)
json.dump(pre, open(ROOT + '/_r219/p6.json', 'w'), indent=1)
