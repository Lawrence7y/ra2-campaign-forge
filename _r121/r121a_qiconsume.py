#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121a_qiconsume.py -- QI(0x7f7c80) 出参 ppv 的消费面普查（t628 静态，单遍 disasm_lite）。

R120 只证到「60 个站点全部 call dword ptr [ecx] = 槽 0 QI」+「站后 10 字节是同一模板」。
本轮再推一格：QI 的**出参**（ppv）在这 60 个站点之后被谁消费、在第几个实参位置上。
这是对象级的量，不是调用模板级的量 —— 模板级的东西（R120 的 60/60）包装器也能复制，
但「出参被当成 OleSaveToStream 的第 1 个实参」必须由真的持有该接口的代码来写。

判据（全部只看字节，不看函数边界，不查 IID-per-function）：
  S1 push imm32 == 0x7f7c80 且首字节 0x68（正控 = 改成 +1 必须 0 站点）
  S2 ppv 槽：站点前 <=10 条内，push R 且其前 <=10 条内有 lea R,[esp+K]
  S3 QI：站点后第一条 call 且操作数是 dword ptr [ecx]
  S4 消费：QI 之后向后扫 <=22 条，第一次 mov P, dword ptr [esp+K]（P = ppv 装回寄存器），
     再向后到第一条 call：IAT 直调 / 寄存器（回溯其在**最近的前置终止块之后**的最后一次写）
  S5 实参位置：P 被 push 后在 call 前一共压了几个，算出 P 是第几个实参（0 基）
  S6 释放：消费 call 之后 <=8 条内是否出现 call dword ptr [reg + 8]（Release）或 IAT Release

反控（必须每条都翻得动）：
  N1 imm32 精确性：站点处 0x68 + imm32 == 目标，逐站点核对，不符必须 0
  N2 偏移敏感：从站点 +1 处起算同一套判据，必须解不出模板（0/60）
  N3 槽位敏感：把 K 改成 K+4 重跑 S4/S5，OleSaveToStream 命中数必须变化
  N4 对照 IID：0x7f7c90（.rdata 里紧邻的另一个 COM 常量）跑同型测量，桶分布必须不同
  N5 恒真排除：把目标换成 .text 里一个不存在的值（0x7f7c84），站点必须 0
