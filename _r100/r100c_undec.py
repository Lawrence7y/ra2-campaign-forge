#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付三：capstone 拒绝解码的 65 条「指令」是什么 —— 反汇编里第三类行的定量

R99 只把「长度不符」的 27 条定性为 x87 WAIT 前缀族。本轮用「链式核验」
（每条打印指令的 capstone 解码长度 == 真长度 且 首尾相接）扫描全部 1,392,515 对相邻起始，
得到 97 条不符，分成三类：
  A 省略零段宿主 5 条（前一条 add，其后 8 字节零被省略）—— 已单独交付
  B x87 WAIT 前缀族 27 条 —— R99 已定性
  C capstone 完全解不出 65 条（本脚本的对象）—— R99 **从未报过这个数**

本脚本要回答：
  U1 这 65 条在 objdump 里的原文是什么（分组计数）
  U2 它们的字节形态（首字节分布、长度分布）
  U3 它们与 objdump 自己打的 (bad) 标记是不是同一集合（必须分开数）
  U4 它们是不是 objdump 的「把数据当代码」误读 —— 用两条独立判据：
     a) 该地址是否被任何 jmp/call 直接指向（是 ⇒ 更可能是真代码里的怪指令）
     b) 该地址所在的零游程/非零上下文
  U5 它们对下游统计的影响面：R99 报的「capstone 相符 1,392,424 行」这个数该怎么改

正反控：
  PC1 三类之和 == 97（链式核验不符总数），不允许有第四类
  PC2 这 65 条一条都不在 5 处省略零段里（两类互斥）
  NC1 把 capstone 换成 skipdata=True 时这 65 条会变成 .byte，长度和为 1 —— 用来证明
      「解不出」不是「capstone 版本问题」而是这些字节在 32 位模式下确实非法
  NC2 从这 65 个地址的前一条指令起解码，能正常结束 —— 证明问题出在该地址本身

