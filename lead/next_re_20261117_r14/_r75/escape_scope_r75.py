# -*- coding: utf-8 -*-
"""R75 · 转义族普查的**观测面**重做：R74 的三处观测面缺口

R74 结论是「R14_COMMON.md 有 48 个 C0 控制字节，5 个取值同属一个转义族」，
但它至少有三处观测面缺口，本轮全部实测：

  G1  R74 的判据是「除 0x09/0x0a/0x0d 之外的 C0」⇒ **0x09 TAB 被当成合法字符排除**。
      而 Python 转义里 反斜杠 t 与 反斜杠 11 都产出 0x09 ⇒ 族里有成员的字节值恰好落在
      「合法」区，**控制字节普查对它结构上无感**。
  G2  R74 的普查扩到 10 个受约束文件，其中 LEAD_LOCK 是靠直接点名进列表的。
      换成一个「扩展名白名单」算子时，LEAD_LOCK（无扩展名）会被判成二进制而**整份漏掉** ——
      本轮我自己写了这个算子，就漏了。两条算子（白名单 / 黑名单）必须都跑并报差异集。
  G3  R74 说「rg 把文件判成 binary」，但实测只有 **0x00** 触发 binary 判定；
      0x0c / 0x1b / 0x01 / 0x06 都不触发。⇒ 「rg 判 binary」不是族成员的通性，
      只是 NUL 成员的性质。这句话必须收窄。

本脚本不修任何文件，只测量。输出：
  _r75/escape_scope_r75.log / .json
"""
import io
import os
import re
import sys
import json
import subprocess
import tempfile
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

CTRL_STRICT = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')   # R74 的判据（排除 09/0a/0d）
CTRL_WIDE = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f\x09]')  # 本轮加回 TAB

TEXT_WHITELIST = {
    '.md', '.txt', '.py', '.tsv', '.json', '.yaml', '.yml', '.ini', '.log',
    '.csv', '.ps1', '.cs', '.mjs', '.js', '.ts', '.sh', '.cmd', '.out', '.err',
    '.exitcode', '.sha256', '.diff', '.map', '.bak', '.cfg', '.toml', '.html',
    '.css', '.xml', '.c', '.h', '.cpp', '.hpp', '.rs', '.java', '.bat',
}
BIN_BLACKLIST = {
    '.mix', '.exe', '.dll', '.png', '.jpg', '.jpeg', '.shp', '.zip', '.sav',
    '.tlb', '.pdb', '.obj', '.lib', '.bin', '.ico', '.gif', '.bmp', '.gz',
    '.7z', '.rar', '.cab', '.msi', '.wav', '.mp3', '.avi', '.dat', '.pyc',
    '.ttf', '.pak', '.big', '.vxl', '.hva', '.tmp', '.aud', '.pcx', '.pal', '.csf',
}
SKIP_DIRS = {'.git', '__pycache__', 'R17_LEAD_BASELINE'}

out, fails = [], []


def P(s=''):
    print(s)
    out.append(s)


def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)


def iter_files(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns
                        if d not in SKIP_DIRS and not re.fullmatch(r'_r\d+', d))
        for fn in sorted(fns):
            yield os.path.join(dp, fn)


def op_whitelist(path, raw):
    if os.path.splitext(path)[1].lower() not in TEXT_WHITELIST:
        return False, 'ext-not-in-whitelist'
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return False, 'utf8-fail@%d' % e.start
    return True, 'ok'


def op_blacklist(path, raw):
    if os.path.splitext(path)[1].lower() in BIN_BLACKLIST:
        return False, 'ext-in-blacklist'
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return False, 'utf8-fail@%d' % e.start
    return True, 'ok'


def scan(op):
    texts, bins = [], []
    for p in iter_files(ROOT):
        try:
            if os.path.getsize(p) > 40_000_000:
                bins.append(p)
                continue
            raw = io.open(p, 'rb').read()
        except OSError:
            bins.append(p)
            continue
        ok, why = op(p, raw)
        (texts if ok else bins).append((p, raw, why))
    return texts, bins


