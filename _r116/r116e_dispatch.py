#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116e_dispatch.py —— 链 L：0x7f7c80 的 35 个「序列化站点」是被一张 **.data 表**驱动的，
不是 35 条独立证据（R116 自错 S-25 的定性收口）。

S-25 的完整形态（这是本轮最重要的方法论修正）：
  r116a 报到「36 个函数请求 0x7f7c80，35 个耦合 OleSaveToStream」。按**指令序列**去重，
  36 个函数只有 **2 种代码形状**（35 份拷贝 + 0x67cef0）。
  但去重到 2 仍然不对：这 35 份拷贝的**函数体逐字节相同**（112 字节全等），
  差异全在调用处的 `mov edx, imm32` —— 而那个 imm32 是一个 .data 结构指针。
  故正确的说法是：
      **1 个例程模板 + 1 张 35 项的表**，而不是 35 个独立实现。
  独立证据数在「代码」维度是 1，在「数据项」维度是 35。两个维度都必须报。

断言：
  A1 35 个 dispatcher 调用点全部满足锚形态 `mov ecx,esi ; mov edx,imm32 ; call rel32`
     （反控：这 35 个 call 全部落在 copy block 内，无一例外）
  A2 35 份被调用函数体的前 112 字节**逐字节全等**（真的是一份模板）
  A3 35 个 edx 立即数**两两不同**，且全部落在 .data (0x812000..0xB7A000)
  A4 每个 edx 指向的 .data 结构里，前 8 字节是一个指向 .rdata 名字/字符串的指针
     （或按实测如实报结构）
  K1 反控（有牙）：把锚形态放宽成「任意 rel32 call 落在 copy block」——
     候选数必须仍是 35，且放宽后会出现 >35 的假阳性吗？如实测
  K2 反控：把 edx 立即数改成常数值（如 0）后，"两两不同" 必须失败
