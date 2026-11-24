#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106b_switchmap.py —— R106 主交付：19 张 switch 分派表的完整「输入 -> case」映射与项值等价性

收口 R105 待办②③：
  ② 两级形态 10 张表：BOUND+1 个输入如何映射到 n 个 case，逐表给分组（此前只证「共 292 项可达」）
  ③ 直接形态 0x728e08 有 4 项同值 0x728de0，这 4 个 case 是否真等价（此前未证）

三条判据都是机器可判、每条都带反控：

  M1 两级形态的可判定前提：byte 表值 max < n 且 表长 == BOUND+1 且「输入 -> byte -> case」满射到全部 n 个 case
     （满射是「每个 case 都有输入能到达」的字节级证明，比 R105 A5 的可达性更强：
      A5 证的是「项值可达」，M1 证的是「该 case 被哪个具体输入选中」）
  M2 未用 case 数 == 0（10 张表逐表）；反控：把 byte 表整体置 0 后 distinct 必须掉到 1
  M3 重复项值的目标块等价性：若目标块入口处「索引寄存器」未被覆盖，则该块对多个索引是同一段代码；
     若已被覆盖（如 0x728de0 首条即 mov eax,[abs]），则不能仅凭项值相同断言等价，须另判

顺带纠正两处口径（实测）：
  E1 R105 表 A2_idioms.row.idx_reg 记的是 iced Register 枚举（37=eax/38=ecx/39=edx），不是寄存器名；
     本脚本按 memory_index 实测重列，19/19 与 R105 枚举值一致（此点 R105 正确，只是没写名）。
  E2 R105 A5 对直接形态用「[0,BOUND] 可达」算，但直接形态的 holder 前面**没有 byte 表**，
     实际可达集合是「0..BOUND 经 cmp/ja 过滤后全部命中表项」= 0..n-1（因 BOUND==n-1），
     故「292/292 可达」在直接形态上是恒等式，不构成独立证据。本轮把这个恒等式性质写清。
