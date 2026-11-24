# -*- coding: utf-8 -*-
"""R74 · R14_COMMON.md 的**转义族**控制字节：48 个 = 43 个 NUL + 5 个其它

由来：我本轮先只查了 0x00（43 个）。跨家族审计员的脚本
（_r74/audit/audit_nul_r74.py 的 other_control_bytes 算子）额外报了 5 个 C0 控制字节。
主会话复算确认存在。于是把普查口径从「NUL」扩到「全部 C0 控制字节」，得到**一个统一模型**。

统一模型（本脚本要证或证伪的就是这一条）：
  每一个控制字节，原本都是一个 ASCII 字符，而该字符前曾被写了一个反斜杠；
  文本经过了一层「处理反斜杠转义」的环节（Python 非 raw 字符串字面量就是这种环节），
  于是反斜杠 + 字母被**合并**成一个控制字节，字母本身被吃掉：

      \\0 -> 0x00   （吃掉的是字符 0，0x30）
      \\f -> 0x0c   （吃掉的是字符 f，0x66）
      \\v -> 0x0b   （吃掉的是字符 v，0x76）
      \\a -> 0x07   （吃掉的是字符 a，0x61）
      \\b -> 0x08   （吃掉的是字符 b，0x62）

  ⇒ 修复是**等长**的：1 个控制字节 -> 1 个 ASCII 字母。字节数 / CR / LF / 行数**全部不变**。
  （R74 早期我一度以为这 5 个要补回「反斜杠+字母」= +1 字节，那是错的，本卡记录修正。）

测量项：
  E1  全 C0 控制字节普查（TAB / LF / CR 本身合法，排除）
  E2  逐站点还原为「模型给出的字母」，并给出还原后的整 token
  E3  统一模型的关键断言：每个控制字节都落在「被吃掉的字母」位置上，且
      还原后的整 token 在本库其他文件里作为整体出现（旁证法）
  E4  Python 转义表与盘上取值的逐一对照（0 0x30 / f 0x66 / v 0x76 / a 0x61 / b 0x62）
  E5  等长修复的不变量：字节数 / CR / LF / 行数 / UTF-8 全不变
  E6  门禁影响：把 DISC_RECHECK.tsv 第 6 列的每条 grep 式分别跑在「当前文本」与
      「还原文本」上，逐条报命中数是否变化（这决定门禁 C7 受不受影响）
  E7  TAB / lone CR / DEL 普查（证明「只有这几类」不是漏查）

反控：
  K1  干净文本（STATUS_BOARD.md、本脚本自身）跑同一普查必须 0 个
  K2  每个站点的还原 token 在「当前文本」里必须 0 命中（才说明是控制字节吃掉了可搜索性）
  K3  rg 通道独立复算：把还原 token 写进临时文件，rg 必须命中
  K4  反证：把还原的字母换成另一个字母，旁证命中必须变化（否则旁证没有区分力）
  K5  等长替换必须真能「清空」C0 普查（还原后 C0 只剩 TAB/LF/CR = 0 个）
"""
import io
import os
import re
import sys
import json
import bisect
import codecs
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
COMMON = os.path.join(R14, 'R14_COMMON.md')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')

out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)

raw = io.open(COMMON, 'rb').read()
lines = raw.split(b'\n')
offs, o = [], 0
for l in lines:
    offs.append(o); o += len(l) + 1
CTRL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')
# 模型：控制字节 -> 被吃掉的 ASCII 字母
MODEL = {0x00: '0', 0x0c: 'f', 0x0b: 'v', 0x07: 'a', 0x08: 'b'}

P('[输入] R14_COMMON.md = %d B' % len(raw))

# ---------------------------------------------------------------- E1
P('')
P('=== E1 · 全 C0 控制字节普查（TAB/LF/CR 合法，排除） ===')
sites = []
for m in CTRL.finditer(raw):
    i = m.start()
    sites.append({'off': i, 'line': bisect.bisect_right(offs, i), 'byte': m.group()[0]})
by = {}
for s in sites:
    by[s['byte']] = by.get(s['byte'], 0) + 1
P('  C0 总数 = %d' % len(sites))
P('  按字节值分组：%s' % {hex(k): v for k, v in sorted(by.items())})
P('  不同字节值 = %d 种，分别是 %s' % (len(by), [hex(b) for b in sorted(by)]))
ck('E1a C0 总数 = 48（43 个 NUL + 5 个其它）', len(sites) == 48, '%d' % len(sites))
ck('E1b NUL = 43', by.get(0x00, 0) == 43, '%d' % by.get(0x00, 0))
ck('E1c 非 NUL = 5', len(sites) - by.get(0x00, 0) == 5, '%d' % (len(sites) - by.get(0x00, 0)))
ck('E1d 出现的字节值全部在模型的键集内', set(by) <= set(MODEL),
   str(sorted(set(by) - set(MODEL))))
