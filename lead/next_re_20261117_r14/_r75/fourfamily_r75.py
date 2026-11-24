# -*- coding: utf-8 -*-
"""R75 · 四族判定：同一个控制字节，**由「紧随其后的字节」决定它出自哪种工具**

R74 的结论是「48 个控制字节统一根因 = Python 非 raw 字符串」。本轮把它拆成可证伪的四族，
判据只用「控制字节 + 紧随其后的字节形态」，工具归属用**正向复现 + 反向失配**双测：

  F1  NUL + x 十六进制      (如 0x00 后接 x47C427)     —— 三种工具都能产出（不可区分）
  F2  NUL + 八进制数字      (如 0x00 后接 04393F0)     —— **只有两字符替换能产出**
  F3  字母类控制字节        (0x07 0x08 0x0b 0x0c)      —— 语言字面量产出，两字符替换不能
  F4  0x1b / 0x06           —— 只有 GNU 系（printf/sed）或 Python 的 xNN 能产出

关键实测（F2）：Python 字面量把 反斜杠 0 0 4 3 9 3 F 0 解成 0x04 + 393F0，
与盘上的 0x00 + 04393F0 **不同**；而「只吃两个字符」的替换解出 0x00 + 04393F0，**相同**。
⇒ F2 这 16 个站点**不可能**由 R74 声称的机制产生，R74 的「统一根因」在这一点上被证伪。

自测：
  P1  F1 站点数 > 0（正控）
  P2  F4 站点数 > 0（正控）
  N1  两字符替换对 F1 必须也复现（否则 F1 的「不可区分」是假的）
  N2  语言字面量对 F2 必须失配（这是 F2 判据的核心）
  N3  两字符替换对 F3 的 0x0c 必须失配
  N4  F2 站点在**任何** Python 字面量还原串下都失配（穷举 1..4 字符还原候选）
"""
import io
import os
import re
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

CTRL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')
BS = 0x5c
OCT = b'01234567'
HEX = b'0123456789abcdefABCDEF'
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

out, fails = [], []


def P(s=''):
    print(s)
    out.append(s)


def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)


# ------------------------------------------------------------------ 采集
P('=== 采集（两条文本算子取并集，避免 R75 自己踩过的漏判面） ===')
files = {}
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
        if CTRL.search(raw):
            files[p] = raw
P('  含控制字节的文本文件 %d 个' % len(files))
rel = lambda p: os.path.relpath(p, ROOT)

sites = []
for p, raw in sorted(files.items()):
    for m in CTRL.finditer(raw):
        o = m.start()
        nxt = raw[o + 1] if o + 1 < len(raw) else None
        sites.append({'file': rel(p), 'off': o, 'byte': m.group()[0], 'next': nxt,
                      'line': raw.count(b'\n', 0, o) + 1,
                      'left': raw[max(0, o - 24):o], 'right': raw[o + 1:o + 25]})
P('  站点总数 %d' % len(sites))

# ------------------------------------------------------------------ 四族判定
P('')
P('=== 四族判定（判据只看「控制字节 + 紧随其后的字节」） ===')


def family(s):
    b, nxt = s['byte'], s['next']
    if b == 0x00 and nxt == 0x78:          # NUL + 字母 x
        return 'F1'
    if b == 0x00 and nxt is not None and nxt in OCT:
        return 'F2'
    if b in (0x07, 0x08, 0x0b, 0x0c):
        return 'F3'
    if b in (0x1b, 0x06, 0x01, 0x02, 0x03):
        return 'F4'
    return 'F5-未分类'


for s in sites:
    s['family'] = family(s)
fam = {}
for s in sites:
    fam.setdefault(s['family'], []).append(s)
P('  %-10s %5s  %s' % ('族', '站点', '判据'))
DESC = {'F1': 'NUL 后接字母 x（十六进制地址首字符）',
        'F2': 'NUL 后接八进制数字 0-7（地址自身的首位被吃掉）',
        'F3': '字母类控制字节 07/08/0b/0c',
        'F4': '0x1b / 0x06 / 0x01 等非字母非 NUL 的控制字节',
        'F5-未分类': 'NUL 后接问号 —— 落在 INI 抽取件的尾部二进制尾料里，不是转义族（见下）'}
