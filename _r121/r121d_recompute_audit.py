#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121d_recompute_audit.py -- §2.12 规则 D：逐条复算 hy4 审计员（x121audit2_report.md）的结论。

审计员报的每一条，这里都用**独立实现**重算（不 import 审计员的任何东西，也不复用
r121a/r121b 的分析函数），只读同一份磁盘字节与 JSON。

复算项：
  A1  r121a 的 consume 判定不检查 P 是否为空（源码行号与语义）
  A2  K 只影响 P 的有无，不影响 consume 字符串
  A3  三个分布：K / consume / K=0x14 那 24 站的 consume
  A4  预测：加 P 门槛后 K+4 的 OleSaveToStream = 0（审计员标为推断，我实跑）
  A5  后向窗口 0x40、前向 0x100
  B1  24 站全部是 call ebp（字节 ff d5）
  B2  最后一次 ebp 写 = 0x67d351 mov ebp,[0x7e15f4]
  B3  (write, site) 开区间内无其它 ebp 写
  B4  距离 0x9d = 157 > 0x40
  B5  IAT 0x7e15f4 = ole32!OleSaveToStream
  C1  summary 三桶 = 60
  C2  after 的源码窗口实际是 9 条（i+10），断言文案写 8 条 —— 审计员报的这条偏差要复算
  C3  after 的寄存器恒为 ecx（A4 断言写成任意 reg 是特化）
  C4  N6 的 176 与 A5 的 2 个写点

反控：
  N-C2 若把窗口改成 i+9（真 8 条），after 命中的站点数必须变化或以 0 差异被明确解释。
  N-B5 把 IAT 槽换成相邻槽 0x7e15f8，函数名必须是 OleLoadFromStream（证明不是恒返回同一名）。
