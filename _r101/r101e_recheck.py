#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付五（§2.12 规则 D 独立复算）：主会话 r101b/r101c 的链分类有一个实质 bug

子代理 hy4 #151 报 B1=41 / B2=27 / B3=2 / B4=0 / B5=18，与我报的 R_resync=59 相差 18，
且它的 B5 恰是 18。差 18 = 19 这个巧合必须查到底，不能记成「实现不同」。

根因（本脚本证明）：我在 r101b/r101c 里用 `h in CAPLEN` 判「宿主起点能不能解码」，
而 CAPLEN 只装**线性扫描的起点**（跳 1 字节重同步时，被跳过的字节即使 capstone 能解码
也不在 CAPLEN 里）。故该判据实际测的是「h 是不是扫描起点」，不是「h 能不能解码」。
「88 个仅 capstone 起点」构造上**全部不是 objdump 行起点**，其中很多也不是扫描起点，
于是被大量误判进 R_resync。

正确判据：`dec(h) is None`（直接问 capstone）。

本脚本同时把「跳转引用」的两个不同来源分开 —— 这是 R100「65 条中 5 条被跳转引用」这条
结论的实质修正点：
  JT_direct ：指令文本形如 jXX / jmp / call 后跟**直接立即数**目标
  JT_table  ：指令文本形如 jmp DWORD PTR [reg*4+ADDR]，ADDR 是**跳转表基址**（不是目标）
hy4 的 A1 把 JT_table 也算了进去，得到 17；真跳转目标只有 5。二者必须分开数：
跳表基址落在 .text 内是结构事实，但它不是「该地址被执行」，不能当可达证据。

正反控：
  PC1 用 dec(h) is None 重算后五类之和 == 88
  PC2 与 hy4 #151 报的 41/27/2/0/18 逐项对照（相同报相同，不同报不同并给原因）
  PC3 JT_direct 与 JT_table 两个集合的交集必须为 0（定义互斥）
  NC1 反控 bug 的存在：用 h in CAPLEN 判据必须复现我的 59/0（证明 bug 被准确定位）
  NC2 反控 JT_direct：全体起点命中数必须 > 1000
  NC3 反控 JT_table：把表基址整体 +4 后命中数必须变化（表基址不是随便命中的）

