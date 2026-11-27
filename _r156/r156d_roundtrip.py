#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R156 D：承载性判据的**鉴别力边界** —— round-trip 检验。

C 脚本证明：把证据项声明的**全部**路径都算进来，12/12 都是 FULL（100%）。
这个结果是真是假？两种解释：
  ① 真：这 12 个 fid 的证据链确实完备。
  ② 空：statement 本来就是从这些路径里抄出来的，逐字必中 ⇒ 判据结构上不可能失败。

判据 ② 的机械判法：statement 的可核取值集合 S 是否 **被** 证据路径文本 T 的取值集合**包含**（S ⊆ T）。
若 S ⊆ T 对绝大多数 fid 成立，则「承载性 100%」是 round-trip 的产物，不是独立佐证。

反控：至少要有若干 fid 的 S 不被 T 包含（否则说明我的包含判据写错了，任何人都能"通过"）。

只判判据的鉴别力，不改 GRADE、不改 evidence_paths、不判事实真假。
"""
import os, re, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D    = ROOT + '/lead/next_re_20261117_r14'
LED  = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
IDX  = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
OUT  = ROOT + '/_r156/r156d_roundtrip.json'

fails = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

def addr_set(s):
    o = set()
    for m in re.finditer(r'(?i)(?<![0-9a-z])0x([0-9a-f]{3,8})(?![0-9a-z])', s): o.add(int(m.group(1), 16))
    for m in re.finditer(r'(?i)(?<![0-9a-z])([0-9a-f]{8})(?![0-9a-z])', s): o.add(int(m.group(1), 16))
    return o

def num_set(s):
    s = re.sub(r'(?<![0-9A-Za-z.])(\d{1,3}(?:,\d{3})+)', lambda m: ' %s ' % m.group(1).replace(',', ''), s)
    s = re.sub(r'§\s*\d+', ' §SEC ', s)
    return set(int(x) for x in re.findall(r'(?<![0-9A-Za-z.])(\d{3,7})(?![0-9A-Za-z])', s))

# 复用 C 的路径解析结果
C = json.load(open(ROOT + '/_r156/r156c_allpaths.json', encoding='utf-8'))
rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
data = {r[0]: r for r in rows[1:]}
t = open(LED, encoding='utf-8').read()
secpos = {}
for m in re.finditer(r'(?m)^## §(\d+[A-Za-z]?) ·', t): secpos.setdefault(m.group(1), []).append(m.start())
def ledger_sec(num):
    p = secpos[num][0]; nx = re.search(r'(?m)^## §', t[p + 10:])
    return t[p:p + 10 + nx.start()] if nx else t[p:]
def ledger_items(num):
    s = ledger_sec(num); hs = []
    for m in re.finditer(r'(?m)^###\s+(.*)$', s):
        h = m.group(1); mm = re.match(r'(?:事项\s*)?([1-9])\s*[\.·、]', h)
        hs.append((m.start(), int(mm.group(1)) if mm else None))
    return [(n, s[p:(hs[i+1][0] if i+1 < len(hs) else len(s))]) for i, (p, n) in enumerate(hs)]
def ledger_item(num, ix):
    for n, tx in ledger_items(num):
        if n == ix: return tx
    return None

rc = open(D + '/R14_COMMON.md', encoding='utf-8', errors='replace').read()
ba = open(D + '/BOARD_ARCHIVE.md', encoding='utf-8', errors='replace').read()
sup = open(D + '/R17_LEDGER_1063/SUPERSEDED.md', encoding='utf-8').read()
def rc_section(n):
    m = re.search(r'(?m)^## %s\b' % re.escape(n), rc)
    if not m: return None
    nx = re.search(r'(?m)^## 2\.\d+\b', rc[m.start() + 5:])
    return rc[m.start(): m.start() + 5 + nx.start()] if nx else rc[m.start():]
def ba_round(n):
    m = re.search(r'(?m)^##.*R17 第 %d 轮' % n, ba)
    if not m: return None
    nx = re.search(r'(?m)^##\s', ba[m.start() + 5:])
    return ba[m.start(): m.start() + 5 + nx.start()] if nx else ba[m.start():]

RE_LEDGER = re.compile(r'R17_LEDGER_([0-9A-Za-z]+)[\\/]+(SECTION\.md|SUPERSEDED\.md)(?:\(([^)]*)\))?')
RE_RC = re.compile(r'R14_COMMON\.md\(([^)]*)\)')
RE_BA = re.compile(r'BOARD_ARCHIVE\.md\(([^)]*)\)')
RE_GOAL = re.compile(r'GOAL_THREE_TARGETS_20261018\.md\(([^)]*)\)')
RE_FILE = re.compile(r'(lead[\\/][^\s;()]+\.(?:tsv|md|json|py))')

def path_text(fid):
    """该 fid 声明的**全部**路径拼成的文本（含 1063R→§1063 重定向）。"""
    parts = []
    for it in data[fid][3].split(';'):
        it = it.strip()
        if not it: continue
        m = RE_LEDGER.search(it)
        if m:
            num, fn, topic = m.group(1), m.group(2), (m.group(3) or '')
            tp = topic.replace('事项', '').strip()
            if fn == 'SUPERSEDED.md': parts.append(sup); continue
            if num in secpos: parts.append(ledger_sec(num)); continue
            if num == '1063R':
                mm = re.match(r'\d+', tp)
                if mm: parts.append(ledger_item('1063', int(mm.group(0))) or '')
            continue
        m = RE_RC.search(it)
        if m: parts.append(''.join(rc_section(x) or '' for x in re.findall(r'(2\.\d+)', m.group(1)))); continue
        m = RE_BA.search(it)
        if m:
            mm = re.search(r'第\s*(\d+)\s*轮', m.group(1))
            if mm: parts.append(ba_round(int(mm.group(1))) or '')
            continue
        m = RE_GOAL.search(it)
        if m: parts.append(''.join(ledger_sec(x) for x in re.findall(r'§(\d+[A-Za-z]?)', m.group(1)) if x in secpos)); continue
        m = RE_FILE.search(it)
        if m:
            p = os.path.join(ROOT, m.group(1).replace('\\', '/'))
            if os.path.isfile(p):
                try: parts.append(open(p, encoding='utf-8', errors='replace').read())
                except Exception: pass
    return ''.join(parts)

FIDS = ['F04', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16']
print('  --- round-trip 检验：statement 取值集 S 是否被 证据路径取值集 T 包含 ---')
recs = []
for f in FIDS:
    S_a, S_n = addr_set(data[f][1]), num_set(data[f][1])
    T = path_text(f)
    T_a, T_n = addr_set(T), num_set(T)
    sub_a = S_a <= T_a; sub_n = S_n <= T_n
    recs.append(dict(fid=f, addr_n=len(S_a), addr_subset=sub_a,
                     num_n=len(S_n), num_subset=sub_n,
                     addr_out=sorted('0x%X' % v for v in S_a - T_a),
                     num_out=sorted(S_n - T_n),
                     path_much_larger=(len(T_a) > len(S_a))))
    print('   %-4s addr S=%-2d 包含=%-5s | num S=%-2d 包含=%-5s | T 的地址比 S 多=%-5s %s'
          % (f, len(S_a), sub_a, len(S_n), sub_n, len(T_a) > len(S_a),
             ('' if (sub_a and sub_n) else '缺口=%s' % (recs[-1]['addr_out'] + [str(x) for x in recs[-1]['num_out']]))))

n_addr_sub = sum(1 for r in recs if r['addr_subset'])
n_num_sub  = sum(1 for r in recs if r['num_subset'])
n_both     = sum(1 for r in recs if r['addr_subset'] and r['num_subset'])
print('  addr S⊆T: %d/12 | num S⊆T: %d/12 | 两者都成立: %d/12' % (n_addr_sub, n_num_sub, n_both))

ck('1.1 addr 轴 S⊆T 至少 10/12（round-trip 成立）', n_addr_sub >= 10, n_addr_sub)
ck('1.2 num 轴 S⊆T 至少 10/12', n_num_sub >= 10, n_num_sub)
ck('1.3 两轴同时成立的 fid >= 10（⇒「承载 100%」是 round-trip 产物）', n_both >= 10, n_both)
# S-419：上一版这里写成「至少 1 个 fid 不被包含」，那是把**期望的数据结论**写进断言了 ——
# 实测就是 12/12 全被包含（这正是本轮的发现）。反控必须换成「喂错的 T 必须不成立」，见 1.7。
ck('1.4 结论：S⊆T 在 12/12 全成立 ⇒ 承载率 100% 是 round-trip 的必然结果，不是独立佐证',
   n_both == 12, n_both)
ck('1.5 反控：T 的取值集普遍**严格大于** S（说明 T 不是 S 的同义重复，round-trip 只朝一个方向）',
   sum(1 for r in recs if r['path_much_larger']) >= 6, sum(1 for r in recs if r['path_much_larger']))
# 正控：C 脚本的 with-redirect 100% 与此处 S⊆T 自洽
allfull = all(m['rate'] == 100.0 or m['rate'] is None for m in C['matrix'])
ck('1.6 正控：与 C 的口径自洽（C 报 with-redirect 全 100%，此处 S⊆T 亦近乎全成立）',
   allfull and n_both >= 10, (allfull, n_both))

# 最强反控：把一个不相关的 fid 的路径当 T，S⊆T 必须不成立
S_a = addr_set(data['F08'][1])
T_wrong = path_text('F11')
ck('1.7 反控：拿 F11 的路径当 F08 的 T，S⊆T 必须不成立',
   not (S_a <= addr_set(T_wrong)), sorted('0x%X' % v for v in S_a - addr_set(T_wrong)))

json.dump(dict(records=recs, n_addr_subset=n_addr_sub, n_num_subset=n_num_sub, n_both=n_both, fails=fails),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('  写出 %s' % OUT)
print('  === FAIL %d ===' % len(fails))
sys.exit(0 if not fails else 1)