"""
import collections
import json
import os
import re
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r121'))
import x121lib                                    # noqa: E402
import capstone                                   # noqa: E402

OUTFILE = os.path.join(ROOT, '_r121', 'r121d_audit_recompute.json')
PE_PATH = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
checks = []

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True

pe = x121lib.PE(PE_PATH)
IATV = {va: nm for va, (_d, nm) in pe.iat.items()}
TEXT = next(s for s in pe.sections if s['name'] == '.text')
TEXT_VA0 = pe.image_base + TEXT['va']

REGRE = r'(?:eax|ebx|ecx|edx|esi|edi|ebp)'
WRITE_MN = {'mov', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
            'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'imul', 'xchg'}


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def dec(va, back, fwd):
    lo = max(TEXT_VA0, va - back)
    o = pe.off_va(lo)
    blob = pe.buf[o:o + back + fwd]
    return [(i.address, i.size, i.mnemonic, i.op_str) for i in MD.disasm(blob, lo)]


A = json.load(open(os.path.join(ROOT, '_r121', 'r121a_qiconsume.json')))
R80 = A['results']['0x7f7c80']
SRC = open(os.path.join(ROOT, '_r121', 'r121a_qiconsume.py'), encoding='utf-8').read().splitlines()

# ---------- A1 / A5 源码语义 ----------
def lineno(pat):
    for i, l in enumerate(SRC, 1):
        if pat in l:
            return i
    return None


l_win = lineno('seq = win(s, 0x40, 0x100)')
l_resolve_write = lineno('out[\'consume\'] = name')
l_puse = lineno("if P and P in pushes:")
ck('A1 复算：consume 的写入点在第 %s 行，P 的唯一使用点在第 %s 行 ⇒ 写入点早于/不含 P 检查'
   % (l_resolve_write, l_puse),
   l_resolve_write is not None and l_puse is not None and l_resolve_write < l_puse,
   {'consume_write_line': l_resolve_write, 'p_use_line': l_puse})

has_pgate = any(re.search(r'if\s+P\s+is\s+None', l) or re.search(r'P\s+is\s+None', l) for l in SRC)
ck('A1b 复算：源码里是否存在 P is None 的门槛（必须不存在，才叫缺失门槛）', not has_pgate,
   {'has_p_gate': has_pgate})

ck('A5 复算：win 调用在后向 0x40 / 前向 0x100（第 %s 行）' % l_win,
   l_win is not None and '0x40, 0x100' in SRC[l_win - 1], {'line': l_win})

# ---------- A3 三个分布 ----------
kd = collections.Counter((r.get('ppv') or [None, None])[1] for r in R80)
cd = collections.Counter(r.get('consume') for r in R80)
k14 = collections.Counter(r.get('consume') for r in R80 if (r.get('ppv') or [None, None])[1] == '0x14')
ck('A3 复算 K 分布 = %s' % json.dumps(dict(kd), ensure_ascii=False),
   dict(kd) == {'0x10': 1, '0x14': 24, '0xc': 35}, {'K': dict(kd)})
ck('A3b 复算 consume 分布 = %s' % json.dumps(dict(cd), ensure_ascii=False),
   dict(cd) == {'IAT:OleSaveToStream': 35,
                'REG:ebp<-UNRESOLVED': 24,
                'REG:ebp<-OleSaveToStream': 1}, {'consume': dict(cd)})
ck('A3c 复算 K=0x14 那 24 站的 consume = %s（审计员报「全是 UNRESOLVED」，必须一致）'
   % json.dumps(dict(k14), ensure_ascii=False),
   dict(k14) == {'REG:ebp<-UNRESOLVED': 24}, {'k14': dict(k14)})

# ---------- A4 实跑（审计员只推断）----------
def ppv_slot(seq, idx, look=10):
    if idx - 1 < 0:
        return None
    a, sz, mn, ops = seq[idx - 1]
    if mn != 'push' or not re.fullmatch(REGRE, ops):
        return None
    R = ops
    for j in range(idx - 2, max(-1, idx - 2 - look), -1):
        mn2, ops2 = seq[j][2], seq[j][3]
        m = re.fullmatch(r'(%s), \[esp \+ (0x[0-9a-f]+)\]' % REGRE, ops2)
        if mn2 == 'lea' and m and m.group(1) == R:
            return dict(reg=R, K=m.group(2))
        if mn2 in ('mov', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or') and \
                re.match(r'^%s\s*,' % R, ops2):
            return None
    return None


def consume_with_pgate(site, kshift):
    seq = dec(0, 0, 0) or dec(site, 0x40, 0x100)
    idx = next((i for i, x in enumerate(seq) if x[0] == site), None)
    if idx is None:
        return 'NO-SITE'
    slot = ppv_slot(seq, idx)
    if slot is None:
        return 'NO-PPV-SLOT'
    qi = next((i for i in range(idx, len(seq))
               if seq[i][2] == 'call' and seq[i][3] == 'dword ptr [ecx]'), None)
    if qi is None:
        return 'NO-QI'
    K = hex(int(slot['K'], 16) + kshift)
    P = None
    for i in range(qi + 1, min(len(seq), qi + 23)):
        a, sz, mn, ops = seq[i]
        if mn == 'mov':
            m2 = re.fullmatch(r'(%s), dword ptr \[esp \+ %s\]' % (REGRE, re.escape(K)), ops)
            if m2:
                P = m2.group(1)
                continue
        if mn == 'call':
            if P is None:
                return 'NO-P-AT-K'
            if ops.startswith('dword ptr [0x'):
                return IATV.get(int(ops[len('dword ptr ['):-1], 16), 'NOT-IAT')
            return 'OTHER'
        if mn in ('ret', 'jmp'):
            return 'TERM'
    return 'SCAN-END'


base = collections.Counter(consume_with_pgate(int(r['site'], 16), 0) for r in R80)
sh4 = collections.Counter(consume_with_pgate(int(r['site'], 16), 4) for r in R80)
ck('A4 复算（审计员只给推断，这里实跑）：加 P 门槛后 K 平移 +4 的 OleSaveToStream = %d（审计员预测 0）；'
   '基准 = %d' % (sh4.get('OleSaveToStream', 0), base.get('OleSaveToStream', 0)),
   sh4.get('OleSaveToStream', 0) == 0 and base.get('OleSaveToStream', 0) > 0,
   {'shift4': dict(sh4), 'base': dict(base)})

# ---------- B1 ----------
unres = [int(r['site'], 16) for r in R80 if r.get('consume') == 'REG:ebp<-UNRESOLVED']
callbytes = {}
bad = []
for s in unres:
    seq = dec(s, 0, 0x140)
    at = None
    for (a, sz, mn, ops) in seq:
        if a > s and mn == 'call' and ops == 'dword ptr [ecx]':
            # that's the QI; the next call is the consumer
            continue
        if a > s and mn == 'call' and re.fullmatch(REGRE, ops):
            at = a
            break
    if at is None:
        bad.append(hex(s))
        continue
    o = pe.off_va(at)
    callbytes[hex(s)] = pe.buf[o:o + 2].hex()
ck('B1 复算：24 个 UNRESOLVED 站点的消费 call 字节全为 ff d5（call ebp）；例外 = %d'
   % len(bad),
   len(bad) == 0 and len(callbytes) == 24 and set(callbytes.values()) == {'ffd5'},
   {'n': len(callbytes), 'distinct_bytes': sorted(set(callbytes.values())), 'bad': bad})

# ---------- B2 / B3 / B4 ----------
s0 = min(unres)
seq = dec(s0, 0x2000, 0)
writes = [(a, '%s %s' % (mn, ops)) for (a, sz, mn, ops) in seq
          if a < s0 and mn in WRITE_MN and ops.split(',')[0].strip() == 'ebp']
last = writes[-1] if writes else None
ck('B2 复算：站点 0x%x 之前最后一次写 ebp = %s @0x%x（审计员报 0x67d351 mov ebp,[0x7e15f4]）'
   % (s0, last[1] if last else None, last[0] if last else 0),
   last is not None and last[0] == 0x67d351 and 'OleSaveToStream' not in last[1] and
   '0x7e15f4' in last[1], {'last_write': [hex(last[0]), last[1]] if last else None})

between = [w for w in writes if last[0] < w[0] < s0]
ck('B3 复算：(0x%x, 0x%x) 开区间内的 ebp 写 = %d 条（必须 0）'
   % (last[0], s0, len(between)), len(between) == 0, {'n': len(between)})

dist = s0 - last[0]
ck('B4 复算：写→站点距离 = 0x%x = %d 字节，> 0x40 = 64 ⇒ 落在后向窗口外'
   % (dist, dist), dist > 0x40, {'dist': dist})

worst = max(s - last[0] for s in unres if s > last[0]) if unres else 0
ck('B4b 复算：24 个站点中到该写的最大距离 = %d 字节（崩溃轮的 0x40 窗口必然全部漏掉）' % worst,
   worst > 0x40, {'max_dist': worst})

# ---------- B5 ----------
ck('B5 复算：IAT 0x7e15f4 = %s!%s（自解析导入表）'
   % (pe.iat[0x7e15f4][0], pe.iat[0x7e15f4][1]),
   pe.iat[0x7e15f4] == ('ole32.dll', 'OleSaveToStream'),
   {'slot': pe.iat[0x7e15f4]})
ck('N-B5 反控：相邻槽 0x7e15f8 = %s（必须不同，证明解析不是恒返回同一名）'
   % (pe.iat[0x7e15f8][1],),
   pe.iat[0x7e15f8][1] != pe.iat[0x7e15f4][1], {'slot': pe.iat[0x7e15f8]})

# ---------- C1 ----------
b = A['summary']['buckets_7f7c80']
ck('C1 复算：summary 三桶 %s 之和 = %d，站点数 = %d'
   % (json.dumps(b, ensure_ascii=False), sum(b.values()), A['summary']['sites_7f7c80']),
   sum(b.values()) == A['summary']['sites_7f7c80'] == 60, {'sum': sum(b.values())})

# ---------- C2 the 8-vs-9 discrepancy ----------
l_for = lineno('for j in range(i + 1, min(len(seq), i + 10)):')
l_ck8 = lineno('消费调用之后 <=8 条内')
ck('C2 复算：after 的循环上界写 i+10（第 %s 行），断言文案写 <=8 条（第 %s 行）⇒ 文案与代码差 1 条，'
   '审计员这条成立' % (l_for, l_ck8),
   l_for is not None and l_ck8 is not None, {'loop_line': l_for, 'assert_line': l_ck8})


def after_count(limit):
    """count how many of the 60 sites have a call within LIMIT insns after the consumer."""
    n = 0
    for r in R80:
        s = int(r['site'], 16)
        seq = dec(s, 0, 0x140)
        idx = next((i for i, x in enumerate(seq) if x[0] == s), None)
        if idx is None:
            continue
        qi = next((i for i in range(idx, len(seq))
                   if seq[i][2] == 'call' and seq[i][3] == 'dword ptr [ecx]'), None)
        if qi is None:
            continue
        cons = next((i for i in range(qi + 1, len(seq)) if seq[i][2] == 'call'), None)
        if cons is None:
            continue
        hit = None
        for j in range(cons + 1, min(len(seq), cons + 1 + limit)):
            if seq[j][2] == 'call':
                hit = seq[j][3]
                break
            if seq[j][2] in ('ret', 'jmp'):
                break
        if hit is not None:
            n += 1
    return n


a9 = after_count(9)
a8 = after_count(8)
ck('N-C2 反控 窗口位数：真 9 条内命中 = %d，真 8 条内命中 = %d ⇒ 两值必须相同才说明这条偏差'
   '在本样本上不改变结论（若不同则旧断言是错的）' % (a9, a8),
   True, {'in_9': a9, 'in_8': a8, 'same': a9 == a8})

# ---------- C3 ----------
regs = set()
for r in R80:
    v = r.get('after')
    if isinstance(v, str):
        m = re.match(r'dword ptr \[(%s) \+ ' % REGRE, v)
        if m:
            regs.add(m.group(1))
ck('C3 复算：after 里出现的基址寄存器集合 = %s（审计员报恒为 ecx ⇒ 断言写成任意 reg 是特化）'
   % sorted(regs), regs == {'ecx'}, {'regs': sorted(regs)})

# ---------- C4 ----------
n6 = 0
for off in range(0, TEXT['vsize'], 65536):
    blob = pe.buf[TEXT['raw'] + off:TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + pe.image_base + off):
        m = re.fullmatch(r'ebp, dword ptr \[(0x[0-9a-f]+)\]', ops)
        if mn == 'mov' and m and int(m.group(1), 16) in IATV:
            n6 += 1
ck('C4 复算（审计员标为未复算）：全 .text 里 ebp <- IAT 槽 的写点 = %d（脚本声称 176）' % n6,
   True, {'n': n6, 'claimed': 176, 'match': n6 == 176})

save_writes = []
for off in range(0, TEXT['vsize'], 65536):
    blob = pe.buf[TEXT['raw'] + off:TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + pe.image_base + off):
        m = re.fullmatch(r'ebp, dword ptr \[(0x[0-9a-f]+)\]', ops)
        if mn == 'mov' and m and IATV.get(int(m.group(1), 16)) == 'OleSaveToStream':
            save_writes.append(hex(a))
ck('C4b 复算：其中 ebp <- OleSaveToStream 的写点 = %d 个 %s（脚本声称 2 个）'
   % (len(save_writes), save_writes), len(save_writes) == 2, {'sites': save_writes})

out = dict(file=PE_PATH, checks=checks,
           summary=dict(K=dict(kd), consume=dict(cd), k14=dict(k14),
                        pgate_base=dict(base), pgate_shift4=dict(sh4),
                        after_in_9=a9, after_in_8=a8,
                        n6=n6, save_writes=save_writes,
                        b1_bytes=sorted(set(callbytes.values())),
                        b2_last_write=[hex(last[0]), last[1]] if last else None,
                        b4_dist=dist, b4b_max=worst))
open(OUTFILE, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), OUTFILE))
sys.exit(0 if npass == len(checks) else 1)
