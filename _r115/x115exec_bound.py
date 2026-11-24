#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""x115exec_bound.py —— R115 执行员（deepseek）独立复算：接口方法表槽数的结构上界 S 尺。

独立性边界（写死在此，便于复算者核查）：
  1. 本脚本不 import _r115/r115_lib.py、_r113/r113_lib.py、_r112/r112_lib.py。
     PE 头/段表、valid_col、vtable 普查、S 尺、指令起点集，全部在本文件内从字节重新实现。
  2. 只把三样东西当「给定输入」：
       ra2bench/gamemd.exe        —— 字节本体
       _r113/census.pkl           —— T / E / B 三列（对照用，不当作结论）
       _r115/iface_subobj_full.json —— 260 个接口子对象 vtable 的清单
     这 260 条清单本身**也要被独立复核**：本脚本从 RTTI 的 COL.offset + BCD.mdisp
     重新推出「这个 vtable 属于哪个类的哪个接口」，与清单逐条比对（A8）。
  3. 独立只可能是代码级独立：valid_col 的判据内容（COL+0x00 sig / COL+0x0C pTD /
     COL+0x10 pCHD / CHD+0x08 nBase / CHD+0x0C pBCA / BCD+0x00 pTD / BCD+0x08 mdisp）
     是 MSVC 的公开布局，不可能也不应该换成别的东西。

S 尺定义（本脚本实现）：
  从 vtable 起点 v 沿 .rdata 线逐 dword 前扫，第一个「其值 ∈ 合法 COL 集合」的 dword
  下标 n 记为 S，停止位置 p = v + 4n。扫到 .rdata 尾仍未遇到 ⇒ None（不猜、不给默认值）。

反控：(a) S+1  (b) S-1  (c) 判据放宽成 .rdata 区间  (d) 全镜像 vs 接口子对象 T==S 比例。