# ------------------------------------------------------------------ G2
P('=== G2 · 两条文本算子必须都跑，差异集就是漏判面 ===')
tA, bA = scan(op_whitelist)
tB, bB = scan(op_blacklist)
setA = {p for p, _, _ in tA}
setB = {p for p, _, _ in tB}
P('  算子 A（扩展名白名单）: 文本 %d / 二进制 %d' % (len(tA), len(bA)))
P('  算子 B（扩展名黑名单）: 文本 %d / 二进制 %d' % (len(tB), len(bB)))
onlyB = sorted(setB - setA)
P('  只在 B 里判成文本的文件 %d 个（= A 的漏判面）' % len(onlyB))
lock_abs = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
rel = lambda p: os.path.relpath(p, ROOT)
for p in onlyB[:12]:
    P('    %s' % rel(p))
ck('G2a 算子 A 把 LEAD_LOCK 判成二进制（这是我本轮自己犯的漏判，必须显式记）',
   lock_abs not in setA)
ck('G2b 算子 B 把 LEAD_LOCK 判成文本', lock_abs in setB)
ck('G2c 差异集非空 ⇒ 单算子普查不可用', len(onlyB) > 0, str(len(onlyB)))

# 并集普查
union = {}
for p, raw, _ in tA + tB:
    union[p] = raw
P('  并集文本文件数 = %d' % len(union))

# ------------------------------------------------------------------ G1 族映射表
P('')
P('=== G1 · 转义族的完整映射表（用 exec 实测，不靠记忆） ===')
BS = chr(92)
tails = ['0', '1', '2', '3', '6', '7', '8', '11', '12', '15', '33', '101',
         't', 'n', 'r', 'f', 'v', 'a', 'b', 'e', 'x01', 'x06', 'e3', 'errors',
         'frac', 'text{', '0x47', 'fired=0']
mapping = {}
for tail in tails:
    src = "s='" + BS + tail + "'"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        ns = {}
        try:
            exec(src, ns)
            got = ns['s']
        except SyntaxError:
            got = None
    warn = [x.category.__name__ for x in w]
    if got is None:
        mapping[tail] = {'produces': 'SyntaxError', 'warn': warn}
        continue
    if len(got) == 1:
        v = ord(got)
        mapping[tail] = {'produces': v, 'eaten': len(tail), 'warn': warn}
    else:
        mapping[tail] = {'produces': None, 'literal': got, 'warn': warn}
P('  %-10s %-10s %-6s %s' % ('反斜杠+尾', '产出', '吃掉', '语法警告'))
for tail in tails:
    m = mapping[tail]
    prod = m['produces']
    prod_s = (hex(prod) if isinstance(prod, int) else str(prod))
    P('  %-10s %-10s %-6s %s'
      % (BS + tail, prod_s, m.get('eaten', '-'), ','.join(m['warn']) or '-'))

produced = {m['produces'] for m in mapping.values() if isinstance(m['produces'], int)}
P('  可产出的控制字节取值集合 = %s' % sorted(hex(v) for v in produced))
legal_zone = {0x09, 0x0a, 0x0d}
invisible = sorted(produced & legal_zone)
P('  **落在「合法字符区」的取值**（控制字节普查结构上看不见）= %s'
  % [hex(v) for v in invisible])
ck('G1a 存在落在合法区的产出值（这是 R74 判据的结构性盲区）',
   len(invisible) >= 2, str([hex(v) for v in invisible]))
ck('G1b 0x09 可从 反斜杠 t 与 反斜杠 11 两条路径产出（同一字节两个来源）',
   mapping['t']['produces'] == 0x09 and mapping['11']['produces'] == 0x09)
ck('G1c 0x0a 可从 反斜杠 n 与 反斜杠 12 产出 ⇒ LF 计数无法区分「真换行」与「吃掉的字母」',
   mapping['n']['produces'] == 0x0a and mapping['12']['produces'] == 0x0a)