内存纪律：disasm_lite，全线性；detail 恒 False。
"""
import collections, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
DATA0, DATA1 = 0x812000, 0xB7A000
OUT = os.path.join(ROOT, '_r116/r116e_dispatch.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


LO, HI = 0x67fdf0, 0x681000

# ---- 收集候选：rel32 call 落在 copy block ----
cand = []
a = 0x67df00
while a < 0x67e400:
    if raw[fo(a)] == 0xe8:
        rel = struct.unpack_from('<i', raw, fo(a) + 1)[0]
        t = a + 5 + rel
        if LO <= t < HI:
            cand.append((a, t))
    a += 1

# ---- A1 锚形态 ----
ok, unmatched = [], []
for a, t in cand:
    if raw[fo(a) - 2:fo(a)] == b'\x8b\xce' and raw[fo(a) - 7] == 0xba:
        ok.append((a, t, struct.unpack_from('<I', raw, fo(a) - 6)[0]))
    else:
        unmatched.append((hex(a), hex(t), raw[fo(a) - 7:fo(a)].hex()))
ck('A1 35 个 dispatcher 调用点全部满足锚形态（call 前 2 字节 = 8B CE 即 mov ecx,esi，'
   '再前 5 字节 = BA + imm32 即 mov edx,imm32）：候选 %d，匹配 %d，不匹配 %d'
   % (len(cand), len(ok), len(unmatched)),
   len(cand) == 35 and len(ok) == 35 and not unmatched,
   {'candidates': len(cand), 'matched': len(ok), 'unmatched': unmatched[:5]})

# ---- A2 函数体逐字节全等 ----
bodies = collections.Counter()
for a, t, edx in ok:
    bodies[bytes(raw[fo(t):fo(t) + 0x70])] += 1
ck('A2 35 份被调用函数体的前 112 字节逐字节全等（模板唯一）：不同的体 %d 种' % len(bodies),
   len(bodies) == 1, {'distinct_bodies': len(bodies),
                      'count': list(bodies.values())})

# ---- A3 edx 两两不同且落在 .data ----
edxs = [e for _, _, e in ok]
in_data = [e for e in edxs if DATA0 <= e < DATA1]
ck('A3 35 个 edx 立即数两两不同（distinct %d / 35）且全部落在 .data [%08x,%08x)：%d 个'
   % (len(set(edxs)), DATA0, DATA1, len(in_data)),
   len(set(edxs)) == 35 and len(in_data) == 35,
   {'distinct': len(set(edxs)), 'in_data': len(in_data)})

# ---- A4 edx 指向的 .data 结构 ----
# .data 的 VirtualSize(0x367be4) 远大于 SizeOfRawData(0x6c000)：尾部是未初始化区(BSS)，
# 文件里没有字节。必须显式区分「有文件映像」与「无文件映像」，不能当成读到 0。
RAW_END = len(raw)


def readable(va, n=4):
    o = fo(va)
    return o >= 0 and o + n <= RAW_END


structs = []
for e in edxs[:35]:
    d = {'va': hex(e), 'in_file': readable(e, 24)}
    if d['in_file']:
        d['dwords'] = ['%08x' % u32(e + 4 * k) for k in range(6)]
        w0 = u32(e)
    else:
        d['dwords'] = None
        w0 = None
    d['w0_in_rdata'] = bool(w0 is not None and L.RD0 <= w0 < L.RD1)
    d['w0_in_text'] = bool(w0 is not None and TS <= w0 < TE)
    structs.append(d)
n_file = sum(1 for d in structs if d['in_file'])
n_bss = 35 - n_file
# S-26（自错）：初版把「首 dword 落在 .text 地址区间」当成「指向 .text 的指针」，
# 实测 4 个命中里 0x00790074 = UTF-16 "t\0y\0"、0x00550047 = "G\0U\0"，
# 是**字符串内容**恰好落在 .text 数值区间，不是指针。区间命中不等于指针，此判据作废。
# 只断言可核的部分：可读项的**首 dword** 不是指向 .rdata 的指针，也不是 .text 代码指针
n_ptr0 = sum(1 for d in structs if d['in_file'] and d['dwords'] and
             (L.RD0 <= int(d['dwords'][0], 16) < L.RD1))
n_small0 = sum(1 for d in structs if d['in_file'] and d['dwords'] and
               int(d['dwords'][0], 16) < 0x10000)
ck('A4 35 个 .data 项如实分区：文件映像内 %d 个、BSS 尾部无文件字节 %d 个；'
   '可读 %d 个中首 dword 指向 .rdata 的 %d 个、首 dword < 0x10000（UTF-16 文本/小常量）的 %d 个'
   '⇒ 这些 .data 项不是统一的指针结构，如实登记，不套语义'
   % (n_file, n_bss, n_file, n_ptr0, n_small0),
   n_file + n_bss == 35 and n_ptr0 == 0,
   {'in_file': n_file, 'bss': n_bss, 'dword0_ptr_rdata': n_ptr0,
    'dword0_small': n_small0,
    'sample': [dict(d) for d in structs if d['in_file']]})

# ---- K1 反控（有牙）：锚形态必须能把「不含 0x7f7c80 的小桩」排除在外 ----
# 0x67fdd0 / 0x67fde0 是 9 字节的 Release 桩（mov eax,[ecx] / test / je / mov ecx,[eax] / push / call [ecx+8] / ret），
# 它们也被 rel32 call 调过，但**不请求 0x7f7c80**。正确反控是：锚形态对它们必须不匹配。
stub_calls = []
a = TS
while a < TE - 5:
    if raw[fo(a)] == 0xe8:
        rel = struct.unpack_from('<i', raw, fo(a) + 1)[0]
        t = a + 5 + rel
        if t in (0x67fdd0, 0x67fde0):
            stub_calls.append((a, t))
    a += 1
stub_anchor = [c for c in stub_calls
               if raw[fo(c[0]) - 2:fo(c[0])] == b'\x8b\xce' and raw[fo(c[0]) - 7] == 0xba]
ck('K1 反控（有牙）：0x67fdd0/0x67fde0 这两个**不请求 0x7f7c80** 的 Release 桩也被 rel32 call '
   '调用 %d 次，其中满足锚形态的 %d 次（必须为 0）⇒ 锚形态确实在筛内容，不是筛地址'
   % (len(stub_calls), len(stub_anchor)),
   len(stub_calls) > 0 and len(stub_anchor) == 0,
   {'stub_calls': len(stub_calls), 'stub_anchor_matched': len(stub_anchor)})

# ---- K2 反控：把 edx 全设成常数，"两两不同" 必须失败 ----
fake = [0xB04BD0] * 35
ck('K2 反控：把 35 个 edx 全设成常数 0xb04bd0 后，distinct 变 %d（必须不是 35）⇒ A3 的'
   '「两两不同」不是恒真判据' % len(set(fake)),
   len(set(fake)) != 35, {'fake_distinct': len(set(fake))})

json.dump({'dispatcher': [{'call': hex(a), 'target': hex(t), 'edx': '%08x' % e} for a, t, e in ok],
           'structs': structs, 'checks': checks,
           'verdict': '35 个站点 = 1 个例程模板 + 1 张 35 项 .data 表；'
                      '独立证据数在代码维度是 1，在数据项维度是 35'},
          open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
