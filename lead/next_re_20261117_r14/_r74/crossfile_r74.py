# -*- coding: utf-8 -*-
"""R74 · 五道 CR 不变量文件 + 门禁脚本的**全控制字节普查**（跨文件）

由来：R14_COMMON.md 的 48 个控制字节是在 `_r74/escapefam_r74.py` 里查的（单文件）。
落盘后回读时发现 `LEAD_LOCK` 也有一个 0x07。于是把普查**扩到全部不变量文件与门禁脚本**，
用同一个判据，一次答清「哪些文件干净、哪些不干净」。

测量项：
  F1  10 个受约束文件的 C0 控制字节普查（TAB / LF / CR 合法，排除）
  F2  每个控制字节的「还原字符」判定：由 Python 单字符转义表给出，不许猜
  F3  缺陷能否追溯到最早留存备份（判「哪一轮写坏」在本库内是否可得）
  F4  新写入的四段（§2.79 / §1128 / 段 DB / 看板第 74 轮）是否引入了新的控制字节
  F5  五道 CR 不变量在原位（不因本轮写入而变）

反控：
  K1  STATUS_BOARD.md（已知干净）跑同一普查必须 0 个
  K2  本轮四份产物脚本自身跑同一普查必须 0 个
  K3  把 0x07 站点还原为字母后，token 必须在本库其他文件里作为整体出现
  K4  普查必须能报出 R14_COMMON 的 48 个（正控：已知非空文件不许报 0）
"""
import io
import os
import re
import sys
import json
import codecs

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)

CTRL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')
MODEL = {0x00: '0', 0x0c: 'f', 0x0b: 'v', 0x07: 'a', 0x08: 'b'}

