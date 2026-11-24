#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付二：88 个「非省略的仅 capstone 起点」的链可达性与外部引用基率对照

R101a 第一版把 88 个地址分成 K3/K4/K5/K6（30/41/10/7），但它的 NC1 反控 FAIL
（引用集整体 +1 后命中 0 → 3），根因是**正控为 0，反控无从谈起**：
88 个地址里被跳转/立即数/数据槽引用的是 **0 个**。

所以本脚本不再问「落在谁内部」（R100 已答、且对 (bad) 宿主无意义），
改问两个有判别力的问题：

  Q1 链可达性：capstone 从**宿主起点**出发，能不能沿自己的解码链走到这 88 个地址？
     - `R_resync`  ：宿主起点 capstone 就解不出（两解码器都认输），是「跳 1 字节重同步」
                     的产物 ⇒ 与 objdump 的切分无关，**不是「objdump 合并」**
     - `T_exact`   ：链恰好走到 a 且 capstone 在此的长度正好补满宿主尾部
                     ⇒ 同一段字节两种切法都自洽，静态不可判（真歧义）
     - `T_short`   ：链走到 a 但 capstone 在此结束后还没到宿主尾部
     - `T_over`    ：链走到 a 且 capstone 越过宿主尾部 ⇒ 两解码器硬冲突
     - `U_offchain`：链根本没走到 a ⇒ a 是「多处重同步」的间接产物

  Q2 外部引用基率：这 88 个地址被引用的比例，与全体 objdump 起点被引用的比例比较
     （若 88 个的引用数为 0，而全体基率给 1.39M 起点上千个引用，
      则「0/88」不是偶然，而是与「真起点」的证据形态不同）。
     再用 R100 的 65 条拒解地址作反向对照（其中 5 条是跳转目标）——
     证明本判据**确实能抓到真起点**，不是恒 0 的空判据。

正反控：
  PC1 88 个地址按 Q1 完备分类，且五类之和 == 88
  PC2 基率对照：全体起点里跳转目标命中率必须显著 > 0（引用集没建坏）
  NC1 反控（有效版）：把「88 个」换成「随机抽 88 个 objdump 起点」，命中数必须 > 0
      （与真 88 个的 0 形成对照；抽 200 次报分布）
  NC2 反控：把引用集整体 +1 字节后，随机对照组的命中数必须崩塌
  NC3 反向对照：65 条 capstone 拒解地址里被跳转引用的数（R100 报 5）必须 > 0