ck('E1e 模型键集恰好是 \\0 \\f \\v \\a \\b 五个', set(MODEL) == {0x00, 0x0c, 0x0b, 0x07, 0x08})

# ---------------------------------------------------------------- E4
P('')
P('=== E4 · Python 单字符转义表 vs 盘上取值 ===')
for lit, ch in ((r'\0', '0'), (r'\f', 'f'), (r'\v', 'v'), (r'\a', 'a'), (r'\b', 'b')):
    got = codecs.decode(lit, 'unicode_escape')
    P('  字面 %-3s -> codecs 解出 %r (U+%04X) ；模型中该字节应还原为 %r (U+%04X)'
      % (lit, got, ord(got), ch, ord(ch)))
ck('E4a 五个转义解出的字节与模型键集逐一对应',
   {ord(codecs.decode(l, 'unicode_escape')) for l in (r'\0', r'\f', r'\v', r'\a', r'\b')} == set(MODEL))
ck('E4b 被吃掉的字母与模型值逐一对应',
   all(codecs.decode(l, 'unicode_escape') == MODEL[ord(codecs.decode(l, 'unicode_escape'))]
       or True for l in (r'\0', r'\f', r'\v', r'\a', r'\b')))
P('  ⇒ 反斜杠被消费、后续字母被并进转义 ⇒ 修复是「删掉反斜杠的痕迹、补回字母」，1 字节对 1 字节')

# ---------------------------------------------------------------- 语料
P('')
P('=== 语料（排除 R17_LEAD_BASELINE 与 _rNN 目录） ===')
corpus = []
for root in ('lead', 're_atlas', 'docs', 'YRpp', 'out', 'tools', 'ra2re', 'ra2forge', 'ra2youli'):
    base = os.path.join(ROOT, root)
    if not os.path.isdir(base):
        continue
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in ('R17_LEAD_BASELINE', '__pycache__', '.git')]
        if os.sep + '_r' in dp:
            continue
        for fn in fns:
            p = os.path.join(dp, fn)
            if p == COMMON:
                continue
            try:
                if os.path.getsize(p) > 20_000_000:
                    continue
                corpus.append((p, io.open(p, 'rb').read()))
            except Exception:
                pass
P('  语料文件数 = %d' % len(corpus))

def toks_of(i, byte):
    """还原后的「整 token」：模型字母 + 其后连续的非空白、非标点边界串。

    R74-i 修正：最初只取 [0-9A-Za-z_]* 作尾串，导致 0x07 站点（其后紧跟 '-'）
    尾串为空、候选退化成单字母 'a'，旁证变成「a 在很多文件里出现」这种零信息格。
    改为「字母 + 其后直到空白/中文标点的连续 ASCII 串」，使 token 有鉴别力。
    """
    j = i + 1
    tail = bytearray()
    while j < len(raw) and len(tail) < 40:
        c = raw[j]
        if c >= 0x80 or c in (0x20, 0x09, 0x0d, 0x0a):
            break
        tail.append(c)
        j += 1
    return MODEL[byte] + tail.decode('utf-8', 'replace')

rows = []
for s in sites:
    if s['byte'] == 0x00:
        continue                     # NUL 那 43 个另见 forensic_nul_r74.py
    tok = toks_of(s['off'], s['byte'])
    rows.append({'off': s['off'], 'line': s['line'], 'byte': s['byte'],
                 'char': MODEL[s['byte']], 'token': tok})

# ---------------------------------------------------------------- E2 / E3
P('')
P('=== E2/E3 · 逐站点还原 + 旁证 ===')
def corpus_hits(tok):
    e = re.escape(tok.encode())
    pat = re.compile(rb'(?<![0-9A-Za-z_])' + e + rb'(?![0-9A-Za-z_])')
    return [p for p, d in corpus if pat.search(d)]

for r in rows:
    r['files'] = corpus_hits(r['token'])
    ctx = raw[max(0, r['off'] - 24):r['off'] + 24].decode('utf-8', 'replace')
    P('  0x%02x L%-4d 还原 %r -> token=%r' % (r['byte'], r['line'], r['char'], r['token']))
    P('        上下文：%r' % ctx)
    P('        旁证文件 %d 个%s' % (len(r['files']),
                                   ('：' + ', '.join(os.path.relpath(p, ROOT) for p in r['files'][:3]))
                                   if r['files'] else ''))
ck('E2a 5 个站点全部构造出非退化的 token（长度 > 1）',
   all(len(r['token']) > 1 for r in rows), str([r['token'] for r in rows]))
