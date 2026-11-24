#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116d_iat_indirect.py —— 两处自错的正面处理（R116 自错 S-24 / S-25）

S-24（IAT 调用形态漏检，主会话自抓）：
  r116a/r116b/r116c 判定「函数是否调用 ole32!OleSaveToStream」时只认
      call dword ptr [0x7e15f4]
  这种**直接 IAT 调用**形态。实测 0x67cef0（唯一被判"未耦合"的函数）用的是
      mov ebp, dword ptr [0x7e15f4]   ; ... ; call ebp
  即**寄存器间接**形态。故「36 个函数里 1 个未耦合」是漏检造成的假缺口，
  真实情况必须把两种形态都算上。

S-25（把同一例程的多份拷贝当多份独立证据，等于 R115 自错 S-15 复发）：
  0x7f7c80 的 42 个 QI 站点分布在 36 个 HB 函数里，但按「抹掉全部立即数后的指令
  序列指纹」去重，只有 **2 种代码形状**：
      形状 P：35 个函数，每个 1 个站点（完全相同的一份例程拷贝 35 次）
      形状 Q：1 个函数（0x67cef0），7 个站点，内含 2 个结构相似的循环
  「35 个函数都耦合」这句在**函数**粒度上成立，但独立证据数只有 2，不是 36。
  必须同时报出两个粒度，不许只挑好看的那个。

断言：
  A1 两种调用形态都识别：直接 call [IAT] 与 mov reg,[IAT] + call reg
  A2 重算耦合：0x7f7c80 的 36 个函数里耦合几个（两种形态都算）
  A3 追加：0x7f7c90(IUnknown) 在两种形态下的耦合数（对照组，必须仍为 0）
  A4 代码形状去重：报告 raw 站点数 / 函数数 / 形状数 三个粒度
  K1 反控：把 mov reg,[IAT] 的识别也套到 0x7f7c90 上，必须仍为 0（不是"任何 mov 都算"）
  K2 反控：伪造 —— 把 IAT 换成不存在的槽，必须 0 命中
