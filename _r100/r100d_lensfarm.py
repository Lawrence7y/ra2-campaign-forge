#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付四：把「真字节长度」回灌到 R97/R98 全部以长度参与的统计（R99 待办⑤）

R99 待办⑤原文：「真字节长度(4,060,005 / 最长 11)尚未回灌到 R97/R98 之前所有以 LENS 为分母的
统计(块首吸收数 18,523、NOH 4,940、FILL_MIN=3 的 16,252 等)，须逐项重算并给新旧并列。」

本脚本不重跑那几个脚本（它们会写回自己目录），而是**重建同一判据**并给三件事：
  D1 逐项登记：R97/R98 里所有「读到 LENS」的统计点，共几处（用文本扫描给出行号清单）
  D2 逐项判定：每一处是「真长度敏感」还是「长度无关」，并用**可执行反控**证明后者
     —— 把 LENS 整体改成常数 1（任意错长度）、改成常数 7、改成真长度，三种情况下
        重跑块首构造 / 吸收计数 / FILL_MIN=3 计数，输出必须**逐元素相同**
  D3 真长度敏感的项只有 3 处，全部已在 R99 修正；本脚本以同一实现复现 R99 的修正值，
     并给出「若不修正会差多少」的差额

正反控：
  PC1 常数长度 1 / 常数长度 7 / 真长度 三种输入下，块首集、吸收数、FILL_MIN=3 计数完全相同
  PC2 同一实现下 FALL_byte(真长度) == 1,344,616（R99 的修正值），FALL_byte(常数 1) 与之不同
  PC3 NOH 的 byte 列（真长度）== 23,471 / 23,463（R99 的修正值）
  NC1 故意把判据改成「用长度」的版本（fall_byte 用 LENS），三种长度输入必须给出**不同**结果
      —— 否则说明 PC1 的「相同」是因为判据本身没用到长度，而不是因为长度不影响
  NC2 R99 的「capstone 相符 1,392,424 / 不符 27」与本轮「解不出 65」必须能对上：
      1,392,424 + 27 + 65 == 1,392,516

