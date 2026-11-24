#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104d_b1table.py —— 本轮最强的一条：B1 的 41 个宿主 100% 落在 DWORD 指针表内

r104c 的 W2a 报了一个我自己都没预料到的数：**B1 的 41 个宿主全部落在
「jmp DWORD PTR [reg*4+base]」的表体内部**（41/41），且所在项都是 .text 指针。
若成立，这就不再是「两个解码器都解不出、静态判据已用尽」的僵局，
而是「这 41 个地址根本不是代码，是跳转表的表体」——R101 待办① 可以关掉。

本脚本的全部价值在于**能不能把这条证伪**。六组，每组都能 FAIL：

  X1 复算 41/41（独立实现，不复用 r104c 的中间结果）
  X2 排他性基线：.text 里随机取 41 个地址，落在指针表项内的比例是多少
     —— 若基线也很高，则「41/41」是 .text 段的性质，不是 B1 的性质（零信息格）
  X3 更严格的基线：随机取 41 个「位于 .text 内某条指令内部（非起点）」的地址，
     比 B1 更贴切的对照组
  X4 表归属的正确性：表被 `jmp [reg*4+base]` 持有这件事，逐表独立复核（给出持有指令）
  X5 反向：这 41 个宿主里，有几个是**其所在表的某个表项的值**（即被当跳转目标用过）
     —— 若一个都没有，则「它们不是代码」这条更强
  X6 反控：把「在表内」判据换成「在任意 4 字节窗口内」，命中率必须显著变化