内存纪律：disasm_lite；逐函数 <=2000 B；detail 恒 False。
"""
import bisect, collections, hashlib, json, os, re, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r116/r116d_iat_indirect.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def fn_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


IAT_SAVE, IAT_LOAD = 0x7e15f4, 0x7e15f8


def body(f, win=2000):
    return L.body(f, win=win)


def ole_save_calls(f, slot=IAT_SAVE):
    """两种形态：
       (1) call dword ptr [slot]                       -> 直接
       (2) mov R, dword ptr [slot] ; ... ; call R       -> 寄存器间接
    返回 [(call_va, form, reg_or_None)]"""
    ins = body(f)
    out = []
    slot_pat = 'dword ptr [%s]' % hex(slot)
    regs = {}                      # reg -> 最近一次从 slot 装载的指令地址
    for a, sz, m, o in ins:
        if m == 'mov' and slot_pat in o and o.endswith(slot_pat):
            r = o.split(',')[0].strip()
            if re.fullmatch(r'[a-z]{2,3}', r):
                regs[r] = a
        elif m == 'mov' and o.endswith(slot_pat):
            r = o.split(',')[0].strip()
            if re.fullmatch(r'[a-z]{2,3}', r):
                regs[r] = a
        elif m in ('xor', 'mov'):
            r = o.split(',')[0].strip()
            if r in regs and slot_pat not in o:
                regs.pop(r, None)
        elif m == 'call':
            if o == slot_pat:
                out.append((a, 'direct', None))
            elif re.fullmatch(r'[a-z]{2,3}', o) and o in regs:
                out.append((a, 'reg_indirect', o))
    return out


def qi_push_sites(iid):
    """指令对齐的 push imm32 站点（复算 r116a，独立实现）。"""
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        a = TS + i
        for back in range(1, 6):
            s0 = a - back
            if s0 < TS:
                continue
            g = list(MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == a + 4 and g[0][2] == 'push':
                out.append({'use': s0, 'fn': fn_of(s0)})
                break
        i = buf.find(pat, i + 1)
    return out


def shape(f, win=700):
    out = []
    for a, sz, m, o in body(f, win=win):
        out.append('%s %s' % (m, re.sub(r'0x[0-9a-f]+', 'I', o)))
    return hashlib.sha256('\n'.join(out).encode()).hexdigest()[:10]


# ---------- A1/A2 ----------
res = {}
for iid in (0x7f7c80, 0x7f7c90):
    sites = qi_push_sites(iid)
    per = collections.defaultdict(list)
    for x in sites:
        if x['fn'] is not None:
            per[x['fn']].append(x['use'])
    direct_only, both = [], []
    for f, us in per.items():
        calls = ole_save_calls(f)
        after = [c for c in calls if c[0] > min(us)]
        if after:
            both.append(f)
            if any(fm == 'direct' for _, fm, _ in after):
                direct_only.append(f)
    shapes = collections.defaultdict(list)
    for f in per:
        shapes[shape(f)].append(f)
    res[hex(iid)] = {'stations': len(sites), 'fns': len(per),
                     'coupled_old_direct_only': len(direct_only),
                     'coupled_both_forms': len(both),
                     'coupled_fns': [hex(f) for f in sorted(both)],
                     'uncoupled_fns': [hex(f) for f in sorted(set(per) - set(both))],
                     'shapes': {k: [hex(x) for x in v] for k, v in shapes.items()},
                     'n_shapes': len(shapes)}
    r = res[hex(iid)]
    print('%s: 站点 %d / 函数 %d / 形状 %d | 只认直接形态耦合 %d | 两种形态都认 %d'
          % (hex(iid), r['stations'], r['fns'], r['n_shapes'],
             r['coupled_old_direct_only'], r['coupled_both_forms']))

b8 = res[hex(0x7f7c80)]
ck('A1 S-24 修正后：0x7f7c80 的 36 个请求函数里，耦合 OleSaveToStream 的从「只认直接 IAT 调用」的 '
   '%d 个变成「两种形态都认」的 %d 个（未耦合 %d 个）'
   % (b8['coupled_old_direct_only'], b8['coupled_both_forms'], len(b8['uncoupled_fns'])),
   b8['coupled_both_forms'] == 36 and len(b8['uncoupled_fns']) == 0,
   {'direct_only': b8['coupled_old_direct_only'], 'both': b8['coupled_both_forms'],
    'uncoupled': b8['uncoupled_fns']})

ck('A2 S-25 修正后（三粒度并列）：0x7f7c80 的 QI 请求站点 %d 个，分布在 %d 个 HB 函数，'
   '但按「抹掉立即数后的指令序列」去重只有 %d 种代码形状 ⇒ 独立证据数是 %d，不是 %d'
   % (b8['stations'], b8['fns'], b8['n_shapes'], b8['n_shapes'], b8['fns']),
   b8['n_shapes'] == 2, {'stations': b8['stations'], 'fns': b8['fns'],
                         'shapes': b8['shapes']})

b9 = res[hex(0x7f7c90)]
ck('A3 对照组：IUnknown 0x7f7c90 的 %d 个请求函数在两种形态下耦合数仍为 %d（不得因放宽形态而上涨）'
   % (b9['fns'], b9['coupled_both_forms']),
   b9['coupled_both_forms'] == 0,
   {'fns': b9['fns'], 'coupled': b9['coupled_both_forms'],
    'shapes': b9['n_shapes']})

# ---------- K1 / K2 ----------
k1 = b9['coupled_both_forms']
ck('K1 反控：寄存器间接识别没有把 IUnknown 的 8 个函数误判成耦合（%d 个）' % k1, k1 == 0, {'k1': k1})

fake = 0
for iid in (0x7f7c80,):
    for x in qi_push_sites(iid):
        if x['fn'] is None:
            continue
        if ole_save_calls(x['fn'], slot=0x7e1500):
            fake += 1
ck('K2 反控（有牙）：把 IAT 槽换成不存在的 0x7e1500，命中数必须为 0（不是"任何 call 都算"）',
   fake == 0, {'fake_hits': fake})

json.dump({'res': res, 'checks': checks}, open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
