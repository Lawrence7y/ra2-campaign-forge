# -*- coding: utf-8 -*-
"""R74 · R14_COMMON.md 的 0x00 字节：本机取证测量（主会话自做，带正反控）

背景：本库把 R14_COMMON.md 当不变量文件，但历史上只约束过 CR 计数，从未做字节级健全性检查。

测量项：
  M1  0x00 站点普查：偏移 / 行号 / 前驱字节分布 / distinct 候选值
  M2  对账：43 个站点里「紧随其后就是一条指令助记符」的站点逐个反汇编核对
      （其余站点只是裸地址引用，不带指令注解，不计入反汇编对账，也不许算通过）
  M3  跨源旁证：distinct 候选值在库内（排除备份与 _rNN）作为整体出现于多少文件
  M4  影响面 A：替换前后 字节数 / CR / LF / 行数 / UTF-8 严格解码
  M5  影响面 B：rg 对当前文件的输出形态 vs 干净文本
  M6  影响面 C：候选值在「当前文本」vs「还原文本」里的命中数差
  M7  根因：能否用一次 re.sub（repl 写成 r'\\0'）复现出同样的 0x00 形态
  M8  留存备份里的 0x00 偏移集合是否与 live 完全相同

反控（纪律 32：反控必须落在判据真正会被读到的那一格）：
  N1  对每个可对账站点，把地址按 +1..+6 位移，必须至少出现一次不吻合
  N2  把某个站点的文档助记符去对「全部 41 个 VA 站点」的反汇编，
      必须绝大多数不吻合（否则该助记符没有鉴别力，M2 恒真）
  N3  干净文本（STATUS_BOARD.md、本脚本自身）跑同一检测器必须 0 个
  N4  rg 差异必须真实：同一短语在干净文本能出行号、在当前文件出不了
  N5  还原必须真的改变可搜索性（否则 M6 无意义）
  N6  re.sub 双跑：repl=r'\\0' 出 0x00，repl=r'\\g<0>' 出完整字符
  N7  M2 的分母必须非零且不是全部站点（否则「只挑对的算」）

本轮自查修正（写进卡面记录，不许悄悄改）：
  R74-a  我最初把「涉及行数」写成 17，实测 19 ⇒ 断言当场 FAIL，改成实测值 19
  R74-b  我最初把「紧随助记符的站点」当成 41 个 VA 全都算，实测只有 7 个站点后面
         直接跟着助记符 ⇒ 原来的 41/2 分类是错的，改为「可对账 7 / 裸引用 36」
  R74-c  我最初的反控 N2 用「把 0x00 换成数字」构造，实测 0/0 —— 因为 '1x47C427'
         根本不是十六进制字面量，那条反控是零信息格 ⇒ 改为「助记符对全站点交叉核对」
  R74-d  我最初 N4b 用「连带义务」当对照短语，实测它只存在于 R14_COMMON、不在看板上
         ⇒ 换成两边都有的短语
"""
import io
import os
import re
import sys
import json
import bisect
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
COMMON = os.path.join(R14, 'R14_COMMON.md')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

raw = io.open(COMMON, 'rb').read()
P('[输入] R14_COMMON.md = %d B' % len(raw))

lines = raw.split(b'\n')
offs, o = [], 0
for l in lines:
    offs.append(o); o += len(l) + 1

sites = []
for m in re.finditer(rb'\x00', raw):
    i = m.start()
    ln = bisect.bisect_right(offs, i) - 1
    tail = re.match(rb'([0-9A-Za-z][0-9A-Za-z0-9]*)', raw[i + 1:i + 20])
    sites.append({'off': i, 'line': ln + 1, 'prev': raw[i - 1:i],
                  'tail': tail.group(1).decode() if tail else None})

# ---------------------------------------------------------------- M1
P('')
P('=== M1 · 0x00 站点普查 ===')
P('  0x00 总数 = %d ；涉及不同行 = %d' % (len(sites), len({s['line'] for s in sites})))
prevhist = {}
for s in sites:
    prevhist[s['prev']] = prevhist.get(s['prev'], 0) + 1