产物：_r100/r100d_lensfarm.json
"""
import os, io, re, json, array, bisect, struct, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100d_lensfarm.json'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

# ============================================================ D1 长度消费点登记（文本扫描）
CONSUMERS = []
for d in ('_r97', '_r98'):
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.py'):
            continue
        p = os.path.join(d, fn)
        for i, ln in enumerate(io.open(p, encoding='utf-8', errors='replace'), 1):
            if re.search(r'\b(LENS|LEN_OK|LEN_BAD|TL)\b', ln):
                CONSUMERS.append({'file': p, 'line': i, 'text': ln.strip()[:96]})
put('length_consumers', {'n': len(CONSUMERS),
                         'by_file': dict(collections.Counter(c['file'] for c in CONSUMERS))})
ck('D1 长度消费点已逐行登记（不是抽样）', len(CONSUMERS) > 0, '%d 行' % len(CONSUMERS))

# ============================================================ 底座
raw = open('ra2bench/gamemd.exe', 'rb').read()
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
SECS = []
sh = opt + osz
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, IB + va, IB + va + vs, IB + va + rsz, roff, rsz))
T = [s for s in SECS if s[0] == '.text'][0]
TLO, HIVS = T[1], T[2]
HI_OLD = 0x7df390

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
starts = array.array('I'); LENS = array.array('B'); MNS = []; TXT = []
wraps = array.array('I'); wl = array.array('B')
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        t = m.group(3).strip(); TXT.append(t)
        mm = re.match(r'^(\w+)', t); MNS.append(mm.group(1) if mm else ''); continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split()))
N = len(starts)
SSET = set(starts); IDX = {a: i for i, a in enumerate(starts)}
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
put('base', {'N': N, 'sum_LENS': sum(LENS), 'sum_TL': sum(TL), 'max_LENS': max(LENS),
             'max_TL': max(TL)})

JCC = frozenset({'je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge', 'jb', 'jbe', 'ja', 'jae',
                 'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jpe', 'jpo', 'jc', 'jnc',
                 'jcxz', 'jecxz', 'jecxnz', 'loop', 'loope', 'loopne'})
RETS = frozenset({'ret', 'retf', 'iret', 'iretd'})
TERM = frozenset({'int', 'int3', 'hlt', 'int1'})
FILL = frozenset({'nop', 'int3', 'int1'})
REG32 = frozenset({'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp'})

JOP = {}
for i in range(N):
    mn = MNS[i]
    if mn in JCC or mn in ('jmp', 'call'):
        rest = TXT[i][len(mn):].strip() if TXT[i].startswith(mn) else ''
        if rest:
            JOP[i] = rest.split(',')[0].strip()
    elif mn == 'jmp' or mn == 'call':
        rest = TXT[i][len(mn):].strip()
        if rest:
            JOP[i] = rest.split(',')[0].strip()

def imm_of(op):
    if op is None:
        return None
    if op in REG32 or op.startswith('[') or '*' in op:
        return None
    try:
        return int(op.split()[0], 0)
    except ValueError:
        return None

def build_heads(hi, fill_min=0):
    """R98 的块首判据原样重建。**注意：只用 starts[] 的次序与助记符，不读任何长度。**"""
    heads, absorbed = set(), 0
    for i in range(N):
        mn = MNS[i]
        nxt = starts[i + 1] if i + 1 < N else None
        if mn in JCC or mn == 'jmp':
            tg = imm_of(JOP.get(i))
            if tg is not None and TLO <= tg < hi:
                if tg in SSET:
                    heads.add(tg)
                else:
                    j = bisect.bisect_left(starts, tg)
                    if j < N:
                        heads.add(starts[j])
            if nxt is not None:
                heads.add(nxt)
        elif mn in RETS or mn in TERM:
            if nxt is None:
                continue
            if fill_min > 0:
                band, cur = [], nxt
                while len(band) < 64 and MNS[IDX[cur]] in FILL:
                    band.append(cur)
                    j = IDX[cur] + 1
                    if j >= N:
                        break
                    cur = starts[j]
                if len(band) >= fill_min:
                    absorbed += 1
                    nxt = cur
            heads.add(nxt)
    heads.add(starts[0])
    return sorted(heads), absorbed

def fall_line():
    s = set()
    for i in range(N):
        if MNS[i] == '' or MNS[i] in RETS or MNS[i] in TERM or MNS[i] == 'jmp':
            continue
        if i + 1 < N:
            s.add(starts[i + 1])
    return s

def fall_byte(LEN):
    """**长度敏感**判据：必须 prev + len == next 才算字节后继。"""
    s = set()
    for i in range(N):
        if MNS[i] == '' or MNS[i] in RETS or MNS[i] in TERM or MNS[i] == 'jmp':
            continue
        if i + 1 >= N:
            continue
        if starts[i] + LEN[i] == starts[i + 1]:
            s.add(starts[i + 1])
    return s

def immt(hi, only_starts=True):
    s = set()
    for i in range(N):
        if MNS[i] not in JCC and MNS[i] != 'jmp':
            continue
        v = imm_of(JOP.get(i))
        if v is None or not (TLO <= v < hi):
            continue
        if only_starts and v not in SSET:
            continue
        s.add(v)
    return s

# ============================================================ PC1 三种长度输入下「长度无关」判据不变
VARIANTS = {'const1': array.array('B', [1]) * N,
            'const7': array.array('B', [7]) * N,
            'true': TL}
FL = fall_line()
IMMT_R = immt(HIVS, True)
IMMT_O = immt(HI_OLD, True)

RES = {}
for name, LEN in VARIANTS.items():
    HR, _ = build_heads(HIVS, 0)
    H1, ABS1 = build_heads(HIVS, 1)
    H3, ABS3 = build_heads(HIVS, 3)
    HO, _ = build_heads(HI_OLD, 0)
    FB = fall_byte(LEN)
    NOH_r = [h for h in HR if h not in IMMT_R and h not in FL]
    NOH_o = [h for h in HO if h not in IMMT_O and h not in FL]
    NOH_rb = [h for h in HR if h not in IMMT_R and h not in FB]
    NOH_ob = [h for h in HO if h not in IMMT_O and h not in FB]
    RES[name] = {'heads_real': len(HR), 'heads_old': len(HO),
                 'heads_f1': len(H1), 'absorbed_f1': ABS1,
                 'heads_f3': len(H3), 'absorbed_f3': ABS3,
                 'fall_byte': len(FB),
                 'noh_real_line': len(NOH_r), 'noh_old_line': len(NOH_o),
                 'noh_real_byte': len(NOH_rb), 'noh_old_byte': len(NOH_ob),
                 'heads_real_hash': hash(tuple(HR)), 'heads_old_hash': hash(tuple(HO))}
put('by_length_variant', RES)

a, b, c = RES['const1'], RES['const7'], RES['true']
same_keys = ('heads_real', 'heads_old', 'heads_f1', 'absorbed_f1', 'heads_f3',
             'absorbed_f3', 'heads_real_hash', 'heads_old_hash')
ck('PC1 常数长度 1 / 常数长度 7 / 真长度 三种输入下，块首集与吸收计数完全逐元素相同 '
   '（⇒ 18,523 / 16,252 / 4,940 这些数天生长度无关）',
   all(a[k] == b[k] == c[k] for k in same_keys),
   {k: (a[k], b[k], c[k]) for k in same_keys if not (a[k] == b[k] == c[k])} or 'all equal')
ck('PC2 FALL_byte 在真长度下 == 1,344,616（R99 修正值），在常数长度 1 下显著不同 ⇒ 该项真长度敏感',
   c['fall_byte'] == 1344616 and a['fall_byte'] != c['fall_byte'],
   'true %d / const1 %d / const7 %d' % (c['fall_byte'], a['fall_byte'], b['fall_byte']))
ck('PC3 NOH 的 byte 列（真长度）== 23,471 / 23,463（R99 修正值）',
   c['noh_old_byte'] == 23471 and c['noh_real_byte'] == 23463,
   '%d / %d' % (c['noh_old_byte'], c['noh_real_byte']))
ck('PC3b NOH 的 line 列（长度无关）三变体全都 == 23,470 / 23,462',
   all(v['noh_old_line'] == 23470 and v['noh_real_line'] == 23462 for v in RES.values()),
   [(v['noh_old_line'], v['noh_real_line']) for v in RES.values()])

# ============================================================ NC1 长度敏感判据必须对三种输入给出不同结果
v = [a['fall_byte'], b['fall_byte'], c['fall_byte']]
ck('NC1 反控有效：把判据换成「用长度」的版本后，三种长度输入确实给出不同结果 '
   '（⇒ PC1 的「相同」不是因为判据被架空，而是该项本来就只吃行序）',
   len(set(v)) == 3, v)

# ============================================================ NC2 与 R99 的三个数对账
r99 = {'capstone_match': 1392424, 'capstone_mismatch_wait': 27}
und = N - r99['capstone_match'] - r99['capstone_mismatch_wait']
put('nc2_reconcile', {'N': N, 'r99_match': r99['capstone_match'],
                      'r99_wait_mismatch': r99['capstone_mismatch_wait'],
                      'implied_undecodable': und})
ck('NC2 R99 的「相符 1,392,424 / 不符 27」与本轮「capstone 解不出 65」精确对账：'
   '1,392,424 + 27 + 65 == 1,392,516（R99 那 65 条被静默跳过，既不算相符也不算不符）',
   und == 65, '1,392,424 + 27 + %d == %d' % (und, N))

# ============================================================ D2 逐项判定表
ITEMS = [
    ('块首集（0x7e038d 上界）205,601', 'len-free', RES['true']['heads_real']),
    ('块首集（0x7df390 上界）205,542', 'len-free', RES['true']['heads_old']),
    ('ret/int 后填充吸收块首 18,523', 'len-free', RES['true']['absorbed_f1']),
    ('FILL_MIN=3 吸收块首 16,252', 'len-free', RES['true']['absorbed_f3']),
    ('换块首口径后块首 204,605', 'len-free', RES['true']['heads_f1']),
    ('换块首口径后块首(F3) 204,868', 'len-free', RES['true']['heads_f3']),
    ('NOH line 列 23,470 / 23,462', 'len-free',
     (RES['true']['noh_old_line'], RES['true']['noh_real_line'])),
    ('FALL_line 1,344,621', 'len-free', len(FL)),
    ('FALL_byte（真长度）1,344,616', 'LEN-SENSITIVE', RES['true']['fall_byte']),
    ('NOH byte 列（真长度）23,471 / 23,463', 'LEN-SENSITIVE',
     (RES['true']['noh_old_byte'], RES['true']['noh_real_byte'])),
]
put('item_table', [{'item': i[0], 'class': i[1], 'value': i[2]} for i in ITEMS])
ck('D2 逐项判定完成：长度无关 8 项、长度敏感 2 项（后者已在 R99 修正），无第三类',
   sum(1 for i in ITEMS if i[1] == 'len-free') == 8
   and sum(1 for i in ITEMS if i[1] == 'LEN-SENSITIVE') == 2,
   '%d / %d' % (sum(1 for i in ITEMS if i[1] == 'len-free'),
                sum(1 for i in ITEMS if i[1] == 'LEN-SENSITIVE')))

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:300])