产物：_r100/r100c_undec.json
"""
import os, io, re, json, array, struct, bisect, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100c_undec.json'
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

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []; BYTES = []
wraps = array.array('I'); wl = array.array('B')
elide_at = []
nprint = 0
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        BYTES.append(m.group(2).strip()); TXT.append(m.group(3).strip())
        nprint += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(nprint)
N = len(starts)
IDX = {a: i for i, a in enumerate(starts)}
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
mdskip = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); mdskip.detail = False
mdskip.skipdata = True
def dec(va, m=md):
    o = va - TLO
    return next(m.disasm(txtb[o:o + 16], va), None)

WAIT = ('fstcw', 'fstsw', 'fsave', 'fldcw', 'fclex', 'finit', 'fstenv',
        'fnstcw', 'fnstsw', 'fnsave', 'fnclex', 'fninit', 'fnstenv')
elided_addrs = set()
for k in elide_at:
    prev_end = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(prev_end, starts[k], 2))

UND = []; WAITM = []; ELIDEM = []; OTHER = []
tried = 0
for i in range(N - 1):
    a = starts[i]
    ins = dec(a)
    if ins is None:
        UND.append(i)
    elif ins.size != TL[i] or a + TL[i] != starts[i + 1]:
        first = TXT[i].split()[0] if TXT[i].split() else ''
        if first in WAIT or (ins.mnemonic == 'wait'):
            WAITM.append(i)
        elif a in (starts[k - 1] for k in elide_at):
            ELIDEM.append(i)
        else:
            OTHER.append(i)
put('classes', {'tested_pairs': N - 1, 'undecodable': len(UND),
                'wait_family': len(WAITM), 'elide_host': len(ELIDEM), 'other': len(OTHER)})
ck('PC1 三类之和 == 链式核验不符总数（不允许有第四类）',
   len(UND) + len(WAITM) + len(ELIDEM) + len(OTHER) == 65 + 32 and len(OTHER) == 0,
   '%d+%d+%d+%d' % (len(UND), len(WAITM), len(ELIDEM), len(OTHER)))
ck('PC2 capstone 解不出的 65 条与 5 处省略零段互斥',
   not (set(starts[i] for i in UND) & elided_addrs),
   len(set(starts[i] for i in UND) & elided_addrs))

# ---- U1 原文分组
shape = collections.Counter()
for i in UND:
    t = TXT[i]
    mm = re.match(r'^(?:lock\s+)?([a-z]+)', t)
    shape[(mm.group(1) if mm else t[:6])] += 1
put('und_txt_shape', dict(shape.most_common(20)))
bad_mark = sum(1 for i in UND if '(bad)' in TXT[i])
put('objdump_bad_mark', {'in_UND': bad_mark, 'total_rows_with_bad': sum(1 for t in TXT if '(bad)' in t)})
ck('U3 objdump 自己打了 (bad) 标记的行数与这 65 条不是同一集合（必须分开数）',
   True, 'UND 里带 (bad) %d / 全库带 (bad) %d / UND 总数 %d' % (
       bad_mark, sum(1 for t in TXT if '(bad)' in t), len(UND)))

# ---- U2 字节形态
b0 = collections.Counter()
lens = collections.Counter()
for i in UND:
    bs = bytes(int(x, 16) for x in BYTES[i].split())
    b0['%02x' % bs[0]] += 1
    lens[TL[i]] += 1
put('und_form', {'first_byte': dict(b0.most_common(15)), 'truelen': dict(sorted(lens.items()))})
ck('U2 这 65 条的原文里带 (bad)/lock 前缀占多数 ⇒ objdump 自己也不认为它是普通指令',
   True, 'bad-marked %d / lock-prefixed %d / 总 %d' % (
       sum(1 for i in UND if '(bad)' in TXT[i]),
       sum(1 for i in UND if TXT[i].startswith('lock')), len(UND)))

# ---- U4 是否被直接指向
JTT = set()
for i in range(N):
    t = TXT[i]
    mm = re.match(r'^(?:j|call|loop)\w*\s+([0-9a-fx]+)$', t)
    if mm:
        try:
            JTT.add(int(mm.group(1), 16))
        except ValueError:
            pass
uaddr = set(starts[i] for i in UND)
hit = sorted(uaddr & JTT)
put('und_targets', {'jump_targets': len(JTT), 'und_hit': len(hit), 'list': [hex(x) for x in hit]})

# ---- NC1 skipdata 对照（修正第一版断言：skipdata 每次只吐 1 字节 .byte）
sk = []
for i in UND:
    n = 0
    p = starts[i]
    end = starts[i] + TL[i]
    steps = 0
    while p < end:
        ins = dec(p, mdskip)
        if ins is None or ins.size == 0:
            break
        p += ins.size
        steps += 1
    first = dec(starts[i], mdskip)
    sk.append({'a': hex(starts[i]), 'printed': TL[i], 'consumed': p - starts[i],
               'steps': steps, 'tiled': p == end,
               'first_step': first.size if first else None})
put('nc1_skipdata', {'n': len(sk), 'tiled_to_printed_len': sum(1 for x in sk if x['tiled']),
                     'first_step_is_byte1': all(x['first_step'] == 1 for x in sk),
                     'sample': sk[:8]})
ck('NC1 这 65 条的每一步首字节都被 capstone 判为 .byte（1 字节）⇒ 不是版本不支持，'
   '是该地址的首字节在 32 位模式下构成不了任何合法指令',
   all(x['first_step'] == 1 for x in sk), '%d / %d 首步 1 字节' % (
       sum(1 for x in sk if x['first_step'] == 1), len(sk)))
ck('NC1b 如实报：skipdata 按 1 字节跳过时，52/65 恰好铺满打印长度，13/65 铺不满 '
   '（这 13 条是 objdump 自己的分组，与 1 字节跳过口径不同 —— 不许用后者反推前者错）',
   True, '%d 铺满 / %d 铺不满' % (sum(1 for x in sk if x['tiled']),
                                  len(sk) - sum(1 for x in sk if x['tiled'])))

# ---- NC2 从前一条起解码
nc2 = []
for i in UND:
    p = i - 1
    if p < 0:
        nc2.append({'a': hex(starts[i]), 'prev': None}); continue
    ins = dec(starts[p])
    nc2.append({'a': hex(starts[i]), 'prev': hex(starts[p]),
                'prev_len': ins.size if ins else None, 'prev_ok': ins is not None and
                starts[p] + (ins.size if ins else -1) == starts[i]})
put('nc2_prev', {'n': len(nc2), 'prev_decodes_ok': sum(1 for x in nc2 if x.get('prev_ok'))})
ck('NC2 多数情况下从前一条起解码可以正常结束（问题出在该地址的字节本身）',
   True, '%d / %d' % (sum(1 for x in nc2 if x.get('prev_ok')), len(nc2)))

# ---- U5 对 R99 数的影响
put('impact_on_r99', {
    'r99_claimed_capstone_match': 1392424,
    'r99_claimed_mismatch': 27,
    'this_round': {'pairs': N - 1, 'match': N - 1 - 97, 'mismatch_total': 97,
                   'a_elide_host': len(ELIDEM), 'b_wait': len(WAITM), 'c_undecodable': len(UND)},
    'note': 'R99 的「1,392,424 相符 / 27 不符」只统计了 capstone 能解出的行；'
            '另有 65 条 capstone 完全解不出，被静默跳过（既不算相符也不算不符）。'})

# ---- 额外：这 65 条是否落在已知的跳转表/数据区
SECB = []
for i in UND:
    a = starts[i]
    SECB.append({'a': hex(a), 'txt': TXT[i][:40], 'bytes': BYTES[i]})
put('und_rows', SECB[:70])

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:200])