P('  前驱字节分布：' + ', '.join('%s:%d' % (k.hex(), v) for k, v in sorted(prevhist.items())))
ck('M1a 0x00 总数 = 43', len(sites) == 43, '%d' % len(sites))
ck('M1b 涉及行数 = 19（实测，非预估）', len({s['line'] for s in sites}) == 19,
   '%d' % len({s['line'] for s in sites}))
ck('M1c 每个 0x00 后面都紧跟字母数字', all(s['tail'] for s in sites))
ck('M1d 前驱字节无一是字母数字（0x00 都落在 token 边界）',
   all(not chr(s['prev'][0]).isalnum() for s in sites))
P('  涉及行：%s' % sorted({s['line'] for s in sites}))

# ---------------------------------------------------------------- M2
P('')
P('=== M2 · 带指令注解的站点逐个反汇编对账 ===')
import pefile, capstone
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
TV, TS = IB + text.VirtualAddress, text.SizeOfRawData
TDATA = pe.get_data(text.VirtualAddress, TS)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
P('  ImageBase=%#x  .text=[%#x, %#x)' % (IB, TV, TV + TS))

MNSET = ('mov', 'and', 'or', 'cmp', 'je', 'jne', 'jmp', 'call', 'push', 'pop',
         'lea', 'test', 'add', 'sub', 'inc', 'dec', 'xor', 'imul', 'ret')

def dis1(va, n=10):
    if not (TV <= va < TV + TS):
        return None, b''
    b = TDATA[va - TV: va - TV + n]
    ins = list(md.disasm(b, va, count=1))
    if not ins:
        return None, b
    return ins[0].mnemonic + ' ' + ins[0].op_str, b

def cand_of(s):
    return '0' + s['tail']

def va_of(c):
    if c.lower().startswith('0x'):
        return int(c, 16)
    if re.fullmatch(r'00[0-9A-F]{6}', c):
        return int(c, 16)
    return None

records = []
for s in sites:
    c = cand_of(s)
    va = va_of(c)
    after = raw[s['off'] + 1 + len(s['tail']): s['off'] + 1 + len(s['tail']) + 30]
    after_s = after.decode('utf-8', 'replace')
    # R74-e 修正：只认「地址后恰好一个空格 + 小写助记符」这一形态。
    # 原版用 lstrip() 后取首个单词，把「0x449440，其体内 call …」「0069DEB0（五模式汇入 call」
    # 这类「地址是被描述的对象、call 在它后面」的句子误判成「该地址就是 call 指令」，
    # 造成 2 处假不吻合（0x449440 / 0069DEB0）。这两个站点是裸引用，不是指令注解。
    doc_mn = None
    m_mn = re.match(r' ([a-z]{2,5})\b', after_s)
    if m_mn and m_mn.group(1) in MNSET:
        doc_mn = m_mn.group(1)
    d, b = (dis1(va) if va is not None else (None, b''))
    match = None
    if doc_mn and d:
        match = (d.split(' ')[0] == doc_mn)
    # R74-f：操作数层的字面比对不当作判据（只作诊断）。原因有二：
    #   1) 正文常在操作数后直接中标注解（例如 and al,1（24 01）），字面必然不等；
    #   2) 正文用 vt 作「持有 vtable 的寄存器」的别名（本库 3 处 [vt+…]），
    #      而实际反汇编写的是 [edx+0x48]，字面必然不等。
    # 因此操作数层只统计「字面完全一致」的条数，并逐个给差异原因，不判 PASS/FAIL。
    def _norm(s):
        s = s.replace('byte ptr ', '').replace('dword ptr ', '').replace('word ptr ', '')
        return re.sub(r'\s+', '', s).lower()
    op_dis = _norm(d.split(' ', 1)[1]) if (d and ' ' in d) else ''
    m_op = re.match(r' ([a-z]{2,5}) ([^\r\n|/；。（]{0,26})', after_s)
    op_doc = _norm(m_op.group(2)) if m_op else ''
    op_exact = bool(op_dis) and bool(op_doc) and op_dis == op_doc
    if op_exact:
        op_note = 'exact'
    elif '[vt+' in op_doc:
        op_note = 'vt-alias'
    elif '（' in after_s[:40] or '(' in after_s[:40]:
        op_note = 'doc-annotated'
    else:
        op_note = 'other'
    records.append({'off': s['off'], 'line': s['line'], 'cand': c, 'va': va,
                    'raw': b[:8].hex(' '), 'disasm': d, 'doc_mn': doc_mn,
                    'after': after_s[:24], 'match': match,
                    'op_dis': op_dis, 'op_doc': op_doc, 'op_exact': op_exact,
                    'op_note': op_note,
                    'in_text': (va is not None and TV <= va < TV + TS)})

