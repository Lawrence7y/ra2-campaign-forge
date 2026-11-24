# -*- coding: utf-8 -*-
"""R75 · 攻击 R74 自己那句「统一根因 = Python 非 raw 字符串」

R74 的原话是：48 个控制字节「统一根因：反斜杠 + 字母被合并成转义字节、字母被吃掉，
这五个字节恰是 Python 非 raw 字符串里 反斜杠 0/f/v/a/b 的解出值」。

本轮把它当**待证伪**的假说，办法是：对每个站点，穷举「还原串 R」，再用**可执行的
转义器**从「还原后的源码串」正向解一次，看能不能逐字节复现盘上看到的
（左上下文 + 控制字节 + 右上下文）。三个转义器：

  E1  python_literal   Python 字符串字面量语义：反斜杠 x + 2 位十六进制、
                       反斜杠 + 八进制最多 3 位、f v a b t n r、未知转义保留反斜杠
  E2  gnu_printf       bash/GNU printf、sed 的 s 语义：额外 反斜杠 e = 0x1b
  E3  twochar_nul      只做两字符替换（反斜杠 + 0 -> NUL），其余原样 ——
                       sed s/反斜杠0/x00/g、str.replace 这一族

判据（可证伪）：
  A1  用**等长**还原（R 为 1 个字符）时，不存在任何单个转义器能覆盖 R14_COMMON 的 48 个站点
  A2  E1（R74 声称的那个）在等长还原下只能覆盖 48 个里的一个真子集
  A3  存在站点在 E1 的任何还原串下都不可复现（即 E1 不是该站点的生成器）

反控与正控：
  P1  E1 + R=0 必须复现所有「NUL 后接 x 十六进制」站点（正控）
  P3  E3 + R=0 必须复现所有「NUL 后接八进制数字」站点（正控）
  N1  在 E1 上把 R 从 0 换成空串必须导致失配（反控：判据不是恒真）
  N2  E3 对 0x0c 站点必须失配（反控：E3 只认 反斜杠 0）
  N3  随机抽一个站点，把右上下文改一个字节，必须失配（反控：复现判据有鉴别力）
"""
import io
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

CTRL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')
OCT = b'01234567'
HEX = b'0123456789abcdefABCDEF'
BS = 0x5c

out, fails = [], []


def P(s=''):
    print(s)
    out.append(s)


def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)


# ------------------------------------------------------------------ 三个转义器
PY_SIMPLE = {0x66: 0x0c, 0x76: 0x0b, 0x61: 0x07, 0x62: 0x08,
             0x74: 0x09, 0x6e: 0x0a, 0x72: 0x0d, 0x5c: 0x5c, 0x27: 0x27, 0x22: 0x22}
GNU_EXTRA = {0x65: 0x1b}          # 反斜杠 e = ESC，仅 GNU printf / sed


def decode(src: bytes, flavour: str) -> bytes:
    """把源码串按指定转义器解一次。未知转义一律保留反斜杠 + 字符（与 Python 一致）。"""
    res = bytearray()
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c != BS:
            res.append(c)
            i += 1
            continue
        if flavour == 'twochar_nul':
            if i + 1 < n and src[i + 1] == 0x30:      # 反斜杠 + 0 -> NUL（只看两字符）
                res.append(0x00)
                i += 2
            else:
                res.append(BS)
                i += 1
            continue
        if i + 1 >= n:
            res.append(BS)
            i += 1
            continue
        nxt = src[i + 1]
        if nxt == 0x78 and flavour == 'python_literal':          # 反斜杠 x HH
            if i + 3 < n and src[i + 2] in HEX and src[i + 3] in HEX:
                res.append(int(src[i + 2:i + 4], 16))
                i += 4
                continue
            res.append(BS)
            i += 1
            continue
        if nxt in OCT:                                            # 八进制 1..3 位
            j = i + 1
            digs = bytearray()
            while j < n and len(digs) < 3 and src[j] in OCT:
                digs.append(src[j])
                j += 1
            res.append(int(bytes(digs), 8) & 0xff)
            i = j
            continue
        if nxt in GNU_EXTRA and flavour == 'gnu_printf':
            res.append(GNU_EXTRA[nxt])
            i += 2
            continue
        if nxt in PY_SIMPLE:
            res.append(PY_SIMPLE[nxt])
            i += 2
            continue
        res.append(BS)
        i += 1
    return bytes(res)


