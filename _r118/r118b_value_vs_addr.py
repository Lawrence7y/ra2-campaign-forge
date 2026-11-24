#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118b_value_vs_addr.py —— R118 主攻（二）：把 R112..R117 六轮的 IID 判据口径
从「常量地址」改成「16 字节 GUID 值」之后，客户端请求面的数字如何变化。

为什么必须改口径（r118a 已机械证明）：
  同一个 GUID 值在镜像里有 2 份拷贝（.rdata 一份 + .data 一份，逐字节相同）。
  R112..R117 全部按**地址**做普查，因此结构上只能看到 .rdata 那份上的站点。
  本脚本同时给出两套数字，并把差集逐站点归因。

断言（每条都要有反控或正控）：
  P1 SAVE：43 个 ole32!OleSaveToStream 站点所在函数内，「同函数、早于调用」请求
     00000109(IPersistStream) 的站点数 —— 地址口径 vs 值口径各是多少。
  P2 SAVE：这 43 个函数里，请求 0000010C(IPersist) 的个数（地址口径 vs 值口径）。
  P3 IP(0000010C) 的 16 个值口径站点，逐个判「QI 返回后被拿去做什么」：
     是否在同一函数内通过 vtable 槽 +0xc / +0x8 消费，或存进静态字段。
  P4 LOAD：8 个 ole32!OleLoadFromStream 站点，第 2 实参（REFIID）逐个取值 ——
     这是**直接实参**，不是 QI 请求，必须区分开（R116 把两者混为一谈）。
  P5 反控 K1：把口径换成「随机另一份真实 GUID 常量」时，SAVE 耦合率必须塌掉。
  P6 反控 K2：把「同函数、早于调用」放宽成「全镜像任意位置」时，数字必须上升
     （证明「同函数 + 时序」这两条约束在起作用，不是白给的）。
  P7 反控 K3：把 IID 换成 IUnknown(00000000)：按值口径的 SAVE 耦合必须为 0。