annot = [r for r in records if r['doc_mn']]
bare = [r for r in records if not r['doc_mn']]
P('  可对账站点（地址后恰好一个空格 + 助记符）= %d ；裸地址引用站点 = %d' % (len(annot), len(bare)))
P('  %-6s %-10s %-26s %-26s %-5s %-13s %s' %
  ('行', '候选', '字节码', '反汇编', '正文', '操作数', '吻合'))
for r in annot:
    P('  %-6d %-10s %-26s %-26s %-5s %-13s %s' %
      (r['line'], r['cand'], r['raw'], r['disasm'], r['doc_mn'], r['op_note'],
       'yes' if r['match'] else ('no' if r['match'] is False else '?')))
ck('M2a 可对账站点数 = 7（实测）', len(annot) == 7, '%d' % len(annot))
ck('M2b 可对账站点 7/7 助记符吻合', all(r['match'] is True for r in annot),
   '%d/%d' % (sum(1 for r in annot if r['match'] is True), len(annot)))
n_bad = sum(1 for r in annot if r['match'] is False)
ck('M2c 可对账站点 0 处不吻合', n_bad == 0, '%d' % n_bad)
op_hist = {}
for r in annot:
    op_hist[r['op_note']] = op_hist.get(r['op_note'], 0) + 1
P('  操作数层诊断（不判 PASS/FAIL，只记差异归因）：%s' % op_hist)
P('  ⇒ 助记符层是可判据的；操作数层不可判据（正文有中文注解与 vt 别名，字面必然不等）')
ck('N7 分母不是全部站点（7 < 43，未把「裸引用」算成通过）', len(annot) < len(records),
   '%d < %d' % (len(annot), len(records)))
va_all = [r for r in records if r['va'] is not None]
ck('M2d 43 个候选值全部解析为 VA（含 2 个字段偏移）', len(va_all) == 43, '%d' % len(va_all))
ck('M2e 其中落在 .text 内的 = 41（0x2BC / 0x2C0 是字段偏移，不在 .text）',
   sum(1 for r in va_all if r['in_text']) == 41, '%d' % sum(1 for r in va_all if r['in_text']))

# ---- N1 位移反控
P('')
P('=== N1 反控 · 地址位移后必须出现不吻合 ===')
n1_rows = []
for r in annot:
    flips = []
    for k in (1, 2, 3, 4, 5, 6):
        d2, _ = dis1(r['va'] + k)
        if (d2 is None) or (d2.split(' ')[0] != r['doc_mn']):
            flips.append(k)
    n1_rows.append((r['cand'], flips))
    P('  %-10s 位移 1..6 中不吻合的位移 = %s' % (r['cand'], flips))
ck('N1 每个可对账站点都存在使其翻转的位移', all(f for _, f in n1_rows),
   '%d/%d' % (sum(1 for _, f in n1_rows if f), len(n1_rows)))