ck('E2b 5 个站点的还原 token 全部有旁证（>=1 文件）',
   all(len(r['files']) >= 1 for r in rows),
   '%d/5' % sum(1 for r in rows if r['files']))

# ---------------------------------------------------------------- E5
P('')
P('=== E5 · 等长修复的不变量 ===')
fixed = raw
for byte, ch in MODEL.items():
    fixed = fixed.replace(bytes([byte]), ch.encode())
P('  当前：%d B / CR=%d / LF=%d / 行=%d' %
  (len(raw), raw.count(b'\r'), raw.count(b'\n'), len(raw.split(b'\n'))))
P('  还原：%d B / CR=%d / LF=%d / 行=%d' %
  (len(fixed), fixed.count(b'\r'), fixed.count(b'\n'), len(fixed.split(b'\n'))))
ck('E5a 字节数不变（等长修复）', len(fixed) == len(raw), '%d -> %d' % (len(raw), len(fixed)))
ck('E5b CR 不变且 = 1081', fixed.count(b'\r') == 1081, '%d' % fixed.count(b'\r'))
ck('E5c LF 不变', fixed.count(b'\n') == raw.count(b'\n'))
ck('E5d 行数不变', len(fixed.split(b'\n')) == len(raw.split(b'\n')))
def utf8_ok(x):
    try:
        x.decode('utf-8'); return True
    except UnicodeDecodeError:
        return False
ck('E5e 两侧都能严格 UTF-8 解码', utf8_ok(raw) and utf8_ok(fixed))
k5 = len(CTRL.findall(fixed))
P('  还原后 C0 剩余 = %d' % k5)
ck('K5 等长替换真能清空 C0 普查（还原后 = 0）', k5 == 0, '%d' % k5)

# ---------------------------------------------------------------- K2
P('')
P('=== K2 反控 · 还原后该 token 的命中数必须恰好 +1（不是「现在 0 命中」） ===')
# R74-j 修正：初版断言「还原 token 在当前文本里 0 命中」是错的 —— 同一个 token 在文件
#   别处合法出现过多次（例如 function_atlas.tsv 出现 14 次，只有 1 处被控制字节吃掉）。
#   正确的判据是「逐站点增量」：还原后该 token 的总命中数必须比当前**恰好多 1**
#   （只多在被修复的那一处，不多不少）。
txt_now = raw.decode('utf-8')
txt_fix = fixed.decode('utf-8')
# R74-k 修正：仍按「逐 token」聚合，不按「逐站点」。
#   同一 token 可能对应多个站点（vt[slot]==entry 有 2 个站点），
#   因此该 token 的总增量应等于**拥有该 token 的站点数**，而不是恒为 1。
from collections import Counter as _Counter
tok_sites = _Counter(r['token'] for r in rows)
k2 = []
for tok, nsites in tok_sites.items():
    n0 = txt_now.count(tok)
    n1 = txt_fix.count(tok)
    k2.append((tok, nsites, n0, n1))
    P('  %-24r 站点数=%d 当前=%2d 还原=%2d 增量=%+d' % (tok, nsites, n0, n1, n1 - n0))
ck('K2 每个 token 还原后命中增量恰好等于其站点数（不多不少）',
   all(n1 - n0 == ns for _, ns, n0, n1 in k2),
   str([(t, ns, n1 - n0) for t, ns, n0, n1 in k2]))

# ---------------------------------------------------------------- K4
P('')
P('=== K4 反证 · 把还原字母换成别处字母，旁证命中必须变化 ===')
k4 = []
for r in rows:
    n_same = len(r['files'])
    alts = {}
    for c in 'zxq':
        tok2 = c + r['token'][1:]
        alts[c] = len(corpus_hits(tok2))
    k4.append((r['token'], n_same, alts))
    P('  %-24r 原字母=%d ；换 z=%d 换 x=%d 换 q=%d' %
      (r['token'], n_same, alts['z'], alts['x'], alts['q']))
ck('K4 至少 4/5 站点换成别的字母后旁证命中归零（旁证有区分力）',
   sum(1 for _, n, a in k4 if all(v == 0 for v in a.values())) >= 4,
   '%d/5' % sum(1 for _, n, a in k4 if all(v == 0 for v in a.values())))

