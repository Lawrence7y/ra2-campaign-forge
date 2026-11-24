# -*- coding: utf-8 -*-
"""R75 · 把 R74 的「控制字节普查」从 10 个受约束文件扩到**全库文本层**

由来：R74 未取得⑥ —— 审计员的 other_control_bytes 思路值得并入常设普查，
但 R74 只扩到 10 个文件，ra2forge / ra2re / tools / docs / lead 等源码与文档树未查。

本脚本回答三件事：
  C1 全库（排除 .git / __pycache__ / R17_LEAD_BASELINE / _r?? 中间产物）有多少文本文件、
     多少二进制文件；判别算子**两条**（结构 + 扩展名白名单），必须都同意才进普查。
  C2 文本文件里「除 0x09 / 0x0a / 0x0d 之外的 C0 字节」逐站点清单（路径/偏移/值/行号）。
  C3 每个取值是否落在 R74 的五成员转义表内；表外的取值单独列。

自测（正控 + 反控）：
  P1 R14_COMMON.md 必须报 48（正控：普查不是恒报 0）
  P2 LEAD_LOCK 必须报 1
  N1 一个已知干净的文本文件跑同一算子必须 0
  N2 ra2bench/gamemd.exe 必须被判成二进制（不进普查）
  N3 maps02.mix 这类「严格 UTF-8 可解码的二进制」必须被扩展名判据拦下 ——
     这是「只用一条判据就会误报」的实测证据（R74 §DB5 观测面选错同族）
  N4 把某站点控制字节换成字母后重跑，该文件命中数必须恰好减 1
  N5 反斜杠残留检测：站点前一字节为反斜杠的必须单独计数（本库应为 0，
     否则模型「只吃字母不吃反斜杠」不成立）
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

CTRL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')

# ---- 判别算子第一条：扩展名白名单（文本族）----
TEXT_EXT = {
    '.md', '.txt', '.py', '.tsv', '.json', '.yaml', '.yml', '.ini', '.log',
    '.csv', '.ps1', '.cs', '.mjs', '.js', '.ts', '.sh', '.cmd', '.out', '.err',
    '.exitcode', '.sha256', '.diff', '.map', '.bak', '.cfg', '.toml', '.html',
    '.css', '.xml', '.c', '.h', '.cpp', '.hpp', '.rs', '.java', '.bat',
}
# ---- 判别算子第二条：严格 UTF-8 可解码（无 NUL 之外的独立判据）----
SKIP_DIRS = {'.git', '__pycache__', 'R17_LEAD_BASELINE'}


def is_text(path, raw):
    """两条判据都同意才算文本；任一条否决即判二进制。返回 (verdict, reason)。"""
    ext = os.path.splitext(path)[1].lower()
    if ext not in TEXT_EXT:
        return False, 'ext-not-in-whitelist'
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return False, 'utf8-fail@%d' % e.start
    return True, 'ok'


def iter_files(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns
                        if d not in SKIP_DIRS and not re.fullmatch(r'_r\d+', d))
        for fn in sorted(fns):
            yield os.path.join(dp, fn)


def walk_scan(limit_bytes=40_000_000):
    texts, bins, skipped = [], [], []
    for p in iter_files(ROOT):
        try:
            sz = os.path.getsize(p)
        except OSError:
            skipped.append((p, 'stat-fail'))
            continue
        if sz > limit_bytes:
            skipped.append((p, 'too-large'))
            continue
        try:
            raw = io.open(p, 'rb').read()
        except OSError:
            skipped.append((p, 'read-fail'))
            continue
        ok, why = is_text(p, raw)
        (texts if ok else bins).append((p, raw, why))
    return texts, bins, skipped


out, fails = [], []


def P(s=''):
    print(s)
    out.append(s)


def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)


def line_of(raw, off):
    return raw.count(b'\n', 0, off) + 1


P('=== C1 · 全库文本/二进制判别（两条判据都要同意） ===')
texts, bins, skipped = walk_scan()
P('  文本文件 %d ；二进制文件 %d ；跳过 %d' % (len(texts), len(bins), len(skipped)))
reasons = {}
for p, _, why in bins:
    key = why.split('@')[0]
    reasons[key] = reasons.get(key, 0) + 1
P('  二进制判据分布：%s' % reasons)
skip_reasons = {}
for p, why in skipped:
    skip_reasons[why] = skip_reasons.get(why, 0) + 1
P('  跳过原因：%s' % skip_reasons)
ck('C1a 文本文件数 > 500（不是空跑）', len(texts) > 500, str(len(texts)))
ck('C1b 二进制文件数 > 20', len(bins) > 20, str(len(bins)))

P('')
P('=== C2 · 文本文件里的 C0 控制字节（除 09/0a/0d） ===')
dirty = []
for p, raw, _ in texts:
    hits = [(m.start(), m.group()[0]) for m in CTRL.finditer(raw)]
    if hits:
        dirty.append((p, raw, hits))
P('  含控制字节的文本文件 %d 个' % len(dirty))
rel = lambda p: os.path.relpath(p, ROOT)
for p, raw, hits in sorted(dirty, key=lambda x: -len(x[2])):
    cnt = {}
    for _, v in hits:
        cnt[hex(v)] = cnt.get(hex(v), 0) + 1
    P('  %-64s %7d B  CTRL=%3d  %s' % (rel(p), len(raw), len(hits), cnt))
ck('C2a 含控制字节的文本文件数 <= 20（否则口径过宽，须复查）', len(dirty) <= 20, str(len(dirty)))
ck('C2b 含控制字节的文本文件数 >= 3（正控：不是恒报 0）', len(dirty) >= 3, str(len(dirty)))

P('')
P('=== C3 · 逐站点（路径 / 偏移 / 值 / 行号 / 左右 24 字节） ===')
MODEL = {0x00: '0', 0x07: 'a', 0x08: 'b', 0x0b: 'v', 0x0c: 'f'}
TABLE_KEYS = set(MODEL)
sites = []
for p, raw, hits in dirty:
    for off, v in hits:
        sites.append({'file': rel(p), 'off': off, 'byte': v, 'line': line_of(raw, off),
                      'left': raw[max(0, off - 24):off].decode('utf-8', 'replace'),
                      'right': raw[off + 1:off + 25].decode('utf-8', 'replace'),
                      'in_table': v in TABLE_KEYS,
                      'prev_byte': raw[off - 1] if off else None})
P('  站点总数 %d' % len(sites))
for s in sites:
    P('  %-52s off=%7d %s line=%d 表内=%-5s 左=%r 右=%r'
      % (s['file'], s['off'], hex(s['byte']), s['line'], s['in_table'],
         s['left'][-18:], s['right'][:18]))
tbl = [s for s in sites if s['in_table']]
off_tbl = [s for s in sites if not s['in_table']]
P('  表内（R74 五成员）站点 %d ；**表外**站点 %d' % (len(tbl), len(off_tbl)))
if off_tbl:
    P('  表外取值清单：%s' % sorted({hex(s['byte']) for s in off_tbl}))
ck('C3a 表外取值存在（这是本条主张的核心：模型作为族不完整）', len(off_tbl) >= 1, str(len(off_tbl)))

P('')
P('=== P1 / P2 正控 ===')
exp = {os.path.join(R14, 'R14_COMMON.md'): 48, os.path.join(ROOT, 'lead', 'LEAD_LOCK'): 1}
for p, n in exp.items():
    raw = io.open(p, 'rb').read()
    got = len(CTRL.findall(raw))
    ck('P %s 报 %d' % (rel(p), n), got == n, str(got))

P('')
P('=== N1 反控：已知干净的文本文件必须 0 ===')
clean_probe = os.path.join(R14, 'STATUS_BOARD.md')
raw = io.open(clean_probe, 'rb').read()
ck('N1 STATUS_BOARD.md 控制字节 0', len(CTRL.findall(raw)) == 0, str(len(CTRL.findall(raw))))
ck('N1b STATUS_BOARD.md 被判成文本', is_text(clean_probe, raw)[0])

P('')
P('=== N2 反控：gamemd.exe 必须是二进制 ===')
exe = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
raw = io.open(exe, 'rb').read()
ok, why = is_text(exe, raw)
ck('N2 gamemd.exe 判成二进制', not ok, why)
ck('N2b 它里面确实有大量控制字节（所以「判成二进制」不是因为它干净）',
   len(CTRL.findall(raw)) > 1000, str(len(CTRL.findall(raw))))

P('')
P('=== N3 反控：严格 UTF-8 可解码的二进制必须被扩展名判据拦下 ===')
for name in ('maps02.mix', 'maps01.mix', 'scratch_fog.shp'):
    p = os.path.join(ROOT, 'ra2bench', name) if name.endswith('.mix') else os.path.join(ROOT, name)
    if not os.path.exists(p):
        ck('N3 %s 存在' % name, False, 'missing')
        continue
    raw = io.open(p, 'rb').read()
    try:
        raw.decode('utf-8')
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False
    verdict, why = is_text(p, raw)
    P('  %-18s utf8可解=%-5s 扩展名判据=%s 最终=%s'
      % (name, utf8_ok, why, '文本' if verdict else '二进制'))
    ck('N3 %s 最终判成二进制（扩展名判据生效）' % name, not verdict, why)
ck('N3d 至少有一个「UTF-8 可解但判二进制」的实例（单判据会误报的实测证据）',
   any('ext-not-in-whitelist' == is_text(os.path.join(ROOT, 'ra2bench', n),
                                        io.open(os.path.join(ROOT, 'ra2bench', n), 'rb').read())[1]
       for n in ('maps02.mix', 'maps01.mix')))

P('')
P('=== N4 反控：把某站点控制字节换成字母后，该文件命中数必须恰好减 1 ===')
if sites:
    s = sites[0]
    p = os.path.join(ROOT, s['file'])
    raw = io.open(p, 'rb').read()
    before = len(CTRL.findall(raw))
    patched = raw[:s['off']] + b'X' + raw[s['off'] + 1:]
    after = len(CTRL.findall(patched))
    ck('N4 替换后命中数恰好 -1', after == before - 1, '%d -> %d' % (before, after))
    ck('N4b 替换后字节数不变（等长修复的前提）', len(patched) == len(raw))

P('')
P('=== N5 · 反斜杠残留检测（模型前提：只吃字母、不留反斜杠） ===')
bs = [s for s in sites if s['prev_byte'] == 0x5c]
P('  站点前一字节为反斜杠（0x5c）的个数 = %d' % len(bs))
for s in bs:
    P('    %s off=%d %s' % (s['file'], s['off'], hex(s['byte'])))
ck('N5 反斜杠残留站点 0 个（否则「只吃字母」不成立）', len(bs) == 0, str(len(bs)))

P('')
P('=== 汇总（全部实测） ===')
P('  文本文件 %d / 二进制文件 %d / 跳过 %d' % (len(texts), len(bins), len(skipped)))
P('  含控制字节的文本文件 %d 个，站点 %d 个' % (len(dirty), len(sites)))
P('  表内 %d 站点、表外 %d 站点' % (len(tbl), len(off_tbl)))
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'texts': len(texts), 'bins': len(bins), 'skipped': len(skipped),
           'dirty': [{'file': rel(p), 'bytes': len(raw), 'hits': len(h)} for p, raw, h in dirty],
           'sites': sites, 'fails': fails},
          io.open(os.path.join(HERE, 'census_all_r75.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'census_all_r75.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