# ---- N2 助记符鉴别力
P('')
P('=== N2 反控 · 文档助记符对全 41 个 .text 站点必须绝大多数不吻合 ===')
allv = [r for r in records if r['in_text']]
n2 = []
for r in annot:
    okc = sum(1 for q in allv if q['disasm'] and q['disasm'].split(' ')[0] == r['doc_mn'])
    n2.append((r['cand'], r['doc_mn'], okc, len(allv)))
    P('  %-10s 正文助记符 %-5s 在 %d / %d 个 .text 站点上成立' %
      (r['cand'], r['doc_mn'], okc, len(allv)))
ck('N2 每个正文助记符的鉴别力都不足半数（否则 M2 恒真）',
   all(okc * 2 < tot for _, _, okc, tot in n2),
   'max=%d/%d' % (max(okc for _, _, okc, _ in n2), len(allv)))

# ---- N3 干净文本
P('')
P('=== N3 反控 · 干净文本跑同一检测器 ===')
board = io.open(BOARD, 'rb').read()
ck('N3 STATUS_BOARD.md 的 0x00 = 0', board.count(b'\x00') == 0, '%d' % board.count(b'\x00'))
ck('N3b 本脚本自身 0x00 = 0',
   io.open(os.path.abspath(__file__), 'rb').read().count(b'\x00') == 0)

# ---------------------------------------------------------------- M3
P('')
P('=== M3 · distinct 候选值的跨源旁证 ===')
distinct = sorted({r['cand'] for r in records})
P('  distinct 候选值 = %d' % len(distinct))
corpus = []
for root in ('lead', 're_atlas', 'out', 'docs', 'ra2youli', 'YRpp'):
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
P('  旁证语料文件数 = %d' % len(corpus))
corr = {}
for c in distinct:
    pat = re.compile(rb'(?<![0-9A-Za-z])' + re.escape(c.encode()) + rb'(?![0-9A-Za-z])')
    corr[c] = sum(1 for _, d in corpus if pat.search(d))
zero = [c for c, v in corr.items() if v == 0]
P('  有旁证（>=1 文件）= %d / %d' % (len(distinct) - len(zero), len(distinct)))
P('  无旁证 = %s' % (zero or '无'))
ck('M3a 至少 30/36 候选值在本库其他文件里有整体出现',
   len(distinct) - len(zero) >= 30, '%d/%d' % (len(distinct) - len(zero), len(distinct)))

# ---------------------------------------------------------------- M4
P('')
P('=== M4 · 替换成 0x30 后 字节数 / CR / LF / 行数 / UTF-8 ===')
fixed = raw.replace(b'\x00', b'0')
P('  替换前：%d B / CR=%d / LF=%d / 行=%d' %
  (len(raw), raw.count(b'\r\n'), raw.count(b'\n'), len(raw.split(b'\n'))))
P('  替换后：%d B / CR=%d / LF=%d / 行=%d' %
  (len(fixed), fixed.count(b'\r\n'), fixed.count(b'\n'), len(fixed.split(b'\n'))))
ck('M4a 总字节数不变', len(raw) == len(fixed))
ck('M4b CR 不变（=1081）', raw.count(b'\r\n') == fixed.count(b'\r\n') == 1081,
   '%d -> %d' % (raw.count(b'\r\n'), fixed.count(b'\r\n')))
ck('M4c LF 不变', raw.count(b'\n') == fixed.count(b'\n'))
ck('M4d 行数不变', len(raw.split(b'\n')) == len(fixed.split(b'\n')))
def utf8_ok(b):
    try:
        b.decode('utf-8'); return True
    except UnicodeDecodeError:
        return False
u1, u2 = utf8_ok(raw), utf8_ok(fixed)
P('  严格 UTF-8 解码：替换前=%s 替换后=%s（0x00 在 UTF-8 里是合法码位 U+0000）' % (u1, u2))
ck('M4e 两侧都能严格 UTF-8 解码（⇒ CR 不变量对这条缺陷完全无感）', u1 and u2)

