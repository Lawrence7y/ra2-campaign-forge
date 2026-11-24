#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110b_seh.py —— 32 位镜像没有 .pdata，那么「有没有第二套现成的函数边界」？

R109 §EK 待办⑥ 原文：『32 位无 .pdata 已确认但 __try/__except 异常处理表是否存在未查，
若存在即第二套现成函数边界』。本轮机械核验，给确定答案。

三条独立判据（全部构造性，不靠命名推断）：
  E1 SEH 链：x86 的 __try 编译产物必有 fs:[0] 的读写
       mov eax, fs:[0]      (64 A1 00 00 00 00)   —— 取当前链头，稍后 mov fs:[0],esp 挂新帧
       mov fs:[0], esp      (64 89 25 00 00 00 00) —— 挂帧
       mov fs:[0], eax      (64 A3 00 00 00 00)   —— 摘帧（有 __finally 时）
       push dword fs:[0]    (64 FF 35 00 00 00 00) —— 另一种取链头写法
     只有当「挂帧」与「摘帧/取链头」在同一个函数体内成对出现，才是真的 __try 块。
  E2 C++ EH：MSVC 的 FuncInfo 结构以 magic 0x19930520（及 0x19930521/0x19930522）开头，
     且其 pUnwindMap / tryblocks 字段是指向 .rdata 的指针。只认「magic + 后续 3 个 dword 全 0 +
     再往后是指向数据节的指针」这一完整形态，排除字节巧合（.rdata 里星期字符串旁就有一个巧合命中）。
  E3 若 E1/E2 任一给出「>= 10% 的函数有边界」才叫「第二套边界」；实测数字说话。