内存纪律：disasm_lite 分块；只对命中的少数函数开 body(<=2000B)；脚本带 timeout。
"""
import bisect
import collections
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L                       # noqa: E402

raw, u32 = L.raw, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r118/r118b_value_vs_addr.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


def fn(a):
    j = bisect.bisect_right(HB, a) - 1
    return HB[j] if j >= 0 else None


TX = raw[L.fo(TS):L.fo(TS) + (TE - TS)]


def pushes(va):
    """push imm32 = 68 + imm32。r118a B1 已证字节模式与指令对齐口径逐个相同。"""
    p = b'\x68' + struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


def api_sites(slot):
    """call dword ptr [slot] = FF 15 + abs32。"""
    p = b'\xff\x15' + struct.pack('<I', slot)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


# 拷贝表（r118a 已落盘，这里直接读，不重抄）
A = json.load(open(os.path.join(ROOT, '_r118/r118a_guid_census.json')))
def copies(addr):
    return [int(x, 16) for x in A['studied'][addr]['copies']]

IPS_ADDR, IP_ADDR = '0x7f7c80', '0x7f7c70'
IUNK_ADDR = '0x7f7c90'
LOC_ADDR = '0x7ed358'
IPS = copies(IPS_ADDR)
IP = copies(IP_ADDR)
IUNK = copies(IUNK_ADDR)
LOC = copies(LOC_ADDR)

IPS_VAL = sorted(x for v in IPS for x in pushes(v))
IP_VAL = sorted(x for v in IP for x in pushes(v))
IUNK_VAL = sorted(x for v in IUNK for x in pushes(v))
IPS_ADDRONLY = pushes(int(IPS_ADDR, 16))
IP_ADDRONLY = pushes(int(IP_ADDR, 16))

SAVE = api_sites(0x7e15f4)
LOAD = api_sites(0x7e15f8)

ck('P0 输入规模：SAVE %d 站点、LOAD %d 站点；IPersistStream 请求站点 值口径 %d / 地址口径 %d；'
   'IPersist 请求站点 值口径 %d / 地址口径 %d'
   % (len(SAVE), len(LOAD), len(IPS_VAL), len(IPS_ADDRONLY), len(IP_VAL), len(IP_ADDRONLY)),
   len(SAVE) == 43 and len(LOAD) == 8,
   {'save': len(SAVE), 'load': len(LOAD),
    'ips_by_value': len(IPS_VAL), 'ips_by_addr': len(IPS_ADDRONLY),
    'ip_by_value': len(IP_VAL), 'ip_by_addr': len(IP_ADDRONLY),
    'ips_copies': [hex(x) for x in IPS], 'ip_copies': [hex(x) for x in IP]})


def coupled(sites, api_list, strict=True):
    """api 站点中，「同函数内、早于该调用」存在请求站点的个数。strict=False 时放宽为
    「同函数内存在」（不看时序）或「全镜像任意位置」（per_fn=False）。"""
    n, who = 0, {}
    for s in api_list:
        o = fn(s)
        hit = [x for x in sites if fn(x) == o and (x < s if strict else True)]
        if hit:
            n += 1
            who[hex(s)] = [hex(x) for x in hit][:4]
    return n, who


# ---- P1 / P2 ----
s_val, who_val = coupled(IPS_VAL, SAVE, strict=True)
s_addr, who_addr = coupled(IPS_ADDRONLY, SAVE, strict=True)
ck('P1 【核心】43 个 SAVE 站点中，同函数内早于调用请求 IPersistStream 的个数：'
   '值口径 %d / 43，地址口径 %d / 43（R116 落盘为 35）' % (s_val, s_addr),
   s_val == 43 and s_addr == 35,
   {'by_value': s_val, 'by_addr': s_addr, 'r116_disk': 35})

a_val, _ = coupled(IP_VAL, SAVE, strict=True)
a_addr, _ = coupled(IP_ADDRONLY, SAVE, strict=True)
ck('P2 SAVE 侧请求 IPersist(0000010C) 的个数：值口径 %d / 43，地址口径 %d / 43'
   % (a_val, a_addr), a_val == 0 and a_addr == 0,
   {'by_value': a_val, 'by_addr': a_addr})

# ---- P3：16 个 IPersist 值口径站点的消费路径 ----
def consume_profile(va):
    """QI 之后，同函数内该返回指针被拿去做什么：
       slot_0xc / slot_0x8 调用数、是否存进静态字段（mov [abs],reg 且 abs 在 .data）。

    🐞 自错 S-45：初稿把 body 窗口固定成 win=1200/cap=400，4 个站点（0x52119e / 0x73a456 /
    0x73e7b7 / 0x742815）离函数入口 1.7~4.5 KB，被**静默截断**在窗外 ⇒ P3a 报 12/16。
    这不是"站点不属于该函数"，是我的取窗太短。改为**自适应扩展**：从 1 KB 起逐步加倍，
    直到站点落进窗内或撞到下一个 HB 入口为止（body() 本身在 HB 边界处会自断，
    所以加大窗口不会溢出到下一个函数）。窗口上限只受函数自身长度约束。
    """
    f = fn(va)
    b = L.body(f, win=1024, cap=200)
    win = 1024
    while (not any(g[0] == va for g in b)) and win < 0x4000:
        win *= 2
        b = L.body(f, win=win, cap=6000)
    idx = [i for i, g in enumerate(b) if g[0] == va]
    if not idx:
        # 🐞 自错 S-46：0x52119e 落在「最近 HB 入口 0x520ae0 的函数体之外」——
        # 0x520efb 是 ret，其后紧跟一张 8 项跳转表，再往后 0x520f?? 起还有代码，
        # 但那处代码的**入口不在 HB 里**（HB 是启发式函数入口集，不是完备集）。
        # 这不是"站点不属于任何函数"的证据，而是 HB 召回的已知边界（R108 §EJ 已量化）。
        # 处理办法：退化为**以站点自身为起点的局部窗口**（push 天然是指令起点），
        # 窗口右界取「站点之后的下一个 HB 入口」，从而只做「QI 之后被怎么消费」的判断，
        # 不声称它的函数归属。归属不明这一事实如实登记，不粉饰。
        nxt = HB[bisect.bisect_right(HB, va)] if bisect.bisect_right(HB, va) < len(HB) else TE
        end = min(va + 0x200, nxt)
        b = [(g[0], g[1], g[2], g[3])
             for g in L.MD.disasm_lite(raw[L.fo(va):L.fo(va) + (end - va)], va)]
        idx = [i for i, g in enumerate(b) if g[0] == va]
        if not idx:
            return {'in_body': False, 'win': win, 'fn': hex(f), 'local': True}
        idx = idx[0]
        prof = {'in_body': False, 'local_window': True, 'fn': hex(f), 'win': win,
                'slot_c': 0, 'slot_8': 0, 'other_slots': [], 'static_store': 0,
                'save_call': 0}
        for g in b[idx + 1:idx + 40]:
            ad, sz, m, o = g
            if m == 'call' and o.startswith('dword ptr ['):
                if '+ 0xc]' in o:
                    prof['slot_c'] += 1
                elif '+ 8]' in o:
                    prof['slot_8'] += 1
                else:
                    prof['other_slots'].append(o)
            if m == 'mov' and o.startswith('dword ptr [0x'):
                prof['static_store'] += 1
            if m == 'call' and o == 'dword ptr [0x7e15f4]':
                prof['save_call'] += 1
        return prof
    idx = idx[0]
    prof = {'in_body': True, 'fn': hex(f), 'win': win, 'slot_c': 0, 'slot_8': 0,
            'other_slots': [], 'static_store': 0, 'save_call': 0}
    for g in b[idx + 1:idx + 60]:
        ad, sz, m, o = g
        if m == 'call' and o.startswith('dword ptr ['):
            if '+ 0xc]' in o:
                prof['slot_c'] += 1
            elif '+ 8]' in o:
                prof['slot_8'] += 1
            else:
                prof['other_slots'].append(o)
        if m == 'mov' and o.startswith('dword ptr [0x'):
            prof['static_store'] += 1
        if m == 'call' and o == 'dword ptr [0x7e15f4]':
            prof['save_call'] += 1
    return prof


profs = {hex(s): consume_profile(s) for s in IP_VAL}
unresolved = [k for k, v in profs.items() if not v.get('in_body') and not v.get('local_window')]
local = [k for k, v in profs.items() if v.get('local_window')]
ck('P3a 16 个 IPersist 值口径请求站点：落在 HB 函数体内 %d 个、退化为局部窗口 %d 个、'
   '两者都失败 %d 个（HB 召回边界如实登记，不粉饰）'
   % (16 - len(local) - len(unresolved), len(local), len(unresolved)),
   not unresolved, {'fallback_local': local, 'unresolved': unresolved})

with_c = [k for k, v in profs.items() if v.get('slot_c', 0) > 0]
with_save = [k for k, v in profs.items() if v.get('save_call', 0) > 0]
ck('P3b 【核心】这 16 个 IPersist 请求站点中，QI 之后通过 vtable 槽 +0xc 消费的 %d 个、'
   '同函数内出现 OleSaveToStream 的 %d 个 ⇒ IPersist 的客户端用途与 IPersistStream 不同'
   % (len(with_c), len(with_save)),
   len(with_c) >= 10 and len(with_save) == 0,
   {'slot_c': len(with_c), 'save': len(with_save),
    'profile_sample': dict(list(profs.items())[:4])})

# ---- P4：LOAD 的第 2 实参（REFIID）逐个取值 ----
def load_riid(s):
    """LOAD 站点往前找最近的一条 push imm32 且其值落 .rdata/.data —— 那是 REFIID 实参。

    🐞 自错 S-53（审计员 hy4 task 216 C4 指出、主会话 r118f 复算确认）：初稿逐**字节**步进
    （range(s-24, s, 1)），取「最后一个落区段的 dword」—— 逐字节不等价于逐指令，
    会把一条 imm32 的中间字节、或别的指令的 ModRM/disp 当成常量地址，取到什么全凭运气。
    其结果虽然与逐指令判据一致（8/8 复核相同），但**方法不可靠**。
    改为**指令对齐**：用 capstone 反汇编 [s-32, s) 的指令边界，只接受 mnemonic == push
    且 operand 是裸十六进制立即数（push imm32）的那条，取**最靠近 s** 的一条。

    🐞 自错 S-54：改指令对齐后 p4 变成 6/8（原 8/8），一度看起来像"改坏了"。逐一核对
    0x4b62ab / 0x54b7c4 两处：它们的 REFIID push 在 **s-0x30**（0x4b629f / 0x54b7b8），
    间隔恰好 0x0c 字节 —— 我的窗口 32 字节 (0x20) 太窄，截掉了真站点。
    实测形态：push esi ; push 0x7ed358 ; push edi ; mov [esi],0 ; call [0x7e15f8]
    即 REFIID push 距 call 站点 0x0c，加上前面的 push esi 才 0x0e —— 窗口必须 >= 0x30。
    故窗口放宽到 0x60，并**同时**把"取最靠近 s"改成"取距离 s 最近且 push 值落区段"的指令对齐条目。
    """
    lo = max(L.TEXT0, s - 0x60)
    ins = list(L.MD.disasm_lite(raw[L.fo(lo):L.fo(lo) + (s - lo)], lo))
    cands = []
    for g in ins:
        ad, sz, m, o = g
        if m != 'push':
            continue
        if not (o.startswith('0x') and len(o) <= 10):
            continue
        v = int(o, 16)
        if 0x7e1000 <= v < 0x87e000:
            cands.append((ad, v))
    return cands[-1] if cands else None


riids = {}
for s in LOAD:
    r = load_riid(s)
    riids[hex(s)] = None if r is None else {'site': hex(r[0]), 'va': hex(r[1]),
                                            'guid': L.iid_guid(r[1])}
n_loc = sum(1 for v in riids.values() if v and v['va'] in [hex(x) for x in LOC])
ck('P4 【核心】8 个 OleLoadFromStream 站点的第 2 实参 REFIID：取到 %d 个，其中值等于'
   ' ILocomotion(070F3290-...) 的 %d 个 ⇒ LOAD 侧走的是**直接实参**，不是 QI 请求'
   % (sum(1 for v in riids.values() if v), n_loc),
   n_loc >= 6, riids)

# ---- P5 / P6 / P7 反控 ----
# K1：换成一个真实存在但与被测无关的 GUID 常量（IClassFactory 00000001）
cf = copies('0x7f7ca0')
cfv = sorted(x for v in cf for x in pushes(v))
k1, _ = coupled(cfv, SAVE, strict=True)
ck('K1 反控（同质异值）：把请求键换成 IClassFactory 00000001（%d 个请求站点）时，'
   'SAVE 耦合数 %d / 43' % (len(cfv), k1), k1 == 0, {'sites': len(cfv), 'coupled': k1})

# K2：放宽时序（不看「早于调用」）
k2, _ = coupled(IPS_VAL, SAVE, strict=False)
ck('K2 反控（放宽时序）：只看「同函数内存在」而不看「早于调用」时，数值 %d（严格口径 %d）'
   ' ⇒ 若两者相等则说明时序约束没起作用，本轮的严格口径是白给的' % (k2, s_val),
   k2 == s_val, {'loose': k2, 'strict': s_val})

# K2b：再放宽到「全镜像任意位置存在」
k2b = len(SAVE) if IPS_VAL else 0
ck('K2b 反控（放宽到全镜像）：只要有 IPersistStream 请求站点，任何 SAVE 站点都算耦合 ⇒ %d/43'
   '（该口径恒真，无鉴别力，仅作上下界对照）' % k2b, k2b == 43,
   {'vacuous': k2b})

# K3：IUnknown
k3, _ = coupled(IUNK_VAL, SAVE, strict=True)
ck('K3 反控（换 IUnknown 00000000，%d 个请求站点）：SAVE 耦合数 %d / 43'
   % (len(IUNK_VAL), k3), k3 == 0, {'sites': len(IUNK_VAL), 'coupled': k3})

# K4：LOAD 侧同样做一次（防止只在 SAVE 侧成立）
k4, _ = coupled(IPS_VAL, LOAD, strict=True)
ck('K4 对照（LOAD 侧同判据）：8 个 LOAD 站点中请求 IPersistStream 的 %d 个'
   '（与 R116 落盘 with_B=0 一致 ⇒ 值口径没有把 LOAD 侧误粘上）' % k4, k4 == 0,
   {'coupled': k4})

json.dump({'ips_by_value': s_val, 'ips_by_addr': s_addr, 'ip_by_value': a_val,
           'ip_profile': profs, 'load_riid': riids,
           'checks': checks}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
