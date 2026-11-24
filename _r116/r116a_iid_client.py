#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116a_iid_client.py —— 链 J：IID 常量的**客户端请求面**，作为
0x7f7c70 / 0x7f7c80 之争的第三条独立数据面（R112/R113/R114/R115 三轮未取得项②）。

R112–R115 的判据域（必须看清，这是本轮的关键）：
  三轮都只读**服务端**：类的 slot0 QI 函数体里 `repe cmpsd` 依次比对的 IID 立即数。
  那个面上 0x7f7c70 与 0x7f7c80 永远出现在同一批函数、命中后写回同一个指针
  ⇒ 认领类集合逐元素相同（各 90 类）、对称差 0 ⇒ 判「不可区分，不编赢家」。
  那个结论是**对的**，但它的适用域只是服务端比对序列。

本轮换到**客户端**：谁把哪个 IID 常量当参数**请求**出去（QueryInterface 的 riid），
以及拿到接口指针之后立刻交给哪个 ole32 API。这是判据来源完全不同的第三面：
  * 服务端面读的是「我认识哪些 IID」（识别集）
  * 客户端面读的是「我被谁按哪个 IID 要过」（请求集）
  识别集对称 不代表 请求集对称。

断言：
  A1 请求面实测：0x7f7c80 有 60 个 push-imm32 请求站点；0x7f7c70 **0 个**（全 .text 字节扫描
     + 指令对齐双重确认：0x7f7c70 的 4 处出现全部是 mov edi,imm32，即服务端 cmpsd 的比对基址，
     从不作为 push 参数出现）
  A2 【去重后仍成立】按**函数**去重（0x67fe70/0x67fef0/... 是同一例程的 10 份拷贝，
     按站点计数会重复计同一份证据 —— 纪律 39）：请求 0x7f7c80 的不同函数 N 个，
     请求 0x7f7c70 的不同函数 0 个
  A3 【耦合】这些函数里，请求之后出现 ole32!OleSaveToStream(0x7e15f4) 或
     OleLoadFromStream(0x7e15f8) 调用的比例
  A4 【反向】43 个 OleSaveToStream 调用点里，同一函数内**先**请求 0x7f7c80 的有几个、
     先请求 0x7f7c70 的有几个
  K1 反控（同质，带牙）：把 IID 换成 IUnknown(0x7f7c90) 做同样统计 —— 它有 56 个 push 站点，
     若它与 Ole*Stream 的耦合率也接近 100%，说明「耦合」不是 0x7f7c80 的特性，A3 无效
  K2 反控（基线）：全 .text 里所有 push imm32 且 imm 是「GUID 形状」常量者，
     求「函数内后续有 Ole*Stream」的基线比例
  K3 反控（形态）：把判据从 push_imm32 放宽成「任意 4 字节出现」，0x7f7c70 仍然 4 处、
     0x7f7c80 变 64 处 ⇒ 放宽后差集不消失（证明结论不依赖指令形态筛选）
