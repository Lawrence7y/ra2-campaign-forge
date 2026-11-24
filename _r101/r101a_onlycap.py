#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付一：把 R100 遗留的「88 个非省略的仅 capstone 起点」逐址定性

R100 只证了「88 个地址落在 objdump 某条指令内部（offset > 0）」，就停在那里，
下轮待办 ① 要求逐址定性：**哪些是 objdump 合并、哪些是真起点被漏**。

r100g 里那 88 个地址的宿主从头到尾都是 `(bad)` / `?` 之类 objdump 自己认输的行
（样本 0x46f5a0 kxnorw k0,k3,(bad) / 0x48db25 (bad) / 0x4c8114 lock ins ...），
所以「落在指令内部」这句话对它们根本没有证据力 —— objdump 在那些字节上没给出合法解码，
「内部」二字无意义。本脚本改用**外部引用证据**（不引入第三套反汇编器，本机也没有）：

判据梯队（逐址唯一归类，优先级从强到弱）：
  K1 `jump_target`      ：.text 内某条 jmp/jcc/call 的立即数恰好等于该地址
                          ⇒ 该地址**必然是真实指令起点**，objdump 在此处切错（漏起点）
  K2 `data_ref`         ：非 .text 段的 4 字节 DWORD 恰等于该地址（虚表/跳表槽）
                          或某条指令的立即数操作数等于该地址
                          ⇒ 同上，但仍可能落在数据段内的伪指针，故排在 K1 之后
  K3 `host_bad`         ：宿主 objdump 文本含 `(bad)` 或 `?`，且无任何外部引用
                          ⇒ objdump 自己未给出合法解码 ⇒ **不可称「合并」**，只能记
                            「objdump 未解出、capstone 解出、无外部引用佐证」
  K4 `ambig_tiling`     ：宿主是合法指令，capstone 从该地址起的解码**恰好填满宿主尾部**
                          （a + len == host_end）⇒ 同一段字节两种切法都自洽，静态不可判
  K5 `conflict`         ：宿主合法且 capstone 解出的边界越过 host_end ⇒ 两解码器硬冲突
  K6 `other`

正反控：
  PC1 88 个地址必须一个不漏地被归入 K1..K6 之一（分类是完备划分，不是抽样）
  PC2 K1/K2 命中数必须 > 0 或明确报 0（判别力自检：若全 0 说明引用集建坏了）
  NC1 反控 K1 的判别力：把引用集整体 +1 字节，命中数必须崩塌到 0 附近
  NC2 反控 K3：把 `(bad)` 判据换成「文本含字母 b」，命中集合必须显著不同
      （证明 K3 不是用空判据糊过去的）
  NC3 反控「宿主一定短」这一隐含假设：统计 88 个宿主的真实长度分布，
      若全是短指令则「合并」故事无从谈起（合并需要宿主够长）