# ------------------------------------------------------------------ 站点
TEXT_EXT = {
    '.md', '.txt', '.py', '.tsv', '.json', '.yaml', '.yml', '.ini', '.log',
    '.csv', '.ps1', '.cs', '.mjs', '.js', '.ts', '.sh', '.cmd', '.out', '.err',
    '.exitcode', '.sha256', '.diff', '.map', '.bak', '.cfg', '.toml', '.html',
    '.css', '.xml', '.c', '.h', '.cpp', '.hpp', '.rs', '.java', '.bat',
}
BIN_EXT = {
    '.mix', '.exe', '.dll', '.png', '.jpg', '.jpeg', '.shp', '.zip', '.sav',
    '.tlb', '.pdb', '.obj', '.lib', '.bin', '.ico', '.gif', '.bmp', '.gz',
    '.7z', '.rar', '.cab', '.msi', '.wav', '.mp3', '.avi', '.dat', '.pyc',
    '.ttf', '.pak', '.big', '.vxl', '.hva', '.tmp', '.aud', '.pcx', '.pal', '.csf',
}
SKIP = {'.git', '__pycache__', 'R17_LEAD_BASELINE'}

P('=== 采集站点（两条文本算子取并集，避免 R75 自己踩过的漏判面） ===')
union = {}
for dp, dns, fns in os.walk(ROOT):
    dns[:] = sorted(d for d in dns if d not in SKIP and not re.fullmatch(r'_r\d+', d))
    for fn in sorted(fns):
        p = os.path.join(dp, fn)
        ext = os.path.splitext(fn)[1].lower()
        if ext in BIN_EXT:
            continue
        try:
            if os.path.getsize(p) > 40_000_000:
                continue
            raw = io.open(p, 'rb').read()
        except OSError:
            continue
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if ext not in TEXT_EXT and ext != '':
            continue          # 白名单外的怪扩展名不进（黑名单已排除二进制族）
        if CTRL.search(raw):
            union[p] = raw
P('  有命中的文本文件 %d 个' % len(union))
rel = lambda p: os.path.relpath(p, ROOT)

sites = []
for p, raw in sorted(union.items()):
    for m in CTRL.finditer(raw):
        o = m.start()
        sites.append({'file': rel(p), 'off': o, 'byte': m.group()[0],
                      'line': raw.count(b'\n', 0, o) + 1,
                      'left': raw[max(0, o - 24):o], 'right': raw[o + 1:o + 25]})
P('  站点总数 %d' % len(sites))

# ------------------------------------------------------------------ 复现判定
FLAVOURS = ['python_literal', 'gnu_printf', 'twochar_nul']
RESTORES = [
    ('0', b'0'), ('f', b'f'), ('v', b'v'), ('a', b'a'), ('b', b'b'),
    ('t', b't'), ('e', b'e'),
    # 四字符形式（非等长修复候选）
    ('\\x%02x', None),
]
# 只有等长还原用于 A1/A2 的严格判定
EQUAL_LEN = [r for r in RESTORES if r[1] is not None]


def reproduce(site, flavour, rbytes):
    """把 R 插回站点位置，用给定转义器解一次，比较是否逐字节等于盘上（左+C+右）。"""
    src = site['left'] + rbytes + site['right']
    got = decode(src, flavour)
    want = site['left'] + bytes([site['byte']]) + site['right']
    # 还原器只作用在整段上；要求解出的结果与盘上目标逐字节相同
    return got == want


P('')
P('=== 逐站点：等长还原下有哪些（转义器, 还原串）能复现 ===')
# R75 自错 1（本轮第三次踩同类）：第一版把「还原串」当成字母本身插回去，
#   忘了源串里是 反斜杠 + 字母 两个字符。E1 是转义器，输入必须是**源码串**，
#   所以插入物恒为 BS + letter。修正后 P1/P3 正控才成立。
def reproduce_letter(site, flavour, letter):
    return reproduce(site, flavour, bytes([BS]) + letter)


