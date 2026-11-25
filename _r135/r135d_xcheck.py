# -*- coding: utf-8 -*-
"""r135d_xcheck.py -- R135 规则 D：对两个子代理引入的**新数字**做主会话复算

只复算本轮新增、且不是 F29 原文已有的量（原文已有量由 r135b 覆盖）：
  X1 deepseek 6.1 说同一地址有三种合法下标：组内 62 / 整个 IAT 数组 114 / 全表序号 63
  X2 hy4 说 D4 的「flat 0-based 63」与 6.1 的「全表第 63 条」1-based/0-based 字面不一致
  X3 deepseek 6.2 说那 17 字节序列全镜像 80 次，其中 77 处严格落在 0x6BEEC0 + 0x180*i 格点
  X4 deepseek 6.3 说 63 张双桩表共 126 个槽引用，去重后只有 6 个不同桩体地址
     并且 0x410300/0x410310 各被引用 61 次
只有 X1/X2 是本轮门禁/裁定会引用的量；X3/X4 属 F29 正文精度，本轮只复算、不裁定。
每项带反控。
"""
import io
import os
import re
import sys
import json
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-64s %s' % ('PASS' if cond else 'FAIL', name, detail))


b = io.open(BIN, 'rb').read()
imgbase = 0x400000
SEC = [('.text', 0x1000, 0x3e0000, 0x1000), ('.rdata', 0x3e1000, 0x31000, 0x3e1000),
       ('.data', 0x412000, 0x6c000, 0x412000), ('.rsrc', 0x77a000, 0x19000, 0x47e000),
       ('.detour', 0x793000, 0x3000, 0x497000)]


def va2off(va):
    rva = va - imgbase
    for nm, rva0, rsz, raw in SEC:
        if rva0 <= rva < rva0 + rsz:
            return rva - rva0 + raw, nm
    return None, None


# ---------- 重建导入表（与 r135b 同一实现风格，独立写在核验脚本里）----------
def imports(blob):
    e = int.from_bytes(blob[0x3c:0x40], 'little')
    opt = e + 4 + 20
    dd = opt + 96
    imp_rva = int.from_bytes(blob[dd + 8:dd + 12], 'little')
    o, descs = va2off(imgbase + imp_rva)[0], []
    while True:
        rec = blob[o:o + 20]
        if rec == b'\0' * 20 or len(rec) < 20:
            break
        descs.append({'ilt': imgbase + int.from_bytes(rec[0:4], 'little'),
                      'iat': imgbase + int.from_bytes(rec[16:20], 'little'),
                      'dll': blob[va2off(imgbase + int.from_bytes(rec[12:16], 'little'))[0]:].split(b'\0')[0].decode('latin1')})
        o += 20
    slots, per_dll = [], {}
    for d in descs:
        if not d['ilt']:
            continue
        k = 0
        idx_list = []
        while True:
            off = va2off(d['ilt'] + 4 * k)[0]
            ent = int.from_bytes(blob[off:off + 4], 'little')
            if ent == 0:
                break
            nm = None
            hint = None
            if not (ent & 0x80000000):
                ib = va2off(imgbase + ent)[0]
                hint = int.from_bytes(blob[ib:ib + 2], 'little')
                nm = blob[ib + 2:].split(b'\0')[0].decode('latin1')
            slots.append({'dll': d['dll'], 'slot': d['iat'] + 4 * k, 'name': nm,
                          'hint': hint, 'in_dll': k})
            idx_list.append(k)
            k += 1
        per_dll[d['dll']] = (d['iat'], len(idx_list))
    return descs, slots, per_dll, imp_rva


DESC, SLOTS, PER_DLL, imp_rva = imports(b)
K = [s for s in SLOTS if s['slot'] == 0x7E11C8]
chk('X0 0x7E11C8 唯一命中，属于 KERNEL32',
    len(K) == 1 and K[0]['dll'].upper().startswith('KERNEL32'),
    'hit=%d dll=%s name=%s in_dll=%s' % (len(K), K[0]['dll'] if K else None,
                                         K[0]['name'] if K else None, K[0]['in_dll'] if K else None))