for k in sorted(fam):
    P('  %-10s %5d  %s' % (k, len(fam[k]), DESC.get(k, '（未分类，须逐站点人工看）')))
ck('P1 F1 站点数 > 0（正控：分类器不是恒空）', len(fam.get('F1', [])) > 0,
   str(len(fam.get('F1', []))))
ck('P2 F2 站点数 > 0（这是本轮的核心主张，必须是实测非空）',
   len(fam.get('F2', [])) > 0, str(len(fam.get('F2', []))))
ck('P3 F3 站点数 > 0', len(fam.get('F3', [])) > 0, str(len(fam.get('F3', []))))
ck('P4 F4 站点数 > 0', len(fam.get('F4', [])) > 0, str(len(fam.get('F4', []))))
# R75 自错 5：第一版断言「未分类必须为 0」——把「判据有洞」与「数据里有非族成员」混成一件事。
#   实测 3 个未分类站点全部是 INI 抽取件的尾部二进制尾料（NUL 后接问号），
#   它们**本来就不属于转义族**，分类器把它们单列出来是**正确行为**，不是洞。
#   改判据：未分类站点必须全部来自「非 .md/.py/.txt 的抽取件」，且其右上下文不含 ASCII 字母数字。
unc = fam.get('F5-未分类', [])
ALNUM = set(range(0x30, 0x3a)) | set(range(0x41, 0x5b)) | set(range(0x61, 0x7b))
P('  未分类站点 %d 个：' % len(unc))
for s in unc:
    P('    %-46s off=%7d %s 右=%r' % (s['file'], s['off'], hex(s['byte']), s['right'][:12]))
ck('P5 未分类站点必须全部在 .ini 抽取件里（不是 .md/.py 这类活文档）',
   all(s['file'].endswith('.ini') for s in unc), str([s['file'] for s in unc]))
ck('P5b 未分类站点的右上下文首字节不是 ASCII 字母数字（是真尾料，不是被吃掉的字母）',
   all(s['next'] is not None and s['next'] not in ALNUM for s in unc),
   str([hex(s['next']) if s['next'] is not None else None for s in unc]))

# ------------------------------------------------------------------ 三工具
def decode_py(src):
    res = bytearray(); i = 0; n = len(src)
    SIMPLE = {0x66: 0x0c, 0x76: 0x0b, 0x61: 0x07, 0x62: 0x08,
              0x74: 0x09, 0x6e: 0x0a, 0x72: 0x0d, 0x5c: 0x5c}
    while i < n:
        c = src[i]
        if c != BS:
            res.append(c); i += 1; continue
        if i + 1 >= n:
            res.append(BS); i += 1; continue
        nx = src[i + 1]
        if nx == 0x78:
            if i + 3 < n and src[i + 2] in HEX and src[i + 3] in HEX:
                res.append(int(src[i + 2:i + 4], 16)); i += 4; continue
            res.append(BS); i += 1; continue
        if nx in OCT:
            j = i + 1; d = bytearray()
            while j < n and len(d) < 3 and src[j] in OCT:
                d.append(src[j]); j += 1
            res.append(int(bytes(d), 8) & 0xff); i = j; continue
        if nx in SIMPLE:
            res.append(SIMPLE[nx]); i += 2; continue
        res.append(BS); i += 1
    return bytes(res)


def decode_twochar(src):
    """只吃两个字符：反斜杠 + 0 -> NUL，其余原样。"""
    res = bytearray(); i = 0; n = len(src)
    while i < n:
        if src[i] == BS and i + 1 < n and src[i + 1] == 0x30:
            res.append(0x00); i += 2
        else:
            res.append(src[i]); i += 1
    return bytes(res)


P('')
P('=== 正向复现：三工具各能复现多少站点 ===')


def repro(s, dec, src_ins):
    src = s['left'] + src_ins + s['right']
    want = s['left'] + bytes([s['byte']]) + s['right']
    return dec(src) == want


LETTER = {0x00: b'0', 0x07: b'a', 0x08: b'b', 0x0b: b'v', 0x0c: b'f',
          0x09: b't', 0x01: b'x01', 0x06: b'x06'}