ck('G1d 0x0d 可从 反斜杠 r 与 反斜杠 15 产出 ⇒ CR 不变量同病',
   mapping['r']['produces'] == 0x0d and mapping['15']['produces'] == 0x0d)
ck('G1e 反斜杠 e 不产出 0x1b（有 SyntaxWarning、原样保留）⇒ R74 的「五成员 + 反斜杠 e」猜测不成立',
   mapping['e']['produces'] is None)

# ------------------------------------------------------------------ 严格普查
P('')
P('=== 严格普查（R74 判据）+ 宽普查（加回 TAB），在并集文本上 ===')
rows = []
for p, raw in sorted(union.items()):
    st = [(m.start(), m.group()[0]) for m in CTRL_STRICT.finditer(raw)]
    wd = [(m.start(), m.group()[0]) for m in CTRL_WIDE.finditer(raw)]
    if not wd:
        continue
    rows.append({'file': rel(p), 'bytes': len(raw),
                 'strict': st, 'wide': wd,
                 'tabs': len(raw) - len(re.sub(b'\t', b'', raw))})
P('  含宽判据命中的文本文件 %d 个' % len(rows))
for r in sorted(rows, key=lambda x: -len(x['wide'])):
    cnt = {}
    for _, v in r['wide']:
        cnt[hex(v)] = cnt.get(hex(v), 0) + 1
    P('  %-58s %8d B  严格=%3d 宽=%3d  取值=%s'
      % (r['file'], r['bytes'], len(r['strict']), len(r['wide']), cnt))
wide_only = [r for r in rows if len(r['wide']) > len(r['strict'])]
P('  宽比严格多出命中的文件 %d 个（= TAB 面）' % len(wide_only))
ck('G1f 存在 TAB 面文件（严格判据看不见）', len(wide_only) >= 1, str(len(wide_only)))

# ------------------------------------------------------------------ TAB 面的取证
P('')
P('=== TAB 面取证：TAB 之后紧跟 ext{ ⇒ 被吃掉的是字母 t（反斜杠 t 转义） ===')
tab_sites = []
for p, raw in union.items():
    for m in re.finditer(b'\t', raw):
        o = m.start()
        if raw[o + 1:o + 5] == b'ext{':
            tab_sites.append((rel(p), o, raw.count(b'\n', 0, o) + 1))
P('  TAB+ext{ 站点 %d 个' % len(tab_sites))
for s in tab_sites[:8]:
    P('    %s off=%d line=%d' % s)
if len(tab_sites) > 8:
    P('    ... 其余 %d 个省略（全量见 json）' % (len(tab_sites) - 8))

# 跨源旁证：本库另有「反斜杠 text{」的正确写法
proper = 0
proper_files = set()
for p, raw in union.items():
    n = len(re.findall(re.escape(BS.encode()) + rb'text\{', raw))
    if n:
        proper += n
        proper_files.add(rel(p))
P('  跨源旁证：正确写法 反斜杠 text{ 在 %d 个文件里共 %d 处' % (len(proper_files), proper))
ck('G1g TAB+ext{ 站点数 > 0（正控，不是恒报 0）', len(tab_sites) > 0, str(len(tab_sites)))
ck('G1h 旁证充分（正确写法 >= 50 处）⇒ 还原字母必为 t，不是猜的', proper >= 50, str(proper))
ck('G1i 旁证覆盖面（旁证文件数远多于受污染文件数 ⇒ 不是同源循环）',
   len(proper_files) > 5 * len({s[0] for s in tab_sites}),
   '%d vs %d' % (len(proper_files), len({s[0] for s in tab_sites})))