产物：_r101/r101b_chain.json
"""
import os, io, re, json, array, bisect, struct, hashlib, random, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101b_chain.json'
DUMP = '/tmp/r93_disasm.txt'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
DUMP_SHA = '5935356b2914d90baeaeb0d8ea5198961976118526b37d341ab72f06d4046c70'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA)
ck('S0b 反汇编 sha256', hashlib.sha256(open(DUMP, 'rb').read()).hexdigest() == DUMP_SHA)

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
TLO, HIVS, TROFF, TRSZ = T[1], T[2], T[4], T[5]
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
N = len(starts); SSET = set(starts)
TL = array.array('B', LENS)
for a, n in zip(wraps, WL):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
ck('S1 行数 1,392,516 / 续行 9,028 / 省略 5',
   N == 1392516 and len(wraps) == 9028 and len(elide_at) == 5, '%d/%d/%d' % (N, len(wraps), len(elide_at)))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dec(p):
    return next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)
ok1, bad1 = [], []
p = TLO
while p < HIVS:
    ins = dec(p)
    if ins is None:
        bad1.append(p); p += 1
    else:
        ok1.append((p, ins.size)); p += ins.size
OK1 = set(a for a, _ in ok1); CAPLEN = dict(ok1); BAD1 = set(bad1)
ck('S2 capstone 跳1 可解 1,392,527 / 不可解 65', len(ok1) == 1392527 and len(bad1) == 65,
   '%d/%d' % (len(ok1), len(bad1)))

only_cap = sorted(OK1 - SSET)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
EL20 = set(only_cap) & elided_addrs
EIGHTY = sorted(set(only_cap) - EL20)
ck('S3 仅capstone 108 = 省略20 + 非省略88', len(only_cap) == 108 and len(EIGHTY) == 88,
   '%d/%d/%d' % (len(only_cap), len(EL20), len(EIGHTY)))

# ---------------- 链可达性
def chain_from(h, limit=64):
    """从 h 起沿 capstone 解码链，返回其经过的起点列表；h 解不出返回 None"""
    if h not in OK1:
        return None
    seq, p, n = [], h, 0
    while n < limit and p < HIVS:
        if p not in CAPLEN:
            break
        seq.append(p); p += CAPLEN[p]; n += 1
    return seq

CLS = collections.Counter(); ROWS = []
def host_of(a):
    j = bisect.bisect_right(starts, a) - 1
    return j
for a in EIGHTY:
    j = host_of(a); hs = starts[j]; hl = TL[j]; he = hs + hl
    txt = TXT[j]
    cl = CAPLEN.get(a)
    ce = a + cl if cl else None
    if hs not in OK1:
        k = 'R_resync'
    else:
        ch = chain_from(hs) or []
        if a in ch:
            if ce == he: k = 'T_exact'
            elif ce is not None and ce > he: k = 'T_over'
            else: k = 'T_short'
        else:
            k = 'U_offchain'
    CLS[k] += 1
    ROWS.append({'a': hex(a), 'host': hex(hs), 'host_len': hl, 'offset': a - hs,
                 'host_txt': txt[:44], 'cap_len': cl, 'cap_end': hex(ce) if ce else None,
                 'host_end': hex(he), 'class': k,
                 'host_bad': ('(bad)' in txt) or ('?' in txt)})
put('q1_classes', dict(sorted(CLS.items())))
put('q1_rows_sample', [r for r in ROWS][:16])
ck('PC1 88 个地址 Q1 完备分类，五类之和 == 88',
   sum(CLS.values()) == 88, dict(sorted(CLS.items())))
put('q1_cross', {k: dict(collections.Counter(r['host_bad'] for r in ROWS if r['class'] == k))
                 for k in sorted(CLS)})

# ---------------- 外部引用集
JCC = frozenset({'je','jne','jz','jnz','jl','jle','jg','jge','jb','jbe','ja','jae','js','jns',
                 'jo','jno','jp','jnp','jpe','jpo','jc','jnc','jcxz','jecxz','jecxnz',
                 'loop','loope','loopne'})
REG32 = frozenset({'eax','ebx','ecx','edx','esi','edi','ebp','esp'})
def split_ops(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '[': d += 1
        elif ch == ']': d -= 1
        if ch == ',' and d == 0: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out
JT, IMMT = set(), set()
for i in range(N):
    t = TXT[i]
    if not t: continue
    mn = t.split()[0]; rest = t[len(mn):].strip()
    if not rest: continue
    for o in split_ops(rest):
        if o in REG32 or o.startswith('[') or '*' in o: continue
        tok = o.split()[0] if o else ''
        if not re.match(r'^(0x[0-9a-f]+|-?[0-9]+)$', tok): continue
        try: v = int(tok, 0)
        except ValueError: continue
        if TLO <= v < HIVS: IMMT.add(v)
    if mn in JCC or mn in ('jmp', 'call'):
        ops = split_ops(rest)
        if ops:
            o = ops[0]
            if not (o in REG32 or o.startswith('[') or '*' in o):
                try:
                    v = int(o.split()[0], 0)
                    if TLO <= v < HIVS: JT.add(v)
                except ValueError:
                    pass
DATA = set()
for nm, lo, hivs, hirs, roff, rsz in SECS:
    if nm == '.text': continue
    for q in range(0, rsz - 3, 4):
        v = struct.unpack_from('<I', raw, roff + q)[0]
        if TLO <= v < HIVS: DATA.add(v)
REF = JT | IMMT | DATA
put('refs', {'jump_targets': len(JT), 'imm_text': len(IMMT), 'data_dword': len(DATA),
             'union': len(REF)})

# ---------------- PC2 基率
base_hit = sum(1 for a in SSET if a in JT)
base_rate = base_hit / len(SSET)
hit88 = sum(1 for a in EIGHTY if a in REF)
hit88_jt = sum(1 for a in EIGHTY if a in JT)
ck('PC2 基率对照：全体 objdump 起点里被跳转引用的数必须显著 > 0（引用集没建坏）',
   base_hit > 1000, '%d 命中 / 1,392,516 = %.4f%%' % (base_hit, 100 * base_rate))
put('base_rate', {'objdump_starts_with_jt': base_hit, 'rate': base_rate,
                  'expected_in_88': base_rate * 88, 'hit88_any_ref': hit88,
                  'hit88_jt_only': hit88_jt})
ck('88 个地址的外部引用命中数（如实报，与基率对照）', True,
   '命中 %d / 88；按基率期望 %.2f' % (hit88, base_rate * 88))

# ---------------- NC1 有效反控：随机抽 88 个起点
rnd = random.Random(20261124)
ALLS = sorted(SSET)
draws = []
for _ in range(200):
    s = rnd.sample(ALLS, 88)
    draws.append(sum(1 for a in s if a in REF))
draws.sort()
ck('NC1 有效反控：随机抽 88 个 objdump 起点的引用命中数分布必须显著 > 0（与真 88 个的 %d 对照）'
   % hit88, draws[100] > 0, 'median %d / min %d / max %d' % (draws[100], draws[0], draws[-1]))
put('nc1_draws', {'median': draws[100], 'min': draws[0], 'max': draws[-1],
                  'p05': draws[10], 'p95': draws[189]})

# ---------------- NC2 反控：引用集 +1
REF1 = set(x + 1 for x in REF)
draws1 = []
for _ in range(200):
    s = rnd.sample(ALLS, 88)
    draws1.append(sum(1 for a in s if a in REF1))
draws1.sort()
ck('NC2 反控：引用集整体 +1 后随机组命中数崩塌',
   draws1[100] < draws[100], 'median %d -> %d' % (draws[100], draws1[100]))

# ---------------- NC3 反向对照：65 条拒解
und_jt = sorted(a for a in BAD1 if a in JT)
und_ref = sorted(a for a in BAD1 if a in REF)
ck('NC3 反向对照：65 条 capstone 拒解地址里被跳转引用的数必须 > 0（判据能抓真起点）',
   len(und_jt) > 0, '%d 条: %s' % (len(und_jt), [hex(x) for x in und_jt]))
put('nc3', {'und_jt': [hex(x) for x in und_jt], 'und_any_ref': len(und_ref)})

# ---------------- 三个数并列
put('summary', {
  'n_only_capstone': 108, 'n_elided': 20, 'n_extra': 88,
  'resync_artifact': CLS['R_resync'], 'tiling_exact': CLS['T_exact'],
  'tiling_short': CLS['T_short'], 'tiling_over': CLS['T_over'],
  'offchain': CLS['U_offchain'],
  'ref_hits_in_extra': hit88,
  'note': '88 个「非省略的仅capstone起点」里 external reference 命中 0；'
          '其中 %d 个是「宿主起点两种解码器都解不出、capstone 跳1字节重同步」的产物，'
          '与 objdump 的切分无关；其余 %d 个是宿主起点双方都认的指令内部的切分分歧'
          '（exact %d / short %d / over %d），静态不可判。'
          % (CLS['R_resync'], 88 - CLS['R_resync'], CLS['T_exact'], CLS['T_short'], CLS['T_over'])})

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:200])