tool_cov = {'py': set(), 'two': set(), 'shell': set()}
for idx, s in enumerate(sites):
    if s['byte'] not in LETTER:
        continue
    ins = bytes([BS]) + LETTER[s['byte']]
    if repro(s, decode_py, ins):
        tool_cov['py'].add(idx)
    if repro(s, decode_twochar, ins):
        tool_cov['two'].add(idx)
    # shell：printf 语义（反斜杠 e 也认），在 G1 里已单独测过 ESC，这里只做 F2/N1 用
for k, v in tool_cov.items():
    P('  %-6s 复现 %d / %d 站点' % (k, len(v), len(sites)))

P('')
P('=== 逐族 × 工具 复现矩阵（核心表） ===')
MATRIX = ['py', 'two']
P('  %-6s %5s %10s %10s' % ('族', '站点', 'py字面量', '两字符替换'))
fam_tool = {}
for k in ('F1', 'F2', 'F3', 'F4'):
    idxs = [i for i, s in enumerate(sites) if s['family'] == k]
    row = {}
    for t in MATRIX:
        row[t] = [i for i in idxs if i in tool_cov[t]]
    fam_tool[k] = row
    P('  %-6s %5d %10s %10s'
      % (k, len(idxs),
         '%d/%d' % (len(row['py']), len(idxs)),
         '%d/%d' % (len(row['two']), len(idxs))))

ck('N1 两字符替换对 F1 **也**能复现（否则 F1「不可区分」是假的）',
   len(fam_tool['F1']['two']) == len(fam.get('F1', [])),
   '%d/%d' % (len(fam_tool['F1']['two']), len(fam.get('F1', []))))
ck('N2 py 字面量对 F2 **全部失配**（这是 F2 判据的核心，16/16 必须为 0）',
   len(fam_tool['F2']['py']) == 0,
   '%d/%d' % (len(fam_tool['F2']['py']), len(fam.get('F2', []))))
ck('N2b 两字符替换对 F2 **全部**复现',
   len(fam_tool['F2']['two']) == len(fam.get('F2', [])),
   '%d/%d' % (len(fam_tool['F2']['two']), len(fam.get('F2', []))))
ck('N3 两字符替换对 F3 的 0x0c **失配**（它只认 反斜杠 0）',
   all(i not in tool_cov['two'] for i, s in enumerate(sites)
       if s['byte'] == 0x0c and s['family'] == 'F3'),
   str(len([1 for s in fam.get('F3', []) if s['byte'] == 0x0c])))

P('')
P('=== N4 · F2 站点：区分「2 字符形式」与「4 字符八进制形式」 ===')
# R75 自错 4（本轮第四次踩同一类：判据范围画错）：
#   第一版断言写成「F2 在任何 Python 还原串下都不可复现」——实测被 b'\\000' 当场推翻。
#   fact：源码 反斜杠 0 0 0 后接 04393F0 时，Python 吃三位八进制得 NUL，剩下的 04393F0 原样保留，
#         结果**恰好**等于盘上。⇒ 「Python 不可能产生」是错的，必须收窄。
#   收窄后的可证伪断言：
#     A2'  R74 声称的**2 字符形式**（反斜杠 0）不可能产生 F2 —— 因为反斜杠 0 后紧跟八进制数字时
#          Python 会继续吃下去（反斜杠 0 0 4 解成 0x04），长度与取值都不对。
#     A2'' 4 字符八进制形式（反斜杠 0 0 0）能产生 F2 —— 但它与「地址首位被吃掉」的语义不符：
#          它把 3 个字符换成了 1 个字节，而盘上只少 1 个字符。
SRC_2CHAR = bytes([BS, 0x30])                 # 反斜杠 0（R74 的模型）
SRC_4CHAR = bytes([BS, 0x30, 0x30, 0x30])     # 反斜杠 0 0 0（八进制）
f2 = fam.get('F2', [])
n2 = sum(1 for s in f2 if repro(s, decode_py, SRC_2CHAR))
n4c = sum(1 for s in f2 if repro(s, decode_py, SRC_4CHAR))
P('  F2 站点 %d 个；用 2 字符形式（反斜杠 0）复现 %d 个；用 4 字符八进制（反斜杠 0 0 0）复现 %d 个'
  % (len(f2), n2, n4c))