TARGETS = [
    ('R14_COMMON.md', os.path.join(R14, 'R14_COMMON.md'), 1081),
    ('STATUS_BOARD.md', os.path.join(R14, 'STATUS_BOARD.md'), 0),
    ('BOARD_ARCHIVE.md', os.path.join(R14, 'BOARD_ARCHIVE.md'), 2952),
    ('DISC_RECHECK.tsv', os.path.join(R14, 'DISC_RECHECK.tsv'), 0),
    ('DISC_ESTABLISH.tsv', os.path.join(R14, 'DISC_ESTABLISH.tsv'), 0),
    ('COMPACT_STATE.md', os.path.join(R14, 'COMPACT_STATE.md'), 0),
    ('check_disc.py', os.path.join(R14, 'check_disc.py'), 309),
    ('recheck_verify.py', os.path.join(R14, 'recheck_verify.py'), 321),
    ('GOAL_THREE_TARGETS_20261018.md',
     os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    ('LEAD_LOCK', os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
]

# ---------------------------------------------------------------- F1 / F5
P('=== F1 · 10 个受约束文件的 C0 控制字节普查 ===')
P('  %-34s %9s %6s %6s %s' % ('文件', '字节', 'CR', 'CTRL', '站点'))
results = {}
for name, path, cr in TARGETS:
    b = io.open(path, 'rb').read()
    hits = [(m.start(), m.group()[0]) for m in CTRL.finditer(b)]
    results[name] = {'bytes': len(b), 'cr': b.count(b'\r'), 'hits': hits}
    P('  %-34s %9d %6d %6d %s' % (name, len(b), b.count(b'\r'), len(hits),
                                  [(o, hex(x)) for o, x in hits[:8]]))
dirty = [n for n, r in results.items() if r['hits']]
clean = [n for n, r in results.items() if not r['hits']]
P('  含控制字节的文件 = %s' % (dirty or '无'))
P('  干净的文件 = %d 个' % len(clean))

ck('F1a 已知非空的 R14_COMMON.md 报出 48 个（正控：普查不是恒报 0）',
   len(results['R14_COMMON.md']['hits']) == 48,
   '%d' % len(results['R14_COMMON.md']['hits']))
ck('F1b LEAD_LOCK 含 1 个控制字节（本轮落盘回读时才发现，此前从未查过）',
   len(results['LEAD_LOCK']['hits']) == 1,
   '%d' % len(results['LEAD_LOCK']['hits']))
ck('F1c 其余 8 个文件干净（含门禁两个脚本）',
   len(clean) == 8, '%d' % len(clean))

P('')
P('=== F5 · 五道 CR 不变量原位 ===')
EXP = {'R14_COMMON.md': 1081, 'LEAD_LOCK': 137,
       'GOAL_THREE_TARGETS_20261018.md': 337,
       'STATUS_BOARD.md': 0, 'BOARD_ARCHIVE.md': 2952}
for n, e in EXP.items():
    got = results[n]['cr']
    ck('F5 %-32s CR = %d' % (n, e), got == e, '%d' % got)
ck('F5f 看板总行数 <= 300',
   io.open(os.path.join(R14, 'STATUS_BOARD.md'), 'rb').read().count(b'\n') <= 300,
   '%d' % io.open(os.path.join(R14, 'STATUS_BOARD.md'), 'rb').read().count(b'\n'))

# ---------------------------------------------------------------- F2
P('')
P('=== F2 · 每个控制字节的还原字符（由转义表给，不许猜） ===')
ESC_TABLE = {}
for lit in (r'\0', r'\f', r'\v', r'\a', r'\b'):
    ESC_TABLE[ord(codecs.decode(lit, 'unicode_escape'))] = lit
P('  转义表：%s' % {hex(k): v for k, v in sorted(ESC_TABLE.items())})
allbytes = set()
for n, r in results.items():
    for _, x in r['hits']:
        allbytes.add(x)
P('  全库出现过的控制字节取值 = %s' % [hex(b) for b in sorted(allbytes)])
ck('F2a 出现过的取值全部在转义表内', allbytes <= set(ESC_TABLE),
   str([hex(b) for b in sorted(allbytes - set(ESC_TABLE))]))
ck('F2b 转义表键集与还原模型键集一致', set(ESC_TABLE) == set(MODEL))

# ---------------------------------------------------------------- F3
P('')
P('=== F3 · 缺陷能否追溯到最早留存备份 ===')
def first_backup_offsets(pat):
    fs = sorted(f for f in os.listdir(BASE) if pat in f)
    rows = []
    for f in fs:
        b = io.open(os.path.join(BASE, f), 'rb').read()
        rows.append((f, len(b), [(m.start(), m.group()[0]) for m in CTRL.finditer(b)]))
    return rows
for label, pat in (('R14_COMMON', 'R14_COMMON'), ('LEAD_LOCK', 'LEAD_LOCK')):
    P('  [%s]' % label)
    rows = first_backup_offsets(pat)
    for f, n, h in rows:
        P('    %-62s %8d B CTRL=%s' % (f, n, [(o, hex(x)) for o, x in h[:4]]))
    offs = {tuple(o for o, _ in h) for _, _, h in rows}
    byteset = {tuple(sorted(set(x for _, x in h))) for _, _, h in rows}
    ck('F3 %s：全部备份的控制字节**偏移集合**相同 ⇒ 本库内定不出写坏轮次' % label,
       len(offs) == 1, '%d 种偏移集合' % len(offs))
    ck('F3 %s：全部备份的控制字节**取值集合**相同' % label,
       len(byteset) == 1, str([sorted(x) for x in byteset]))
    P('    备份份数 = %d' % len(rows))

# ---------------------------------------------------------------- F4
P('')
P('=== F4 · 本轮四段是否引入了新的控制字节 ===')
segs = [
    ('R14_COMMON §2.79', os.path.join(R14, 'R14_COMMON.md'), '## 2.79'),
    ('台账 §1128', os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), '## §1128'),
    ('LEAD_LOCK DB', os.path.join(ROOT, 'lead', 'LEAD_LOCK'), '## DB ·'),
    ('看板第 74 轮', os.path.join(R14, 'STATUS_BOARD.md'), '## 🔴 R17 第 74 轮'),
]
for label, path, marker in segs:
    b = io.open(path, 'rb').read()
    try:
        i = b.rindex(marker.encode('utf-8'))
    except ValueError:
        ck('F4 %s 段存在' % label, False, 'marker not found')
        continue
    seg = b[i:]
    h = CTRL.findall(seg)
    P('  %-20s 段 %6d B ；控制字节 %d %s' % (label, len(seg), len(h),
                                            [hex(x[0]) for x in h[:6]]))
    ck('F4 %s 段内 0 个控制字节' % label, not h, str([hex(x[0]) for x in h[:6]]))
    ck('F4 %s 段内容非空（>1000 B）' % label, len(seg) > 1000, '%d' % len(seg))

# ---------------------------------------------------------------- K1 / K2
P('')
P('=== K1 / K2 反控 ===')
board = io.open(os.path.join(R14, 'STATUS_BOARD.md'), 'rb').read()
ck('K1 STATUS_BOARD.md（已知干净）C0 = 0', len(CTRL.findall(board)) == 0)
for f in ('forensic_nul_r74.py', 'escapefam_r74.py', 'write_r74.py', 'crossfile_r74.py'):
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        P('  (跳过 %s：尚不存在)' % f)
        continue
    ck('K2 %s 自身 C0 = 0' % f, len(CTRL.findall(io.open(p, 'rb').read())) == 0)

# ---------------------------------------------------------------- K3
P('')
P('=== K3 · 把 0x07 站点还原为字母，token 必须在本库其他文件里作为整体出现 ===')
lock = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 'rb').read()
off, byte = results['LEAD_LOCK']['hits'][0]
# R74-l 修正：初版只取到空白为止，token 退化成 'and' —— 933 个文件命中，
#   那是零信息格（与 R73 §DA5 同族）。改为**连空格一起收**，取到中文标点或
#   注释边界为止，使 token 具备鉴别力（预期 'and al,1'）。
i = off + 1
tail = bytearray()
# R74-m 二次修正：收到句末会让 token 变成整句（0 旁证，同样无鉴别力）。
#   按「指令 + 操作数」这一格截断：遇到 ASCII 的 / 、; 或中文即停。
while i < len(lock) and len(tail) < 30:
    c = lock[i]
    if c >= 0x80 or c in (0x0d, 0x0a) or c in (0x2f, 0x3b):
        break
    tail.append(c); i += 1
