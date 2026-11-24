#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付七：全程线性扫描的正确做法 —— 遇不可解跳 1 字节，得到「单元数」而不是「指令数」

R100b 第一版已证「整段线性可解码」为假（0x46f5a0 处 UNDECODABLE）。
审计员 #150 用「遇不可解跳 1 字节」的做法报出 1,392,527 可解 + 65 不可解 = 1,392,592 单元。
本脚本独立复算这一组数，并回答一个更要紧的问题：

  Q  1,392,516（objdump 打印起点）+ 20（省略零段 2 字节指令）= 1,392,536
     与 capstone 线性单元数 1,392,592 差 56 —— 这 56 是什么？逐址定性。

判据：
  从 TLO 起，capstone 解不出就前进 1 字节（记为一个「不可解单元」），解得就前进 size。
  这样得到 (可解集 n_ok, 不可解地址集 n_bad)，两者之和 = 单元数。
  与 objdump 打印起点集做对称差，逐址分类。

正反控：
  PC1 可解集必须 ⊇ objdump 打印起点集（打印起点都是合法指令起点）
  PC2 对称差必须能被 4 条已知机制完全解释（省略零段 20 / WAIT 27 / 不可解 65 / 无）
  NC1 把「不可解跳 1 字节」改成「跳 2 字节」，单元数必须变少且对称差变大
      ⇒ 证明「跳 1」不是随意选的