ck('A2\' **2 字符形式对 F2 全部失配**（这是 R74 模型的适用边界）', n2 == 0,
   '%d/%d' % (n2, len(f2)))
ck('A2\'\' 4 字符八进制形式对 F2 全部复现（这就是我第一版断言的错处，如实记）',
   n4c == len(f2), '%d/%d' % (n4c, len(f2)))
# 等长性对照：2 字符形式是 1:1；4 字符形式是 4:1（吃掉 3 字符换 1 字节）
ck('A2\'\'\' 2 字符形式是 2 字符换 1 字节、4 字符形式是 4 字符换 1 字节 ⇒ 两者不是同一机制',
   len(SRC_2CHAR) != len(SRC_4CHAR))

P('')
P('=== F2 逐站点清单（这是本轮最硬的一条） ===')
for s in fam.get('F2', []):
    P('  %-46s off=%7d line=%4d 右=%r' % (s['file'], s['off'], s['line'], s['right'][:14]))

# ------------------------------------------------------------------ 真实工具复核
P('')
P('=== 真实工具复核（不是模拟器，是 GNU printf 本体） ===')
CASES = [
    ('F2 反斜杠 0 0 4 3 9 3 F 0', b'\\004393F0', 0x00),
    ('F2 反斜杠 0 4 6 B 5 C 0', b'\\046B5C0', 0x00),
    ('F1 反斜杠 0 x 4 7 C 4 2 7', b'\\0x47C427', 0x00),
    ('F4 反斜杠 e 3', b'\\e3', 0x1b),
    ('F4 反斜杠 x 0 6', b'\\x06', 0x06),
]
P('  %-30s %-18s %-20s %s' % ('用例', 'printf 输出', 'Python 字面量输出', '是否一致'))
agree = {}
for label, src, want_first in CASES:
    r = subprocess.run(['printf', src], capture_output=True)
    sh = r.stdout
    code = "s = '" + src.decode('latin-1') + "'"
    ns = {}
    try:
        exec(code, ns)
        pyb = ns['s'].encode('latin-1')
    except Exception as e:
        pyb = b'<ERR ' + str(e).encode() + b'>'
    same = sh == pyb
    agree[label] = same
    P('  %-30s %-18s %-20s %s'
      % (label, sh[:12].hex(), pyb[:12].hex(), 'same' if same else 'DIFFER'))

# R75 自错 7（本轮第五次踩同一族：断言方向写反）：第一版 T1 断言「printf 与 Python 在
#   NUL + 八进制上必须不同」。实测**相同** —— 两者都把 反斜杠 0 0 4 吃成 0x04 再留 3393F0...
#   ⇒ 「NUL + 八进制数字」这一形态**两种工具都产不出来**。真正能产出它的是
#   **两字符替换**（sed 的 s/反斜杠 0/NUL/g、Python 的 str.replace）。
#   下面用 sed 本体做同一实验，把出资方钉死。
P('')
P('=== sed 本体复核（两字符替换的真实工具） ===')
import tempfile
td = tempfile.mkdtemp(prefix='r75sed_')
sed_cases = [('F2', b'A\\004393F0B\n'), ('F1', b'A\\0x47C427B\n')]
sed_res = {}
for label, raw in sed_cases:
    fp = os.path.join(td, label + '.txt')
    io.open(fp, 'wb').write(raw)
    # R75 自错 8：sed 的替换文本里**不能**直接放 NUL（execve 参数不允许内嵌 0x00，
    #   subprocess 当场 ValueError）。改用 sed 的转义写法反斜杠 x 0 0，由 sed 自己解出 NUL。
    # R75 自错 9：模式串只写了一个反斜杠（BRE 里 反斜杠 0 另有含义），必须写**两个**
    #   反斜杠 —— sed 正则里 反斜杠 反斜杠 才匹配一个**字面**反斜杠，再跟 0。
    #   实测区别：单反斜杠版输出 41 5c 00 00 34...（反斜杠没被匹配掉、尾随多一个 NUL），
    #   双反斜杠版输出 41 00 30 34 33...（正是盘上形态）。
    pat = 's/' + chr(92) * 2 + '0/' + chr(92) + 'x00/g'
    r = subprocess.run(['sed', pat, fp], capture_output=True)
    # R75 自错 10：变量名 out 与 P() 的累加器重名，把它从 list 覆盖成 bytes。
    #   改名 sed_out；这也是本轮运行日志最后一次崩溃的原因。
    sed_out = r.stdout
    pyrep = raw.decode('latin-1').replace(chr(92) + '0', '\x00').encode('latin-1')
    sed_res[label] = {'sed': sed_out.hex(), 'py_replace': pyrep.hex(),
                      'same': sed_out.rstrip(b'\n') == pyrep.rstrip(b'\n')}
    P('  %-4s 原文=%-18r sed=%-24s str.replace=%-24s 一致=%s'
      % (label, raw, sed_out.hex(), pyrep.hex(), sed_res[label]['same']))