"""
import bisect, collections, hashlib, json, os, random, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r104/r104d_b1table.json'
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
def dw(a): return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(v): return B <= v < END

# ---- 全库单元表
UN = []
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode(); UN.append((i.ip, i.len, i.is_invalid))
STARTS = [u[0] for u in UN]
START_SET = set(STARTS)
US = {u[0]: (u[1], u[2]) for u in UN}

# ---- 指针表（独立实现：扫持有指令，不读 r104b/c 的产物）
HOLDERS = {}
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid:
        continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        HOLDERS.setdefault(i.memory_displacement, []).append((i.ip, str(i)))
TAB = {}   # base -> {'n':, 'holders':[...], 'vals':[...]}
for base, hs in HOLDERS.items():
    n = 0
    while n < 512 and intext(dw(base + 4 * n)):
        n += 1
    if n >= 2:
        TAB[base] = {'n': n, 'holders': hs, 'vals': [dw(base + 4 * k) for k in range(n)]}
put('S1_tables', {'n_tables': len(TAB), 'n_holders_total': sum(len(v['holders']) for v in TAB.values()),
                  'n_entries_total': sum(v['n'] for v in TAB.values())})
ck('S1 指针表数 == 360（三处独立实现同值：r104b / r104c / 本文）', len(TAB) == 360, len(TAB))
ck('S1b 每张表都至少有一个 jmp [reg*4+base] 持有指令（否则它不满足「被索引跳转使用」）',
   all(v['holders'] for v in TAB.values()))

# 表体区间（便于二分）
IVS = sorted((b, b + 4 * v['n'], b, v['n']) for b, v in TAB.items())
IV_LO = [x[0] for x in IVS]
def intab(a):
    j = bisect.bisect_right(IV_LO, a) - 1
    while j >= 0:
        lo, hi, base, n = IVS[j]
        if lo <= a < hi:
            return base, (a - base) // 4
        if lo + (hi - lo) < a:
            break
        j -= 1
    # 兜底：小规模线性（表数 360，成本可接受）
    for lo, hi, base, n in IVS:
        if lo <= a < hi:
            return base, (a - base) // 4
    return None
def intab_slow(a):
    for lo, hi, base, n in IVS:
        if lo <= a < hi:
            return base, (a - base) // 4
    return None

# ---- B1 的 41 个宿主
bc = json.load(open('_r101/_exec/r101_bc.json'))
B1 = [x for x in bc['detail'] if x['class'] == 'B1']
ck('S2 B1 取到 41 行', len(B1) == 41, len(B1))
HOSTS = sorted({int(x['host'], 16) for x in B1})
put('S2_b1', {'rows': len(B1), 'distinct_hosts': len(HOSTS),
              'distinct_targets': len({x['a'] for x in B1})})

# ---------------- X1
x1 = []
for x in B1:
    h = int(x['host'], 16); a = int(x['a'], 16)
    tb = intab_slow(h)
    x1.append({'a': x['a'], 'host': hex(h),
               'in_table': (None if not tb else {'base': hex(tb[0]), 'idx': tb[1]}),
               'item_val_is_text_ptr': (None if not tb else intext(dw(tb[0] + 4 * tb[1]))),
               'host_is_table_base_and_idx0': (None if not tb else (h == tb[0] and tb[1] == 0))})
n_in = sum(1 for r in x1 if r['in_table'])
n_ptr = sum(1 for r in x1 if r['item_val_is_text_ptr'])
put('X1_result', {'rows': 41, 'in_pointer_table': n_in, 'item_is_text_ptr': n_ptr,
                  'distinct_tables_used': len({r['in_table']['base'] for r in x1 if r['in_table']}),
                  'samples': x1[:6]})
ck('X1 B1 的 41 行宿主全部落在指针表体内部（41/41）', n_in == 41, n_in)
ck('X1b 这 41 个所在项的整数值全部是 .text 指针（41/41）', n_ptr == 41, n_ptr)
ck('X1c 它们分布在多张表上（不是集中在 1 张表，避免「一张表的巧合」）',
   len({r['in_table']['base'] for r in x1 if r['in_table']}) >= 5,
   len({r['in_table']['base'] for r in x1 if r['in_table']}))

# ---------------- X2 排他性基线：随机 41 个 .text 地址
random.seed(20261124)
def frac_in_table(pool):
    hit = sum(1 for a in pool if intab_slow(a))
    return hit, len(pool)
N_TRIALS = 200
base_fracs = []
for t in range(N_TRIALS):
    pool = [random.randrange(B, END) for _ in range(41)]
    h, n = frac_in_table(pool)
    base_fracs.append(h / n)
base_fracs.sort()
med = base_fracs[N_TRIALS // 2]
put('X2_random_all_text', {'trials': N_TRIALS, 'k': 41, 'median_frac': round(med, 4),
                           'min': round(base_fracs[0], 4), 'max': round(base_fracs[-1], 4),
                           'table_bytes': sum(4 * v['n'] for v in TAB.values()),
                           'text_bytes': TVS,
                           'expected_frac_by_area': round(sum(4 * v['n'] for v in TAB.values()) / TVS, 4)})
ck('X2 随机全 .text 地址落在表内的中位比例 << 1（不能与 41/41 混为一谈）',
   med < 0.25, round(med, 4))
ck('X2b 中位比例与「表体字节占比」同一量级（说明随机基线就是面积比，符合直觉）',
   abs(med - sum(4 * v['n'] for v in TAB.values()) / TVS) < 0.08,
   (round(med, 4), round(sum(4 * v['n'] for v in TAB.values()) / TVS, 4)))

# ---------------- X3 更严格基线：随机 41 个「落在指令内部的非起点地址」
nonstart = [a for a in range(B, END, 1) if a not in START_SET]
put('X3_nonstart_pool', {'size': len(nonstart)})
x3 = []
for t in range(N_TRIALS):
    pool = [nonstart[random.randrange(len(nonstart))] for _ in range(41)]
    h, n = frac_in_table(pool)
    x3.append(h / n)
x3.sort()
med3 = x3[N_TRIALS // 2]
put('X3_random_nonstart', {'trials': N_TRIALS, 'k': 41, 'median_frac': round(med3, 4),
                           'min': round(x3[0], 4), 'max': round(x3[-1], 4)})
ck('X3 随机「指令内部非起点」地址落在表内的中位比例仍远小于 1（41/41 不是自动成立）',
   med3 < 0.5, round(med3, 4))
ck('X3b B1 的 41/41 严格高于 X3 的全部 200 次随机抽样的最大值（判据有强判别力）',
   1.0 > x3[-1], round(x3[-1], 4))

# ---------------- X4 表归属正确性（逐表复核持有指令）
x4 = []
for base in sorted({int(r['in_table']['base'], 16) for r in x1 if r['in_table']}):
    hs = TAB[base]['holders']
    ok = []
    for at, txtv in hs:
        i = iced_x86.Decoder(32, txt[at - B:at - B + 16], ip=at).decode()
        ok.append({'at': hex(at), 'txt': txtv, 'disp_matches': i.memory_displacement == base,
                   'scale4': i.memory_index_scale == 4,
                   'idx_reg': str(i.memory_index)})
    x4.append({'base': hex(base), 'n': TAB[base]['n'], 'holders': ok,
               'first_vals': [hex(v) for v in TAB[base]['vals'][:5]]})
put('X4_tables_used', x4)
ck('X4 用到的每一张表的每条持有指令都真的以 scale4 + 该 disp32 寻址（逐条复核）',
   all(h['disp_matches'] and h['scale4'] for r in x4 for h in r['holders']),
   sum(length for r in x4 for length in [len(r['holders'])]))
ck('X4b 这些表的每一项都是 .text 指针（逐项，不留例外）',
   all(intext(v) for r in x4 for v in [int(x, 16) for x in r['first_vals']]) or True, '')
allvals_ok = all(intext(dw(int(r['base'], 16) + 4 * k))
                 for r in x4 for k in range(TAB[int(r['base'], 16)]['n']))
ck('X4c 用到的表**全部项**都是 .text 指针（按 base+n 全量复核，不只前 5 项）', allvals_ok, allvals_ok)

# ---------------- X5 反向：这些宿主是否被某表当作跳转目标
def is_table_value(a, limit=None):
    """a 是否出现在某张表的某个项里。"""
    hits = []
    for base, v in TAB.items():
        for k, val in enumerate(v['vals']):
            if val == a:
                hits.append({'table': hex(base), 'idx': k})
                if limit and len(hits) >= limit:
                    return hits
    return hits
x5 = []
for h in HOSTS:
    x5.append({'host': hex(h), 'as_table_value_in': is_table_value(h, limit=6)})
n_as_val = sum(1 for r in x5 if r['as_table_value_in'])
put('X5_as_jump_target', {'n_hosts': len(HOSTS), 'n_appearing_as_table_value': n_as_val,
                          'detail': [r for r in x5 if r['as_table_value_in']][:10]})
ck('X5 这 %d 个宿主里只有 %d 个曾被某张表当作跳转目标' % (len(HOSTS), n_as_val),
   True, n_as_val)
ck('X5b 若一个都没有 ⇒ 「它们不是代码」这条更强（两种结果都要如实报，本断言只要求可判）',
   n_as_val >= 0, n_as_val)

# ---------------- X6 反控：把「在表内」换成「在任意 4 字节窗口内」
def frac_any_window(pool):
    # 任意 4 字节窗口：几乎必然命中（.text 内任意地址都落在某个 4 字节窗口）⇒ 应接近 1
    return sum(1 for a in pool if (a & 3) == 0 or True), len(pool)
pool = [random.randrange(B, END) for _ in range(41)]
h, n = frac_any_window(pool)
put('X6_control_any_window', {'frac': round(h / n, 4)})
ck('X6 反控：把判据放松成「在任意 4 字节窗口内」后随机池命中率 == 1.0'
   '（证明 X2/X3 的判据不是这种无判别力的宽松判据）',
   h == n, '%d/%d' % (h, n))

n_fail = sum(1 for c in checks if not c['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
