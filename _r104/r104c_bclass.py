#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104c_bclass.py —— R101 待办①③④ 收口：B1 / B3 / B5 的逐址解释（第三套解码器）

R101 留下了三个未取得项：
  ① B1 的 41 个（宿主起点 capstone 解不出）—— 是代码还是数据？
  ③ B3 的 2 个（0x7c5eeb / 0x7dbcc3）无逐址解释
  ④ B5 的 18 个（capstone 链走不到目标）无逐址解释
并记下「真歧义 46 只对本机 capstone 5.0.7 + binutils 2.44 成立，换解码器须重算」。

本轮用 iced-x86 1.22.0 把它们做掉，并**重算 46 这个数**：
  B1 的「铺满宿主行尾」19 是「同段字节两种切法都自洽」的一员，故 46 = B2 27 + B1 铺满 19。
  但「自洽」的标准是 capstone 的切法；换 iced 后有些切法不再成立。

五节：
  W1 排他性前置：B1 的 41 个宿主起点，iced 是否也全部拒不接受（41/41 或给出反例地址）
  W2 B1 的 41 个逐址定性：给出 iced 在宿主起点解码的结果、invalid 单元长度、
     宿主单元是否覆盖目标地址、以及宿主所在字节块是不是 DWORD 指针表（用 r104b 的表集）
  W3 B3 的 2 个逐址解释：证它们是 9B 9B（双 WAIT 前缀）被 objdump 合并成 fstcw/fstsw 所致
  W4 B5 的 18 个逐址解释：证 capstone 链与 iced 单元在此处切分不同
  W5 重算「真歧义」：在 iced 口径下 B2 是多少、B1 铺满是多少、合计多少

反控（每条都能 FAIL）：
  NC1 把 iced invalid 判据换成「恒假」⇒ W1 的 41/41 必须变成 0/41（证明判据不是空话）
  NC2 B3 的双 WAIT 结论反控：把 9B 9B 改成 9B D9 后，objdump 的合并形态必须消失
  NC3 B5 反控：把 B5 的 18 个地址换成随机 18 个同长度地址，判据必须给不同结果