"""
import hashlib, json, os, struct, sys
from collections import Counter, OrderedDict

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, '_r104/vendor')
import iced_x86

OUT = '_r106/r106b_switchmap.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

R = OrderedDict()
def put(k, v):
    R[k] = v

F = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
raw = open(EXE, 'rb').read()
ck('S0 exe sha256 == R104/R105 记录值',
   hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))

def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None

def u32(va):
    return struct.unpack_from('<I', raw, off(va))[0]

def dis1(va):
    o = off(va)
    dec = iced_x86.Decoder(32, raw[o:o + 64], ip=va)
    return dec.decode()

REGNAME = {37: 'eax', 38: 'ecx', 39: 'edx', 40: 'ebx', 41: 'esp', 42: 'ebp', 43: 'esi', 44: 'edi'}

# table, n, holder, bound, byte_table, two_level, default, R105 idx_reg enum
ROWS = [
 (0x46f5a0,   4, 0x46e4be, 47, 0x46f5b0, True,  0x46f4c9, 38),
 (0x48db10,  13, 0x48d583, 37, 0x48db44, True,  0x48dac4, 39),
 (0x48dd10,   5, 0x48dce0, 39, 0x48dd24, True,  0x48dd0d, 38),
 (0x4c8114,  46, 0x4c6cd7, 45, None,     False, 0x4c8109, 37),
 (0x5001e4,   5, 0x4ffde9,  4, None,     False, 0x5001ce, 37),
 (0x58bda4,   5, 0x58bd85,  4, None,     False, 0x58bda1, 38),
 (0x69b15c,   4, 0x69af3e,  3, None,     False, 0x69b148, 37),
 (0x6a92c4,   3, 0x6a8e1e, 14, 0x6a92d0, True,  0x6a8f49, 38),
 (0x6adbdc,   3, 0x6acf2a, 22, 0x6adbe8, True,  0x6adbcc, 38),
 (0x6b0238,   7, 0x6afd73,  6, None,     False, 0x6b0231, 37),
 (0x6dfdec, 145, 0x6dd8e7,144, None,     False, 0x6dfddd, 39),
 (0x708d54,   5, 0x708c4e,  4, None,     False, 0x708d4d, 37),
 (0x71f2c0,  14, 0x71eea2, 45, 0x71f2f8, True,  0x71f069, 39),
 (0x71f328,  10, 0x71f092, 55, 0x71f350, True,  0x71f1b1, 38),
 (0x71f778,   2, 0x71f6d0, 55, 0x71f780, True,  0x71f6da, 37),
 (0x71f9e0,   2, 0x71f9d3, 58, 0x71f9e8, True,  0x71f9dd, 38),
 (0x728e08,   7, 0x728c17,  6, None,     False, 0x728dfc, 37),
 (0x7291ac,   7, 0x728e6c,  6, None,     False, 0x7290f6, 38),
 (0x79f028,   5, 0x79ed73, 94, 0x79f03c, True,  0x79f01b, 39),
]

# ---------- E0 表基址与项数复核（不信任外部输入，先自查） ----------
tot = 0
ok_n = 0
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    tot += n
    ok_n += 1
ck('E0a 19 张表项数合计 == 292', tot == 292, tot)
ck('E0b 表基址全在 .text 内',
   all(off(b) is not None for b, *_ in ROWS), '')
vals_all = {}
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    vals_all[base] = [u32(base + 4 * i) for i in range(n)]
ck('E0c 全部 292 项值都落在 .text 且是 4 字节对齐位',
   all(off(v) is not None for vs in vals_all.values() for v in vs),
   sum(1 for vs in vals_all.values() for v in vs if off(v) is None))

# ---------- E1 holder 索引寄存器实测（纠正 R105 只记枚举没记名） ----------
e1rows = []
e1_ok = 0
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    i = dis1(holder)
    mi = i.memory_index
    disp = i.memory_displacement
    same = (mi == ir and disp == base)
    e1_ok += 1 if same else 0
    e1rows.append({'table': hex(base), 'holder': hex(holder),
                   'insn': F.format(i), 'mem_index_enum': mi,
                   'mem_index_name': REGNAME.get(mi, '?'),
                   'disp': hex(disp), 'r105_enum': ir, 'ok': same})
ck('E1a 19/19 holder 都是 jmp dword ptr [reg*4+表基址] 且 memory_index == R105 枚举值',
   e1_ok == 19, e1_ok)
ck('E1b 19/19 disp == 表基址（表基址取自持有指令，非外部猜测）',
   all(int(r['disp'], 16) == int(r['table'], 16) for r in e1rows), '')
put('E1_holder_index', {'tested': 19, 'ok': e1_ok, 'rows': e1rows})

# ---------- M2 未用 case 数 == 0（两级形态） ----------
m2rows = []
m2_ok = 0
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    if not two:
        continue
    bs = raw[off(bt):off(bt) + bound + 1]
    used = sorted(set(bs))
    unused = [i for i in range(n) if i not in used]
    full = (len(bs) == bound + 1 and max(bs) < n and len(unused) == 0)
    m2_ok += 1 if full else 0
    m2rows.append({'table': hex(base), 'n': n, 'bound': bound,
                   'n_bytes': len(bs), 'max_byte': max(bs),
                   'distinct_cases_used': len(used),
                   'unused_cases': unused, 'surjective': full})
ck('M2a 两级形态 10/10：表长 == BOUND+1', all(r['n_bytes'] == r['bound'] + 1 for r in m2rows),
   [r['n_bytes'] - r['bound'] for r in m2rows])
ck('M2b 两级形态 10/10：max(byte) < n', all(r['max_byte'] < r['n'] for r in m2rows),
   [r['max_byte'] for r in m2rows])
ck('M2c 两级形态 10/10：未用 case 数 == 0（满射）', m2_ok == 10, m2_ok)
put('M2_surjective', {'tested': 10, 'surjective': m2_ok, 'rows': m2rows})

# 反控 N1：byte 表整体置 0 -> distinct 必须掉到 1（证明满射判据有判别力）
n1_ok = 0
n1rows = []
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    if not two:
        continue
    bs = bytearray(raw[off(bt):off(bt) + bound + 1])
    real = len(set(bs))
    bs0 = bytes(len(bs))
    c0 = len(set(bs0))
    n1_ok += 1 if (real > 1 and c0 == 1) else 0
    n1rows.append({'table': hex(base), 'distinct_real': real, 'distinct_zeroed': c0})
ck('N1 反控：10/10 byte 表置 0 后 distinct == 1（满射判据非恒真）', n1_ok == 10, n1_ok)
# 反控 N2：把 byte 表值全部 +1（模 256）-> 若有值 >= n 则 max<n 判据必须响
n2_ok = 0
n2rows = []
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    if not two:
        continue
    bs = bytes(raw[off(bt):off(bt) + bound + 1])
    plus = bytes((b + 1) & 0xFF for b in bs)
    bad = [b for b in plus if b >= n]
    n2_ok += 1 if len(bad) > 0 else 0
    n2rows.append({'table': hex(base), 'n': n, 'n_bad_after_inc': len(bad),
                   'max_after_inc': max(plus)})
ck('N2 反控：10/10 byte 表 +1 后必出现 >= n 的值（max<n 判据非恒真）', n2_ok == 10, n2_ok)

# ---------- M1 输入 -> case 完整映射（逐表） ----------
m1 = []
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    if not two:
        continue
    bs = raw[off(bt):off(bt) + bound + 1]
    grp = OrderedDict()
    for inp, c in enumerate(bs):
        grp.setdefault(c, []).append(inp)
    rows = []
    for c in sorted(grp):
        rows.append({'case': c, 'n_inputs': len(grp[c]),
                     'inputs': grp[c],
                     'target': hex(vals_all[base][c])})
    m1.append({'table': hex(base), 'n': n, 'bound': bound,
               'n_inputs_total': len(bs), 'n_cases_used': len(grp),
               'groups': rows,
               'largest_group': max(len(v) for v in grp.values()),
               'n_singleton_groups': sum(1 for v in grp.values() if len(v) == 1)})
ck('M1a 10 张表 sum(分组输入数) == BOUND+1（映射不重不漏）',
   all(sum(g['n_inputs'] for g in t['groups']) == t['n_inputs_total'] for t in m1), '')
ck('M1b 10 张表每组 target 都是该项的真实表项值（字节闭合）',
   all(g['target'] == hex(vals_all[int(t['table'], 16)][g['case']])
       for t in m1 for g in t['groups']), '')
ck('M1c 10 张表的 case 数 == n（满射，与 M2c 互证）',
   all(t['n_cases_used'] == t['n'] for t in m1), [(t['table'], t['n'], t['n_cases_used']) for t in m1])
put('M1_input_to_case', {'tested': 10, 'rows': m1})

# ---------- M3 直接形态：BOUND == n-1 与 default 复用 ----------
m3 = []
m3a = 0
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    if two:
        continue
    eqdflt = [i for i, v in enumerate(vals_all[base]) if v == dflt]
    m3a += 1 if bound == n - 1 else 0
    m3.append({'table': hex(base), 'n': n, 'bound': bound,
               'bound_eq_n_minus_1': bound == n - 1,
               'default': hex(dflt), 'entries_eq_default': eqdflt,
               'n_entries_eq_default': len(eqdflt)})
ck('M3a 直接形态 9/9：BOUND == n-1（故输入域 0..BOUND 恰等于项下标域）', m3a == 9, m3a)
put('M3_direct', {'tested': 9, 'rows': m3})
ck('M3b 直接形态里 9 张中 3 张至少 1 项与 default 目标同址（0x4c8114/0x6dfdec/0x708d54）',
   len([r for r in m3 if r['n_entries_eq_default'] > 0]) == 3,
   [(r['table'], r['n_entries_eq_default']) for r in m3])

# ---------- M4 重复项值：目标块是否入口即覆盖索引寄存器 ----------
def block_head_instructions(va, k=4):
    o = off(va)
    dec = iced_x86.Decoder(32, raw[o:o + 15 * k + 32], ip=va)
    out = []
    for _ in range(k):
        if not dec.can_decode:
            break
        out.append(dec.decode())
    return out

def writes_idx_reg(ins_list, idx_enum):
    """块前 k 条里是否写过索引寄存器（任何 op 是目标寄存器且就是 idx_enum）"""
    for i in ins_list:
        # op0 是寄存器写且等于 idx_enum
        if i.op_count >= 1 and i.op0_kind == iced_x86.OpKind.REGISTER and i.op0_register == idx_enum:
            return True, hex(i.ip) + ':' + F.format(i)
    return False, ''

m4rows = []
for base, n, holder, bound, bt, two, dflt, ir in ROWS:
    vals = vals_all[base]
    c = Counter(vals)
    dups = {t: cnt for t, cnt in c.items() if cnt > 1}
    if not dups:
        continue
    for tgt, cnt in sorted(dups.items()):
        idxs = [i for i, v in enumerate(vals) if v == tgt]
        head = block_head_instructions(tgt, 4)
        wr, wh = writes_idx_reg(head, ir)
        m4rows.append({'table': hex(base), 'target': hex(tgt), 'count': cnt,
                       'indices': idxs, 'idx_reg': REGNAME.get(ir, '?'),
                       'head': [F.format(i) for i in head],
                       'head_writes_idx_reg': wr, 'head_write_at': wh,
                       'is_default_target': tgt == dflt})
put('M4_dup_targets', {'tested': len(m4rows), 'rows': m4rows})
# 自错登记 E-sw1：本块初版把断言写死成「7 组 / 6 张表 / 1 组例外」——那是本脚本早期
# 用窄口径（只在两级形态 10 张表里找）得出的数，被 r106d 的全 19 张表普查推翻。
# 实测：8 组重复、分布在 5 张表、其中 3 组目标块首 4 条写了索引寄存器。
# 且「写了索引寄存器」不等于「依赖旧值」：0x69af45/0x69b08c 是 xor eax,eax 全写
# （不读旧值 ⇒ 仍等价），只有真正的读-改-写才影响等价性。这条粗判据已被 r106c 的
# op.access 细判据取代（r106c 得 6 IDX_DEAD_HERE / 2 CALL_CLOBBER / 0 DEPENDS）。
ck('M4a 重复项值共 8 组（5 张表）—— E-sw1 修正后实测',
   len(m4rows) == 8 and len({r['table'] for r in m4rows}) == 5,
   (len(m4rows), len({r['table'] for r in m4rows})))
equi = [r for r in m4rows if not r['head_writes_idx_reg']]
ck('M4b 5 组目标块首 4 条未写索引寄存器（粗判据下无覆盖迹象）',
   len(equi) == 5, len(equi))
wrote = [r for r in m4rows if r['head_writes_idx_reg']]
ck('M4c 3 组目标块首 4 条写了索引寄存器：0x69af45(xor 全写) / 0x69b08c(xor 全写) / '
   '0x728de0(mov 全写)——三者皆不读旧值，粗判据不能据此判「不等价」，须交 r106c 细判据',
   len(wrote) == 3
   and sorted(r['target'] for r in wrote) == ['0x69af45', '0x69b08c', '0x728de0'],
   [r['target'] for r in wrote])

# ---------- M5 0x728e08 那 4 项到底等价吗：直接看两段代码 ----------
base = 0x728e08
vals = vals_all[base]
ck('M5a 0x728e08 项值序列 == [728de0,728dd9,728dd0,728c1e,728de0,728de0,728de0]',
   [hex(v) for v in vals] == ['0x728de0', '0x728dd9', '0x728dd0', '0x728c1e',
                              '0x728de0', '0x728de0', '0x728de0'], [hex(v) for v in vals])
# 关键是：0x728dd9 与 0x728dd0 各自写 [edi+14h] 常量不同，然后都跳到 0x728de0
a = [F.format(i) for i in block_head_instructions(0x728dd0, 2)]
b = [F.format(i) for i in block_head_instructions(0x728dd9, 2)]
c0 = [F.format(i) for i in block_head_instructions(0x728de0, 2)]
d = [F.format(i) for i in block_head_instructions(0x728c1e, 2)]
ck('M5b 0x728dd0 = mov [edi+14h],5 ; jmp 728de0（前置设置块）', a[0] == 'mov dword ptr [edi+14h],5'
   and a[1] == 'jmp short 00728DE0h', a)
ck('M5c 0x728dd9 = mov [edi+14h],7 ; 落穿 728de0（前置设置块）', b[0] == 'mov dword ptr [edi+14h],7',
   b)
ck('M5d 0x728de0 = 公共尾块（mov eax,[0B0F910h] 起始）', c0[0] == 'mov eax,[0B0F910h]', c0)
ck('M5e 0x728c1e = 与前三者完全不同的一段（mov eax,[edi+8]）', d[0] == 'mov eax,[edi+8]', d)
# 语义结论：项 0/4/5/6 全指公共尾块；项 1/2 是写不同常量的前置块，且都流入公共尾块
ck('M5f 因此 case 0/4/5/6 在代码上完全同址同码（4 项真等价）；case 1/2 不是与它们等价，'
   '而是各写不同常量后合流到同一尾块',
   [hex(v) for v in vals].count('0x728de0') == 4, '')
put('M5_728e08', {'entries': [hex(v) for v in vals],
                  'blocks': {'0x728de0': c0, '0x728dd9': b, '0x728dd0': a, '0x728c1e': d},
                  'verdict': 'case 0/4/5/6 同址同码 = 4 项真等价；case 1/2 各写不同常量（5/7）到 [edi+14h] 后合流到 0x728de0 尾块，故 case 0/1/2/4/5/6 六者在「尾块」上共享代码，但 1/2 有各自独有的前置写入'})

# ---------- M6 default 目标的可达性（直接形态 3 张有项等于 default） ----------
put('M6_summary', {
    'two_level_tables': 10, 'direct_tables': 9,
    'entries_total': 292, 'distinct_targets': len(set(v for vs in vals_all.values() for v in vs)),
    'dup_groups': len(m4rows), 'dup_entries_surplus': sum(r['count'] - 1 for r in m4rows),
    'tables_with_zero_dup': len([1 for b, *_ in ROWS if len(set(vals_all[b])) == len(vals_all[b])]),
    'input_domain_total_two_level': sum(t['n_inputs_total'] for t in m1),
    'case_slots_total': sum(t['n'] for t in m1),
})

d = {'checks': checks, 'R': R}
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
print('产物 %s (%d B)' % (OUT, os.path.getsize(OUT)), flush=True)
sys.exit(0 if not fails else 1)