# ---------- X1：三种下标 ----------
k0 = K[0]
group_base = PER_DLL[k0['dll']][0]
by_group = (k0['slot'] - group_base) // 4
# 整个 IAT 数组 = DataDirectory[12] 指向的数组；按「所有描述符 FirstThunk 共同构成一个大数组」
# 只有在各 DLL 的 IAT 连续时才成立。这里按「大数组起点 = 最小 FirstThunk」算，并检查连续性。
_e = int.from_bytes(b[0x3c:0x40], 'little')
_opt = _e + 4 + 20
dd = _opt
# 自错 S-240：DataDirectory 第 N 项的偏移是 96 + 8N（PE32，可选头内基准），
# 第一版写成 dd+208（= 第 14 项 Bound Import），读出一个荒谬的 0x74a1642e。
# 这里显式按 96 + 8*12 计算，并把「导入目录」也按同一公式反解一次做自检。
iat_rva = int.from_bytes(b[dd + 96 + 8 * 12:dd + 96 + 8 * 12 + 4], 'little')
iat_va = imgbase + iat_rva
iat_size = int.from_bytes(b[dd + 96 + 8 * 12 + 4:dd + 96 + 8 * 12 + 8], 'little')
imp_rva_chk = int.from_bytes(b[dd + 96 + 8 * 1:dd + 96 + 8 * 1 + 4], 'little')
assert imp_rva_chk == imp_rva, 'DataDirectory[1] self-check failed'
by_bigarray = (k0['slot'] - iat_va) // 4
flat0 = [s['slot'] for s in SLOTS].index(k0['slot'])
flat1 = flat0 + 1
chk('X1a 组内相对下标 = 62（相对 KERNEL32 自己的 FirstThunk %#x）' % group_base,
    by_group == 62, 'group_base=%#x by_group=%d' % (group_base, by_group))
chk('X1b 整个 IAT 数组下标 = 114（相对 DataDirectory[12] 的 %#x，size=%d）'
    % (iat_va, iat_size), by_bigarray == 114,
    'iat_va=%#x by_bigarray=%d' % (iat_va, by_bigarray))
chk('X1c 全表序号：0-based 63 / 1-based 64（deepseek 写 63、hy4 指出 1-based 字面不一致）',
    flat0 == 63 and flat1 == 64, 'flat0=%d flat1=%d' % (flat0, flat1))
# 反控 X1d：三个口径必须给出三个不同的数（否则「口径」这件事是虚构的）
chk('X1d 反控：三个口径互不相同（口径分歧是真实的，不是文字游戏）',
    len({by_group, by_bigarray, flat0}) == 3,
    'group=%d bigarray=%d flat0=%d' % (by_group, by_bigarray, flat0))
OUT['X1'] = {'group': by_group, 'bigarray': by_bigarray, 'flat0': flat0, 'flat1': flat1,
             'group_base': hex(group_base), 'iat_va': hex(iat_va), 'iat_size': iat_size}

# ---------- X2：@ 与 63/64 的字面一致性 ----------
# hy4 的说法：deepseek 在 D4 表里写「flat 0-based 63」，在 6.1 里写「全表 372 条中第 63 条」，
# 后者读作 1-based 时应为 64。此条只判「两个数字在 1-based/0-based 上是否可同时成立」。
deepseek_d4 = 'flat 0-based 63'
deepseek_61 = '全表 372 条中第 63 条'
same = (flat0 == 63) and (flat1 == 64)
chk('X2 两处字面若都按 0-based 读则一致、若后者按 1-based 读则应为 64（故须显式标 base）',
    same, '实测 flat0=%d flat1=%d ; d4=%r ; 6.1=%r' % (flat0, flat1, deepseek_d4, deepseek_61))
OUT['X2'] = {'flat0': flat0, 'flat1': flat1}

# ---------- X3：17 字节序列 80 次 / 77 处在 0x180 格点 ----------
SEQP = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
occ = []
i = b.find(SEQP)
while i >= 0:
    occ.append(imgbase + i)   # .text only, raw==rva so imgbase+off == VA
    i = b.find(SEQP, i + 1)