内存纪律：disasm_lite，逐函数 <=2000 B，detail 恒 False。
"""
import bisect, collections, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r116/r116a_iid_client.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def fn_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


_IAT = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream'}
_IAT_ALL = dict(_IAT)
_IAT_ALL.update({0x7e15fc: 'CoCreateInstance', 0x7e15f0: 'CLSIDFromString',
                 0x7e15d8: 'CoRegisterClassObject', 0x7e15d4: 'OleInitialize'})

_IID = {0x7f7c70: '0x7f7c70 (A)', 0x7f7c80: '0x7f7c80 (B)', 0x7f7c90: '0x7f7c90 (IUnknown)',
        0x7f7ca0: '0x7f7ca0 (IClassFactory)', 0x7ed358: '0x7ed358 (ILocomotion)',
        0x7e9ae0: '0x7e9ae0 (IRTTITypeInfo-ish)'}


def insn_ending_at(va):
    """找一条从 va-back 起、末端恰好落在 va+4 的指令（即它消费了 va 处这个 imm32）。"""
    for back in range(1, 9):
        start = va - back
        if start < TS:
            continue
        g = list(MD.disasm_lite(raw[fo(start):fo(start) + 16], start))
        if g and g[0][0] == start and g[0][0] + g[0][1] == va + 4:
            return g[0]
    return None


def sites(iid):
    """[{use_va, form, fn}] —— form ∈ {push_imm32, mov_imm32, other_imm32}"""
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        va = TS + i
        s = insn_ending_at(va)
        form = 'other_imm32'
        if s is not None:
            form = ('push_imm32' if s[2] == 'push' else
                    ('mov_imm32' if s[2] == 'mov' else 'other_imm32'))
        out.append({'use_va': s[0] if s else va, 'form': form, 'fn': fn_of(va)})
        i = buf.find(pat, i + 1)
    return out


def ole_calls(f):
    out = []
    for a, sz, m, o in L.body(f):
        if m != 'call':
            continue
        try:
            v = int(o.replace('dword ptr [', '').replace(']', ''), 16)
        except ValueError:
            continue
        if v in _IAT_ALL:
            out.append((a, _IAT_ALL[v]))
    return out


# ---------- A1 请求面 ----------
S = {iid: sites(iid) for iid in _IID}
rows = {}
for iid, nm in _IID.items():
    s = S[iid]
    forms = dict(collections.Counter(x['form'] for x in s))
    pushf = sorted(set(x['fn'] for x in s if x['form'] == 'push_imm32'))
    rows[nm] = {'total_byte_hits': len(s), 'forms': forms,
                'push_sites': forms.get('push_imm32', 0),
                'push_distinct_fns': len(pushf), 'push_fns': [hex(f) for f in pushf]}
    print('%-26s total %3d  %-46s push %2d sites / %2d fns'
          % (nm, len(s), str(forms), forms.get('push_imm32', 0), len(pushf)))

a70, a80 = rows['0x7f7c70 (A)'], rows['0x7f7c80 (B)']
ck('A1 客户端请求面完全不对称：0x7f7c80 push-imm32 请求站点 %d 个；0x7f7c70 %d 个'
   % (a80['push_sites'], a70['push_sites']),
   a80['push_sites'] == 60 and a70['push_sites'] == 0,
   {'B_pushes': a80['push_sites'], 'A_pushes': a70['push_sites'],
    'A_forms': a70['forms'], 'B_forms': a80['forms']})

ck('A2 去重到**函数**后结论不变：请求 0x7f7c80 的不同函数 %d 个，请求 0x7f7c70 的 %d 个'
   % (a80['push_distinct_fns'], a70['push_distinct_fns']),
   a80['push_distinct_fns'] >= 1 and a70['push_distinct_fns'] == 0,
   {'B_fns': a80['push_distinct_fns'], 'A_fns': a70['push_distinct_fns']})

# ---------- A3 耦合（按函数去重） ----------
def couple(iid, want=('OleSaveToStream', 'OleLoadFromStream')):
    per_fn = {}
    for x in S[iid]:
        if x['form'] != 'push_imm32' or x['fn'] is None:
            continue
        per_fn.setdefault(x['fn'], []).append(x['use_va'])
    hit, miss = [], []
    for f, us in sorted(per_fn.items()):
        after = [c for c in ole_calls(f) if c[0] > min(us)]
        if any(n in want for _, n in after):
            hit.append(f)
        else:
            miss.append(f)
    return per_fn, hit, miss


pf80, hit80, miss80 = couple(0x7f7c80)
ck('A3 耦合【按函数去重】：%d 个请求 0x7f7c80 的函数中，%d 个在请求之后调用 ole32!OleSaveToStream '
   '或 OleLoadFromStream（%.1f%%）；未耦合 %d 个 %s'
   % (len(pf80), len(hit80), 100.0 * len(hit80) / max(1, len(pf80)), len(miss80),
      [hex(f) for f in miss80][:8]),
   len(pf80) > 0 and len(hit80) >= 1,
   {'fns': len(pf80), 'coupled': len(hit80), 'uncoupled': [hex(f) for f in miss80]})

# ---------- A4 反向 ----------
buf = raw[fo(TS):fo(TE)]
save_sites = []
pat = struct.pack('<I', 0x7e15f4)
i = buf.find(pat)
while i != -1:
    va = TS + i
    if raw[fo(va) - 2:fo(va)] == b'\xff\x15':
        save_sites.append(va - 2)
    i = buf.find(pat, i + 1)
load_sites = []
pat = struct.pack('<I', 0x7e15f8)
i = buf.find(pat)
while i != -1:
    va = TS + i
    if raw[fo(va) - 2:fo(va)] == b'\xff\x15':
        load_sites.append(va - 2)
    i = buf.find(pat, i + 1)


def before(iid, call_va):
    f = fn_of(call_va)
    return [x for x in S[iid] if x['form'] == 'push_imm32' and x['fn'] == f and x['use_va'] < call_va]


rev = {'save': {'sites': len(save_sites), 'with_B': 0, 'with_A': 0},
       'load': {'sites': len(load_sites), 'with_B': 0, 'with_A': 0}}
for c in save_sites:
    rev['save']['with_B'] += 1 if before(0x7f7c80, c) else 0
    rev['save']['with_A'] += 1 if before(0x7f7c70, c) else 0
for c in load_sites:
    rev['load']['with_B'] += 1 if before(0x7f7c80, c) else 0
    rev['load']['with_A'] += 1 if before(0x7f7c70, c) else 0
ck('A4 反向：OleSaveToStream %d 站点中同函数内先请求 0x7f7c80 者 %d、先请求 0x7f7c70 者 %d；'
   'OleLoadFromStream %d 站点中分别为 %d / %d'
   % (rev['save']['sites'], rev['save']['with_B'], rev['save']['with_A'],
      rev['load']['sites'], rev['load']['with_B'], rev['load']['with_A']),
   rev['save']['with_A'] == 0 and rev['load']['with_A'] == 0 and rev['save']['with_B'] > 0,
   rev)

# ---------- K1 反控：同质 IID（IUnknown） ----------
pf90, hit90, miss90 = couple(0x7f7c90)
ck('K1 反控（同质）：把 IID 换成 IUnknown 0x7f7c90 —— 它有 %d 个 push 请求、%d 个不同函数，'
   '其中与 Ole*Stream 耦合 %d 个（%.1f%%）。若耦合率也接近 100%% 则 A3 无牙'
   % (len([x for x in S[0x7f7c90] if x['form'] == 'push_imm32']), len(pf90),
      len(hit90), 100.0 * len(hit90) / max(1, len(pf90))),
   100.0 * len(hit90) / max(1, len(pf90)) < 50.0,
   {'fns': len(pf90), 'coupled': len(hit90), 'rate': round(100.0 * len(hit90) / max(1, len(pf90)), 2),
    'B_rate': round(100.0 * len(hit80) / max(1, len(pf80)), 2)})

# ---------- K2 反控：基线 ----------
guidish = set()
for a in range(L.RD0, L.RD1 - 0x10, 4):
    # GUID 尾 8 字节 = C0 00 00 00 00 00 00 46 ⇒ dword@+8 = 0x000000C0、dword@+12 = 0x46000000
    if u32(a + 4) == 0x00000000 and u32(a + 8) == 0x000000C0 and u32(a + 0xc) == 0x46000000:
        guidish.add(a)
base_fns, base_hit = set(), set()
for g in sorted(guidish):
    for x in sites(g):
        if x['form'] != 'push_imm32' or x['fn'] is None:
            continue
        base_fns.add((g, x['fn']))
        after = [c for c in ole_calls(x['fn']) if c[0] > x['use_va']]
        if any(n in ('OleSaveToStream', 'OleLoadFromStream') for _, n in after):
            base_hit.add((g, x['fn']))
ck('K2 反控（基线）：.rdata 里所有 GUID 形状常量（末 12 字节 = 0000-C000-000000000046）'
   '共 %d 个；其中被 push 请求且所在函数后续有 Ole*Stream 的 (IID,函数) 对 %d / 全部 %d 对 = %.1f%%'
   ' —— 0x7f7c80 的 %d/%d 必须显著高于该基线'
   % (len(guidish), len(base_hit), len(base_fns),
      100.0 * len(base_hit) / max(1, len(base_fns)), len(hit80), len(pf80)),
   len(base_fns) > 0 and 100.0 * len(base_hit) / len(base_fns) < 100.0 * len(hit80) / max(1, len(pf80)),
   {'guiddish_iids': len(guidish), 'base_pairs': len(base_fns), 'base_coupled': len(base_hit),
    'base_rate': round(100.0 * len(base_hit) / max(1, len(base_fns)), 2)})

# ---------- K3 反控：放宽形态 ----------
tot = {iid: len(S[iid]) for iid in _IID}
ck('K3 反控（放宽形态）：判据从「指令对齐的 push_imm32」放宽成「任意 4 字节命中」后，'
   '0x7f7c70 = %d 处、0x7f7c80 = %d 处，差集不消失（放宽不改变不对称性）'
   % (tot[0x7f7c70], tot[0x7f7c80]),
   tot[0x7f7c70] == 4 and tot[0x7f7c80] == 64, {hex(k): v for k, v in tot.items()})

json.dump({'rows': rows, 'coupling': {'B': [hex(f) for f in hit80],
                                      'B_miss': [hex(f) for f in miss80],
                                      'IUnknown': [hex(f) for f in hit90]},
           'reverse': rev, 'baseline': {'guiddish': len(guidish), 'pairs': len(base_fns),
                                        'coupled': len(base_hit)},
           'checks': checks},
          open(OUT, 'w'), indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (npass, len(checks)))
print('WROTE', OUT)
sys.exit(0 if npass == len(checks) else 1)
