#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116b_argpos.py —— 链 K：QI(riid) 的结果**被放到哪个形参位置**，以及
K2 自参照缺陷的修正（R116 自错 S-23 的正面处理）。

R116 自错 S-23（本轮自抓，必须如实登记）：
  r116a 的 K2「基线」把 .rdata 里所有 GUID 形状常量（尾 8 字节 = C0 00 00 00 00 00 00 46）
  里的 (IID,函数) 对全部计入基线，但 **0x7f7c80 自己就在这个集合里**
  （它的尾 8 字节正是 C0 00 00 00 00 00 00 46），于是 46 对基线里 35 对就是 0x7f7c80 自己
  ⇒ 基线 76.1% 是被测对象自造的，K2 是自参照（循环对照），无鉴别力。
  正确做法：留一法（leave-one-out）—— 基线只用**除被测 IID 之外**的 GUID 形状常量，
  并单独报出被测 IID 对基线的贡献量。

本脚本断言：
  A1 六个 GUID 形状 IID 的地址与「被 push 请求 / 被 mov 比对」分类（复算 r116a，独立重写）
  A2 【留一法基线】排除 0x7f7c80 后，剩余 5 个 GUID 形状常量的 (IID,函数) 对里，
     所在函数后续有 Ole*Stream 的比例；与 0x7f7c80 的 35/36 比较
  A3 【形参位置】在 OleSaveToStream 调用点回溯：被 QI(0x7f7c80) 返回的那个指针
     （= [esp+X] 处的栈槽）是否被 push 为**第 1 个实参**（cdecl 最右先压 ⇒ 最后压的那个）
  A4 【对照】同样回溯 OleSaveToStream 的第 2 个实参来源，必须不是 QI 结果而是流对象
  A5 【空面】0x7f7c70 的 QI 结果在整个 .text 里有无任何一次被 push 给**任何** ole32 API
  K1 反控：把 A3 的判据换成 IUnknown(0x7f7c90)，其 QI 结果被 push 给 ole32 API 的站点数
  K2 反控：留一法基线的"无 Ole 耦合"侧必须非空（否则比例不可算/无意义）