# ---------------------------------------------------------------- M5
P('')
P('=== M5 · rg 对当前文件的输出形态 ===')
# R74-g 修正：原选「口径对同类行」当对照短语，但该串在本库别处 0 命中
#   ⇒ 「干净文本搜不到」这个对照格是零信息格（与 R73 同族错误）。
# 改用**同内容对照**：把 43 个 0x00 换成 0x30 写成临时文件（仅此一处分歧），
#   在「同一内容、只差 43 字节」的两个文件上跑同一条 rg，差异只可能来自这 43 字节。
PHRASE = '连带义务'
def rg(args):
    p = subprocess.run(['rg'] + args, cwd=ROOT, capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')
rel_c = os.path.relpath(COMMON, ROOT)
rel_b = os.path.relpath(BOARD, ROOT)
TMPF = os.path.join(HERE, '_m5_fixed_probe.md')
io.open(TMPF, 'wb').write(fixed)
rel_t = os.path.relpath(TMPF, ROOT)
rc1, so1, se1 = rg(['-n', PHRASE, rel_c])
rc2, so2, se2 = rg(['-n', PHRASE, rel_t])
rc3, so3, se3 = rg(['--text', '-n', PHRASE, rel_c])
rc4, so4, se4 = rg(['-n', PHRASE, rel_b])
P('  短语 = %r（在 live 与还原副本里都存在）' % PHRASE)
P('  A) rg 当前 R14_COMMON.md（含 43 个 0x00）：rc=%d stdout=%r' % (rc1, so1[:100]))
P('  B) rg 还原副本（同内容、只差 43 字节）：rc=%d stdout=%r' % (rc2, so2[:100]))
P('  C) rg --text 当前 R14_COMMON.md：rc=%d stdout=%r' % (rc3, so3[:100]))
P('  D) rg 干净 STATUS_BOARD.md：rc=%d 命中行数=%d' % (rc4, so4.count('\n')))
ck('N4 rg 对当前文件报 binary 且不给行号',
   ('binary file matches' in (so1 + se1)) and PHRASE not in so1, so1[:60])
# R74-h 修正：rg 对**单个文件**参数不打印文件名，输出形态是「行号:内容」而不是「路径:行号:内容」。
#   原判据用 r':\d+:' 去要求两侧都有冒号 ⇒ 对单文件调用恒不成立，是我的判据错，不是数据错。
HAS_LINENO = re.compile(r'(?m)^\d+:')
ck('N4b 同内容的还原副本上 rg 给出「行号:内容」',
   rc2 == 0 and HAS_LINENO.search(so2) is not None, repr(so2[:40]))
ck('N4c 加 --text 后行号内容能出来（⇒ 不是没内容，是被 binary 判定挡住）',
   rc3 == 0 and HAS_LINENO.search(so3) is not None, repr(so3[:40]))
ck('N4d A 与 B 的差只可能来自那 43 字节（两文件字节数相同、内容仅此一处不同）',
   len(io.open(TMPF, 'rb').read()) == len(raw))
try:
    os.remove(TMPF)
except OSError:
    pass

# ---------------------------------------------------------------- M6
P('')
P('=== M6 · 候选值在「当前文本」vs「还原文本」里的命中数 ===')
fixed_txt, raw_txt = fixed.decode('utf-8'), raw.decode('utf-8')
lost = {}
for c in distinct:
    pat = re.compile(r'(?<![0-9A-Za-z])' + re.escape(c) + r'(?![0-9A-Za-z])')
    lost[c] = (len(pat.findall(raw_txt)), len(pat.findall(fixed_txt)))
tot_now = sum(v[0] for v in lost.values())
tot_fix = sum(v[1] for v in lost.values())
invisible = sorted(c for c, (a, b) in lost.items() if b > a)
P('  命中总数：当前=%d  还原后=%d  差=%d' % (tot_now, tot_fix, tot_fix - tot_now))
P('  有命中被 0x00 吃掉的候选值 = %d' % len(invisible))
ck('M6a 还原后命中数必须严格增加', tot_fix > tot_now, '%d -> %d' % (tot_now, tot_fix))
ck('N5 至少 20 个候选值存在「还原后才搜得到」的命中', len(invisible) >= 20, '%d' % len(invisible))

# ---------------------------------------------------------------- M7
P('')
P('=== M7 · 根因：一次 re.sub（repl 写成 r"\\0"）就能复现 ===')
probe = 'x 0x47C427 y 004393F0 z'
bad = re.sub(r'(?<![0-9A-Za-z])0(?=[0-9A-Za-z])', r'\0', probe)
good = re.sub(r'(?<![0-9A-Za-z])0(?=[0-9A-Za-z])', r'\g<0>', probe)
P('  repl=r"\\0"     -> %r' % bad)
P('  repl=r"\\g<0>"  -> %r' % good)
ck('N6 repl=r"\\0" 在 token 首字节处产出 0x00（与盘上形态一致）', bad.count('\x00') == 2, repr(bad))
ck('N6b repl=r"\\g<0>" 原样保留 0（反控：不是 re 模块的问题）', '\x00' not in good, repr(good))
ck('N6c 盘上 43 处的「token 首字节 = 0、前驱非字母数字」与 \\0 事故形态同构',
   all(not chr(s['prev'][0]).isalnum() for s in sites)
   and all(re.fullmatch(r'[0-9A-Za-z]+', s['tail']) for s in sites))

# ---------------------------------------------------------------- M8
P('')
P('=== M8 · 留存备份的 0x00 偏移集合 ===')
baks = []
for fn in sorted(os.listdir(BASE)):
    if 'R14_COMMON' not in fn:
        continue
    b = io.open(os.path.join(BASE, fn), 'rb').read()
    baks.append((fn, len(b), [m.start() for m in re.finditer(rb'\x00', b)]))
for fn, n, of in baks:
    P('  %-66s %8d B  0x00=%2d' % (fn, n, len(of)))
same = all(x[2] == baks[0][2] for x in baks) if baks else False
ck('M8a 全部备份的 0x00 偏移集合相同', same, '%d 份' % len(baks))
ck('M8b 备份份数 >= 10', len(baks) >= 10, '%d' % len(baks))
ck('M8c 每份备份的 0x00 计数都等于 live 的 43',
   all(len(x[2]) == 43 for x in baks), str([len(x[2]) for x in baks]))

# ---------------------------------------------------------------- 汇总
P('')
P('=== 汇总（全部为实测） ===')
P('  0x00 = %d 个，分布在 %d 行；distinct 候选值 = %d' %
  (len(sites), len({s['line'] for s in sites}), len(distinct)))
P('  可对账站点 %d 个，助记符吻合 %d、不吻合 %d；裸地址引用站点 %d 个（不计入对账）' %
  (len(annot), sum(1 for r in annot if r['match'] is True), n_bad, len(bare)))
P('  不变量：字节数 %d 不变 / CR 1081 不变 / LF %d 不变 / 行 %d 不变 / 两侧 UTF-8 可解'
  % (len(raw), raw.count(b'\n'), len(raw.split(b'\n'))))
P('  rg：当前文件被判 binary、不给行号；--text 才能出行号')
P('  可搜索性：命中 %d -> %d（+%d），%d 个候选值有命中被吃掉' %
  (tot_now, tot_fix, tot_fix - tot_now, len(invisible)))
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))

json.dump({'sites': records, 'corroboration': corr,
           'lost': {k: list(v) for k, v in lost.items()},
           'invisible': invisible,
           'summary': {'nul': len(sites), 'lines': len({s['line'] for s in sites}),
                       'distinct': len(distinct), 'annot': len(annot),
                       'match': sum(1 for r in annot if r['match'] is True),
                       'mismatch': n_bad, 'hits_now': tot_now, 'hits_fixed': tot_fix,
                       'fails': fails}},
          io.open(os.path.join(HERE, 'forensic_nul_r74.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(HERE, 'forensic_nul_r74.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