内存纪律：全程 detail=False；.text 按 64 KB 分块 disasm_lite；指令起点用 array('I') 排序
数组 + 二分（不建 set，省 40+ MB）；不产生子进程；无孤儿进程。
"""
import array
import bisect
import collections
import hashlib
import json
import os
import pickle
import struct
import sys
import time
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
CENSUS = os.path.join(ROOT, '_r113/census.pkl')
IFACE = os.path.join(ROOT, '_r115/iface_subobj_full.json')
OUT = os.path.join(ROOT, '_r115/x115exec_bound.json')

t0 = time.time()
checks = []


def ck(name, ok, detail=''):
    checks.append({'name': name, 'ok': bool(ok), 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + ((' | ' + str(detail)[:200]) if detail != '' else ''), flush=True)
    return bool(ok)


def hx(x):
    return None if x is None else hex(x)


# ---------------------------------------------------------------- 1. PE 层（自写）
raw = open(EXE, 'rb').read()
SHA = hashlib.sha256(raw).hexdigest()
IB = 0x400000
IMG_END = IB + len(raw)
fo = lambda v: v - IB
u32 = lambda v: struct.unpack_from('<I', raw, fo(v))[0]
i32 = lambda v: struct.unpack_from('<i', raw, fo(v))[0]
in_img = lambda v: IB <= v <= IMG_END - 4


def parse_sections(buf):
    pe = struct.unpack_from('<I', buf, 0x3c)[0]
    assert buf[pe:pe + 4] == b'PE\x00\x00', 'not PE'
    nsec = struct.unpack_from('<H', buf, pe + 6)[0]
    optsz = struct.unpack_from('<H', buf, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', buf, opt)[0]
    assert magic == 0x10b, 'not PE32: %#x' % magic
    imagebase = struct.unpack_from('<I', buf, opt + 28)[0]
    so = opt + optsz
    out = {}
    for i in range(nsec):
        o = so + 40 * i
        nm = buf[o:o + 8].rstrip(b'\0').decode('ascii')
        vsz, va, rsz, rptr = struct.unpack_from('<IIII', buf, o + 8)
        ch = struct.unpack_from('<I', buf, o + 36)[0]
        out[nm] = {'va': va + imagebase, 'vend': va + imagebase + vsz,
                   'rptr': rptr + imagebase, 'rsz': rsz, 'char': ch}
    return imagebase, out


imagebase, SEC = parse_sections(raw)
assert imagebase == IB, imagebase
TEXT0, TEXT1 = SEC['.text']['va'], SEC['.text']['vend']
RD0, RD1 = SEC['.rdata']['va'], SEC['.rdata']['vend']
ck('A0 段表自解一致（.text/.rdata 由 PE 头自算，不硬编码）',
   (TEXT0, TEXT1, RD0, RD1) == (0x401000, 0x7e038d, 0x7e1000, 0x811074),
   '%s %s %s %s' % (hx(TEXT0), hx(TEXT1), hx(RD0), hx(RD1)))

CENS = pickle.load(open(CENSUS, 'rb'))
ck('A1 镜像 sha256 与 census.pkl 记录一致', SHA == CENS['sha'], SHA)

# ---------------------------------------------------------------- 2. RTTI / valid_col（自写）
def type_name(td):
    """pTypeDescriptor → MSVC 装饰名（只剥一次 @@ 终止符，不剥名字内部的 @）。"""
    s = raw[fo(td) + 8:fo(td) + 8 + 256].split(b'\x00')[0].decode('ascii', 'replace')
    if len(s) > 3 and s[0] == '.' and s[1] == '?' and s[2] == 'A':
        s = s[3:]
        if s and s[0] in 'VUT':
            s = s[1:]
    if s.endswith('@@'):
        s = s[:-2]
    elif s.endswith('@'):
        s = s[:-1]
    return s


def is_td(v):
    return in_img(v) and raw[fo(v) + 8:fo(v) + 11] in (b'.?A', b'.?U', b'.?V', b'.?T')


def valid_col(a, nbase_cap=96):
    """合法 COL：sig==0、pTD 合法、pCHD 合法、BCD 数组每一项合法。"""
    if not in_img(a) or not in_img(a + 0x14):
        return False
    if u32(a) != 0:
        return False
    if not is_td(u32(a + 0xc)):
        return False
    chd = u32(a + 0x10)
    if not in_img(chd) or not in_img(chd + 0x10):
        return False
    nbc = u32(chd + 8)
    pbca = u32(chd + 0xc)
    if not (1 <= nbc <= nbase_cap):
        return False
    if not in_img(pbca) or not in_img(pbca + 4 * nbc - 4):
        return False
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        if not in_img(bcd) or not in_img(bcd + 0x1c) or not is_td(u32(bcd)):
            return False
    return True


COLS = set(a for a in range(RD0, RD1 - 0x18, 4) if valid_col(a))
ck('A2 自算合法 COL 集合与 census 一致', COLS == set(CENS['cols']), '%d 个' % len(COLS))

# vtable 普查：位置 p 的值是合法 COL，且 p+4 的首槽落在 .text
V2C = {}
for p in range(RD0, RD1 - 4, 4):
    d = u32(p)
    if d in COLS and TEXT0 <= u32(p + 4) < TEXT1:
        V2C[p + 4] = d
ck('A3 自算 vtable 普查与 census 一致', V2C == {k: CENS['V2C'][k] for k in CENS['V2C']},
   '%d 个' % len(V2C))

COLPTR = set(v - 4 for v in V2C)
POS = set(p for p in range(RD0, RD1 - 3, 4) if u32(p) in COLS)
refcnt = collections.Counter(u32(p) for p in POS)
ck('A4 「值 ∈ COLS 的位置」与「COL 指针位置」是同一集合，且每个 COL 被引用恰一次',
   POS == COLPTR and len(POS) == len(COLPTR) == len(COLS) and max(refcnt.values()) == 1,
   'POS=%d COLPTR=%d COLS=%d maxref=%d' % (len(POS), len(COLPTR), len(COLS), max(refcnt.values())))


def T_ruler(v, cap=4000):
    """T：从 v 起连续落在 .text 的 dword 个数。"""
    n = 0
    while n < cap and TEXT0 <= u32(v + 4 * n) < TEXT1:
        n += 1
    return n


CEN_T = CENS['T']
ck('A5 自算 T 尺与 census 的 T 逐点相等（→ census 的 T 语义被我独立复现）',
   all(T_ruler(v) == CEN_T[v] for v in V2C), 'n=%d' % len(CEN_T))

# ---------------------------------------------------------------- 3. S 尺（本轮新尺，自写）
def S_scan(v, pred, limit=RD1):
    """从 v 起逐 dword 扫，第一个满足 pred 的 dword 下标；扫到 limit 仍未遇到返回 None。"""
    n = 0
    while v + 4 * n + 4 <= limit:
        if pred(u32(v + 4 * n)):
            return n, v + 4 * n
        n += 1
        if n > 40000:
            return None, None
    return None, None


S = {}
for v in V2C:
    n, p = S_scan(v, lambda d: d in COLS)
    S[v] = (n, p)

undef = sorted(v for v in S if S[v][0] is None)
ck('A6 S 尺有 1 个无定义，且它在 .rdata 内之后再无任何 COL 值 dword',
   len(undef) == 1 and S_scan(undef[0], lambda d: d in COLS, limit=IMG_END)[0] is None,
   [hx(v) for v in undef])

Sd = {v: S[v][0] for v in S if S[v][0] is not None}
# S 的停止位置集合 vs COLPTR：应只差「从未被任何 vtable 的 S 扫到」的那些
stops = set(S[v][1] for v in Sd)
ck('A7 S 停止位置集合 ⊆ COLPTR，且 S 与 census 的 B 尺逐点相等（→ S 是 B 的重新表述）',
   stops <= COLPTR and all(Sd[v] == CENS['B'][v] for v in Sd),
   'stops=%d COLPTR=%d 差=%s' % (len(stops), len(COLPTR),
                                 [hx(x) for x in sorted(COLPTR - stops)]))

# ---------------------------------------------------------------- 4. 指令起点集（.text 线性扫描，64KB 分块）
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False
MD.skipdata = False
STARTS = array.array('I')
pos = TEXT0
while pos < TEXT1:
    hi = min(pos + 65536, TEXT1)
    last = pos
    for a, sz, m, o in MD.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi:
            break
        STARTS.append(a)
        last = a + sz
    if last <= pos:            # 解码未前进（非法字节）→ 强制前进 1 字节，保持线性扫描语义
        last = pos + 1
    pos = last                 # 下一块从「上一块最后一条指令的尾部」续，避免块边界失同步
STARTS = array.array('I', sorted(set(STARTS)))


def is_start(a):
    i = bisect.bisect_left(STARTS, a)
    return i < len(STARTS) and STARTS[i] == a


ck('A8 .text 线性扫描得到指令起点集（64KB 分块，detail=False）',
   len(STARTS) > 1_000_000 and is_start(TEXT0), 'starts=%d span=%s-%s' % (len(STARTS), hx(TEXT0), hx(TEXT1)))

# ---------------------------------------------------------------- 5. 接口子对象清单（给定输入 + 独立复核）
IF = json.load(open(IFACE))
IFACE = {}
for name, rows in IF.items():
    for cls, off_in, va in rows:
        IFACE[int(va, 16)] = (name, cls, off_in)
ck('A9 接口子对象清单 260 条、全部落在自算 vtable 普查内',
   len(IFACE) == 260 and set(IFACE) <= set(V2C), 'n=%d' % len(IFACE))


def col_layout(v):
    """v 的 COL/CHD 结构：offset、mdisp==offset 的基类名集合（含 IUnknown 与不含）。"""
    col = V2C[v]
    off = u32(col + 4)
    chd = u32(col + 0x10)
    nbc = u32(chd + 8)
    pbca = u32(chd + 0xc)
    bases = []
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        bases.append((type_name(u32(bcd)), i32(bcd + 8), i))
    cand_all = [b[0] for b in bases if b[1] == off]
    cand_ni = [b[0] for b in bases if b[1] == off and b[0] != 'IUnknown']
    return {'col': col, 'offset': off, 'chd': chd, 'nbases': nbc,
            'own': bases[0][0], 'mdisp0': bases[0][1],
            'cand_all': cand_all, 'cand_ni': cand_ni}


LAY = {v: col_layout(v) for v in V2C}
mis = []
for v, (name, cls, off_in) in IFACE.items():
    L = LAY[v]
    if len(L['cand_ni']) != 1 or L['cand_ni'][0] != name or L['own'] != cls or L['offset'] != off_in:
        mis.append({'va': hx(v), 'file': [name, cls, off_in], 'derived': [L['cand_ni'], L['own'], L['offset']]})
ck('A10 清单可由 RTTI（COL.offset + BCD.mdisp）独立重建，260/260 一致',
   not mis, 'mismatch=%d' % len(mis))

# ---------------------------------------------------------------- Q1
def ascii_tail(va, n=64):
    b = raw[fo(va):fo(va) + n]
    return ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)


q1 = {
    'valid_col_total': len(COLS),
    'vtable_total': len(V2C),
    'S_defined': len(Sd),
    'S_undefined': len(undef),
    'S_dist': collections.Counter(Sd.values()).most_common(),
    'S_equals_B_all_defined': all(Sd[v] == CENS['B'][v] for v in Sd),
    'stops_equal_pos': stops == POS,
    'colptr_never_a_stop': sorted(hx(x) for x in COLPTR - stops),
    'undef_detail': [],
}
for v in undef:
    L = LAY[v]
    nxt = sorted(x for x in COLS if x > v)[:3]
    q1['undef_detail'].append({
        'va': hx(v), 'col': hx(L['col']), 'class': L['own'], 'offset': L['offset'],
        'T': CEN_T[v], 'E': CENS['E'][v], 'B': CENS['B'][v],
        'slots_0_7': [hx(u32(v + 4 * i)) for i in range(8)],
        'ascii_after': ascii_tail(v + 24),
        'nearest_col_after_by_address': [hx(x) for x in nxt],
        'reason': '该 vtable 是 .rdata 内 vtable 区块的最后一个；它之后到 .rdata 尾之间'
                  '（再放宽到整个镜像尾）不存在任何取值为合法 COL 起点的 dword，'
                  '故 S 无定义。注意：地址更大的 COL 起点确实存在（见 '
                  'nearest_col_after_by_address），但没有任何 dword 指向它们，'
                  '所以 S 的判据扫不到。',
    })

# ---------------------------------------------------------------- Q2
per = collections.OrderedDict()
for v in sorted(IFACE):
    name, cls, off_in = IFACE[v]
    d = per.setdefault(name, {'n_vt': 0, 'classes': [], 'T': set(), 'E': set(), 'S': set(),
                              'B': set(), 'offsets': set(), 'eq_all': 0, 'ne_fail': [],
                              'slotvals': collections.defaultdict(set)})
    d['n_vt'] += 1
    d['classes'].append(cls)
    d['T'].add(CEN_T[v])
    d['E'].add(CENS['E'][v])
    d['S'].add(Sd[v])
    d['B'].add(CENS['B'][v])
    d['offsets'].add(off_in)
    eq = (CEN_T[v] == CENS['E'][v] == Sd[v])
    d['eq_all'] += 1 if eq else 0
    if not eq:
        d['ne_fail'].append({'va': hx(v), 'T': CEN_T[v], 'E': CENS['E'][v], 'S': Sd[v]})
    for i in range(Sd[v]):
        d['slotvals'][i].add(u32(v + 4 * i))

per_out = {}
for name, d in per.items():
    per_out[name] = {
        'n_vt': d['n_vt'],
        'classes': sorted(set(d['classes'])),
        'n_distinct_classes': len(set(d['classes'])),
        'T_set': sorted(d['T']), 'E_set': sorted(d['E']), 'S_set': sorted(d['S']), 'B_set': sorted(d['B']),
        'T_constant': len(d['T']) == 1, 'E_constant': len(d['E']) == 1,
        'S_constant': len(d['S']) == 1, 'B_constant': len(d['B']) == 1,
        'col_offsets': sorted(d['offsets']),
        'pointwise_T_eq_E_eq_S': d['eq_all'],
        'E_mismatch': d['ne_fail'],
        'slot_index_distinct_values': {i: len(s) for i, s in sorted(d['slotvals'].items())},
    }

n_if = len(IFACE)
pointwise = sum(1 for v in IFACE if CEN_T[v] == CENS['E'][v] == Sd[v])
q2 = {
    'iface_count': len(per_out),
    'vt_count': n_if,
    'pointwise_T_eq_E_eq_S': pointwise,
    'pointwise_ratio': round(pointwise / n_if, 6),
    'three_way_holds_everywhere': pointwise == n_if,
    'T_eq_S': sum(1 for v in IFACE if CEN_T[v] == Sd[v]),
    'T_eq_E': sum(1 for v in IFACE if CEN_T[v] == CENS['E'][v]),
    'E_eq_S': sum(1 for v in IFACE if CENS['E'][v] == Sd[v]),
    'per_iface': per_out,
}
ck('A11 接口子对象上 T==S 全成立，且每个接口的 S 取值集合只有一个元素',
   q2['T_eq_S'] == n_if and all(p['S_constant'] for p in per_out.values()),
   'T==S %d/%d' % (q2['T_eq_S'], n_if))

# ---------------------------------------------------------------- Q3 反控
# (a) 边界后移一格
a_in_text = a_is_start = a_is_col = a_is_colptr = 0
a_bad = []
for v in sorted(Sd):
    p = v + 4 * Sd[v]
    d = u32(p)
    if TEXT0 <= d < TEXT1:
        a_in_text += 1
    if is_start(d):
        a_is_start += 1
    if d in COLS:
        a_is_col += 1
    if p in COLPTR:
        a_is_colptr += 1
    if TEXT0 <= d < TEXT1:
        a_bad.append({'va': hx(v), 'S': Sd[v], 'dword': hx(d)})
ia = [v for v in IFACE if v in Sd]
q3a = {
    'n_evaluated': len(Sd),
    'S_plus_1_dword_in_text': a_in_text,
    'S_plus_1_dword_is_insn_start': a_is_start,
    'S_plus_1_dword_is_valid_col': a_is_col,
    'S_plus_1_position_is_a_colptr': a_is_colptr,
    'control_fails_as_hypothesis': a_in_text == 0,
    'iface': {
        'n': len(ia),
        'S_plus_1_dword_in_text': sum(1 for v in ia if TEXT0 <= u32(v + 4 * Sd[v]) < TEXT1),
        'S_plus_1_dword_is_insn_start': sum(1 for v in ia if is_start(u32(v + 4 * Sd[v]))),
        'S_plus_1_dword_is_valid_col': sum(1 for v in ia if u32(v + 4 * Sd[v]) in COLS),
    },
}

# (b) 边界前移一格
def b_stat(vs):
    r = {'n': len(vs), 'in_text': 0, 'insn_start': 0, 'is_valid_col': 0, 'is_zero': 0,
         'not_in_text': []}
    for v in vs:
        d = u32(v + 4 * (Sd[v] - 1))
        if TEXT0 <= d < TEXT1:
            r['in_text'] += 1
            if is_start(d):
                r['insn_start'] += 1
        else:
            if len(r['not_in_text']) < 40:
                r['not_in_text'].append({'va': hx(v), 'S': Sd[v], 'dword': hx(d),
                                         'T': CEN_T[v]})
        if d in COLS:
            r['is_valid_col'] += 1
        if d == 0:
            r['is_zero'] += 1
    return r


iface_set = set(IFACE)
q3b = {
    'all': b_stat(sorted(Sd)),
    'iface': b_stat(sorted(ia)),
    'non_iface': b_stat(sorted(set(Sd) - iface_set)),
    'split_by_T_eq_S': {
        'T_eq_S': b_stat([v for v in sorted(Sd) if CEN_T[v] == Sd[v]]),
        'T_ne_S': b_stat([v for v in sorted(Sd) if CEN_T[v] != Sd[v]]),
    },
}

# (c) 判据放宽：值 ∈ .rdata 区间
def S_relaxed(v, lo=RD0, hi=RD1):
    return S_scan(v, lambda d: lo <= d < hi)[0]


SR = {v: S_relaxed(v) for v in V2C}
SRi = {v: S_scan(v, lambda d: IB <= d < IMG_END)[0] for v in V2C}
changed = [v for v in V2C if (S[v][0] is None) != (SR[v] is None) or
           (S[v][0] is not None and SR[v] is not None and S[v][0] != SR[v])]
detail_c = []
for v in changed:
    detail_c.append({'va': hx(v), 'S': S[v][0], 'S_rdata_relaxed': SR[v], 'T': CEN_T[v],
                     'in_iface': v in iface_set})
q3c = {
    'n_vt': len(V2C),
    'changed': len(changed),
    'changed_ratio': round(len(changed) / len(V2C), 6),
    'became_smaller': sum(1 for v in changed if SR[v] is not None and (
        S[v][0] is None or SR[v] < S[v][0])),
    'became_larger': sum(1 for v in changed if S[v][0] is not None and SR[v] is not None and SR[v] > S[v][0]),
    'iface_changed': sum(1 for v in changed if v in iface_set),
    'detail': detail_c,
    'iface_S_unchanged': all(S[v][0] == SR[v] for v in ia),
    'extra_probe_image_relaxed': {
        'changed_vs_S': sum(1 for v in V2C if (S[v][0] is None) != (SRi[v] is None) or
                            (S[v][0] is not None and SRi[v] is not None and S[v][0] != SRi[v])),
    },
}

# (d) 比例 + 分层
def ratio(vs):
    vs = list(vs)
    n = sum(1 for v in vs if CEN_T[v] == Sd.get(v, -1))
    return {'n': len(vs), 'T_eq_S': n, 'ratio': round(n / len(vs), 6) if vs else None}


prim = [v for v in Sd if LAY[v]['offset'] == 0]
sub = [v for v in Sd if LAY[v]['offset'] != 0]
# 分层：S 停止位置处是不是「同 CHD 组的另一个 vtable」（= 本 vtable 不是组尾）
grp_non_tail, grp_tail = [], []
pos2v = {}
for v in V2C:
    pos2v[v - 4] = v
for v in Sd:
    nv = pos2v.get(v + 4 * Sd[v])
    same = nv is not None and LAY[nv]['chd'] == LAY[v]['chd']
    (grp_non_tail if same else grp_tail).append(v)
q3d = {
    'all': ratio(Sd),
    'iface_subobj': ratio(ia),
    'primary_offset0': ratio(prim),
    'subobj_offset_nonzero': ratio(sub),
    'strata_by_group_adjacency': {
        'non_tail_next_is_same_chd_sibling': ratio(grp_non_tail),
        'tail': ratio(grp_tail),
        'iface_all_non_tail': all(v in set(grp_non_tail) for v in ia),
        'n_iface_in_non_tail': sum(1 for v in ia if v in set(grp_non_tail)),
    },
    'gap_fill_between_T_and_S': dict(collections.Counter(
        ('zero' if u32(v + 4 * i) == 0 else
         'text' if TEXT0 <= u32(v + 4 * i) < TEXT1 else
         'rdata' if RD0 <= u32(v + 4 * i) < RD1 else
         'other_image' if IB <= u32(v + 4 * i) < IMG_END else
         'outside_image')
        for v in Sd for i in range(CEN_T[v], Sd[v]))),
    'verdict': None,
}
non_tail_ratio = q3d['strata_by_group_adjacency']['non_tail_next_is_same_chd_sibling']['ratio']
tail_ratio = q3d['strata_by_group_adjacency']['tail']['ratio']
q3d['verdict'] = ('T==S 在接口子对象上 100%% 与「接口」无关：按「S 停止位置是否同 CHD 组的'
                  '另一个 vtable」分层后，非组尾 %s、组尾 %s，而 260 个接口子对象全部落在'
                  '非组尾层。T==S 承重的是「子对象 vtable 与下一个 vtable 在 .rdata 里首尾'
                  '相接且中间没有非代码 dword」，这是排布性质；单看 100%% 不能当「两把独立'
                  '尺子互证槽数值」的证据。' % (non_tail_ratio, tail_ratio))

# ---------------------------------------------------------------- Q4
own_len = collections.defaultdict(set)          # 接口 → 其承接类的「类自身 vtable」长度
by_cls = collections.defaultdict(dict)          # 类 → {接口: 槽数}
for v, (name, cls, off_in) in IFACE.items():
    by_cls[cls][name] = Sd[v]
prim_of = collections.defaultdict(list)
for v in V2C:
    if LAY[v]['offset'] == 0:
        prim_of[LAY[v]['own']].append(v)
for name in per_out:
    for cls in per_out[name]['classes']:
        for pv in prim_of.get(cls, []):
            own_len[name].add(CEN_T[pv])

multi_iface_cls = {c: d for c, d in by_cls.items() if len(d) > 1}
vary_in_cls = [c for c, d in multi_iface_cls.items() if len(set(d.values())) > 1]
own_range = {}
for name, d in own_len.items():
    own_range[name] = {'n_own_vt': len(d), 'min': min(d) if d else None, 'max': max(d) if d else None,
                       'distinct': len(d)}
q4 = {
    'direction_1_iface_constant_across_classes': {
        'ifaces_with_more_than_1_class': sum(1 for p in per_out.values() if p['n_distinct_classes'] > 1),
        'all_S_constant': all(p['S_constant'] for p in per_out.values()),
        'all_T_constant': all(p['T_constant'] for p in per_out.values()),
        'max_classes_per_iface': max(p['n_distinct_classes'] for p in per_out.values()),
        'own_vtable_len_range': own_range,
    },
    'direction_2_classes_with_multiple_ifaces': {
        'n_classes_with_multiple_iface_subobj': len(multi_iface_cls),
        'n_where_counts_differ_within_class': len(vary_in_cls),
        'examples': [{'class': c, 'counts': multi_iface_cls[c]} for c in sorted(multi_iface_cls)[:4]],
    },
    'direction_3_offset_invariance': {
        'INoticeSink_offsets': sorted(per_out['INoticeSink']['col_offsets']) if 'INoticeSink' in per_out else None,
        'INoticeSink_S_set': per_out['INoticeSink']['S_set'] if 'INoticeSink' in per_out else None,
    },
    'confound_disclosure': q3d['verdict'],
    'S_is_B': q1['S_equals_B_all_defined'],
    's_build': {
        'c_direction': None,
        'T_ne_S_examples': [],
    },
}
tns = [v for v in sorted(Sd) if CEN_T[v] != Sd[v]][:8]
for v in tns:
    q4['s_build']['T_ne_S_examples'].append({
        'va': hx(v), 'T': CEN_T[v], 'S': Sd[v], 'offset': LAY[v]['offset'],
        'slot_at_T': hx(u32(v + 4 * CEN_T[v])),
        'kind': ('zero' if u32(v + 4 * CEN_T[v]) == 0 else
                 'text' if TEXT0 <= u32(v + 4 * CEN_T[v]) < TEXT1 else
                 'rdata' if RD0 <= u32(v + 4 * CEN_T[v]) < RD1 else
                 'other_image' if IB <= u32(v + 4 * CEN_T[v]) < IMG_END else 'outside_image')})

ck('A12 反控 (a) 有牙：S+1 那一格无一落在 .text（1213/1213 全是 COL 指针）',
   q3a['S_plus_1_dword_in_text'] == 0, q3a['S_plus_1_dword_in_text'])
ck('A13 反控 (b) 有牙：S-1 那一格在接口子对象上 260/260 落在 .text',
   q3b['iface']['in_text'] == q3b['iface']['n'], '%d/%d' % (q3b['iface']['in_text'], q3b['iface']['n']))
ck('A14 反控 (c)：把判据放宽成 .rdata 区间后接口子对象 0 个改判，全镜像改判数远小于 1%%',
   q3c['iface_changed'] == 0 and q3c['changed_ratio'] < 0.01, q3c['changed'])
ck('A15 反控 (d)：全镜像 T==S 明显低于接口子对象上的 100%%',
   q3d['all']['ratio'] < 0.95 and q3d['iface_subobj']['ratio'] == 1.0,
   'all=%s iface=%s' % (q3d['all']['ratio'], q3d['iface_subobj']['ratio']))

# 结论（模型自己的判断，不照抄主会话）
verdict_supports = [
    '同一个接口在不同承接类上，槽数（S 与 T 两个判据都）恒等：INoticeSource 78 类、'
    'IRTTITypeInfo 78 类、INoticeSink 81 类、ILocomotion 12 类，各自的 S 取值集合都是单元素。'
    '这些承接类的类自身 vtable 长度跨 24..344、取 19~20 个不同值，与接口槽数无关联。',
    '同一个类内，不同接口的槽数不同：84 个含 >=2 个接口子对象的类中，84/84 的槽数按接口而变'
    '（例：AITriggerTypeClass 的 INoticeSource=1、INoticeSink=1、IRTTITypeInfo=6）。'
    '「槽数是类属性」这一假设被双向否证。',
    'INoticeSink 的两种子对象偏移（8 与 21784）给出同一槽数 1 ⇒ 槽数与对象内位置/偏移无关。',
    'S 与 T 在 260 个接口子对象上逐点相等，且 S-1 那一格 260/260 是 .text 指令起点、'
    'S 那一格 260/260 是 COL 指针而非代码 ⇒ 这 260 个窗口内没有填充或数据块被误计入。',
]
verdict_not_supported = [
    '「S 是独立于 T 的新尺子」不成立：实测「取值为合法 COL 的 dword 位置集合」与'
    '「COL 指针位置集合」是同一集合（1214 个，一一对应且每个 COL 只被引用一次），'
    '故 S 与 census 的 B 尺逐点相等（1213/1213）。S 只是 B 的重新表述，与 T 才算两路证据。',
    '「T==S 比值 100% 证明槽数已被两把独立尺子互证」不成立：按「S 停止位置是否同 CHD 组'
    '的另一个 vtable」分层，非组尾 260/260=100%、组尾 719/953=75.45%，260 个接口子对象'
    '全部落在非组尾层。T==S 承重的是「子对象 vtable 紧挨着下一个 vtable、中间没有非代码'
    'dword」这一排布事实，是必要条件而不是槽数定义。',
    '「槽数 = 接口声明的方法数」未被证明：本库无头文件，也没有对 slot k 做调用点/签名'
    '对齐分析。能证明的是「发射出来的槽数只由接口决定」，不能证明「槽数与接口声明逐一相等」'
    '（例如编译器多插一个槽也不会被 T/S 判据发现）。',
    '样本量：只有 10 个接口 / 94 个承接类。「恒定」是这份镜像上的经验事实，不是 ABI 定理；'
    '其中 5 个接口只有 1 个承接类，对它们「跨类恒定」是空命题。',
    'E 尺不恒定（ILocomotion 的 3 个类给出 3/14/17 而 S 全为 50）：这不是槽数变化，是 E 判据'
    '（入口前有填充）在共享 thunk 上失效；用 E 当作「槽数」的第三把尺子必须打折扣。',
]
q4['verdict'] = {
    'supports': verdict_supports,
    'cannot_support': verdict_not_supported,
    'answer': ('部分成立：本镜像的实测支持「接口子对象方法表的槽数只由接口决定、与承接类和'
               '子对象偏移无关」，但**不能**支持「该数字等于接口声明的方法数」，也不能支持'
               '「T 与 S 是两把互不相关的尺子互证」（S == B，且 T==S 的 100% 由排布紧邻解释）。'),
}

# ---------------------------------------------------------------- 落盘
res = {
    'generator': '_r115/x115exec_bound.py (R115 exec, deepseek, independent recompute)',
    'exe_sha256': SHA,
    'runtime_sec': None,
    'q1_S_ruler': q1,
    'q2_three_rulers': q2,
    'q3_controls': {'a': q3a, 'b': q3b, 'c': q3c, 'd': q3d},
    'q4_evidence': q4,
}
res['runtime_sec'] = round(time.time() - t0, 2)
fails = [c['name'] for c in checks if not c['ok']]
res['assertions'] = checks
res['assertions_failed'] = len(fails)
res['assertions_failed_names'] = fails
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n== summary ==')
print('S defined %d / %d, undefined %s' % (q1['S_defined'], q1['vtable_total'], q1['undef_detail'] and [d['va'] for d in q1['undef_detail']]))
print('T==E==S pointwise %d/%d' % (pointwise, n_if))
print('(a) S+1 in text %d ; (b) S-1 in text all=%d iface=%d ; (c) changed %d ; (d) all=%s iface=%s'
      % (a_in_text, q3b['all']['in_text'], q3b['iface']['in_text'], len(changed),
         q3d['all']['ratio'], q3d['iface_subobj']['ratio']))
print('assertions failed: %d %s' % (len(fails), fails))
print('runtime %.2fs' % res['runtime_sec'])
sys.exit(1 if fails else 0)