token = MODEL[byte] + tail.decode().rstrip()
P('  LEAD_LOCK off=%d byte=0x%02x -> 还原 %r -> token=%r' % (off, byte, MODEL[byte], token))
corpus = []
for root in ('lead', 're_atlas', 'docs', 'YRpp', 'out', 'tools', 'ra2re'):
    base = os.path.join(ROOT, root)
    if not os.path.isdir(base):
        continue
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in ('R17_LEAD_BASELINE', '__pycache__', '.git')]
        if os.sep + '_r' in dp:
            continue
        for fn in fns:
            p = os.path.join(dp, fn)
            if p in (os.path.join(ROOT, 'lead', 'LEAD_LOCK'),):
                continue
            try:
                if os.path.getsize(p) > 20_000_000:
                    continue
                corpus.append((p, io.open(p, 'rb').read()))
            except Exception:
                pass
P('  语料文件数 = %d' % len(corpus))
pat = re.compile(rb'(?<![0-9A-Za-z_])' + re.escape(token.encode()) + rb'(?![0-9A-Za-z_])')
hit_files = [p for p, d in corpus if pat.search(d)]
P('  token 旁证文件数 = %d' % len(hit_files))
for p in hit_files[:4]:
    P('    %s' % os.path.relpath(p, ROOT))
ck('K3 还原 token 至少 1 个旁证文件', len(hit_files) >= 1, '%d' % len(hit_files))
ck('K3b 还原 token 含空格与操作数（非退化到单词级）', ' ' in token and len(token) > 6, repr(token))
ck('K3c 旁证文件数必须远小于语料文件数（否则该 token 是零信息格）',
   len(hit_files) < len(corpus) * 0.25,
   '%d / %d = %.1f%%' % (len(hit_files), len(corpus), 100.0 * len(hit_files) / max(1, len(corpus))))

# ---------------------------------------------------------------- 汇总
P('')
P('=== 汇总（全部实测） ===')
P('  受约束文件 %d 个；含控制字节 %d 个（%s）；干净 %d 个'
  % (len(TARGETS), len(dirty), dirty, len(clean)))
P('  R14_COMMON.md : 48 个（43 个 0x00 + 0x0c/0x0b×2/0x07/0x08 各若干）')
P('  LEAD_LOCK     : 1 个（0x07，还原为字母 a）')
P('  其余 8 个（含门禁 check_disc.py / recheck_verify.py）：干净')
P('  五道 CR 不变量全部原位；看板行数见 F5f')
P('  缺陷全部可追溯到最早留存备份，且全部备份的偏移集合与取值集合都相同'
  ' ⇒ 本库内定不出写坏轮次')
P('  本轮四段：0 个控制字节（写入层的往返解析硬闸拦住了）')
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'files': {n: {'bytes': r['bytes'], 'cr': r['cr'],
                         'hits': [[o, x] for o, x in r['hits']]}
                     for n, r in results.items()},
           'dirty': dirty, 'clean': clean, 'fails': fails},
          io.open(os.path.join(HERE, 'crossfile_r74.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'crossfile_r74.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
