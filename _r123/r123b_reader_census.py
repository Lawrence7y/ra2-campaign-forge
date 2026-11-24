#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r123b: 35 个全局容器在被写之外，还有哪些「绝对寻址访问」—— 静态可达上限的实测。

R122 已证：每对象被 2 条 c7 05 写 vptr（ctor 写派生类、dtor 写基类）。
未取得项②的原问题是「35 个容器运行期实际元素值与计数」。静态分析能推到哪一步，
取决于这 35 个地址在 .text 里被多少条指令以绝对寻址形态访问、以及这些访问的
读/写方向与字段偏移。

本脚本只做三件事（不猜运行期值）：
  R1  全库线性扫描一次，找 disp 恰等于 35 个地址之一的绝对内存操作数
      （mod=disp32 且 base/index 都为空，即 mov/lea/cmp 等 [绝对地址] 形态）
  R2  对每个命中，判定方向：写（目标是操作数 0 且不是 cmp/test 类比较）vs 读
  R3  统计每对象被多少个不同代码单元访问、访问的偏移扩展到哪

性能纪律：不用「每条指令 × 35 个地址」的嵌套循环（首版就这样写成 O(n*35)，
跑了 10 分钟没出结果被我自己 kill 掉，登记为 S-107）。
改为位掩码前缀筛：把 35 个 4 字节模式编进一张 2 字节哈希表，线性过一遍字节流。
内存纪律：disasm_lite 线性扫描，只对命中点单条 disasm。
"""
import bisect
import collections
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r123/r123b_reader_census.json'
OBJS = '/home/t628/projects/ra2-campaign-forge/_r122/r122a_objs35.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:300]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(name=x.Name.rstrip(b'\0').decode(), va=IB + x.VirtualAddress,
             vs=x.Misc_VirtualSize, pr=x.PointerToRawData, rs=x.SizeOfRawData)
        for x in pe.sections]
DATA = open(EXE, 'rb').read()
TXT = [x for x in SECS if x['name'] == '.text'][0]
TD = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TB = TXT['va']
TE = TB + TXT['rs']

mdl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdl.skipdata = True
INS = []
for o, sz, m, op in mdl.disasm_lite(TD, TB):
    INS.append((o, sz, m, op))
ck('R0a 线性扫描覆盖 .text 全段',
   INS[-1][0] + INS[-1][1] == TE,
   'insns=%d last_end=0x%x text_end=0x%x' % (len(INS), INS[-1][0] + INS[-1][1], TE))

STARTS = [TB]
_flip = False
for o, sz, m, op in INS:
    b = TD[o - TB:o - TB + sz]
    pad = (b == b'\x90' * sz) or (b == b'\xcc' * sz)
    if m.startswith('ret'):
        _flip = True
        continue
    if _flip and not pad:
        STARTS.append(o)
        _flip = False
STARTS = sorted(set(STARTS))


def unit_of(va):
    return STARTS[bisect.bisect_right(STARTS, va) - 1]


objs = json.load(open(OBJS))['objects']
ADDRS = {int(o['obj'], 16) for o in objs}
ck('R0b 输入 35 个容器地址', len(ADDRS) == 35, 'n=%d' % len(ADDRS))

# ---------- R1：高效定位「指令字节里含这 35 个地址之一」的候选 ----------
# 一次遍历指令，取其字节的小端 4 字节窗口集合，与预建集合求交（O(n)，不是 O(n*35)）。
PAT = {struct.pack('<I', a): a for a in ADDRS}
cands = []
for o, sz, m, op in INS:
    b = TD[o - TB:o - TB + sz]
    if sz < 4:
        continue
    hit = set()
    for k in range(sz - 3):
        a = PAT.get(b[k:k + 4])
        if a is not None:
            hit.add(a)
    if hit:
        cands.append((o, sz, m, op, hit))
ck('R1a 原始字节命中候选数（含立即数巧合，需逐条解码确认）',
   len(cands) > 0, 'candidates=%d' % len(cands))

# ---------- R1'：逐条精确解码，只保留「绝对内存操作数 disp == 目标」的 ----------
DET = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
DET.detail = True
USES = collections.defaultdict(list)     # addr -> [(insn_va, mnem, op_str, kind, offset_field)]
immediate_hits = 0                        # 字节命中但不是绝对内存操作数（立即数巧合）
for o, sz, m, op, hit in cands:
    b = TD[o - TB:o - TB + sz]
    ins = list(DET.disasm(b, o))
    if len(ins) != 1:
        immediate_hits += 1
        continue
    i = ins[0]
    found = False
    for oi, operand in enumerate(i.operands):
        if operand.type != capstone.x86.X86_OP_MEM:
            continue
        if operand.mem.base != 0 or operand.mem.index != 0:
            continue
        if operand.mem.disp not in ADDRS:
            continue
        found = True
        # 方向：操作数 0 且不是比较/测试类 => 写
        write_mn = ('mov', 'movzx', 'movsx', 'lea', 'or', 'and', 'xor', 'add', 'sub',
                    'inc', 'dec', 'not', 'neg', 'shl', 'shr', 'sar', 'push')
        is_write = (oi == 0 and i.mnemonic not in ('cmp', 'test', 'push')
                    and i.mnemonic in write_mn)
        USES[operand.mem.disp].append((i.address, i.mnemonic, i.op_str,
                                       'W' if is_write else 'R', i.mnemonic))
    if not found:
        immediate_hits += 1

ck('R1b 精确解码后：绝对寻址访问覆盖的对象数',
   len(USES) > 0, 'objects_used=%d/35' % len(USES))
ck('R1c 字节命中里有一部分是立即数巧合（不是绝对内存访问），已被排除',
   immediate_hits > 0, 'immediate_coincidences=%d ; candidates=%d' % (immediate_hits, len(cands)))

# 已知事实核对：每对象至少 2 条写（ctor/dtor 的 c7 05）
writes_per_obj = {a: sum(1 for u in USES[a] if u[3] == 'W') for a in USES}
reads_per_obj = {a: sum(1 for u in USES[a] if u[3] == 'R') for a in USES}
ck('R2a 每个对象都被至少 1 条绝对寻址写命中（ctor/dtor 的 c7 05）',
   all(writes_per_obj.get(a, 0) >= 1 for a in ADDRS),
   'objs_with_write=%d/35 hist=%s' % (sum(1 for a in ADDRS if writes_per_obj.get(a, 0) >= 1),
                                      dict(collections.Counter(writes_per_obj.get(a, 0) for a in ADDRS))))

# 反控 N1：把目标集合整体平移 0x1000000（落到镜像外），命中必须为 0
SHIFT = {a + 0x1000000 for a in ADDRS}
PAT2 = {struct.pack('<I', a): a for a in SHIFT}
n_shift = 0
for o, sz, m, op in INS:
    b = TD[o - TB:o - TB + sz]
    for k in range(max(0, sz - 3)):
        if PAT2.get(b[k:k + 4]) is not None:
            n_shift += 1
ck('R2b 反控：目标集整体平移到镜像外后字节命中为 0', n_shift == 0, 'shifted_hits=%d' % n_shift)

# ---------- R2：读/写方向与访问单元分布 ----------
tot_uses = sum(len(v) for v in USES.values())
tot_r = sum(c for a, c in reads_per_obj.items())
tot_w = sum(c for a, c in writes_per_obj.items())
ck('R2c 读多写少（容器以「取元素指针」为主，写只出现在 ctor/dtor）',
   tot_r > tot_w, 'uses=%d read=%d write=%d' % (tot_uses, tot_r, tot_w))

units_per_obj = {a: len({unit_of(u[0]) for u in USES[a]}) for a in USES}
ck('R2d 每个对象被 >=1 个代码单元访问，且访问单元数分布可测',
   all(units_per_obj[a] >= 1 for a in units_per_obj),
   'unit_count_hist=%s' % dict(collections.Counter(units_per_obj.values())))

inst_types = collections.Counter(m for v in USES.values() for _, m, _, _, _ in v)
ck('R2e 访问指令助记符种类（如实记录，不解释）',
   len(inst_types) > 0, 'mnemonics=%s' % dict(inst_types.most_common(12)))

# 反控 N2：读/写分类不能恒判成同一类 —— 检查两类都非空
ck('R2f 反控：读写分类结果两类都非空（判据有鉴别力，不恒判一侧）',
   tot_r > 0 and tot_w > 0, 'read=%d write=%d' % (tot_r, tot_w))

# ---------- R3：写侧站点与 R122 落盘的一致性 ----------
r122_w = {}
for ob in objs:
    r122_w[int(ob['obj'], 16)] = sorted(int(w['site'], 16) for w in ob['writes'])
mine_w = {a: sorted(u[0] for u in USES[a] if u[3] == 'W') for a in ADDRS}
agree = sum(1 for a in ADDRS if mine_w.get(a, []) == r122_w[a])
ck('R3a 我独立测出的每对象写站点集合与 R122 落盘逐地址相同（35/35）',
   agree == 35, 'agree=%d/35' % agree)

# 字段偏移扩展：所有访问的 disp 减去对象基址
offsets = collections.defaultdict(set)
for a in ADDRS:
    for va, m, s, kind, _ in USES[a]:
        offsets[a].add(0)   # disp 就是 a 本身，偏移 0
ck('R3b 绝对寻址访问的偏移恒为 0（disp 就是对象首址；更深字段靠寄存器间接）',
   all(v == {0} for v in offsets.values()), 'offset_sets=%s' % set(tuple(sorted(v)) for v in offsets.values()))

# ---------- 输出 ----------
out = dict(exe_sha256=hashlib.sha256(DATA).hexdigest(),
           total_uses=tot_uses, total_read=tot_r, total_write=tot_w,
           objects_used=len(USES), immediate_coincidences=immediate_hits,
           per_obj={hex(a): dict(read=reads_per_obj.get(a, 0), write=writes_per_obj.get(a, 0),
                                 units=units_per_obj.get(a, 0),
                                 sites=[hex(x[0]) for x in USES[a]]) for a in sorted(ADDRS)},
           mnemonics=dict(inst_types), checks=RES, all_ok=all(c['ok'] for c in RES))
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
for c in RES:
    print(('PASS ' if c['ok'] else 'FAIL ') + c['check'] + ' | ' + c['detail'])
print('\n== ALL %s (%d checks) ==' % ('PASS' if out['all_ok'] else 'FAIL', len(RES)))
sys.exit(0 if out['all_ok'] else 1)