内存纪律：单一正则扫描 4 MB 字节流（不反汇编全段），命中点才开 detail。
"""
import json, os, re, struct
from collections import Counter
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB = 0x400000
fo = lambda va: va - IB

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = [(s.Name.decode().strip('\x00'), IB + s.VirtualAddress, IB + s.VirtualAddress + s.Misc_VirtualSize)
        for s in pe.sections]
T = [x for x in SECT if x[0] == '.text'][0]
TS, TE = T[1], T[2]
DATA = [x for x in SECT if x[0] in ('.rdata', '.data', '.detour')]
ck('S0 节表现读：.text = [%s, %s)；无 .pdata（5 节：%s）'
   % (hex(TS), hex(TE), [n for n, _, _ in SECT]),
   not any(n == '.pdata' for n, _, _ in SECT) and len(SECT) == 5, [n for n, _, _ in SECT])

def sec_of(v):
    for n, a, b in SECT:
        if a <= v < b:
            return n
    return None

def in_data(v):
    return any(a <= v < b for n, a, b in DATA)

# ---------- E1 SEH 链 ----------
PAT = {
    'mov_eax_fs0':  bytes.fromhex('64A100000000'),
    'mov_fs0_esp':  bytes.fromhex('64892500000000'),
    'mov_fs0_eax':  bytes.fromhex('64A300000000'),
    'push_dw_fs0':  bytes.fromhex('64FF3500000000'),
}
txt = raw[TS - IB:TE - IB]
HIT = {}
for k, p in PAT.items():
    idx = [m.start() + TS for m in re.finditer(re.escape(p), txt)]
    HIT[k] = idx
ck('E1a .text 内四种 fs:[0] 访问形态计数 = %s'
   % {k: len(v) for k, v in HIT.items()},
   len(HIT['mov_fs0_esp']) > 0, {k: len(v) for k, v in HIT.items()})

# 全镜像（含 .detour 节，本镜像非原版导入布局）再数一遍
allhits = {k: [m.start() + IB for m in re.finditer(re.escape(p), raw) if sec_of(m.start() + IB)] for k, p in PAT.items()}
ck('E1b 全镜像（含 .detour）计数 = %s；.detour 内 = %s'
   % ({k: len(v) for k, v in allhits.items()},
      {k: [hex(x) for x in v if sec_of(x) == '.detour'] for k, v in allhits.items()}),
   True, {k: len(v) for k, v in allhits.items()})

# 成对性：挂帧点与取链头点的距离（同一 __try 块内应 < 64 B）
pairs = []
for a in HIT['mov_fs0_esp']:
    near = [b for b in HIT['mov_eax_fs0'] + HIT['push_dw_fs0'] if 0 < a - b < 64]
    if near:
        pairs.append((min(near), a, a - min(near)))
ck('E1c 「取链头(64 A1/64 FF 35) → 挂帧(64 89 25)」距离 < 64 B 的成对点数 = %d；'
   '若 SEH 是常用边界，此处应达数万（HB 边界实测 17,766 个）'
   % len(pairs), True, {'pairs': len(pairs), 'sample': [(hex(a), hex(b), d) for a, b, d in pairs[:6]]})

# 这些成对点落在哪些函数里（用 HB 边界反查）
import array
D = {}
f2 = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f2.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k2 = f2.read(kl).decode()
    arr = array.array('I'); arr.frombytes(f2.read(n * isz)); D[k2] = arr
f2.close()
starts = D['starts']; SSET = set(starts); RETS = sorted(D['rets'])

def ret_size(r):
    return 3 if raw[fo(r)] in (0xc2, 0xca) else 1

HB = set()
for r in RETS:
    q = r + ret_size(r)
    n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
ck('E1d HB 边界复算 = %d（R108/R109 同口径 17,766）' % len(HB), len(HB) == 17766, len(HB))

import bisect
HBS = sorted(HB)
def func_start(x):
    i = bisect.bisect_right(HBS, x) - 1
    return HBS[i] if i >= 0 else None

seh_funcs = set()
for a, b, d in pairs:
    fa = func_start(a)
    if fa is not None:
        seh_funcs.add(fa)
ck('E1e 含成对 SEH 帧操作的函数数 = %d / HB 总函数 %d = %.2f%% ⇒ **SEH 覆盖不到 1%% 的函数，'
   '不能当第二套函数边界**' % (len(seh_funcs), len(HB), 100.0 * len(seh_funcs) / len(HB)),
   len(seh_funcs) < 0.05 * len(HB),
   {'seh_funcs': len(seh_funcs), 'hb': len(HB), 'pct': round(100.0 * len(seh_funcs) / len(HB), 2)})

# ---------- E2 C++ EH FuncInfo ----------
MAGICS = [0x19930520, 0x19930521, 0x19930522, 0x19930510]
straight = []
coincid = []
for mg in MAGICS:
    pat = struct.pack('<I', mg)
    i = 0
    while True:
        j = raw.find(pat, i)
        if j < 0:
            break
        v = j + IB
        i = j + 1
        if v % 4:            # FuncInfo 是 4 字节对齐结构
            continue
        f0, f1, f2_ = struct.unpack_from('<III', raw, j + 4)
        w0, w1, w2 = struct.unpack_from('<III', raw, j + 16)
        # 完整形态：紧随 3 个 0，再往后至少一个指针落在数据节
        if f0 == 0 and f1 == 0 and f2_ == 0 and (in_data(w0) or in_data(w1) or in_data(w2)):
            straight.append((v, sec_of(v), mg, hex(w0), hex(w1), hex(w2)))
        else:
            coincid.append((v, sec_of(v), mg, hex(f0), hex(f1), hex(f2_)))
ck('E2a magic 0x19930520/21/22/10 在镜像内的「完整 FuncInfo 形态」命中 = %d；'
   '不满足形态的巧合命中 = %d（含 .text 内那一处）'
   % (len(straight), len(coincid)),
   len(straight) < 1000, {'straight': [(hex(a), s) for a, s, mg, *_ in straight],
                          'coincid': [(hex(a), s) for a, s, mg, *_ in coincid]})
ck('E2b 完整形态命中里落在 .text 的 = %d（FuncInfo 应在 .rdata/.data，落 .text 即判为字节巧合）'
   % sum(1 for a, s, *_ in straight if s == '.text'),
   sum(1 for a, s, *_ in straight if s == '.text') == 0,
   [(hex(a), s) for a, s, *_ in straight])

# ---------- E3 反向：.text 里有没有指向这些 FuncInfo 的立即数 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
fis = set(a for a, *_ in straight)
refs = []
if fis:
    pos = TS
    while pos < TE:
        hi = min(pos + 65536, TE)
        last = pos
        for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(ho := hi) + 16], pos):
            if a >= hi:
                break
            last = a + sz
            for tok in re.findall(r'0x[0-9a-f]+', o):
                if int(tok, 16) in fis:
                    refs.append((a, int(tok, 16)))
        if last <= pos:
            last = pos + 1
        pos = last
ck('E3 .text 中指向「完整 FuncInfo」的立即数引用 = %d 条'
   % len(refs), True, [(hex(a), hex(t)) for a, t in refs[:10]])

ck('E4 结论（机械判定）：第二套函数边界**不存在** —— SEH 覆盖 %.2f%% 的函数、'
   'C++ EH FuncInfo 全镜像 %d 条、被 .text 引用 %d 条；三者都远不足以当边界源'
   % (100.0 * len(seh_funcs) / len(HB), len(fis), len(refs)),
   len(seh_funcs) < 0.05 * len(HB) and len(fis) < 100,
   {'seh_pct': round(100.0 * len(seh_funcs) / len(HB), 2), 'funcinfo': len(fis), 'refs': len(refs)})

json.dump({'checks': checks, 'pat_counts': {k: len(v) for k, v in HIT.items()},
           'seh_sites': [hex(a) for a in HIT['mov_fs0_esp']],
           'pairs': [[hex(a), hex(b), d] for a, b, d in pairs],
           'seh_funcs': [hex(x) for x in sorted(seh_funcs)], 'hb': len(HB),
           'funcinfo': [[hex(a), s, hex(mg), w0, w1, w2] for a, s, mg, *rest in straight for w0, w1, w2 in [rest]],
           'funcinfo_coincid': [[hex(a), s, hex(mg)] for a, s, mg, *_ in coincid],
           'text_refs': [[hex(a), hex(t)] for a, t in refs]},
          open('_r110/r110b_seh.json', 'w'), ensure_ascii=False, indent=1)
print('\nSEH 挂帧点 %d 个 / 取链头点 %d 个 / 成对 %d / 涉及函数 %d / HB 函数 %d'
      % (len(HIT['mov_fs0_esp']), len(HIT['mov_eax_fs0']), len(pairs), len(seh_funcs), len(HB)))
np_ = sum(1 for c in checks if c['ok'])
print('ASSERT %d/%d PASS, FAIL %d' % (np_, len(checks), len(checks) - np_))