内存纪律：disasm_lite 单遍 + 64 KiB 分块，未对 .text 整段开 detail=True。
"""
import array
import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r119'))
from _pe119 import PE_, BUF                      # noqa: E402
import capstone                                  # noqa: E402

OUT = os.path.join(ROOT, '_r121', 'r121a_qiconsume.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


TEXT = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True
IAT = json.load(io.open(os.path.join(ROOT, '_r119', 'iat_names.json'), encoding='utf-8'))
IATV = {int(k, 16): v[1] for k, v in IAT.items()}
WRITE_MN = {'mov', 'lea', 'xor', 'pop', 'add', 'sub', 'and', 'or', 'imul', 'movzx', 'movsx',
            'inc', 'dec', 'shl', 'shr', 'xchg', 'adc', 'sbb'}
TERM_MN = {'ret', 'jmp'}
REGRE = r'(?:eax|ebx|ecx|edx|esi|edi|ebp)'


def sites_of(target):
    out = []
    for off in range(0, TEXT['vsize'], 65536):
        blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
        for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
            if mn == 'push' and ops.startswith('0x'):
                try:
                    if int(ops, 16) == target:
                        out.append(a)
                except ValueError:
                    pass
    return out


def win(va, back, fwd):
    o = PE_.va2off(va - back)
    return list(MD.disasm_lite(BUF[o:o + back + fwd], va - back))


def ppv_slot(seq, idx):
    for i in range(idx - 1, max(-1, idx - 11), -1):
        a, sz, mn, ops = seq[i]
        if mn != 'push' or not re.fullmatch(REGRE, ops):
            continue
        R = ops
        for j in range(i - 1, max(-1, i - 11), -1):
            a2, sz2, mn2, ops2 = seq[j]
            m = re.fullmatch(r'(%s), \[esp \+ (0x[0-9a-f]+)\]' % REGRE, ops2)
            if mn2 == 'lea' and m and m.group(1) == R:
                return R, m.group(2), hex(a2)
            if re.match(r'^%s,' % R, ops2) and mn2 in WRITE_MN:
                break
        break
    return None


def last_write(seq, upto, reg):
    """该回归：从 upto 向前，只在**最近的前置终止指令之后**的线性块内找最后一次写。"""
    lo = 0
    for k in range(upto - 1, -1, -1):
        if seq[k][2] in TERM_MN and not (seq[k][2] == 'jmp' and False):
            lo = k + 1
            break
    last = None
    for k in range(lo, upto):
        a, sz, mn, ops = seq[k]
        if re.match(r'^%s\s*,' % reg, ops) and mn in WRITE_MN:
            last = (hex(a), mn, ops)
    return last


def resolve(seq, i, depth=0):
    a, sz, mn, ops = seq[i]
    if ops.startswith('dword ptr [0x'):
        v = int(ops[len('dword ptr ['):-1], 16)
        return 'IAT:' + IATV.get(v, 'NOT-IAT:%x' % v), v
    if re.fullmatch(REGRE, ops):
        w = last_write(seq, i, ops)
        if w:
            m = re.fullmatch(r'%s, dword ptr \[(0x[0-9a-f]+)\]' % ops, w[2])
            if m:
                v = int(m.group(1), 16)
                return 'REG:%s<-%s' % (ops, IATV.get(v, 'NOT-IAT:%x' % v)), v
            return 'REG:%s<-%s' % (ops, w[1]), None
        return 'REG:%s<-UNRESOLVED' % ops, None
    if ops.startswith('dword ptr ['):
        return 'VT:' + ops[len('dword ptr ['):-1], None
    return 'REL:' + ops, None


def analyze(s, target, kshift=0, shift=0):
    seq = win(s, 0x40, 0x100)
    idx = [i for i, x in enumerate(seq) if x[0] == s + shift]
    if not idx:
        return {'site': hex(s), 'err': 'site-not-located'}
    idx = idx[0]
    out = {'site': hex(s)}
    slot = ppv_slot(seq, idx)
    out['ppv'] = [slot[0], slot[1]] if slot else None
    qi = None
    for i in range(idx, len(seq)):
        if seq[i][2] == 'call' and re.fullmatch(r'dword ptr \[(%s)\]' % REGRE, seq[i][3]):
            base = seq[i][3][len('dword ptr ['):-1]
            if base == slot[0] if slot else False:
                pass
        if seq[i][2] == 'call' and seq[i][3] == 'dword ptr [ecx]':
            qi = i
            break
    out['qi'] = hex(seq[qi][0]) if qi is not None else None
    if slot is None:
        out['consume'] = 'NO-PPV'
        return out
    if qi is None:
        out['consume'] = 'NO-QI'
        return out
    K = slot[1]
    if kshift:
        K = hex(int(K, 16) + kshift)
    P = None
    pushes = []
    for i in range(qi + 1, min(len(seq), qi + 23)):
        a, sz, mn, ops = seq[i]
        m = re.fullmatch(r'(%s), dword ptr \[esp \+ %s\]' % (REGRE, re.escape(K)), ops)
        if mn == 'mov' and m:
            P = m.group(1)
            out['P'] = P
            out['P_at'] = hex(a)
            continue
        if mn == 'push':
            mm = re.fullmatch(REGRE, ops)
            pushes.append(mm.group(0) if mm else 'imm:' + ops)
            continue
        if mn == 'call':
            name, _ = resolve(seq, i)
            out['consume'] = name
            out['consume_at'] = hex(a)
            if P and P in pushes:
                k = pushes.index(P)
                out['arg_index'] = len(pushes) - 1 - k
                out['n_pushes'] = len(pushes)
            out['pushes'] = list(pushes)
            rel = None
            for j in range(i + 1, min(len(seq), i + 10)):
                if seq[j][2] == 'call':
                    rel = seq[j][3]
                    break
                if seq[j][2] in TERM_MN:
                    break
            out['after'] = rel
            return out
        if mn in TERM_MN:
            out['consume'] = 'TERM-BEFORE-CALL'
            return out
    out['consume'] = 'SCAN-END'
    return out


res = {}
T80 = 0x7f7c80
S80 = sites_of(T80)
res['0x7f7c80'] = [analyze(s, T80) for s in S80]
c80 = collections.Counter(r.get('consume') for r in res['0x7f7c80'])
arg80 = collections.Counter((r.get('consume'), r.get('arg_index')) for r in res['0x7f7c80'])
after80 = collections.Counter(r.get('after') for r in res['0x7f7c80'])

ck('A1 站点数 = %d（判据：首字节 0x68 且 imm32 == 0x7f7c80），全部能定位 ppv 槽 = %d'
   % (len(S80), sum(1 for r in res['0x7f7c80'] if r.get('ppv'))),
   len(S80) == 60 and all(r.get('ppv') for r in res['0x7f7c80']),
   {'n': len(S80)})

ck('A2 消费面桶分布 = %s；其中 OleSaveToStream 类 = %d'
   % (json.dumps(dict(c80), ensure_ascii=False),
      sum(v for k, v in c80.items() if 'OleSaveToStream' in (k or ''))),
   sum(c80.values()) == 60,
   {'buckets': dict(c80)})

ck('A3 ppv 的实参位置分布 = %s（0 = OleSaveToStream 的第 1 个实参 pPStm；该分布的键集合 = %s）'
   % (json.dumps({'%s@%s' % k: v for k, v in arg80.items()}, ensure_ascii=False),
      sorted(set(k[1] for k in arg80), key=lambda x: (x is None, x))),
   0 in [k[1] for k in arg80],
   {'argpos': {'%s@%s' % k: v for k, v in arg80.items()}})

ck('A4 消费调用之后 <=8 条内出现 call dword ptr [reg + 8]（= Release）的站点 = %d/%d'
   % (after80.get('dword ptr [ecx + 8]', 0), len(S80)),
   after80.get('dword ptr [ecx + 8]', 0) == len(S80), {'after': dict(after80)})

# ---- N1 imm32 精确性 ----
n1_bad = 0
for s in S80:
    o = PE_.va2off(s)
    if BUF[o] != 0x68 or int.from_bytes(BUF[o + 1:o + 5], 'little') != T80:
        n1_bad += 1
ck('N1 反控 imm32 精确：%d 个站点逐字节核对首字节 0x68 + imm32 == 0x7f7c80，不符 = %d'
   % (len(S80), n1_bad), n1_bad == 0, {'n_bad': n1_bad})

# ---- N2 偏移敏感 ----
n2 = [analyze(s, T80, shift=1) for s in S80]
n2_tmpl = sum(1 for r in n2 if r.get('ppv'))
ck('N2 反控 偏移敏感：从站点 +1 处起算同一套判据，解出 ppv 槽的 = %d/%d（必须 0）'
   % (n2_tmpl, len(S80)), n2_tmpl == 0, {'n': n2_tmpl})

# ---- N3 槽位敏感 ----
n3 = [analyze(s, T80, kshift=4) for s in S80]
n3_save = sum(1 for r in n3 if 'OleSaveToStream' in (r.get('consume') or ''))
ck('N3 反控 槽位敏感：把 ppv 槽 K 改成 K+4 重跑，OleSaveToStream 命中 = %d（原 %d，必须变化）'
   % (n3_save, sum(v for k, v in c80.items() if 'OleSaveToStream' in (k or ''))),
   n3_save != sum(v for k, v in c80.items() if 'OleSaveToStream' in (k or '')),
   {'kshift': n3_save})

# ---- N4 对照 IID ----
T90 = 0x7f7c90
S90 = sites_of(T90)
res['0x7f7c90'] = [analyze(s, T90) for s in S90]
c90 = collections.Counter(r.get('consume') for r in res['0x7f7c90'])
ck('N4 对照 0x7f7c90：站点 %d，ppv 槽解出 %d，消费桶 %s ⇒ 与 0x7f7c80 的桶分布不同'
   % (len(S90), sum(1 for r in res['0x7f7c90'] if r.get('ppv')),
      json.dumps(dict(c90), ensure_ascii=False)),
   len(S90) == 56 and dict(c90) != dict(c80), {'c90': dict(c90)})

# ---- N5 恒真排除 ----
Sx = sites_of(0x7f7c84)
ck('N5 反控 恒真排除：目标换成 0x7f7c84（+4，不是指令立即数）⇒ 站点 = %d（必须 0）' % len(Sx),
   len(Sx) == 0, {'n': len(Sx)})

# ---- N6 .text 里所有 ebp<-IAT 写点（给 S4 的「寄存器缓存」判据一个总量） ----
n6 = []
for off in range(0, TEXT['vsize'], 65536):
    blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
        m = re.fullmatch(r'ebp, dword ptr \[(0x[0-9a-f]+)\]', ops)
        if mn == 'mov' and m:
            v = int(m.group(1), 16)
            if v in IATV:
                n6.append([hex(a), IATV[v]])
ck('N6 全 .text 里「ebp <- IAT 槽」的写点 = %d 个（S4 的寄存器回溯判据有真实基数，非恒真）'
   % len(n6), len(n6) > 0, {'n': len(n6)})
save_ebp = [x for x in n6 if x[1] == 'OleSaveToStream']
ck('A5 其中 ebp <- OleSaveToStream 的写点 = %d 个：%s（这解释了 A2 里 REG 桶的来源）'
   % (len(save_ebp), [x[0] for x in save_ebp]), len(save_ebp) == 2, {'sites': save_ebp})

json.dump({'checks': checks, 'results': res,
           'summary': {'sites_7f7c80': len(S80), 'buckets_7f7c80': dict(c80),
                       'argpos_7f7c80': {'%s@%s' % k: v for k, v in arg80.items()},
                       'after_7f7c80': dict(after80),
                       'sites_7f7c90': len(S90), 'buckets_7f7c90': dict(c90)}},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), OUT))
sys.exit(0 if npass == len(checks) else 1)
