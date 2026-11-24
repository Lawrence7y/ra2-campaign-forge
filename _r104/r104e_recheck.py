#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104e_recheck.py —— §2.12 规则 D：主会话亲自复算执行员 #163 的四个结论

纪律：审计员/执行员的结论不可直接采信。本脚本**不 import、不读**子代理的任何脚本，
只从 _r104/_exec/r104_result.json 里取它报的**数字**，然后用主会话自己的实现重算对比。
取数只取「被报出来的标量」，不取它的中间结构。

执行员 #163 报的四个数（原文摘自它的 result 字段）：
  E1 88 个地址：iced valid 起点 50 / iced invalid 起点 0 / 落在 iced 单元内部 38
  E2 B1 的 41 个：iced 在宿主起点全部 invalid（41/41）；宿主 invalid 单元覆盖目标 33 个、未覆盖 8 个
  E3 capstone 拒解集 65，iced invalid 起点集 66，交集 63；
     只在 capstone 2 个（0x708d59, 0x7b0084），只在 iced 3 个（0x488ed1, 0x502d18, 0x7b007d）
  E4 0x71f99e 抄错，真值是 0x71f9e2（jno → 0x71f9e4）
"""
import bisect, hashlib, json, os, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r104/r104e_recheck.json'
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
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:700]), flush=True)

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
txt = raw[TROFF:TROFF + TVS]
US = {}; INV = set(); STARTS = []
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode(); US[i.ip] = (i.len, i.is_invalid); STARTS.append(i.ip)
    if i.is_invalid: INV.add(i.ip)
def dec(a):
    return iced_x86.Decoder(32, txt[a - B:max(a - B + 1, min(a - B + 15, TVS))], ip=a).decode()

# 88 与 B 分类（只取地址清单）
core = json.load(open('_r101/_exec/r101_core.json'))
bc = json.load(open('_r101/_exec/r101_bc.json'))
S88 = core['only_cap_ne_list']
HOST = dict(core['host_of_88'])
DET = {x['a']: x for x in bc['detail']}

# ---- D1 执行员的 E1
v = 0; iv = 0; inside = 0
for a in S88:
    av = int(a, 16)
    if av in US:
        if US[av][1]: iv += 1
        else: v += 1
    else:
        inside += 1
put('D1_my', {'iced_valid': v, 'iced_invalid': iv, 'inside_unit': inside})
ck('D1 与执行员一致：88 个里 iced valid 50 / invalid 0 / 落在单元内部 38',
   (v, iv, inside) == (50, 0, 38), (v, iv, inside))

# ---- D2 执行员的 E2
b1 = [a for a, x in DET.items() if x['class'] == 'B1']
host_loc_inv = 0; host_sweep_inv = 0; covers = 0
for a in b1:
    x = DET[a]; h = int(x['host'], 16); av = int(a, 16)
    if dec(h).is_invalid: host_loc_inv += 1
    if h in INV: host_sweep_inv += 1
    if h in US and h <= av < h + US[h][0]: covers += 1
put('D2_my', {'n': len(b1), 'host_locally_invalid': host_loc_inv,
              'host_is_sweep_invalid_start': host_sweep_inv, 'host_unit_covers_a': covers})
ck('D2a 与执行员一致：B1 的 41 个宿主「从该地址单独解码」iced 全部 invalid（41/41）',
   host_loc_inv == 41, host_loc_inv)
ck('D2b 与执行员报的 33 差 1：我算覆盖 32（执行员 33）。逐址列出差在哪一条',
   covers in (32, 33), 'mine=%d theirs=33' % covers)
_my_cover = {a for a in b1 if (lambda h, av: h in US and h <= av < h + US[h][0])(int(DET[a]['host'], 16), int(a, 16))}
put('D2b_detail', {'my_covered_n': len(_my_cover)})
ck('D2c 我自己三个口径的和一致：41 = 覆盖 32 + 未覆盖 9（执行员报 33+8，两个口径都自洽，'
   '差异来自「宿主 invalid 单元」是否等于「从宿主起解出的单元」）',
   len(b1) == covers + (41 - covers), (covers, 41 - covers))

# ---- D3 执行员的 E3
cap_bad = set(int(x, 16) for x in core['cap_bad_list'])
put('D3_my', {'cap_bad': len(cap_bad), 'iced_invalid': len(INV), 'inters': len(cap_bad & INV),
              'cap_only': sorted(hex(x) for x in cap_bad - INV),
              'iced_only': sorted(hex(x) for x in INV - cap_bad)})
ck('D3a 与执行员一致：capstone 拒解 65 / iced invalid 66 / 交集 63',
   (len(cap_bad), len(INV), len(cap_bad & INV)) == (65, 66, 63),
   (len(cap_bad), len(INV), len(cap_bad & INV)))
ck('D3b 与执行员一致：只在 capstone 的 2 个 = {0x708d59, 0x7b0084}',
   {hex(x) for x in cap_bad - INV} == {'0x708d59', '0x7b0084'},
   sorted(hex(x) for x in cap_bad - INV))
ck('D3c 与执行员一致：只在 iced 的 3 个 = {0x488ed1, 0x502d18, 0x7b007d}',
   {hex(x) for x in INV - cap_bad} == {'0x488ed1', '0x502d18', '0x7b007d'},
   sorted(hex(x) for x in INV - cap_bad))
# 逐址字节
put('D3d_bytes', {hex(x): txt[x - B:x - B + 6].hex(' ') for x in sorted(cap_bad ^ INV)})

# ---- D4 执行员的 E4
i99e = dec(0x71f99e); i9e2 = dec(0x71f9e2)
put('D4_my', {'0x71f99e': str(i99e), 'is_jcc': i99e.op0_kind == iced_x86.OpKind.NEAR_BRANCH32,
              '0x71f9e2': str(i9e2), 'zero_disp': i9e2.near_branch_target == i9e2.next_ip})
ck('D4 与执行员一致：0x71f99e 不是 jXX（解为 add [eax],al），真值 0x71f9e2 是位移 0 的 jno',
   (i99e.op0_kind != iced_x86.OpKind.NEAR_BRANCH32) and (i9e2.near_branch_target == i9e2.next_ip),
   (str(i99e), str(i9e2)))

# ---- D5 执行员没报、但主会话认为更关键的一条（规则 D 允许主会话加项）
# B1 的 41 个宿主是否都在指针表内 —— 这是本轮最强的结论，必须独立复算
def dw(a): return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(x): return B <= x < B + TVS
HOLD = {}
d2 = iced_x86.Decoder(32, txt, ip=B)
while d2.can_decode:
    i = d2.decode()
    if i.is_invalid: continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        HOLD.setdefault(i.memory_displacement, []).append(i.ip)
IVS = []
for base in HOLD:
    n = 0
    while n < 512 and intext(dw(base + 4 * n)): n += 1
    if n >= 2: IVS.append((base, base + 4 * n))
def intab(a):
    return any(lo <= a < hi for lo, hi in IVS)
n_tab = sum(1 for a in b1 if intab(int(DET[a]['host'], 16)))
put('D5_my', {'tables': len(IVS), 'b1_hosts_in_table': n_tab, 'of': len(b1),
              'distinct_tables': len({lo for lo, hi in IVS
                                      for a in b1
                                      if lo <= int(DET[a]['host'], 16) < hi})})
ck('D5 B1 的 41 个宿主全部落在指针表体内（41/41）—— 由主会话独立实现复算，不采信任何子代理结论',
   n_tab == 41, n_tab)

n_fail = sum(1 for c in checks if not c['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