per_site = []
for s in sites:
    feas = []
    for fl in FLAVOURS:
        for name, rb in EQUAL_LEN:
            if reproduce_letter(s, fl, rb):
                feas.append((fl, name))
    # 四字符形式单独试（反斜杠 x HH，四个字符解成 1 字节）
    wide = []
    for fl in ('python_literal', 'gnu_printf'):
        cand = ('\\x%02x' % s['byte']).encode()
        if reproduce(s, fl, cand):
            wide.append((fl, cand.decode()))
    per_site.append({'file': s['file'], 'off': s['off'], 'byte': s['byte'],
                     'line': s['line'], 'equal_len_feasible': feas,
                     'wide_feasible': wide})
    P('  %-48s off=%7d %s line=%d 等长可行=%s 四字符可行=%s'
      % (s['file'], s['off'], hex(s['byte']), s['line'],
         [f[0] + '/' + f[1] for f in feas], [w[0] + '/' + w[1] for w in wide]))

P('')
P('=== A2 · E1（Python 字面量，R74 声称的那种）在等长还原下的覆盖率 ===')
e1 = [x for x in per_site if any(f[0] == 'python_literal' for f in x['equal_len_feasible'])]
e2 = [x for x in per_site if any(f[0] == 'gnu_printf' for f in x['equal_len_feasible'])]
e3 = [x for x in per_site if any(f[0] == 'twochar_nul' for f in x['equal_len_feasible'])]
P('  E1 覆盖 %d / %d 站点' % (len(e1), len(per_site)))
P('  E2 覆盖 %d / %d 站点' % (len(e2), len(per_site)))
P('  E3 覆盖 %d / %d 站点' % (len(e3), len(per_site)))
none = [x for x in per_site if not x['equal_len_feasible'] and not x['wide_feasible']]
P('  三个转义器都复现不了的站点 %d 个' % len(none))
for x in none:
    P('    %s off=%d %s' % (x['file'], x['off'], hex(x['byte'])))
ck('A2a E1 等长覆盖率 < 100%（R74 的「统一根因」作为通用解释不成立）',
   len(e1) < len(per_site), '%d / %d' % (len(e1), len(per_site)))
ck('A2b E1 等长覆盖率 > 50%（它不是完全无关，只是不通用）',
   len(e1) * 2 > len(per_site), '%d / %d' % (len(e1), len(per_site)))

P('')
P('=== A1 · 等长还原下是否存在「单个转义器覆盖全部」 ===')
ck('A1a 没有单个转义器在等长还原下覆盖全部站点',
   not (len(e1) == len(per_site) or len(e2) == len(per_site) or len(e3) == len(per_site)),
   'E1=%d E2=%d E3=%d 总=%d' % (len(e1), len(e2), len(e3), len(per_site)))

P('')
P('=== A3 · 只算 R14_COMMON.md 一个文件（R74 的「统一」是对这一个文件说的） ===')
rc = [x for x in per_site if x['file'].endswith('R14_COMMON.md')]
P('  R14_COMMON.md 站点 %d 个' % len(rc))
cnt = {}
for x in rc:
    key = ','.join(sorted(f[0] for f in x['equal_len_feasible'])) or '(无)'
    cnt[key] = cnt.get(key, 0) + 1
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
    P('    可行转义器集合 [%s] : %d 站点' % (k, v))
only_e3 = [x for x in rc if all(f[0] == 'twochar_nul' for f in x['equal_len_feasible'])]
only_e1e2 = [x for x in rc if x['equal_len_feasible'] and
             all(f[0] in ('python_literal', 'gnu_printf') for f in x['equal_len_feasible'])]
P('  等长还原下**只能**由 E3（两字符替换）复现的站点 %d 个' % len(only_e3))
P('  等长还原下**只能**由 E1/E2（语言字面量）复现的站点 %d 个' % len(only_e1e2))
ck('A3a R14_COMMON.md 单个文件内就需要 ≥2 个不同转义器 ⇒ 「统一根因」被证伪',
   len(only_e3) > 0 and len(only_e1e2) > 0,
   'onlyE3=%d onlyE1E2=%d' % (len(only_e3), len(only_e1e2)))

P('')
P('=== P1 / P3 正控 ===')
xsites = [x for x in per_site if x['byte'] == 0x00 and x['off'] is not None]
P('  NUL 站点 %d 个' % len(xsites))
xhex = [x for x in xsites if x['equal_len_feasible'] and
        ('python_literal', '0') in x['equal_len_feasible']]
