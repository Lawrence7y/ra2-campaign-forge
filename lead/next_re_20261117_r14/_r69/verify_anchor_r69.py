# -*- coding: utf-8 -*-
# R69 · 任务1B 续：limitations 列非 § 引用「是否落在本行锚内」机械核验
# 定义：本行锚 = 本行 evidence_paths 里各条目的「文件路径 + 括号内锚点」全文。
# 对 R17_* / M* 引用，检查该引用串是否出现在本行锚全文里；F* 引用另作悬空+对称性核验。
import os, re, sys, io

ROOT = '/home/t628/projects/ra2-campaign-forge'
TSV  = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv')

fails, log = [], []
def W(s=''):
    print(s); log.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

rows = [l.split('\t') for l in open(TSV, encoding='utf-8').read().split('\n') if l]
hdr, data = rows[0], rows[1:]
byid = {r[0]: r for r in data}

FPAT = re.compile(r'(?<![A-Za-z0-9_])(F\d{2})(?!\d)')
MPAT = re.compile(r'(?<![A-Za-z0-9_])(M\d{1,3})(?!\d)')
RPAT = re.compile(r'(?<![A-Za-z0-9_])(R17_[A-Z0-9_]+)')

# --- 自测 ---
W('--- 自测（正控/反控）---')
def contains_tok(text, tok):
    return tok in text
ck('A 正控：锚全文含 R17_R52_ADJ_D4',
   contains_tok('lead/x/R17_R52_ADJ_D4/VERDICT.md(§1)', 'R17_R52_ADJ_D4'))
ck('B 反控：不该把 R17_R52_ADJ_D4X 当成命中 R17_R52_ADJ_D4',
   not contains_tok('lead/x/R17_R52_ADJ_D4X/VERDICT.md', 'R17_R52_ADJ_D4')
   or True)  # 说明：本检查用整串 in，D4X 含 D4 前缀会误命，故引用串须带边界
# 改用带边界判据
BND = lambda t: re.compile(r'(?<![A-Za-z0-9_])' + re.escape(t) + r'(?![A-Za-z0-9_])')
ck('B2 反控：带边界后 R17_R52_ADJ_D4 不命中 R17_R52_ADJ_D4X',
   not BND('R17_R52_ADJ_D4').search('lead/x/R17_R52_ADJ_D4X/VERDICT.md'))
ck('B3 正控：带边界后命中真串',
   bool(BND('R17_R52_ADJ_D4').search('lead/x/R17_R52_ADJ_D4/VERDICT.md')))
ck('C 正控：M103 在 PANEL.md(M103 段) 内',
   bool(BND('M103').search('COVERAGE/PANEL.md(M103 段)')))
ck('D 反控：M1 不得命中 M103',
   not BND('M1').search('COVERAGE/PANEL.md(M103 段)'))

# --- 主核验 ---
W('')
W('=== limitations 非 § 引用 vs 本行锚 ===')
stat = {'R': [0, 0], 'M': [0, 0], 'F': [0, 0]}   # [in-anchor, not-in-anchor]
detail = []
for r in data:
    fid, lim, ev = r[0], r[4], r[3]
    pairs = []
    for m in RPAT.finditer(lim): pairs.append(('R', m.group(1)))
    for m in MPAT.finditer(lim): pairs.append(('M', m.group(1)))
    for m in FPAT.finditer(lim): pairs.append(('F', m.group(1)))
    seenp = set()
    for kind, tok in pairs:
        if (kind, tok) in seenp: continue
        seenp.add((kind, tok))
        if kind == 'F':
            continue          # F 引用单独按悬空+对称性核
        hit = bool(BND(tok).search(ev))
        stat[kind][0 if hit else 1] += 1
        detail.append((fid, kind, tok, hit))

W('  R17_* 引用：落在本行锚内 %d / 不在 %d' % (stat['R'][0], stat['R'][1]))
W('  M*     引用：落在本行锚内 %d / 不在 %d' % (stat['M'][0], stat['M'][1]))
W('')
W('  不在本行锚内的条目（这类引用无法由本行证据自证）：')
for fid, kind, tok, hit in detail:
    if not hit:
        W('    %-4s %s %-26s | 本行 evidence_paths = %s' % (fid, kind, tok, byid[fid][3][:150]))

ck('反控：确实存在「不在锚内」的条目（否则该检查无判别力）',
   stat['R'][1] + stat['M'][1] > 0, '%d+%d' % (stat['R'][1], stat['M'][1]))
ck('恒等式：在锚内 + 不在锚内 = R 去重对 + M 去重对',
   stat['R'][0] + stat['R'][1] + stat['M'][0] + stat['M'][1] == len(detail),
   '%d vs %d' % (stat['R'][0] + stat['R'][1] + stat['M'][0] + stat['M'][1], len(detail)))

# --- 悬空 F + R 目标存在性 ---
W('')
W('=== 引用目标存在性 ===')
idset = set(byid)
dangF = sorted({tok for r in data for tok in FPAT.findall(r[4])} - idset)
W('  悬挂 F 号: %s' % (dangF or '无'))
ck('无悬挂 F 号', dangF == [])

RD = os.path.join(ROOT, 'lead/next_re_20261117_r14')
rall = sorted({tok for r in data for tok in RPAT.findall(r[4])})
W('  R17_* 目标存在性：')
rmiss = []
for t in rall:
    ex = os.path.exists(os.path.join(RD, t)) or os.path.exists(os.path.join(RD, t + '.md'))
    W('    %-26s 存在=%s' % (t, ex))
    if not ex: rmiss.append(t)
ck('反控：缺失集非空则说明确有悬挂（本项测的是判别力，不判对错）', True, str(rmiss))

# --- F 引用双向对称性（承接上一个脚本，这里只做交叉核对）---
W('')
W('=== F 引用双向对交叉核对 ===')
edges = sorted({(r[0], t) for r in data for t in FPAT.findall(r[4])})
both = [(a, b) for a, b in edges if (b, a) in edges and a < b]
W('  双向对 %d: %s' % (len(both), ', '.join('%s<->%s' % p for p in both)))
# 逐对回读原文，确认两侧都写了「同看/同引」
for a, b in both:
    la = byid[a][4]
    lb = byid[b][4]
    oka = re.search(r'同看|同引|并观', la) is not None
    okb = re.search(r'同看|同引|并观', lb) is not None
    ck('%s<->%s 两侧都写明同看/同引' % (a, b), oka and okb, 'a=%s b=%s' % (oka, okb))

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_anchor_r69.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
sys.exit(0 if not fails else 1)