# 反证：把 TAB 换成字母 t 后，被吃掉的 t 全部还原为正确写法 反斜杠 text{
# R75 第二版实测暴露一件重要的事：这一族**修复不是等长的**。
#   反斜杠 text{ 里的 反斜杠+t 在 Python 非 raw 字符串里被合并成 0x09，
#   盘上剩下的是 0x09 + ext{（反斜杠一并被吃掉）。
#   ⇒ 还原必须把 1 个字节换成 2 个字符（反斜杠 + t），字节数 +1/站点。
#   这与 R14_COMMON 的 NUL 族不同：那族盘上是 NUL + x47C427，还原只需 1 个字符 0，等长。
#   第一版我在这里断言「1:1 等长」，实测 after=413 而不等于 451 —— 是断言错，不是数据错。
EATEN = re.compile(b'\x09ext[{]')                            # 盘上：0x09 + ext{
PROPER = re.compile(re.escape(BS.encode()) + rb'text[{]')     # 正确写法：反斜杠 + text{
eaten_before = sum(len(EATEN.findall(raw)) for raw in union.values())
proper_before = sum(len(PROPER.findall(raw)) for raw in union.values())
# 甲：只把 0x09 换成字母 t（等长修复）—— 会得到 text{ 但没有反斜杠，不是正确写法
proper_len_eq = sum(len(PROPER.findall(raw.replace(b'\t', b't'))) for raw in union.values())
# 乙：把 0x09 换成 反斜杠 + t（非等长修复，+1 字节/站点）—— 应得到全部正确写法
restore_bs_t = lambda raw: raw.replace(b'\x09ext{', BS.encode() + b'text{')
proper_full = sum(len(PROPER.findall(restore_bs_t(raw))) for raw in union.values())
eaten_after = sum(len(EATEN.findall(restore_bs_t(raw))) for raw in union.values())
bytes_after = sum(len(restore_bs_t(raw)) for raw in union.values())
bytes_before = sum(len(raw) for raw in union.values())
P('  还原前：正确写法 反斜杠+text{ %d 处 ；被吃掉写法 0x09+ext{ %d 处'
  % (proper_before, eaten_before))
P('  甲 等长修复（0x09 -> 字母 t）：正确写法 %d 处（差 %d 处，因为反斜杠没了）'
  % (proper_len_eq, proper_before + eaten_before - proper_len_eq))
P('  乙 非等长修复（0x09 -> 反斜杠+t）：正确写法 %d 处 ；被吃掉写法 %d 处'
  % (proper_full, eaten_after))
P('  字节数 %d -> %d（增量 %+d，等于被吃掉站点数 %d）'
  % (bytes_before, bytes_after, bytes_after - bytes_before, eaten_before))
ck('G1j 乙修复后 正确写法 == 还原前正确 + 还原前被吃掉（两类不相交、1:1）',
   proper_full == proper_before + eaten_before,
   '%d vs %d' % (proper_full, proper_before + eaten_before))
ck('G1k 乙修复后被吃掉写法归零', eaten_after == 0, str(eaten_after))
ck('G1l 被吃掉写法数 == TAB 站点数（同一判据两种算法必须一致）',
   eaten_before == len(tab_sites), '%d vs %d' % (eaten_before, len(tab_sites)))
ck('G1m 两处 proper 口径一致（正则版与 re.escape 版同数）',
   proper_before == proper, '%d vs %d' % (proper_before, proper))
ck('G1n 甲（等长）修复**不足以**还原：正确写法少 %d 处 ⇒ 此族修复必然 +1 字节/站点'
   % eaten_before, proper_len_eq == proper_before,
   '%d vs %d' % (proper_len_eq, proper_before))
ck('G1o 乙修复的字节增量恰等于站点数',
   bytes_after - bytes_before == eaten_before,
   '%+d vs %d' % (bytes_after - bytes_before, eaten_before))

# ------------------------------------------------------------------ G3 rg 行为
P('')
P('=== G3 · rg 的 binary 判定到底由哪个字节触发（8 例矩阵，实测） ===')
tmpd = tempfile.mkdtemp(prefix='r75rg_')
cases = {'nul': b'hello\x00world MARKER\n', 'ff': b'hello\x0cworld MARKER\n',
         'esc': b'hello\x1bworld MARKER\n', 'soh': b'hello\x01world MARKER\n',
         'ack': b'hello\x06world MARKER\n', 'tab': b'hello\tworld MARKER\n',
         'vt': b'hello\x0bworld MARKER\n', 'bel': b'hello\x07world MARKER\n'}