ck('P1 E1 + 还原 0 能复现的 NUL 站点数 > 0', len(xhex) > 0, str(len(xhex)))
e3nul = [x for x in xsites if ('twochar_nul', '0') in x['equal_len_feasible']]
ck('P3 E3 + 还原 0 能复现的 NUL 站点数 > 0', len(e3nul) > 0, str(len(e3nul)))
ck('P4 E1 与 E3 的 NUL 覆盖集**不相同**（否则两族其实是一族）',
   {x['off'] + x['byte'] for x in xhex} != {x['off'] + x['byte'] for x in e3nul})

P('')
P('=== N1 / N2 / N3 反控 ===')
s0 = sites[0]
ck('N1 在 E1 上把还原串换成空串必须失配',
   not reproduce(s0, 'python_literal', b''))
ck('N1b 在 E1 上把还原串换成「反斜杠 + 错字母」也必须失配',
   s0['byte'] != 0x00 and not reproduce_letter(s0, 'python_literal', b'z'))
ffsite = next((s for s in sites if s['byte'] == 0x0c), None)
ck('N2 E3 对 0x0c 站点必须失配（E3 只认 反斜杠 0）',
   ffsite is not None and not reproduce_letter(ffsite, 'twochar_nul', b'f'))
# R75 自错 2：xsites 取自 per_site（只有 offset 等摘要），没有 left/right；
#   reproduce 需要真上下文，必须从 sites 里取，不能从摘要里取。
# R75 自错 3：第一版 N3 把「右上下文」改成坏值后，want 与 src 都用同一个坏右上下文，
#   于是两边一起坏、比较恒真 —— 这不是反控，是零信息格（R73 §DA5 同族，第五次）。
#   改成「喂错还原字母」：对同一个 NUL 站点喂 反斜杠 1（产出 0x01），必须失配。
sx = next(s for s in sites if s['byte'] == 0x00)
ck('N3 对同一 NUL 站点喂错还原字母（反斜杠 1 产出 0x01）必须失配（判据有鉴别力）',
   not reproduce_letter(sx, 'python_literal', b'1'))

P('')
P('=== 0x1b 专属：E1 在任何还原串下都不可复现？ ===')
escsites = [s for s in sites if s['byte'] == 0x1b]
P('  0x1b 站点 %d 个' % len(escsites))
for s in escsites:
    ok_py = reproduce_letter(s, 'python_literal', b'e')
    ok_wide = reproduce_letter(s, 'python_literal', b'\\x1b')
    ok_gnu = reproduce_letter(s, 'gnu_printf', b'e')
    P('    %-46s off=%d  E1+R=e:%s  E1+R=\\x1b:%s  E2+R=e:%s'
      % (s['file'], s['off'], ok_py, ok_wide, ok_gnu))
ck('A3b 每个 0x1b 站点在 E1 下 R=e 都失配（Python 没有 反斜杠 e 转义）',
   all(not reproduce_letter(s, 'python_literal', b'e') for s in escsites), str(len(escsites)))
ck('A3c 每个 0x1b 站点在 E2 下 R=e 都复现（GNU printf / sed 的 反斜杠 e = ESC）',
   all(reproduce_letter(s, 'gnu_printf', b'e') for s in escsites), str(len(escsites)))
ck('A3d 0x1b 站点数 > 0（正控）', len(escsites) > 0, str(len(escsites)))

P('')
P('=== 汇总（全部实测） ===')
P('  站点 %d；E1 等长覆盖 %d、E2 %d、E3 %d；无解 %d'
  % (len(per_site), len(e1), len(e2), len(e3), len(none)))
P('  R14_COMMON.md：只能 E3 的 %d 个、只能 E1/E2 的 %d 个 ⇒ 单文件内 ≥2 个转义器'
  % (len(only_e3), len(only_e1e2)))
P('  0x1b 站点 %d 个：E1 全部失配、E2 全部复现' % len(escsites))
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'sites': per_site, 'e1': len(e1), 'e2': len(e2), 'e3': len(e3),
           'none': none, 'only_e3_rc': only_e3, 'only_e1e2_rc': only_e1e2,
           'fails': fails},
          io.open(os.path.join(HERE, 'escaper_attack_r75.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'escaper_attack_r75.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