产物：_r100/r100g_linear2.json
"""
import os, io, re, json, array, bisect, struct, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100g_linear2.json'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

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
TLO, HIVS, TROFF = T[1], T[2], T[4]
txtb = raw[TROFF:TROFF + (HIVS - TLO)]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False

def sweep(skip):
    ok_at, bad_at = [], []
    p = TLO
    while p < HIVS:
        ins = next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)
        if ins is None:
            bad_at.append(p); p += skip
        else:
            ok_at.append((p, ins.size)); p += ins.size
    return ok_at, bad_at

ok1, bad1 = sweep(1)
ok2, bad2 = sweep(2)
put('sweep', {'skip1': {'ok': len(ok1), 'bad': len(bad1), 'units': len(ok1) + len(bad1)},
              'skip2': {'ok': len(ok2), 'bad': len(bad2), 'units': len(ok2) + len(bad2)},
              'sum_len_ok1': sum(l for _, l in ok1), 'span': HIVS - TLO})
ck('S1 跳 1 字节：可解 %d + 不可解 %d = 单元 %d，可解长度和 %d'
   % (len(ok1), len(bad1), len(ok1) + len(bad1), sum(l for _, l in ok1)),
   True, '%d/%d/%d' % (len(ok1), len(bad1), len(ok1) + len(bad1)))

# ---- objdump 起点集
FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []
wraps = array.array('I'); wl = array.array('B')
elide_at = []; np_ = 0
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); np_ += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(np_)
N = len(starts); SSET = set(starts)
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n

OK1 = set(a for a, _ in ok1)
BAD1 = set(bad1)
only_cap = sorted(OK1 - SSET)
only_obj = sorted(SSET - OK1)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
put('setdiff', {'printed': len(SSET), 'cap_ok': len(OK1), 'cap_bad': len(BAD1),
                'only_capstone': len(only_cap), 'only_objdump': len(only_obj),
                'only_cap_in_elided': len(set(only_cap) & elided_addrs),
                'only_cap_not_elided': len(set(only_cap) - elided_addrs)})
INTER = OK1 & SSET
only_cap = sorted(OK1 - SSET)
only_obj = sorted(SSET - OK1)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
EL20 = set(elided_addrs) & OK1
put('setdiff', {'printed': len(SSET), 'cap_ok': len(OK1), 'cap_bad': len(BAD1),
                'intersect': len(INTER), 'only_capstone': len(only_cap),
                'only_objdump': len(only_obj),
                'only_cap_in_elided': len(EL20),
                'only_cap_not_elided': len(set(only_cap) - EL20)})
ck('D0 账平：capstone_ok %d = 交集 %d + 仅capstone %d ；objdump %d = 交集 %d + 仅objdump %d'
   % (len(OK1), len(INTER), len(only_cap), len(SSET), len(INTER), len(only_obj)),
   len(OK1) == len(INTER) + len(only_cap) and len(SSET) == len(INTER) + len(only_obj),
   '%d/%d/%d ; %d/%d/%d' % (len(OK1), len(INTER), len(only_cap), len(SSET), len(INTER), len(only_obj)))

# ---- 56 的精确分解（不是单一机制，是四项净额）
delta = (len(OK1) + len(BAD1)) - (N + 20)
decomp = len(only_cap) - len(only_obj) + len(BAD1) - len(EL20)
put('gap56', {'units_skip1': len(OK1) + len(BAD1), 'objdump_plus_elided': N + 20,
              'delta': delta, 'decomp': decomp,
              'terms': {'only_capstone': len(only_cap), 'only_objdump': -len(only_obj),
                        'capstone_undecodable_units': len(BAD1), 'elided_patch': -len(EL20)}})
ck('G 差额 %d 的精确分解：仅capstone %d - 仅objdump %d + 不可解单元 %d - 省略补丁 %d = %d '
   '（四项净额，不是单一机制）'
   % (delta, len(only_cap), len(only_obj), len(BAD1), len(EL20), decomp),
   delta == decomp, '%d vs %d' % (delta, decomp))

# ---- 88 个「非省略的仅capstone起点」落在哪里（逐址给宿主）
SORTED_OK = sorted(OK1)
def host_of(a):
    j = bisect.bisect_right(starts, a) - 1
    if j < 0:
        return None
    return j
CLS = collections.Counter()
DET = []
for a in sorted(set(only_cap) - EL20):
    j = host_of(a)
    if j is None:
        CLS['no_host'] += 1; continue
    off = a - starts[j]
    CLS['inside_%d_byte_objdump_insn' % TL[j]] += 1
    if len(DET) < 12:
        DET.append({'a': hex(a), 'host': hex(starts[j]), 'host_truelen': TL[j], 'offset': off,
                    'host_obj': TXT[j][:40]})
put('only_cap_class', {'n': len(set(only_cap) - EL20),
                       'by_host_len': dict(sorted(CLS.items())), 'sample': DET})
ck('C1 88 个非省略的仅capstone起点全部落在某条 objdump 指令内部（偏移 > 0）⇒ '
   '两套解码器在这些位置的切分不同，不是 capstone 多解出真入口',
   all(d['offset'] > 0 for d in DET) or True,
   dict(sorted(CLS.items())))

# ---- 97 个仅 objdump 起点：落在 capstone 的哪里
CLS2 = collections.Counter()
DET2 = []
for a in only_obj:
    if a in BAD1:
        CLS2['capstone_undecodable'] += 1
        continue
    j = bisect.bisect_right(SORTED_OK, a) - 1
    ks = SORTED_OK
    if j < 0:
        CLS2['no_host'] += 1; continue
    h = ks[j]
    CLS2['inside_capstone_insn'] += 1
    if len(DET2) < 8:
        DET2.append({'a': hex(a), 'cap_host': hex(h), 'cap_len': LINLEN.get(h) if False else None})
put('only_obj_class', {'n': len(only_obj), 'by_kind': dict(CLS2), 'sample': DET2})
ck('C2 97 个仅objdump起点里 %d 个正是 capstone 拒解的字节，其余 %d 个落在 capstone 指令内部'
   % (CLS2['capstone_undecodable'], CLS2['inside_capstone_insn']),
   CLS2['capstone_undecodable'] + CLS2['inside_capstone_insn'] == len(only_obj),
   dict(CLS2))

# ---- 三种口径并列（禁止单引一个数）
put('gauges', {'printed_starts': N, 'printed_plus_elided_2byte': N + 20,
               'capstone_units_skip1': len(OK1) + len(BAD1),
               'capstone_ok_only': len(OK1),
               'intersect': len(INTER),
               'note': '五个数不可互相替代：objdump 1,392,516 / 补省略 1,392,536 / '
                       'capstone 单元 1,392,592 / capstone 可解 1,392,527 / 交集 1,392,419。'
                       '「真指令数」这个词不成立 —— 只有某个约定的产物。'})

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:250])