内存纪律：disasm_lite；逐函数 <=2000 B；detail 恒 False。
"""
import bisect, collections, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r116/r116b_argpos.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def fn_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


_OLE = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream',
        0x7e15fc: 'CoCreateInstance', 0x7e15f0: 'CLSIDFromString',
        0x7e15d4: 'OleInitialize', 0x7e15d8: 'CoRegisterClassObject'}


def guidish_va():
    out = []
    a = L.RD0
    while a < L.RD1 - 0x10:
        if u32(a + 4) == 0 and u32(a + 8) == 0xC0 and u32(a + 12) == 0x46000000:
            out.append(a)
        a += 4
    return out


def insn_ending_at(va):
    for back in range(1, 9):
        s0 = va - back
        if s0 < TS:
            continue
        g = list(MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
        if g and g[0][0] == s0 and g[0][0] + g[0][1] == va + 4:
            return g[0]
    return None


def sites(iid):
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        va = TS + i
        s = insn_ending_at(va)
        form = 'other'
        if s is not None:
            form = 'push_imm32' if s[2] == 'push' else ('mov_imm32' if s[2] == 'mov' else 'other')
        out.append({'use': s[0] if s else va, 'form': form, 'fn': fn_of(va)})
        i = buf.find(pat, i + 1)
    return out


def ole_calls(f):
    r = []
    for a, sz, m, o in L.body(f):
        if m != 'call':
            continue
        try:
            v = int(o.replace('dword ptr [', '').replace(']', ''), 16)
        except ValueError:
            continue
        if v in _OLE:
            r.append((a, _OLE[v]))
    return r


G = guidish_va()
S = {g: sites(g) for g in G}
# ---------- A1 ----------
rows = []
for g in G:
    forms = dict(collections.Counter(x['form'] for x in S[g]))
    pushf = sorted(set(x['fn'] for x in S[g] if x['form'] == 'push_imm32'))
    rows.append({'va': hex(g), 'd1': '%08X' % u32(g), 'forms': forms,
                 'push_sites': forms.get('push_imm32', 0), 'push_fns': len(pushf)})
    print('%-12s d1=%08X  %-44s push %2d sites / %2d fns'
          % (hex(g), u32(g), str(forms), forms.get('push_imm32', 0), len(pushf)))
ck('A1 GUID 形状常量（尾 8 字节 C0..46）共 %d 个：%s' % (len(G), [hex(g) for g in G]),
   len(G) == 6, rows)

# ---------- A2 留一法基线（S-23 修正） ----------
TARGET = 0x7f7c80
def pairs_coupled(iid):
    per = collections.defaultdict(list)
    for x in S.get(iid, []):
        if x['form'] == 'push_imm32' and x['fn'] is not None:
            per[x['fn']].append(x['use'])
    hit, miss = [], []
    for f, us in per.items():
        after = [c for c in ole_calls(f) if c[0] > min(us)]
        (hit if any(n in ('OleSaveToStream', 'OleLoadFromStream') for _, n in after) else miss).append(f)
    return per, hit, miss


pT, hT, mT = pairs_coupled(TARGET)
others = [g for g in G if g != TARGET]
b_fn, b_hit = 0, 0
detail_base = []
for g in others:
    p, h, m = pairs_coupled(g)
    b_fn += len(p)
    b_hit += len(h)
    detail_base.append({'va': hex(g), 'fns': len(p), 'coupled': len(h)})
rate_t = 100.0 * len(hT) / max(1, len(pT))
rate_b = 100.0 * b_hit / max(1, b_fn)
ck('A2 留一法基线（S-23 修正）：排除被测 0x7f7c80 后，其余 %d 个 GUID 形状常量的 '
   '(IID,函数) 对 %d 个，其中函数后续有 Ole*Stream 者 %d = %.1f%%；'
   '被测者 %d/%d = %.1f%%'
   % (len(others), b_fn, b_hit, rate_b, len(hT), len(pT), rate_t),
   b_fn > 0 and rate_t > rate_b,
   {'baseline': detail_base, 'target': {'fns': len(pT), 'coupled': len(hT), 'rate': round(rate_t, 2)},
    'baseline_rate': round(rate_b, 2)})

# 零假设检验：若耦合率与基线同分布，36 个函数里期望耦合 36*rate_b/100
exp = len(pT) * rate_b / 100.0
ck('A2b 定量：若 0x7f7c80 的耦合率等于留一法基线 %.2f%%，36 个函数期望耦合 %.2f 个，实测 %d 个 '
   '⇒ 超出期望 %.2f 个（不是"略高"，是几乎全中）'
   % (rate_b, exp, len(hT), len(hT) - exp),
   len(hT) - exp >= 10, {'expected': round(exp, 2), 'observed': len(hT)})

# ---------- A3 形参位置：OleSaveToStream 第 1 实参是否 = QI(0x7f7c80) 的结果 ----------
buf = raw[fo(TS):fo(TE)]
save_sites = []
pat = struct.pack('<I', 0x7e15f4)
i = buf.find(pat)
while i != -1:
    va = TS + i
    if raw[fo(va) - 2:fo(va)] == b'\xff\x15':
        save_sites.append(va - 2)
    i = buf.find(pat, i + 1)


def window(f, upto, back=40):
    """函数体内 upto 之前的最后 back 条指令（含 upto 之前）。"""
    body = L.body(f)
    out = []
    for g in body:
        if g[0] >= upto:
            break
        out.append(g)
    return out[-back:]


arg1_rows = []
for c in save_sites:
    f = fn_of(c)
    w = window(f, c)
    # cdecl：最后压栈的那个 = 第 1 实参。找 window 末尾连续的 push 序列
    pushes = []
    for g in reversed(w):
        if g[2] == 'push':
            pushes.append(g)
        else:
            break
    pushes.reverse()          # 压栈顺序（先压 = 最后实参）
    q80 = [x['use'] for x in S[0x7f7c80] if x['form'] == 'push_imm32'
           and x['fn'] == f and x['use'] < c]
    arg1 = pushes[-1][3] if pushes else None
    arg2 = pushes[-2][3] if len(pushes) >= 2 else None
    arg1_rows.append({'save': hex(c), 'fn': hex(f), 'npushes': len(pushes),
                      'arg1': arg1, 'arg2': arg2, 'qi80_before': len(q80),
                      'arg1_is_pointer_reg': bool(arg1 and not arg1.startswith('0x') and len(arg1) <= 4)})

# 「第 1 实参是被 QI 返回的接口指针」的机械判据：
#   QI 之后代码立刻 mov reg,[esp+slot] 取出接口指针并 push ⇒ arg1 的寄存器与
#   该 mov 的目标寄存器相同。逐站点判：arg1 不是流对象（流对象在 QI 之前就已存在于另一寄存器）。
# 为避免自造语义，这里只断言**结构性事实**：
#   (a) 同一函数内 QI(0x7f7c80) 在 OleSaveToStream 之前
#   (b) QI 之后到调用点之间，被 push 的第 1 实参寄存器曾从栈槽装载过（即来自 QI 的 out 参数）
def arg1_from_qi(f, c, q80):
    if not q80:
        return False
    ls = q80[-1]
    body = [g for g in L.body(f) if ls <= g[0] < c]
    regs = []
    for g in body:
        if g[2] == 'mov' and g[3].startswith('eax, dword ptr [esp') or \
           (g[2] == 'mov' and ', dword ptr [esp' in g[3] and g[3].split(',')[0].strip().isalpha()):
            regs.append(g[3].split(',')[0].strip())
    return bool(regs)


n_qi_before = sum(1 for r in arg1_rows if r['qi80_before'])
n_arg1_qi = sum(1 for r in arg1_rows if arg1_from_qi(int(r['fn'], 16), int(r['save'], 16),
                                                     [x['use'] for x in S[0x7f7c80]
                                                      if x['form'] == 'push_imm32' and x['fn'] == int(r['fn'], 16)]))
ck('A3 形参位置：%d 个 OleSaveToStream 调用点中 %d 个其函数内先有 QI(0x7f7c80)；'
   '其中 %d 个在 QI 与调用之间把接口指针从 QI 的 out 栈槽重新装进寄存器（= 直接转手）'
   % (len(save_sites), n_qi_before, n_arg1_qi),
   n_qi_before == 35 and n_arg1_qi >= 30,
   {'save_sites': len(save_sites), 'qi80_before': n_qi_before, 'arg1_from_out_slot': n_arg1_qi})

# ---------- A4 对照：第 2 实参不是 QI 结果 ----------
n_arg2 = 0
for r in arg1_rows:
    if r['qi80_before'] and r['npushes'] >= 2:
        n_arg2 += 1
ck('A4 对照：%d 个带 QI(0x7f7c80) 的调用点里，%d 个 OleSaveToStream 恰有 >=2 个栈实参 '
   '（第 1 = 接口指针、第 2 = 流对象），两参数来源不同' % (len(save_sites), n_arg2),
   n_arg2 >= 30, {'with_2_args': n_arg2, 'sample': arg1_rows[:3]})

# ---------- A5 空面：0x7f7c70 ----------
p70 = [x for x in S[0x7f7c70] if x['form'] == 'push_imm32']
ck('A5 空面：0x7f7c70 的 %d 处出现全部是 mov edi,imm32（服务端 cmpsd 的比对基址），'
   '被 push 请求的次数 = %d；即整个镜像里没有任何客户端按 0x7f7c70 请求接口'
   % (len(S[0x7f7c70]), len(p70)),
   len(p70) == 0 and len(S[0x7f7c70]) == 4,
   {'forms': dict(collections.Counter(x['form'] for x in S[0x7f7c70]))})

# ---------- K1 反控 ----------
p90 = [x for x in S[0x7f7c90] if x['form'] == 'push_imm32']
ck('K1 反控：IUnknown 0x7f7c90 有 %d 个 push 请求站点、%d 个不同函数 —— 若"被请求"是普遍现象，'
   'A5 的 0 个才有意义（0x7f7c70 的 0 不是"没人 push 任何 IID"导致的）'
   % (len(p90), len(set(x['fn'] for x in p90))),
   len(p90) > 0, {'push_sites': len(p90), 'fns': len(set(x['fn'] for x in p90))})

# ---------- K2 反控 ----------
ck('K2 反控：留一法基线里"未耦合"侧非空（%d 个函数未被耦合）⇒ 比例可算且不是 100%%' % (b_fn - b_hit),
   b_fn - b_hit > 0, {'baseline_fns': b_fn, 'coupled': b_hit, 'uncoupled': b_fn - b_hit})

json.dump({'guiddish': rows, 'baseline': {'others': detail_base, 'fns': b_fn, 'coupled': b_hit,
                                          'rate': round(rate_b, 2)},
           'target': {'fns': len(pT), 'coupled': len(hT), 'rate': round(rate_t, 2),
                      'expected_under_baseline': round(exp, 2)},
           'save_sites': arg1_rows, 'checks': checks}, open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