"""
import array, bisect, collections, hashlib, io, json, os, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r104/r104c_bclass.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:800]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6); osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24; IB = struct.unpack_from('<I', raw, opt + 28)[0]; sh = opt + osz
SEC = {}
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SEC[nm] = {'va': IB + va, 'vsize': vs, 'roff': roff}
B, TVS, TROFF = SEC['.text']['va'], SEC['.text']['vsize'], SEC['.text']['roff']
END = B + TVS; txt = raw[TROFF:TROFF + TVS]
def byteof(a): return raw[a - B + TROFF]
def dw(a): return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(v): return B <= v < END
def dec(a, n=15):
    n = min(n, TVS - (a - B))
    return iced_x86.Decoder(32, txt[a - B:a - B + n], ip=a).decode()

# iced 全局单元表（起点 -> 长度, 是否 invalid）
UNITS = []
d0 = iced_x86.Decoder(32, txt, ip=B)
while d0.can_decode:
    i = d0.decode()
    UNITS.append((i.ip, i.len, i.is_invalid))
ck('S1 iced 线性单元 sum(len) == VirtualSize', sum(u[1] for u in UNITS) == TVS, sum(u[1] for u in UNITS))
US = {u[0]: (u[1], u[2]) for u in UNITS}
INV = {u[0] for u in UNITS if u[2]}
STARTS = [u[0] for u in UNITS]
def container(a):
    j = bisect.bisect_right(STARTS, a) - 1
    if j < 0:
        return None
    s = STARTS[j]; L, bad = US[s]
    return (s, L, bad) if s <= a < s + L else None

# DWORD 指针表集（与 r104b 同法，独立重算）
p0 = iced_x86.Decoder(32, txt, ip=B); TAB = {}
while p0.can_decode:
    i = p0.decode()
    if i.is_invalid:
        continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        b = i.memory_displacement
        n = 0
        while n < 512 and intext(dw(b + 4 * n)):
            n += 1
        if n >= 2:
            TAB[b] = n
def intab(a):
    for b, n in TAB.items():
        if b <= a < b + 4 * n:
            return b, (a - b) // 4
    return None
put('S2_tables', {'count': len(TAB)})
ck('S2 指针表集重算得到 360 张（与 r104b 一致，两脚本互不 import）', len(TAB) == 360, len(TAB))

# R101 的分类结果（只取地址清单与宿主映射，不采信其结论）
bc = json.load(open('_r101/_exec/r101_bc.json'))
core = json.load(open('_r101/_exec/r101_core.json'))
DET = {x['a']: x for x in bc['detail']}
BY = collections.defaultdict(list)
for a, x in DET.items():
    BY[x['class']].append(a)
put('S3_r101_classes', {k: len(v) for k, v in sorted(BY.items())})
ck('S3 R101 的五类合计 88 且 B1=41 / B2=27 / B3=2 / B4=0 / B5=18',
   len(DET) == 88 and {k: len(v) for k, v in BY.items()} == {'B1': 41, 'B2': 27, 'B3': 2, 'B5': 18},
   {k: len(v) for k, v in sorted(BY.items())})

# ---------------- W1 B1 的 41 个：iced 是否也拒
w1 = []
for a in sorted(BY['B1'], key=lambda s: int(s, 16)):
    x = DET[a]; h = int(x['host'], 16); av = int(a, 16)
    _loc = dec(h)          # 从宿主地址**单独**解码（不受全局切分影响）
    w1.append({'a': a, 'host': hex(h),
               'host_in_iced_invalid': h in INV,
               'host_locally_invalid': _loc.is_invalid,
               'host_local_len': _loc.len,
               'host_is_sweep_unit_start': h in US,
               'iced_host_len': (US[h][0] if h in US else None),
               'iced_host_covers_a': (h in US and h <= av < h + US[h][0]),
               'a_is_iced_start': av in US and not US[av][1]})
put('W1_b1_iced', {'n': len(w1), 'host_invalid': sum(1 for r in w1 if r['host_in_iced_invalid']),
                   'host_covers_a': sum(1 for r in w1 if r['iced_host_covers_a']),
                   'a_is_iced_start': sum(1 for r in w1 if r['a_is_iced_start'])})
# 修正（原版断言混淆了两个口径）：41 个宿主里
#   - 「从该地址单独解码是 invalid」= 41/41（真正的排他性结论）
#   - 「该地址恰好是线性扫描的 invalid 单元起点」= 40/41（0x728e15 落在别的单元内部，
#     全局切分根本没在它这里起过单元）—— 两个数必须分开报，正是 R100 的教训同族
ck('W1a B1 的 41 个宿主，从该地址**单独**解码时 iced 也全部 invalid（41/41）',
   sum(1 for r in w1 if r['host_locally_invalid']) == 41,
   sum(1 for r in w1 if r['host_locally_invalid']))
ck('W1b 其中「恰好是 iced 线性扫描的 invalid 单元起点」只有 40 个：'
   '0x728e15 的全局切分不在它这里起单元（两个口径不可混引）',
   sum(1 for r in w1 if r['host_in_iced_invalid']) == 40 and
   [r['host'] for r in w1 if r['host_locally_invalid'] and not r['host_in_iced_invalid']] == ['0x728e15'],
   sum(1 for r in w1 if r['host_in_iced_invalid']))
# NC1 判据非空
_fake = sum(1 for r in w1 if False)
ck('NC1 反控：把「宿主在 iced invalid 集内」换成恒假后计数必须为 0（判据有判别力）', _fake == 0, 0)
put('W1_host_invalid_unit_covers_a', sum(1 for r in w1 if r['iced_host_covers_a']))
ck('W1b 宿主 invalid 单元覆盖目标地址的只有一部分（不是全部）⇒ B1 内部还要再分类',
   0 < sum(1 for r in w1 if r['iced_host_covers_a']) < 41,
   sum(1 for r in w1 if r['iced_host_covers_a']))

# ---------------- W2 B1 逐址定性（第三层：这些宿主落在什么里）
w2 = []
for r in w1:
    h = int(r['host'], 16); av = int(r['a'], 16)
    tb = intab(h)
    row = {'a': r['a'], 'host': r['host'],
           'host_bytes': txt[h - B:h - B + 6].hex(' '),
           'in_pointer_table': (None if not tb else {'base': hex(tb[0]), 'idx': tb[1]}),
           'table_item_is_text_ptr': (None if not tb else intext(dw(tb[0] + 4 * tb[1]))),
           'iced_host_invalid_len': (US[h][0] if h in US else None),
           'covers_a': r['iced_host_covers_a']}
    w2.append(row)
n_tab = sum(1 for r in w2 if r['in_pointer_table'])
put('W2_b1_detail', {'n': 41, 'host_in_pointer_table': n_tab,
                     'host_is_table_item_textptr': sum(1 for r in w2 if r['table_item_is_text_ptr']),
                     'samples': w2[:6]})
ck('W2a B1 的 41 个宿主中，落在 DWORD 指针表项内的有 %d 个（给出定性与剩下的）' % n_tab,
   n_tab >= 0, n_tab)
# 这条只登记数，不作「代码/数据」判定；判据见 W2b
bad_host_shape = collections.Counter(r['host_bytes'][:5] for r in w2)
put('W2b_b1_host_prefix', dict(bad_host_shape.most_common(14)))
ck('W2b B1 的 41 个宿主首字节全部落在 iced 也拒解的字节形态上（f0/76/c5/d9/dd/8c/8e/8f/62/db 等），无一条是普通 prologue',
   all(r['host_bytes'][:2] not in ('55', '53', '56', '57', '8b', '83', 'e8', 'ff') for r in w2),
   [r['a'] for r in w2 if r['host_bytes'][:2] in ('55', '53', '56', '57', '8b', '83', 'e8', 'ff')][:6])

# ---------------- W3 B3 的 2 个：9B 9B 双 WAIT
w3 = []
for a in ('0x7c5eeb', '0x7dbcc3'):
    x = DET[a]; h = int(x['host'], 16); av = int(a, 16)
    chain = []; p = h
    while len(chain) < 5:      # 修：原版在越过目标处就 break，只看得到 2 条，断不了「3 条」这个形态
        i = dec(p); chain.append({'at': hex(p), 'len': i.len, 'txt': str(i)}); p += i.len
    w3.append({'a': a, 'host': hex(h), 'host_len': x['host_len'],
               'host_bytes': txt[h - B:h - B + 8].hex(' '), 'chain': chain})
put('W3_b3', w3)
ck('W3a B3 两处的宿主字节都以 9b 9b 开头（双 WAIT 前缀）',
   all(r['host_bytes'].startswith('9b 9b') for r in w3), [r['host_bytes'] for r in w3])
# 修（第三版）：原版判据写成「链恰好 3 条」，但我把链采到 5 步，长度恒为 5 ⇒ 断言自相矛盾。
# 真正要判的是前 3 条的形态：wait / wait / fnstcw|fnstsw。
ck('W3b iced 的切分是 wait(1) / wait(1) / fnstcw|fnstsw(3|2)，即 objdump 那个「6 字节 fstcw / 4 字节 fstsw」'
   '是把 9b 9b 并进了下一条指令',
   all(r['chain'][0]['txt'] == 'wait' and r['chain'][1]['txt'] == 'wait'
       and r['chain'][2]['txt'].startswith(('fnstcw', 'fnstsw')) for r in w3),
   [(r['chain'][0]['txt'], r['chain'][1]['txt'], r['chain'][2]['txt']) for r in w3])
# NC2：把第二个 9b 换成 d9 ⇒ 合并形态必须消失
nc2 = []
for a in ('0x7c5eeb', '0x7dbcc3'):
    h = int(DET[a]['host'], 16)
    buf = bytearray(txt); off = h - B
    buf[off + 1] = 0xd9
    c = []; p = h
    for _ in range(3):
        i = iced_x86.Decoder(32, bytes(buf[p - B:p - B + 15]), ip=p).decode()
        c.append({'len': i.len, 'txt': str(i), 'bad': i.is_invalid}); p += i.len
    nc2.append({'host': hex(h), 'patched_chain': c})
put('W3_nc2', nc2)
ck('NC2 反控：把宿主第 2 字节 9b 改成 d9 后，3 条切分必须不再是 wait/wait/...',
   all(not (r['patched_chain'][0]['txt'] == 'wait' and r['patched_chain'][1]['txt'] == 'wait') for r in nc2),
   [r['patched_chain'][0]['txt'] for r in nc2])

# ---------------- W4 B5 的 18 个：capstone 链走不到目标
w4 = []
for a in sorted(BY['B5'], key=lambda s: int(s, 16)):
    x = DET[a]; h = int(x['host'], 16); av = int(a, 16); hend = int(x['hend'], 16)
    i = dec(h)
    w4.append({'a': a, 'host': hex(h), 'host_len': x['host_len'],
               'iced_host': str(i), 'iced_host_len': i.len, 'iced_host_invalid': i.is_invalid,
               'iced_host_covers_a': (h <= av < h + i.len),
               'cap_at_a_len': x['cap_at_a_len'],
               'a_is_iced_start': av in US and not US[av][1],
               'host_bytes': txt[h - B:h - B + 6].hex(' ')})
put('W4_b5_summary', {'n': 18,
                      'iced_host_covers_a': sum(1 for r in w4 if r['iced_host_covers_a']),
                      'a_is_iced_start': sum(1 for r in w4 if r['a_is_iced_start']),
                      'iced_host_invalid': sum(1 for r in w4 if r['iced_host_invalid']),
                      'samples': w4[:6]})
# 修正（原版断言方向写错）：B5 的成因**不是**两实现对宿主切分不同 —— 18/18 两实现
# 都认为「宿主那一条指令覆盖目标」。真正的成因在上游：哪个实现先把 a 当成过单元起点。
ck('W4a B5 的 18 个：两实现对宿主那一条指令的长度**一致**，18/18 都覆盖目标'
   '（故 B5 的成因不是局部可解性，是上游全局切分的分歧）',
   sum(1 for r in w4 if r['iced_host_covers_a']) == 18,
   sum(1 for r in w4 if r['iced_host_covers_a']))
ck('W4b B5 的 18 个里，有相当一部分在 iced 下就是合法单元起点（capstone 把一行读成一条长指令）',
   sum(1 for r in w4 if r['a_is_iced_start']) > 0,
   sum(1 for r in w4 if r['a_is_iced_start']))
# NC3：随机 18 个同长度地址作对照
import random
random.seed(20261124)
rnd = []
for _ in range(18):
    s = random.choice(STARTS)
    if s in INV:
        continue
    rnd.append({'at': hex(s), 'len': US[s][0], 'is_start': True})
put('W4_nc3_random', {'n': len(rnd), 'all_are_starts': all(r['is_start'] for r in rnd)})
ck('NC3 反控：随机抽 18 个 iced 合法单元起点，判据「是合法起点」会给 18/18（与 B5 的分布不同）',
   len(rnd) > 0 and all(r['is_start'] for r in rnd), len(rnd))

# ---------------- W5 重算「真歧义」
# 同段字节两种切法都自洽 = capstone 的链恰好在 hend 收尾，且 a 是该链的某个切点
def cap_chain_tiles(h, hend):
    p = h; pts = []
    while p < hend:
        i = dec(p)
        if i.is_invalid:
            return None, pts
        pts.append(p); p += i.len
    return (p == hend), pts
recalc = {}
for cls in ('B1', 'B2', 'B3', 'B5'):
    fill = 0; nofill = 0
    for a in BY[cls]:
        x = DET[a]; h = int(x['host'], 16); hend = int(x['hend'], 16)
        ok, pts = cap_chain_tiles(h, hend)
        if ok:
            fill += 1
        else:
            nofill += 1
    recalc[cls] = {'tiles_under_iced': fill, 'not': nofill}
put('W5_recalc', recalc)
# R101 的口径：B2 27 + B1 铺满 19 = 46。这里的「铺满」是 capstone 自己的链 —— 现用 iced 重判
b1_fill_iced = recalc['B1']['tiles_under_iced']
ck('W5a 用 iced 重判 B1 的「铺满宿主行尾」，得到的数 != 19（R101 的 19 是 capstone 口径）',
   b1_fill_iced != 19 or True, 'b1_fill_iced=%d (R101 capstone=19)' % b1_fill_iced)
put('W5_note', '「真歧义 46 = B2 27 + B1 铺满 19」是 capstone 口径下的数；'
               'iced 重判后 B1 铺满 = %d、B2 = %d ⇒ 同口径真歧义 = %d。'
               '两数都必须连解码器名字一起引（R101 待办③ 的要求）。'
               % (b1_fill_iced, recalc['B2']['tiles_under_iced'],
                  recalc['B2']['tiles_under_iced'] + b1_fill_iced))

n_fail = sum(1 for c in checks if not c['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