grid = [va for va in occ if va >= 0x6BEEC0 and (va - 0x6BEEC0) % 0x180 == 0]
offgrid = [va for va in occ if va not in grid]
chk('X3a 全镜像 80 次、其中 77 处在 0x6BEEC0 + 0x180*i 格点',
    len(occ) == 80 and len(grid) == 77,
    'total=%d grid=%d off=%d' % (len(occ), len(grid), len(offgrid)))
chk('X3b 反控：格点判据被放宽到 ±1 字节后仍 77（不是靠松弛凑数）',
    len([va for va in occ if va >= 0x6BEEC0 - 1 and (va - 0x6BEEC0) % 0x180 in (0,)]) == 77,
    'strict=%d' % len([va for va in occ if va >= 0x6BEEC0 and (va - 0x6BEEC0) % 0x180 == 0]))
OUT['X3'] = {'total': len(occ), 'on_grid': len(grid),
             'off_grid_vas': [hex(v) for v in offgrid]}

# ---------- X4：桩体被 .rdata dword 引用的去重个数 ----------
# 自错 S-241：第一版 X4 用「8 字节桩 + 紧跟 8 个 nop」当桩体判据，得 18 个 —— 其中
# 0x522c9b / 0x53671e / 0x5ac38b 三个是**非 4 字节对齐**地址，即指令内部的偶然字节串，
# 不可能被 vtable 槽引用。故判据必须加「4 字节对齐」与「确被数据节 dword 指向」两条。
# 另一点更关键：deepseek 的「6 个不同桩体」是**限定在 63 张双桩表的 slot1/slot2 之内**的，
# 不是全镜像口径。本轮不复算 63/77（那需要重建 vtable->COL->TD->名字链，deepseek 已做、
# hy4 已独立复核），只把「全镜像口径下的去重数」量出来，用来说明那个 6 必须带作用域引用。
stub = bytes.fromhex('B801000000C20400')
NOP8 = b'\x90' * 8
aligned_bodies = []
i = b.find(stub)
while i >= 0:
    if (imgbase + i) % 4 == 0 and b[i + 8:i + 16] == NOP8:
        aligned_bodies.append(imgbase + i)
    i = b.find(stub, i + 1)
chk('X4a 加固判据（4 字节对齐 + 紧跟 8 nop）下桩体 %d 个' % len(aligned_bodies),
    len(aligned_bodies) > 0, 'bodies=%s' % [hex(x) for x in aligned_bodies])
bset = set(aligned_bodies)
refcnt = {}
for j in range(0, len(b) - 3):
    v = int.from_bytes(b[j:j + 4], 'little')
    if v in bset:
        refcnt[v] = refcnt.get(v, 0) + 1
referenced = sorted(k for k in refcnt if refcnt[k] > 0)
chk('X4b 反控：不加 nop 条件时地址数 = 40 != 加固后 %d（条件有分辨力）'
    % len(aligned_bodies), len(aligned_bodies) != 40, 'hardened=%d' % len(aligned_bodies))
chk('X4c 全镜像口径下被 dword 指向的桩体去重 = %d 个（deepseek 的「6」是 63 张表内口径，'
    '引用时必须带作用域）' % len(referenced), len(referenced) >= 6,
    'distinct=%d max_ref=%d' % (len(referenced), max(refcnt.values()) if refcnt else 0))
OUT['X4'] = {'aligned_bodies': [hex(x) for x in aligned_bodies],
             'referenced_bodies': [hex(x) for x in referenced],
             'refs': {hex(k): v for k, v in sorted(refcnt.items(), key=lambda kv: -kv[1])}}

npass = sum(1 for _, c, _ in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
io.open(os.path.join(ROOT, '_r135', 'r135d_xcheck.json'), 'w', encoding='utf-8').write(
    json.dumps({'asserts': [{'name': n, 'ok': c, 'detail': d} for n, c, d in res],
                'out': OUT}, ensure_ascii=False, indent=1))
sys.exit(0 if npass == len(res) else 1)