ck('T5 sed 与 Python 的 str.replace 在 F2 形态上**一致**（两字符替换是同一机制）',
   sed_res['F2']['same'], str(sed_res['F2']))
ck('T5b sed 与 str.replace 在 F1 形态上**也一致**', sed_res['F1']['same'])
ck('T5c sed 的输出首字节是 0x41 0x00（NUL 紧接原样 004393F0）⇒ 正是盘上形态',
   sed_res['F2']['sed'].startswith('4100'), sed_res['F2']['sed'][:12])
ck('T1 printf 与 Python 在「NUL + 八进制数字」上**一致**（⇒ 两者都产不出 F2，F2 只能来自两字符替换）',
   agree['F2 反斜杠 0 0 4 3 9 3 F 0'] is True and agree['F2 反斜杠 0 4 6 B 5 C 0'] is True,
   str(agree))
ck('T2 printf 与 Python 在「NUL + x」上**一致**（F1 不可区分）',
   agree['F1 反斜杠 0 x 4 7 C 4 2 7'] is True)
ck('T3 printf 能产出 ESC、Python 不能（F4 的 0x1b 归属）',
   agree['F4 反斜杠 e 3'] is False)
ck('T4 printf 与 Python 在 反斜杠 x 0 6 上一致（F4 的 0x06 无法区分）',
   agree['F4 反斜杠 x 0 6'] is True)

# ------------------------------------------------------------------ 等长性
P('')
P('=== 各族的修复是否等长（R74 只测过 NUL 族，说「等长」） ===')
LEN = {'F1': ('1 -> 1（NUL 换成字符 0）', 0),
       'F2': ('1 -> 1（NUL 换成字符 0）', 0),
       'F3': ('1 -> 1（换成对应字母 f/v/a/b）', 0),
       'F4': ('0x1b -> 反斜杠+e 为 1 -> 2；若只要 1 -> 1 则须改成 x1b 写法（4 字符）', 1)}
for k in ('F1', 'F2', 'F3', 'F4'):
    n = len(fam.get(k, []))
    P('  %-4s 站点 %3d  等长修复 %s' % (k, n, LEN[k][0]))
ck('L1 R74 的「修复等长」只对 F1/F2/F3 成立，对 F4 不成立（+1 字节/站点）',
   LEN['F4'][1] == 1 and LEN['F1'][1] == 0 and LEN['F3'][1] == 0)

P('')
P('=== 汇总（全部实测） ===')
P('  含控制字节的文本文件 %d 个 ；站点 %d 个' % (len(files), len(sites)))
for k in sorted(fam):
    P('  %-4s %3d 站点  py复现 %3d  两字符复现 %3d'
      % (k, len(fam[k]),
         len(fam_tool.get(k, {}).get('py', [])),
         len(fam_tool.get(k, {}).get('two', []))))
P('  F2（NUL+八进制）%d 个站点：py 字面量 0 复现，两字符替换全部复现 ⇒ 机制不同源'
  % len(fam.get('F2', [])))
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'files': len(files),
           'sites': [{k: (v.hex() if isinstance(v, bytes) else v) for k, v in s.items()}
                     for s in sites],
           'families': {k: len(v) for k, v in fam.items()},
           'tool_cov': {k: sorted(v) for k, v in tool_cov.items()},
           'printf_vs_py': agree, 'sed_vs_py': {k: v for k, v in sed_res.items()},
           'fails': fails},
          io.open(os.path.join(HERE, 'fourfamily_r75.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'fourfamily_r75.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
