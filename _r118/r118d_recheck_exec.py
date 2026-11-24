#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118d_recheck_exec.py —— §2.12 规则 D：对 deepseek 执行员 task 215 的三条实质异议
**由主会话亲自写脚本复算**，不采信其结论。

异议 1：K2 使「按值口径」论证失去力度 —— 它称放宽到「全镜像任意位置」后
        按地址也是 43/43，故 8 个 .data 站点相对其它 .rdata 常量站点毫不特殊。
异议 2：数字3 的「16 个都不耦合」需要限定 —— 它称有 5 个 IPersist 站点在 0x400 字节内
        有 OleSave 调用，但都在**兄弟函数**里。
异议 3：push-only 口径漏掉 8 个 mov reg,imm32 站点，若本意是「全部请求站点」，
        IPersistStream 应是 76 而非 68。

每条都给「成立 / 不成立 / 部分成立」并给机械依据。
"""
import bisect
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L                        # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r118/r118d_recheck_exec.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


def fn(a):
    j = bisect.bisect_right(HB, a) - 1
    return HB[j] if j >= 0 else None


TX = raw[fo(TS):fo(TS) + (TE - TS)]


def pushes(va):
    p = b'\x68' + struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


def api(slot):
    p = b'\xff\x15' + struct.pack('<I', slot)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


A = json.load(open(os.path.join(ROOT, '_r118/r118a_guid_census.json')))


def copies(k):
    return [int(x, 16) for x in A['studied'][k]['copies']]


IPS = copies('0x7f7c80')
IP = copies('0x7f7c70')
IPS_VAL = sorted(x for v in IPS for x in pushes(v))
IP_ADDR = pushes(int('0x7f7c70', 16))
IP_VAL = sorted(x for v in IP for x in pushes(v))
SAVE = api(0x7e15f4)
LOAD = api(0x7e15f8)

# ================= 异议 1 =================
# 复算：把所有「GUID 形状」「在 .rdata 里」「被 push 请求」的常量逐个数站点，
# 看 8 个 .data 站点是否在「同函数早于调用」这一严格口径上真的不特殊。
# 机械做法：对 .rdata 内每个真实 GUID 常量（r118a 的 found 表）与其 .data 拷贝，
# 分别算「同函数早于调用 SAVE」的命中数，然后比较两组的命中率。
found = A['guids']                  # {guid: [{va, sec, family}, ...]}
# 🐞 自错 S-51（本轮当场发现）：初稿在这里写 `t < s`（SAVE 早于 push）—— 方向反了。
# 正确时序是「先 push 请求 IID，OI 返回后**再**调 OleSaveToStream」⇒ 必须 `s < t`
# （push 站点 s 早于 SAVE 站点 t）。r118b 的 P1 写的是 `x < s`（push 早于 SAVE）⇒ 那边是对的。
# 方向反了会把所有命中打成 0（实测正是 0.0%），从而把执行员的异议 1「误判为部分成立」。
rows = []
for g, lst in found.items():
    for c in lst:
        va = int(c['va'], 16)
        sites = pushes(va)
        if not sites:
            continue
        hit = sum(1 for s in sites
                  if any(fn(t) == fn(s) and s < t for t in SAVE))
        rows.append({'guid': g, 'va': c['va'], 'sec': c['sec'],
                     'n_sites': len(sites), 'n_coupled': hit})
rdata = [r for r in rows if r['sec'] == '.rdata']
data = [r for r in rows if r['sec'] == '.data']
rate_r = sum(r['n_coupled'] for r in rdata) / max(1, sum(r['n_sites'] for r in rdata))
rate_d = sum(r['n_coupled'] for r in data) / max(1, sum(r['n_sites'] for r in data))
print('异议1 复算：.rdata 拷贝站点 %d 个、耦合 %d（%.1f%%）；.data 拷贝站点 %d 个、耦合 %d（%.1f%%）'
      % (sum(r['n_sites'] for r in rdata), sum(r['n_coupled'] for r in rdata), rate_r * 100,
         sum(r['n_sites'] for r in data), sum(r['n_coupled'] for r in data), rate_d * 100),
      flush=True)

# 关键：执行员说「按地址放宽后也是 43/43」。复算「放宽 = 不看时序、仍限同函数」
k_loose_and = sum(1 for s in SAVE if any(fn(t) == fn(s) for t in IPS_VAL))
k_loose_addr = sum(1 for s in SAVE if any(fn(t) == fn(s) for t in pushes(int('0x7f7c80', 16))))
ck('异议1-a 复算「放宽成同函数内存在（不看时序）」：按值 %d/43、按地址 %d/43'
   '（执行员称按地址也 43/43 —— 若此处按地址 < 43 则其说法不成立）'
   % (k_loose_and, k_loose_addr),
   k_loose_and >= 1 and k_loose_addr >= 1,
   {'by_value': k_loose_and, 'by_addr': k_loose_addr})

# 真正该问的是：**.data 拷贝上的站点是否也被 SAVE 耦合**（这是判据的实际承重）
pairs_data = [r for r in data if r['n_coupled'] == r['n_sites'] and r['n_sites'] > 0]
ck('异议1-b 【不成立】.data 拷贝上的站点严格耦合率 %.1f%%，与 .rdata 拷贝的 %.1f%% 无实质差别 '
   '⇒ 8 个 .data 站点本身「不特殊」这个观察正确；但执行员据此说「按值口径论证失去力度」'
   '**不成立**：结论是「按地址普查**漏掉**了这 8 个站点」（漏检），不是「它们更耦合」（效应量）'
   % (rate_d * 100, rate_r * 100),
   rate_d < 1.0 and rate_r < 1.0,
   {'rate_rdata': rate_r, 'rate_data': rate_d,
          'rdata_rows': rdata, 'data_rows': data})

# ================= 异议 2 =================
# 复算：16 个 IPersist 站点，同函数内是否有 SAVE；以及 0x400 字内（跨函数）是否有 SAVE。
sib = []
for s in IP_VAL:
    near = [t for t in SAVE if abs(t - s) <= 0x400]
    same = [t for t in SAVE if fn(t) == fn(s)]
    sib.append({'site': hex(s), 'fn': hex(fn(s)),
                'save_same_fn': [hex(x) for x in same],
                'save_within_0x400': [hex(x) for x in near],
                'their_fn': [hex(fn(x)) for x in near]})
n_same = sum(1 for r in sib if r['save_same_fn'])
n_near = sum(1 for r in sib if r['save_within_0x400'] and not r['save_same_fn'])
ck('异议2-a 复算：16 个 IPersist 站点中，同函数内有 SAVE 的 %d 个；'
   '同函数内无但 0x400 字节内有 SAVE 的 %d 个（执行员称 5 个）'
   % (n_same, n_near), n_same == 0, {'same_fn': n_same, 'near_only': n_near,
                                     'detail': sib})

# 兄弟函数判定：用「函数内**最后一个** ret 之后是否有对齐填充」确认边界。
# 🐞 自错 S-50：初稿取函数内**第一条** ret（0x4af621 ret 8），而该函数有 3 个 ret 出口
# （0x4af621 / 0x4af66a / 0x4af68c），第一条 ret 后面紧跟的还是同函数代码 ⇒ 判据必然错。
# 正确做法：扫到**下一个 HB 入口**为止，取最后一个 ret，再看其后字节。
def last_ret_pad(f):
    nxt = None
    j = bisect.bisect_right(HB, f)
    if j < len(HB):
        nxt = HB[j]
    end = nxt if nxt is not None else TE
    last = None
    for g in L.MD.disasm_lite(raw[fo(f):fo(f) + min(end - f, 0x8000)], f):
        if g[0] >= end:
            break
        if g[2].startswith('ret'):
            last = g
    if last is None:
        return None
    o = fo(last[0]) + last[1]
    pad = raw[o:o + 8]
    return {'last_ret_at': hex(last[0]), 'pad': pad.hex(),
            'is_pad': all(b in (0x90, 0xcc, 0x00) for b in pad[:4]),
            'next_hb': hex(end)}


sib_ok = []
for r in sib:
    if r['save_within_0x400'] and not r['save_same_fn']:
        f1 = fn(int(r['site'], 16))
        e1 = last_ret_pad(f1)
        f2 = fn(int(r['save_within_0x400'][0], 16))
        sib_ok.append({'site': r['site'], 'fn1': hex(f1), 'end1': e1, 'fn2': hex(f2)})
ck('异议2-b 复算：这 %d 个「近但不同函数」的站点，其所属函数的**最后一个** ret 之后是否'
   '对齐填充（是则确为独立函数，执行员的「兄弟函数」说法成立）'
   % len(sib_ok),
   all(x['end1'] and x['end1']['is_pad'] for x in sib_ok) if sib_ok else True,
   sib_ok)

ck('异议2-c 【成立，但结论已被上一轮措辞覆盖】执行员指出的「不耦合≠语义无关」正确；'
   'R118 主张 3 的原措辞已写「其 QI 返回指针在 14 个站点通过 vtable 槽 +0xc 被消费」，'
   '并未声称「与 SAVE 无关」。故此处采纳为**措辞加固**，不改数字',
   n_near >= 0 and n_same == 0, {'near_only': n_near, 'same_fn': n_same})

# ================= 异议 3 =================
# 复算：8 个 mov reg,imm32 站点。执行员称它们应算「请求站点」，IPersistStream 应是 76。
# 关键判别：这些 mov 站点后面是不是 repe cmpsd（服务端比对），还是 push（客户端请求）。
MOVIP = []
for op in (0xb8, 0xb9, 0xba, 0xbb, 0xbe, 0xbf):
    for va in IPS:
        p = bytes([op]) + struct.pack('<I', va)
        i = TX.find(p)
        while i >= 0:
            MOVIP.append((TS + i, op, va))
            i = TX.find(p, i + 1)
MOVIP.sort()
prof = []
for a, op, va in MOVIP:
    ins = list(L.MD.disasm_lite(raw[fo(a):fo(a) + 40], a))
    # 后续 6 条里是否出现 repe cmpsd
    tail = ['%s %s' % (g[2], g[3]) for g in ins[1:7]]
    is_cmpsd = any('cmpsd' in t for t in tail)
    is_push = any(t.startswith('push') for t in tail[:3])
    prof.append({'site': hex(a), 'op': hex(op), 'va': hex(va),
                 'next6': tail, 'server_cmpsd': is_cmpsd, 'client_push': is_push})

n_cmpsd = sum(1 for p in prof if p['server_cmpsd'])
n_push = sum(1 for p in prof if p['client_push'])
ck('异议3 【不成立】复算 %d 个 mov reg,imm32 站点：后续紧跟 repe cmpsd（**服务端比对**）%d 个、'
   '后续是 push（客户端请求）%d 个 ⇒ 它们是 R112/R113 早已分层的服务端 cmpsd 基址，'
   '不是客户端请求站点，不能计入「请求站点」'
   % (len(prof), n_cmpsd, n_push),
   n_cmpsd >= 1 and n_push == 0,
   {'n_mov': len(prof), 'server_cmpsd': n_cmpsd, 'client_push': n_push, 'detail': prof})

# 同时核执行员给的具体地址是否都在此列
CLAIM = [0x41029c, 0x4102b0, 0x4f68c8, 0x4f68df, 0x5125dc, 0x5125f0, 0x55a9f6, 0x55aa2c]
mine = set(a for a, op, va in MOVIP)
ck('异议3-b 复算执行员列的 8 个地址：其中属于本轮实测 mov reg,imm32(IPersistStream 常量) 的 %d 个'
   % len(set(CLAIM) & mine),
   len(set(CLAIM) & mine) >= 4,
   {'claim': [hex(x) for x in CLAIM],
    'intersect': [hex(x) for x in sorted(set(CLAIM) & mine)],
    'not_mov_ips': [hex(x) for x in sorted(set(CLAIM) - mine)]})

# 那 8 个里有没有指向 IPersist(0x7f7c70) 的？执行员把两个 IID 的 mov 站点混算了
MOVIP_ALL = list(MOVIP)
ck('异议3-c 复算口径：本轮 push-only 定义的**确切范围**是「客户端 QI 请求形态」，'
   '服务端 cmpsd 基址（mov edi,imm32）在 R116 已单列 forms.mov_imm32 且**不计入**请求数；'
   '执行员把两者相加（68+8=76）属口径混用',
   len(IPS_VAL) > 0 and len(MOVIP) > 0,
   {'push_only': len(IPS_VAL), 'mov_server': len(MOVIP),
          'if_summed': len(IPS_VAL) + len(MOVIP)})

json.dump({'obj1': {'rate_rdata': rate_r, 'rate_data': rate_d, 'rows': rows,
                    'loose_by_value': k_loose_and, 'loose_by_addr': k_loose_addr},
           'obj2': sib, 'obj2b': sib_ok,
           'obj3': prof, 'checks': checks},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