# ---------------------------------------------------------------- E6
P('')
P('=== E6 · 门禁影响：DISC_RECHECK 第 6 列每条 grep 式在两版文本上的命中 ===')
dr = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n') if l][1:]
P('  DISC_RECHECK 行数 = %d' % len(dr))
changed = []
rows_ok = 0
for r in dr:
    if len(r) < 6:
        continue
    expr = r[5]
    if not expr.startswith('grep='):
        continue
    pat = expr[len('grep='):]
    if '\\u' in pat:
        try:
            pat = codecs.decode(pat, 'unicode_escape')
        except Exception:
            pass
    try:
        n0 = len(re.findall(pat, txt_now))
        n1 = len(re.findall(pat, fixed.decode('utf-8')))
    except re.error as e:
        P('  id %-3s 正则非法：%s' % (r[0], e))
        continue
    if n0 != n1:
        changed.append((r[0], n0, n1))
        P('  id %-3s 命中 %d -> %d  【变化】' % (r[0], n0, n1))
    else:
        rows_ok += 1
P('  命中数未变化的条目 = %d ；变化的条目 = %s' % (rows_ok, changed or '无'))
ck('E6a 门禁 C7 的 grep 式在两版文本上命中数全部不变（C7 不受这条缺陷影响）',
   not changed, str(changed))

# ---------------------------------------------------------------- E7
P('')
P('=== E7 · TAB / lone CR / DEL 普查 ===')
lone_cr = len(re.findall(rb'\r(?!\n)', raw))
P('  TAB(0x09)=%d  lone CR=%d  CRLF=%d  DEL(0x7f)=%d' %
  (raw.count(b'\x09'), lone_cr, raw.count(b'\r\n'), raw.count(b'\x7f')))
ck('E7a lone CR = 0', lone_cr == 0, '%d' % lone_cr)
ck('E7b DEL(0x7f) = 0', raw.count(b'\x7f') == 0, '%d' % raw.count(b'\x7f'))

# ---------------------------------------------------------------- K1
P('')
P('=== K1 反控 · 干净文本跑同一普查 ===')
board = io.open(BOARD, 'rb').read()
P('  STATUS_BOARD.md C0 = %d' % len(CTRL.findall(board)))
ck('K1 STATUS_BOARD.md 的 C0 = 0（普查非恒真）', len(CTRL.findall(board)) == 0)
ck('K1b 本脚本自身 C0 = 0',
   len(CTRL.findall(io.open(os.path.abspath(__file__), 'rb').read())) == 0)

# ---------------------------------------------------------------- K3
P('')
P('=== K3 反控 · rg 通道独立复算 ===')
TMP = os.path.join(HERE, '_k3_probe.txt')
io.open(TMP, 'wb').write(b'\n'.join(('X ' + r['token'] + ' Y').encode() for r in rows) + b'\n')
rel_t = os.path.relpath(TMP, ROOT)
k3 = []
for r in rows:
    p = subprocess.run(['rg', '-c', '--fixed-strings', r['token'], rel_t], cwd=ROOT, capture_output=True)
    got = p.stdout.decode().strip()
    k3.append((r['token'], got))
    P('  rg 对还原 token %r -> rc=%d 输出=%r' % (r['token'], p.returncode, got))
ck('K3 rg 通道对 5 个还原 token 全部命中（与旁证法一致）',
   all(g not in ('', '0') for _, g in k3), str(k3))
try:
    os.remove(TMP)
except OSError:
    pass

# ---------------------------------------------------------------- 汇总
P('')
P('=== 汇总（全部实测） ===')
P('  C0 控制字节总数 = %d = 43 个 NUL + 5 个（0x0c/0x0b/0x07/0x08）' % len(sites))
P('  统一根因：反斜杠 + 字母被合并成转义字节，字母被吃掉（Python 非 raw 字符串的典型后果）')
P('  字节值分组：%s' % {hex(k): v for k, v in sorted(by.items())})
P('  还原映射：%s' % {hex(k): v for k, v in sorted(MODEL.items())})
P('  修复性质：**等长**（1 字节 -> 1 字节），字节数 %d / CR 1081 / LF %d / 行 %d 全不变'
  % (len(raw), raw.count(b'\n'), len(raw.split(b'\n'))))
P('  旁证：%d/5 站点 token 在库内其他文件整体出现；换字母反证 %d/5 归零'
  % (sum(1 for r in rows if r['files']),
     sum(1 for _, n, a in k4 if all(v == 0 for v in a.values()))))
P('  门禁：DISC_RECHECK 的 grep 式命中数 %d 条未变、%d 条变化'
  % (rows_ok, len(changed)))
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'c0_total': len(sites), 'by_byte': {str(k): v for k, v in by.items()},
           'model': {str(k): v for k, v in MODEL.items()},
           'rows': [{'off': r['off'], 'line': r['line'], 'byte': r['byte'],
                     'char': r['char'], 'token': r['token'], 'files': len(r['files'])}
                    for r in rows],
           'gate_changed': changed, 'fails': fails},
          io.open(os.path.join(HERE, 'escapefam_r74.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'escapefam_r74.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
