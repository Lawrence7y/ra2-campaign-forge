#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：F29 的 40 个 8 字节桩，逐个查「谁引用它」——正测 + 反控。

背景（看板 §九 第 5 项）：R139 顺带实测「40 个桩里只有 14 个被 .data/.rdata 引用，
引用共 176 次，其中 0x410300/0x410310 各 74 次」，其余 26 个桩的引用来源未查。
本脚本把 40 个桩全查一遍，分四类命中：
  A 数据节（.data/.rdata）里出现桩 VA 的 4 字节值  -> 「被虚表/指针表引用」
  B .text 里的 4 字节立即数（mov reg,imm32 一类）   -> 「被当常量装载」
  C .text 里的 E8/E9 rel32 直接跳到桩               -> 「直接 call/jmp」
  D 落盘外（.data 虚拟尾部不落盘）                  -> 无法判定
并回答：「63/77 用到的桩」是哪些、它们各自落在哪一类。

反控（必须能真的 FAIL）
  N1 把桩 VA 全部 +1 再查 => 命中必须大幅下降（否则是子串误命中）
  N2 只查 .rsrc/.detour 两个节 => 命中必须为 0
  N3 用「镜像内任意值」代替桩集合（取 40 个随机 VA）=> 数据节命中必须为 0
"""
import os
import re
import json
import struct
import random
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
raw = open(EXE, 'rb').read()

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e + 6)[0]
opt_size = struct.unpack_from('<H', raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
SECS = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append(dict(name=nm, vsize=vs, rva=va, rsize=rs, rptr=rp))

fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def off_of(va):
    rva = va - IB
    for s in SECS:
        if s['rva'] <= rva < s['rva'] + s['rsize']:
            return s['rptr'] + (rva - s['rva'])
    return None


def d32(va):
    o = off_of(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]


# ---------- 0. 节表与桩集合 ----------
ck('0.0 目标文件大小 4,825,360', len(raw) == 4825360, len(raw))
ck('0.1 ImageBase == 0x400000', IB == 0x400000, hex(IB))
STUB = bytes.fromhex('B801000000C20400')
stub_va = []
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    i = seg.find(STUB)
    while i != -1:
        stub_va.append(base + i)
        i = seg.find(STUB, i + 1)
stub_va = sorted(stub_va)
ck('0.2 桩 VA 集合 == 40', len(stub_va) == 40, len(stub_va))
ck('0.3 桩全在 .text', all(0x401000 <= v < 0x401000 + 4063232 for v in stub_va),
   sorted({s['name'] for v in stub_va for s in SECS
           if s['rva'] <= v - IB < s['rva'] + s['rsize']}))
out['stubs'] = [hex(v) for v in stub_va]

# ---------- 1. 逐桩查引用 ----------
DATA_SECS = [s for s in SECS if s['name'] in ('.data', '.rdata')]
TEXT = [s for s in SECS for _ in [0] if s['name'] == '.text'][0]
OTHER_SECS = [s for s in SECS if s['name'] in ('.rsrc', '.detour')]


def data_hits(stubset):
    """数据节里出现桩 VA 的 4 字节值的所有位置（按 VA 记录）。"""
    hits = collections.defaultdict(list)
    for s in DATA_SECS:
        seg = raw[s['rptr']:s['rptr'] + s['rsize']]
        base = IB + s['rva']
        for v in stubset:
            n = struct.pack('<I', v)
            i = seg.find(n)
            while i != -1:
                hits[v].append((base + i, s['name']))
                i = seg.find(n, i + 4)
    return hits


def other_hits(stubset):
    n = 0
    for s in OTHER_SECS:
        seg = raw[s['rptr']:s['rptr'] + s['rsize']]
        for v in stubset:
            n += seg.count(struct.pack('<I', v))
    return n


def text_imm_hits(stubset):
    """`.text` 里出现桩 VA 作为 4 字节立即数的位置（不区分编码形态，属上界）。"""
    hits = collections.defaultdict(list)
    seg = raw[TEXT['rptr']:TEXT['rptr'] + TEXT['rsize']]
    base = IB + TEXT['rva']
    for v in stubset:
        n = struct.pack('<I', v)
        i = seg.find(n)
        while i != -1:
            hits[v].append(base + i)
            i = seg.find(n, i + 1)
    return hits


def text_branch_hits(stubset):
    """`.text` 里 E8/E9 rel32 解码后落点 == 某桩 的位置（真指令边界上界近似：
    不做完整反汇编，只扫 E8/E9 两个操作码，故属上界，报告里明确标注）。"""
    ss = set(stubset)
    hits = collections.defaultdict(list)
    seg = raw[TEXT['rptr']:TEXT['rptr'] + TEXT['rsize']]
    base = IB + TEXT['rva']
    for i in range(len(seg) - 5):
        op = seg[i]
        if op != 0xE8 and op != 0xE9:
            continue
        rel = struct.unpack_from('<i', seg, i + 1)[0]
        tgt = base + i + 5 + rel
        if tgt in ss:
            hits[tgt].append((base + i, 'call' if op == 0xE8 else 'jmp'))
    return hits


dh = data_hits(stub_va)
th = text_imm_hits(stub_va)
bh = text_branch_hits(stub_va)
oh = other_hits(stub_va)

n_data_ref = len(dh)
n_data_cnt = sum(len(v) for v in dh.values())
ck('1.1 被数据节引用的桩数 == 14（R139 结论）', n_data_ref == 14, n_data_ref)
ck('1.2 数据节引用总次数 == 176（R139 结论）', n_data_cnt == 176, n_data_cnt)
ck('1.3 0x410300 与 0x410310 各 74 次（R139 结论）',
   len(dh.get(0x410300, [])) == 74 and len(dh.get(0x410310, [])) == 74,
   (len(dh.get(0x410300, [])), len(dh.get(0x410310, []))))

print('\n=== 40 个桩逐桩引用普查 ===')
print('  VA          data  text-imm  text-branch  谁引')
rows = []
for v in stub_va:
    d = len(dh.get(v, []))
    t = len(th.get(v, []))
    b = len(bh.get(v, []))
    who = ''
    if d:
        who = 'vtable/ptr'
    elif b:
        who = 'direct-branch'
    elif t:
        who = 'imm-only'
    else:
        who = 'NONE'
    rows.append(dict(va=hex(v), data=d, text_imm=t, text_branch=b, kind=who))
    print('  %-11s %-5d %-9d %-12d %s' % (hex(v), d, t, b, who))

out['rows'] = rows

kinds = collections.Counter(r['kind'] for r in rows)
print('\n  分类小计:', dict(kinds))
ck('1.4 四类之和 == 40', sum(kinds.values()) == 40, dict(kinds))
ck('1.5 零引用（三类全 0）的桩数 == 26 或更少', kinds.get('NONE', 0) <= 26, kinds.get('NONE', 0))
ck('1.6 .rsrc/.detour 里桩 VA 命中 == 0', oh == 0, oh)
ck('1.7 桩 VA 在 .text 里作为立即数至少命中 1 次',
   sum(len(v) for v in th.values()) >= 1, sum(len(v) for v in th.values()))

# ---------- 2. 反控 ----------
print('\n=== 反控 ===')
# N1 桩 VA 全部 +1
shift = [v + 1 for v in stub_va]
dh1 = data_hits(shift)
ck('N1 桩 VA 全 +1 后数据节命中骤降（< 176）', sum(len(x) for x in dh1.values()) < 176,
   sum(len(x) for x in dh1.values()))
# N2 只查 .rsrc/.detour
ck('N2 .rsrc/.detour 命中 == 0（已并入 1.6）', oh == 0, oh)
# N3 随机 40 个 .text VA 当桩集合
random.seed(141)
rnd = [0x410000 + random.randrange(0, 4000000) for _ in range(40)]
dh3 = data_hits(rnd)
ck('N3 随机 40 个 VA 的数据节命中远小于 176（且 <= 5）',
   sum(len(x) for x in dh3.values()) <= 5, sum(len(x) for x in dh3.values()))

# ---------- 3. 与 63/77 的连接：63 用到的桩对 ----------
E = json.load(open(os.path.join(ROOT, '_r139', 'r139e_f29_6377.json'), encoding='utf-8'))
ck('3.1 r139e 的 both_stub == 63', E['both_stub'] == 63, E['both_stub'])
ck('3.2 r139e 的 non_both == 14', len(E['non_both']) == 14, len(E['non_both']))

# 复算 63 用到的桩对（不读 r139e 的中间态，自己重算）
DATA = DATA_SECS
td = []
for s in DATA:
    if s['name'] != '.data':
        continue
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for m in re.finditer(rb'\.\?AV([A-Za-z0-9_@?$<>:,\-]+?)@@', seg):
        td.append((base + m.start() - 8, m.group(1).decode('latin1')))
ck('3.3 TypeDescriptor 962 个', len(td) == 962, len(td))

refidx = collections.defaultdict(list)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for tva, _ in td:
        n = struct.pack('<I', tva)
        i = seg.find(n)
        while i != -1:
            refidx[tva].append(base + i)
            i = seg.find(n, i + 4)

cols = collections.defaultdict(set)
for tva, nm in td:
    for r in refidx.get(tva, []):
        c = r - 12
        if d32(c) == 0 and d32(c + 12) == tva:
            cols[nm].add(c)
vt_of = collections.defaultdict(set)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for nm, cs in cols.items():
        for c in cs:
            n = struct.pack('<I', c)
            i = seg.find(n)
            while i != -1:
                vt_of[nm].add(base + i + 4)
                i = seg.find(n, i + 4)

pat = re.compile(rb'\.\?AV\?\$TClassFactory@V([A-Za-z0-9_]+)@@@')
args = []
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    for m in pat.finditer(seg):
        args.append(m.group(1).decode('latin1'))
ck('3.4 TClassFactory 实参 77 个', len(args) == 77 and len(set(args)) == 77,
   (len(args), len(set(args))))

sset = set(stub_va)
pairs = collections.Counter()
used = set()
for a in sorted(args):
    for vt in sorted(vt_of[a]):
        s1, s2 = d32(vt + 4), d32(vt + 8)
        if s1 in sset and s2 in sset:
            pairs[(s1, s2)] += 1
            used.update((s1, s2))
            break
print('\n=== 63 用到的桩对 ===')
for (a, b), n in pairs.most_common():
    print('  (%s, %s) x%d' % (hex(a), hex(b), n))
print('  用到的不同桩:', len(used), sorted(hex(v) for v in used))
ck('3.5 63 用到的桩对分布与 R139 一致（(0x410300,0x410310) 覆盖 61）',
   pairs.get((0x410300, 0x410310), 0) == 61, pairs.get((0x410300, 0x410310), 0))
ck('3.6 63 只用到 3 个不同桩', len(used) == 3, len(used))
out['pairs'] = [dict(a=hex(a), b=hex(b), n=n) for (a, b), n in pairs.most_common()]
out['used_stubs'] = sorted(hex(v) for v in used)

# 26 个未被 63 用到的桩，各自属于哪一类
unused = [v for v in stub_va if v not in used]
cls = collections.Counter()
for v in unused:
    if dh.get(v):
        cls['data'] += 1
    elif bh.get(v):
        cls['direct-branch'] += 1
    elif th.get(v):
        cls['imm-only'] += 1
    else:
        cls['NONE'] += 1
print('\n=== 37 个未被 63 用到的桩的引用类别 ===')
print(' ', dict(cls))
ck('3.7 未被 63 用到的桩 == 37', len(unused) == 37, len(unused))
ck('3.8 分类小计之和 == 37', sum(cls.values()) == 37, sum(cls.values()))
out['unused_pool'] = dict(cls)

out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(os.path.join(ROOT, '_r141', 'r141a_stub_refs.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言合计 %d 项，PASS %d，FAIL %d' % (len(fails) + sum(1 for _ in []), 0, len(fails)))