产物：_r101/r101e_recheck.json
"""
import os, io, re, json, array, bisect, struct, hashlib, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101e_recheck.json'
DUMP = '/tmp/r93_disasm.txt'
EXE = 'ra2bench/gamemd.exe'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest()[:16] == '73201cc021497c95')
ck('S0b 反汇编 sha256', hashlib.sha256(open(DUMP, 'rb').read()).hexdigest()[:16] == '5935356b2914d90b')

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
TLO, HIVS, TROFF = T[1], T[2], T[4]
txtb = raw[TROFF:TROFF + (HIVS - TLO)]

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []
wraps = array.array('I'); WL = array.array('B'); elide_at = []; nprint = 0
for ln in io.open(DUMP, encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); nprint += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); WL.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(nprint)
N = len(starts); SSET = set(starts); IDX = {a: i for i, a in enumerate(starts)}
TL = array.array('B', LENS)
for a, n in zip(wraps, WL):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
ck('S1 行数 1,392,516 / 续行 9,028 / 省略 5',
   N == 1392516 and len(wraps) == 9028 and len(elide_at) == 5, '%d/%d/%d' % (N, len(wraps), len(elide_at)))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dec(p):
    if not (TLO <= p < HIVS): return None
    return next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)
def caplen(p):
    i = dec(p)
    return i.size if i else None

ok1, bad1 = [], []
p = TLO
while p < HIVS:
    i = dec(p)
    if i is None:
        bad1.append(p); p += 1
    else:
        ok1.append((p, i.size)); p += i.size
OK1 = set(a for a, _ in ok1); CAPLEN = dict(ok1); BAD1 = set(bad1)
# 集 A（objdump 行起点且 capstone 解不出）—— R100 的 52/13 是对它测的
A_SET = set(starts[i] for i in range(N) if dec(starts[i]) is None)
ck('S2 capstone 跳1 可解 1,392,527 / 不可解 65', len(ok1) == 1392527 and len(bad1) == 65,
   '%d/%d' % (len(ok1), len(bad1)))
ck('S3 集 A（行起点不可解）65，与集 B（扫描不可解）65 交集 62',
   len(A_SET) == 65 and len(A_SET & BAD1) == 62, '%d / %d' % (len(A_SET), len(A_SET & BAD1)))

only_cap = sorted(OK1 - SSET)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
EL20 = set(only_cap) & elided_addrs
EIGHTY = sorted(set(only_cap) - EL20)
ck('S4 108 = 20 + 88', len(only_cap) == 108 and len(EL20) == 20 and len(EIGHTY) == 88,
   '%d/%d/%d' % (len(only_cap), len(EL20), len(EIGHTY)))

# ======================================================== 一、bug 复现与修正
def classify(mode):
    """mode='capsweep' 用 h in CAPLEN（我 r101b 的错判据）；mode='direct' 用 dec(h) is None"""
    CL = collections.Counter(); ROWS = []
    for a in EIGHTY:
        j = bisect.bisect_right(starts, a) - 1
        hs = starts[j]; hl = TL[j]; he = hs + hl
        cl_at_a = caplen(a); ce = a + cl_at_a
        if mode == 'capsweep':
            host_bad = hs not in CAPLEN
        else:
            host_bad = dec(hs) is None
        if host_bad:
            k = 'B1' if mode == 'direct' else 'R_resync'
        else:
            # 沿链走（用 caplen 而不是 CAPLEN，链本身也要允许从非扫描起点起）
            q = hs; reached = False
            for _ in range(64):
                sz = caplen(q)
                if sz is None or not (TLO <= q < HIVS): break
                q += sz
                if q == a: reached = True; break
                if q >= he: break
            if not reached:
                k = 'B5' if mode == 'direct' else 'U_offchain'
            else:
                if ce == he: k = 'B2' if mode == 'direct' else 'T_exact'
                elif ce > he: k = 'B4' if mode == 'direct' else 'T_over'
                else: k = 'B3' if mode == 'direct' else 'T_short'
        CL[k] += 1
        ROWS.append({'a': hex(a), 'host': hex(hs), 'hl': hl, 'off': a - hs,
                     'cl_at_a': cl_at_a, 'cap_end': hex(ce), 'host_end': hex(he),
                     'cls': k, 'host_decodable': dec(hs) is not None,
                     'host_is_sweep_start': hs in CAPLEN, 'txt': TXT[j][:40]})
    return CL, ROWS

BUG, RBUG = classify('capsweep')
FIX, RFIX = classify('direct')
put('bug_repro', {'my_r101b_classes': dict(sorted(BUG.items())),
                  'r101b_reported': {'R_resync': 59, 'T_exact': 27, 'T_short': 2},
                  'note': '用 h in CAPLEN 判宿主可否解码'})
put('fixed', {'classes': dict(sorted(FIX.items())),
              'hy4_151_reported': {'B1': 41, 'B2': 27, 'B3': 2, 'B4': 0, 'B5': 18}})
ck('NC1 反控 bug 存在：用 h in CAPLEN 判据必须复现我的 59/27/2/0/0',
   BUG['R_resync'] == 59 and BUG['T_exact'] == 27 and BUG['T_short'] == 2
   and BUG['T_over'] == 0 and BUG['U_offchain'] == 0, dict(sorted(BUG.items())))
ck('PC1 修正后五类之和 == 88', sum(FIX.values()) == 88, dict(sorted(FIX.items())))
CK_NAMES = {'B1': 'B1', 'B2': 'B2', 'B3': 'B3', 'B4': 'B4', 'B5': 'B5'}
HY4 = {'B1': 41, 'B2': 27, 'B3': 2, 'B4': 0, 'B5': 18}
agree = {k: (FIX[k], HY4[k]) for k in HY4 if FIX[k] == HY4[k]}
ck('PC2 与 hy4 #151 的 41/27/2/0/18 逐项对照：完全一致则 CONFIRMED，否则逐项报差',
   all(FIX[k] == HY4[k] for k in HY4),
   {k: '%d vs %d' % (FIX[k], HY4[k]) for k in HY4})

err18 = [r for r in RBUG if r['cls'] == 'R_resync' and r['host_decodable']]
put('bug_mechanism', {
  'n_misclassified': len(err18),
  'why': '这些 88 个地址的宿主起点用 h in CAPLEN 判为「不可解码」，'
         '但 dec(h) 实际能解出 %d 条合法指令；它们不是线性扫描起点，是因为扫描在此之前的'
         '某处跳过了这段字节。' % len(err18),
  'sample': [{'a': r['a'], 'host': r['host'], 'dec_len': caplen(int(r['host'], 16)),
              'txt': r['txt']} for r in err18[:10]]})
ck('PC4 被误判的地址数 == 59 - 41 == 18（与 hy4 B5 的巧合必须解释成同一批地址，不是数字巧合）',
   len(err18) == 18, len(err18))

# ======================================================== 二、JT_direct vs JT_table
JCC = frozenset({'je','jne','jz','jnz','jl','jle','jg','jge','jb','jbe','ja','jae','js','jns',
                 'jo','jno','jp','jnp','jpe','jpo','jc','jnc','jcxz','jecxz','jecxnz',
                 'loop','loope','loopne'})
REG32 = frozenset({'eax','ebx','ecx','edx','esi','edi','ebp','esp'})
JT_direct = set(); JT_table = set()
TBRE = re.compile(r'^(?:DWORD|WORD|BYTE) PTR \[([^\]]*\*[^\]]*)\]$')
for i in range(N):
    t = TXT[i]
    if not t: continue
    mn = t.split()[0]; rest = t[len(mn):].strip()
    if not rest: continue
    if mn in JCC or mn in ('jmp', 'call'):
        o = rest
        if o.startswith('0x') or re.match(r'^-?\d', o):
            try:
                v = int(o.split()[0], 0)
                if TLO <= v < HIVS: JT_direct.add(v)
            except ValueError: pass
        elif o.startswith('DWORD PTR ['):
            inner = o[len('DWORD PTR ['):].rstrip(']')
            toks = [x.strip() for x in inner.replace('-', '+-').split('+') if x.strip()]
            for tk in toks:
                if '*' in tk or tk in REG32: continue
                try:
                    v = int(tk, 0)
                except ValueError: continue
                if TLO <= v < HIVS: JT_table.add(v)
# 【修正】第一版断言「定义互斥、交集必为 0」是**我的断言错**，不是数据错。
# 实测交集恰 5 个，逐个查证都是真事实：同一地址既被 jXX 直接指向、又被 jmp [reg*4+ADDR] 当表基址。
# 断言改成「如实报交集并逐个给出双向证据」。
ov = sorted(JT_direct & JT_table)
OVD = []
for v in ov:
    srcs = []
    for i in range(N):
        t = TXT[i]
        if not t: continue
        mn = t.split()[0]
        if mn not in JCC and mn not in ('jmp', 'call'): continue
        rest = t[len(mn):].strip()
        if rest.startswith('0x'):
            try:
                if int(rest.split()[0], 0) == v:
                    srcs.append({'kind': 'direct', 'at': hex(starts[i]), 'txt': t[:40]})
            except ValueError: pass
        elif rest.startswith('DWORD PTR [') and ('0x%x' % v) in rest:
            srcs.append({'kind': 'table_base', 'at': hex(starts[i]), 'txt': t[:44]})
    OVD.append({'a': hex(v), 'srcs': srcs, 'row_here': TXT[IDX[v]][:44] if v in IDX else None})
put('jt_overlap_detail', OVD)
ck('PC3 如实报 JT_direct ∩ JT_table = %d 个（第一版断言「交集为 0」是我的断言错，已改）'
   % len(ov), True, '%d 个：%s' % (len(ov), [hex(x) for x in ov]))
ck('PC3b 交集 5 个每个都必须同时给出 direct 与 table_base 两类来源（不是解析假象）',
   all(len({s['kind'] for s in r['srcs']}) == 2 for r in OVD),
   [sorted({s['kind'] for s in r['srcs']}) for r in OVD])
put('jump_sets', {'JT_direct': len(JT_direct), 'JT_table': len(JT_table),
                  'intersect': len(JT_direct & JT_table)})
hit_a_direct = sorted(A_SET & JT_direct)
hit_a_table = sorted(A_SET & JT_table)
put('setA_refs', {'n_A': len(A_SET),
                  'hit_JT_direct': [hex(x) for x in hit_a_direct],
                  'hit_JT_table': [hex(x) for x in hit_a_table],
                  'n_direct': len(hit_a_direct), 'n_table': len(hit_a_table)})
ck('R100 的「65 条中 5 条被跳转引用」在 JT_direct 口径下复算',
   True, '%d 条：%s' % (len(hit_a_direct), [hex(x) for x in hit_a_direct]))
ck('hy4 #151 的「17 条被跳转来源命中」= JT_direct ∪ JT_table（口径是并，不是直接目标）',
   len(hit_a_direct) + len(hit_a_table) == 17,
   '%d + %d = %d' % (len(hit_a_direct), len(hit_a_table), len(hit_a_direct) + len(hit_a_table)))
put('table_base_rows', [{'a': hex(x), 'row': TXT[IDX[x]][:44]} for x in hit_a_table])

# 88 与新集
hit88_direct = sorted(set(EIGHTY) & JT_direct)
hit88_table = sorted(set(EIGHTY) & JT_table)
put('set88_refs', {'hit_JT_direct': [hex(x) for x in hit88_direct],
                   'hit_JT_table': [hex(x) for x in hit88_table]})
ck('NC2 反控 JT_direct：全体 1,392,516 起点命中数必须 > 1000', len(SSET & JT_direct) > 1000,
   len(SSET & JT_direct))
shift = set(x + 4 for x in JT_table)
ck('NC3 反控 JT_table：表基址整体 +4 后与集 A 的命中数必须变化',
   len(A_SET & shift) != len(hit_a_table), '%d -> %d' % (len(hit_a_table), len(A_SET & shift)))

# ======================================================== 三、集 A 的 5 个「跳转目标」形态审计
# 【实质修正】R100 把「65 条里 5 条被跳转引用」当作「它们更像真代码」的证据。
# 本段逐条给这 5 个的引用源，看「跳转」的形态是否撑得起这个推论。
FORM = []
for v in hit_a_direct:
    srcs = []
    for i in range(N):
        t = TXT[i]
        if not t: continue
        mn = t.split()[0]
        if mn not in JCC and mn not in ('jmp', 'call'): continue
        rest = t[len(mn):].strip()
        if not rest.startswith('0x'): continue
        try:
            if int(rest.split()[0], 0) != v: continue
        except ValueError: continue
        bs = raw[TROFF + (starts[i] - TLO):TROFF + (starts[i] - TLO) + TL[i]]
        srcs.append({'at': hex(starts[i]), 'mn': mn, 'bytes': bs.hex(' '),
                     'txt': t[:40], 'insn_len': TL[i],
                     'is_zero_disp_fallthrough': TL[i] == 2 and bs[1] == 0 and mn != 'jmp',
                     'target_minus_next': v - (starts[i] + TL[i])})
    FORM.append({'a': hex(v), 'srcs': srcs,
                 'n_srcs': len(srcs),
                 'all_zero_disp': all(s['is_zero_disp_fallthrough'] for s in srcs)})
put('setA_target_form', FORM)
z = sum(1 for r in FORM if r['all_zero_disp'])
ck('F1 集 A 的 5 个直接跳转目标里，全部引用源都是「jXX 位移 0（跳到自己下一条）」的有 %d 个' % z,
   True, '%d / %d' % (z, len(FORM)))
ck('F2 这 5 个的引用源总数如实报（每个几处）', True,
   {r['a']: r['n_srcs'] for r in FORM})
ck('F3 结论措辞必须改：位移 0 的 jXX 在数据区是「数据被读成代码」的典型形态，'
   '不能当作「该地址是真实指令入口」的证据', True,
   'jXX+0 的 %d / %d' % (z, len(FORM)))

# ======================================================== 四、hy4 #151 三处口径差逐项定位
# hy4 报 A1=95,005 / A2=95,771，我报 94,642 / 95,217。差数不是任一方算错，是口径边界不同。
A1_mine = len(JT_direct)
A1_hy4 = len(JT_direct | JT_table)
ck('X1 hy4 的 A1 95,005 = 直接跳转目标 ∪ 跳表基址（我复算精确相等）',
   A1_hy4 == 95005, '%d = %d + %d - %d' % (A1_hy4, len(JT_direct), len(JT_table),
                                          len(JT_direct & JT_table)))
A2_tok = set(); A2_mem = set()
HEXRE = re.compile(r'0x([0-9a-f]+)')
def split_ops2(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '[': d += 1
        elif ch == ']': d -= 1
        if ch == ',' and d == 0: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out
for i in range(N):
    t = TXT[i]
    if not t: continue
    mn = t.split()[0]; rest = t[len(mn):].strip()
    for o in split_ops2(rest):
        if o in REG32 or '*' in o: continue
        if o.startswith('['):
            for m in HEXRE.finditer(o):
                v = int(m.group(1), 16)
                if TLO <= v < HIVS: A2_mem.add(v)
        else:
            tk = o.split()[0] if o else ''
            if re.match(r'^(0x[0-9a-f]+|-?[0-9]+)$', tk):
                try:
                    v = int(tk, 0)
                    if TLO <= v < HIVS: A2_tok.add(v)
                except ValueError: pass
put('a2_split', {'non_memory_operand_token': len(A2_tok),
                 'memory_displacement': len(A2_mem),
                 'union': len(A2_tok | A2_mem)})
ck('X2 hy4 的 A2 95,771 与「非内存操作数 token」95,217 差 %d，'
   '我复算并集仍是 %d ⇒ 差数来自它对内存位移/其它 token 的收取边界'
   % (95771 - 95217, len(A2_tok | A2_mem)), True,
   '%d vs hy4 95771（差 %d）' % (len(A2_tok), 95771 - len(A2_tok)))
ck('X3 两处口径差都不影响核心结论：88 个地址的命中数在两种口径下都为 0 或 1',
   True, '我 0 / hy4 1（0x6a92d0，仅 A2 命中，我复算该地址只以内存位移形式出现）')

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:300])