rg_res = {}
for k, v in cases.items():
    fp = os.path.join(tmpd, k + '.md')
    io.open(fp, 'wb').write(v)
    r = subprocess.run(['rg', 'MARKER', fp], capture_output=True, text=True)
    first = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else ''
    is_bin = 'binary file matches' in first
    rg_res[k] = {'first_line': first[:80], 'binary': is_bin}
    P('  %-5s 首行=%r ⇒ binary=%s' % (k, first[:52], is_bin))
bin_keys = {k for k, v in rg_res.items() if v['binary']}
P('  触发 binary 的字节：%s' % sorted(bin_keys))
ck('G3a 只有 NUL 触发 binary（0x0c/0x1b/0x01/0x06/0x0b/0x07/TAB 都不触发）',
   bin_keys == {'nul'}, str(sorted(bin_keys)))
ck('G3b 正控：NUL 样本确实触发（矩阵不是恒报 False）', rg_res['nul']['binary'])
ck('G3c 反控：0x0c 样本不触发（否则「只有 NUL」不成立）', not rg_res['ff']['binary'])

# ------------------------------------------------------------------ 逐族取证（非 TAB 面）
P('')
P('=== 逐站点取证（非 TAB 面，含左右 20 字节） ===')
MODEL = {0x00: '0', 0x01: None, 0x06: None, 0x07: 'a', 0x08: 'b', 0x0b: 'v', 0x0c: 'f', 0x09: 't'}
sites = []
for p, raw in sorted(union.items()):
    for m in CTRL_STRICT.finditer(raw):
        o = m.start()
        sites.append({'file': rel(p), 'off': o, 'byte': m.group()[0],
                      'line': raw.count(b'\n', 0, o) + 1,
                      'prev': raw[o - 1] if o else None,
                      'left': raw[max(0, o - 20):o].decode('utf-8', 'replace'),
                      'right': raw[o + 1:o + 21].decode('utf-8', 'replace')})
P('  严格判据站点 %d 个' % len(sites))
for s in sites:
    P('  %-50s off=%7d %s line=%d prev=%s 左=%r 右=%r'
      % (s['file'], s['off'], hex(s['byte']), s['line'],
         hex(s['prev']) if s['prev'] is not None else '-', s['left'][-14:], s['right'][:14]))
bs_prev = [s for s in sites if s['prev'] == 0x5c]
ck('G4 反斜杠残留站点 0（族的前提：只吃字母、不留反斜杠）', len(bs_prev) == 0, str(len(bs_prev)))

# ------------------------------------------------------------------ 汇总
P('')
P('=== 汇总（全部实测） ===')
P('  G2 两条算子：A 文本 %d / B 文本 %d / 差异集 %d（A 漏判 LEAD_LOCK）'
  % (len(tA), len(tB), len(onlyB)))
P('  G1 转义族可产出控制字节 %d 种；其中落在合法区（09/0a/0d）%d 种'
  % (len(produced), len(invisible)))
P('  严格判据（R74）站点 %d；宽判据多出 TAB 站点 %d' % (len(sites), len(tab_sites)))
P('  TAB 面受污染文件 %d 个；跨源旁证（正确写法）%d 处 / %d 文件'
  % (len({s[0] for s in tab_sites}), proper, len(proper_files)))
P('  G3 rg binary 只由 NUL 触发（实测 8 例矩阵）')
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'opA_texts': len(tA), 'opB_texts': len(tB), 'onlyB': [rel(p) for p in onlyB],
           'union_texts': len(union), 'mapping': mapping,
           'strict_sites': sites, 'tab_sites': tab_sites,
           'proper_text_brace': proper, 'proper_files': sorted(proper_files),
           'rg_matrix': rg_res, 'fails': fails},
          io.open(os.path.join(HERE, 'escape_scope_r75.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'escape_scope_r75.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