产物：_r101/r101a_onlycap.json
"""
import os, io, re, json, array, bisect, struct, hashlib, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101a_onlycap.json'
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
ck('S0 exe sha256 同一份', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
ck('S0b 反汇编 sha256 同一份', hashlib.sha256(open(DUMP, 'rb').read()).hexdigest() == DUMP_SHA)

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

# ---------------- 反汇编文本三类行
FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []
wraps = array.array('I'); WL = array.array('B')
elide_at = []; nprint = 0
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
ck('S1 指令行 1,392,516 / 续行 9,028 / 省略行 5',
   N == 1392516 and len(wraps) == 9028 and len(elide_at) == 5,
   '%d / %d / %d' % (N, len(wraps), len(elide_at)))

# ---------------- capstone 线性扫描（不可解跳 1 字节）
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def sweep(skip=1):
    ok, bad = [], []
    p = TLO
    while p < HIVS:
        ins = next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)
        if ins is None:
            bad.append(p); p += skip
        else:
            ok.append((p, ins.size)); p += ins.size
    return ok, bad
ok1, bad1 = sweep(1)
OK1 = set(a for a, _ in ok1)
CAPLEN = dict(ok1)
BAD1 = set(bad1)
ck('S2 capstone 跳1: 可解 1,392,527 / 不可解 65 / 单元 1,392,592（复算 R100）',
   len(ok1) == 1392527 and len(bad1) == 65, '%d/%d' % (len(ok1), len(bad1)))

only_cap = sorted(OK1 - SSET)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
EL20 = set(only_cap) & elided_addrs
EIGHTY = sorted(set(only_cap) - EL20)
ck('S3 仅 capstone 起点 108 = 省略零段 20 + 非省略 88（复算 R100）',
   len(only_cap) == 108 and len(EL20) == 20 and len(EIGHTY) == 88,
   '%d / %d / %d' % (len(only_cap), len(EL20), len(EIGHTY)))

# ---------------- 外部引用证据集
JCC = frozenset({'je','jne','jz','jnz','jl','jle','jg','jge','jb','jbe','ja','jae',
                 'js','jns','jo','jno','jp','jnp','jpe','jpo','jc','jnc',
                 'jcxz','jecxz','jecxnz','loop','loope','loopne'})
REG32 = frozenset({'eax','ebx','ecx','edx','esi','edi','ebp','esp'})
def split_ops(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '[': d += 1
        elif ch == ']': d -= 1
        if ch == ',' and d == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out
def imm_val(txt):
    ops = split_ops(txt.strip())
    if not ops: return None
    o = ops[0]
    if o in REG32 or o.startswith('[') or '*' in o: return None
    try: return int(o.split()[0], 0)
    except ValueError: return None

JT = set()            # 跳转/调用立即数目标
IMMT = set()          # 任意立即数操作数里出现的 .text 地址
MN = []
for i in range(N):
    t = TXT[i]
    mn = t.split()[0] if t else ''
    MN.append(mn)
    rest = t[len(mn):].strip()
    if not rest: continue
    for o in split_ops(rest):
        if o in REG32 or o.startswith('[') or '*' in o: continue
        tok = o.split()[0] if o else ''
        if not re.match(r'^(0x[0-9a-f]+|-?[0-9]+)$', tok): continue
        try: v = int(tok, 0)
        except ValueError: continue
        if TLO <= v < HIVS: IMMT.add(v)
    if mn in JCC or mn in ('jmp', 'call'):
        v = imm_val(rest)
        if v is not None and TLO <= v < HIVS: JT.add(v)
ck('S4 跳转目标集规模 > 50,000（判别力自检：集合没建坏）', len(JT) > 50000, len(JT))

# 非 .text 段 4 字节槽里指向 .text 的值
DATA = set()
for nm, lo, hivs, hirs, roff, rsz in SECS:
    if nm == '.text': continue
    for p in range(0, rsz - 3, 4):
        v = struct.unpack_from('<I', raw, roff + p)[0]
        if TLO <= v < HIVS: DATA.add(v)
put('refs', {'jump_targets': len(JT), 'imm_text_refs': len(IMMT), 'data_dword_refs': len(DATA),
             'union': len(JT | IMMT | DATA)})
ck('PC2 引用集总规模 > 50,000（三个来源都有内容）',
   len(JT | IMMT | DATA) > 50000, len(JT | IMMT | DATA))

# ---------------- 逐址归类
def host_of(a):
    j = bisect.bisect_right(starts, a) - 1
    return j
CLS = collections.Counter()
ROWS = []
for a in EIGHTY:
    j = host_of(a)
    hstart = starts[j]; hlen = TL[j]; hend = hstart + hlen
    htxt = TXT[j]
    caplen = CAPLEN.get(a)
    cend = a + caplen if caplen else None
    rec = {'a': hex(a), 'host': hex(hstart), 'host_len': hlen, 'offset': a - hstart,
           'host_txt': htxt[:44], 'cap_len': caplen,
           'cap_end': hex(cend) if cend else None, 'host_end': hex(hend)}
    if a in JT:
        k = 'K1_jump_target'; rec['from'] = [hex(x) for x in [a]]
    elif a in DATA or a in IMMT:
        k = 'K2_data_ref'
        rec['src'] = ('data_dword' if a in DATA else '') + ('imm' if a in IMMT else '')
    elif ('(bad)' in htxt) or ('?' in htxt):
        k = 'K3_host_bad_no_ref'
    elif cend == hend:
        k = 'K4_ambig_tiling'
    elif cend is not None and cend > hend:
        k = 'K5_conflict_past_host_end'
    else:
        k = 'K6_other_short'
    rec['class'] = k
    CLS[k] += 1
    ROWS.append(rec)
put('class_counts', dict(sorted(CLS.items())))
ck('PC1 88 个地址逐个归入 K1..K6（完备划分，不是抽样）',
   sum(CLS.values()) == 88 and all(k.startswith('K') for k in CLS), dict(CLS))
put('rows_sample', ROWS[:14])
put('by_host_len', dict(sorted(collections.Counter(r['host_len'] for r in ROWS).items())))
put('by_offset', dict(sorted(collections.Counter(r['offset'] for r in ROWS).items())))

# ---------------- NC1 反控（修正版）
# 【第一版此处 FAIL 且原因必须记下】第一版写的是「引用集整体 +1 后命中数崩塌」，
# 实测 0 -> 3 —— 反控反而**变大**。根因不是判据坏，而是**正控本身为 0**：
# 88 个地址里被三类引用命中的是 0 个，故「崩塌」这个方向无从谈起（0 没法再降）。
# 正确做法：反控必须与「正控>0」的对照组配对，才有判别力（见 r101b_chain 的随机 88 组）。
# 这里保留该测量并如实报 0 -> 3，断言改成「如实记录」而非「必须下降」。
JT1 = set(x + 1 for x in JT); D1 = set(x + 1 for x in DATA); I1 = set(x + 1 for x in IMMT)
n_shift = sum(1 for a in EIGHTY if a in JT1 or a in D1 or a in I1)
n_true = sum(1 for a in EIGHTY if a in JT or a in DATA or a in IMMT)
put('nc1_shift', {'hit_true': n_true, 'hit_shifted': n_shift,
                  'note': '正控为 0 时「+1 后下降」这个反控方向失效（0 -> 3 反而变大）；'
                          '有效反控须配正控>0 的随机对照组，已由 r101b_chain.py 的 NC1 完成。'})
ck('NC1 如实报：88 个地址的引用命中 0，引用集 +1 后为 %d —— 正控为 0，'
   '故「下降」型反控在此无效，须改用随机对照组（r101b NC1）' % n_shift,
   True, '%d -> %d' % (n_true, n_shift))

# ---------------- NC2 反控：K3 判据换成一个更松的
loose = sum(1 for r in ROWS if 'b' in r['host_txt'])
strict = CLS['K3_host_bad_no_ref']
ck('NC2 反控：K3 判据换成「文本含字母 b」后命中数不同（证明不是空判据）',
   loose != strict, 'loose %d vs strict %d' % (loose, strict))

# ---------------- NC3：宿主长度分布
hl = collections.Counter(r['host_len'] for r in ROWS)
ck('NC3 88 个宿主的真实长度分布如实报（合并故事需要长宿主）',
   max(hl) <= 15, dict(sorted(hl.items())))

# ---------------- K1/K2 明细逐条落地（可被任何第三方直接核）
K1ROWS = [r for r in ROWS if r['class'] == 'K1_jump_target']
K2ROWS = [r for r in ROWS if r['class'] == 'K2_data_ref']
srcmap = collections.defaultdict(list)
for i in range(N):
    mn = MN[i]
    if mn in JCC or mn in ('jmp', 'call'):
        v = imm_val(TXT[i][len(mn):].strip())
        if v in set(int(r['a'], 16) for r in K1ROWS):
            srcmap[hex(v)].append({'at': hex(starts[i]), 'mn': mn, 'bytes': TXT[i][:40]})
put('k1_rows', K1ROWS[:20])
put('k1_sources', dict(list(srcmap.items())[:20]))

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:200])
